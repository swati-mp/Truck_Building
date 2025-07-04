import streamlit as st
st.set_page_config(page_title="Truck Allocation Report", layout="wide")

import pandas as pd
import folium
from streamlit_folium import st_folium

# ✅ Save the map as HTML and offer download
from io import BytesIO
import base64

from utils import db_utils, logic, map_utils
from utils import auth

auth.require_login_and_sidebar()

# # Access role
# role = st.session_state.get("role", "admin")

st.title("📦🚛 Truck Allocation & Route Optimization")

# Load data
orders_df = db_utils.load_csv("orders.csv")
customers_df = db_utils.load_csv("customers.csv")
products_df = db_utils.load_csv("products.csv")
trucks_df = db_utils.load_csv("trucks.csv")
warehouses_df = db_utils.load_csv("warehouses.csv")
config = db_utils.load_config()

# Check for missing files
if orders_df.empty or customers_df.empty or products_df.empty or trucks_df.empty or warehouses_df.empty:
    st.warning("⚠️ Ensure all data files exist: Customers, Products, Trucks, Orders, and Warehouses.")
else:
    st.subheader("📅 Select Delivery Date")
    selected_date = st.date_input("Delivery Date")

    if "allocation_results" not in st.session_state:
        st.session_state.allocation_results = None
        st.session_state.route_df = None
        st.session_state.filtered_orders = None
        st.session_state.customer_summary = None
        st.session_state.filo_allocated_df = None

    if st.button("🚚 Run Truck Allocation"):
        orders_df['delivery_date'] = pd.to_datetime(orders_df['delivery_date']).dt.date
        selected_date = pd.to_datetime(selected_date).date()
        filtered_orders = orders_df[orders_df['delivery_date'] == selected_date]

        if filtered_orders.empty:
            st.warning("⚠️ No orders found for the selected date.")
        else:
            with st.spinner("🔄 Running Allocation Logic..."):
                # ✅ Pass warehouses_df to all relevant logic functions
                customer_summary = logic.prepare_customer_summary(filtered_orders, customers_df, products_df)
                allocation_results, route_df = logic.run_allocation(
                    filtered_orders, customers_df, products_df, trucks_df, config, warehouses_df
                )
                filo_allocated_df = logic.filo_grouped_truck_allocation(
                    filtered_orders, customers_df, products_df, trucks_df, config,
                    fuel_price_per_litre=90.0, mileage_kmpl=4.0, warehouses_df=warehouses_df
                )
                # filo_allocated_df = logic.filo_grouped_truck_allocation(
                #     filtered_orders, customers_df, products_df, trucks_df, config,
                #     warehouses_df=warehouses_df
                # )


                # Save to session
                st.session_state.allocation_results = allocation_results
                st.session_state.route_df = route_df
                st.session_state.filtered_orders = filtered_orders
                st.session_state.customer_summary = customer_summary
                st.session_state.filo_allocated_df = filo_allocated_df

                st.success("✅ Allocation Completed!")

    # If allocation already run
    if st.session_state.allocation_results is not None:
        st.subheader("📄 Customer Report")

        customer_report_df = st.session_state.allocation_results.drop(columns=["assigned_truck_type"], errors="ignore")
        st.dataframe(customer_report_df)

    # ✅ Add download button
        st.download_button(
            label="⬇️ Download Customer Report (CSV)",
            data=customer_report_df.to_csv(index=False).encode('utf-8'),
            file_name="customer_report.csv",
            mime="text/csv"
        )

        st.subheader("📑 Detailed Truck Allocations (Customer/Product-wise)")
        detailed_allocation = db_utils.generate_truck_allocation_details(
            st.session_state.allocation_results,
            st.session_state.filtered_orders,
            customers_df,
            products_df
        ).drop(columns=["assigned_truck_type"], errors="ignore")
        st.dataframe(detailed_allocation)

        # ✅ Add download button
        st.download_button(
            label="⬇️ Download Detailed Allocation (CSV)",
            data=detailed_allocation.to_csv(index=False).encode('utf-8'),
            file_name="detailed_truck_allocation.csv",
            mime="text/csv"
        )

        st.subheader("📦 FILO-based Truck Allocations (Route Aware + Fuel Cost + Emissions)")
        st.dataframe(st.session_state.filo_allocated_df)

        st.download_button(
            "⬇️ Download FILO Truck Allocation CSV",
            data=st.session_state.filo_allocated_df.to_csv(index=False),
            file_name="filo_truck_allocation.csv",
            mime="text/csv"
        )

        # # 🗺️ Route Map with Warehouse Origin
        st.subheader("🗺️ Route Map (FILO with Color-coded Trucks)")

        filo_map = map_utils.create_colored_route_map(
            st.session_state.filo_allocated_df, customers_df, warehouses_df
        )
        st_folium(filo_map, width=900)

        # Save map to HTML in memory
        map_html = filo_map.get_root().render()
        map_buffer = BytesIO(map_html.encode("utf-8"))

        # Download button for HTML map
        st.download_button(
            label="⬇️ Download Route Map (HTML)",
            data=map_buffer,
            file_name="filo_route_map.html",
            mime="text/html"
        )




