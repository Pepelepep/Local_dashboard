import streamlit as st
import pandas as pd
from shopify_sdk.db.database import load_table

def render():
    st.title("📦 Vue Stock – Produits et Disponibilité")

    # --- Load data
    df = load_table("inventory")

    # --- Nettoyage
    df["available_quantity"] = pd.to_numeric(df["available_quantity"], errors="coerce").fillna(0).astype(int)
    df["location_name"] = df["location_name"].fillna("Non défini")
    df["product_title"] = df["product_title"].fillna("Produit inconnu")

    # --- Extraire l’ID Shopify depuis le GID et recréer l'URL
    df["product_id"] = df["product_id"].str.extract(r"/Product/(\d+)$")
    df["Lien Shopify"] = df["product_id"].apply(
        lambda pid: f"https://admin.shopify.com/store/{st.secrets['SHOP']}/products/{pid}" if pd.notnull(pid) else None
    )

    # --- Filtre par lieu
    locations = df["location_name"].unique()
    selected_location = st.selectbox("📍 Filtrer par lieu de stockage :", options=locations)
    df = df[df["location_name"] == selected_location]

    # --- Seuil
    seuil = st.slider("🔻 Seuil critique de stock :", min_value=0, max_value=20, value=5)

    # --- Regroupement par produit
    grouped = df.groupby("product_title").agg(
        total_variants=("variant_id", "nunique"),
        total_stock=("available_quantity", "sum"),
        variants_below_threshold=("available_quantity", lambda x: (x <= seuil).sum()),
        product_url=("Lien Shopify", "first")
    ).reset_index()

    # --- Alerte visuelle
    def alert_color(row):
        if row["variants_below_threshold"] == 0:
            return "🟢"
        elif row["variants_below_threshold"] < row["total_variants"]:
            return "🟠"
        else:
            return "🔴"

    grouped["Alerte"] = grouped.apply(alert_color, axis=1)

    # --- Affichage tableau
    st.subheader("📊 Produits sous seuil")

    # --- Table pour affichage DataFrame cliquable
    styled_table = grouped.sort_values(by="variants_below_threshold", ascending=False).head(20)[[
        "Alerte", "product_title", "total_variants",
        "variants_below_threshold", "total_stock", "product_url"
    ]].rename(columns={
        "product_title": "Produit",
        "total_variants": "Nb Variantes",
        "variants_below_threshold": "Sous seuil",
        "total_stock": "Stock total",
        "product_url": "Lien Shopify"
    })
    
    styled_table = styled_table.sort_values(by="Sous seuil", ascending=False).head(20)

    st.dataframe(
        styled_table,
        use_container_width=True,
        height=600
    )

    # --- Détail par SKU sous le seuil
    st.subheader("🧾 Détail des variantes sous le seuil")

    df_detail = df[df["available_quantity"] <= seuil].copy()

    df_detail = df_detail[[
        "location_name", "product_title", "variant_sku", "variant_size", "available_quantity",
          "Lien Shopify"
    ]].rename(columns={
        "location_name": "Lieu",
        "product_title": "Produit",
        "variant_sku": "SKU",
        "variant_size": "Taille",
        "available_quantity": "Stock",
        "Lien Shopify": "Lien Shopify"
    })

    df_detail = df_detail.sort_values(by="Stock")

    st.dataframe(
        df_detail,
        use_container_width=True,
        height=500
    )