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
            for li_edge in order["lineItems"]["edges"]:
                item = li_edge["node"]

                rows.append({
                    "order_id": order["id"],
                    "order_name": order["name"],
                    "created_at": order["createdAt"],
                    "email": order.get("email"),
                    "financial_status": order.get("displayFinancialStatus"),
                    "fulfillment_status": order.get("displayFulfillmentStatus"),
                    "tags": ", ".join(order.get("tags", [])),

                    "line_item_id": item["id"],
                    "title": item["title"],
                    "sku": item.get("sku"),
                    "vendor": item.get("vendor"),
                    "quantity": item.get("quantity"),
                    "original_unit_price": item.get("originalUnitPriceSet", {}).get("shopMoney", {}).get("amount"),
                    "original_currency": item.get("originalUnitPriceSet", {}).get("shopMoney", {}).get("currencyCode"),
                    "discounted_unit_price": item.get("discountedUnitPriceSet", {}).get("shopMoney", {}).get("amount"),
                    "discounted_currency": item.get("discountedUnitPriceSet", {}).get("shopMoney", {}).get("currencyCode"),
                    "unfulfilled_quantity": item.get("unfulfilledQuantity")
                })

        has_next = orders["pageInfo"]["hasNextPage"]

    return pd.DataFrame(rows)