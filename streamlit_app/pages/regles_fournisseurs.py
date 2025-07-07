import streamlit as st
from shopify_sdk.db.database import load_table

def render():
    st.title("📋 Règles fournisseurs")

    products_df = load_table("products")
    stock_df = load_table("inventory")
    orders_df = load_table("orders")
    vendors_df = load_table("vendors")
    vendors_df["Payment_Term_Definition"] = vendors_df["Payment_Term_Definition"].astype(str)

    st.markdown("⚙️ Règles définies par fournisseur :")
    st.dataframe(vendors_df, use_container_width=True)
