import os

# Détection si on tourne dans Streamlit
try:
    import streamlit as st
    STREAMLIT_MODE = True
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
    STREAMLIT_MODE = False

def get_shop_credentials():
    """
    Récupère les credentials Shopify du client unique (version simple).
    Compatible Streamlit ou .env
    """
    if STREAMLIT_MODE:
        return {
            "SHOP_NAME": st.secrets["SHOP_NAME_TEC"],
            "ACCESS_TOKEN": st.secrets["SHOPIFY_API_TOKEN"]
        }
    else:
        return {
            "SHOP_NAME": os.getenv("SHOP_NAME_TEC"),
            "ACCESS_TOKEN": os.getenv("SHOPIFY_API_TOKEN")
        }
