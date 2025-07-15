import streamlit as st
import pandas as pd
from utils import db_utils, auth

st.set_page_config(page_title="Order Transactions", layout="wide")
auth.require_login_and_sidebar()

st.title("📝 Order Transactions")

# File paths
ORDER_FILE = "orders.csv"
CUSTOMER_FILE = "customers.csv"
PRODUCT_FILE = "products.csv"

# Load data
orders_df = db_utils.load_csv(ORDER_FILE)
customers_df = db_utils.load_csv(CUSTOMER_FILE)
products_df = db_utils.load_csv(PRODUCT_FILE)

# Join to get names
if not orders_df.empty:
    merged_df = orders_df.copy()

    merged_df = merged_df.merge(customers_df[["customer_id", "customer_name"]],
                                 on="customer_id", how="left")
    merged_df = merged_df.merge(products_df[["product_id", "product_name"]],
                                 on="product_id", how="left")

    # Format columns
    merged_df["order_id"] = merged_df["order_id"].astype(str)
    merged_df["delivery_date"] = pd.to_datetime(merged_df["delivery_date"], errors='coerce').dt.date

    st.subheader("📋 All Order Transactions")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_customer = st.selectbox("Filter by Customer", options=["All"] + sorted(merged_df["customer_name"].dropna().unique().tolist()))
    with col2:
        selected_product = st.selectbox("Filter by Product", options=["All"] + sorted(merged_df["product_name"].dropna().unique().tolist()))
    with col3:
        search_order = st.text_input("🔍 Search by Order ID")

    # Apply filters
    filtered_df = merged_df.copy()
    if selected_customer != "All":
        filtered_df = filtered_df[filtered_df["customer_name"] == selected_customer]
    if selected_product != "All":
        filtered_df = filtered_df[filtered_df["product_name"] == selected_product]
    if search_order:
        filtered_df = filtered_df[filtered_df["order_id"].str.contains(search_order.strip(), case=False)]

    # Columns to display
    display_cols = ["order_id", "customer_name", "product_name", "num_boxes", "delivery_date", "placed_by"]
    st.dataframe(filtered_df[display_cols], use_container_width=True)

    # Delete Section
    with st.expander("🗑️ Delete Order"):
        delete_id = st.text_input("Enter Order ID to Delete")
        if st.button("Delete Order"):
            if delete_id in orders_df["order_id"].astype(str).values:
                orders_df = db_utils.delete_entry_by_id(orders_df, "order_id", delete_id)
                db_utils.save_csv(orders_df, ORDER_FILE)
                st.success(f"✅ Order '{delete_id}' deleted successfully!")
                st.rerun()
            else:
                st.warning("⚠️ Order ID not found.")

else:
    st.info("ℹ️ No orders available yet.")
