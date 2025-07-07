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
                inventory_item = variant.get("inventoryItem", {})
                inventory_levels = inventory_item.get("inventoryLevels", {}).get("edges", [])
                for level in inventory_levels:
                    node = level["node"]
                    quantities = node.get("quantities", [])
                    available_qty = next((q["quantity"] for q in quantities if q["name"] == "available"), None)
                    updated_at_qty = next((q["updatedAt"] for q in quantities if q["name"] == "available"), None)
        
                    rows.append({
                        "product_id": product["id"],
                        "title": product["title"],
                        "vendor": product["vendor"],
                        "product_type": product["productType"],
                        "tags": ", ".join(product.get("tags", [])),
                        "product_updated_at": product.get("updatedAt"),
                        "variant_id": variant["id"],
                        "variant_title": variant["title"],
                        "sku": variant.get("sku"),
                        "price": variant.get("price"),
                        "variant_updated_at": variant.get("updatedAt"),
                        "inventory_item_id": inventory_item.get("id"),
                        "location": node["location"]["name"],
                        "available_quantity": available_qty,
                        "updatedAt": updated_at_qty
                    })

        has_next = products["pageInfo"]["hasNextPage"]

    return pd.DataFrame(rows)