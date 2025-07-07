import streamlit as st
import pandas as pd
from shopify_sdk.db.database import load_table
from shopify_sdk.recommandations.core import compute_recommendations

def render():
    st.title("🤖 Recommandations d’achat intelligentes")

    # --- Chargement des données
    products_df = load_table("products")
    stock_df = load_table("inventory")
    orders_df = load_table("orders")
    vendors_df = load_table("vendors")

    df = compute_recommendations(products_df, stock_df, orders_df, vendors_df)

    # --- Filtres en haut
    col1, col2, col3 = st.columns(3)

    with col1:
        locations = df["location_name"].dropna().unique()
        selected_location = st.selectbox("📍 Lieu de stockage", options=locations)
        df = df[df["location_name"] == selected_location]

    with col2:
        selected_alerts = st.multiselect("🚨 Alertes", options=["rouge", "orange", "vert"], default=["rouge", "orange", "vert"])
        df = df[df["Alerte"].isin(selected_alerts)]

    with col3:
        vendors = df["vendor"].dropna().unique()
        selected_vendors = st.multiselect("🏷️ Marques", options=vendors, default=list(vendors))
        df = df[df["vendor"].isin(selected_vendors)]

    # --- Filtre ventes récentes avec sélecteur et valeur par défaut
    # --- Filtres en haut
    col4, col5,= st.columns(2)

    with col4:
        vente_filter = st.selectbox(
            "📦 Produits à inclure",
            options=["Tous", "Avec ventes récentes", "Sans ventes récentes"],
            index=1  # Présélection sur "Avec ventes récentes"
        )
        if vente_filter == "Avec ventes récentes":
            df = df[df["Ventes récentes"]]
        elif vente_filter == "Sans ventes récentes":
            df = df[~df["Ventes récentes"]]

    with col5:
        recommander_filter = st.selectbox(
            "☑️ A recommander ?",
            options=["Oui", "Non"],
            index=0  # Présélection sur "Avec ventes récentes"
        )
        if recommander_filter == "Oui":
            df = df[df["À recommander"]]
        elif recommander_filter == "Non":
            df = df[~df["À recommander"]]
        

    # --- Tableau final
    st.subheader("📋 Produits recommandés à prioriser")

    display_df = df[[
        "🟡", "vendor", "title","variant_sku",  "location_name",
        "available_quantity", "avg_sales_7d", "avg_sales_14d", "avg_sales_30d",
        "mean_sales", "days_to_oos", "Delivery_Days", "Score Importance", "À recommander"
    ]].rename(columns={
        "🟡": "Alerte",
        "vendor": "Marque",
        "title": "Produit",
        "variant_sku": "SKU",
        "location_name": "Lieu",
        "available_quantity": "Stock actuel",
        "avg_sales_7d": "Ventes 7j",
        "avg_sales_14d": "Ventes 14j",
        "avg_sales_30d": "Ventes 30j",
        "mean_sales": "Ventes moy.",
        "days_to_oos": "Jours avant rupture",
        "Delivery_Days": "Délai fournisseur"
    })

    display_df = display_df.sort_values("Score Importance", ascending=False)

    st.dataframe(display_df, use_container_width=True, height=600)
