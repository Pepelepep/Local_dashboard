import pandas as pd

def compute_recommendations(products_df, stock_df, orders_df, vendors_df):
    vendors_df = vendors_df.rename(columns={"Supplier": "vendor"}) if "Supplier" in vendors_df.columns else vendors_df

    # --- Ajout du champ variant_size depuis stock_df
    df = stock_df.merge(
        products_df[["sku", "title", "vendor"]],
        left_on="variant_sku", right_on="sku", how="left"
    )

    df = df.merge(vendors_df, on="vendor", how="left")

    # --- Ajout du champ taille (optionnel pour clarté visuelle)
    if "variant_size" in stock_df.columns:
        df["variant_size"] = stock_df["variant_size"]

    # --- Calcul des ventes moyennes
    orders_df["created_at"] = pd.to_datetime(orders_df["created_at"], utc=True)
    now = pd.Timestamp.now(tz="UTC")

    for days in [7, 14, 30]:
        recent_orders = orders_df[orders_df["created_at"] >= now - pd.Timedelta(days=days)]
        sales = recent_orders.groupby("sku")["quantity"].sum() / days
        df[f"avg_sales_{days}d"] = df["variant_sku"].map(sales).fillna(0)

    df["mean_sales"] = df[["avg_sales_7d", "avg_sales_14d", "avg_sales_30d"]].mean(axis=1)
    df["mean_sales"] = df["mean_sales"].replace(0, 0.01)

    df["Delivery_Days"] = pd.to_numeric(df.get("Delivery_Days", 7), errors="coerce").fillna(7).astype(int)
    df["days_to_oos"] = df["available_quantity"] / df["mean_sales"]

    def tag(row):
        if row["available_quantity"] == 0:
            return "rouge"
        elif row["days_to_oos"] <= row["Delivery_Days"]:
            return "orange"
        else:
            return "vert"

    df["Alerte"] = df.apply(tag, axis=1)
    df["Ventes récentes"] = df["avg_sales_30d"] > 0
    df["\u00c0 recommander"] = (df["Ventes récentes"]) & (df["Alerte"].isin(["rouge", "orange"]))

    # Score d’importance (normalisé)
    df["norm_sales"] = df["avg_sales_30d"] / df["avg_sales_30d"].max()
    df["norm_delai"] = df["Delivery_Days"] / df["Delivery_Days"].max()
    df["norm_stock"] = 1 / (df["available_quantity"] + 1)

    df["Score Importance"] = (
            0.5 * df["norm_sales"] +
            0.3 * df["norm_delai"] +
            0.2 * df["norm_stock"]
    ).round(3)

    df["🟡"] = df["Alerte"].map({"rouge": "🔴", "orange": "🟠", "vert": "🟢"})

    # --- Suppression des doublons connus
    df = df.drop_duplicates(subset=["variant_sku", "location_name", "vendor"])

    return df