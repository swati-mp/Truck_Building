import os
import json
import pandas as pd
import numpy as np

# Define the path to the data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.json')

def load_csv(filename):
    """Load a CSV file from the data directory with cleaned column names."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        df = pd.read_csv(path)
        df.columns = [col.strip() for col in df.columns]  # 🚀 always clean headers
        return df
    else:
        return pd.DataFrame()

def save_csv(df, filename):
    """Save a DataFrame to a CSV file in the data directory."""
    path = os.path.join(DATA_DIR, filename)
    df.to_csv(path, index=False)

def delete_entry_by_id(df, id_column, delete_id):
    # Ensure proper comparison (in case of int vs str mismatch)
    df[id_column] = df[id_column].astype(str)
    delete_id = str(delete_id)

    return df[df[id_column] != delete_id]

def load_config():
    """Load configuration from JSON file or return default values."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        return {"min_load_percent": 60, "max_load_percent": 95}  # Default values

def save_config(config):
    """Save configuration to JSON file."""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def debug_truck_assignment(total_weight, truck_capacity, config):
    """Debug helper: Shows how truck is selected for a given total weight."""
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
    """Print debug info for all customer allocations."""
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

def group_orders_by_truck(allocation_df, orders_df):
    """Group orders by assigned truck type for display."""
    grouped_orders = pd.merge(orders_df, allocation_df[['customer_id', 'assigned_truck_type']], on='customer_id', how='left')
    grouped = grouped_orders.groupby('assigned_truck_type').apply(
        lambda g: g[['order_id', 'customer_id', 'product_id', 'num_boxes']].reset_index(drop=True)
    ).reset_index()
    return grouped

def generate_truck_allocation_details(allocation_df, orders_df, customers_df, products_df):
    merged_orders = pd.merge(orders_df, customers_df, on="customer_id", how="left")
    merged_orders = pd.merge(merged_orders, products_df, on="product_id", how="left")
    merged_orders = pd.merge(merged_orders, allocation_df[['customer_id', 'assigned_truck_type']], on="customer_id", how="left")

    detailed_allocation = merged_orders[[
        'assigned_truck_type', 'order_id', 'customer_name', 'product_name', 'num_boxes', 'weight_per_box', 'size_per_box'
    ]]
    return detailed_allocation.sort_values(by=['assigned_truck_type', 'customer_name'])

def group_orders_by_truck_filo(allocation_results, filtered_orders, trucks_df, config):
    trucks_df = trucks_df.copy()
    trucks_df["min_capacity_kg"] = trucks_df["capacity_tons"] * 1000 * (config['min_load_percent'] / 100)
    trucks_df["max_capacity_kg"] = trucks_df["capacity_tons"] * 1000 * (config['max_load_percent'] / 100)

    # Add truck cost per kg for optimization
    trucks_df["cost_per_kg"] = trucks_df["cost_per_km"] / trucks_df["capacity_tons"]

    # Merge order details
    merged = pd.merge(filtered_orders, allocation_results[['customer_id']], on='customer_id', how='inner')
    merged = merged.sort_values(by='delivery_date', ascending=False)  # FILO (reverse by date or add delivery priority)

    result_rows = []
    used_trucks = []

    total_weight = merged["num_boxes"].sum() * 10  # Assuming 10kg per box; modify as per your products

    # Sort trucks by cost_per_kg ascending (cheapest first)
    trucks_sorted = trucks_df.sort_values(by='cost_per_kg')

    for _, truck in trucks_sorted.iterrows():
        if total_weight < truck['min_capacity_kg']:
            continue

        if total_weight > truck['max_capacity_kg']:
            continue  # current truck can't fully accommodate, move to next truck

        used_trucks.append({
            "truck_type": truck["truck_type"],
            "capacity_tons": truck["capacity_tons"],
            "cost_per_km": truck["cost_per_km"],
            "allocated_weight_kg": total_weight,
            "estimated_cost": round(total_weight * truck["cost_per_kg"], 2)
        })
        break  # assign one truck only for this simplified example

    return pd.DataFrame(used_trucks)

