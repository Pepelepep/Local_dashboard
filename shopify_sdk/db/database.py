import os
import pandas as pd
from sqlalchemy import create_engine, text

def get_db_config():
    """
    Lit la config DB : d'abord Streamlit, sinon env, sinon crash.
    """
    config = {}
    # 1️⃣ Essaye Streamlit secrets (le plus simple si tu lances via streamlit run)
    try:
        import streamlit as st
        secrets = st.secrets
        config["user"] = secrets.get("user", None)
        config["password"] = secrets.get("password", None)
        config["host"] = secrets.get("host", None)
        config["port"] = secrets.get("port", 5432)
        config["database"] = secrets.get("database", None)
    except (ModuleNotFoundError, AttributeError):
        # 2️⃣ Sinon variables d'environnement
        config["user"] = os.getenv("USER") or os.getenv("user")
        config["password"] = os.getenv("PASSWORD") or os.getenv("password")
        config["host"] = os.getenv("HOST") or os.getenv("host")
        config["port"] = os.getenv("PORT") or os.getenv("port", 5432)
        config["database"] = os.getenv("DATABASE") or os.getenv("database")

    # Sécurité : cast du port
    if config["port"] is not None:
        config["port"] = int(str(config["port"]))
    else:
        config["port"] = 5432

    # Sécurité : crash clair si manque une info
    for k in ["user", "password", "host", "database"]:
        if not config[k]:
            raise ValueError(f"⚠️ Variable de config DB manquante : {k}")

    return config

def get_engine():
    cfg = get_db_config()
    return create_engine(
        f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )

def upsert_table(df: pd.DataFrame, table_name: str):
    engine = get_engine()
    with engine.begin() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"✅ Table `{table_name}` upsertée ({len(df)} lignes)")

def load_table(table_name: str) -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)