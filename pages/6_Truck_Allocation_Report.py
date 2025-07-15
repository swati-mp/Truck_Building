import streamlit as st
st.set_page_config(page_title="Truck Allocation Report", layout="wide")

import pandas as pd
import folium
from streamlit_folium import st_folium

from io import BytesIO
import os
from datetime import date

from utils import db_utils, logic, map_utils, auth

auth.require_login_and_sidebar()

st.title("📦🚛 Truck Allocation & Route Optimization")

# Load data once using caching
@st.cache_data
def load_all_data():
    return (
        db_utils.load_csv("orders.csv"),
        db_utils.load_csv("customers.csv"),
        db_utils.load_csv("products.csv"),
        db_utils.load_csv("trucks.csv"),
        db_utils.load_csv("warehouses.csv"),
        db_utils.load_config()
    )

orders_df, customers_df, products_df, trucks_df, warehouses_df, config = load_all_data()

if orders_df.empty or customers_df.empty or products_df.empty or trucks_df.empty or warehouses_df.empty:
    st.warning("⚠️ Ensure all data files exist: Customers, Products, Trucks, Orders, and Warehouses.")
    st.stop()

if "allocation_cache" not in st.session_state:
    st.session_state["allocation_cache"] = {}

st.subheader("📅 Select Delivery Date")
selected_date = st.date_input("Delivery Date")
date_key = str(selected_date)

@st.cache_data(show_spinner="🔄 Running FILO allocation...", hash_funcs={pd.DataFrame: lambda _: None})
def run_filo_allocation(filtered_orders, customers_df, products_df, trucks_df, config, warehouses_df):
    return logic.filo_grouped_truck_allocation(
        filtered_orders=filtered_orders,
        customers_df=customers_df,
        products_df=products_df,
        trucks_df=trucks_df,
        config=config,
        fuel_price_per_litre=90.0,
        mileage_kmpl=4.0,
        warehouses_df=warehouses_df
    )

run_triggered = st.button("🚚 Run Allocation")

if run_triggered:
    orders_df['delivery_date'] = pd.to_datetime(orders_df['delivery_date'], errors='coerce').dt.date
    selected_date = pd.to_datetime(selected_date).date()
    filtered_orders = orders_df[orders_df['delivery_date'] == selected_date]

    if filtered_orders.empty:
        st.warning("⚠️ No orders found for the selected date.")
    else:
        with st.spinner("🔄 Running Allocation Logic..."):
            customer_summary = logic.prepare_customer_summary(filtered_orders, customers_df, products_df)

            allocation_results, route_df = logic.run_allocation(
                filtered_orders, customers_df, products_df, trucks_df, config, warehouses_df
            )

            filo_allocated_df = run_filo_allocation(
                filtered_orders, customers_df, products_df, trucks_df, config, warehouses_df
            )

            db_utils.save_csv(allocation_results, "data/allocation_summary.csv")

            st.session_state["allocation_cache"][date_key] = {
                "filtered_orders": filtered_orders,
                "customer_summary": customer_summary,
                "route_df": route_df,
                "filo_allocated_df": filo_allocated_df,
                "allocation_results": allocation_results
            }

        st.success("✅ Truck Allocation Completed and Saved.")

# Always load from session state (persist until new Run Allocation)
cached_data = st.session_state["allocation_cache"].get(date_key)

if cached_data:
    allocation_results = cached_data["allocation_results"]
    customer_summary = cached_data["customer_summary"]
    filtered_orders = cached_data["filtered_orders"]
    filo_df = cached_data["filo_allocated_df"]

    st.subheader("📄 Customer Report")
    customer_report_df = allocation_results.drop(columns=["assigned_truck_type"], errors="ignore")
    st.dataframe(customer_report_df)
    st.download_button("⬇️ Download Customer Report (CSV)", customer_report_df.to_csv(index=False), file_name="customer_report.csv")

    # st.subheader("📑 Detailed Truck Allocations (Customer/Product-wise)")
    # detailed_allocation = db_utils.generate_truck_allocation_details(
    #     allocation_results, filtered_orders, customers_df, products_df
    # ).drop(columns=["assigned_truck_type"], errors="ignore")
    # st.dataframe(detailed_allocation)
    # st.download_button("⬇️ Download Detailed Allocation (CSV)", detailed_allocation.to_csv(index=False), file_name="detailed_truck_allocation.csv")

    st.subheader("📦 FILO-based Truck Allocations (Route Aware + Fuel Cost + Emissions)")
    if filo_df is not None and not filo_df.empty:
        filo_df['delivery_date'] = pd.to_datetime(filo_df['delivery_date']).dt.date
        filtered_filo_df = filo_df[filo_df['delivery_date'] == selected_date]

        if not filtered_filo_df.empty:
            st.dataframe(filtered_filo_df)
            st.download_button("⬇️ Download FILO Truck Allocation CSV", filtered_filo_df.to_csv(index=False), file_name=f"filo_truck_allocation_{selected_date}.csv")

            st.subheader("🗺️ Route Map (FILO with Color-coded Trucks)")
            filo_map = map_utils.create_colored_route_map(filtered_filo_df, customers_df, warehouses_df)
            st_folium(filo_map, width=900)

            map_html = filo_map.get_root().render()
            st.download_button("⬇️ Download Route Map (HTML)", BytesIO(map_html.encode("utf-8")), file_name="filo_route_map.html")
        else:
            st.info("❌ No trucks were allocated based on FILO logic for the selected date.")
    else:
        st.info("❌ No FILO allocation data available.")
