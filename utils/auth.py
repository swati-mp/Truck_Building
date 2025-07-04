# # import streamlit as st

# # USERS = {
# #     "admin": {"password": "admin123", "role": "admin"},
# #     "manager": {"password": "manager123", "role": "manager"},
# #     "viewer": {"password": "viewer123", "role": "viewer"},
# # }

# # def login_page():
# #     st.title("🔐 Login")  # ❌ NO set_page_config here
# #     username = st.text_input("Username")
# #     password = st.text_input("Password", type="password")
# #     if st.button("Login"):
# #         user = USERS.get(username)
# #         if user and user['password'] == password:
# #             st.session_state['logged_in'] = True
# #             st.session_state['username'] = username
# #             st.session_state['role'] = user['role']
# #             st.success(f"✅ Login successful! Welcome **{username.capitalize()}** ({user['role'].capitalize()}).")
# #             st.rerun()
# #         else:
# #             st.error("❌ Invalid username or password.")

# # def logout():
# #     st.session_state.clear()
# #     st.success("✅ Logged out successfully.")
# #     st.rerun()

# # def require_login_and_sidebar():
# #     if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
# #         login_page()
# #         st.stop()

# #     st.sidebar.success(f"🔐 Logged in as: {st.session_state.get('role', 'user').capitalize()}")

# #     if st.sidebar.button("🚪 Logout"):
# #         logout()

# import streamlit as st
# import pandas as pd

# CUSTOMER_FILE = "data/customers.csv"

# # Predefined admin/manager
# USERS = {
#     "admin": {"password": "admin123", "role": "admin"},
#     "manager": {"password": "manager123", "role": "manager"},
# }

# def load_customer_users():
#     try:
#         df = pd.read_csv(CUSTOMER_FILE)
#         return df[['username', 'password', 'customer_id', 'customer_name']].dropna()
#     except Exception as e:
#         st.error(f"Error loading customers: {e}")
#         return pd.DataFrame()

# def login_page():
#     st.title("🔐 Login")
#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")

#     if st.button("Login", key="login_btn"):
#         # First try predefined users
#         user = USERS.get(username)
#         if user and user["password"] == password:
#             st.session_state["logged_in"] = True
#             st.session_state["username"] = username
#             st.session_state["role"] = user["role"]
#             st.success(f"✅ Login successful! Welcome **{username.capitalize()}** ({user['role'].capitalize()})")
#             st.rerun()
#             return

#         # Try customer users from CSV
#         customer_df = load_customer_users()
#         row = customer_df[customer_df["username"] == username]
#         if not row.empty and row.iloc[0]["password"] == password:
#             st.session_state["logged_in"] = True
#             st.session_state["username"] = username
#             st.session_state["role"] = "user"
#             st.session_state["customer_id"] = int(row.iloc[0]["customer_id"])
#             st.session_state["customer_name"] = row.iloc[0]["customer_name"]
#             st.success(f"✅ Login successful! Welcome **{username}** (User)")
#             st.rerun()
#         else:
#             st.error("❌ Invalid username or password.")

# def logout():
#     st.session_state.clear()
#     st.success("✅ Logged out successfully.")
#     st.rerun()

# def require_login_and_sidebar():
#     if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
#         login_page()
#         st.stop()

#     role = st.session_state.get("role", "user")
#     st.sidebar.success(f"🔐 Logged in as: {st.session_state.get('username')}")

#     # Common link
#     st.sidebar.page_link("main.py", label="🏠 Main Dashboard")

#     # Role-specific sidebar
#     if role == "admin":
#         st.sidebar.page_link("pages/2_Truck_Master.py", label="🚛 Truck Master")
#         st.sidebar.page_link("pages/3_Product_Master.py", label="📦 Product Master")
#         st.sidebar.page_link("pages/4_Order_Transaction.py", label="📝 Order Transaction")
#         st.sidebar.page_link("pages/5_Truck_Config.py", label="⚙️ Truck Config")
#         st.sidebar.page_link("pages/6_Truck_Allocation_Report.py", label="📊 Truck Allocation Report")

#     elif role == "user":
#         st.sidebar.page_link("pages/1_Customer_Master.py", label="👤 Customer Master")
#         st.sidebar.page_link("pages/7_Place_Order.py", label="🛒 Place Order")

#     # Logout Button with Unique Key
#     if st.sidebar.button("🚪 Logout", key="logout_btn"):
#         logout()

import streamlit as st
import pandas as pd
import time
from geopy.geocoders import Nominatim

CUSTOMER_FILE = "data/customers.csv"
geolocator = Nominatim(user_agent="truck_delivery_optimizer")

# Predefined users
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "manager": {"password": "manager123", "role": "manager"},
}

# Load customers
def load_customer_users():
    try:
        df = pd.read_csv(CUSTOMER_FILE)
        return df[['username', 'password', 'customer_id', 'customer_name']].dropna()
    except Exception as e:
        st.error(f"Error loading customers: {e}")
        return pd.DataFrame()

# Save new customer with geolocation
def save_new_customer(name, full_address, username, password):
    try:
        df = pd.read_csv(CUSTOMER_FILE)
    except:
        df = pd.DataFrame()

    if not df.empty and "customer_id" in df.columns:
        new_id = int(df["customer_id"].max()) + 1
    else:
        new_id = 1

    # Geocode the address
    try:
        location = geolocator.geocode(full_address)
        if not location:
            st.warning("⚠️ Could not locate address. Please enter a valid address.")
            return False

        latitude = location.latitude
        longitude = location.longitude

        # Extract address and state smartly from location.raw
        address_data = location.raw.get("address", {})
        state = address_data.get("state", "")
        city = address_data.get("city") or address_data.get("town") or address_data.get("village") or address_data.get("suburb", "")
        address_only = f"{city}".strip() if city else full_address

    except Exception as e:
        st.error(f"❌ Geocoding error: {e}")
        return False

    # Prepare new row
    new_row = {
        "customer_id": new_id,
        "customer_name": name,
        "address": address_only,
        "state": state,
        "latitude": latitude,
        "longitude": longitude,
        "username": username,
        "password": password
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CUSTOMER_FILE, index=False)
    return True

# Login + Signup page
def login_page():
    st.title("🔐 Login / Sign Up")
    menu = st.radio("Select Action", ["Login", "Sign Up"], horizontal=True)

    if menu == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", key="login_btn"):
            # Check admin/manager
            user = USERS.get(username)
            if user and user["password"] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = user["role"]
                st.success(f"✅ Welcome **{username.capitalize()}** ({user['role'].capitalize()})")
                st.rerun()
                return

            # Check CSV users
            customer_df = load_customer_users()
            row = customer_df[customer_df["username"] == username]
            if not row.empty and row.iloc[0]["password"] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = "user"
                st.session_state["customer_id"] = int(row.iloc[0]["customer_id"])
                st.session_state["customer_name"] = row.iloc[0]["customer_name"]
                st.success(f"✅ Welcome **{username}** (User)")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

    elif menu == "Sign Up":
        st.subheader("📝 New Customer Sign Up")
        name = st.text_input("Customer Name")
        full_address = st.text_input("Full Address (for location detection)")
        state = st.text_input("State")  # 👈 manually entered by user
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Create Account", key="signup_btn"):
            if name and full_address and state and username and password:
                try:
                    df = pd.read_csv(CUSTOMER_FILE)
                except:
                    df = pd.DataFrame()

                # if username in df.get("username", []):
                #     st.error("⚠️ Username already exists. Please choose another.")
                #     return
                if "username" in df.columns and username in df["username"].values:
                    st.error("⚠️ Username already exists. Please choose another.")
                    return


                # Geocode for lat/lon only
                try:
                    location = geolocator.geocode(full_address)
                    if not location:
                        st.warning("⚠️ Could not locate address. Please enter a valid address.")
                        return

                    latitude = location.latitude
                    longitude = location.longitude
                except Exception as e:
                    st.error(f"❌ Geocoding error: {e}")
                    return

                new_id = int(df["customer_id"].max()) + 1 if not df.empty else 1
                new_row = {
                    "customer_id": new_id,
                    "customer_name": name,
                    "address": full_address,
                    "state": state,
                    "latitude": latitude,
                    "longitude": longitude,
                    "username": username,
                    "password": password
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(CUSTOMER_FILE, index=False)
                st.success("✅ Account created! Please login now.")
                time.sleep(3)  
                st.rerun()
            else:
                st.warning("⚠️ Please fill in all fields.")


# Logout
def logout():
    st.session_state.clear()
    st.success("✅ Logged out successfully.")
    st.rerun()

# Sidebar role-based links
def require_login_and_sidebar():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        login_page()
        st.stop()

    role = st.session_state.get("role", "user")
    st.sidebar.page_link("main.py", label="🏠 Main Dashboard")

    if role == "admin":
        st.sidebar.page_link("pages/2_Truck_Master.py", label="🚛 Truck Master")
        st.sidebar.page_link("pages/3_Product_Master.py", label="📦 Product Master")
        st.sidebar.page_link("pages/4_Order_Transaction.py", label="📝 Order Transaction")
        st.sidebar.page_link("pages/5_Truck_Config.py", label="⚙️ Truck Config")
        st.sidebar.page_link("pages/6_Truck_Allocation_Report.py", label="📊 Truck Allocation Report")

    elif role == "user":
        st.sidebar.page_link("pages/1_Customer_Master.py", label="👤 Customer Master")
        st.sidebar.page_link("pages/7_Place_Order.py", label="🛒 Place Order")

    st.sidebar.success(f"🔐 Logged in as: {st.session_state.get('username')}")
    
    if st.sidebar.button("🚪 Logout", key="logout_btn"):
        logout()
