import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

def get_pg_engine():
    """Connexion PostgreSQL via st.secrets"""
    return create_engine(
        f"postgresql://{st.secrets['user']}:{st.secrets['password']}@{st.secrets['host']}:{st.secrets['port']}/{st.secrets['database']}"
    )

def upsert_df_to_table(df: pd.DataFrame, table_name: str, key_columns: list):
    """UPSERT (insert or update) un DataFrame dans PostgreSQL"""
    engine = get_pg_engine()
    with engine.begin() as conn:
        # Create temp table
        temp_table = f"{table_name}_temp"
        df.to_sql(temp_table, con=conn, index=False, if_exists="replace")

        # Build upsert SQL
        cols = df.columns.tolist()
        updates = ", ".join([f"{col}=EXCLUDED.{col}" for col in cols if col not in key_columns])
        keys = ", ".join(key_columns)
        columns = ", ".join(cols)

        upsert_sql = text(f"""
            INSERT INTO {table_name} ({columns})
            SELECT {columns} FROM {temp_table}
            ON CONFLICT ({keys}) DO UPDATE SET {updates};
            DROP TABLE {temp_table};
        """)
        conn.execute(upsert_sql)
    print(f"✅ Upsert vers '{table_name}' terminé ({len(df)} lignes).")
