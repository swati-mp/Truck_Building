import streamlit as st
st.set_page_config(page_title="Truck Delivery Optimizer", layout="wide")  # ✅ MUST be first Streamlit command

from utils import auth
import pandas as pd
from datetime import date

# ✅ Enforce login and show sidebar with logout
auth.require_login_and_sidebar()

# 🚚 Main Page Content
st.title("🚚 Truck Building Optimizer - Dashboard")
st.markdown(f"Welcome **{st.session_state['username'].capitalize()}** 👋")
st.markdown("Use the sidebar to navigate between different modules.")
st.markdown("---")

# 🔒 Admin-only dashboard
if st.session_state["role"] == "admin":
    st.subheader("📊 Overview Metrics")

    try:
        orders_df = pd.read_csv("data/orders.csv")
        trucks_df = pd.read_csv("data/trucks.csv")
        customers_df = pd.read_csv("data/customers.csv")
    except:
        orders_df = pd.DataFrame()
        trucks_df = pd.DataFrame()
        customers_df = pd.DataFrame()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Orders", len(orders_df))
    col2.metric("Total Trucks", len(trucks_df))
    col3.metric("Total Customers", len(customers_df))

    st.markdown("### 🗓️ Today's Orders")
    today = date.today()
    if not orders_df.empty:
        orders_df['delivery_date'] = pd.to_datetime(orders_df['delivery_date']).dt.date
        today_orders = orders_df[orders_df['delivery_date'] == today]
        st.dataframe(today_orders)
    else:
        st.info("No orders data available.")
else:
    st.warning("You do not have access to the admin dashboard.")
