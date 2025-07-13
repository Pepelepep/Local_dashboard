# scripts/test_queries.py
import pandas as pd
from shopify_sdk.config import get_shop_credentials
from shopify_sdk.queries.products import fetch_products_variants_df
from shopify_sdk.queries.orders import fetch_orders_line_items_df
from shopify_sdk.queries.inventory import fetch_inventory_levels_df

def main():
    config = get_shop_credentials()

    # print("\n✅ Testing PRODUCTS...")
    # products_df = fetch_products_variants_df(config)
    # print(products_df.head())
    # print(f"✔ {len(products_df)} product variants loaded.\n")

    print("\n✅ Testing ORDERS...")
    orders_df = fetch_orders_line_items_df(config)
    print(orders_df.head())
    print(f"✔ {len(orders_df)} line items loaded.\n")
    # 
    # print("\n✅ Testing INVENTORY...")
    # inventory_df = fetch_inventory_levels_df(config)
    # print(inventory_df.head())
    # print(f"✔ {len(inventory_df)} inventory rows loaded.\n")

if __name__ == "__main__":
    main()
