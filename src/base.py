from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import text
from .db import get_engine

# Caminhos base para os arquivos SQL
_SQL_DIR = Path(__file__).parent.parent / "sql"

def _ler_sql(nome_arquivo: str) -> str:
    caminho = _SQL_DIR / nome_arquivo
    if not caminho.exists():
        return ""
    return caminho.read_text(encoding="utf-8")

def _executar_query(arquivo_sql, params, filial=None):
    sql = _ler_sql(arquivo_sql)
    if not sql:
        return pd.DataFrame()
        
    if filial:
        sql = sql.replace("/* FILTRO_FILIAL */", "AND m.CodFilial = :filial")
        params["filial"] = int(filial)
    else:
        sql = sql.replace("/* FILTRO_FILIAL */", "")
        
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)

def buscar_vendas(data_inicio, data_fim, hora_inicio, hora_fim, filial):
    params = {"data_inicio": data_inicio, "data_fim": data_fim, "hora_inicio": hora_inicio, "hora_fim": hora_fim}
    return _executar_query("visao_vendas.sql", params, filial)

def buscar_departamentos(data_inicio, data_fim, hora_inicio, hora_fim, filial):
    params = {"data_inicio": data_inicio, "data_fim": data_fim, "hora_inicio": hora_inicio, "hora_fim": hora_fim}
    return _executar_query("visao_departamentos.sql", params, filial)

def buscar_pagamentos(data_inicio, data_fim, hora_inicio, hora_fim, filial):
    params = {"data_inicio": data_inicio, "data_fim": data_fim, "hora_inicio": hora_inicio, "hora_fim": hora_fim}
    return _executar_query("visao_pagamentos.sql", params, filial)

def buscar_compras(data_inicio, data_fim, filial):
    params = {"data_inicio": data_inicio, "data_fim": data_fim}
    return _executar_query("visao_compras.sql", params, filial)
    
@st.cache_data(ttl=600)
def buscar_sazonalidade(data_inicio, data_fim, filial=""):
    params = {"data_inicio": data_inicio, "data_fim": data_fim}
    return _executar_query("visao_sazonalidade.sql", params, filial)

def buscar_transferencias(data_inicio, data_fim, filial):
    params = {"data_inicio": data_inicio, "data_fim": data_fim}
    return _executar_query("visao_transferencias.sql", params, filial)

@st.cache_data(ttl=600)
def buscar_tributos(data_inicio, data_fim):
    params = {"data_inicio": data_inicio, "data_fim": data_fim}
    return _executar_query("visao_tributos.sql", params, None)