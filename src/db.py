"""Conexão SQL Server + listas para dropdowns."""
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from .config import get_db_credentials

@st.cache_resource
def get_engine():
    cred = get_db_credentials()
    url = f"mssql+pymssql://{cred['username']}:{cred['password']}@{cred['server']}:{cred['port']}/{cred['database']}"
    return create_engine(url, pool_pre_ping=True)

@st.cache_data(ttl=3600)
def carregar_filiais() -> dict:
    try:
        q = "SELECT CodFilial, NomeFilial FROM Filiais WHERE Ativo = 1 ORDER BY NomeFilial"
        df = pd.read_sql(q, get_engine())
        return dict(zip(df['CodFilial'].astype(str), df['NomeFilial']))
    except Exception:
        return {"1": "PB - ALECRIM", "2": "PB - VIA DIRETA", "3": "PB - ZONA SUL", "4": "SRB - ZONA NORTE", "5": "PB - ATACADO"}

@st.cache_data(ttl=3600)
def carregar_fornecedores() -> list:
    try:
        q = "SELECT DISTINCT NomeCliFor FROM Cli_For WHERE NomeCliFor IS NOT NULL AND NomeCliFor <> '' ORDER BY NomeCliFor"
        df = pd.read_sql(q, get_engine())
        return df["NomeCliFor"].tolist()
    except Exception:
        return []