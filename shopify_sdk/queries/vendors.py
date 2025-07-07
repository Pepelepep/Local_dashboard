from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import streamlit as st
import json
from dotenv import load_dotenv
import os

load_dotenv()
def fetch_vendors_df():
    # Connexion Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Load from secrets
    json_creds_str = os.getenv('GCP_SERVICE_ACCOUNT')
    if not json_creds_str:
        raise ValueError("⚠️ Variable GCP_SERVICE_ACCOUNT manquante dans le fichier .env")

    json_creds = json.loads(json_creds_str)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_creds, scope)
    client = gspread.authorize(creds)

    # Ouverture du Google Sheet
    sheet_url = "https://docs.google.com/spreadsheets/d/1NATO1x_KlDUQ6F0vbD32xqM_hPsS0NqDawo3_CdcO0o"
    worksheet = client.open_by_url(sheet_url).worksheet("Business_rules")

    # Lecture en dataframe
    vendors_df = get_as_dataframe(worksheet, evaluate_formulas=True)
    vendors_df.rename(columns={"Supplier": "vendor"}, inplace=True)

    return vendors_df.dropna(how="all")