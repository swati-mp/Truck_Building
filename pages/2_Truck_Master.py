import streamlit as st
st.set_page_config(page_title="Truck Master", layout="wide")

import pandas as pd
from utils import db_utils
from utils import auth

auth.require_login_and_sidebar()

# Access role:
role = st.session_state.get("role", "admin") 

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

with st.expander("➕ Add New Truck Type"):
    with st.form("add_truck_form", clear_on_submit=True):
        auto_id = get_next_truck_id(trucks_df)
        st.markdown(f"**Auto-generated Truck ID:** `{auto_id}`")

        truck_type = st.text_input("Truck Type (e.g., 5 Tons, 10 Tons)")
        capacity_tons = st.number_input("Capacity (tons)", min_value=0.0, step=0.5, format="%.2f")
        cost_per_km = st.number_input("Cost per KM (₹)", min_value=0.0, step=1.0, format="%.2f")
        fuel_efficiency_kmpl = st.number_input("Fuel Efficiency (KM per Litre)", min_value=1.0, step=0.5, format="%.2f")

        submitted = st.form_submit_button("Add Truck")

        if submitted:
            if truck_type and capacity_tons and cost_per_km and fuel_efficiency_kmpl:
                new_entry = pd.DataFrame([{
                    "truck_id": auto_id,
                    "truck_type": truck_type,
                    "capacity_tons": capacity_tons,
                    "cost_per_km": cost_per_km,
                    "fuel_efficiency_kmpl": fuel_efficiency_kmpl
                }])
                trucks_df = pd.concat([trucks_df, new_entry], ignore_index=True)
                db_utils.save_csv(trucks_df, TRUCK_FILE)
                st.success(f"✅ Truck '{truck_type}' added successfully with ID `{auto_id}`!")
            else:
                st.warning("⚠️ Please fill in all fields.")

st.subheader("🚚 Truck Types List")

if not trucks_df.empty:
    st.dataframe(trucks_df)

    with st.expander("🗑️ Delete Truck Type"):
        delete_type = st.text_input("Enter Truck Type to Delete")
        if st.button("Delete Truck"):
            if delete_type in trucks_df["truck_type"].values:
                trucks_df = db_utils.delete_entry_by_id(trucks_df, "truck_type", delete_type)
                db_utils.save_csv(trucks_df, TRUCK_FILE)
                st.success(f"✅ Truck Type '{delete_type}' deleted.")
            else:
                st.warning("⚠️ Truck Type not found.")
else:
    st.info("ℹ️ No truck types available. Please add trucks.")


'''
truck.csv
truck_id,truck_type,capacity_tons,cost_per_km
1,Mini Truck,1.0,8.0
2,Large Truck,10.0,25.0
3,Tempo,0.8,6.5
4,Heavy Duty Truck,15.0,35.0
5,Medium Truck,1.5,12.0

'''