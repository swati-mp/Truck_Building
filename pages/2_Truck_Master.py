import streamlit as st
st.set_page_config(page_title="Truck Master", layout="wide")

import pandas as pd
from utils import db_utils
from utils import auth
import time 

auth.require_login_and_sidebar()

st.title("🚛 Truck Master")

TRUCK_FILE = "trucks.csv"

# Load truck data
trucks_df = db_utils.load_csv(TRUCK_FILE)

# Auto-generate truck_id
def get_next_truck_id(df):
    if df.empty or "truck_id" not in df.columns:
        return 1
    try:
        return int(df["truck_id"].astype(int).max()) + 1
    except:
        return 1

# Add New Truck
with st.expander("➕ Add New Truck Type"):
    with st.form("add_truck_form", clear_on_submit=True):
        auto_id = get_next_truck_id(trucks_df)
        st.markdown(f"**Auto-generated Truck ID:** `{auto_id}`")

        truck_type = st.text_input("Truck Type (e.g., Mini Truck, Large Truck)")
        state = st.text_input("State (e.g., Maharashtra, Gujarat)")
        capacity_tons = st.number_input("Capacity (e.g., 5 Tons, 10 Tons)", min_value=0.0, step=0.5, format="%.2f")
        cost_per_km = st.number_input("Cost per KM (₹)", min_value=0.0, step=1.0, format="%.2f")
        fuel_efficiency_kmpl = st.number_input("Fuel Efficiency (KM per Litre)", min_value=1.0, step=0.5, format="%.2f")

        submitted = st.form_submit_button("Add Truck")

        if submitted:
            if truck_type and state and capacity_tons and cost_per_km and fuel_efficiency_kmpl:
                new_entry = pd.DataFrame([{
                    "truck_id": auto_id,
                    "truck_type": truck_type,
                    "state": state,
                    "capacity_tons": capacity_tons,
                    "cost_per_km": cost_per_km,
                    "fuel_efficiency_kmpl": fuel_efficiency_kmpl
                }])
                trucks_df = pd.concat([trucks_df, new_entry], ignore_index=True)
                db_utils.save_csv(trucks_df, TRUCK_FILE)
                st.success(f"✅ Truck '{truck_type}' added successfully with ID `{auto_id}`!")
            else:
                st.warning("⚠️ Please fill in all fields.")

# Show Truck List
st.subheader("🚚 Truck Types List")

if not trucks_df.empty:
    st.dataframe(trucks_df)

    with st.expander("🗑️ Delete Truck"):
        delete_id = st.text_input("Enter Truck ID to Delete")
        if st.button("Delete Truck"):
            if delete_id.isdigit() and int(delete_id) in trucks_df["truck_id"].astype(int).values:
                trucks_df = db_utils.delete_entry_by_id(trucks_df, "truck_id", int(delete_id))
                db_utils.save_csv(trucks_df, TRUCK_FILE)
                st.success(f"✅ Truck with ID '{delete_id}' deleted.")
                time.sleep(2) 
                st.rerun()
            else:
                st.warning("⚠️ Truck ID not found.")
else:
    st.info("ℹ️ No Truck available.")