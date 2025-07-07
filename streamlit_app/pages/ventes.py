import streamlit as st
import pandas as pd
import altair as alt
from shopify_sdk.db.database import load_table

def render():
    st.title("📈 Ventes – Chiffre d'affaires")

    # --- Load data
    df = load_table("orders")

    # --- Nettoyage et typage
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["discounted_unit_price"] = pd.to_numeric(df["discounted_unit_price"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["revenue"] = df["discounted_unit_price"] * df["quantity"]
    df["date"] = df["created_at"].dt.date

    # --- Filtres de période
    st.subheader("📅 Sélectionne une période")
    col1, col2= st.columns(2)

    min_date = df["date"].min()
    max_date = df["date"].max()

    with col1:
        start_date = st.date_input("Date de début", min_value=min_date, max_value=max_date, value=min_date)
    
    with col2:
        end_date = st.date_input("Date de fin", min_value=min_date, max_value=max_date, value=max_date)
    
    if start_date > end_date:
        st.error("❌ La date de début doit être antérieure à la date de fin.")
        return

    # --- Filtrage
    filtered_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    if filtered_df.empty:
        st.warning("Aucune donnée pour cette période.")
        return

    # --- Agrégation par jour
    daily_sales = (
        filtered_df.groupby("date")
        .agg(
            total_revenue=pd.NamedAgg(column="revenue", aggfunc="sum"),
            total_quantity=pd.NamedAgg(column="quantity", aggfunc="sum")
        )
        .reset_index()
    )

    # --- Graphique combiné (barres + ligne avec axes indépendants)
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

    chart = alt.layer(bar, line).resolve_scale(
        y="independent"
    ).properties(width=750, height=400)

    st.altair_chart(chart, use_container_width=True)

    # --- Top 10 produits vendus
    st.subheader("🏆 Top 10 des produits les plus vendus")

    top_products = (
        df.groupby("title")
        .agg(total_quantity=("quantity", "sum"))
        .sort_values("total_quantity", ascending=False)
        .head(10)
        .reset_index()
    )

    bar_top = alt.Chart(top_products).mark_bar().encode(
        x=alt.X("total_quantity:Q", title="Quantité vendue"),
        y=alt.Y("title:N", sort='-x', title="Produit"),
        tooltip=["title:N", "total_quantity:Q"]
    ).properties(width=700, height=400)

    st.altair_chart(bar_top, use_container_width=True)

    # --- Table des commandes
    st.subheader("🧾 Détail des commandes récentes")

    recent_orders = df.sort_values("created_at", ascending=False).head(20)
    st.dataframe(recent_orders[[
        "order_name", "created_at", "title", "quantity", "discounted_unit_price", "vendor", "financial_status"
    ]].rename(columns={
        "order_name": "Commande",
        "created_at": "Date",
        "title": "Produit",
        "quantity": "Quantité",
        "discounted_unit_price": "Prix Unitaire (CAD $)",
        "vendor": "Marque",
        "financial_status": "Statut"
    }), use_container_width=True)
