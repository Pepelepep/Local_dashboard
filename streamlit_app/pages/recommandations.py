import streamlit as st
import pandas as pd
import io
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

    # --- Calcul de la quantité à commander
    df["Quantité à commander"] = ((df["mean_sales"] * df["Delivery_Days"]) - df["available"]).round().clip(lower=0).astype(int)

    # --- Filtres dynamiques en haut
    col1, col2, col3 = st.columns(3)

    # --- Filtre par lieu de stockage avec "Tous"
    locations = sorted(df["location_name"].dropna().unique())
    all_locations = ["Tous"] + locations
    with col1:
        selected_location = st.selectbox("📍 Lieu de stockage", options=all_locations, index=0)
        if selected_location != "Tous":
            df = df[df["location_name"] == selected_location]

    # --- Filtres sur alertes et marques
    with col2:
        selected_alerts = st.multiselect("🚨 Alertes", options=["rouge", "orange", "vert"], default=["rouge", "orange", "vert"])
        df = df[df["Alerte"].isin(selected_alerts)]

    with col3:
        vendors = sorted(df["vendor"].dropna().unique())
        all_vendors = ["Tous"] + vendors
        selected_vendors = st.multiselect("🏷️ Marques", options=all_vendors, default=["Tous"])
        if "Tous" not in selected_vendors:
            df = df[df["vendor"].isin(selected_vendors)]

    # --- Filtres complémentaires (ventes récentes, à recommander)
    col4, col5 = st.columns(2)
    with col4:
        vente_filter = st.selectbox(
            "📦 Produits à inclure",
            options=["Tous", "Avec ventes récentes", "Sans ventes récentes"],
            index=1
        )
        if vente_filter == "Avec ventes récentes":
            df = df[df["Ventes récentes"]]
        elif vente_filter == "Sans ventes récentes":
            df = df[~df["Ventes récentes"]]

    with col5:
        recommander_filter = st.selectbox(
            "☑️ À recommander ?",
            options=["Tous", "Oui", "Non"],
            index=1
        )
        if recommander_filter == "Oui":
            df = df[df["À recommander"]]
        elif recommander_filter == "Non":
            df = df[~df["À recommander"]]

    # --- Tableau final trié par score d'importance décroissant
    st.subheader("📋 Variantes recommandées à commander")

    display_df = df[[
        "🟡", "vendor", "product_title", "variant_title", "sku", "location_name",
        "available", "avg_sales_30d", "mean_sales", "Delivery_Days",
        "Quantité à commander", "days_to_oos", "Score Importance"
    ]].rename(columns={
        "🟡": "Alerte",
        "vendor": "Marque",
        "product_title": "Produit",
        "variant_title": "Taille",
        "sku": "SKU",
        "location_name": "Lieu",
        "available": "Stock actuel",
        "avg_sales_30d": "Ventes moy. 30j",
        "mean_sales": "Ventes moy/j",
        "Delivery_Days": "Délai fournisseur",
        "days_to_oos": "Jours avant rupture"
    })

    display_df = display_df.sort_values("Score Importance", ascending=False)

    st.dataframe(display_df, use_container_width=True, height=600)

    # Export CSV (UTF-8 BOM + ; comme séparateur)
    csv_buffer = io.StringIO()
    display_df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')

    st.download_button(
        label="⬇️ Exporter en CSV",
        data=csv_buffer.getvalue(),
        file_name="recommandations_achat_utf8.csv",
        mime="text/csv"
    )
