import streamlit as st
import pandas as pd
from datetime import date
from utils import auth

st.set_page_config(page_title="Truck Delivery Optimizer", layout="wide")
auth.require_login_and_sidebar()

st.title("🚚 Truck Delivery Optimizer - Dashboard")
st.markdown(f"Welcome **{st.session_state['username'].capitalize()}** 👋")
st.markdown("Use the sidebar to navigate between different modules.")
st.markdown("---")

# Utility to safely read CSV files
def safe_read_csv(path):
    try:
        return pd.read_csv(path)
    except:
        return pd.DataFrame()

# Load CSVs
orders_df = safe_read_csv("data/orders.csv")
customers_df = safe_read_csv("data/customers.csv")
products_df = safe_read_csv("data/products.csv")
allocation_df = safe_read_csv("data/allocation.csv")
trucks_df = safe_read_csv("data/trucks.csv")

# Ensure orders have order_id
if not orders_df.empty and "order_id" not in orders_df.columns:
    orders_df["order_id"] = range(1, len(orders_df) + 1)

# Convert date fields to datetime.date
orders_df['delivery_date'] = pd.to_datetime(orders_df['delivery_date'], errors='coerce').dt.date
if not allocation_df.empty:
    allocation_df['delivery_date'] = pd.to_datetime(allocation_df['delivery_date'], errors='coerce').dt.date

# ========== 🔒 ADMIN DASHBOARD ==========
if st.session_state["role"] == "admin":
    st.subheader("📊 Overview Metrics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Orders", len(orders_df))
    col2.metric("Total Trucks", len(trucks_df))
    col3.metric("Total Customers", len(customers_df))

    st.markdown("### 🗓️ Select Delivery Date")
    selected_date = st.date_input("Select Delivery Date", date.today())

    if not orders_df.empty:
        daily_orders = orders_df[orders_df['delivery_date'] == selected_date]

        if daily_orders.empty:
            st.warning("No orders found for selected date.")
        else:
            # Merge customer and product names
            daily_orders = daily_orders.merge(customers_df[['customer_id', 'customer_name']], on='customer_id', how='left')
            daily_orders = daily_orders.merge(products_df[['product_id', 'product_name']], on='product_id', how='left')

            # Merge with allocation
            if not allocation_df.empty and 'truck_id' in allocation_df.columns:
                merged = daily_orders.merge(
                    allocation_df[['customer_id', 'delivery_date', 'truck_id']],
                    on=['customer_id', 'delivery_date'],
                    how='left'
                )
                merged['Status'] = merged['truck_id'].apply(
                    lambda x: f"Allocated (Truck {x})" if pd.notna(x) else "Not Allocated"
                )
            else:
                merged = daily_orders.copy()
                merged['Status'] = "Not Allocated"

            st.dataframe(merged[[ 'order_id', 'customer_name', 'product_name', 'num_boxes', 'delivery_date', 'Status' ]])
    else:
        st.info("No orders data available.")

# ========== 👤 USER DASHBOARD ==========
else:
    st.subheader("📦 Your Allocated Orders")
    username = st.session_state.get("username", "")
    customer_id = st.session_state.get("customer_id", None)

    if not orders_df.empty and 'placed_by' in orders_df.columns and customer_id is not None:
        user_orders = orders_df[
            (orders_df['placed_by'] == username) & (orders_df['customer_id'] == customer_id)
        ].copy()

        if not user_orders.empty and not allocation_df.empty:
            # Merge with allocation using customer_id + delivery_date
            allocated_orders = user_orders.merge(
                allocation_df[['customer_id', 'delivery_date', 'truck_id']],
                on=['customer_id', 'delivery_date'],
                how='inner'  # Only keep allocated
            )

            if not allocated_orders.empty:
                # Add product name
                allocated_orders = allocated_orders.merge(
                    products_df[['product_id', 'product_name']],
                    on='product_id', how='left'
                )
                allocated_orders['Status'] = allocated_orders['truck_id'].apply(
                    lambda x: f"Allocated (Truck {x})"
                )

                display_cols = ['order_id', 'product_name', 'num_boxes', 'delivery_date', 'Status']
                st.dataframe(allocated_orders[display_cols])
            else:
                st.info("ℹ️ You don't have any allocated orders yet.")
        else:
            st.info("ℹ️ You have not placed any orders.")
    elif 'placed_by' not in orders_df.columns:
        st.error("⚠️ 'placed_by' column not found in orders.csv.")
    else:
        st.info("ℹ️ No order data available.")
