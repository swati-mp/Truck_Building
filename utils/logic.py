import pandas as pd
from geopy.distance import geodesic
import uuid

def calculate_box_volume(size_per_box):
    return size_per_box

def nearest_neighbor_route(locations, start_coord):
    if not locations:
        return []
    route = [start_coord]
    remaining = locations.copy()
    while remaining:
        last = route[-1]
        next_point = min(remaining, key=lambda coord: geodesic(last, coord).km)
        route.append(next_point)
        remaining.remove(next_point)
    return route

def prepare_customer_summary(filtered_orders, customers_df, products_df):
    merged = filtered_orders.merge(customers_df, on="customer_id", how="left")
    merged = merged.merge(products_df, on="product_id", how="left")

    merged['total_weight_kg'] = merged['num_boxes'] * merged['weight_per_box']
    merged['total_volume_m3'] = merged['num_boxes'] * merged['size_per_box']

    customer_summary = merged.groupby(
        ['customer_id', 'customer_name', 'latitude', 'longitude']
    ).agg({
        'total_weight_kg': 'sum',
        'total_volume_m3': 'sum'
    }).reset_index()

    return customer_summary

def run_allocation(filtered_orders, customers_df, products_df, trucks_df, config):
    customer_summary = prepare_customer_summary(filtered_orders, customers_df, products_df)

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
            "assigned_truck_type": truck_type
        })

    allocation_df = pd.DataFrame(allocations)
    start_coord = (customers_df.iloc[0]['latitude'], customers_df.iloc[0]['longitude'])
    customer_coords = [(row['latitude'], row['longitude']) for _, row in allocation_df.iterrows()]
    optimized_route = nearest_neighbor_route(customer_coords, start_coord)[1:]

    route_df = pd.DataFrame(optimized_route, columns=['latitude', 'longitude'])
    route_df['stop_order'] = range(len(route_df), 0, -1)

    return allocation_df, route_df

def filo_grouped_truck_allocation(filtered_orders, customers_df, products_df, trucks_df, config,
                                   fuel_price_per_litre=90.0, mileage_kmpl=4.0):
    merged = filtered_orders.merge(customers_df, on='customer_id')
    merged = merged.merge(products_df, on='product_id')

    merged['total_weight_kg'] = merged['num_boxes'] * merged['weight_per_box']
    merged['total_volume_m3'] = merged['num_boxes'] * merged['size_per_box']

    customers = merged[['customer_id', 'latitude', 'longitude']].drop_duplicates()
    start_coord = (customers_df.iloc[0]['latitude'], customers_df.iloc[0]['longitude'])
    customer_coords = [(row['latitude'], row['longitude']) for _, row in customers.iterrows()]
    ordered_route = nearest_neighbor_route(customer_coords, start_coord)[1:]

    merged['route_order'] = merged.apply(lambda row:
        ordered_route.index((row['latitude'], row['longitude'])) + 1, axis=1)

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
                truck_allocations.append(assigned)
                remaining_boxes.drop(index=selected_rows, inplace=True)
                truck_id += 1
                break
            else:
                continue

    return pd.concat(truck_allocations, ignore_index=True)

# def generate_filo_manifest(filo_allocated_df, orders_df, customers_df, products_df):
#     if filo_allocated_df.empty:
#         return pd.DataFrame()

#     # Merge based on presence of product_id
#     if 'product_id' in filo_allocated_df.columns:
#         merged = filo_allocated_df.copy()
#     else:
#         merged = filo_allocated_df.merge(
#             orders_df[['order_id', 'customer_id', 'product_id', 'num_boxes']],
#             on='order_id', how='left'
#         )

#     # Add product and customer names
#     if 'product_id' in merged.columns:
#         merged = merged.merge(
#             products_df[['product_id', 'product_name']],
#             on='product_id', how='left'
#         )

#     merged = merged.merge(
#         customers_df[['customer_id', 'customer_name']],
#         on='customer_id', how='left'
#     )

#     # Sort by truck_id and reverse stop_sequence for FILO
#     merged = merged.sort_values(by=['truck_id', 'stop_sequence'], ascending=[True, False])

#     # Generate manifest
#     manifest = merged.groupby(['truck_id', 'truck_type', 'stop_sequence']).agg({
#         'customer_name': 'first',
#         'product_name': 'first',
#         'num_boxes': 'sum',
#         'total_weight': 'sum',
#         'fuel_cost': 'first',
#         'emissions_kg': 'first'
#     }).reset_index()

#     return manifest

def generate_filo_manifest(filo_allocated_df, orders_df, customers_df, products_df):
    if filo_allocated_df.empty:
        return pd.DataFrame()

    # Strip column names to remove whitespace
    products_df.columns = [col.strip() for col in products_df.columns]
    orders_df.columns = [col.strip() for col in orders_df.columns]

    # 🔍 Add debug print statements here
    print("Products columns:", products_df.columns.tolist())
    print("Orders columns:", orders_df.columns.tolist())

    # Ensure necessary columns
    if 'product_id' not in products_df.columns:
        raise ValueError("❌ 'product_id' missing in products_df")
    if 'product_id' not in orders_df.columns:
        raise ValueError("❌ 'product_id' missing in orders_df")

    merged = filo_allocated_df.merge(
        orders_df[['order_id', 'customer_id', 'product_id', 'num_boxes']],
        on='order_id', how='left'
    ).merge(
        products_df[['product_id', 'product_name']],
        on='product_id', how='left'
    ).merge(
        customers_df[['customer_id', 'customer_name']],
        on='customer_id', how='left'
    )

    manifest = merged.groupby(['truck_id', 'truck_type', 'stop_sequence']).agg({
        'customer_name': 'first',
        'product_name': 'first',
        'num_boxes': 'sum',
        'total_weight': 'sum'
    }).reset_index().sort_values(by=['truck_id', 'stop_sequence'], ascending=[True, False])

    return manifest

def multi_truck_allocation(customer_summary, trucks_df, config):
    trucks_df = trucks_df.copy()
    trucks_df["min_capacity_kg"] = trucks_df["capacity_tons"] * 1000 * (config['min_load_percent'] / 100)
    trucks_df["max_capacity_kg"] = trucks_df["capacity_tons"] * 1000 * (config['max_load_percent'] / 100)
    trucks_df["cost_per_kg"] = trucks_df["cost_per_km"] / (trucks_df["capacity_tons"] * 1000)

    allocations = []

    for _, row in customer_summary.iterrows():
        customer_id = row['customer_id']
        customer_name = row['customer_name']
        remaining_weight = row['total_weight_kg']

        trucks_sorted = trucks_df.sort_values(by='cost_per_kg')

        for _, truck in trucks_sorted.iterrows():
            if remaining_weight <= 0:
                break

            alloc_weight = min(remaining_weight, truck['max_capacity_kg'])
            if alloc_weight >= truck['min_capacity_kg']:
                allocations.append({
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'truck_type': truck['truck_type'],
                    'allocated_weight_kg': alloc_weight,
                    'truck_capacity_kg': truck['capacity_tons'] * 1000,
                    'cost_per_km': truck['cost_per_km'],
                    'cost_per_kg': truck['cost_per_kg'],
                    'total_estimated_cost': round(alloc_weight * truck['cost_per_kg'], 2)
                })
                remaining_weight -= alloc_weight

        if remaining_weight > 0:
            fallback_truck = trucks_sorted.iloc[-1]
            allocations.append({
                'customer_id': customer_id,
                'customer_name': customer_name,
                'truck_type': fallback_truck['truck_type'] + " (Forced)",
                'allocated_weight_kg': remaining_weight,
                'truck_capacity_kg': fallback_truck['capacity_tons'] * 1000,
                'cost_per_km': fallback_truck['cost_per_km'],
                'cost_per_kg': fallback_truck['cost_per_kg'],
                'total_estimated_cost': round(remaining_weight * fallback_truck['cost_per_kg'], 2)
            })

    return pd.DataFrame(allocations)
