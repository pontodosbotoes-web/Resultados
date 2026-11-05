import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from src.db import carregar_filiais, carregar_fornecedores
from src.base import buscar_vendas, buscar_departamentos, buscar_pagamentos, buscar_compras, buscar_tributos

st.set_page_config(page_title="Acompanhamento Gerencial", layout="wide", page_icon="📊")

# CSS Customizado
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 100% !important; background-color: #0d1117; }
        
        .titulo-pagina { font-size: 24px; font-weight: 700; text-align: center; color: #f0f6fc; padding-bottom: 10px; margin-bottom: 10px; }
        
        .tema-titulo { font-size: 20px; font-weight: 700; color: #f0f6fc; margin-top: 20px; margin-bottom: 12px; padding-bottom: 6px; }
        
        .card-item { border-radius: 10px; padding: 12px 14px 6px 14px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; transition: 0.2s; margin-bottom: 10px;}
        .card-item:hover { filter: brightness(1.2); }
        
        .card-label { font-size: 13px; font-weight: 600; color: #c9d1d9; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
        .card-value { font-size: 20px; font-weight: 700; color: #f0f6fc; }
        
        .pct-participacao { font-size: 13px; font-weight: 600; color: #f6ad55; margin-left: 5px; }
        .pct-positiva { font-size: 13px; font-weight: 600; color: #3fb950; margin-left: 5px; }
        .pct-negativa { font-size: 13px; font-weight: 600; color: #f85149; margin-left: 5px; }
        
        .depto-header { font-size: 18px; font-weight: 600; color: #f0f6fc; margin-top: 10px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;}
        .depto-valor { font-size: 16px; color: #58a6ff; font-weight: 700; background: rgba(88,166,255,0.1); padding: 2px 10px; border-radius: 15px;}
        
        div[data-testid="stFormSubmitButton"] > button { width: 100% !important; }

        /* ESTILO DO BOTÃO ATUALIZAR (VERDE) */
        div[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"], div[data-testid="stButton"] button[kind="primary"] {
            background-color: #238636 !important;
            color: #ffffff !important;
            border: 1px solid #238636 !important;
            transition: all 0.2s;
        }
        div[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:hover, div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: #2ea043 !important;
            border-color: #2ea043 !important;
            box-shadow: 0 0 10px rgba(46, 160, 67, 0.4) !important;
        }

        /* ESTILO DO BOTÃO LIMPAR (VERMELHO) */
        div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"], div[data-testid="stButton"] button {
            background-color: #da3633 !important;
            color: #ffffff !important;
            border: 1px solid #da3633 !important;
            transition: all 0.2s;
        }
        div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"]:hover, div[data-testid="stButton"] button:hover {
            background-color: #f85149 !important;
            border-color: #f85149 !important;
            box-shadow: 0 0 10px rgba(248, 81, 73, 0.4) !important;
        }
        
        /* ESTILO DO BOTÃO DE DOWNLOAD (GERAR PDF) */
        div[data-testid="stDownloadButton"] button {
            background-color: #1f6feb !important;
            color: #ffffff !important;
            border: 1px solid #1f6feb !important;
            transition: all 0.2s;
        }
        div[data-testid="stDownloadButton"] button:hover {
            background-color: #388bfd !important;
            border-color: #388bfd !important;
            box-shadow: 0 0 10px rgba(56, 139, 253, 0.4) !important;
        }

        /* ===== TRIBUTOS ===== */
        .tabela-wrapper { overflow-x: auto; margin: 10px 0 30px 0; }
        .tributos-tabela { width: 100%; border-collapse: collapse; font-size: 14px; background: #161b22; border-radius: 8px; border: 1px solid #30363d; }
        .tributos-tabela th { background: #0d1117; color: #f0f6fc; padding: 10px 12px; border-bottom: 2px solid #30363d; font-weight: 600; white-space: nowrap; }
        .tributos-tabela td { padding: 8px 12px; border-bottom: 1px solid #21262d; color: #c9d1d9; }
        .tributos-tabela td:first-child { text-align: left !important; font-weight: 500; }
        .tributos-tabela td:not(:first-child) { text-align: right !important; font-variant-numeric: tabular-nums; }
        .tributos-tabela tr:hover td { background: #1c2128; }
        
        .tributos-tabela .total-entrada td { color: #3fb950; font-weight: 700; background: rgba(63, 185, 80, 0.08); border-top: 1px solid #3fb950; }
        .tributos-tabela .subtotal-entrada td { color: #56d364; font-weight: 600; background: rgba(63, 185, 80, 0.04); }
        .tributos-tabela .total-saida td { color: #ff7b72; font-weight: 700; background: rgba(248, 81, 73, 0.08); border-top: 1px solid #f85149; }
        .tributos-tabela .subtotal-saida td { color: #ffa198; font-weight: 600; background: rgba(248, 81, 73, 0.04); }
        .tributos-tabela .debito td { color: #f85149; font-weight: 700; background: rgba(248, 81, 73, 0.1); border-top: 1px solid #f85149; }
        .tributos-tabela .credito td { color: #3fb950; font-weight: 700; background: rgba(63, 185, 80, 0.1); border-top: 1px solid #3fb950; }
        .tributos-tabela .resultado td { font-weight: 700; font-size: 15px; border-top: 3px double #58a6ff; border-bottom: 3px double #58a6ff; padding-top: 12px; padding-bottom: 12px; }
        .tributos-tabela .resultado td:first-child { color: #58a6ff; }
        .tributos-tabela .devolucao td { color: #ffa198; font-style: italic; }
        .tributos-tabela .nao-tributada td { color: #8b949e; font-style: italic; background: rgba(139, 148, 158, 0.04); }
        .tributos-tabela .bloco-fim td { border-bottom: 3px solid #58a6ff !important; }
    </style>
""", unsafe_allow_html=True)

try:
    tz_br = ZoneInfo("America/Sao_Paulo")
except:
    tz_br = None
hoje = datetime.now(tz_br).date() if tz_br else date.today()

filiais_dict = carregar_filiais()
filiais_inv = {v: k for k, v in filiais_dict.items()}
NOMES_FILIAIS = {1: "PB - ALECRIM", 2: "PB - VIA DIRETA", 3: "PB - ZONA SUL", 4: "SRB - ZONA NORTE", 5: "PB - ATACADO"}

st.markdown('<div class="titulo-pagina">📊 Acompanhamento Gerencial</div>', unsafe_allow_html=True)

tab_visao, tab_compras, tab_tributos = st.tabs(["💰 Vendas", "🛒 Compras", "⚖️ Tributos"])

def formatar_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_numero(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_decimal(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_inteiro(v):
    return f"{int(v):,}".replace(",", ".")

def criar_mini_grafico(df_hora, col_valor, cor_hex, is_moeda=True):
    if df_hora.empty: return go.Figure()
    
    if is_moeda:
        custom_data = [f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") for v in df_hora[col_valor]]
        hover_tpl = "%{x}h<br>R$ %{customdata}<extra></extra>"
    else:
        custom_data = [f"{int(v):,}".replace(",", ".") for v in df_hora[col_valor]]
        hover_tpl = "%{x}h<br>%{customdata}<extra></extra>"

    max_val = df_hora[col_valor].max()
    
    r = int(cor_hex[1:3], 16); g = int(cor_hex[3:5], 16); b = int(cor_hex[5:7], 16)
    cor_transparente = f"rgba({r}, {g}, {b}, 0.4)"
    
    cores_barras = []
    for v in df_hora[col_valor]:
        if v == max_val and max_val > 0:
            cores_barras.append("#FFFFFF")
        else:
            cores_barras.append(cor_transparente)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_hora["Hora"], 
        y=df_hora[col_valor],
        marker_color=cores_barras,
        customdata=custom_data,
        hovertemplate=hover_tpl
    ))
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0), height=45,
        xaxis=dict(visible=False, showspikes=False), 
        yaxis=dict(visible=False, rangemode='tozero', showspikes=False),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False,
        hovermode="x unified",
        bargap=0.1
    )
    return fig

def renderizar_tema(titulo, icone, dados, col_valor, cor_hex, tipo_pct, fmt="moeda", campo_itens="porFilial", is_filial=True):
    st.markdown(f'<div class="tema-titulo">{icone} {titulo}</div>', unsafe_allow_html=True)
    total = dados.get("total", 0)
    itens = dados.get(campo_itens, [])
    
    def html_card(nome, valor, pct_html="", is_consolidado=False):
        r = int(cor_hex[1:3], 16); g = int(cor_hex[3:5], 16); b = int(cor_hex[5:7], 16)
        bg_color = f"rgba({r}, {g}, {b}, 0.08)"
        
        border_color = cor_hex if is_consolidado else "#30363d"
        border_left = f"4px solid {cor_hex}" if is_consolidado else "1px solid #30363d"
        style_str = f"background-color: {bg_color}; border: 1px solid {border_color}; border-left: {border_left};"
        
        label_nome = "🏆 Consolidado" if is_consolidado else nome
        label_style = f"color: {cor_hex};" if is_consolidado else ""
        value_style = f"color: {cor_hex};" if is_consolidado else ""
        
        val_fmt = formatar_moeda(valor) if fmt == "moeda" else (formatar_inteiro(valor) if fmt == "inteiro" else formatar_decimal(valor))
        return f'<div class="card-item" style="{style_str}"><div class="card-label" style="{label_style}">{label_nome}</div><div class="card-value" style="{value_style}">{val_fmt} {pct_html}</div></div>'

    def render_card_col(col, item):
        pct_html = ""
        if total > 0:
            if tipo_pct == "participacao":
                pct = (item["valor"] / total) * 100
                pct_html = f'<span class="pct-participacao">({pct:.1f}%)</span>'
            elif tipo_pct == "variacao":
                diff = ((item["valor"] - total) / total) * 100
                sinal = "+" if diff > 0 else ""
                classe = "pct-positiva" if diff >= 0 else "pct-negativa"
                pct_html = f'<span class="{classe}">({sinal}{diff:.1f}%)</span>'
        
        with col:
            st.markdown(html_card(item["nome"], item["valor"], pct_html), unsafe_allow_html=True)
            if "horas" in item and dados.get("labelsHoras"):
                key_item = f"item_{titulo.replace(' ', '_').replace('/', '')}_{item['nome'].replace(' ', '_').replace('.', '')}_{col_valor}"
                fig = criar_mini_grafico(pd.DataFrame({"Hora": dados["labelsHoras"], "Val": item["horas"]}), "Val", cor_hex, fmt=="moeda")
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=key_item)

    if is_filial:
        cols = st.columns([1.1, 1, 1, 1, 1])
        with cols[0]:
            st.markdown(html_card("", total, is_consolidado=True), unsafe_allow_html=True)
            df_cons = dados.get("horasConsolidado", [])
            labels = dados.get("labelsHoras", [])
            if df_cons and labels:
                key_cons = f"cons_{titulo.replace(' ', '_').replace('/', '')}_{col_valor}"
                fig_cons = criar_mini_grafico(pd.DataFrame({"Hora": labels, "Val": df_cons}), "Val", cor_hex, fmt=="moeda")
                st.plotly_chart(fig_cons, use_container_width=True, config={'displayModeBar': False}, key=key_cons)
        
        for i, item in enumerate(itens):
            if i + 1 >= len(cols): break
            render_card_col(cols[i + 1], item)
            
    else:
        cols = st.columns([1.1, 1, 1, 1, 1])
        with cols[0]:
            st.markdown(html_card("", total, is_consolidado=True), unsafe_allow_html=True)
            df_cons = dados.get("horasConsolidado", [])
            labels = dados.get("labelsHoras", [])
            if df_cons and labels:
                key_cons = f"cons_{titulo.replace(' ', '_').replace('/', '')}_{col_valor}"
                fig_cons = criar_mini_grafico(pd.DataFrame({"Hora": labels, "Val": df_cons}), "Val", cor_hex, fmt=="moeda")
                st.plotly_chart(fig_cons, use_container_width=True, config={'displayModeBar': False}, key=key_cons)

        for i in range(4):
            if i < len(itens):
                render_card_col(cols[i+1], itens[i])
        
        itens_restantes = itens[4:]
        for i in range(0, len(itens_restantes), 5):
            chunk = itens_restantes[i:i+5]
            cols_chunk = st.columns(5)
            for j, item in enumerate(chunk):
                render_card_col(cols_chunk[j], item)
        st.write("") 


# ==========================================
# ABA VENDAS
# ==========================================
with tab_visao:
    if "dt_ini_visao" not in st.session_state: st.session_state["dt_ini_visao"] = hoje
    if "dt_fim_visao" not in st.session_state: st.session_state["dt_fim_visao"] = hoje
    if "h_ini_visao" not in st.session_state: st.session_state["h_ini_visao"] = datetime.strptime("00:00", "%H:%M").time()
    if "h_fim_visao" not in st.session_state: st.session_state["h_fim_visao"] = datetime.strptime("23:59", "%H:%M").time()
    if "filial_visao" not in st.session_state: st.session_state["filial_visao"] = "Todas"

    with st.form(key="form_filtros"):
        c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1.2, 1.4], vertical_alignment="bottom")
        
        data_ini = c1.date_input("De:", key="dt_ini_visao", format="DD/MM/YYYY")
        data_fim = c2.date_input("Até:", key="dt_fim_visao", format="DD/MM/YYYY")
        h_ini = c3.time_input("Hora:", key="h_ini_visao")
        h_fim = c4.time_input("Até:", key="h_fim_visao")
        filial_sel = c5.selectbox("Filial:", ["Todas"] + list(filiais_inv.keys()), key="filial_visao")
        
        with c6:
            col_btn1, col_btn2 = st.columns(2)
            btn = col_btn1.form_submit_button("🔄 Atualizar", use_container_width=True, type="primary")
            btn_limpar = col_btn2.form_submit_button("🧹 Limpar", use_container_width=True)

    if btn_limpar:
        for k in ["dt_ini_visao", "dt_fim_visao", "h_ini_visao", "h_fim_visao", "filial_visao"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

    filial_cod = "" if filial_sel == "Todas" else filiais_inv[filial_sel]
    
    with st.spinner("Carregando dados..."):
        df_vendas = buscar_vendas(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), h_ini.hour, h_fim.hour, filial_cod)
        if not df_vendas.empty:
            df_vendas["CodFilial"] = pd.to_numeric(df_vendas["CodFilial"], errors="coerce").fillna(0).astype(int)
            
        df_depto = buscar_departamentos(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), h_ini.hour, h_fim.hour, filial_cod)
        df_pag = buscar_pagamentos(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), h_ini.hour, h_fim.hour, filial_cod)

    if df_vendas.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
    else:
        labels_h = sorted(df_vendas["Hora"].unique().tolist())
        tot_vendas = df_vendas["ValorVenda"].sum()
        tot_trans = df_vendas["QtdVendas"].sum()
        tot_itens = df_vendas["QtdItens"].sum()

        temas = [
            {"id": "vendas", "titulo": "Vendas", "icone": "💰", "total": tot_vendas, "col": "ValorVenda", "cor": "#58a6ff", "fmt": "moeda", "pct": "participacao"},
            {"id": "transacoes", "titulo": "Transações", "icone": "🛒", "total": tot_trans, "col": "QtdVendas", "cor": "#3fb950", "fmt": "inteiro", "pct": "participacao"},
            {"id": "ticket", "titulo": "Ticket Médio", "icone": "🎫", "total": (tot_vendas / tot_trans if tot_trans else 0), "col": "Ticket", "cor": "#d29922", "fmt": "moeda", "pct": "variacao"},
            {"id": "itens", "titulo": "Itens", "icone": "📦", "total": tot_itens, "col": "QtdItens", "cor": "#9f7aea", "fmt": "decimal", "pct": "participacao"},
            {"id": "itens_venda", "titulo": "Itens por Venda (R$/item)", "icone": "💰", "total": (tot_vendas / tot_itens if tot_itens else 0), "col": "ItensVenda", "cor": "#4fd1c5", "fmt": "moeda", "pct": "variacao"},
            {"id": "itens_trans", "titulo": "Itens por Transação", "icone": "📊", "total": (tot_itens / tot_trans if tot_trans else 0), "col": "ItensTrans", "cor": "#f687b3", "fmt": "decimal", "pct": "variacao"},
        ]

        for t in temas:
            itens_filial = []
            for cod, nome in NOMES_FILIAIS.items():
                df_f = df_vendas[df_vendas["CodFilial"] == cod]
                v_vendas = df_f["ValorVenda"].sum()
                v_trans = df_f["QtdVendas"].sum()
                v_itens = df_f["QtdItens"].sum()
                
                if t["col"] == "ValorVenda": val = v_vendas
                elif t["col"] == "QtdVendas": val = v_trans
                elif t["col"] == "QtdItens": val = v_itens
                elif t["col"] == "Ticket": val = (v_vendas / v_trans if v_trans else 0)
                elif t["col"] == "ItensVenda": val = (v_vendas / v_itens if v_itens else 0)
                elif t["col"] == "ItensTrans": val = (v_itens / v_trans if v_trans else 0)
                
                h_list = []
                for h in labels_h:
                    df_fh = df_f[df_f["Hora"] == h]
                    h_vendas = df_fh["ValorVenda"].sum()
                    h_trans = df_fh["QtdVendas"].sum()
                    h_itens = df_fh["QtdItens"].sum()
                    
                    if t["col"] == "ValorVenda": hv = h_vendas
                    elif t["col"] == "QtdVendas": hv = h_trans
                    elif t["col"] == "QtdItens": hv = h_itens
                    elif t["col"] == "Ticket": hv = (h_vendas / h_trans if h_trans else 0)
                    elif t["col"] == "ItensVenda": hv = (h_vendas / h_itens if h_itens else 0)
                    elif t["col"] == "ItensTrans": hv = (h_itens / h_trans if h_trans else 0)
                    h_list.append(hv)
                    
                itens_filial.append({"nome": nome, "valor": val, "horas": h_list})

            cons_horas = []
            for h in labels_h:
                df_h = df_vendas[df_vendas["Hora"] == h]
                h_v = df_h["ValorVenda"].sum()
                h_t = df_h["QtdVendas"].sum()
                h_i = df_h["QtdItens"].sum()
                if t["col"] == "ValorVenda": hv = h_v
                elif t["col"] == "QtdVendas": hv = h_t
                elif t["col"] == "QtdItens": hv = h_i
                elif t["col"] == "Ticket": hv = (h_v / h_t if h_t else 0)
                elif t["col"] == "ItensVenda": hv = (h_v / h_i if h_i else 0)
                elif t["col"] == "ItensTrans": hv = (h_i / h_t if h_t else 0)
                cons_horas.append(hv)

            dados_tema = {"total": t["total"], "porFilial": itens_filial, "labelsHoras": labels_h, "horasConsolidado": cons_horas}
            renderizar_tema(t["titulo"], t["icone"], dados_tema, t["col"], t["cor"], t["pct"], t["fmt"], "porFilial", is_filial=True)

        if not df_depto.empty:
            labels_depto = sorted(df_depto["Hora"].unique().tolist())
            tot_depto = df_depto["ValorVenda"].sum()
            itens_depto = []
            for depto_nome in df_depto["NomeDepto"].unique():
                df_d = df_depto[df_depto["NomeDepto"] == depto_nome]
                val = df_d["ValorVenda"].sum()
                horas = [df_d[df_d["Hora"] == h]["ValorVenda"].sum() for h in labels_depto]
                itens_depto.append({"nome": depto_nome, "valor": val, "horas": horas})
            itens_depto = sorted(itens_depto, key=lambda x: x["valor"], reverse=True)
            cons_horas_d = [df_depto[df_depto["Hora"] == h]["ValorVenda"].sum() for h in labels_depto]
            dados_d = {"total": tot_depto, "departamentos": itens_depto, "labelsHoras": labels_depto, "horasConsolidado": cons_horas_d}
            renderizar_tema("Vendas por Departamento", "📂", dados_d, "ValorVenda", "#38bdf8", "participacao", "moeda", "departamentos", is_filial=False)

        if not df_pag.empty:
            labels_pag = sorted(df_pag["Hora"].unique().tolist())
            tot_pag = df_pag["Valor"].sum()
            itens_pag = []
            for form in df_pag["Denominacao"].unique():
                df_p = df_pag[df_pag["Denominacao"] == form]
                val = df_p["Valor"].sum()
                horas = [df_p[df_p["Hora"] == h]["Valor"].sum() for h in labels_pag]
                itens_pag.append({"nome": form, "valor": val, "horas": horas})
            itens_pag = sorted(itens_pag, key=lambda x: x["valor"], reverse=True)
            cons_horas_p = [df_pag[df_pag["Hora"] == h]["Valor"].sum() for h in labels_pag]
            dados_p = {"total": tot_pag, "porForma": itens_pag, "labelsHoras": labels_pag, "horasConsolidado": cons_horas_p}
            renderizar_tema("Forma de Pagamento", "💳", dados_p, "Valor", "#f0883e", "participacao", "moeda", "porForma", is_filial=False)

            df_pag_port = df_pag.dropna(subset=["NomePortador"])
            if not df_pag_port.empty:
                itens_port = []
                for port in df_pag_port["NomePortador"].unique():
                    df_pt = df_pag_port[df_pag_port["NomePortador"] == port]
                    val = df_pt["Valor"].sum()
                    horas = [df_pt[df_pt["Hora"] == h]["Valor"].sum() for h in labels_pag]
                    itens_port.append({"nome": port, "valor": val, "horas": horas})
                itens_port = sorted(itens_port, key=lambda x: x["valor"], reverse=True)
                cons_horas_pt = [df_pag_port[df_pag_port["Hora"] == h]["Valor"].sum() for h in labels_pag]
                dados_pt = {"total": tot_pag, "porPortador": itens_port, "labelsHoras": labels_pag, "horasConsolidado": cons_horas_pt}
                renderizar_tema("Portador", "👤", dados_pt, "Valor", "#f97583", "participacao", "moeda", "porPortador", is_filial=False)

# ==========================================
# ABA COMPRAS
# ==========================================
with tab_compras:
    try:
        lista_fornecedores = carregar_fornecedores()
    except Exception:
        lista_fornecedores = []
    
    if "dt_ini_compras" not in st.session_state: st.session_state["dt_ini_compras"] = date(hoje.year, 1, 1)
    if "dt_fim_compras" not in st.session_state: st.session_state["dt_fim_compras"] = date(hoje.year, 12, 31)
    if "filial_compras" not in st.session_state: st.session_state["filial_compras"] = "Todas"
    if "fornecedor_compras" not in st.session_state: st.session_state["fornecedor_compras"] = "Todos"

    if st.session_state["fornecedor_compras"] != "Todos" and st.session_state["fornecedor_compras"] not in lista_fornecedores:
        st.session_state["fornecedor_compras"] = "Todos"

    with st.form(key="form_compras"):
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1.2, 1.5, 1.4], vertical_alignment="bottom")
        
        data_ini_c = c1.date_input("De:", key="dt_ini_compras", format="DD/MM/YYYY")
        data_fim_c = c2.date_input("Até:", key="dt_fim_compras", format="DD/MM/YYYY")
        filial_c_sel = c3.selectbox("Filial:", ["Todas"] + list(filiais_inv.keys()), key="filial_compras")
        fornecedor_sel = c4.selectbox("Fornecedor:", ["Todos"] + lista_fornecedores, key="fornecedor_compras")
        
        with c5:
            col_btn1, col_btn2 = st.columns(2)
            btn_compras = col_btn1.form_submit_button("🔄 Atualizar", use_container_width=True, type="primary")
            btn_limpar_comp = col_btn2.form_submit_button("🧹 Limpar", use_container_width=True)

    if btn_limpar_comp:
        for k in ["dt_ini_compras", "dt_fim_compras", "filial_compras", "fornecedor_compras"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

    filial_cod_c = "" if filial_c_sel == "Todas" else filiais_inv[filial_c_sel]
    
    with st.spinner("Carregando dados de compras..."):
        df_compras = buscar_compras(data_ini_c.strftime("%Y-%m-%d"), data_fim_c.strftime("%Y-%m-%d"), filial_cod_c)
    
    if df_compras.empty:
        st.info("Nenhuma compra encontrada para o período.")
    else:
        if fornecedor_sel != "Todos":
            df_compras = df_compras[df_compras["Fornecedor"] == fornecedor_sel]
            
        if df_compras.empty:
            st.info(f"Nenhuma compra encontrada para o fornecedor {fornecedor_sel} neste período.")
        else:
            tot_val_geral = df_compras["Valor"].sum()
            
            df_tot_depto = df_compras.groupby("Departamento")["Valor"].sum().reset_index()
            df_tot_depto = df_tot_depto.sort_values("Departamento", ascending=True)
            
            meses_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
            df_compras['Mes_Nome'] = df_compras['Mes'].map(meses_map)
            meses_colunas = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

            cards_data = [("💰 Total Comprado", tot_val_geral, "#58a6ff", "")]
            cores_depto = ["#3fb950", "#d29922", "#9f7aea", "#f687b3", "#38bdf8", "#f0883e", "#f97583", "#4fd1c5"]
            
            for i, row in df_tot_depto.iterrows():
                cor = cores_depto[i % len(cores_depto)]
                pct = (row["Valor"] / tot_val_geral) * 100 if tot_val_geral > 0 else 0
                pct_html = f'<span class="pct-participacao">({pct:.1f}%)</span>'
                cards_data.append((f"📂 {row['Departamento']}", row["Valor"], cor, pct_html))

            for i in range(0, len(cards_data), 5):
                chunk = cards_data[i:i+5]
                cols = st.columns(5)
                for j, (nome, valor, cor, pct_html) in enumerate(chunk):
                    with cols[j]:
                        r = int(cor[1:3], 16); g = int(cor[3:5], 16); b = int(cor[5:7], 16)
                        bg_color = f"rgba({r}, {g}, {b}, 0.08)"
                        st.markdown(f'''
                            <div class="card-item" style="background-color: {bg_color}; border: 1px solid {cor}; border-left: 4px solid {cor};">
                                <div class="card-label" style="color: {cor};" title="{nome}">{nome}</div>
                                <div class="card-value" style="color: {cor};">{formatar_moeda(valor)} {pct_html}</div>
                            </div>
                        ''', unsafe_allow_html=True)
            
            st.write("")

            if not df_tot_depto.empty:
                deptos_nomes = df_tot_depto['Departamento'].tolist()
                sub_tabs = st.tabs(deptos_nomes)

                for sub_tab, (_, row) in zip(sub_tabs, df_tot_depto.iterrows()):
                    with sub_tab:
                        depto = row['Departamento']
                        
                        df_d = df_compras[df_compras["Departamento"] == depto]
                        
                        df_pivot = df_d.pivot_table(
                            index=['Fornecedor'], 
                            columns='Mes_Nome', 
                            values='Valor', 
                            aggfunc='sum'
                        )
                        
                        for m in meses_colunas:
                            if m not in df_pivot.columns: df_pivot[m] = 0.0
                                
                        df_pivot = df_pivot[meses_colunas]
                        df_pivot['Total'] = df_pivot.sum(axis=1)
                        df_pivot = df_pivot.fillna(0)
                        df_pivot = df_pivot.sort_index(ascending=True)
                        
                        linha_total = df_pivot.sum().to_frame().T
                        linha_total.index = ['TOTAL']
                        df_final = pd.concat([df_pivot, linha_total])
                        
                        def fmt_br(x):
                            if pd.isna(x) or x == 0:
                                return "-"
                            return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        
                        def highlight_total(row):
                            if row.name == 'TOTAL':
                                return ['font-weight: bold; color: #58a6ff;'] * len(row)
                            return [''] * len(row)
                        
                        st.dataframe(
                            df_final.style.format(fmt_br).apply(highlight_total, axis=1),
                            use_container_width=True
                        )

# ==========================================
# FUNÇÃO GERADORA DE PDF DE TRIBUTOS
# ==========================================
def gerar_pdf_tributos(colunas, rows_saidas, rows_entradas, rows_resultado, atacado, pb, srb, data_ini, data_fim):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    
    # CABEÇALHO COM TÍTULO À ESQUERDA E PERÍODO À DIREITA
    left_style = ParagraphStyle('Left', parent=styles['Heading2'], alignment=0, fontSize=12, spaceAfter=0)
    right_style = ParagraphStyle('Right', parent=styles['Normal'], alignment=2, fontSize=10, spaceAfter=0)
    
    header_data = [
        [Paragraph("<b>Acompanhamento Gerencial - Tributos</b>", left_style),
         Paragraph(f"Período: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", right_style)]
    ]
    header_table = Table(header_data, colWidths=[400, 400])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    
    # TABELA DE DADOS
    header_style = ParagraphStyle('Header', parent=styles['Normal'], textColor=colors.white, fontName='Helvetica-Bold', fontSize=8, alignment=1)
    cell_left = ParagraphStyle('CellLeft', parent=styles['Normal'], fontSize=8, alignment=0)
    cell_right = ParagraphStyle('CellRight', parent=styles['Normal'], fontSize=8, alignment=2)
    cell_bold_right = ParagraphStyle('CellBoldRight', parent=styles['Normal'], fontSize=8, alignment=2, fontName='Helvetica-Bold')
    cell_bold_left = ParagraphStyle('CellBoldLeft', parent=styles['Normal'], fontSize=8, alignment=0, fontName='Helvetica-Bold')
    
    headers = ['Operação'] + [f['NomeFilial'] for _, f in colunas.iterrows()] + ['Total']
    table_data = [[Paragraph(h, header_style) for h in headers]]
    
    def add_row_to_data(label, key, opts):
        bold = opts.get('bold', False)
        left_style = cell_bold_left if bold else cell_left
        right_style = cell_bold_right if bold else cell_right
        
        row = [Paragraph(label, left_style)]
        total = 0
        for _, f in colunas.iterrows():
            val = f[key] if key else 0
            total += val
            if 'fmt' in opts:
                try:
                    val_str = opts['fmt'](val, f)
                except:
                    val_str = formatar_moeda(val)
            else:
                val_str = formatar_moeda(val)
            
            if key == 'resultado':
                if val < 0:
                    val_str = f"-{formatar_moeda(abs(val))}"
                else:
                    val_str = formatar_moeda(val)
            
            row.append(Paragraph(val_str, right_style))
        
        if key == 'resultado':
            total_str = formatar_moeda(total) if total >= 0 else f"-{formatar_moeda(abs(total))}"
        else:
            total_str = formatar_moeda(total)
        
        row.append(Paragraph(total_str, right_style))
        return row
    
    all_rows = rows_saidas + rows_entradas + rows_resultado
    for label, key, opts in all_rows:
        table_data.append(add_row_to_data(label, key, opts))
    
    # LARGURAS AJUSTADAS PARA NÃO QUEBRAR AS COLUNAS
    col_widths = [150] + [100] * len(colunas) + [100]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    
    elements.append(Spacer(1, 15))
    
    saldo_atacado = atacado["resultado"].sum() if not atacado.empty else 0
    saldo_pb = pb["resultado"].sum() if not pb.empty else 0
    saldo_srb = srb["resultado"].sum() if not srb.empty else 0
    saldo_cons = saldo_atacado + saldo_pb + saldo_srb
    
    result_style = ParagraphStyle('Result', parent=styles['Normal'], alignment=1, fontSize=11, spaceAfter=10)
    results_text = f"Resultado PB - ATACADO: {formatar_moeda(saldo_atacado)} &nbsp;&nbsp;&nbsp; Resultado PB - FILIAIS: {formatar_moeda(saldo_pb)} &nbsp;&nbsp;&nbsp; Resultado SRB: {formatar_moeda(saldo_srb)} &nbsp;&nbsp;&nbsp; Consolidado: {formatar_moeda(saldo_cons)}"
    elements.append(Paragraph(results_text, result_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================
# ABA TRIBUTOS
# ==========================================
with tab_tributos:
    if "dt_ini_trib" not in st.session_state: st.session_state["dt_ini_trib"] = hoje.replace(day=1)
    if "dt_fim_trib" not in st.session_state: st.session_state["dt_fim_trib"] = hoje

    # Filtros e Botões
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1.5], vertical_alignment="bottom")
    data_ini_t = c1.date_input("De:", key="dt_ini_trib", format="DD/MM/YYYY")
    data_fim_t = c2.date_input("Até:", key="dt_fim_trib", format="DD/MM/YYYY")

    # Botões de Ação no topo
    with c3:
        btn_atualizar = st.button("🔄 Atualizar", use_container_width=True, type="primary")
    with c4:
        btn_limpar = st.button("🧹 Limpar", use_container_width=True)

    if btn_limpar:
        for k in ["dt_ini_trib", "dt_fim_trib"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

    # Carregar Dados
    with st.spinner("Carregando dados tributários..."):
        df_trib = buscar_tributos(data_ini_t.strftime("%Y-%m-%d"), data_fim_t.strftime("%Y-%m-%d"))
        
    pdf_bytes = None
    if df_trib.empty:
        st.info("Nenhum dado encontrado para o período.")
    else:
        df_trib["CodFilial"] = pd.to_numeric(df_trib["CodFilial"], errors="coerce").fillna(0).astype(int)
        
        cols_numeric = ["VendasBruto", "VendasLiquidoDesconto", "ICMS_Vendas", "DevolucaoVendas", "TransfEnvTotal", "TransfEnvTrib", "TransfEnvNaoTrib", "ICMS_TransfEnv", "ComprasTotal", "ComprasTrib", "ComprasNaoTrib", "ICMS_Compras", "TransfRecTotal", "TransfRecTrib", "TransfRecNaoTrib", "ICMS_TransfRec", "TributosAntecipados"]
        for c in cols_numeric:
            df_trib[c] = pd.to_numeric(df_trib[c], errors="coerce").fillna(0)
            
        tem_movimento = (
            (df_trib["VendasBruto"] > 0) | 
            (df_trib["ComprasTotal"] > 0) | 
            (df_trib["TransfEnvTotal"] > 0) | 
            (df_trib["TransfRecTotal"] > 0) | 
            (df_trib["TributosAntecipados"] != 0)
        )
        df_trib = df_trib[tem_movimento].copy()
        
        if df_trib.empty:
            st.info("Nenhuma filial com movimentação neste período.")
        else:
            df_trib["vendasLiquido"] = df_trib["VendasLiquidoDesconto"] - df_trib["DevolucaoVendas"]
            
            # --- VETORIZAÇÃO (RÁPIDO) ---
            df_trib["tributoVendasIntegral"] = df_trib["ICMS_Vendas"]
            df_trib["pctVendasEfetivo"] = (df_trib["ICMS_Vendas"] / df_trib["VendasBruto"] * 100).fillna(0)
            df_trib["tributoVendasAdicional"] = 0.0
            df_trib["pctAdicional"] = 0.0
            df_trib["icmsTransfEnv"] = df_trib["ICMS_TransfEnv"]
            df_trib["pctTransfEnvEfetivo"] = (df_trib["ICMS_TransfEnv"] / df_trib["TransfEnvTotal"] * 100).fillna(0)
            
            # Atacado (5)
            mask_atacado = df_trib["CodFilial"] == 5
            df_trib.loc[mask_atacado, "tributoVendasIntegral"] = df_trib.loc[mask_atacado, "VendasBruto"] * 0.071
            df_trib.loc[mask_atacado, "pctVendasEfetivo"] = 7.10
            
            mask_adic = mask_atacado & (df_trib["vendasLiquido"] < 400000.0)
            df_trib.loc[mask_adic, "tributoVendasAdicional"] = df_trib.loc[mask_adic, "vendasLiquido"] * 0.049
            df_trib.loc[mask_adic, "pctAdicional"] = 4.90
            
            df_trib.loc[mask_atacado, "icmsTransfEnv"] = df_trib.loc[mask_atacado, "TransfEnvTrib"] * 0.071
            df_trib.loc[mask_atacado, "pctTransfEnvEfetivo"] = 7.10
            df_trib.loc[mask_atacado, "ICMS_Compras"] = 0.0
            df_trib.loc[mask_atacado, "ICMS_TransfRec"] = 0.0
            
            df_trib.loc[mask_atacado, "ComprasTrib"] = 0.0
            df_trib.loc[mask_atacado, "TransfRecTrib"] = 0.0
            df_trib.loc[mask_atacado, "ComprasNaoTrib"] = df_trib.loc[mask_atacado, "ComprasTotal"]
            df_trib.loc[mask_atacado, "TransfRecNaoTrib"] = df_trib.loc[mask_atacado, "TransfRecTotal"]
            
            # SRB (4)
            mask_srb = df_trib["CodFilial"] == 4
            df_trib.loc[mask_srb, "tributoVendasIntegral"] = df_trib.loc[mask_srb, "VendasBruto"] * 0.143
            df_trib.loc[mask_srb, "pctVendasEfetivo"] = 14.30
            
            df_trib.loc[mask_srb, "icmsTransfEnv"] = 0.0
            df_trib.loc[mask_srb, "pctTransfEnvEfetivo"] = 0.0
            df_trib.loc[mask_srb, "ICMS_Compras"] = 0.0
            df_trib.loc[mask_srb, "ICMS_TransfRec"] = 0.0
            
            df_trib.loc[mask_srb, "TransfEnvTrib"] = 0.0
            df_trib.loc[mask_srb, "TransfEnvNaoTrib"] = df_trib.loc[mask_srb, "TransfEnvTotal"]
            df_trib.loc[mask_srb, "ComprasTrib"] = 0.0
            df_trib.loc[mask_srb, "TransfRecTrib"] = 0.0
            df_trib.loc[mask_srb, "ComprasNaoTrib"] = df_trib.loc[mask_srb, "ComprasTotal"]
            df_trib.loc[mask_srb, "TransfRecNaoTrib"] = df_trib.loc[mask_srb, "TransfRecTotal"]
                
            df_trib["totalSaidas"] = df_trib["vendasLiquido"] + df_trib["TransfEnvTotal"]
            df_trib["totalSaidasTrib"] = df_trib["vendasLiquido"] + df_trib["TransfEnvTrib"]
            df_trib["totalSaidasNaoTrib"] = df_trib["TransfEnvNaoTrib"]
            
            df_trib["totalEntradas"] = df_trib["ComprasTotal"] + df_trib["TransfRecTotal"] + df_trib["TributosAntecipados"]
            df_trib["totalEntradasTrib"] = df_trib["ComprasTrib"] + df_trib["TransfRecTrib"] + df_trib["TributosAntecipados"]
            df_trib["totalEntradasNaoTrib"] = df_trib["ComprasNaoTrib"] + df_trib["TransfRecNaoTrib"]
            
            df_trib["debitoICMS"] = df_trib["tributoVendasIntegral"] + df_trib["tributoVendasAdicional"] + df_trib["icmsTransfEnv"]
            df_trib["creditoICMS"] = df_trib["ICMS_Compras"] + df_trib["ICMS_TransfRec"] + df_trib["TributosAntecipados"]
            df_trib["resultado"] = df_trib["creditoICMS"] - df_trib["debitoICMS"]

            atacado = df_trib[df_trib["CodFilial"] == 5]
            pb = df_trib[df_trib["CodFilial"].isin([1, 2, 3])].sort_values("NomeFilial")
            srb = df_trib[df_trib["CodFilial"] == 4]
            colunas = pd.concat([atacado, pb, srb])
            
            rows_saidas = [
                ("Valor Vendas Bruto", "VendasBruto", {}),
                ("Valor Devolução Vendas", "DevolucaoVendas", {"cls": "devolucao"}),
                ("Valor Vendas Líquido", "vendasLiquido", {"bold": True}),
                ("Tributo Vendas Integral", "tributoVendasIntegral", {
                    "fmt": lambda v, f: f"{formatar_moeda(v)} ({f['pctVendasEfetivo']:.2f}%)"
                }),
                ("Tributo Vendas Adicional", "tributoVendasAdicional", {
                    "fmt": lambda v, f: f"{formatar_moeda(v)} ({f['pctAdicional']:.2f}%)"
                }),
                ("Valor Transferências Enviadas", "TransfEnvTotal", {}),
                ("Tributo Transferências Enviadas", "icmsTransfEnv", {
                    "fmt": lambda v, f: f"{formatar_moeda(v)} ({f['pctTransfEnvEfetivo']:.2f}%)"
                }),
                ("Total de Saídas", "totalSaidas", {"bold": True, "cls": "total-saida"}),
                ("Saídas Tributadas", "totalSaidasTrib", {"bold": True, "cls": "subtotal-saida"}),
                ("Saídas Não Tributadas", "totalSaidasNaoTrib", {"bold": True, "cls": "nao-tributada"}),
                ("Tributos Saídas", "debitoICMS", {"bold": True, "cls": "debito bloco-fim"})
            ]
            
            rows_entradas = [
                ("Valor Compras", "ComprasTotal", {}),
                ("Tributo Compras", "ICMS_Compras", {}),
                ("Valor Transferências Recebidas", "TransfRecTotal", {}),
                ("Tributo Transferências Recebidas", "ICMS_TransfRec", {}),
                ("Tributos Antecipados", "TributosAntecipados", {}),
                ("Total de Entradas", "totalEntradas", {"bold": True, "cls": "total-entrada"}),
                ("Entradas Tributadas", "totalEntradasTrib", {"bold": True, "cls": "subtotal-entrada"}),
                ("Entradas Não Tributadas", "totalEntradasNaoTrib", {"bold": True, "cls": "nao-tributada"}),
                ("Tributos Entradas", "creditoICMS", {"bold": True, "cls": "credito bloco-fim"})
            ]
            
            rows_resultado = [
                ("Resultado", "resultado", {"bold": True, "cls": "resultado"})
            ]

            # GERA O PDF
            pdf_bytes = gerar_pdf_tributos(colunas, rows_saidas, rows_entradas, rows_resultado, atacado, pb, srb, data_ini_t, data_fim_t)
            
            # NOME DO ARQUIVO
            timestamp_str = datetime.now(tz_br).strftime("%Y%m%d %H%M%S") if tz_br else datetime.now().strftime("%Y%m%d %H%M%S")
            nome_arquivo = f"Acompanhamento Gerencial - Tributos {timestamp_str}.pdf"

            # BOTÃO DE DOWNLOAD (GERAR PDF) na coluna c5
            with c5:
                st.download_button(
                    label="📄 Gerar PDF",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True
                )

            # RENDERIZA OS CARDS E TABELAS
            saldo_atacado = atacado["resultado"].sum() if not atacado.empty else 0
            saldo_pb = pb["resultado"].sum() if not pb.empty else 0
            saldo_srb = srb["resultado"].sum() if not srb.empty else 0
            saldo_cons = saldo_atacado + saldo_pb + saldo_srb
            
            c_cards = st.columns(4)
            def render_card_trib(col, title, val):
                cor = "#3fb950" if val >= 0 else "#f85149"
                r = int(cor[1:3], 16); g = int(cor[3:5], 16); b = int(cor[5:7], 16)
                bg_color = f"rgba({r}, {g}, {b}, 0.08)"
                with col:
                    st.markdown(f'''
                        <div class="card-item" style="background-color: {bg_color}; border: 1px solid {cor}; border-left: 4px solid {cor};">
                            <div class="card-label" style="color: {cor}; white-space: normal;">{title}</div>
                            <div class="card-value" style="color: {cor};">{formatar_moeda(val)}</div>
                        </div>
                    ''', unsafe_allow_html=True)
            
            render_card_trib(c_cards[0], "📊 Resultado PB - ATACADO", saldo_atacado)
            render_card_trib(c_cards[1], "📊 Resultado PB - FILIAIS", saldo_pb)
            render_card_trib(c_cards[2], "📊 Resultado SRB", saldo_srb)
            render_card_trib(c_cards[3], "📊 Consolidado", saldo_cons)
            
            st.write("") 
            
            def build_trib_table(rows_list):
                html = '<div class="tabela-wrapper"><table class="tributos-tabela">'
                html += '<thead><tr><th style="text-align:left;">Operação</th>'
                for _, f in colunas.iterrows():
                    html += f'<th style="text-align:right;">{f["NomeFilial"]}</th>'
                html += '<th style="text-align:right;">📊 Total</th></tr></thead><tbody>'
                
                for label, key, opts in rows_list:
                    cls = opts.get("cls", "")
                    bold = opts.get("bold", False)
                    label_fmt = f"<strong>{label}</strong>" if bold else label
                    html += f'<tr class="{cls}"><td style="text-align:left; padding-left:8px;">{label_fmt}</td>'
                    total = 0
                    for _, f in colunas.iterrows():
                        val = f[key] if key else 0
                        total += val
                        if "fmt" in opts:
                            val_str = opts["fmt"](val, f)
                        else:
                            val_str = formatar_numero(val)
                        if key == "resultado":
                            val_str = formatar_numero(val) if val >= 0 else f"-{formatar_numero(abs(val))}"
                        html += f'<td style="text-align:right;" class="{cls}">{val_str}</td>'
                        
                    if key == "resultado":
                        total_str = formatar_numero(total) if total >= 0 else f"-{formatar_numero(abs(total))}"
                    else:
                        total_str = formatar_numero(total)
                    html += f'<td style="text-align:right;" class="{cls}">{total_str}</td></tr>'
                
                html += '</tbody></table></div>'
                return html

            tab_saidas, tab_entradas, tab_resultado = st.tabs(["📉 Saídas", "📈 Entradas", "📊 Resultado"])
            
            with tab_saidas:
                st.markdown(build_trib_table(rows_saidas), unsafe_allow_html=True)

            with tab_entradas:
                st.markdown(build_trib_table(rows_entradas), unsafe_allow_html=True)

            with tab_resultado:
                st.markdown(build_trib_table(rows_resultado), unsafe_allow_html=True)