import time
import re
from gql import gql
from ..client import init_graphql_client
from ..utils import load_query
from ..config import get_shop_credentials

# ------------------------------
# Utils
# ------------------------------
def slugify(text):
    text = re.sub(r"[^\w]+", "-", text.upper())
    return text[:12]


def generate_sku(product, variant):
    vendor = slugify(product.get("vendor", ""))
    ptype = slugify(product.get("productType", ""))
    title = slugify(product.get("title", ""))
    suffix = variant["id"][-6:]
    return f"{vendor}-{ptype}-{title}-{suffix}"

# ------------------------------
# Mutation : Update SKU
# ------------------------------
def update_sku_on_shopify(client, variant_id, new_sku):
    mutation = gql(load_query("mutations.qgl"))
    variables = {"input": {"id": variant_id, "sku": new_sku}}
    result = client.execute(mutation, variable_values=variables)
    errors = result["productVariantUpdate"].get("userErrors", [])
    if errors:
        print(f"❌ {variant_id} → {new_sku} : {errors}")
    else:
        print(f"✅ {variant_id} → {new_sku}")


# ------------------------------
# Main loop : Fetch & Apply
# ------------------------------
def process_all_products():
    config = get_shop_credentials()
    client = init_graphql_client(config["SHOP_NAME"], config["ACCESS_TOKEN"])

    query = gql(load_query("products_basic.gql"))
    cursor, has_next = None, True

    while has_next:
        result = client.execute(query, variable_values={"cursor": cursor})
        products = result["products"]

        for edge in products["edges"]:
            cursor = edge["cursor"]
            product = edge["node"]
            for v_edge in product["variants"]["edges"]:
                variant = v_edge["node"]
                new_sku = generate_sku(product, variant)
                update_sku_on_shopify(client, variant["id"], new_sku)
                time.sleep(0.5)  # évite throttling Shopify

        has_next = products["pageInfo"]["hasNextPage"]


if __name__ == "__main__":
    process_all_products()