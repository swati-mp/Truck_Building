import streamlit as st
from utils import auth, db_utils
from geopy.geocoders import Nominatim
import pandas as pd
from io import BytesIO
import base64
import os

st.set_page_config(page_title="Customer Master", layout="wide")
auth.require_login_and_sidebar()

st.title("👤 Customer Profile")

# Constants
CUSTOMER_FILE = "customers.csv"
ORDERS_FILE = "orders.csv"
PRODUCT_FILE = "products.csv"
ALLOCATION_FILE = "allocation.csv"
geolocator = Nominatim(user_agent="truck_delivery_optimizer")

# Session info
role = st.session_state.get("role")
username = st.session_state.get("username")
customer_id = st.session_state.get("customer_id")

# Load data
customers_df = db_utils.load_csv(CUSTOMER_FILE)
orders_df = db_utils.load_csv(ORDERS_FILE)
products_df = db_utils.load_csv(PRODUCT_FILE)
allocation_df = db_utils.load_csv(ALLOCATION_FILE) if os.path.exists(os.path.join("data", ALLOCATION_FILE)) else pd.DataFrame()

# Check for required column
if "customer_id" not in customers_df.columns:
    st.error("❌ 'customer_id' column missing in customers.csv")
    st.stop()

# ========== ADMIN ==========
if role == "admin":
    st.subheader("📋 Customer List")

    if not customers_df.empty:
        st.dataframe(customers_df)

        def to_excel(df):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            writer.close()
            return output.getvalue()

        def get_table_download_link_excel(df, filename):
            val = to_excel(df)
            b64 = base64.b64encode(val).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}.xlsx">🗕️ Download Excel</a>'
            return href

        st.markdown(get_table_download_link_excel(customers_df, "customers"), unsafe_allow_html=True)

        with st.expander("➕ Add New Customer"):
            with st.form("add_customer_form", clear_on_submit=True):
                new_id = db_utils.get_next_id(customers_df, "customer_id")
                st.markdown(f"**Auto-generated Customer ID:** `{new_id}`")
                name = st.text_input("Customer Name")
                address = st.text_input("Full Address")
                phone = st.text_input("Phone")
                email = st.text_input("Email")
                submitted = st.form_submit_button("Add Customer")

                if submitted:
                    if name and address and phone and email:
                        try:
                            location = geolocator.geocode(address)
                            lat, lon = (location.latitude, location.longitude) if location else (None, None)
                        except:
                            lat, lon = None, None

                        if lat and lon:
                            new_row = pd.DataFrame([{
                                "customer_id": new_id,
                                "customer_name": name,
                                "address": address,
                                "latitude": lat,
                                "longitude": lon,
                                "phone": phone,
                                "email": email
                            }])
                            customers_df = pd.concat([customers_df, new_row], ignore_index=True)
                            db_utils.save_csv(customers_df, CUSTOMER_FILE)
                            st.success(f"✅ Customer '{name}' added successfully!")
                        else:
                            st.error("❌ Failed to fetch coordinates.")
                    else:
                        st.warning("⚠️ All fields are required.")

        with st.expander("🗑️ Delete Customer"):
            delete_id = st.text_input("Enter Customer ID to Delete")
            if st.button("Delete"):
                if delete_id in customers_df["customer_id"].astype(str).values:
                    customers_df = db_utils.delete_entry_by_id(customers_df, "customer_id", delete_id)
                    db_utils.save_csv(customers_df, CUSTOMER_FILE)
                    st.success(f"✅ Customer ID '{delete_id}' deleted.")
                else:
                    st.warning("⚠️ Customer ID not found.")

    else:
        st.info("ℹ️ No customer data available.")

# ========== USER ==========
else:
    st.subheader("👤 Your Information")

    user_data = customers_df[customers_df["customer_id"] == customer_id]

    if not user_data.empty:
        user_row = user_data.iloc[0]

        st.markdown(f"""
        - **Customer ID:** `{user_row['customer_id']}`
        - **Name:** {user_row['customer_name']}
        - **Username:** `{username}`
        - **Phone:** {str(user_row.get('phone', 'N/A')).split('.')[0]}
        - **Email:** {user_row.get('email', 'N/A')}
        - **Address:** {user_row['address']}
        - **Latitude:** {user_row['latitude']}
        - **Longitude:** {user_row['longitude']}
        """)

        with st.expander("✏️ Edit Contact Details"):
            with st.form("edit_contact_form"):
                new_address = st.text_input("New Address", value=user_row['address'])
                new_phone = st.text_input("Phone", value=str(user_row.get('phone', '')))
                new_email = st.text_input("Email", value=user_row.get('email', ''))
                update = st.form_submit_button("Update")

                if update:
                    try:
                        location = geolocator.geocode(new_address)
                        lat, lon = (location.latitude, location.longitude) if location else (None, None)
                    except:
                        lat, lon = None, None

                    if lat and lon:
                        customers_df.loc[customers_df["customer_id"] == customer_id, "address"] = new_address
                        customers_df.loc[customers_df["customer_id"] == customer_id, "latitude"] = lat
                        customers_df.loc[customers_df["customer_id"] == customer_id, "longitude"] = lon
                        customers_df.loc[customers_df["customer_id"] == customer_id, "phone"] = new_phone
                        customers_df.loc[customers_df["customer_id"] == customer_id, "email"] = new_email
                        db_utils.save_csv(customers_df, CUSTOMER_FILE)
                        st.success("✅ Details updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Unable to fetch coordinates. Try a different address.")
    else:
        st.error("❌ Your customer data was not found.")

    st.subheader("📦 Your Orders")

    if not orders_df.empty and "placed_by" in orders_df.columns:
        user_orders = orders_df[orders_df["placed_by"] == username].copy()
        if not user_orders.empty:
            user_orders['delivery_date'] = pd.to_datetime(user_orders['delivery_date'], errors='coerce').dt.date
            if 'order_date' in user_orders.columns:
                user_orders['order_date'] = pd.to_datetime(user_orders['order_date'], errors='coerce').dt.date

            user_orders = user_orders.merge(products_df[['product_id', 'product_name']], on='product_id', how='left')

            # ✅ Merge using customer_id and delivery_date to get truck_id and truck_type
            if not allocation_df.empty and "truck_id" in allocation_df.columns:
                allocation_df['delivery_date'] = pd.to_datetime(allocation_df['delivery_date'], errors='coerce').dt.date
                user_orders = user_orders.merge(
                    allocation_df[['customer_id', 'delivery_date', 'truck_id', 'truck_type']],
                    on=['customer_id', 'delivery_date'],
                    how='left'
                )
                user_orders['Status'] = user_orders.apply(
                    lambda row: f"Allocated (Truck {row['truck_id']} - {row['truck_type']})"
                    if pd.notna(row['truck_id']) else "Not Allocated",
                    axis=1
                )
            else:
                user_orders['Status'] = "Not Allocated"

            search_term = st.text_input("🔍 Search orders by Product Name or Order ID")
            if search_term:
                user_orders = user_orders[
                    user_orders['product_name'].str.contains(search_term, case=False, na=False) |
                    user_orders['order_id'].astype(str).str.contains(search_term, case=False)
                ]

            display_cols = ['order_id', 'product_name']
            if 'order_date' in user_orders.columns:
                display_cols.append('order_date')
            display_cols += ['delivery_date', 'num_boxes', 'Status']

            st.dataframe(user_orders[display_cols])

        else:
            st.info("ℹ️ You have not placed any orders yet.")
    else:
        st.info("ℹ️ No order data available.")
