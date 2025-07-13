import os
try:
    import streamlit as st
except ImportError:
    st = None

def get_shop_credentials():
    if st is not None and hasattr(st, "secrets"):
        shop_name = st.secrets.get("SHOP_NAME_TEC")
        access_token = st.secrets.get("SHOPIFY_API_TOKEN")
    else:
        shop_name = os.getenv("SHOP_NAME_TEC")
        access_token = os.getenv("SHOPIFY_API_TOKEN")
    print(f"SHOP_NAME = {shop_name!r}")  # <-- DEBUG
    if not shop_name or not access_token:
        raise ValueError("Credentials Shopify manquants")
    return {
        "SHOP_NAME": shop_name,
        "ACCESS_TOKEN": access_token,
    }
