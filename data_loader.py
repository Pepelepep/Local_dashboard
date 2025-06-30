# data_loader.py
import pandas as pd
from fetch_graphql import fetch_products_df,fetch_stock_df, fetch_orders_df
from gspread_dataframe import get_as_dataframe
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import streamlit as st
import json

def fetch_vendors_df():
    # Connexion Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Load from secrets
    json_creds = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_creds, scope)
    client = gspread.authorize(creds)

    # Charger la page Business_rules
    spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1NATO1x_KlDUQ6F0vbD32xqM_hPsS0NqDawo3_CdcO0o")
    worksheet = spreadsheet.worksheet("Business_rules")
    vendors_df = get_as_dataframe(worksheet, evaluate_formulas=True)

    return vendors_df.dropna(how="all")

def fetch_datasets():
    products_df = fetch_products_df()
    stock_df = fetch_stock_df()
    orders_df = fetch_orders_df()
    vendors_df = fetch_vendors_df()
    return products_df, stock_df, orders_df, vendors_df


