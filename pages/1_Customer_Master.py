import streamlit as st
st.set_page_config(page_title="Customer Master", layout="wide")

from utils import auth, db_utils
from geopy.geocoders import Nominatim
import pandas as pd

auth.require_login_and_sidebar()

# Access role:
role = st.session_state.get("role", "admin") 

st.title("🚚 Customer Master")

CUSTOMER_FILE = "customers.csv"

# Load customer data
customers_df = db_utils.load_csv(CUSTOMER_FILE)

geolocator = Nominatim(user_agent="truck_delivery_optimizer")

def fetch_coordinates(address):
    try:
        location = geolocator.geocode(address)
        return location.latitude, location.longitude if location else (None, None)
    except:
        return None, None

def get_next_customer_id(df):
    if df.empty:
        return 1
    try:
        return int(df["customer_id"].astype(int).max()) + 1
    except:
        return 1  # fallback in case of invalid data

with st.expander("➕ Add New Customer"):
    with st.form("add_customer_form", clear_on_submit=True):
        auto_id = get_next_customer_id(customers_df)
        st.markdown(f"**Auto-generated Customer ID:** `{auto_id}`")
        name = st.text_input("Customer Name")
        address = st.text_input("Full Address")
        submitted = st.form_submit_button("Add Customer")

        if submitted:
            if name and address:
                latitude, longitude = fetch_coordinates(address)
                if latitude and longitude:
                    new_entry = pd.DataFrame([{
                        "customer_id": auto_id,
                        "customer_name": name,
                        "address": address,
                        "latitude": latitude,
                        "longitude": longitude
                    }])
                    customers_df = pd.concat([customers_df, new_entry], ignore_index=True)
                    db_utils.save_csv(customers_df, CUSTOMER_FILE)
                    st.success(f"✅ Customer '{name}' added successfully with ID `{auto_id}`!")
                else:
                    st.error("❌ Could not fetch coordinates for the provided address.")
            else:
                st.warning("⚠️ Please fill in all fields.")

st.subheader("📋 Customer List")

if not customers_df.empty:
    st.dataframe(customers_df)

    with st.expander("🗑️ Delete Customer"):
        delete_id = st.text_input("Enter Customer ID to Delete")
        if st.button("Delete"):
            if delete_id in customers_df["customer_id"].astype(str).values:
                customers_df = db_utils.delete_entry_by_id(customers_df, "customer_id", delete_id)
                db_utils.save_csv(customers_df, CUSTOMER_FILE)
                st.success(f"✅ Customer with ID '{delete_id}' deleted.")
            else:
                st.warning("⚠️ Customer ID not found.")
else:
    st.info("ℹ️ No customers available. Please add customers.")
