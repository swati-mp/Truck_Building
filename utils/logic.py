import pandas as pd
import numpy as np
import uuid
import os
from geopy.distance import geodesic
from utils.db_utils import get_customer_warehouse

def prepare_customer_summary(filtered_orders, customers_df, products_df):
    filtered_orders['customer_id'] = filtered_orders['customer_id']
    customers_df['customer_id'] = customers_df['customer_id']
    filtered_orders['product_id'] = filtered_orders['product_id']
    products_df['product_id'] = products_df['product_id']

    merged = filtered_orders.merge(customers_df, on='customer_id')
    merged = merged.merge(products_df, on='product_id')

    summary = merged.groupby(['customer_id', 'customer_name', 'latitude', 'longitude']).agg(
        total_weight_kg=pd.NamedAgg(column='weight_per_box', aggfunc=lambda x: (x * merged.loc[x.index, 'num_boxes']).sum()),
        total_volume_m3=pd.NamedAgg(column='size_per_box', aggfunc=lambda x: (x * merged.loc[x.index, 'num_boxes']).sum())
    ).reset_index()

    return summary

def haversine_np(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def nearest_neighbor_route(customer_coords, start_coord):
    if not customer_coords:
        return []

    coords = np.array(customer_coords)
    visited = [start_coord]
    current = np.array(start_coord)
    remaining = coords.copy()

    while len(remaining) > 0:
        lat1, lon1 = current[0], current[1]
        lat2, lon2 = remaining[:, 0], remaining[:, 1]
        distances = haversine_np(lat1, lon1, lat2, lon2)
        nearest_idx = np.argmin(distances)
        nearest_coord = remaining[nearest_idx]
        visited.append(tuple(nearest_coord))
        remaining = np.delete(remaining, nearest_idx, axis=0)
        current = nearest_coord

    return visited

def run_allocation(filtered_orders, customers_df, products_df, trucks_df, config, warehouses_df):
    all_allocations = []
    all_routes = []

    states = customers_df['state'].unique()
    for state in states:
        state_customers = customers_df[customers_df['state'] == state]
        state_orders = filtered_orders[filtered_orders['customer_id'].isin(state_customers['customer_id'])]

        if state_orders.empty:
            continue

        customer_summary = prepare_customer_summary(state_orders, state_customers, products_df)
        truck_capacity = trucks_df.copy()
        truck_capacity['min_capacity_kg'] = trucks_df['capacity_tons'] * 1000 * (config['min_load_percent'] / 100)
        truck_capacity['max_capacity_kg'] = trucks_df['capacity_tons'] * 1000 * (config['max_load_percent'] / 100)

        allocations = []
        for _, row in customer_summary.iterrows():
            total_weight = row['total_weight_kg']
            total_volume = row['total_volume_m3']

            suitable_trucks = truck_capacity[
                (truck_capacity['min_capacity_kg'] <= total_weight) &
                (total_weight <= truck_capacity['max_capacity_kg'])
            ].sort_values(by='capacity_tons')

            truck_type = suitable_trucks.iloc[0]['truck_type'] if not suitable_trucks.empty else '❌ No Suitable Truck Found'

            allocations.append({
                "customer_id": row['customer_id'],
                "customer_name": row['customer_name'],
                "latitude": row['latitude'],
                "longitude": row['longitude'],
                "state": state,
                "total_weight_kg": round(total_weight, 2),
                "total_volume_m3": round(total_volume, 2),
                "assigned_truck_type": truck_type  
            })

        allocation_df = pd.DataFrame(allocations)

        warehouse = warehouses_df[warehouses_df['state'] == state]
        if not warehouse.empty:
            start_coord = (warehouse.iloc[0]['latitude'], warehouse.iloc[0]['longitude'])
        else:
            start_coord = (allocation_df['latitude'].mean(), allocation_df['longitude'].mean())

        customer_coords = [(row['latitude'], row['longitude']) for _, row in allocation_df.iterrows()]
        optimized_route = nearest_neighbor_route(customer_coords, start_coord)[1:]

        route_df = pd.DataFrame(optimized_route, columns=['latitude', 'longitude'])
        route_df['stop_order'] = range(len(route_df), 0, -1)
        route_df['state'] = state

        all_allocations.append(allocation_df)
        all_routes.append(route_df)

    return pd.concat(all_allocations, ignore_index=True), pd.concat(all_routes, ignore_index=True)

def calculate_total_route_distance(route_coords):
    return sum(
        geodesic(route_coords[i], route_coords[i + 1]).km
        for i in range(len(route_coords) - 1)
    )

def filo_grouped_truck_allocation(filtered_orders, customers_df, products_df, trucks_df, config,
                                   fuel_price_per_litre=90.0, mileage_kmpl=4.0, warehouses_df=None):
    import uuid
    import os
    import pandas as pd
    from utils.logic import calculate_total_route_distance, nearest_neighbor_route

    all_truck_allocations = []
    states = customers_df['state'].dropna().unique()

    # Ensure consistent data types
    filtered_orders['customer_id'] = filtered_orders['customer_id'].astype(str)
    filtered_orders['product_id'] = filtered_orders['product_id'].astype(str)
    customers_df['customer_id'] = customers_df['customer_id'].astype(str)
    products_df['product_id'] = products_df['product_id'].astype(str)

    target_date = pd.to_datetime(filtered_orders['delivery_date'].iloc[0]).date()
    min_percent = config.get('min_load_percent', 60) / 100
    max_percent = config.get('max_load_percent', 95) / 100

    for state in states:
        state_customers = customers_df[customers_df['state'] == state]
        state_orders = filtered_orders[filtered_orders['customer_id'].isin(state_customers['customer_id'])]
        state_trucks = trucks_df[trucks_df['state'] == state]
        state_warehouse = warehouses_df[warehouses_df['state'] == state] if warehouses_df is not None else pd.DataFrame()

        if state_orders.empty or state_trucks.empty:
            continue

        # Merge all required details
        merged = state_orders.merge(state_customers, on='customer_id').merge(products_df, on='product_id')
        merged['total_weight_kg'] = merged['num_boxes'] * merged['weight_per_box']
        merged['total_volume_m3'] = merged['num_boxes'] * merged['size_per_box']

        # Summarize per customer
        customer_summary = merged.groupby(
            ['customer_id', 'customer_name', 'latitude', 'longitude', 'delivery_date']
        ).agg({
            'total_weight_kg': 'sum',
            'total_volume_m3': 'sum'
        }).reset_index()

        # Determine starting warehouse or average
        start_coord = (
            (state_warehouse.iloc[0]['latitude'], state_warehouse.iloc[0]['longitude'])
            if not state_warehouse.empty else
            (customer_summary['latitude'].mean(), customer_summary['longitude'].mean())
        )

        # Get route using Nearest Neighbor
        customer_coords = list(zip(customer_summary['latitude'], customer_summary['longitude']))
        ordered_route = nearest_neighbor_route(customer_coords, start_coord)[1:]

        # Apply FILO: farthest delivery first
        customer_summary['route_order'] = customer_summary.apply(
            lambda row: ordered_route.index((row['latitude'], row['longitude'])) + 1
            if (row['latitude'], row['longitude']) in ordered_route else 0,
            axis=1
        )
        customer_summary = customer_summary.sort_values(by='route_order', ascending=False)

        # Add truck capacity limits
        state_trucks = state_trucks.copy()
        state_trucks['min_capacity_kg'] = state_trucks['capacity_tons'] * 1000 * min_percent
        state_trucks['max_capacity_kg'] = state_trucks['capacity_tons'] * 1000 * max_percent
        state_trucks = state_trucks.sort_values(by='capacity_tons', ascending=False)

        truck_allocations = []
        remaining_customers = customer_summary.copy()
        truck_id = 1

        while not remaining_customers.empty:
            assigned = pd.DataFrame()

            for _, truck in state_trucks.iterrows():
                truck_capacity = truck['capacity_tons'] * 1000
                min_capacity = truck['min_capacity_kg']
                max_capacity = truck['max_capacity_kg']

                load_sum = 0
                selected_rows = []

                # Try adding customers until the truck is efficiently filled
                for idx, row in remaining_customers.iterrows():
                    if load_sum + row['total_weight_kg'] <= truck_capacity:
                        load_sum += row['total_weight_kg']
                        selected_rows.append(idx)

                if selected_rows and min_capacity <= load_sum <= max_capacity:
                    assigned = remaining_customers.loc[selected_rows].copy()
                    remaining_customers.drop(index=selected_rows, inplace=True)

                    # Assign truck info
                    assigned['truck_type'] = truck['truck_type']
                    assigned['truck_id'] = str(uuid.uuid4())[:8]
                    assigned['route_id'] = truck_id
                    assigned['truck_capacity_kg'] = truck_capacity
                    assigned['utilization_percent'] = round((load_sum / truck_capacity) * 100, 2)
                    assigned['state'] = state
                    assigned['delivery_date'] = assigned['delivery_date'].iloc[0]

                    # Route distance + fuel
                    route_points = assigned.sort_values("route_order")[["latitude", "longitude"]].values
                    depot = start_coord if start_coord else route_points[0]
                    full_route = [depot] + [tuple(coord) for coord in route_points] + [depot]
                    total_distance_km = calculate_total_route_distance(full_route)

                    fuel_used_litres = total_distance_km / mileage_kmpl
                    assigned['total_distance_km'] = round(total_distance_km, 2)
                    assigned['fuel_cost'] = round(fuel_used_litres * fuel_price_per_litre, 2)
                    assigned['emissions_estimate'] = round(fuel_used_litres * 2.68, 2)

                    truck_allocations.append(assigned)
                    truck_id += 1
                    break  # Move to next truck

            if assigned.empty:
                break  # Stop if no truck can be used efficiently

        if truck_allocations:
            all_truck_allocations.append(pd.concat(truck_allocations, ignore_index=True))

    final_df = pd.concat(all_truck_allocations, ignore_index=True) if all_truck_allocations else pd.DataFrame()

    # Save/merge output to file
    existing_path = "data/allocation.csv"
    if os.path.exists(existing_path):
        existing_df = pd.read_csv(existing_path)
        existing_df['delivery_date'] = pd.to_datetime(existing_df['delivery_date']).dt.date
        existing_df = existing_df[existing_df['delivery_date'] != target_date]
        final_df = pd.concat([existing_df, final_df], ignore_index=True)

    if not final_df.empty:
        final_df.to_csv(existing_path, index=False)

    return final_df


