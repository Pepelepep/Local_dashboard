# import streamlit as st
# import pandas as pd
# from shopify_sdk.db.database import load_table
# 
# def render():
#     st.title("📦 Produits utilisés (vendus)")
# 
#     products_df = load_table("products")
#     stock_df = load_table("inventory")
#     orders_df = load_table("orders")
#     vendors_df = load_table("vendors")
#     orders_df["created_at"] = pd.to_datetime(orders_df["created_at"], utc=True)
# 
#     nb_days = st.selectbox("Période à afficher :", [7, 30, 90], index=1)
#     now = pd.Timestamp.now(tz="UTC")
#     recent_orders = orders_df[orders_df["created_at"] >= now - pd.Timedelta(days=nb_days)]
# 
#     used_products = (
#         recent_orders.groupby(["sku", "title"])
#         .agg({"quantity": "sum", "discounted_unit_price": "mean"})
#         .reset_index()
#         .sort_values("quantity", ascending=False)
#     )
#     used_products.rename(columns={"discounted_unit_price": "Prix moyen"}, inplace=True)
# 
#     st.dataframe(used_products)
