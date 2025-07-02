import pandas as pd
import uuid
from geopy.distance import geodesic
from utils.db_utils import get_customer_warehouse

def prepare_customer_summary(filtered_orders, customers_df, products_df):
    merged = filtered_orders.merge(customers_df, on='customer_id')
    merged = merged.merge(products_df, on='product_id')

    summary = merged.groupby(['customer_id', 'customer_name', 'latitude', 'longitude']).agg(
        total_weight_kg=pd.NamedAgg(column='weight_per_box', aggfunc=lambda x: (x * merged.loc[x.index, 'num_boxes']).sum()),
        total_volume_m3=pd.NamedAgg(column='size_per_box', aggfunc=lambda x: (x * merged.loc[x.index, 'num_boxes']).sum())
    ).reset_index()

    return summary

def nearest_neighbor_route(customer_coords, start_coord):
    if not customer_coords:
        return []

    visited = []
    current = start_coord
    coords = customer_coords.copy()

    while coords:
        next_customer = min(coords, key=lambda x: geodesic(current, x).km)
        visited.append(next_customer)
        coords.remove(next_customer)
        current = next_customer

    return [start_coord] + visited

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
                "total_weight_kg": round(total_weight, 2),
                "total_volume_m3": round(total_volume, 2),
                "assigned_truck_type": truck_type,
                "state": state
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


def filo_grouped_truck_allocation(filtered_orders, customers_df, products_df, trucks_df, config,
                                   fuel_price_per_litre=90.0, mileage_kmpl=4.0, warehouses_df=None):
    all_truck_allocations = []
    states = customers_df['state'].unique()

    for state in states:
        state_customers = customers_df[customers_df['state'] == state]
        state_orders = filtered_orders[filtered_orders['customer_id'].isin(state_customers['customer_id'])]

        if state_orders.empty:
            continue

        merged = state_orders.merge(state_customers, on='customer_id').merge(products_df, on='product_id')
        merged['total_weight_kg'] = merged['num_boxes'] * merged['weight_per_box']
        merged['total_volume_m3'] = merged['num_boxes'] * merged['size_per_box']

        # Get warehouse for this state
        warehouse = warehouses_df[warehouses_df['state'] == state]
        if not warehouse.empty:
            start_coord = (warehouse.iloc[0]['latitude'], warehouse.iloc[0]['longitude'])
        else:
            start_coord = (merged['latitude'].mean(), merged['longitude'].mean())  # fallback

        # Determine route
        customers = merged[['customer_id', 'latitude', 'longitude']].drop_duplicates()
        customer_coords = [(row['latitude'], row['longitude']) for _, row in customers.iterrows()]
        ordered_route = nearest_neighbor_route(customer_coords, start_coord)[1:]

        merged['route_order'] = merged.apply(lambda row:
            ordered_route.index((row['latitude'], row['longitude'])) + 1
            if (row['latitude'], row['longitude']) in ordered_route else 0, axis=1)

        merged = merged.sort_values(by='route_order', ascending=False)

        trucks_df = trucks_df.copy()
        trucks_df['min_capacity_kg'] = trucks_df['capacity_tons'] * 1000 * (config['min_load_percent'] / 100)
        trucks_df['max_capacity_kg'] = trucks_df['capacity_tons'] * 1000 * (config['max_load_percent'] / 100)

        truck_allocations = []
        remaining_boxes = merged.copy()
        truck_id = 1

        while not remaining_boxes.empty:
            truck_uuid = str(uuid.uuid4())[:8]
            for _, truck in trucks_df.sort_values(by='capacity_tons', ascending=True).iterrows():
                truck_capacity = truck['capacity_tons'] * 1000
                box_sum = 0
                selected_rows = []
                for idx, box in remaining_boxes.iterrows():
                    if box_sum + box['total_weight_kg'] <= truck_capacity:
                        selected_rows.append(idx)
                        box_sum += box['total_weight_kg']

                if selected_rows:
                    assigned = remaining_boxes.loc[selected_rows].copy()
                    assigned['truck_type'] = truck['truck_type']
                    assigned['truck_id'] = truck_uuid
                    assigned['route_id'] = truck_id
                    assigned['fuel_cost'] = round((box_sum / mileage_kmpl) * fuel_price_per_litre, 2)
                    assigned['emissions_estimate'] = round((box_sum / mileage_kmpl) * 2.68, 2)
                    assigned['truck_capacity_kg'] = truck_capacity
                    assigned['utilization_percent'] = round((box_sum / truck_capacity) * 100, 2)
                    assigned['state'] = state
                    truck_allocations.append(assigned)
                    remaining_boxes.drop(index=selected_rows, inplace=True)
                    truck_id += 1
                    break

        if truck_allocations:
            all_truck_allocations.append(pd.concat(truck_allocations, ignore_index=True))

    return pd.concat(all_truck_allocations, ignore_index=True) if all_truck_allocations else pd.DataFrame()

def multi_truck_allocation(customer_summary_df, trucks_df, config):
    trucks_df = trucks_df.copy()
    trucks_df['min_capacity_kg'] = trucks_df['capacity_tons'] * 1000 * (config['min_load_percent'] / 100)
    trucks_df['max_capacity_kg'] = trucks_df['capacity_tons'] * 1000 * (config['max_load_percent'] / 100)

    multi_allocations = []

    for _, row in customer_summary_df.iterrows():
        customer_id = row['customer_id']
        customer_name = row['customer_name']
        total_weight = row['total_weight_kg']
        total_volume = row['total_volume_m3']

        best_fit = None
        best_cost = float('inf')

        for _, truck in trucks_df.iterrows():
            if truck['min_capacity_kg'] <= total_weight <= truck['max_capacity_kg']:
                cost_per_kg = truck['cost_per_km'] / truck['capacity_tons']
                if cost_per_kg < best_cost:
                    best_cost = cost_per_kg
                    best_fit = truck

        assigned_truck = best_fit['truck_type'] if best_fit is not None else "❌ No Suitable Truck"

        multi_allocations.append({
            "customer_id": customer_id,
            "customer_name": customer_name,
            "total_weight_kg": round(total_weight, 2),
            "total_volume_m3": round(total_volume, 2),
            "best_fit_truck_type": assigned_truck,
            "cost_per_kg": round(best_cost, 2) if best_fit is not None else "N/A"
        })

    return pd.DataFrame(multi_allocations)
