import streamlit as st
import pandas as pd
import io
from shopify_sdk.db.database import load_table
from shopify_sdk.recommandations.core import compute_recommendations


def render():
    st.title("🤖 Recommandations d’achat intelligentes")

    # --- Chargement des données sources
    products_df = load_table("products")
    stock_df = load_table("inventory")
    orders_df = load_table("orders")
    vendors_df = load_table("vendors")

    # =============== Meta produits : date d'ajout (tolérant aux schémas) ===============
    # On détecte une colonne de création disponible dans la table products
    candidate_created_cols = ["product_created_at", "createdAt", "product_createdAt", "created_at"]
    created_col = next((c for c in candidate_created_cols if c in products_df.columns), None)

    # Prépare le mini-DF pour le merge (uniquement les colonnes réellement présentes)
    meta_cols = []
    if "variant_id" in products_df.columns:
        meta_cols.append("variant_id")
    if "product_id" in products_df.columns:
        meta_cols.append("product_id")
    if created_col:
        meta_cols.append(created_col)

    if meta_cols:
        prod_dates = products_df.loc[:, meta_cols].copy()
        if created_col:
            prod_dates.rename(columns={created_col: "product_created_at"}, inplace=True)
            prod_dates["product_created_at"] = pd.to_datetime(prod_dates["product_created_at"], errors="coerce")
    else:
        prod_dates = pd.DataFrame(columns=["variant_id", "product_id", "product_created_at"])

    # =============== Calcul des recommandations ===============
    df = compute_recommendations(products_df, stock_df, orders_df, vendors_df)

    # Merge de la date d’ajout (priorité à variant_id, sinon product_id) — seulement si TOUTES les colonnes requises existent
    merged_created = False
    if not prod_dates.empty:
        if all(col in df.columns for col in ["variant_id"]) and \
                all(col in prod_dates.columns for col in ["variant_id", "product_created_at"]):
            df = df.merge(prod_dates[["variant_id", "product_created_at"]], on="variant_id", how="left")
            merged_created = True
        elif all(col in df.columns for col in ["product_id"]) and \
                all(col in prod_dates.columns for col in ["product_id", "product_created_at"]):
            df = df.merge(prod_dates[["product_id", "product_created_at"]], on="product_id", how="left")
            merged_created = True

    # Garantit l'existence de la colonne même si pas (encore) disponible
    if "product_created_at" not in df.columns:
        df["product_created_at"] = pd.NaT

    # Typage date + helper "jours depuis création"
    df["product_created_at"] = pd.to_datetime(df["product_created_at"], errors="coerce")
    now = pd.Timestamp.now(tz=None)
    df["days_since_creation"] = (now - df["product_created_at"]).dt.days

    if not merged_created:
        st.info("ℹ️ La date d’ajout du produit n’est pas encore disponible dans la base (champ `product_created_at`). "
                "Le filtre « Ajoutés dans les 30 derniers jours » sera vide tant que l’extraction n’aura pas été rejouée "
                "avec le champ GraphQL `createdAt`.")

    # --- Calcul de la quantité à commander
    df["Quantité à commander"] = (
            (df["mean_sales"] * df["Delivery_Days"]) - df["available"]
    ).round().clip(lower=0).astype(int)

    # ===================== Filtres =====================
    col1, col2, col3 = st.columns(3)

    # Lieu de stockage
    locations = sorted(df["location_name"].dropna().unique().tolist())
    all_locations = ["Tous"] + locations
    with col1:
        selected_location = st.selectbox("📍 Lieu de stockage", options=all_locations, index=0)
        if selected_location != "Tous":
            df = df[df["location_name"] == selected_location]

    # Alerte & Marques
    with col2:
        selected_alerts = st.multiselect(
            "🚨 Alertes", options=["rouge", "orange", "vert"], default=["rouge", "orange", "vert"]
        )
        df = df[df["Alerte"].isin(selected_alerts)]

    with col3:
        vendors = sorted(df["vendor"].dropna().unique().tolist())
        all_vendors = ["Tous"] + vendors
        selected_vendors = st.multiselect("🏷️ Marques", options=all_vendors, default=["Tous"])
        if "Tous" not in selected_vendors:
            df = df[df["vendor"].isin(selected_vendors)]

    # Filtres complémentaires
    col4, col5, col6 = st.columns(3)

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

    with col6:
        last_30_only = st.checkbox("🆕 Ajoutés dans les 30 derniers jours", value=False)
        if last_30_only:
            df = df[df["product_created_at"].notna() & (df["days_since_creation"] <= 30)]

    # ===================== Tableau =====================
    st.subheader("📋 Variantes recommandées à commander")

    # On inclut la date d’ajout si présente
    cols_for_view = [
        "🟡", "vendor", "product_title", "variant_title", "sku", "location_name",
        "available", "avg_sales_30d", "mean_sales", "Delivery_Days",
        "Quantité à commander", "days_to_oos", "Score Importance", "product_created_at"
    ]
    cols_for_view = [c for c in cols_for_view if c in df.columns]

    display_df = df[cols_for_view].rename(columns={
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
        "days_to_oos": "Jours avant rupture",
        "product_created_at": "Ajouté le",
    })

    # Format lisible pour la date d’ajout (si colonne présente)
    if "Ajouté le" in display_df.columns:
        display_df["Ajouté le"] = pd.to_datetime(display_df["Ajouté le"], errors="coerce").dt.date

    display_df = display_df.sort_values("Score Importance", ascending=False)

    st.dataframe(display_df, use_container_width=True, height=600)

    # --- Export CSV (UTF-8 BOM + ; comme séparateur)
    csv_buffer = io.StringIO()
    display_df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')

    st.download_button(
        label="⬇️ Exporter en CSV",
        data=csv_buffer.getvalue(),
        file_name="recommandations_achat_utf8.csv",
        mime="text/csv"
    )
