import streamlit as st
import pandas as pd
from shopify_sdk.db.database import load_table

def render():
    st.title("📦 Vue Stock – Produits et Disponibilité")

    # --- Load data
    df = load_table("inventory")
    
    # Charger les produits
    products_df = load_table("products")[["variant_id", "product_id","product_title","variant_title","size","vendor"]]
    df = df.merge(products_df, on="variant_id", how="left")

    # --- Nettoyage
    df["available"] = pd.to_numeric(df["available"], errors="coerce").fillna(0).astype(int)
    df["location_name"] = df["location_name"].fillna("Non défini")
    df["variant_id"] = df["variant_id"].fillna("")

    # --- Extraire les IDs numériques
    df["product_num_id"] = df["product_id"].str.extract(r"/Product/(\d+)")
    df["variant_num_id"] = df["variant_id"].str.extract(r"/ProductVariant/(\d+)")

    # --- Construire le lien Produit
    df["Lien Shopify Produit"] = df.apply(
        lambda row: (
            f"https://admin.shopify.com/store/{st.secrets['SHOP']}/products/{row['product_num_id']}"
            if pd.notnull(row["product_num_id"]) and pd.notnull(row["variant_num_id"]) else None
        ), axis=1
    )
    
    # --- Construire le lien Shopify du variant
    df["Lien Shopify Variant"] = df.apply(
        lambda row: (
            f"https://admin.shopify.com/store/{st.secrets['SHOP']}/products/{row['product_num_id']}/variants/{row['variant_num_id']}"
            if pd.notnull(row["product_num_id"]) and pd.notnull(row["variant_num_id"]) else None
        ), axis=1
    )

    # --- Filtre par lieu
    locations = df["location_name"].dropna().unique().tolist()
    locations.sort()
    locations.insert(0, "Tous")  # Ajoute "Tous" en premier
    
    selected_location = st.selectbox("📍 Filtrer par lieu de stockage :", options=locations)
    
    # Applique le filtre uniquement si un lieu spécifique est choisi
    if selected_location != "Tous":
        df = df[df["location_name"] == selected_location]

    # --- Seuil
    seuil = st.slider("🔻 Seuil critique de stock :", min_value=0, max_value=20, value=5)

    # --- Regroupement par produit
    grouped = df.groupby(["product_title"]).agg(
        total_variants=("variant_id", "nunique"),
        total_stock=("available", "sum"),
        variants_below_threshold=("available", lambda x: (x <= seuil).sum()),
        product_url=("Lien Shopify Produit", "first")
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

    styled_table = grouped.sort_values(by="variants_below_threshold", ascending=False).head(20)[[
        "Alerte", "product_title", "total_variants",
        "variants_below_threshold", "total_stock", "product_url"
    ]].rename(columns={
        "product_title": "Produit",
        "total_variants": "Nb Variantes",
        "variants_below_threshold": "Sous seuil",
        "total_stock": "Stock total",
        "product_url": "Lien Shopify Produit"
    })

    st.dataframe(
        styled_table,
        use_container_width=True,
        height=600
    )

    # --- Détail par SKU sous le seuil
    st.subheader("🧾 Détail des variantes sous le seuil")

    df_detail = df[df["available"] <= seuil].copy()

    df_detail = df_detail[[
        "location_name", "product_title","variant_title", "available", "Lien Shopify Variant"
    ]].rename(columns={
        "location_name": "Lieu",
        "product_title": "Produit",
        "variant_title": "variant",
        "available": "Stock",
        "Lien Shopify": "Lien Shopify Variant"
    })

    df_detail = df_detail.sort_values(by="Stock")

    st.dataframe(
        df_detail,
        use_container_width=True,
        height=500
    )
