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

'''gives detailed truck allocation based on products/orders per customer,
    optimizes route, and loads based on total weight within truck capacity.
    
# def filo_grouped_truck_allocation(filtered_orders, customers_df, products_df, trucks_df, config,
#                                    fuel_price_per_litre=90.0, mileage_kmpl=4.0, warehouses_df=None):
#     all_truck_allocations = []
#     states = customers_df['state'].unique()

#     for state in states:
#         state_customers = customers_df[customers_df['state'] == state]
#         state_orders = filtered_orders[filtered_orders['customer_id'].isin(state_customers['customer_id'])]

#         if state_orders.empty:
#             continue

#         merged = state_orders.merge(state_customers, on='customer_id').merge(products_df, on='product_id')
#         merged['total_weight_kg'] = merged['num_boxes'] * merged['weight_per_box']
#         merged['total_volume_m3'] = merged['num_boxes'] * merged['size_per_box']

#         # Get warehouse for this state
#         warehouse = warehouses_df[warehouses_df['state'] == state]
#         if not warehouse.empty:
#             start_coord = (warehouse.iloc[0]['latitude'], warehouse.iloc[0]['longitude'])
#         else:
#             start_coord = (merged['latitude'].mean(), merged['longitude'].mean())  # fallback

#         # Determine route
#         customers = merged[['customer_id', 'latitude', 'longitude']].drop_duplicates()
#         customer_coords = [(row['latitude'], row['longitude']) for _, row in customers.iterrows()]
#         ordered_route = nearest_neighbor_route(customer_coords, start_coord)[1:]

#         merged['route_order'] = merged.apply(lambda row:
#             ordered_route.index((row['latitude'], row['longitude'])) + 1
#             if (row['latitude'], row['longitude']) in ordered_route else 0, axis=1)

#         merged = merged.sort_values(by='route_order', ascending=False)

#         trucks_df = trucks_df.copy()
#         trucks_df['min_capacity_kg'] = trucks_df['capacity_tons'] * 1000 * (config['min_load_percent'] / 100)
#         trucks_df['max_capacity_kg'] = trucks_df['capacity_tons'] * 1000 * (config['max_load_percent'] / 100)

#         truck_allocations = []
#         remaining_boxes = merged.copy()
#         truck_id = 1

#         while not remaining_boxes.empty:
#             truck_uuid = str(uuid.uuid4())[:8]
#             for _, truck in trucks_df.sort_values(by='capacity_tons', ascending=True).iterrows():
#                 truck_capacity = truck['capacity_tons'] * 1000
#                 box_sum = 0
#                 selected_rows = []
#                 for idx, box in remaining_boxes.iterrows():
#                     if box_sum + box['total_weight_kg'] <= truck_capacity:
#                         selected_rows.append(idx)
#                         box_sum += box['total_weight_kg']

#                 if selected_rows:
#                     assigned = remaining_boxes.loc[selected_rows].copy()
#                     assigned['truck_type'] = truck['truck_type']
#                     assigned['truck_id'] = truck_uuid
#                     assigned['route_id'] = truck_id
#                     assigned['fuel_cost'] = round((box_sum / mileage_kmpl) * fuel_price_per_litre, 2)
#                     assigned['emissions_estimate'] = round((box_sum / mileage_kmpl) * 2.68, 2)
#                     assigned['truck_capacity_kg'] = truck_capacity
#                     assigned['utilization_percent'] = round((box_sum / truck_capacity) * 100, 2)
#                     assigned['state'] = state
#                     truck_allocations.append(assigned)
#                     remaining_boxes.drop(index=selected_rows, inplace=True)
#                     truck_id += 1
#                     break

#         if truck_allocations:
#             all_truck_allocations.append(pd.concat(truck_allocations, ignore_index=True))

#     return pd.concat(all_truck_allocations, ignore_index=True) if all_truck_allocations else pd.DataFrame()
'''

def filo_grouped_truck_allocation(filtered_orders, customers_df, products_df, trucks_df, config,
                                   fuel_price_per_litre=90.0, mileage_kmpl=4.0, warehouses_df=None):
    """
    Truck allocation grouped by customer_id — combines all products/orders per customer,
    optimizes route, and loads based on total weight within truck capacity.
    """
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

        # Combine multiple product orders per customer
        customer_summary = merged.groupby(['customer_id', 'customer_name', 'latitude', 'longitude']).agg({
            'total_weight_kg': 'sum',
            'total_volume_m3': 'sum'
        }).reset_index()

        # Get warehouse coordinates
        warehouse = warehouses_df[warehouses_df['state'] == state]
        if not warehouse.empty:
            start_coord = (warehouse.iloc[0]['latitude'], warehouse.iloc[0]['longitude'])
        else:
            start_coord = (customer_summary['latitude'].mean(), customer_summary['longitude'].mean())

        # Optimize customer delivery route
        customer_coords = list(zip(customer_summary['latitude'], customer_summary['longitude']))
        ordered_route = nearest_neighbor_route(customer_coords, start_coord)[1:]

        # Assign route order
        customer_summary['route_order'] = customer_summary.apply(lambda row:
            ordered_route.index((row['latitude'], row['longitude'])) + 1
            if (row['latitude'], row['longitude']) in ordered_route else 0, axis=1)
        customer_summary = customer_summary.sort_values(by='route_order', ascending=False)

        # Prepare truck capacity
        trucks_df = trucks_df.copy()
        trucks_df['min_capacity_kg'] = trucks_df['capacity_tons'] * 1000 * (config['min_load_percent'] / 100)
        trucks_df['max_capacity_kg'] = trucks_df['capacity_tons'] * 1000 * (config['max_load_percent'] / 100)

        truck_allocations = []
        remaining_customers = customer_summary.copy()
        truck_id = 1

        while not remaining_customers.empty:
            truck_uuid = str(uuid.uuid4())[:8]

            for _, truck in trucks_df.sort_values(by='capacity_tons', ascending=True).iterrows():
                truck_capacity = truck['capacity_tons'] * 1000
                box_sum = 0
                selected_rows = []

                for idx, row in remaining_customers.iterrows():
                    if box_sum + row['total_weight_kg'] <= truck_capacity:
                        selected_rows.append(idx)
                        box_sum += row['total_weight_kg']

                if selected_rows:
                    assigned = remaining_customers.loc[selected_rows].copy()
                    assigned['truck_type'] = truck['truck_type']
                    assigned['truck_id'] = truck_uuid
                    assigned['route_id'] = truck_id
                    assigned['fuel_cost'] = round((box_sum / mileage_kmpl) * fuel_price_per_litre, 2)
                    assigned['emissions_estimate'] = round((box_sum / mileage_kmpl) * 2.68, 2)
                    assigned['truck_capacity_kg'] = truck_capacity
                    assigned['utilization_percent'] = round((box_sum / truck_capacity) * 100, 2)
                    assigned['state'] = state

                    truck_allocations.append(assigned)
                    remaining_customers.drop(index=selected_rows, inplace=True)
                    truck_id += 1
                    break

        if truck_allocations:
            all_truck_allocations.append(pd.concat(truck_allocations, ignore_index=True))

    return pd.concat(all_truck_allocations, ignore_index=True) if all_truck_allocations else pd.DataFrame()

# def filo_grouped_truck_allocation(
#     filtered_orders,
#     customers_df,
#     products_df,
#     trucks_df,
#     config,
#     mileage_kmpl_fallback=4.0,
#     warehouses_df=None
# ):
#     """
#     FILO-based truck allocation using per-customer grouping.
#     Uses per-truck capacity, fuel efficiency (kmpl), and fuel cost (cost_per_km).
#     """
#     all_truck_allocations = []
#     states = customers_df['state'].unique()

#     for state in states:
#         state_customers = customers_df[customers_df['state'] == state]
#         state_orders = filtered_orders[filtered_orders['customer_id'].isin(state_customers['customer_id'])]

#         if state_orders.empty:
#             continue

#         # Merge order details
#         merged = state_orders.merge(state_customers, on='customer_id').merge(products_df, on='product_id')
#         merged['total_weight_kg'] = merged['num_boxes'] * merged['weight_per_box']
#         merged['total_volume_m3'] = merged['num_boxes'] * merged['size_per_box']

#         # Group orders per customer
#         customer_summary = merged.groupby(
#             ['customer_id', 'customer_name', 'latitude', 'longitude']
#         ).agg({
#             'total_weight_kg': 'sum',
#             'total_volume_m3': 'sum'
#         }).reset_index()

#         # Get warehouse coordinates for this state
#         warehouse = warehouses_df[warehouses_df['state'] == state] if warehouses_df is not None else pd.DataFrame()
#         if not warehouse.empty:
#             start_coord = (warehouse.iloc[0]['latitude'], warehouse.iloc[0]['longitude'])
#         else:
#             start_coord = (customer_summary['latitude'].mean(), customer_summary['longitude'].mean())

#         # Optimize customer route (FILO)
#         customer_coords = list(zip(customer_summary['latitude'], customer_summary['longitude']))
#         ordered_route = nearest_neighbor_route(customer_coords, start_coord)[1:]  # skip warehouse

#         # Assign route order
#         customer_summary['route_order'] = customer_summary.apply(
#             lambda row: ordered_route.index((row['latitude'], row['longitude'])) + 1
#             if (row['latitude'], row['longitude']) in ordered_route else 0,
#             axis=1
#         )
#         customer_summary = customer_summary.sort_values(by='route_order', ascending=False)

#         # Truck filtering & capacity calculations
#         state_trucks = trucks_df[trucks_df['state'] == state].copy()
#         if state_trucks.empty:
#             continue

#         state_trucks['min_capacity_kg'] = state_trucks['capacity_tons'] * 1000 * (config['min_load_percent'] / 100)
#         state_trucks['max_capacity_kg'] = state_trucks['capacity_tons'] * 1000 * (config['max_load_percent'] / 100)

#         truck_allocations = []
#         remaining_customers = customer_summary.copy()
#         truck_id = 1

#         while not remaining_customers.empty:
#             for _, truck in state_trucks.sort_values(by='capacity_tons').iterrows():
#                 truck_capacity = truck['capacity_tons'] * 1000
#                 min_cap = truck['min_capacity_kg']
#                 max_cap = truck['max_capacity_kg']
#                 efficiency = truck.get('fuel_efficiency_kmpl', mileage_kmpl_fallback)
#                 fuel_price = truck.get('cost_per_km', 90.0)

#                 box_sum = 0
#                 selected_rows = []

#                 for idx, row in remaining_customers.iterrows():
#                     if box_sum + row['total_weight_kg'] <= max_cap:
#                         selected_rows.append(idx)
#                         box_sum += row['total_weight_kg']

#                 # Allocate if within min/max limits
#                 if box_sum >= min_cap and selected_rows:
#                     truck_uuid = str(uuid.uuid4())[:8]
#                     assigned = remaining_customers.loc[selected_rows].copy()

#                     assigned['truck_type'] = truck['truck_type']
#                     assigned['truck_id'] = truck_uuid
#                     assigned['route_id'] = truck_id
#                     assigned['truck_capacity_kg'] = truck_capacity
#                     assigned['utilization_percent'] = round((box_sum / truck_capacity) * 100, 2)
#                     assigned['fuel_cost'] = round((box_sum / efficiency) * fuel_price, 2)
#                     assigned['emissions_estimate'] = round((box_sum / efficiency) * 2.68, 2)
#                     assigned['state'] = state

#                     truck_allocations.append(assigned)
#                     remaining_customers.drop(index=selected_rows, inplace=True)
#                     truck_id += 1
#                     break

#         if truck_allocations:
#             all_truck_allocations.append(pd.concat(truck_allocations, ignore_index=True))

#     return pd.concat(all_truck_allocations, ignore_index=True) if all_truck_allocations else pd.DataFrame()
