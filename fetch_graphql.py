# fetch_graphql.py
import os
import pandas as pd
import requests
from dotenv import load_dotenv
import streamlit as st

SHOP_NAME = st.secrets["SHOP_NAME_TEC"]
ACCESS_TOKEN = st.secrets["SHOPIFY_API_TOKEN"]
GRAPHQL_URL = f"https://{SHOP_NAME}/admin/api/2024-01/graphql.json"
SHOP_NAME_LOCAL = st.secrets["SHOP_NAME_LOCAL"]

HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": ACCESS_TOKEN
}

# ----------------------------------------
# 1. PRODUCTS_DF
# ----------------------------------------
QUERY_PRODUCTS = """
query getProducts($cursor: String) {
  products(first: 50, after: $cursor) {
    pageInfo {
      hasNextPage
    }
    edges {
      cursor
      node {
        id
        title
        vendor
        productType
        tags
        variants(first: 10) {
          edges {
            node {
              id
              sku
              price
            }
          }
        }
      }
    }
  }
}
"""

def fetch_products_df():
    cursor, has_next = None, True
    rows = []
    while has_next:
        r = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": QUERY_PRODUCTS, "variables": {"cursor": cursor}})
        r.raise_for_status()
        data = r.json()["data"]["products"]
        for edge in data["edges"]:
            cursor = edge["cursor"]
            node = edge["node"]
            for v_edge in node["variants"]["edges"]:
                variant = v_edge["node"]
                rows.append({
                    "product_id": node["id"],
                    "title": node["title"],
                    "vendor": node["vendor"],
                    "product_type": node["productType"],
                    "tags": ", ".join(node["tags"]),
                    "variant_id": variant["id"],
                    "sku": variant["sku"],
                    "price": float(variant["price"])
                })
        has_next = data["pageInfo"]["hasNextPage"]
    return pd.DataFrame(rows)

# ----------------------------------------
# 2. STOCK_DF
# ----------------------------------------
QUERY_STOCK = """
query getProductStock($cursor: String) {
  products(first: 50, after: $cursor) {
    pageInfo {
      hasNextPage
    }
    edges {
      cursor
      node {
        variants(first: 10) {
          edges {
            node {
              id
              sku
              inventoryItem {
                tracked
                inventoryLevels(first: 5) {
                  edges {
                    node {
                      location {
                        name
                      }
                      quantities(names: ["available"]) {
                        name
                        quantity
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

def fetch_stock_df():
    cursor, has_next = None, True
    rows = []
    while has_next:
        r = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": QUERY_STOCK, "variables": {"cursor": cursor}})
        r.raise_for_status()
        data = r.json()["data"]["products"]
        for edge in data["edges"]:
            cursor = edge["cursor"]
            for v_edge in edge["node"]["variants"]["edges"]:
                variant = v_edge["node"]
                inv = variant.get("inventoryItem")
                if inv and inv.get("tracked"):
                    for lvl in inv.get("inventoryLevels", {}).get("edges", []):
                        node = lvl["node"]
                        qty = next((q["quantity"] for q in node.get("quantities", []) if q["name"] == "available"), None)
                        rows.append({
                            "variant_id": variant["id"],
                            "sku": variant["sku"],
                            "location": node["location"]["name"],
                            "available": qty
                        })
        has_next = data["pageInfo"]["hasNextPage"]
    return pd.DataFrame(rows)

# ----------------------------------------
# 3. ORDERS_DF
# ----------------------------------------
QUERY_ORDERS = """
query getOrders($cursor: String) {
  orders(first: 50, after: $cursor, reverse: true) {
    pageInfo {
      hasNextPage
    }
    edges {
      cursor
      node {
        id
        name
        createdAt
        lineItems(first: 10) {
          edges {
            node {
              title
              quantity
              sku
              originalUnitPrice
              discountedUnitPrice
            }
          }
        }
      }
    }
  }
}
"""

def fetch_orders_df():
    cursor, has_next = None, True
    rows = []
    while has_next:
        r = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": QUERY_ORDERS, "variables": {"cursor": cursor}})
        r.raise_for_status()
        data = r.json()["data"]["orders"]
        for edge in data["edges"]:
            cursor = edge["cursor"]
            o = edge["node"]
            for li in o["lineItems"]["edges"]:
                item = li["node"]
                rows.append({
                    "order_id": o["id"],
                    "order_name": o["name"],
                    "created_at": o["createdAt"],
                    "title": item["title"],
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "original_unit_price": float(item["originalUnitPrice"]),
                    "discounted_unit_price": float(item["discountedUnitPrice"])
                })
        has_next = data["pageInfo"]["hasNextPage"]
    return pd.DataFrame(rows)

