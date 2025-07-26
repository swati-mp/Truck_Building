import streamlit as st
import pandas as pd
from utils import db_utils, auth

st.set_page_config(page_title="Product Master", layout="wide")
auth.require_login_and_sidebar()

st.title("📦 Product Master")
PRODUCT_FILE = "products.csv"
products_df = db_utils.load_csv(PRODUCT_FILE)

<<<<<<< HEAD
# ------------------ ADD NEW PRODUCT ------------------
with st.expander("➕ Add New Product"):
    with st.form("add_product_form", clear_on_submit=True):
=======
# Auto-generate product_id starting from 101
def get_next_product_id(df):
    if df.empty or "product_id" not in df.columns:
        return 101
    try:
        max_id = pd.to_numeric(df["product_id"], errors="coerce").dropna().astype(int).max()
        return max(101, max_id + 1)
    except:
        return 101


# ------------------ ADD NEW PRODUCT ------------------
with st.expander("➕ Add New Product"):
    with st.form("add_product_form", clear_on_submit=True):
        auto_id = get_next_product_id(products_df)
        st.markdown(f"**Auto-generated Truck ID:** `{auto_id}`")

>>>>>>> df81800 (Enhanced delivery map with GraphHopper for optimized truck routing.)
        product_name = st.text_input("Product Name")
        length_cm = st.number_input("Length (cm)", min_value=0.0, step=0.1, format="%.2f")
        width_cm = st.number_input("Width (cm)", min_value=0.0, step=0.1, format="%.2f")
        height_cm = st.number_input("Height (cm)", min_value=0.0, step=0.1, format="%.2f")
        weight_kg = st.number_input("Weight (kg)", min_value=0.0, step=0.1, format="%.2f")
        available_stock = st.number_input("Available Stock (Boxes)", min_value=0, step=1)

        submitted = st.form_submit_button("Add Product")

        if submitted:
            if product_name and length_cm > 0 and width_cm > 0 and height_cm > 0 and weight_kg > 0:
                product_id = db_utils.get_next_id(products_df, "product_id")
                size_per_box = round((length_cm * width_cm * height_cm) / 1_000_000, 6)

                new_entry = pd.DataFrame([{
                    "product_id": product_id,
                    "product_name": product_name,
                    "weight_per_box": weight_kg,
                    "size_per_box": size_per_box,
                    "available_stock": int(available_stock)
                }])
                products_df = pd.concat([products_df, new_entry], ignore_index=True)
                db_utils.save_csv(products_df, PRODUCT_FILE)
                st.success(f"✅ Product '{product_name}' added with ID {product_id}!")
            else:
                st.warning("⚠️ Please fill in all fields with valid values.")

# ------------------ EDIT EXISTING PRODUCT ------------------
if not products_df.empty:
    with st.expander("✏️ Edit Existing Product"):
        selected_id = st.selectbox("Select Product ID to Edit", products_df["product_id"])

        selected_product = products_df[products_df["product_id"] == selected_id].iloc[0]

        with st.form("edit_product_form"):
            new_name = st.text_input("Product Name", value=selected_product["product_name"])
            new_weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1, value=selected_product["weight_per_box"], format="%.2f")
            new_size = selected_product["size_per_box"]  # not editable here, but can be added
            add_stock = st.number_input("Add More Stock (Boxes)", min_value=0, step=1)
            submit_edit = st.form_submit_button("Update Product")

            if submit_edit:
                idx = products_df[products_df["product_id"] == selected_id].index[0]
                products_df.at[idx, "product_name"] = new_name
                products_df.at[idx, "weight_per_box"] = new_weight
                products_df.at[idx, "available_stock"] += int(add_stock)
                db_utils.save_csv(products_df, PRODUCT_FILE)
                st.success(f"✅ Product ID {selected_id} updated. Stock increased by {add_stock}.")

# ------------------ PRODUCT TABLE ------------------
st.subheader("📋 Product List")

if not products_df.empty:
    st.dataframe(products_df)

    # ------------------ DELETE PRODUCT ------------------
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
    st.info("ℹ️ No products available.")
