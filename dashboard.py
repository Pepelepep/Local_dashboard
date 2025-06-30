# dashboard.py
import streamlit as st
import pandas as pd
import altair as alt
from data_loader import fetch_datasets
from recommandations import compute_recommendations  # <-- Nouveau module à créer

st.set_page_config(page_title="Shopify Dashboard", layout="wide")

# --- Chargement des données --- #
# 🔁 Bouton de rafraîchissement
if st.button("🔄 Rafraîchir les données Shopify"):
    products_df, stock_df, orders_df, vendors_df = fetch_datasets()
    orders_df["created_at"] = pd.to_datetime(orders_df["created_at"], utc=True)
    st.success("Données mises à jour avec succès ! ✅")
else:
    @st.cache_data
    def load_data():
        return fetch_datasets()
    products_df, stock_df, orders_df, vendors_df = load_data()
    orders_df["created_at"] = pd.to_datetime(orders_df["created_at"], utc=True)

# --- Layout --- #
st.title("📦 Tableau de bord Shopify")
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛍️ Produits", "📦 Stock", "📈 Ventes", "📊 Recommandations d’achat", "📋 Règles fournisseurs"
])

# --- Tab Produits --- #
with tab1:
    st.subheader("Catalogue produits")
    vendor_filter = st.multiselect("Filtrer par marque (vendor)", options=products_df["vendor"].unique())
    filtered_products = products_df[products_df["vendor"].isin(vendor_filter)] if vendor_filter else products_df
    st.dataframe(filtered_products)

# --- Tab Stock --- #
with tab2:
    st.subheader("Niveau de stock")
    threshold = st.slider("Seuil d'alerte de stock", min_value=0, max_value=20, value=5)
    low_stock = stock_df[stock_df["available"] <= threshold]
    st.warning(f"{len(low_stock)} produits avec un stock ≤ {threshold}")
    st.dataframe(low_stock)

    st.altair_chart(
        alt.Chart(stock_df)
        .mark_bar()
        .encode(
            x="available:Q",
            y=alt.Y("sku:N").sort("-x"),
            text=alt.Text("available"),
            color=alt.condition(
                alt.datum.available <= threshold,
                alt.value("crimson"),
                alt.value("steelblue")
            )
        ),
        use_container_width=True,
        )

# --- Tab Ventes --- #
with tab3:
    st.subheader("Ventes récentes")
    orders_df["created_at"] = pd.to_datetime(orders_df["created_at"])
    orders_df["day"] = orders_df["created_at"].dt.date
    orders_df["quantity"] = orders_df["quantity"].astype(int)

    nb_days = st.selectbox("Filtrer les ventes sur les derniers jours :", [7, 30, 90], index=1)
    recent_orders = orders_df[
        orders_df["created_at"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=nb_days)
        ]

    top_sales = recent_orders.groupby("title")["quantity"].sum().reset_index().sort_values("quantity", ascending=False)

    st.dataframe(top_sales.head(20), use_container_width=True)
    st.altair_chart(
        alt.Chart(top_sales.head(20))
        .mark_bar()
        .encode(
            x="quantity:Q",
            y=alt.Y("title:N").sort("-x")
        ),
        use_container_width=True
    )


# --- TAB RECOMMANDATIONS --- #
with tab4:
    st.subheader("📦 Recommandations d'achat (selon ventes et délais fournisseurs)")

    reco_df = compute_recommendations(products_df, stock_df, orders_df, vendors_df)

    # --- Interface --- #
    vendors = reco_df['vendor'].dropna().unique()
    vendor_filter = st.multiselect("Filtrer par marque", vendors, default=list(vendors))
    alerte_filter = st.multiselect("Filtrer par alerte", ['rouge', 'orange', 'vert'], default=['rouge', 'orange', 'vert'])

    filtered_df = reco_df[reco_df['vendor'].isin(vendor_filter) & reco_df['Alerte'].isin(alerte_filter)]

    st.dataframe(filtered_df[[
        'sku', 'title', 'vendor', 'available',
        'avg_sales_7d', 'avg_sales_14d', 'avg_sales_30d',
        'days_to_oos', 'Delivery_Days', 'Alerte'
    ]], use_container_width=True)

    st.subheader("📈 Nombre de produits par alerte")
    alert_counts = filtered_df['Alerte'].value_counts().reindex(['rouge', 'orange', 'vert'], fill_value=0)
    st.bar_chart(alert_counts)

# --- Tab Règles Fournisseurs --- #
with tab5:
    vendors_df["Payment_Term_Definition"] = vendors_df["Payment_Term_Definition"].astype(str)
    st.subheader("Règles fournisseurs personnalisées")
    st.markdown("Modifiez ce fichier dans Google Sheets pour appliquer vos règles de paiement, livraison, marge, etc.")
    st.dataframe(vendors_df)

