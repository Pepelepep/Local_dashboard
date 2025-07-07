import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('user')}:{os.getenv('password')}@{os.getenv('host')}:{os.getenv('port')}/{os.getenv('database')}"
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
