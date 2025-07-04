import streamlit as st
st.set_page_config(page_title="Truck Delivery Optimizer", layout="wide")  # ✅ MUST be first Streamlit command

from utils import auth
import pandas as pd
from datetime import date

# ✅ Enforce login and show sidebar with logout
auth.require_login_and_sidebar()

# # 🚚 Main Page Content
# st.title("🚚 Truck Building Optimizer - Dashboard")
# st.markdown(f"Welcome **{st.session_state['username'].capitalize()}** 👋")
# st.markdown("Use the sidebar to navigate between different modules.")
# st.markdown("---")

# # 🔒 Admin-only dashboard
# if st.session_state["role"] == "admin":
#     st.subheader("📊 Overview Metrics")

#     try:
#         orders_df = pd.read_csv("data/orders.csv")
#         trucks_df = pd.read_csv("data/trucks.csv")
#         customers_df = pd.read_csv("data/customers.csv")
#         allocation_df = st.session_state.get("filo_allocated_df", pd.DataFrame())  # or allocation_results
#     except:
#         orders_df = pd.DataFrame()
#         trucks_df = pd.DataFrame()
#         customers_df = pd.DataFrame()
#         allocation_df = pd.DataFrame()

#     col1, col2, col3 = st.columns(3)
#     col1.metric("Total Orders", len(orders_df))
#     col2.metric("Total Trucks", len(trucks_df))
#     col3.metric("Total Customers", len(customers_df))

#     st.markdown("### 🗓️ Today's Orders")
#     today = date.today()
#     if not orders_df.empty:
#         orders_df['delivery_date'] = pd.to_datetime(orders_df['delivery_date']).dt.date
#         today_orders = orders_df[orders_df['delivery_date'] == today]

#         # Merge with allocation info based on customer_id
#         if not allocation_df.empty:
#             allocated = allocation_df[['customer_id', 'truck_id']].drop_duplicates()
#             today_orders = today_orders.merge(allocated, on='customer_id', how='left')
#             today_orders['Status'] = today_orders['truck_id'].apply(
#                 lambda x: f"Allocated (Truck {x})" if pd.notna(x) else "Not Allocated"
#             )
#         else:
#             today_orders['Status'] = "Not Allocated"

#         # Show orders with allocation status
#         st.dataframe(today_orders[[
#             'order_id', 'customer_id', 'product_id', 'num_boxes', 'delivery_date', 'Status'
#         ]])
#     else:
#         st.info("No orders data available.")
    
# 🚚 Truck Building Optimizer - Dashboard
import pandas as pd
from datetime import date
import streamlit as st

st.title("🚚 Truck Building Optimizer - Dashboard")
st.markdown(f"Welcome **{st.session_state['username'].capitalize()}** 👋")
st.markdown("Use the sidebar to navigate between different modules.")
st.markdown("---")

# 🔒 Role-Based Dashboard
if st.session_state["role"] == "admin":
    st.subheader("📊 Overview Metrics")
    try:
        orders_df = pd.read_csv("data/orders.csv")
        trucks_df = pd.read_csv("data/trucks.csv")
        customers_df = pd.read_csv("data/customers.csv")
        allocation_df = st.session_state.get("filo_allocated_df", pd.DataFrame())
    except:
        orders_df = pd.DataFrame()
        trucks_df = pd.DataFrame()
        customers_df = pd.DataFrame()
        allocation_df = pd.DataFrame()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Orders", len(orders_df))
    col2.metric("Total Trucks", len(trucks_df))
    col3.metric("Total Customers", len(customers_df))

    st.markdown("### 🗓️ Today's Orders")
    today = date.today()
    if not orders_df.empty:
        orders_df['delivery_date'] = pd.to_datetime(orders_df['delivery_date']).dt.date
        user_orders = orders_df[orders_df['delivery_date'] == today]

        if not allocation_df.empty:
            allocated = allocation_df[['customer_id', 'truck_id']].drop_duplicates()
            user_orders = user_orders.merge(allocated, on='customer_id', how='left')
            user_orders['Status'] = user_orders['truck_id'].apply(
                lambda x: f"Allocated (Truck {x})" if pd.notna(x) else "Not Allocated"
            )
        else:
            user_orders['Status'] = "Not Allocated"

        st.dataframe(user_orders[[
            'order_id', 'customer_id', 'product_id', 'num_boxes', 'delivery_date', 'Status'
        ]])
    else:
        st.info("No orders data available.")

# else:
#     # 👤 User View
#     st.subheader("📦 Your Orders")
#     try:
#         orders_df = pd.read_csv("data/orders.csv")
#         allocation_df = st.session_state.get("filo_allocated_df", pd.DataFrame())
#     except:
#         orders_df = pd.DataFrame()
#         allocation_df = pd.DataFrame()

#     username = st.session_state["username"]

#     if not orders_df.empty:
#         if 'placed_by' in orders_df.columns:
#             user_orders = orders_df[orders_df['placed_by'] == username].copy()

#             if not user_orders.empty:
#                 user_orders['delivery_date'] = pd.to_datetime(user_orders['delivery_date']).dt.date
#                 if 'order_date' in user_orders.columns:
#                     user_orders['order_date'] = pd.to_datetime(user_orders['order_date']).dt.date

#                 if not allocation_df.empty:
#                     allocated = allocation_df[['customer_id', 'truck_id']].drop_duplicates()
#                     user_orders = user_orders.merge(allocated, on='customer_id', how='left')
#                     user_orders['Status'] = user_orders['truck_id'].apply(
#                         lambda x: f"Allocated (Truck {x})" if pd.notna(x) else "Not Allocated"
#                     )
#                 else:
#                     user_orders['Status'] = "Not Allocated"

#                 display_cols = ['order_id', 'customer_id', 'product_id']
#                 if 'order_date' in user_orders.columns:
#                     display_cols.append('order_date')
#                 display_cols += ['delivery_date', 'num_boxes', 'Status']

#                 st.dataframe(user_orders[display_cols])
#             else:
#                 st.info("ℹ️ You have not placed any orders.")
#         else:
#             st.error("⚠️ 'placed_by' column not found in orders.csv.")
#     else:
#         st.info("ℹ️ No order data available.")
else:
    # 👤 User View
    st.subheader("📦 Your Orders")
    try:
        orders_df = pd.read_csv("data/orders.csv")
        allocation_df = st.session_state.get("filo_allocated_df", pd.DataFrame())
    except:
        orders_df = pd.DataFrame()
        allocation_df = pd.DataFrame()

    username = st.session_state.get("username", "")

    if not orders_df.empty:
        if 'placed_by' in orders_df.columns:
            user_orders = orders_df[orders_df['placed_by'] == username].copy()

            if not user_orders.empty:
                user_orders['delivery_date'] = pd.to_datetime(user_orders['delivery_date'], errors='coerce').dt.date
                if 'order_date' in user_orders.columns:
                    user_orders['order_date'] = pd.to_datetime(user_orders['order_date'], errors='coerce').dt.date

                if not allocation_df.empty:
                    allocated = allocation_df[['customer_id', 'truck_id']].drop_duplicates()
                    user_orders = user_orders.merge(allocated, on='customer_id', how='left')
                    user_orders['Status'] = user_orders['truck_id'].apply(
                        lambda x: "Allocated" if pd.notna(x) else "Not Allocated"
                    )
                else:
                    user_orders['Status'] = "Not Allocated"

                display_cols = ['order_id', 'customer_id', 'product_id']
                if 'order_date' in user_orders.columns:
                    display_cols.append('order_date')
                display_cols += ['delivery_date', 'num_boxes', 'Status']

                st.dataframe(user_orders[display_cols])
            else:
                st.info("ℹ️ You have not placed any orders.")
        else:
            st.error("⚠️ 'placed_by' column not found in orders.csv.")
    else:
        st.info("ℹ️ No order data available.")
