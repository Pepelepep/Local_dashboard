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
    products_df = load_table("products")[["variant_id", "product_title", "variant_title", "size", "vendor"]]
    df = df.merge(products_df, on="variant_id", how="left")

    # --- Nettoyage et typage
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["revenue"] = df["price"] * df["quantity"]
    df["vendor"] = df["vendor"].fillna("(Sans marque)")

    # --- Jour / heure
    df["date"] = df["created_at"].dt.date
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    cat_type = CategoricalDtype(categories=days_order, ordered=True)
    df["day_of_week"] = df["created_at"].dt.day_name().astype(cat_type)

    # --- Localisation horaire (Montréal)
    try:
        mtl_tz = pytz.timezone("America/Toronto")
        # si déjà aware, tz_convert; sinon, tz_localize
        if pd.Series(df["created_at"]).dt.tz is not None:
            df["created_at"] = df["created_at"].dt.tz_convert(mtl_tz)
        else:
            df["created_at"] = df["created_at"].dt.tz_localize(mtl_tz)
    except Exception:
        pass
    df["hour"] = df["created_at"].dt.hour

    # --- Filtre par lieu
    locations = df["location_name"].dropna().unique().tolist()
    locations.sort()
    locations.insert(0, "Tous")

    st.subheader("📅 Sélectionne une boutique et la période")
    col1, col2, col3 = st.columns(3)
    min_date = df["date"].min()
    max_date = df["date"].max()

    with col1:
        selected_location = st.selectbox("📍 Point de vente :", options=locations)
        if selected_location != "Tous":
            df = df[df["location_name"] == selected_location]

    with col2:
        start_date = st.date_input("Date de début", min_value=min_date, max_value=max_date, value=min_date)
    with col3:
        end_date = st.date_input("Date de fin", min_value=min_date, max_value=max_date, value=max_date)

    if start_date > end_date:
        st.error("❌ La date de début doit être antérieure à la date de fin.")
        return

    # --- Base all-time (respecte la boutique sélectionnée)
    df_alltime = df.copy()

    # --- Filtrage période
    filtered_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
    if filtered_df.empty:
        st.warning("Aucune donnée pour cette période.")
        return

    # =======================
    #  Courbe / Barres journalières
    # =======================
    daily_sales = (
        filtered_df.groupby("date", as_index=False)
        .agg(total_revenue=("revenue", "sum"), total_quantity=("quantity", "sum"))
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

    # =======================
    #  Heatmap heure x jour
    # =======================
    heatmap_data = (
        filtered_df.groupby(["day_of_week", "hour"], observed=True, as_index=False)
        .agg(avg_sales=("order_id", "nunique"))
    )
    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X("hour:O", title="Heure (0-23)"),
        y=alt.Y("day_of_week:N", title="Jour de la semaine", sort=days_order),
        color=alt.Color("avg_sales:Q", scale=alt.Scale(scheme='blues'), title="Nb ventes moyennes"),
        tooltip=["day_of_week", "hour", "avg_sales"]
    ).properties(width=700, height=300, title="📊 Ventes moyennes par heure et jour")
    st.altair_chart(heatmap, use_container_width=True)

    # =======================
    #  Top 10 produits + drilldown variants
    # =======================
    st.subheader("🏆 Top 10 des produits les plus vendus (cliquer un produit)")

    top_products = (
        filtered_df.groupby("product_title", dropna=False, as_index=False)
        .agg(total_quantity=("quantity", "sum"))
        .sort_values("total_quantity", ascending=False)
        .head(10)
    )
    variant_sales_all = (
        filtered_df.groupby(["product_title", "variant_title"], dropna=False, as_index=False)
        .agg(quantity=("quantity", "sum"))
    )

    select_prod = alt.selection_point(fields=["product_title"], on="click", clear="mouseup", nearest=True, empty=False)

    bar_top = (
        alt.Chart(top_products)
        .mark_bar(color="#1f77b4")
        .encode(
            x=alt.X("total_quantity:Q", title=None, axis=None),
            y=alt.Y("product_title:N", sort=alt.SortField(field="total_quantity", order="descending"), title="Produit"),
            tooltip=["product_title", "total_quantity"],
        )
        .add_params(select_prod)
    )
    text_top = (
        alt.Chart(top_products)
        .mark_text(color="white", fontWeight="bold", align="right", baseline="middle", dx=-6)
        .encode(
            x="total_quantity:Q",
            y=alt.Y("product_title:N", sort=alt.SortField(field="total_quantity", order="descending")),
            text=alt.Text("total_quantity:Q", format="d"),
        )
    )
    chart_top = bar_top + text_top

    detail_base = (
        alt.Chart(variant_sales_all)
        .transform_filter(select_prod)
        .transform_joinaggregate(product_total="sum(quantity)", groupby=["product_title"])
        .transform_calculate(
            pct="datum.quantity / datum.product_total * 100",
            label="datum.quantity + ' | ' + format(datum.quantity / datum.product_total * 100, '.2f') + '%'"
        )
    )
    variant_sort_desc = alt.SortField(field="quantity", order="descending")
    bar_detail = (
        detail_base.mark_bar(color="#ff7f0e")
        .encode(
            x=alt.X("quantity:Q", title=None, axis=None),
            y=alt.Y("variant_title:N", sort=variant_sort_desc, title="Variant / Taille"),
            tooltip=[alt.Tooltip("variant_title:N", title="Variant"),
                     alt.Tooltip("quantity:Q", title="Qté"),
                     alt.Tooltip("pct:Q", title="% du produit", format=".2f")],
        )
        .properties(width=800, height=240, title="Détail par variant (cliquer un produit au-dessus)")
    )
    text_detail = (
        detail_base.mark_text(color="white", fontWeight="bold", align="right", baseline="middle", dx=-6, fontSize=12)
        .encode(
            x="quantity:Q",
            y=alt.Y("variant_title:N", sort=variant_sort_desc),
            text="label:N",
        )
    )
    chart_detail = bar_detail + text_detail

    st.altair_chart(chart_top & chart_detail, use_container_width=True)

    # ===============================
    #  Ventes par marque (all-time) + drilldown variants
    # ===============================
    st.subheader("🏷️ Ventes par marque (all-time) et répartition par tailles")
    
    # Totaux marques (all-time, respecte le filtre boutique appliqué à df_alltime)
    brand_totals = (
        df_alltime.groupby("vendor", dropna=False, as_index=False)["quantity"]
        .sum()
        .rename(columns={"quantity": "total_sold"})
        .sort_values("total_sold", ascending=False)
    )
    
    brand_top15 = brand_totals.head(15)
    
    # --- Sélection Altair (clic sur une marque)
    select_brand = alt.selection_point(
        fields=["vendor"], on="click", nearest=True, clear="mouseup", empty=True
    )
    
    # --- Top 15 Marques (labels non tronqués, police plus grande)
    bar_brands = (
        alt.Chart(brand_top15)
        .mark_bar(color="#1f77b4")
        .encode(
            x=alt.X("total_sold:Q", title=None, axis=None),
            y=alt.Y(
                "vendor:N",
                sort=alt.SortField(field="total_sold", order="descending"),
                title="Marque",
                axis=alt.Axis(labelLimit=1000,  # pas de troncature
                              labelFontSize=14,
                              titleFontSize=14,
                              labelPadding=6)
            ),
            tooltip=[alt.Tooltip("vendor:N", title="Marque"),
                     alt.Tooltip("total_sold:Q", title="Nb vendus")]
        )
        .add_params(select_brand)
        .properties(width=900, height=340, title="🏆 Top 15 des marques (all-time)")
    )
    
    # Valeurs en blanc dans les barres
    text_brands = (
        alt.Chart(brand_top15)
        .mark_text(color="white", fontWeight="bold", align="right", baseline="middle", dx=-6, fontSize=13)
        .encode(
            x="total_sold:Q",
            y=alt.Y("vendor:N", sort=alt.SortField(field="total_sold", order="descending"),
                    axis=alt.Axis(labelLimit=1000, labelFontSize=14)),
            text=alt.Text("total_sold:Q", format="d"),
        )
    )
    
    st.altair_chart(bar_brands + text_brands, use_container_width=True)
    
    # --- Sélecteur placé SOUS le graphe (fallback clavier)
    brand_options = brand_totals["vendor"].tolist()
    default_index = 0 if len(brand_options) > 0 else None
    selected_brand = st.selectbox(
        "🔎 Choisir une marque pour la répartition des variants",
        options=brand_options,
        index=default_index,
    )
    
    # ===============================
    #  Détail par variants (variant_title) – filtré par CLIC OU selectbox
    # ===============================
    
    # Agrégat all-time par (marque, variant_title)
    brand_variant_all = (
        df_alltime.groupby(["vendor", "variant_title"], dropna=False, as_index=False)["quantity"]
        .sum()
        .rename(columns={"quantity": "sold_qty"})
    )
    
    # Base Altair avec filtre combiné + calcul % et label "Qté | %"
    detail_base = (
        alt.Chart(brand_variant_all)
        .transform_filter(select_brand | (alt.datum.vendor == selected_brand))
        .transform_joinaggregate(brand_total="sum(sold_qty)", groupby=["vendor"])
        .transform_calculate(
            pct_in_brand="datum.sold_qty / datum.brand_total * 100",
            label="datum.sold_qty + ' | ' + format(datum.sold_qty / datum.brand_total * 100, '.2f') + '%'"
        )
    )
    
    variant_sort_desc = alt.SortField(field="sold_qty", order="descending")
    
    bars_variants = (
        detail_base
        .mark_bar(color="#ff7f0e")
        .encode(
            x=alt.X("sold_qty:Q", title=None, axis=None),
            y=alt.Y("variant_title:N",
                    sort=variant_sort_desc,
                    title="Variant / Taille",
                    axis=alt.Axis(labelLimit=1000, labelFontSize=13, titleFontSize=13)),
            tooltip=[
                alt.Tooltip("vendor:N", title="Marque"),
                alt.Tooltip("variant_title:N", title="Variant / Taille"),
                alt.Tooltip("sold_qty:Q", title="Nb vendus"),
                alt.Tooltip("pct_in_brand:Q", title="% dans la marque", format=".2f"),
            ],
        )
        .properties(width=900, height=280, title="Répartition des variants (all-time)")
    )
    
    labels_variants = (
        detail_base
        .mark_text(color="white", fontWeight="bold", align="right", baseline="middle", dx=-6, fontSize=12)
        .encode(
            x="sold_qty:Q",
            y=alt.Y("variant_title:N", sort=variant_sort_desc,
                    axis=alt.Axis(labelLimit=1000, labelFontSize=13)),
            text="label:N",
        )
    )
    
    st.altair_chart(bars_variants + labels_variants, use_container_width=True)
    
    # ===============================
    #  Tableau : Marque | Variant / Taille | Nb vendus | % dans la marque
    #  (filtré par clic OU selectbox)
    # ===============================
    detail_df = (
        brand_variant_all
        .assign(_keep=1)  # pour éviter de toucher à l'Altair selection state, on filtre côté pandas pour le tableau
    )
    
    # Si une marque a été cliquée, on privilégie ce filtre ; sinon, le selectbox
    # (Streamlit ne donne pas l'état de select_brand, donc on s'aligne sur le selectbox côté table)
    detail_df = detail_df[detail_df["vendor"] == selected_brand]
    
    # Calcule % dans la marque pour le tableau
    brand_total = detail_df["sold_qty"].sum()
    detail_df["pct_in_brand"] = (detail_df["sold_qty"] / brand_total * 100).fillna(0)
    
    table_variants = (
        detail_df.rename(columns={
            "vendor": "Marque",
            "variant_title": "Variant / Taille",
            "sold_qty": "Nb vendus",
            "pct_in_brand": "% dans la marque"
        })
        .loc[:, ["Marque", "Variant / Taille", "Nb vendus", "% dans la marque"]]
        .sort_values("Nb vendus", ascending=False)
        .reset_index(drop=True)
    )
    
    st.dataframe(table_variants, use_container_width=True, hide_index=True)



    # =======================
    #  Détail des commandes récentes
    # =======================
    st.subheader("🧾 Détail des commandes récentes")
    recent_orders = filtered_df.sort_values("created_at", ascending=False).head(20)
    display_cols = ["order_name", "created_at", "product_title", "variant_title", "quantity", "price"]
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
