from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import text
from .db import get_engine

_SQL_PATH = Path(__file__).parent.parent / "sql" / "base.sql"
_SQL_BASE = _SQL_PATH.read_text(encoding="utf-8")

_SQL_TRANSITO_PATH = Path(__file__).parent.parent / "sql" / "transf_em_transito.sql"
_SQL_TRANSITO = _SQL_TRANSITO_PATH.read_text(encoding="utf-8") if _SQL_TRANSITO_PATH.exists() else ""

_SQL_RECEBIDAS_PATH = Path(__file__).parent.parent / "sql" / "transf_recebidas_recentes.sql"
_SQL_RECEBIDAS = _SQL_RECEBIDAS_PATH.read_text(encoding="utf-8") if _SQL_RECEBIDAS_PATH.exists() else ""

_SQL_VENDAS = Path(__file__).parent.parent / "sql" / "visao_vendas.sql"
_SQL_PAGAMENTOS = Path(__file__).parent.parent / "sql" / "visao_pagamentos.sql"
_SQL_DEPARTAMENTOS = Path(__file__).parent.parent / "sql" / "visao_departamentos.sql"
_SQL_COMPRAS = Path(__file__).parent.parent / "sql" / "visao_compras.sql"
_SQL_TRIBUTOS = Path(__file__).parent.parent / "sql" / "visao_tributos.sql"

def _build_produto_filter(produto: str) -> tuple[str, dict]:
    """Mantido apenas para compatibilidade se usado no futuro."""
    return "", {}

def _executar_query(arquivo_sql, params, filial=None):
    sql = arquivo_sql.read_text(encoding="utf-8")
    if filial:
        sql = sql.replace("/* FILTRO_FILIAL */", "AND m.CodFilial = :filial")
        params["filial"] = int(filial)
    else:
        sql = sql.replace("/* FILTRO_FILIAL */", "")
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)

def buscar_vendas(data_inicio, data_fim, hora_inicio, hora_fim, filial):
    params = {"data_inicio": data_inicio, "data_fim": data_fim, "hora_inicio": hora_inicio, "hora_fim": hora_fim}
    return _executar_query(_SQL_VENDAS, params, filial)

def buscar_departamentos(data_inicio, data_fim, hora_inicio, hora_fim, filial):
    params = {"data_inicio": data_inicio, "data_fim": data_fim, "hora_inicio": hora_inicio, "hora_fim": hora_fim}
    return _executar_query(_SQL_DEPARTAMENTOS, params, filial)

def buscar_pagamentos(data_inicio, data_fim, hora_inicio, hora_fim, filial):
    params = {"data_inicio": data_inicio, "data_fim": data_fim, "hora_inicio": hora_inicio, "hora_fim": hora_fim}
    return _executar_query(_SQL_PAGAMENTOS, params, filial)

def buscar_compras(data_inicio, data_fim, filial):
    params = {"data_inicio": data_inicio, "data_fim": data_fim}
    return _executar_query(_SQL_COMPRAS, params, filial)

@st.cache_data(ttl=600)
def buscar_tributos(data_inicio, data_fim):
    params = {"data_inicio": data_inicio, "data_fim": data_fim}
    return _executar_query(_SQL_TRIBUTOS, params, None)