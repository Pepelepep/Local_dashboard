from shopify_sdk.config import get_shop_credentials
from shopify_sdk.queries.products import fetch_products_variants_df
from shopify_sdk.queries.orders import fetch_orders_line_items_df
from shopify_sdk.queries.inventory import fetch_inventory_levels_df
from shopify_sdk.queries.vendors import fetch_vendors_df
from shopify_sdk.db.database import upsert_table

def main():
    config = get_shop_credentials()

    print("🔄 Products...")
    upsert_table(fetch_products_variants_df(config), "products")

    print("🔄 Orders...")
    upsert_table(fetch_orders_line_items_df(config), "orders")

    print("🔄 Inventory...")
    upsert_table(fetch_inventory_levels_df(config), "inventory")

    print("🔄 Vendors...")
    upsert_table(fetch_vendors_df(), "vendors")

    print("✅ Données synchronisées avec succès vers PostgreSQL.")

if __name__ == "__main__":
    main()