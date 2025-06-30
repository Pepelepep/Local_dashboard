# recommandation.py
import pandas as pd
from datetime import datetime, timedelta
import pytz

def compute_recommendations(products_df, stock_df, orders_df, vendors_df):
    orders_df['order_date'] = pd.to_datetime(orders_df['created_at'])
    sales_agg = orders_df.groupby(['sku', 'created_at']).agg({'quantity': 'sum'}).reset_index()
    today = datetime.now(pytz.UTC)

    def rolling_avg(df, days):
        cutoff = today - timedelta(days=days)
        return df[df['created_at'] >= cutoff].groupby('sku')['quantity'].mean().rename(f'avg_sales_{days}d')

    avg_sales_7d = rolling_avg(sales_agg, 7)
    avg_sales_14d = rolling_avg(sales_agg, 14)
    avg_sales_30d = rolling_avg(sales_agg, 30)

    sales_avg_df = avg_sales_7d.to_frame().join([avg_sales_14d, avg_sales_30d], how='outer').reset_index()

    df = stock_df.merge(sales_avg_df, on='sku', how='left')
    df = df.merge(products_df[['sku', 'title', 'vendor']], on='sku', how='left')
    df = df.merge(vendors_df[['Supplier', 'Delivery_Days']], left_on='vendor', right_on='Supplier', how='left')

    df['days_to_oos'] = df['available'] / df['avg_sales_7d']

    def classify_alert(row):
        if pd.isna(row['days_to_oos']) or row['avg_sales_7d'] == 0:
            return 'vert'
        elif row['days_to_oos'] <= row['Delivery_Days']:
            return 'rouge'
        elif row['days_to_oos'] <= row['Delivery_Days'] + 3:
            return 'orange'
        else:
            return 'vert'

    df['Alerte'] = df.apply(classify_alert, axis=1)

    return df[[
        'sku', 'title', 'vendor', 'available',
        'avg_sales_7d', 'avg_sales_14d', 'avg_sales_30d',
        'days_to_oos', 'Delivery_Days', 'Alerte'
    ]].sort_values(by=['Alerte', 'days_to_oos'])
