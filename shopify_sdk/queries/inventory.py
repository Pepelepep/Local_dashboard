# shopify_sdk/queries/inventory.py
import pandas as pd
import time
from gql import gql
from ..client import init_graphql_client
from ..utils import load_query

def fetch_inventory_levels_df(config):
    client = init_graphql_client(config["SHOP_NAME"], config["ACCESS_TOKEN"])
    query = gql(load_query("inventory.gql"))

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
                item = variant.get("inventoryItem", {})
                inventory_levels = item.get("inventoryLevels", {}).get("edges", [])

                for level in inventory_levels:
                    node = level["node"]
                    quantities = node.get("quantities", [])
                    available_qty = next((q["quantity"] for q in quantities if q["name"] == "available"), None)
                    updated_at = next((q["updatedAt"] for q in quantities if q["name"] == "available"), None)

                    rows.append({
                        "product_id": product["id"],
                        "product_title": product["title"],
                        "variant_id": variant["id"],
                        "variant_sku": variant.get("sku"),
                        "inventory_item_id": item.get("id"),
                        "inventory_sku": item.get("sku"),
                        "tracked": item.get("tracked"),
                        "requires_shipping": item.get("requiresShipping"),
                        "item_created_at": item.get("createdAt"),
                        "item_updated_at": item.get("updatedAt"),
                        "location_id": node["location"]["id"],
                        "location_name": node["location"]["name"],
                        "available_quantity": available_qty,
                        "quantity_updated_at": updated_at
                    })

        has_next = products["pageInfo"]["hasNextPage"]

    return pd.DataFrame(rows)