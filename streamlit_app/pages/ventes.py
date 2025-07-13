import streamlit as st
import pandas as pd
from pandas.api.types import CategoricalDtype
import altair as alt
import pytz
from shopify_sdk.db.database import load_table

def render():
    st.title("📈 Ventes – Chiffre d'affaires")

    # --- Load data
    df = load_table("orders")
    products_df = load_table("products")[["variant_id", "product_title","variant_title","size","vendor"]]
    df = df.merge(products_df, on="variant_id", how="left")

    # --- Nettoyage et typage
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["revenue"] = df["price"] * df["quantity"]
    df["date"] = df["created_at"].dt.date

    # --- Créer le jour de la semaine avec l'ordre voulu
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    cat_type = CategoricalDtype(categories=days_order, ordered=True)
    df["day_of_week"] = df["created_at"].dt.day_name().astype(cat_type)

    # --- Localisation horaire (Montréal)
    mtl_tz = pytz.timezone("America/Toronto")
    df["created_at"] = df["created_at"].dt.tz_convert(mtl_tz)
    df["hour"] = df["created_at"].dt.hour

    # --- Filtre par lieu
    locations = df["location_name"].dropna().unique().tolist()
    locations.sort()
    locations.insert(0, "Tous")  # Ajoute "Tous" en premier
        
    # --- Filtres de période
    st.subheader("📅 Sélectionne une boutique et la période")
    col1, col2, col3 = st.columns(3)
    min_date = df["date"].min()
    max_date = df["date"].max()
    with col1:
        selected_location = st.selectbox("📍 Point de vente :", options=locations)

        # Applique le filtre uniquement si un lieu spécifique est choisi
        if selected_location != "Tous":
            df = df[df["location_name"] == selected_location]
    with col2:
        start_date = st.date_input("Date de début", min_value=min_date, max_value=max_date, value=min_date)
    with col3:
        end_date = st.date_input("Date de fin", min_value=min_date, max_value=max_date, value=max_date)

    if start_date > end_date:
        st.error("❌ La date de début doit être antérieure à la date de fin.")
        return

    # --- Filtrage
    filtered_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
    if filtered_df.empty:
        st.warning("Aucune donnée pour cette période.")
        return

    # --- Agrégation par jour
    daily_sales = (
        filtered_df.groupby("date")
        .agg(total_revenue=pd.NamedAgg(column="revenue", aggfunc="sum"),
             total_quantity=pd.NamedAgg(column="quantity", aggfunc="sum"))
        .reset_index()
    )

    st.subheader("📊 Ventes (barres) et chiffre d'affaires (ligne) par jour")
    bar = alt.Chart(daily_sales).mark_bar(color="#1f77b4").encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("total_quantity:Q", axis=alt.Axis(title="Quantité vendue")),
        tooltip=["date:T", "total_quantity"]
    )
    line = alt.Chart(daily_sales).mark_line(color="#ff7f0e", point=True).encode(
        x="date:T",
        y=alt.Y("total_revenue:Q", axis=alt.Axis(title="Chiffre d'affaires (CA)")),
        tooltip=["date:T", "total_revenue"]
    )
    st.altair_chart(alt.layer(bar, line).resolve_scale(y="independent"), use_container_width=True)

    # Aggrégation
    heatmap_data = (
        filtered_df.groupby(["day_of_week", "hour"], observed=True)
        .agg(avg_sales=("order_id", "nunique"))
        .reset_index()
    )
    
    # Heatmap
    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X("hour:O", title="Heure (0-23)"),
        y=alt.Y("day_of_week:N", title="Jour de la semaine", sort=days_order),
        color=alt.Color("avg_sales:Q", scale=alt.Scale(scheme='blues'), title="Nb ventes moyennes"),
        tooltip=["day_of_week", "hour", "avg_sales"]
    ).properties(
        width=700,
        height=300,
        title="📊 Ventes moyennes par heure et jour"
    )
    
    st.altair_chart(heatmap, use_container_width=True)
    
    # --- Top produits
    st.subheader("🏆 Top 10 des produits les plus vendus")
    top_products = filtered_df.groupby("sku").agg(
        total_quantity=("quantity", "sum")
    ).reset_index().sort_values("total_quantity", ascending=False).head(10)
    
    bar_top = alt.Chart(top_products).mark_bar().encode(
        x="total_quantity:Q", y=alt.Y("sku:N", sort='-x'), tooltip=["sku", "total_quantity"]
    ).properties(width=700, height=400)
    
    st.altair_chart(bar_top, use_container_width=True)
    
    
    
    # --- Détail des commandes
    st.subheader("🧾 Détail des commandes récentes")
    recent_orders = filtered_df.sort_values("created_at", ascending=False).head(20)
    display_cols = ["order_name", "created_at", "product_title","variant_title", "quantity", "price"]
    if "vendor" in recent_orders.columns:
        display_cols.append("vendor")
    
    st.dataframe(
        recent_orders[display_cols].rename(columns={
            "order_name": "Commande",
            "created_at": "Date",
            "vendor": "Marque",
            "product_title": "Produit",
            "variant_title": "Taille",
            "quantity": "Quantité",
            "price": "Prix Unitaire (CAD $)"
        }),
        use_container_width=True
    )

