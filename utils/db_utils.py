import os
import pandas as pd
import json
import numpy as np

# Base and data directories
try:
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
except NameError:
    BASE_DIR = os.getcwd()

DATA_DIR = os.path.join(BASE_DIR, 'data')
CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'config.json')


# ✅ Utility function: check file existence
def file_exists(filepath):
    return os.path.exists(os.path.join(DATA_DIR, filepath))


# Load CSV
def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            df.columns = [col.strip() for col in df.columns]
            return df
        except Exception as e:
            print(f"[ERROR] Failed to read {filename}: {e}")
            return pd.DataFrame()
    else:
        print(f"[WARN] File not found: {path}")
        return pd.DataFrame()

def save_csv(df, path):
    # Ensure the folder exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)

# Delete entry by ID
def delete_entry_by_id(df, id_column, delete_id):
    df[id_column] = df[id_column].astype(str)
    delete_id = str(delete_id)
    return df[df[id_column] != delete_id]

# Auto-incrementing ID
def get_next_id(df, id_column):
    if df.empty or id_column not in df.columns:
        return 1
    try:
        return int(df[id_column].astype(int).max()) + 1
    except:
        return 1

# Config JSON
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        return {"min_load_percent": 60, "max_load_percent": 95}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Debugging truck assignment
def debug_truck_assignment(total_weight, truck_capacity, config):
    suitable_trucks = truck_capacity[
        (truck_capacity['min_capacity_kg'] <= total_weight) &
        (total_weight <= truck_capacity['max_capacity_kg'])
    ].sort_values(by='capacity_kg')

    if suitable_trucks.empty:
        return "❌ No Suitable Truck Found"
    else:
        truck = suitable_trucks.iloc[0]
        utilization = round((total_weight / truck['capacity_kg']) * 100, 2)
        return (
            f"Chosen Truck: {truck['truck_type']} | Total Weight: {total_weight} kg | "
            f"Utilization: {utilization}% of {truck['capacity_kg']} kg (Truck Capacity)"
        )

def print_allocation_debug(customer_summary, truck_capacity, config):
    debug_list = []
    for _, row in customer_summary.iterrows():
        debug_info = debug_truck_assignment(row['total_weight_kg'], truck_capacity, config)
        debug_list.append({
            "customer_id": row['customer_id'],
            "customer_name": row['customer_name'],
            "total_weight_kg": row['total_weight_kg'],
            "debug_info": debug_info
        })
    return pd.DataFrame(debug_list)

# Group orders by assigned truck
def group_orders_by_truck(allocation_df, orders_df):
    grouped_orders = pd.merge(orders_df, allocation_df[['customer_id', 'assigned_truck_type']], on='customer_id', how='left')
    grouped = grouped_orders.groupby('assigned_truck_type').apply(
        lambda g: g[['order_id', 'customer_id', 'product_id', 'num_boxes']].reset_index(drop=True)
    ).reset_index()
    return grouped

# # Truck allocation summary
# # def generate_truck_allocation_details(allocation_df, orders_df, customers_df, products_df):
# #     merged_orders = pd.merge(orders_df, customers_df, on="customer_id", how="left")
# #     merged_orders = pd.merge(merged_orders, products_df, on="product_id", how="left")
# #     merged_orders = pd.merge(
# #         merged_orders,
# #         allocation_df[['customer_id', 'assigned_truck_type']],
# #         on="customer_id",
# #         how="left"
# #     )

# #     grouped = merged_orders.groupby(['assigned_truck_type', 'customer_name']).agg({
# #         'product_name': lambda x: ', '.join(sorted(set(x))),
# #         'num_boxes': 'sum',
# #         'weight_per_box': 'sum',
# #         'size_per_box': 'sum'
# #     }).reset_index()

# #     grouped = grouped.rename(columns={
# #         'num_boxes': 'total_boxes',
# #         'weight_per_box': 'total_weight',
# #         'size_per_box': 'total_volume'
# #     })

# #     return grouped.sort_values(by=['assigned_truck_type', 'customer_name'])
# def generate_truck_allocation_details(allocation_df, orders_df, customers_df, products_df):
#     # Convert merge keys to string to avoid type mismatch error
#     orders_df['customer_id'] = orders_df['customer_id'].astype(str)
#     customers_df['customer_id'] = customers_df['customer_id'].astype(str)
#     orders_df['product_id'] = orders_df['product_id'].astype(str)
#     products_df['product_id'] = products_df['product_id'].astype(str)
#     allocation_df['customer_id'] = allocation_df['customer_id'].astype(str)

#     # Merge in correct order
#     merged_orders = pd.merge(orders_df, customers_df, on="customer_id", how="left")
#     merged_orders = pd.merge(merged_orders, products_df, on="product_id", how="left")
#     merged_orders = pd.merge(
#         merged_orders,
#         allocation_df[['customer_id', 'assigned_truck_type']],
#         on="customer_id",
#         how="left"
#     )

#     grouped = merged_orders.groupby(['assigned_truck_type', 'customer_name']).agg({
#         'product_name': lambda x: ', '.join(sorted(set(x))),
#         'num_boxes': 'sum',
#         'weight_per_box': 'sum',
#         'size_per_box': 'sum'
#     }).reset_index()

#     grouped = grouped.rename(columns={
#         'num_boxes': 'total_boxes',
#         'weight_per_box': 'total_weight',
#         'size_per_box': 'total_volume'
#     })

#     return grouped.sort_values(by=['assigned_truck_type', 'customer_name'])


# FILO allocation grouping
def group_orders_by_truck_filo(allocation_results, filtered_orders, trucks_df, config):
    trucks_df = trucks_df.copy()
    trucks_df["min_capacity_kg"] = trucks_df["capacity_tons"] * 1000 * (config['min_load_percent'] / 100)
    trucks_df["max_capacity_kg"] = trucks_df["capacity_tons"] * 1000 * (config['max_load_percent'] / 100)
    trucks_df["cost_per_kg"] = trucks_df["cost_per_km"] / trucks_df["capacity_tons"]

    merged = pd.merge(filtered_orders, allocation_results[['customer_id']], on='customer_id', how='inner')
    merged = merged.sort_values(by='delivery_date', ascending=False)

    result_rows = []
    used_trucks = []

    total_weight = merged["num_boxes"].sum() * 10  # Adjust if product-specific weights available

    trucks_sorted = trucks_df.sort_values(by='cost_per_kg')

    for _, truck in trucks_sorted.iterrows():
        if total_weight < truck['min_capacity_kg']:
            continue
        if total_weight > truck['max_capacity_kg']:
            continue

        used_trucks.append({
            "truck_type": truck["truck_type"],
            "capacity_tons": truck["capacity_tons"],
            "cost_per_km": truck["cost_per_km"],
            "allocated_weight_kg": total_weight,
            "estimated_cost": round(total_weight * truck["cost_per_kg"], 2)
        })
        break

    return pd.DataFrame(used_trucks)

# Get assigned warehouse for customer
def get_customer_warehouse(customer_row, warehouses_df):
    state = customer_row.get("state")
    warehouse = warehouses_df[warehouses_df["state"] == state]
    if not warehouse.empty:
        return warehouse.iloc[0]["latitude"], warehouse.iloc[0]["longitude"]
    else:
        return None, None
