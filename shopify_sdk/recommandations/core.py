import pandas as pd

def compute_recommendations(products_df, stock_df, orders_df, vendors_df):
    # --- Harmonisation du nom de fournisseur si besoin
    if "Supplier" in vendors_df.columns:
        vendors_df = vendors_df.rename(columns={"Supplier": "vendor"})

    # --- Merge stock <-> produits
    df = pd.merge(stock_df, products_df, on="variant_id", how="left")

    # --- Merge stock/produits <-> vendors (règles fournisseurs)
    df = pd.merge(df, vendors_df, left_on="vendor", right_on="vendor", how="left")

    # --- Ajout du champ taille (optionnel)
    if "variant_size" in stock_df.columns:
        df["variant_size"] = stock_df["variant_size"]

    # --- Calcul des moyennes mobiles de ventes (7j, 14j, 30j) par SKU
    orders_df["created_at"] = pd.to_datetime(orders_df["created_at"], utc=True)
    now = pd.Timestamp.now(tz="UTC")
    for days in [7, 14, 30]:
        recent_orders = orders_df[orders_df["created_at"] >= now - pd.Timedelta(days=days)]
        sales = recent_orders.groupby("sku")["quantity"].sum() / days
        df[f"avg_sales_{days}d"] = df["sku"].map(sales).fillna(0)

    # --- Moyenne mobile globale
    df["mean_sales"] = df[["avg_sales_7d", "avg_sales_14d", "avg_sales_30d"]].mean(axis=1)
    df["mean_sales"] = df["mean_sales"].replace(0, 0.01)  # éviter la division par zéro

    # --- Récupération ou fallback du délai fournisseur
    df["Delivery_Days"] = pd.to_numeric(df.get("Delivery_Days", 7), errors="coerce").fillna(7).astype(int)

    # --- Jours avant OOS (Out Of Stock)
    df["days_to_oos"] = df["available"] / df["mean_sales"]

    # --- Niveau d’alerte basé sur le stock et délai fournisseur
    def tag(row):
        if row["available"] == 0:
            return "rouge"
        elif row["days_to_oos"] <= row["Delivery_Days"]:
            return "orange"
        else:
            return "vert"
    df["Alerte"] = df.apply(tag, axis=1)

    # --- Ventes récentes
    df["Ventes récentes"] = df["avg_sales_30d"] > 0
    df["À recommander"] = (df["Ventes récentes"]) & (df["Alerte"].isin(["rouge", "orange"]))

    # --- Score d’importance (priorisation, pondération paramétrable)
    df["norm_sales"] = df["avg_sales_30d"] / (df["avg_sales_30d"].max() or 1)
    df["norm_delai"] = df["Delivery_Days"] / (df["Delivery_Days"].max() or 1)
    df["norm_stock"] = 1 / (df["available"] + 1)
    df["Score Importance"] = (
            0.5 * df["norm_sales"] +
            0.3 * df["norm_delai"] +
            0.2 * df["norm_stock"]
    ).round(3)

    # --- Emoji/pastille d’alerte
    df["🟡"] = df["Alerte"].map({"rouge": "🔴", "orange": "🟠", "vert": "🟢"})

    # --- Suppression des doublons connus
    # df = df.drop_duplicates(subset=["variant_sku", "location_name", "vendor"])

    return df
