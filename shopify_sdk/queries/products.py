import pandas as pd
import time
from gql import gql
from ..client import init_graphql_client
from ..utils import load_query

def fetch_products_variants_df(config):
    client = init_graphql_client(config["SHOP_NAME"], config["ACCESS_TOKEN"])
    query = gql(load_query("products.gql"))

    cursor, has_next = None, True
    rows = []

    while has_next:
        try:
            result = client.execute(query, variable_values={"cursor": cursor})
        except Exception as e:
            if "Throttled" in str(e):
                print("⏳ Throttled — pause de 2 secondes")
                time.sleep(2)
                continue
            else:
                raise e

        products = result["products"]
        for edge in products["edges"]:
            cursor = edge["cursor"]
            product = edge["node"]

            for v_edge in product["variants"]["edges"]:
                variant = v_edge["node"]

                size_option = next(
                    (opt["value"] for opt in variant.get("selectedOptions", []) if opt["name"] == "Taille"),
                    None
                )

                rows.append({
                    "product_id": product["id"],
                    "product_title": product["title"],
                    "product_type": product.get("productType"),
                    "vendor": product.get("vendor"),
                    "product_created_at": product.get("createdAt"),   # <-- AJOUTÉ
                    "product_updated_at": product.get("updatedAt"),
                    "variant_id": variant["id"],
                    "variant_title": variant.get("title"),
                    "sku": variant.get("sku"),
                    "price": variant.get("price"),
                    "variant_updated_at": variant.get("updatedAt"),
                    "size": size_option
                })

        has_next = products["pageInfo"]["hasNextPage"]

    df = pd.DataFrame(rows)
    # parsage utile pour la suite
    if "product_created_at" in df.columns:
        df["product_created_at"] = pd.to_datetime(df["product_created_at"], errors="coerce")
    if "product_updated_at" in df.columns:
        df["product_updated_at"] = pd.to_datetime(df["product_updated_at"], errors="coerce")
    if "variant_updated_at" in df.columns:
        df["variant_updated_at"] = pd.to_datetime(df["variant_updated_at"], errors="coerce")
    return df
