from gql import Client
from gql.transport.requests import RequestsHTTPTransport

def init_graphql_client(shop_name, access_token):
    url = f"https://{shop_name}/admin/api/2024-01/graphql.json"
    transport = RequestsHTTPTransport(
        url=url,
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        },
        retries=3,
    )
    return Client(transport=transport, fetch_schema_from_transport=False)