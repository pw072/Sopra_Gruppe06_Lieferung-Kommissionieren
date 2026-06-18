import pyodbc
import pandas as pd
import streamlit as st


def get_connection():
    cfg = st.secrets["mssql"]

    conn_str = (
        f"DRIVER={{{cfg['driver']}}};"
        f"SERVER={cfg['server']};"
        f"DATABASE={cfg['database']};"
        f"UID={cfg['username']};"
        f"PWD={cfg['password']};"
        f"TrustServerCertificate={cfg.get('trust_cert', 'yes')};"
    )

    return pyodbc.connect(conn_str)


def fetch_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql(sql, conn, params=params)
import pyodbc
import pandas as pd
import streamlit as st


def get_connection():
    cfg = st.secrets["mssql"]

    conn_str = (
        f"DRIVER={{{cfg['driver']}}};"
        f"SERVER={cfg['server']};"
        f"DATABASE={cfg['database']};"
        f"UID={cfg['username']};"
        f"PWD={cfg['password']};"
        f"TrustServerCertificate={cfg.get('trust_cert', 'yes')};"
    )

    return pyodbc.connect(conn_str)


import pyodbc
import pandas as pd
import streamlit as st


def get_connection():
    cfg = st.secrets["mssql"]

    conn_str = (
        f"DRIVER={{{cfg['driver']}}};"
        f"SERVER={cfg['server']};"
        f"DATABASE={cfg['database']};"
        f"UID={cfg['username']};"
        f"PWD={cfg['password']};"
        f"TrustServerCertificate={cfg.get('trust_cert', 'yes')};"
    )

    return pyodbc.connect(conn_str)


def fetch_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Führt eine SELECT-Abfrage aus und gibt das Ergebnis als Tabelle zurück."""
    with get_connection() as conn:
        return pd.read_sql(sql, conn, params=params)


def execute_scalar(sql: str, params: tuple = ()):
    """
    Führt eine Abfrage aus, die EINEN Wert zurückgibt
    (z. B. eine neue ID nach EXEC ... SELECT @id).
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_non_query(sql: str, params: tuple = ()):
    """
    Führt eine Anweisung aus, die KEIN Ergebnis zurückgibt
    (z. B. ein UPDATE oder eine Prozedur ohne SELECT am Ende).
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()