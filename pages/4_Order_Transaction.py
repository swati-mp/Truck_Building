import streamlit as st
st.set_page_config(page_title="Order Transactions", layout="wide")

import pandas as pd
from utils import db_utils
from utils import auth

auth.require_login_and_sidebar()

# Access role
role = st.session_state.get("role", "admin")

st.title("📝 Order Transactions")

# File paths
ORDER_FILE = "orders.csv"
CUSTOMER_FILE = "customers.csv"
PRODUCT_FILE = "products.csv"

# Load data
orders_df = db_utils.load_csv(ORDER_FILE)
customers_df = db_utils.load_csv(CUSTOMER_FILE)
products_df = db_utils.load_csv(PRODUCT_FILE)

# Add New Order Section
with st.expander("➕ Add New Order"):
    with st.form("add_order_form", clear_on_submit=True):
        # Auto-generate Order ID
        if not orders_df.empty and 'order_id' in orders_df.columns:
            max_id = pd.to_numeric(orders_df['order_id'], errors='coerce').max()
            order_id = int(max_id) + 1
        else:
            order_id = 1001

        st.markdown(f"**Auto-generated Order ID:** `{order_id}`")

        customer_id = st.selectbox("Customer ID", customers_df["customer_id"] if not customers_df.empty else [])
        product_id = st.selectbox("Product ID", products_df["product_id"] if not products_df.empty else [])
        num_boxes = st.number_input("Quantity (Number of Boxes)", min_value=1, step=1)
        delivery_date = st.date_input("Delivery Date")

        submitted = st.form_submit_button("Add Order")

        if submitted:
            if customer_id and product_id and num_boxes and delivery_date:
                new_entry = pd.DataFrame([{
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "num_boxes": num_boxes,
                    "delivery_date": delivery_date
                }])
                orders_df = pd.concat([orders_df, new_entry], ignore_index=True)
                db_utils.save_csv(orders_df, ORDER_FILE)
                st.success(f"✅ Order '{order_id}' added successfully!")
            else:
                st.warning("⚠️ Please fill in all fields.")

# Orders List Section
st.subheader("📋 Orders List")

if not orders_df.empty:
    st.dataframe(orders_df)

    with st.expander("🗑️ Delete Order"):
        delete_id = st.text_input("Enter Order ID to Delete")
        if st.button("Delete Order"):
            if delete_id in orders_df["order_id"].astype(str).values:
                orders_df = db_utils.delete_entry_by_id(orders_df, "order_id", delete_id)
                db_utils.save_csv(orders_df, ORDER_FILE)
                st.success(f"✅ Order '{delete_id}' deleted.")
            else:
                st.warning("⚠️ Order ID not found.")
else:
    st.info("ℹ️ No orders available. Please add orders.")
