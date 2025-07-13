import pandas as pd
import time
from gql import gql
from ..client import init_graphql_client
from ..utils import load_query

def fetch_orders_line_items_df(config):
    client = init_graphql_client(config["SHOP_NAME"], config["ACCESS_TOKEN"])
    query = gql(load_query("orders.gql"))

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

        orders = result["orders"]

        for edge in orders["edges"]:
            cursor = edge["cursor"]
            order = edge["node"]

            order_id = order["id"]
            created_at = order["createdAt"]
            name = order["name"]
            status = order["displayFinancialStatus"]

            # Récupérer la première boutique (location) si présente
            fulfillments = order.get("fulfillments", [])
            location_name = (
                fulfillments[0]["location"]["name"]
                if fulfillments and fulfillments[0].get("location")
                else None
            )

            for li_edge in order["lineItems"]["edges"]:
                item = li_edge["node"]
                variant = item.get("variant")
                if variant is None:
                    continue  # ignorer les lignes sans SKU

                rows.append({
                    "order_id": order_id,
                    "created_at": created_at,
                    "order_name":name,
                    "line_item_id": item["id"],
                    "variant_id": variant["id"],
                    "sku": variant["sku"],
                    "quantity": item.get("quantity"),
                    "price": item.get("discountedUnitPriceSet", {}).get("shopMoney", {}).get("amount"),
                    "location_name": location_name,
                    "order_status" : status
                })

        has_next = orders["pageInfo"]["hasNextPage"]

    return pd.DataFrame(rows)
