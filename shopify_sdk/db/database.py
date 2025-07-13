import os
import pandas as pd
from sqlalchemy import create_engine, text

def get_db_config():
    """
    Charge la config depuis les variables d'environnement OU les secrets Streamlit.
    (Compatible Github Actions et local)
    """
    # On essaye d'abord les env Github Actions
    config = {
        "user": os.getenv("USER") or os.getenv("user"),
        "password": os.getenv("PASSWORD") or os.getenv("password"),
        "host": os.getenv("HOST") or os.getenv("host"),
        "port": os.getenv("PORT") or os.getenv("port"),
        "database": os.getenv("DATABASE") or os.getenv("database"),
    }
    # (optionnel) tu peux ajouter un fallback Streamlit ici si tu veux compatibilité locale
    # import streamlit as st
    # for k in config:
    #     if not config[k] and k in st.secrets:
    #         config[k] = st.secrets[k]
    return config

def get_engine():
    cfg = get_db_config()
    # ⚠️ On force la conversion de port
    port = int(cfg["port"]) if cfg["port"] is not None else 5432
    return create_engine(
        f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{port}/{cfg['database']}"
    )

def upsert_table(df: pd.DataFrame, table_name: str):
    """
    Remplace les données de la table `table_name` avec le DataFrame fourni.
    """
    engine = get_engine()
    with engine.begin() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"✅ Table `{table_name}` upsertée ({len(df)} lignes)")

def load_table(table_name: str) -> pd.DataFrame:
    """
    Charge la table `table_name` depuis la base PostgreSQL.
    """
    engine = get_engine()
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)
