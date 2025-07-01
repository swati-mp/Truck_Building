import streamlit as st
st.set_page_config(page_title="Product Master", layout="wide")

import pandas as pd
from utils import db_utils
from utils import auth

auth.require_login_and_sidebar()

# Access role:
role = st.session_state.get("role", "admin")

st.title("📦 Product Master")

PRODUCT_FILE = "products.csv"

# Load product data
products_df = db_utils.load_csv(PRODUCT_FILE)

with st.expander("➕ Add New Product"):
    with st.form("add_product_form", clear_on_submit=True):
        product_name = st.text_input("Product Name")
        length_cm = st.number_input("Length (cm)", min_value=0.0, step=0.1, format="%.2f")
        width_cm = st.number_input("Width (cm)", min_value=0.0, step=0.1, format="%.2f")
        height_cm = st.number_input("Height (cm)", min_value=0.0, step=0.1, format="%.2f")
        weight_kg = st.number_input("Weight (kg)", min_value=0.0, step=0.1, format="%.2f")
        submitted = st.form_submit_button("Add Product")

        if submitted:
            if product_name and length_cm > 0 and width_cm > 0 and height_cm > 0 and weight_kg > 0:
                # Auto-generate product_id
                if not products_df.empty and 'product_id' in products_df.columns:
                    max_id = products_df['product_id'].astype(int).max()
                    product_id = int(max_id) + 1
                else:
                    product_id = 101

                # Calculate volume in cubic meters
                size_per_box = round((length_cm * width_cm * height_cm) / 1_000_000, 6)

                new_entry = pd.DataFrame([{
                    "product_id": product_id,
                    "product_name": product_name,
                    "weight_per_box": weight_kg,
                    "size_per_box": size_per_box
                }])
                products_df = pd.concat([products_df, new_entry], ignore_index=True)
                db_utils.save_csv(products_df, PRODUCT_FILE)
                st.success(f"✅ Product '{product_name}' added with ID {product_id}!")
            else:
                st.warning("⚠️ Please fill in all fields with valid values.")

st.subheader("📋 Product List")

if not products_df.empty:
    st.dataframe(products_df)

    with st.expander("🗑️ Delete Product"):
        delete_id = st.text_input("Enter Product ID to Delete")
        if st.button("Delete Product"):
            if delete_id.isdigit() and int(delete_id) in products_df["product_id"].astype(int).values:
                products_df = db_utils.delete_entry_by_id(products_df, "product_id", int(delete_id))
                db_utils.save_csv(products_df, PRODUCT_FILE)
                st.success(f"✅ Product with ID '{delete_id}' deleted.")
            else:
                st.warning("⚠️ Product ID not found.")
else:
    st.info("ℹ️ No products available. Please add products.")
