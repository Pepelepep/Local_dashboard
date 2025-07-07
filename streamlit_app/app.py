import streamlit as st
import sys
import os
from streamlit_option_menu import option_menu

# --- Ajout du path pour import local des modules de page
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pages import stock, ventes, regles_fournisseurs, recommandations

# --- Config de la page principale
st.set_page_config(page_title="📦 Dashboard Shopify", layout="wide")

# --- Supprimer totalement la sidebar (même réduite)
st.markdown("""
    <style>
    /* Supprimer le bandeau gauche Streamlit */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Barre de navigation horizontale custom
selected = option_menu(
    menu_title=None,
    options=["Ventes", "Stock", "Recommandations", "Règles fournisseurs"],
    icons=["bar-chart", "boxes", "lightbulb", "list-task"],
    orientation="horizontal",
    default_index=0,
    styles={
        "container": {"padding": "0!important", "background-color": "#1e1e1e"},
        "icon": {"color": "white", "font-size": "18px"},
        "nav-link": {
            "font-size": "16px",
            "color": "#ccc",
            "margin": "0 8px",
            "padding": "8px 16px",
            "border-radius": "8px",
            "--hover-color": "#333333"
        },
        "nav-link-selected": {
            "background-color": "#ff4b4b",
            "color": "white"
        },
    }
)

# --- Rendu des pages
if selected == "Ventes":
    ventes.render()
elif selected == "Stock":
    stock.render()
elif selected == "Recommandations":
    recommandations.render()
elif selected == "Règles fournisseurs":
    regles_fournisseurs.render()