import streamlit as st

USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "manager": {"password": "manager123", "role": "manager"},
    "viewer": {"password": "viewer123", "role": "viewer"},
}

def login_page():
    st.title("🔐 Login")  # ❌ NO set_page_config here
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = USERS.get(username)
        if user and user['password'] == password:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['role'] = user['role']
            st.success(f"✅ Login successful! Welcome **{username.capitalize()}** ({user['role'].capitalize()}).")
            st.rerun()
        else:
            st.error("❌ Invalid username or password.")

def logout():
    st.session_state.clear()
    st.success("✅ Logged out successfully.")
    st.rerun()

def require_login_and_sidebar():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        login_page()
        st.stop()

    st.sidebar.success(f"🔐 Logged in as: {st.session_state.get('role', 'user').capitalize()}")

    if st.sidebar.button("🚪 Logout"):
        logout()
