import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils import auth, db_utils

st.set_page_config(page_title="Place Order", layout="wide")
auth.require_login_and_sidebar()

# File paths
ORDER_FILE = "orders.csv"
PRODUCT_FILE = "products.csv"

st.title("🍚 Place Multi-Product Order")

# Load data
products_df = db_utils.load_csv(PRODUCT_FILE)
orders_df = db_utils.load_csv(ORDER_FILE)

# Clean and ensure stock column
if "available_stock" not in products_df.columns:
    products_df["available_stock"] = 0
products_df["available_stock"] = products_df["available_stock"].fillna(0).astype(int)

# Filter in-stock products
available_products_df = products_df[products_df["available_stock"] > 0].copy()
if available_products_df.empty:
    st.warning("⚠️ No products in stock. Cannot place order.")
    st.stop()

# Session info
customer_id = st.session_state.get("customer_id", 1)
username = st.session_state.get("username", "user1")

# Get next order ID
def get_next_order_id(df):
    return int(df["order_id"].max()) + 1 if not df.empty else 1001

# Initialize cart in session
if "order_cart" not in st.session_state:
    st.session_state.order_cart = []

# Product name map
product_name_map = dict(zip(available_products_df["product_id"], available_products_df["product_name"]))

st.markdown("### 🧾 Add Product to Cart")

with st.form("add_to_cart_form"):
    product_id = st.selectbox(
        "Select Product",
        options=available_products_df["product_id"],
        format_func=lambda pid: f"{product_name_map[pid]} (Stock: {available_products_df.loc[available_products_df['product_id'] == pid, 'available_stock'].values[0]})"
    )
    max_stock = int(available_products_df.loc[available_products_df["product_id"] == product_id, "available_stock"].values[0])
    qty = st.number_input("Quantity (Boxes)", min_value=1, max_value=max_stock, step=1)
    add = st.form_submit_button("➕ Add to Cart")

    if add:
        st.session_state.order_cart.append({
            "product_id": product_id,
            "product_name": product_name_map[product_id],
            "num_boxes": int(qty)
        })
        st.success(f"Added {qty} box(es) of {product_name_map[product_id]} to cart.")
        st.rerun()

# Show cart
if st.session_state.order_cart:
    st.markdown("### 🛒 Order Cart")
    cart_df = pd.DataFrame(st.session_state.order_cart)

    # Add delete buttons for each row
    for idx, item in cart_df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 3, 2, 1])
        col1.write(f"**{item['product_name']}**")
        col2.write(f"{item['num_boxes']} box(es)")
        if col4.button("❌", key=f"delete_{idx}"):
            st.session_state.order_cart.pop(idx)
            st.rerun()

    with st.form("finalize_order_form"):
        st.markdown("### 📦 Finalize Order")
        order_date = st.date_input("Order Date", value=date.today())
        delivery_date = st.date_input("Delivery Date", min_value=date.today() + timedelta(days=1))
        confirm = st.form_submit_button("✅ Place Order")

        if confirm:
            order_id = get_next_order_id(orders_df)
            new_orders = []
            updated_products_df = products_df.copy()

            for item in st.session_state.order_cart:
                product_id = item["product_id"]
                qty = item["num_boxes"]
                available = int(updated_products_df.loc[updated_products_df["product_id"] == product_id, "available_stock"].values[0])

                if qty > available:
                    st.error(f"❌ Not enough stock for {product_name_map[product_id]}. Only {available} left.")
                    st.stop()

                new_orders.append({
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "num_boxes": qty,
                    "order_date": order_date,
                    "delivery_date": delivery_date,
                    "placed_by": username
                })
                # Deduct stock
                updated_products_df.loc[updated_products_df["product_id"] == product_id, "available_stock"] -= qty

            new_orders_df = pd.DataFrame(new_orders)
            orders_df = pd.concat([orders_df, new_orders_df], ignore_index=True)
            db_utils.save_csv(orders_df, ORDER_FILE)
            db_utils.save_csv(updated_products_df, PRODUCT_FILE)

            st.success(f"✅ Order #{order_id} placed successfully for {len(new_orders)} item(s)!")
            st.session_state.order_cart = []  # Clear cart
            st.rerun()
else:
    st.info("🛒 Cart is empty. Add items above.")
