import streamlit as st
import pandas as pd
import time
from geopy.geocoders import Nominatim

CUSTOMER_FILE = "data/customers.csv"
geolocator = Nominatim(user_agent="truck_delivery_optimizer")

# Predefined users (Admin/Manager)
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "manager": {"password": "manager123", "role": "manager"},
}

# Load customer CSV (reusable)
def load_customer_users():
    try:
        df = pd.read_csv(CUSTOMER_FILE)
        df = df.drop_duplicates(subset=["username"])  # 🔁 Remove duplicates if any
        return df[['username', 'password', 'customer_id', 'customer_name']].dropna()
    except Exception as e:
        st.error(f"Error loading customers: {e}")
        return pd.DataFrame()

# Login/Sign-up Page
def login_page():
    st.title("🔐 Login / Sign Up")
    menu = st.radio("Select Action", ["Login", "Sign Up"], horizontal=True)

    if menu == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", key="login_btn"):
            # Admin or Manager
            user = USERS.get(username)
            if user and user["password"] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = user["role"]
                st.success(f"✅ Welcome **{username.capitalize()}** ({user['role'].capitalize()})")
                st.rerun()

            # Check Customer CSV
            else:
                df = load_customer_users()
                row = df[df["username"].str.lower() == username.lower()]
                if not row.empty and row.iloc[0]["password"] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = row.iloc[0]["username"]
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
        state = st.text_input("State")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Create Account", key="signup_btn"):
            if name and full_address and state and username and password:
                try:
                    df = pd.read_csv(CUSTOMER_FILE)
                except:
                    df = pd.DataFrame()

                # Check for duplicate username (case insensitive)
                if "username" in df.columns and username.lower() in df["username"].str.lower().values:
                    st.error("⚠️ Username already exists. Please choose another.")
                    return

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

# Sidebar role-based access
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
