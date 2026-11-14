import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from src.db import carregar_filiais, carregar_fornecedores
from src.base import (
    buscar_tributos,
    buscar_vendas, buscar_departamentos, buscar_pagamentos,
    buscar_sazonalidade, buscar_sazonalidade_hora, buscar_sazonalidade_diautil,
    buscar_compras,
    buscar_transferencias
)

st.set_page_config(page_title="Acompanhamento Gerencial", layout="wide", page_icon="📊")

st.markdown("""
    <style>
        /* Reset e Layout Base */
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 100% !important; background-color: #F3F4F6; }
        
        /* Títulos */
        .titulo-pagina { font-size: 28px; font-weight: 800; text-align: center; color: #111827; padding-bottom: 10px; margin-bottom: 25px; letter-spacing: -0.5px; }
        .tema-titulo { font-size: 18px; font-weight: 700; color: #374151; margin-top: 20px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB; }
        
        /* Cards (Design Premium) */
        .card-item { 
            border-radius: 12px; 
            padding: 20px; 
            height: 100%; 
            display: flex; 
            flex-direction: column; 
            justify-content: space-between; 
            transition: all 0.2s ease-in-out; 
            margin-bottom: 10px; 
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03);
        }
        .card-item:hover { 
            transform: translateY(-2px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); 
            border-color: #D1D5DB;
        }
        .card-label { font-size: 12px; font-weight: 700; color: #6B7280; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-transform: uppercase; letter-spacing: 0.05em;}
        .card-value { font-size: 26px; font-weight: 800; color: #111827; line-height: 1.2; font-variant-numeric: tabular-nums; }
        
        /* Porcentagens */
        .pct-participacao { font-size: 13px; font-weight: 700; color: #D97706; margin-left: 4px; }
        .pct-positiva { font-size: 13px; font-weight: 700; color: #059669; margin-left: 4px; }
        .pct-negativa { font-size: 13px; font-weight: 700; color: #DC2626; margin-left: 4px; }
        
        div[data-testid="stFormSubmitButton"] > button { width: 100% !important; }

        /* Botões do Topo */
        div[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"], div[data-testid="stButton"] button[kind="primary"] {
            background-color: #4F46E5 !important; color: #ffffff !important; border: none !important;
            transition: all 0.2s; height: 44px !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 14px !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        div[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:hover, div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: #4338CA !important; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3) !important;
        }
        
        div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"], div[data-testid="stButton"] button {
            background-color: #EF4444 !important; color: #ffffff !important; border: none !important;
            transition: all 0.2s; height: 44px !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 14px !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"]:hover, div[data-testid="stButton"] button:hover {
            background-color: #DC2626 !important; box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.3) !important;
        }
        
        div[data-testid="stDownloadButton"] button {
            background-color: #3B82F6 !important; color: #ffffff !important; border: none !important;
            transition: all 0.2s; height: 44px !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 14px !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        div[data-testid="stDownloadButton"] button:hover {
            background-color: #2563EB !important; box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3) !important;
        }

        /* Tabelas HTML (Tributos) */
        .tabela-wrapper { overflow-x: auto; margin: 10px 0 25px 0; border-radius: 8px; border: 1px solid #E5E7EB; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05); }
        .tributos-tabela { width: 100%; border-collapse: collapse; font-size: 14px; background: #FFFFFF; }
        .tributos-tabela th { background: #F9FAFB; color: #4B5563; padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 700; white-space: nowrap; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }
        .tributos-tabela td { padding: 10px 16px; border-bottom: 1px solid #F3F4F6; color: #374151; font-weight: 500; font-variant-numeric: tabular-nums; }
        .tributos-tabela td:first-child { text-align: left !important; font-weight: 600; color: #111827; }
        .tributos-tabela td:not(:first-child) { text-align: right !important; }
        .tributos-tabela tr:hover td { background: #F9FAFB; }
        
        /* Cores de Status Tabelas */
        .tributos-tabela .total-entrada td { color: #047857; font-weight: 700; background: #ECFDF5; border-top: 2px solid #A7F3D0; }
        .tributos-tabela .subtotal-entrada td { color: #065F46; font-weight: 600; background: #F0FDF4; }
        .tributos-tabela .total-saida td { color: #B91C1C; font-weight: 700; background: #FEF2F2; border-top: 2px solid #FECACA; }
        .tributos-tabela .subtotal-saida td { color: #991B1B; font-weight: 600; background: #FEF2F2; }
        .tributos-tabela .debito td { color: #DC2626; font-weight: 700; background: #FEE2E2; border-top: 2px solid #EF4444; }
        .tributos-tabela .credito td { color: #059669; font-weight: 700; background: #D1FAE5; border-top: 2px solid #10B981; }
        .tributos-tabela .resultado td { font-weight: 800; font-size: 16px; border-top: 3px double #4F46E5; border-bottom: 3px double #4F46E5; padding-top: 14px; padding-bottom: 14px; }
        .tributos-tabela .resultado td:first-child { color: #4F46E5; }
        .tributos-tabela .devolucao td { color: #DC2626; font-style: italic; }
        .tributos-tabela .nao-tributada td { color: #6B7280; font-style: italic; background: #F9FAFB; }
        
        /* Legendas Sazonalidade */
        .legenda-container { display: flex; gap: 12px; font-size: 12px; color: #4B5563; margin-top: -10px; margin-bottom: 20px; align-items: center; flex-wrap: wrap; background: #FFFFFF; padding: 10px 14px; border-radius: 8px; border: 1px solid #E5E7EB; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02); }
        .legenda-item { display: flex; align-items: center; gap: 6px; font-weight: 600; }
        .legenda-cor { width: 12px; height: 12px; border-radius: 3px; border: 1px solid rgba(0,0,0,0.1); }

        /* Painel de Filtros (Control Panel) */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stWidgetLabel"]) {
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 16px 20px 12px 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
            border: 1px solid #E5E7EB;
            margin-bottom: 24px;
        }
        
        /* Estilo dos Rótulos (De, Até, Filial...) */
        div[data-testid="stWidgetLabel"] p {
            font-size: 11px !important;
            font-weight: 700 !important;
            color: #6B7280 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* ==========================================
           ALINHAMENTO DE FILTROS (LABEL + INPUT NA MESMA LINHA)
           ========================================== */
        div[data-testid="stDateInput"], 
        div[data-testid="stTimeInput"], 
        div[data-testid="stSelectbox"] {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            gap: 8px !important;
        }
        
        /* Remove a margem inferior do rótulo para alinhar com o input */
        div[data-testid="stWidgetLabel"] {
            margin-bottom: 0px !important;
            display: flex;
            align-items: center;
        }
        
        /* Deixa o texto do rótulo um pouco mais escuro e justo ao lado do campo */
        div[data-testid="stWidgetLabel"] p {
            margin-bottom: 0px !important;
            color: #374151 !important;
            font-size: 13px !important;
        }
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

def limpar_vendas():
    st.session_state["dt_ini_visao"] = hoje
    st.session_state["dt_fim_visao"] = hoje
    st.session_state["h_ini_visao"] = datetime.strptime("00:00", "%H:%M").time()
    st.session_state["h_fim_visao"] = datetime.strptime("23:59", "%H:%M").time()
    st.session_state["filial_visao"] = "Todas"
    for k in ["df_vendas", "df_depto_vendas", "df_pag_vendas", "pdf_bytes_vendas"]:
        if k in st.session_state: del st.session_state[k]

def limpar_compras():
    st.session_state["dt_ini_compras"] = date(hoje.year, 1, 1)
    st.session_state["dt_fim_compras"] = date(hoje.year, 12, 31)
    st.session_state["filial_compras"] = "Todas"
    st.session_state["fornecedor_compras"] = "Todos"
    for k in ["df_compras", "pdf_bytes_comp"]:
        if k in st.session_state: del st.session_state[k]

def limpar_transferencias():
    st.session_state["dt_ini_transf"] = date(hoje.year, 1, 1)
    st.session_state["dt_fim_transf"] = date(hoje.year, 12, 31)
    st.session_state["filial_origem_transf"] = "Todas"
    for k in ["df_transf", "pdf_bytes_transf"]:
        if k in st.session_state: del st.session_state[k]

def limpar_tributos():
    st.session_state["dt_ini_trib"] = hoje.replace(day=1)
    st.session_state["dt_fim_trib"] = hoje
    for k in ["df_trib", "pdf_bytes_trib"]:
        if k in st.session_state: del st.session_state[k]

def limpar_sazonalidade():
    st.session_state["dt_ini_saz"] = hoje - timedelta(days=365)
    st.session_state["dt_fim_saz"] = hoje
    st.session_state["h_ini_saz"] = datetime.strptime("08:00", "%H:%M").time()
    st.session_state["h_fim_saz"] = datetime.strptime("20:59", "%H:%M").time()
    for k in ["df_saz_hist", "df_saz_periodo", "df_saz_comparativo", 
              "df_saz_hist_hora", "df_saz_periodo_hora", "df_saz_comp_hora", 
              "df_saz_hist_diautil", "df_saz_periodo_diautil", "df_saz_comp_diautil", 
              "pdf_bytes_saz"]:
        if k in st.session_state: del st.session_state[k]

st.markdown('<div class="titulo-pagina">📊 Acompanhamento Gerencial</div>', unsafe_allow_html=True)

tab_tributos, tab_visao, tab_sazonalidade, tab_compras, tab_transferencias = st.tabs(["⚖️ Tributos", "💰 Vendas", "📅 Sazonalidade", "🛒 Compras", "🔄 Transferências"])

def formatar_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_numero(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_decimal(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_inteiro(v):
    return f"{int(v):,}".replace(",", ".")

def formatar_pct(v):
    return f"{v:.2f}%".replace(".", ",")

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
    cor_transparente = f"rgba({r}, {g}, {b}, 0.3)"
    cores_barras = []
    for v in df_hora[col_valor]:
        if v == max_val and max_val > 0: cores_barras.append(cor_hex)
        else: cores_barras.append(cor_transparente)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_hora["Hora"], y=df_hora[col_valor], marker_color=cores_barras, customdata=custom_data, hovertemplate=hover_tpl))
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=45, xaxis=dict(visible=False, showspikes=False), yaxis=dict(visible=False, rangemode='tozero', showspikes=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, hovermode="x unified", bargap=0.15)
    return fig

def renderizar_tema(titulo, icone, dados, col_valor, cor_hex, tipo_pct, fmt="moeda", campo_itens="porFilial", is_filial=True):
    st.markdown(f'<div class="tema-titulo">{icone} {titulo}</div>', unsafe_allow_html=True)
    total = dados.get("total", 0)
    itens = dados.get(campo_itens, [])
    
    def html_card(nome, valor, pct_html="", is_consolidado=False):
        r = int(cor_hex[1:3], 16); g = int(cor_hex[3:5], 16); b = int(cor_hex[5:7], 16)
        bg_color = f"rgba({r}, {g}, {b}, 0.05)"
        border_left = f"5px solid {cor_hex}"
        style_str = f"border-left: {border_left};"
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
            if i < len(itens): render_card_col(cols[i+1], itens[i])
        itens_restantes = itens[4:]
        for i in range(0, len(itens_restantes), 5):
            chunk = itens_restantes[i:i+5]
            cols_chunk = st.columns(5)
            for j, item in enumerate(chunk): render_card_col(cols_chunk[j], item)
        st.write("")


# ==========================================
# PDF
# ==========================================
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#64748B'))
        self.drawRightString(self._pagesize[0] - 20, 15, f"página {self._pageNumber} de {page_count}")


def gerar_pdf_vendas(df_vendas, df_depto, df_pag, data_ini, data_fim):
    buffer = BytesIO()
    page_size = portrait(A4)
    margin_lr = 20
    usable_width = page_size[0] - (margin_lr * 2)
    doc = SimpleDocTemplate(buffer, pagesize=page_size, rightMargin=margin_lr, leftMargin=margin_lr, topMargin=15, bottomMargin=22)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading2'], alignment=0, fontSize=12, spaceAfter=0, spaceBefore=0)
    period_style = ParagraphStyle('Period', parent=styles['Normal'], alignment=2, fontSize=8, spaceAfter=0)
    section_heading = ParagraphStyle('SectionHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, spaceBefore=4, spaceAfter=3, textColor=colors.HexColor('#1E293B'))
    header_style = ParagraphStyle('Header', parent=styles['Normal'], textColor=colors.white, fontName='Helvetica-Bold', fontSize=8, alignment=1)
    cell_left = ParagraphStyle('CellLeft', parent=styles['Normal'], fontSize=8, alignment=0)
    cell_right = ParagraphStyle('CellRight', parent=styles['Normal'], fontSize=8, alignment=2)
    cell_bold_right = ParagraphStyle('CellBoldRight', parent=styles['Normal'], fontSize=8, alignment=2, fontName='Helvetica-Bold')
    PAD_V = 2; PAD_H = 4

    header_data = [[Paragraph("<b>Acompanhamento Gerencial - Vendas</b>", title_style), Paragraph(f"Período: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", period_style)]]
    header_table = Table(header_data, colWidths=[usable_width * 0.60, usable_width * 0.40])
    header_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 0), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    elements.append(header_table)

    elements.append(Paragraph("<b>RESUMO GERAL (CONSOLIDADO E POR FILIAL)</b>", section_heading))
    filiais_ordem = [5, 1, 2, 3, 4]
    filiais_ativas = [f for f in filiais_ordem if df_vendas[df_vendas["CodFilial"] == f]["ValorVenda"].sum() > 0]
    if filiais_ativas:
        headers = ['Operação'] + [NOMES_FILIAIS[f] for f in filiais_ativas] + ['Total']
        tot_vendas = df_vendas["ValorVenda"].sum(); tot_trans = df_vendas["QtdVendas"].sum(); tot_itens = df_vendas["QtdItens"].sum()
        dados_metricas = {
            "Vendas (R$)": [df_vendas[df_vendas["CodFilial"] == f]["ValorVenda"].sum() for f in filiais_ativas],
            "Transações (Qtd)": [df_vendas[df_vendas["CodFilial"] == f]["QtdVendas"].sum() for f in filiais_ativas],
            "Ticket Médio (R$)": [], "Itens (Qtd)": [df_vendas[df_vendas["CodFilial"] == f]["QtdItens"].sum() for f in filiais_ativas],
            "Itens por Venda (R$)": [], "Itens por Transação (Qtd)": [],
        }
        for f in filiais_ativas:
            v = df_vendas[df_vendas["CodFilial"] == f]["ValorVenda"].sum()
            t = df_vendas[df_vendas["CodFilial"] == f]["QtdVendas"].sum()
            i = df_vendas[df_vendas["CodFilial"] == f]["QtdItens"].sum()
            dados_metricas["Ticket Médio (R$)"].append(v / t if t > 0 else 0)
            dados_metricas["Itens por Venda (R$)"].append(v / i if i > 0 else 0)
            dados_metricas["Itens por Transação (Qtd)"].append(i / t if t > 0 else 0)
        table_data = [[Paragraph(h, header_style) for h in headers]]
        for nome, valores in dados_metricas.items():
            row = [Paragraph(nome, cell_left)]
            for val in valores:
                fmt_val = formatar_moeda(val) if "(R$)" in nome else formatar_decimal(val) if "(Qtd)" in nome else str(int(val))
                row.append(Paragraph(fmt_val, cell_right))
            if nome == "Ticket Médio (R$)": total_val = tot_vendas / tot_trans if tot_trans else 0
            elif nome == "Itens por Venda (R$)": total_val = tot_vendas / tot_itens if tot_itens else 0
            elif nome == "Itens por Transação (Qtd)": total_val = tot_itens / tot_trans if tot_trans else 0
            else: total_val = sum(valores)
            fmt_total = formatar_moeda(total_val) if "(R$)" in nome else formatar_decimal(total_val) if "(Qtd)" in nome else str(int(total_val))
            row.append(Paragraph(fmt_total, cell_bold_right))
            table_data.append(row)
        n_numeric = len(filiais_ativas) + 1
        col_operacao = 120
        col_numeric = (usable_width - col_operacao) / n_numeric
        col_widths = [col_operacao] + [col_numeric] * n_numeric
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]), ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V), ('TOPPADDING', (0, 0), (-1, -1), PAD_V), ('LEFTPADDING', (0, 0), (-1, -1), PAD_H), ('RIGHTPADDING', (0, 0), (-1, -1), PAD_H)]))
        elements.append(t)
        elements.append(Spacer(1, 4))

    if not df_depto.empty:
        elements.append(Paragraph("<b>VENDAS POR DEPARTAMENTO</b>", section_heading))
        df_depto_agg = df_depto.groupby("NomeDepto")["ValorVenda"].sum().reset_index().sort_values("ValorVenda", ascending=False)
        total_depto = df_depto_agg["ValorVenda"].sum()
        depto_data = [[Paragraph("Departamento", header_style), Paragraph("Vendas (R$)", header_style), Paragraph("Participação", header_style)]]
        for _, row in df_depto_agg.iterrows():
            pct = (row["ValorVenda"] / total_depto * 100) if total_depto > 0 else 0
            depto_data.append([Paragraph(row["NomeDepto"], cell_left), Paragraph(formatar_moeda(row["ValorVenda"]), cell_right), Paragraph(formatar_pct(pct), cell_right)])
        col3_widths = [usable_width * 0.50, usable_width * 0.30, usable_width * 0.20]
        t_depto = Table(depto_data, colWidths=col3_widths, repeatRows=1)
        t_depto.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]), ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V), ('TOPPADDING', (0, 0), (-1, -1), PAD_V), ('LEFTPADDING', (0, 0), (-1, -1), PAD_H), ('RIGHTPADDING', (0, 0), (-1, -1), PAD_H)]))
        elements.append(t_depto)
        elements.append(Spacer(1, 4))

    if not df_pag.empty:
        elements.append(Paragraph("<b>VENDAS POR FORMA DE PAGAMENTO</b>", section_heading))
        df_pag_agg = df_pag.groupby("Denominacao")["Valor"].sum().reset_index().sort_values("Valor", ascending=False)
        total_pag = df_pag_agg["Valor"].sum()
        pag_data = [[Paragraph("Forma de Pagamento", header_style), Paragraph("Vendas (R$)", header_style), Paragraph("Participação", header_style)]]
        for _, row in df_pag_agg.iterrows():
            pct = (row["Valor"] / total_pag * 100) if total_pag > 0 else 0
            pag_data.append([Paragraph(row["Denominacao"], cell_left), Paragraph(formatar_moeda(row["Valor"]), cell_right), Paragraph(formatar_pct(pct), cell_right)])
        col3_widths = [usable_width * 0.50, usable_width * 0.30, usable_width * 0.20]
        t_pag = Table(pag_data, colWidths=col3_widths, repeatRows=1)
        t_pag.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]), ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V), ('TOPPADDING', (0, 0), (-1, -1), PAD_V), ('LEFTPADDING', (0, 0), (-1, -1), PAD_H), ('RIGHTPADDING', (0, 0), (-1, -1), PAD_H)]))
        elements.append(t_pag)
        elements.append(Spacer(1, 4))
        df_pag_port = df_pag.dropna(subset=["NomePortador"])
        if not df_pag_port.empty:
            elements.append(Paragraph("<b>VENDAS POR PORTADOR</b>", section_heading))
            df_port_agg = df_pag_port.groupby("NomePortador")["Valor"].sum().reset_index().sort_values("Valor", ascending=False)
            total_port = df_port_agg["Valor"].sum()
            port_data = [[Paragraph("Portador", header_style), Paragraph("Vendas (R$)", header_style), Paragraph("Participação", header_style)]]
            for _, row in df_port_agg.iterrows():
                pct = (row["Valor"] / total_port * 100) if total_port > 0 else 0
                port_data.append([Paragraph(row["NomePortador"], cell_left), Paragraph(formatar_moeda(row["Valor"]), cell_right), Paragraph(formatar_pct(pct), cell_right)])
            col3_widths = [usable_width * 0.50, usable_width * 0.30, usable_width * 0.20]
            t_port = Table(port_data, colWidths=col3_widths, repeatRows=1)
            t_port.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]), ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V), ('TOPPADDING', (0, 0), (-1, -1), PAD_V), ('LEFTPADDING', (0, 0), (-1, -1), PAD_H), ('RIGHTPADDING', (0, 0), (-1, -1), PAD_H)]))
            elements.append(t_port)

    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer


def gerar_pdf_compras(df_compras, data_ini, data_fim):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    left_style = ParagraphStyle('Left', parent=styles['Heading2'], alignment=0, fontSize=12, spaceAfter=0)
    right_style = ParagraphStyle('Right', parent=styles['Normal'], alignment=2, fontSize=10, spaceAfter=0)
    header_data = [[Paragraph("<b>Acompanhamento Gerencial - Compras</b>", left_style), Paragraph(f"Período: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", right_style)]]
    header_table = Table(header_data, colWidths=[400, 400])
    header_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 15), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    elements.append(header_table)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], textColor=colors.white, fontName='Helvetica-Bold', fontSize=7, alignment=1)
    cell_left = ParagraphStyle('CellLeft', parent=styles['Normal'], fontSize=7, alignment=0)
    cell_right = ParagraphStyle('CellRight', parent=styles['Normal'], fontSize=7, alignment=2)
    cell_bold_left = ParagraphStyle('CellBoldLeft', parent=styles['Normal'], fontSize=7, alignment=0, fontName='Helvetica-Bold')
    cell_bold_right = ParagraphStyle('CellBoldRight', parent=styles['Normal'], fontSize=7, alignment=2, fontName='Helvetica-Bold')
    meses_colunas = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_tot_depto = df_compras.groupby("Departamento")["Valor"].sum().reset_index().sort_values("Departamento")
    df_resumo = df_compras.pivot_table(index="Departamento", columns="Mes_Nome", values="Valor", aggfunc="sum")
    for m in meses_colunas:
        if m not in df_resumo.columns: df_resumo[m] = 0.0
    df_resumo = df_resumo[meses_colunas]
    df_resumo["Total"] = df_resumo.sum(axis=1)
    df_resumo = df_resumo.fillna(0).sort_index()
    linha_total_geral = df_resumo.sum().to_frame().T
    linha_total_geral.index = ["TOTAL GERAL"]
    df_resumo_final = pd.concat([df_resumo, linha_total_geral])
    elements.append(Paragraph("<b>RESUMO POR DEPARTAMENTO (MENSAL)</b>", styles['Heading3']))
    resumo_headers = ['Departamento'] + meses_colunas + ['Total Anual']
    resumo_data = [[Paragraph(h, header_style) for h in resumo_headers]]
    for depto, r in df_resumo_final.iterrows():
        is_total = (depto == "TOTAL GERAL")
        row_cells = [Paragraph(depto, cell_bold_left if is_total else cell_left)]
        for m in meses_colunas + ['Total']:
            val = r[m]
            val_str = formatar_numero(val) if val != 0 else "-"
            row_cells.append(Paragraph(val_str, cell_bold_right if is_total else cell_right))
        resumo_data.append(row_cells)
    col_widths_resumo = [150] + [48] * len(meses_colunas) + [65]
    t_resumo = Table(resumo_data, colWidths=col_widths_resumo, repeatRows=1)
    t_resumo.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DBEAFE')), ('LINEABOVE', (0, -1), (-1, -1), 1.2, colors.HexColor('#1E293B'))]))
    elements.append(t_resumo)
    elements.append(Spacer(1, 10))
    for _, row in df_tot_depto.iterrows():
        depto = row['Departamento']
        df_d = df_compras[df_compras["Departamento"] == depto]
        df_pivot = df_d.pivot_table(index=['Fornecedor'], columns='Mes_Nome', values='Valor', aggfunc='sum')
        for m in meses_colunas:
            if m not in df_pivot.columns: df_pivot[m] = 0.0
        df_pivot = df_pivot[meses_colunas]
        df_pivot['Total'] = df_pivot.sum(axis=1)
        df_pivot = df_pivot.fillna(0).sort_index()
        linha_total = df_pivot.sum().to_frame().T
        linha_total.index = ['TOTAL']
        df_final = pd.concat([df_pivot, linha_total])
        headers = ['Fornecedor'] + meses_colunas + ['Total']
        table_data = [[Paragraph(h, header_style) for h in headers]]
        for fornecedor, r in df_final.iterrows():
            is_total = (fornecedor == 'TOTAL')
            row_cells = [Paragraph(fornecedor, cell_bold_left if is_total else cell_left)]
            for m in meses_colunas + ['Total']:
                val = r[m]
                val_str = formatar_numero(val) if val != 0 else "-"
                row_cells.append(Paragraph(val_str, cell_bold_right if is_total else cell_right))
            table_data.append(row_cells)
        elements.append(Paragraph(f"<b>■ Departamento: {depto}</b>", styles['Heading3']))
        col_widths = [130] + [50] * len(meses_colunas) + [70]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 4)]))
        elements.append(t)
        elements.append(Spacer(1, 15))
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer


def gerar_pdf_transferencias(df_transf, data_ini, data_fim):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    left_style = ParagraphStyle('Left', parent=styles['Heading2'], alignment=0, fontSize=12, spaceAfter=0)
    right_style = ParagraphStyle('Right', parent=styles['Normal'], alignment=2, fontSize=10, spaceAfter=0)
    header_data = [[Paragraph("<b>Acompanhamento Gerencial - Transferências</b>", left_style), Paragraph(f"Período: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", right_style)]]
    header_table = Table(header_data, colWidths=[400, 400])
    header_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 15), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    elements.append(header_table)

    header_style = ParagraphStyle('Header', parent=styles['Normal'], textColor=colors.white, fontName='Helvetica-Bold', fontSize=7, alignment=1)
    cell_left = ParagraphStyle('CellLeft', parent=styles['Normal'], fontSize=7, alignment=0)
    cell_right = ParagraphStyle('CellRight', parent=styles['Normal'], fontSize=7, alignment=2)
    cell_bold_left = ParagraphStyle('CellBoldLeft', parent=styles['Normal'], fontSize=7, alignment=0, fontName='Helvetica-Bold')
    cell_bold_right = ParagraphStyle('CellBoldRight', parent=styles['Normal'], fontSize=7, alignment=2, fontName='Helvetica-Bold')
    sub_heading = ParagraphStyle('SubHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, spaceBefore=6, spaceAfter=3, textColor=colors.HexColor('#1E293B'))

    meses_colunas = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

    df_entradas_all = df_transf[df_transf["TipoDado"] == "ENTRADA"].copy()
    df_saidas_all = df_transf[df_transf["TipoDado"] == "SAIDA"].copy()

    df_resumo = df_saidas_all.pivot_table(index="FilialDestino", columns="Mes_Nome", values="Valor", aggfunc="sum")
    for m in meses_colunas:
        if m not in df_resumo.columns: df_resumo[m] = 0.0
    if df_resumo.empty:
        df_resumo = pd.DataFrame(columns=meses_colunas + ['Total'])
    else:
        df_resumo = df_resumo[meses_colunas]
        df_resumo["Total"] = df_resumo.sum(axis=1)
        df_resumo = df_resumo.fillna(0).sort_index()

    linha_total_geral = df_resumo.sum().to_frame().T
    linha_total_geral.index = ["TOTAL GERAL"]
    df_resumo_final = pd.concat([df_resumo, linha_total_geral])

    elements.append(Paragraph("<b>RESUMO POR FILIAL DESTINO (MENSAL) — baseado em SAÍDAS</b>", styles['Heading3']))
    resumo_headers = ['Filial Destino'] + meses_colunas + ['Total Anual']
    resumo_data = [[Paragraph(h, header_style) for h in resumo_headers]]
    for destino, r in df_resumo_final.iterrows():
        is_total = (destino == "TOTAL GERAL")
        nome_dest = "TOTAL GERAL" if is_total else NOMES_FILIAIS.get(int(destino), f"Filial {destino}")
        row_cells = [Paragraph(nome_dest, cell_bold_left if is_total else cell_left)]
        for m in meses_colunas + ['Total']:
            val = r[m] if m in r else 0
            val_str = formatar_numero(val) if val != 0 else "-"
            row_cells.append(Paragraph(val_str, cell_bold_right if is_total else cell_right))
        resumo_data.append(row_cells)
    col_widths_resumo = [150] + [48] * len(meses_colunas) + [65]
    t_resumo = Table(resumo_data, colWidths=col_widths_resumo, repeatRows=1)
    t_resumo.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DBEAFE')), ('LINEABOVE', (0, -1), (-1, -1), 1.2, colors.HexColor('#1E293B'))]))
    elements.append(t_resumo)
    elements.append(Spacer(1, 10))

    def montar_tabela_pivot(df_sub, coluna_index, cor_header_hex):
        if df_sub.empty:
            return None
        df_pivot = df_sub.pivot_table(index=coluna_index, columns='Mes_Nome', values='Valor', aggfunc='sum')
        for m in meses_colunas:
            if m not in df_pivot.columns: df_pivot[m] = 0.0
        df_pivot = df_pivot[meses_colunas]
        df_pivot['Total'] = df_pivot.sum(axis=1)
        df_pivot = df_pivot.fillna(0).sort_index()
        linha_total = df_pivot.sum().to_frame().T
        linha_total.index = ['TOTAL']
        df_final = pd.concat([df_pivot, linha_total])
        headers = [coluna_index] + meses_colunas + ['Total']
        table_data = [[Paragraph(h, header_style) for h in headers]]
        for chave, r in df_final.iterrows():
            is_total = (chave == 'TOTAL')
            nome = "TOTAL" if is_total else NOMES_FILIAIS.get(int(chave), f"Filial {chave}")
            row_cells = [Paragraph(nome, cell_bold_left if is_total else cell_left)]
            for m in meses_colunas + ['Total']:
                val = r[m]
                val_str = formatar_numero(val) if val != 0 else "-"
                row_cells.append(Paragraph(val_str, cell_bold_right if is_total else cell_right))
            table_data.append(row_cells)
        col_widths = [130] + [50] * len(meses_colunas) + [70]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(cor_header_hex)), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 4)]))
        return t

    todas_filiais = sorted(set(df_entradas_all["FilialDestino"].unique().tolist() + df_saidas_all["FilialOrigem"].unique().tolist()))

    for filial in todas_filiais:
        nome_filial = NOMES_FILIAIS.get(int(filial), f"Filial {filial}")
        elements.append(Paragraph(f"<b>■ Filial: {nome_filial}</b>", styles['Heading3']))

        df_ent = df_entradas_all[df_entradas_all["FilialDestino"] == filial]
        elements.append(Paragraph(f"<b>📥 ENTRADAS em {nome_filial}</b>", sub_heading))
        t_ent = montar_tabela_pivot(df_ent, "FilialOrigem", '#065F46')
        if t_ent: elements.append(t_ent)
        else: elements.append(Paragraph("<i>Nenhuma entrada no período.</i>", styles['Normal']))
        elements.append(Spacer(1, 6))

        df_sai = df_saidas_all[df_saidas_all["FilialOrigem"] == filial]
        elements.append(Paragraph(f"<b>📤 SAÍDAS de {nome_filial}</b>", sub_heading))
        t_sai = montar_tabela_pivot(df_sai, "FilialDestino", '#7F1D1D')
        if t_sai: elements.append(t_sai)
        else: elements.append(Paragraph("<i>Nenhuma saída no período.</i>", styles['Normal']))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph(f"<b>💰 SALDO em {nome_filial} (Entradas − Saídas)</b>", sub_heading))

        tot_ent_mes = {m: (df_ent[df_ent["Mes_Nome"] == m]["Valor"].sum() if not df_ent.empty else 0.0) for m in meses_colunas}
        tot_sai_mes = {m: (df_sai[df_sai["Mes_Nome"] == m]["Valor"].sum() if not df_sai.empty else 0.0) for m in meses_colunas}
        tot_ent_ano = sum(tot_ent_mes.values())
        tot_sai_ano = sum(tot_sai_mes.values())
        saldo_ano = tot_ent_ano - tot_sai_ano

        saldo_rows = [
            ("📥 Total Entradas", tot_ent_mes, tot_ent_ano),
            ("📤 Total Saídas", tot_sai_mes, tot_sai_ano),
            ("💰 Saldo", {m: tot_ent_mes[m] - tot_sai_mes[m] for m in meses_colunas}, saldo_ano),
        ]

        saldo_headers = ['Descrição'] + meses_colunas + ['Total']
        saldo_data = [[Paragraph(h, header_style) for h in saldo_headers]]

        for label, vals_mes, val_total in saldo_rows:
            is_saldo = label.startswith("💰")
            row_cells = [Paragraph(label, cell_bold_left if is_saldo else cell_left)]
            for m in meses_colunas:
                v = vals_mes[m]
                if v == 0:
                    txt = "-"
                elif is_saldo:
                    txt = ("-" if v < 0 else "+") + formatar_numero(abs(v))
                else:
                    txt = formatar_numero(v)
                row_cells.append(Paragraph(txt, cell_bold_right if is_saldo else cell_right))
            if val_total == 0:
                txt_total = "-"
            elif is_saldo:
                txt_total = ("-" if val_total < 0 else "+") + formatar_numero(abs(val_total))
            else:
                txt_total = formatar_numero(val_total)
            row_cells.append(Paragraph(txt_total, cell_bold_right if is_saldo else cell_right))
            saldo_data.append(row_cells)

        col_widths_saldo = [130] + [50] * len(meses_colunas) + [70]
        t_saldo = Table(saldo_data, colWidths=col_widths_saldo, repeatRows=1)
        style_saldo = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FEF3C7')),
            ('LINEABOVE', (0, -1), (-1, -1), 1.2, colors.HexColor('#D97706')),
        ]
        t_saldo.setStyle(TableStyle(style_saldo))
        elements.append(t_saldo)
        elements.append(Spacer(1, 12))

    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer


def gerar_pdf_tributos(colunas, rows_saidas, rows_entradas, rows_resultado, atacado, pb, srb, data_ini, data_fim):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    left_style = ParagraphStyle('Left', parent=styles['Heading2'], alignment=0, fontSize=12, spaceAfter=0)
    right_style = ParagraphStyle('Right', parent=styles['Normal'], alignment=2, fontSize=10, spaceAfter=0)
    header_data = [[Paragraph("<b>Acompanhamento Gerencial - Tributos</b>", left_style), Paragraph(f"Período: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", right_style)]]
    header_table = Table(header_data, colWidths=[400, 400])
    header_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 15), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    elements.append(header_table)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], textColor=colors.white, fontName='Helvetica-Bold', fontSize=8, alignment=1)
    cell_left = ParagraphStyle('CellLeft', parent=styles['Normal'], fontSize=8, alignment=0)
    cell_right = ParagraphStyle('CellRight', parent=styles['Normal'], fontSize=8, alignment=2)
    cell_bold_right = ParagraphStyle('CellBoldRight', parent=styles['Normal'], fontSize=8, alignment=2, fontName='Helvetica-Bold')
    cell_bold_left = ParagraphStyle('CellBoldLeft', parent=styles['Normal'], fontSize=8, alignment=0, fontName='Helvetica-Bold')
    headers = ['Operação'] + [f['NomeFilial'] for _, f in colunas.iterrows()] + ['Total']
    table_data = [[Paragraph(h, header_style) for h in headers]]
    def add_row_to_data(label, key, opts):
        bold = opts.get('bold', False)
        left_s = cell_bold_left if bold else cell_left
        right_s = cell_bold_right if bold else cell_right
        row = [Paragraph(label, left_s)]
        total = 0
        for _, f in colunas.iterrows():
            val = f[key] if key else 0
            total += val
            if 'fmt' in opts:
                try: val_str = opts['fmt'](val, f)
                except: val_str = formatar_moeda(val)
            else: val_str = formatar_moeda(val)
            if key == 'resultado':
                val_str = f"-{formatar_moeda(abs(val))}" if val < 0 else formatar_moeda(val)
            row.append(Paragraph(val_str, right_s))
        if key == 'resultado':
            total_str = formatar_moeda(total) if total >= 0 else f"-{formatar_moeda(abs(total))}"
        else:
            total_str = formatar_moeda(total)
        row.append(Paragraph(total_str, right_s))
        return row
    for label, key, opts in rows_saidas + rows_entradas + rows_resultado:
        table_data.append(add_row_to_data(label, key, opts))
    col_widths = [150] + [115] * len(colunas) + [75]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]), ('FONTSIZE', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 4)]))
    elements.append(t)
    elements.append(Spacer(1, 15))
    saldo_atacado = atacado["resultado"].sum() if not atacado.empty else 0
    saldo_pb = pb["resultado"].sum() if not pb.empty else 0
    saldo_srb = srb["resultado"].sum() if not srb.empty else 0
    saldo_cons = saldo_atacado + saldo_pb + saldo_srb
    result_style = ParagraphStyle('Result', parent=styles['Normal'], alignment=1, fontSize=11, spaceAfter=10)
    results_text = f"Resultado PB - ATACADO: {formatar_moeda(saldo_atacado)} &nbsp;&nbsp;&nbsp; Resultado PB - FILIAIS: {formatar_moeda(saldo_pb)} &nbsp;&nbsp;&nbsp; Resultado SRB: {formatar_moeda(saldo_srb)} &nbsp;&nbsp;&nbsp; Consolidado: {formatar_moeda(saldo_cons)}"
    elements.append(Paragraph(results_text, result_style))
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer

# ==========================================
# SAZONALIDADE — funções auxiliares
# ==========================================
DIAS_SEMANA = {1: "Segunda", 2: "Terça", 3: "Quarta", 4: "Quinta", 5: "Sexta", 6: "Sábado"}

def formatar_indice(v):
    if pd.isna(v): return "-"
    return f"{v:.4f}".replace(".", ",")

def formatar_variacao_pct(v):
    if pd.isna(v): return "-"
    return f"{v:+.2f}%".replace(".", ",")

def _calc_idx_generic(df, col_name, index_range, multiplier):
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["CodFilial"] = pd.to_numeric(df["CodFilial"], errors="coerce").fillna(0).astype(int)
    df[col_name] = pd.to_numeric(df[col_name], errors="coerce").fillna(0).astype(int)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["QtdDias"] = pd.to_numeric(df["QtdDias"], errors="coerce").fillna(0)

    resultado = {}
    for cod in [1, 2, 3, 4]:
        sub = df[df["CodFilial"] == cod]
        if sub.empty:
            continue
        soma_idx = sub.groupby(col_name)["Valor"].sum()
        qtd_idx = sub.groupby(col_name)["QtdDias"].sum()
        media_idx = (soma_idx / qtd_idx).replace([float("inf"), -float("inf")], 0).fillna(0)
        media_geral = sub["Valor"].sum() / sub["QtdDias"].sum() if sub["QtdDias"].sum() > 0 else 0
        if media_geral == 0:
            continue
        idx_bruto = media_idx / media_geral
        soma_idx = idx_bruto.sum()
        if soma_idx == 0:
            continue
        idx_norm = idx_bruto * multiplier / soma_idx
        resultado[cod] = idx_norm

    if not resultado:
        return pd.DataFrame()

    df_idx = pd.DataFrame(resultado)
    df_idx = df_idx.reindex(index_range).fillna(0)
    df_idx["Total"] = df_idx.mean(axis=1)
    
    nomes = {cod: NOMES_FILIAIS.get(cod, f"Filial {cod}") for cod in [1, 2, 3, 4]}
    df_idx = df_idx.rename(columns=nomes)
    return df_idx

def calcular_indices_sazonalidade(df):
    df_idx = _calc_idx_generic(df, "DiaSemana", range(1, 7), 6)
    if not df_idx.empty:
        df_idx.index = [DIAS_SEMANA[d] for d in df_idx.index]
        df_idx.index.name = "Dia da Semana"
    return df_idx

def calcular_indices_sazonalidade_hora(df):
    df_idx = _calc_idx_generic(df, "Hora", range(0, 24), 24)
    if not df_idx.empty:
        df_idx.index = [f"{h:02d}:00" for h in df_idx.index]
        df_idx.index.name = "Hora"
        df_idx = df_idx[df_idx["Total"] > 0]  # ← NOVO: remove horas sem movimento
    return df_idx
    
def calcular_indices_sazonalidade_diautil(df):
    # Usa 21 como multiplicador base (média de dias úteis no mês)
    df_idx = _calc_idx_generic(df, "DiaUtil", range(1, 24), 21)
    if not df_idx.empty:
        df_idx.index = [f"{d}º Dia" for d in df_idx.index]
        df_idx.index.name = "Dia Útil"
        df_idx = df_idx[df_idx["Total"] > 0]  # Remove dias sem movimento
    return df_idx

def gerar_pdf_sazonalidade(df_hist_idx, df_periodo_idx, df_comparativo, df_hist_hora, df_periodo_hora, df_comp_hora, df_hist_diautil, df_periodo_diautil, df_comp_diautil, data_ini, data_fim, h_ini, h_fim):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=portrait(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    left_style = ParagraphStyle('Left', parent=styles['Heading2'], alignment=0, fontSize=12, spaceAfter=0)
    right_style = ParagraphStyle('Right', parent=styles['Normal'], alignment=2, fontSize=10, spaceAfter=0)
    
    txt_periodo = f"Período: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')} | {h_ini.strftime('%H:%M')} às {h_fim.strftime('%H:%M')}"
    header_data = [[Paragraph("<b>Acompanhamento Gerencial - Sazonalidade</b>", left_style), Paragraph(txt_periodo, right_style)]]
    
    header_table = Table(header_data, colWidths=[300, 255])
    header_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 15), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    elements.append(header_table)

    def montar_tabela(df_idx, formato_func, com_pct=False, is_hora=False):
        if df_idx is None or df_idx.empty:
            return Paragraph("<i>Sem dados.</i>", styles['Normal'])
        
        font_sz = 6.5 if is_hora else 8
        pad_v = 1 if is_hora else 4
        
        header_style = ParagraphStyle(f'Header_{is_hora}', parent=styles['Normal'], textColor=colors.white, fontName='Helvetica-Bold', fontSize=font_sz, alignment=1)
        cell_left = ParagraphStyle(f'CellLeft_{is_hora}', parent=styles['Normal'], fontSize=font_sz, alignment=0)
        cell_right = ParagraphStyle(f'CellRight_{is_hora}', parent=styles['Normal'], fontSize=font_sz, alignment=2)

        headers = [df_idx.index.name or "Index"] + list(df_idx.columns)
        data = [[Paragraph(h, header_style) for h in headers]]
        for idx, row in df_idx.iterrows():
            cells = [Paragraph(str(idx), cell_left)]
            for col in df_idx.columns:
                v = row[col]
                if com_pct and col != "Total" and not pd.isna(v) and v != 0:
                    total = row["Total"]
                    pct = ((v / total) - 1) * 100 if total > 0 else 0
                    txt = f"{v:.4f} ({pct:+.2f}%)".replace(".", ",")
                else:
                    txt = formato_func(v)
                cells.append(Paragraph(txt, cell_right))
            data.append(cells)
        
        col_widths = [90] + [93] * len(df_idx.columns) 
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), pad_v),
            ('TOPPADDING', (0, 0), (-1, -1), pad_v),
        ]))
        return t

    heading_dia = ParagraphStyle('H_Dia', parent=styles['Heading3'], fontSize=10, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor('#1E293B'))
    heading_hora = ParagraphStyle('H_Hora', parent=styles['Heading3'], fontSize=8, spaceBefore=4, spaceAfter=2, textColor=colors.HexColor('#1E293B'))

    # FOLHA 1: DIAS DA SEMANA
    elements.append(Paragraph("<b>ÍNDICE DE SAZONALIDADE (DIAS) — HISTÓRICO COMPLETO</b>", heading_dia))
    elements.append(montar_tabela(df_hist_idx, formatar_indice, com_pct=True))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>ÍNDICE DE SAZONALIDADE (DIAS) — PERÍODO SELECIONADO</b>", heading_dia))
    elements.append(montar_tabela(df_periodo_idx, formatar_indice, com_pct=True))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>COMPARATIVO (DIAS) — PERÍODO vs. HISTÓRICO (variação %)</b>", heading_dia))
    elements.append(montar_tabela(df_comparativo, formatar_variacao_pct))
    
    elements.append(PageBreak())
    
    # FOLHA 2: HORAS
    elements.append(Paragraph("<b>ÍNDICE DE SAZONALIDADE (HORAS) — HISTÓRICO COMPLETO</b>", heading_hora))
    elements.append(montar_tabela(df_hist_hora, formatar_indice, com_pct=True, is_hora=True))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("<b>ÍNDICE DE SAZONALIDADE (HORAS) — PERÍODO SELECIONADO</b>", heading_hora))
    elements.append(montar_tabela(df_periodo_hora, formatar_indice, com_pct=True, is_hora=True))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("<b>COMPARATIVO (HORAS) — PERÍODO vs. HISTÓRICO (variação %)</b>", heading_hora))
    elements.append(montar_tabela(df_comp_hora, formatar_variacao_pct, is_hora=True))

    elements.append(PageBreak())

    # FOLHA 3: DIAS ÚTEIS
    elements.append(Paragraph("<b>ÍNDICE DE SAZONALIDADE (DIAS ÚTEIS) — HISTÓRICO COMPLETO</b>", heading_dia))
    elements.append(montar_tabela(df_hist_diautil, formatar_indice, com_pct=True))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>ÍNDICE DE SAZONALIDADE (DIAS ÚTEIS) — PERÍODO SELECIONADO</b>", heading_dia))
    elements.append(montar_tabela(df_periodo_diautil, formatar_indice, com_pct=True))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>COMPARATIVO (DIAS ÚTEIS) — PERÍODO vs. HISTÓRICO (variação %)</b>", heading_dia))
    elements.append(montar_tabela(df_comp_diautil, formatar_variacao_pct))

    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer

# ==========================================
# ABA VENDAS
# ==========================================
with tab_visao:
    if "dt_ini_visao" not in st.session_state: st.session_state["dt_ini_visao"] = hoje
    if "dt_fim_visao" not in st.session_state: st.session_state["dt_fim_visao"] = hoje
    if "h_ini_visao" not in st.session_state: st.session_state["h_ini_visao"] = datetime.strptime("00:00", "%H:%M").time()
    if "h_fim_visao" not in st.session_state: st.session_state["h_fim_visao"] = datetime.strptime("23:59", "%H:%M").time()
    if "filial_visao" not in st.session_state: st.session_state["filial_visao"] = "Todas"

    with st.container(border=True):
        c1, c2, c3, c4, c5, c_acoes = st.columns([1, 1, 1, 1, 1.2, 2.5], vertical_alignment="bottom")
        data_ini = c1.date_input("De:", key="dt_ini_visao", format="DD/MM/YYYY")
        data_fim = c2.date_input("Até:", key="dt_fim_visao", format="DD/MM/YYYY")
        h_ini = c3.time_input("Hora:", key="h_ini_visao")
        h_fim = c4.time_input("Até:", key="h_fim_visao")
        filial_sel = c5.selectbox("Filial:", ["Todas"] + list(filiais_inv.keys()), key="filial_visao")

        with c_acoes:
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                btn_atualizar = st.button("🔄 Atualizar", use_container_width=True, type="primary", key="btn_atualizar_visao")
            with col_b2:
                st.button("🧹 Limpar", use_container_width=True, on_click=limpar_vendas, key="btn_limpar_visao")
            with col_b3:
                pdf_bytes_visao = st.session_state.get("pdf_bytes_vendas")
                if pdf_bytes_visao:
                    ts = datetime.now(tz_br).strftime("%Y%m%d %H%M%S") if tz_br else datetime.now().strftime("%Y%m%d %H%M%S")
                    st.download_button(label="📄 Gerar PDF", data=pdf_bytes_visao, file_name=f"Acompanhamento Gerencial - Vendas {ts}.pdf", mime="application/pdf", use_container_width=True, key="btn_pdf_vendas")
                else:
                    st.button("📄 Gerar PDF", disabled=True, use_container_width=True, key="btn_pdf_vendas_disabled")

    _foi_primeira_carga_visao = "df_vendas" not in st.session_state
    if _foi_primeira_carga_visao or btn_atualizar:
        filial_cod = "" if filial_sel == "Todas" else filiais_inv[filial_sel]
        try:
            with st.spinner("Carregando dados..."):
                df_vendas = buscar_vendas(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), h_ini.hour, h_fim.hour, filial_cod)
                if not df_vendas.empty:
                    df_vendas["CodFilial"] = pd.to_numeric(df_vendas["CodFilial"], errors="coerce").fillna(0).astype(int)
                df_depto = buscar_departamentos(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), h_ini.hour, h_fim.hour, filial_cod)
                df_pag = buscar_pagamentos(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), h_ini.hour, h_fim.hour, filial_cod)
                st.session_state["df_vendas"] = df_vendas
                st.session_state["df_depto_vendas"] = df_depto
                st.session_state["df_pag_vendas"] = df_pag
                st.session_state["pdf_bytes_vendas"] = gerar_pdf_vendas(df_vendas, df_depto, df_pag, data_ini, data_fim) if not df_vendas.empty else None
        except Exception as e:
            st.error(f"Erro ao carregar dados de vendas: {e}")
            st.stop()

    if _foi_primeira_carga_visao: st.rerun()

    df_vendas = st.session_state.get("df_vendas", pd.DataFrame())
    df_depto = st.session_state.get("df_depto_vendas", pd.DataFrame())
    df_pag = st.session_state.get("df_pag_vendas", pd.DataFrame())

    if df_vendas.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
    else:
        labels_h = sorted(df_vendas["Hora"].unique().tolist())
        tot_vendas = df_vendas["ValorVenda"].sum()
        tot_trans = df_vendas["QtdVendas"].sum()
        tot_itens = df_vendas["QtdItens"].sum()
        temas = [
            {"id": "vendas", "titulo": "Vendas", "icone": "💰", "total": tot_vendas, "col": "ValorVenda", "cor": "#3b82f6", "fmt": "moeda", "pct": "participacao"},
            {"id": "transacoes", "titulo": "Transações", "icone": "🛒", "total": tot_trans, "col": "QtdVendas", "cor": "#10b981", "fmt": "inteiro", "pct": "participacao"},
            {"id": "ticket", "titulo": "Ticket Médio", "icone": "🎫", "total": (tot_vendas / tot_trans if tot_trans else 0), "col": "Ticket", "cor": "#f59e0b", "fmt": "moeda", "pct": "variacao"},
            {"id": "itens", "titulo": "Itens", "icone": "📦", "total": tot_itens, "col": "QtdItens", "cor": "#8b5cf6", "fmt": "decimal", "pct": "participacao"},
            {"id": "itens_venda", "titulo": "Itens por Venda (R$/item)", "icone": "💰", "total": (tot_vendas / tot_itens if tot_itens else 0), "col": "ItensVenda", "cor": "#14b8a6", "fmt": "moeda", "pct": "variacao"},
            {"id": "itens_trans", "titulo": "Itens por Transação", "icone": "📊", "total": (tot_itens / tot_trans if tot_trans else 0), "col": "ItensTrans", "cor": "#ec4899", "fmt": "decimal", "pct": "variacao"},
        ]
        for t in temas:
            itens_filial = []
            for cod, nome in NOMES_FILIAIS.items():
                df_f = df_vendas[df_vendas["CodFilial"] == cod]
                v_vendas = df_f["ValorVenda"].sum(); v_trans = df_f["QtdVendas"].sum(); v_itens = df_f["QtdItens"].sum()
                if t["col"] == "ValorVenda": val = v_vendas
                elif t["col"] == "QtdVendas": val = v_trans
                elif t["col"] == "QtdItens": val = v_itens
                elif t["col"] == "Ticket": val = (v_vendas / v_trans if v_trans else 0)
                elif t["col"] == "ItensVenda": val = (v_vendas / v_itens if v_itens else 0)
                elif t["col"] == "ItensTrans": val = (v_itens / v_trans if v_trans else 0)
                h_list = []
                for h in labels_h:
                    df_fh = df_f[df_f["Hora"] == h]
                    h_vendas = df_fh["ValorVenda"].sum(); h_trans = df_fh["QtdVendas"].sum(); h_itens = df_fh["QtdItens"].sum()
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
                h_v = df_h["ValorVenda"].sum(); h_t = df_h["QtdVendas"].sum(); h_i = df_h["QtdItens"].sum()
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
            renderizar_tema("Vendas por Departamento", "📂", dados_d, "ValorVenda", "#0ea5e9", "participacao", "moeda", "departamentos", is_filial=False)

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
            renderizar_tema("Forma de Pagamento", "💳", dados_p, "Valor", "#f97316", "participacao", "moeda", "porForma", is_filial=False)

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
                renderizar_tema("Portador", "👤", dados_pt, "Valor", "#ef4444", "participacao", "moeda", "porPortador", is_filial=False)

# ==========================================
# ABA SAZONALIDADE
# ==========================================
with tab_sazonalidade:
    if "dt_ini_saz" not in st.session_state: st.session_state["dt_ini_saz"] = hoje - timedelta(days=365)
    if "dt_fim_saz" not in st.session_state: st.session_state["dt_fim_saz"] = hoje
    if "h_ini_saz" not in st.session_state: st.session_state["h_ini_saz"] = datetime.strptime("08:00", "%H:%M").time()
    if "h_fim_saz" not in st.session_state: st.session_state["h_fim_saz"] = datetime.strptime("20:59", "%H:%M").time()

    with st.container(border=True):
        c1, c2, c3, c4, c_acoes = st.columns([1, 1, 1, 1, 2.5], vertical_alignment="bottom")
        data_ini_saz = c1.date_input("De:", key="dt_ini_saz", format="DD/MM/YYYY")
        data_fim_saz = c2.date_input("Até:", key="dt_fim_saz", format="DD/MM/YYYY")
        h_ini_saz = c3.time_input("Hora:", key="h_ini_saz")
        h_fim_saz = c4.time_input("Até:", key="h_fim_saz")

        with c_acoes:
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                btn_saz = st.button("🔄 Atualizar", use_container_width=True, type="primary", key="btn_atualizar_saz")
            with col_b2:
                st.button("🧹 Limpar", use_container_width=True, on_click=limpar_sazonalidade, key="btn_limpar_saz")
            with col_b3:
                pdf_bytes_saz = st.session_state.get("pdf_bytes_saz")
                if pdf_bytes_saz:
                    ts = datetime.now(tz_br).strftime("%Y%m%d %H%M%S") if tz_br else datetime.now().strftime("%Y%m%d %H%M%S")
                    st.download_button(label="📄 Gerar PDF", data=pdf_bytes_saz, file_name=f"Acompanhamento Gerencial - Sazonalidade {ts}.pdf", mime="application/pdf", use_container_width=True, key="btn_pdf_saz")
                else:
                    st.button("📄 Gerar PDF", disabled=True, use_container_width=True, key="btn_pdf_saz_disabled")

    _foi_primeira_carga_saz = "df_saz_hist" not in st.session_state
    if _foi_primeira_carga_saz or btn_saz:
        try:
            with st.spinner("Carregando dados de sazonalidade..."):
                df_hist = buscar_sazonalidade("1900-01-01", "2100-12-31", h_ini_saz.hour, h_fim_saz.hour, "")
                df_periodo = buscar_sazonalidade(data_ini_saz.strftime("%Y-%m-%d"), data_fim_saz.strftime("%Y-%m-%d"), h_ini_saz.hour, h_fim_saz.hour, "")

                df_hist_hora = buscar_sazonalidade_hora("1900-01-01", "2100-12-31", h_ini_saz.hour, h_fim_saz.hour, "")
                df_periodo_hora = buscar_sazonalidade_hora(data_ini_saz.strftime("%Y-%m-%d"), data_fim_saz.strftime("%Y-%m-%d"), h_ini_saz.hour, h_fim_saz.hour, "")

                df_hist_diautil = buscar_sazonalidade_diautil("1900-01-01", "2100-12-31", "")
                df_periodo_diautil = buscar_sazonalidade_diautil(data_ini_saz.strftime("%Y-%m-%d"), data_fim_saz.strftime("%Y-%m-%d"), "")

                df_hist_idx = calcular_indices_sazonalidade(df_hist)
                df_periodo_idx = calcular_indices_sazonalidade(df_periodo)
                df_hist_hora_idx = calcular_indices_sazonalidade_hora(df_hist_hora)
                df_periodo_hora_idx = calcular_indices_sazonalidade_hora(df_periodo_hora)
                df_hist_diautil_idx = calcular_indices_sazonalidade_diautil(df_hist_diautil)
                df_periodo_diautil_idx = calcular_indices_sazonalidade_diautil(df_periodo_diautil)

                if not df_hist_idx.empty and not df_periodo_idx.empty:
                    df_comparativo = ((df_periodo_idx / df_hist_idx) - 1) * 100
                    df_comparativo = df_comparativo.replace([float("inf"), -float("inf")], None).round(2)
                else:
                    df_comparativo = pd.DataFrame()

                if not df_hist_hora_idx.empty and not df_periodo_hora_idx.empty:
                    df_comp_hora = ((df_periodo_hora_idx / df_hist_hora_idx) - 1) * 100
                    df_comp_hora = df_comp_hora.replace([float("inf"), -float("inf")], None).round(2)
                else:
                    df_comp_hora = pd.DataFrame()

                if not df_hist_diautil_idx.empty and not df_periodo_diautil_idx.empty:
                    df_comp_diautil = ((df_periodo_diautil_idx / df_hist_diautil_idx) - 1) * 100
                    df_comp_diautil = df_comp_diautil.replace([float("inf"), -float("inf")], None).round(2)
                else:
                    df_comp_diautil = pd.DataFrame()

                st.session_state["df_saz_hist"] = df_hist_idx
                st.session_state["df_saz_periodo"] = df_periodo_idx
                st.session_state["df_saz_comparativo"] = df_comparativo
                st.session_state["df_saz_hist_hora"] = df_hist_hora_idx
                st.session_state["df_saz_periodo_hora"] = df_periodo_hora_idx
                st.session_state["df_saz_comp_hora"] = df_comp_hora
                st.session_state["df_saz_hist_diautil"] = df_hist_diautil_idx
                st.session_state["df_saz_periodo_diautil"] = df_periodo_diautil_idx
                st.session_state["df_saz_comp_diautil"] = df_comp_diautil

                if not df_hist_idx.empty and not df_periodo_idx.empty:
                    st.session_state["pdf_bytes_saz"] = gerar_pdf_sazonalidade(
                        df_hist_idx, df_periodo_idx, df_comparativo, 
                        df_hist_hora_idx, df_periodo_hora_idx, df_comp_hora,
                        df_hist_diautil_idx, df_periodo_diautil_idx, df_comp_diautil,
                        data_ini_saz, data_fim_saz, h_ini_saz, h_fim_saz
                    )
                else:
                    st.session_state["pdf_bytes_saz"] = None
        except Exception as e:
            st.error(f"Erro ao carregar sazonalidade: {e}")
            st.stop()

    if _foi_primeira_carga_saz: st.rerun()

    df_hist_idx = st.session_state.get("df_saz_hist", pd.DataFrame())
    df_periodo_idx = st.session_state.get("df_saz_periodo", pd.DataFrame())
    df_comparativo = st.session_state.get("df_saz_comparativo", pd.DataFrame())
    df_hist_hora_idx = st.session_state.get("df_saz_hist_hora", pd.DataFrame())
    df_periodo_hora_idx = st.session_state.get("df_saz_periodo_hora", pd.DataFrame())
    df_comp_hora = st.session_state.get("df_saz_comp_hora", pd.DataFrame())
    df_hist_diautil_idx = st.session_state.get("df_saz_hist_diautil", pd.DataFrame())
    df_periodo_diautil_idx = st.session_state.get("df_saz_periodo_diautil", pd.DataFrame())
    df_comp_diautil = st.session_state.get("df_saz_comp_diautil", pd.DataFrame())

    if df_hist_idx.empty and df_periodo_idx.empty:
        st.info("Nenhum dado de vendas encontrado.")
    else:
        def _cor_idx(v):
            if pd.isna(v): return ""
            if v > 1.05: return "background-color: #bbf7d0; color: #166534; font-weight: 700;"
            if v > 1.025: return "background-color: #dcfce7; color: #15803d; font-weight: 700;"
            if v >= 0.975: return "background-color: #fef3c7; color: #b45309; font-weight: 700;"
            if v >= 0.95: return "background-color: #fee2e2; color: #b91c1c; font-weight: 700;"
            return "background-color: #fecaca; color: #991b1b; font-weight: 700;"

        def _cor_hora_idx(v):
            if pd.isna(v): return ""
            if v >= 3.00: return "background-color: #bbf7d0; color: #166534; font-weight: 700;"
            if v >= 2.00: return "background-color: #dcfce7; color: #15803d; font-weight: 700;"
            if v >= 1.00: return "background-color: #fef3c7; color: #b45309; font-weight: 700;"
            if v >= 0.95: return "background-color: #fee2e2; color: #b91c1c; font-weight: 700;"
            return "background-color: #fecaca; color: #991b1b; font-weight: 700;"

        def _cor_comp(v):
            if pd.isna(v): return ""
            if v >= 5.0: return "background-color: #bbf7d0; color: #166534; font-weight: 700;"
            if v >= 2.5: return "background-color: #dcfce7; color: #15803d; font-weight: 700;"
            if v > -2.5: return "background-color: #f1f5f9; color: #475569; font-weight: 600;"
            if v > -5.0: return "background-color: #fee2e2; color: #b91c1c; font-weight: 700;"
            return "background-color: #fecaca; color: #991b1b; font-weight: 700;"

        def _render(df_idx, titulo, fmt_func, cor_func):
            st.markdown(f"<div class='tema-titulo'>{titulo}</div>", unsafe_allow_html=True)
            if df_idx.empty:
                st.info("Sem dados para o período.")
                return
            styled = df_idx.style.format(fmt_func).map(cor_func)
            styled = styled.set_properties(**{'text-align': 'right'})
            st.dataframe(styled, use_container_width=True)
            
        def _render_com_pct(df_idx, titulo, cor_func):
            st.markdown(f"<div class='tema-titulo'>{titulo}</div>", unsafe_allow_html=True)
            if df_idx.empty:
                st.info("Sem dados para o período.")
                return
            
            df_display = df_idx.copy()

            def fmt_with_pct(val, total):
                if pd.isna(val) or val == 0: return "-"
                pct = ((val / total) - 1) * 100 if total > 0 else 0
                return f"{val:.4f} ({pct:+.2f}%)".replace(".", ",")

            for col in df_display.columns:
                if col != "Total":
                    df_display[col] = df_display.apply(lambda row: fmt_with_pct(row[col], row["Total"]), axis=1)
                else:
                    df_display[col] = df_display[col].apply(lambda x: f"{x:.4f}".replace(".", ",") if not pd.isna(x) else "-")

            def apply_colors(row):
                return [cor_func(df_idx.loc[row.name, col]) for col in df_idx.columns]

            styled = df_display.style.apply(apply_colors, axis=1)
            styled = styled.set_properties(**{'text-align': 'right'})
            st.dataframe(styled, use_container_width=True)

        # DEFINIÇÃO DAS LEGENDAS HTML
        legenda_dias = '''
        <div class="legenda-container">
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#bbf7d0;"></div> > 1,05 (Melhor)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#dcfce7;"></div> 1,025 a 1,05 (Crescendo)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#fef3c7;"></div> 0,975 a 1,025 (Normal)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#fee2e2;"></div> 0,95 a 0,975 (Regredindo)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#fecaca;"></div> < 0,95 (Pior)</div>
        </div>
        '''
        legenda_horas = '''
        <div class="legenda-container">
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#bbf7d0;"></div> > 3,00 (Melhor)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#dcfce7;"></div> 2,00 a 3,00 (Crescendo)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#fef3c7;"></div> 1,00 a 2,00 (Normal)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#fee2e2;"></div> 0,95 a 1,00 (Regredindo)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#fecaca;"></div> < 0,95 (Pior)</div>
        </div>
        '''
        legenda_comp = '''
        <div class="legenda-container">
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#bbf7d0;"></div> > +5,0% (Melhor)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#dcfce7;"></div> +2,5% a +5,0% (Crescendo)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#f1f5f9;"></div> -2,5% a +2,5% (Normal)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#fee2e2;"></div> -5,0% a -2,5% (Regredindo)</div>
            <div class="legenda-item"><div class="legenda-cor" style="background-color:#fecaca;"></div> < -5,0% (Pior)</div>
        </div>
        '''

        # --- TABELAS DE DIAS DA SEMANA ---
        _render_com_pct(df_hist_idx, "📊 Índice de Sazonalidade (DIAS) — Histórico Completo", _cor_idx)
        st.markdown(legenda_dias, unsafe_allow_html=True)
        
        _render_com_pct(df_periodo_idx, f"📊 Índice de Sazonalidade (DIAS) — Período", _cor_idx)
        st.markdown(legenda_dias, unsafe_allow_html=True)
        
        _render(df_comparativo, "📈 Comparativo (DIAS) — Período vs. Histórico", formatar_variacao_pct, _cor_comp)
        st.markdown(legenda_comp, unsafe_allow_html=True)

        st.markdown("---")

        # --- TABELAS DE HORAS ---
        _render_com_pct(df_hist_hora_idx, "🕒 Índice de Sazonalidade (HORAS) — Histórico Completo", _cor_hora_idx)
        st.markdown(legenda_horas, unsafe_allow_html=True)
        
        _render_com_pct(df_periodo_hora_idx, f"🕒 Índice de Sazonalidade (HORAS) — Período", _cor_hora_idx)
        st.markdown(legenda_horas, unsafe_allow_html=True)
        
        _render(df_comp_hora, "📈 Comparativo (HORAS) — Período vs. Histórico", formatar_variacao_pct, _cor_comp)
        st.markdown(legenda_comp, unsafe_allow_html=True)

        st.markdown("---")

        # --- TABELAS DE DIAS ÚTEIS ---
        _render_com_pct(df_hist_diautil_idx, "📊 Índice de Sazonalidade (DIAS ÚTEIS) — Histórico Completo", _cor_idx)
        st.markdown(legenda_dias, unsafe_allow_html=True)
        
        _render_com_pct(df_periodo_diautil_idx, f"📊 Índice de Sazonalidade (DIAS ÚTEIS) — Período", _cor_idx)
        st.markdown(legenda_dias, unsafe_allow_html=True)
        
        _render(df_comp_diautil, "📈 Comparativo (DIAS ÚTEIS) — Período vs. Histórico", formatar_variacao_pct, _cor_comp)
        st.markdown(legenda_comp, unsafe_allow_html=True)
        
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

    with st.container(border=True):
        c1, c2, c3, c4, c_acoes = st.columns([1, 1, 1.2, 1.5, 2.5], vertical_alignment="bottom")
        data_ini_c = c1.date_input("De:", key="dt_ini_compras", format="DD/MM/YYYY")
        data_fim_c = c2.date_input("Até:", key="dt_fim_compras", format="DD/MM/YYYY")
        filial_c_sel = c3.selectbox("Filial:", ["Todas"] + list(filiais_inv.keys()), key="filial_compras")
        fornecedor_sel = c4.selectbox("Fornecedor:", ["Todos"] + lista_fornecedores, key="fornecedor_compras")

        with c_acoes:
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                btn_compras = st.button("🔄 Atualizar", use_container_width=True, type="primary", key="btn_atualizar_compras")
            with col_b2:
                st.button("🧹 Limpar", use_container_width=True, on_click=limpar_compras, key="btn_limpar_compras")
            with col_b3:
                pdf_bytes_comp = st.session_state.get("pdf_bytes_comp")
                if pdf_bytes_comp:
                    ts = datetime.now(tz_br).strftime("%Y%m%d %H%M%S") if tz_br else datetime.now().strftime("%Y%m%d %H%M%S")
                    st.download_button(label="📄 Gerar PDF", data=pdf_bytes_comp, file_name=f"Acompanhamento Gerencial - Compras {ts}.pdf", mime="application/pdf", use_container_width=True, key="btn_pdf_compras")
                else:
                    st.button("📄 Gerar PDF", disabled=True, use_container_width=True, key="btn_pdf_compras_disabled")

    _foi_primeira_carga_compras = "df_compras" not in st.session_state
    if _foi_primeira_carga_compras or btn_compras:
        filial_cod_c = "" if filial_c_sel == "Todas" else filiais_inv[filial_c_sel]
        try:
            with st.spinner("Carregando dados de compras..."):
                df_compras = buscar_compras(data_ini_c.strftime("%Y-%m-%d"), data_fim_c.strftime("%Y-%m-%d"), filial_cod_c)
                if not df_compras.empty:
                    if fornecedor_sel != "Todos":
                        df_compras = df_compras[df_compras["Fornecedor"] == fornecedor_sel]
                    if not df_compras.empty:
                        df_compras['Mes_Nome'] = df_compras['Mes'].map({1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'})
                        st.session_state["df_compras"] = df_compras
                        st.session_state["pdf_bytes_comp"] = gerar_pdf_compras(df_compras, data_ini_c, data_fim_c)
                    else:
                        st.session_state["df_compras"] = df_compras
                        st.session_state["pdf_bytes_comp"] = None
                else:
                    st.session_state["df_compras"] = df_compras
                    st.session_state["pdf_bytes_comp"] = None
        except Exception as e:
            st.error(f"Erro ao carregar compras: {e}")
            st.stop()

    if _foi_primeira_carga_compras: st.rerun()

    df_compras = st.session_state.get("df_compras", pd.DataFrame())
    if df_compras.empty:
        st.info("Nenhuma compra encontrada para o período/filtros.")
    else:
        tot_val_geral = df_compras["Valor"].sum()
        df_tot_depto = df_compras.groupby("Departamento")["Valor"].sum().reset_index().sort_values("Departamento", ascending=True)
        meses_colunas = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        cards_data = [("💰 Total Comprado", tot_val_geral, "#3b82f6", "")]
        cores_depto = ["#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#0ea5e9", "#f97316", "#ef4444", "#14b8a6"]
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
                    st.markdown(f'<div class="card-item" style="border-left: 5px solid {cor}; background-color: #FFFFFF;"><div class="card-label" style="color: {cor};" title="{nome}">{nome}</div><div class="card-value">{formatar_moeda(valor)} {pct_html}</div></div>', unsafe_allow_html=True)
        st.write("")
        if not df_tot_depto.empty:
            deptos_nomes = df_tot_depto['Departamento'].tolist()
            sub_tabs = st.tabs(deptos_nomes)
            for sub_tab, (_, row) in zip(sub_tabs, df_tot_depto.iterrows()):
                with sub_tab:
                    depto = row['Departamento']
                    df_d = df_compras[df_compras["Departamento"] == depto]
                    df_pivot = df_d.pivot_table(index=['Fornecedor'], columns='Mes_Nome', values='Valor', aggfunc='sum')
                    for m in meses_colunas:
                        if m not in df_pivot.columns: df_pivot[m] = 0.0
                    df_pivot = df_pivot[meses_colunas]
                    df_pivot['Total'] = df_pivot.sum(axis=1)
                    df_pivot = df_pivot.fillna(0).sort_index(ascending=True)
                    linha_total = df_pivot.sum().to_frame().T
                    linha_total.index = ['TOTAL']
                    df_final = pd.concat([df_pivot, linha_total])
                    def fmt_br(x):
                        if pd.isna(x) or x == 0: return "-"
                        return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    def highlight_total(row):
                        if row.name == 'TOTAL': return ['font-weight: bold; color: #2563eb; background-color: #eff6ff;'] * len(row)
                        return [''] * len(row)
                    st.dataframe(df_final.style.format(fmt_br).apply(highlight_total, axis=1), use_container_width=True)

# ==========================================
# ABA TRANSFERÊNCIAS
# ==========================================
with tab_transferencias:
    if "dt_ini_transf" not in st.session_state: st.session_state["dt_ini_transf"] = date(hoje.year, 1, 1)
    if "dt_fim_transf" not in st.session_state: st.session_state["dt_fim_transf"] = date(hoje.year, 12, 31)
    if "filial_origem_transf" not in st.session_state: st.session_state["filial_origem_transf"] = "Todas"

    with st.container(border=True):
        c1, c2, c3, c_acoes = st.columns([1, 1, 1.2, 2.5], vertical_alignment="bottom")
        data_ini_tr = c1.date_input("De:", key="dt_ini_transf", format="DD/MM/YYYY")
        data_fim_tr = c2.date_input("Até:", key="dt_fim_transf", format="DD/MM/YYYY")
        filial_tr_sel = c3.selectbox("Filial:", ["Todas"] + list(filiais_inv.keys()), key="filial_origem_transf")

        with c_acoes:
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                btn_transf = st.button("🔄 Atualizar", use_container_width=True, type="primary", key="btn_atualizar_transf")
            with col_b2:
                st.button("🧹 Limpar", use_container_width=True, on_click=limpar_transferencias, key="btn_limpar_transf")
            with col_b3:
                pdf_bytes_tr = st.session_state.get("pdf_bytes_transf")
                if pdf_bytes_tr:
                    ts = datetime.now(tz_br).strftime("%Y%m%d %H%M%S") if tz_br else datetime.now().strftime("%Y%m%d %H%M%S")
                    st.download_button(label="📄 Gerar PDF", data=pdf_bytes_tr, file_name=f"Acompanhamento Gerencial - Transferencias {ts}.pdf", mime="application/pdf", use_container_width=True, key="btn_pdf_transf")
                else:
                    st.button("📄 Gerar PDF", disabled=True, use_container_width=True, key="btn_pdf_transf_disabled")

    _foi_primeira_carga_transf = "df_transf" not in st.session_state
    if _foi_primeira_carga_transf or btn_transf:
        filial_cod_tr = "" if filial_tr_sel == "Todas" else filiais_inv[filial_tr_sel]
        try:
            with st.spinner("Carregando dados de transferências..."):
                df_transf = buscar_transferencias(data_ini_tr.strftime("%Y-%m-%d"), data_fim_tr.strftime("%Y-%m-%d"), filial_cod_tr)
                if not df_transf.empty:
                    df_transf["FilialOrigem"] = pd.to_numeric(df_transf["FilialOrigem"], errors="coerce").fillna(0).astype(int)
                    df_transf["FilialDestino"] = pd.to_numeric(df_transf["FilialDestino"], errors="coerce").fillna(0).astype(int)
                    df_transf["Mes"] = pd.to_numeric(df_transf["Mes"], errors="coerce").fillna(0).astype(int)
                    df_transf['Mes_Nome'] = df_transf['Mes'].map({1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'})
                    st.session_state["df_transf"] = df_transf
                    st.session_state["pdf_bytes_transf"] = gerar_pdf_transferencias(df_transf, data_ini_tr, data_fim_tr)
                else:
                    st.session_state["df_transf"] = df_transf
                    st.session_state["pdf_bytes_transf"] = None
        except Exception as e:
            st.error(f"Erro ao carregar transferências: {e}")
            st.stop()

    if _foi_primeira_carga_transf: st.rerun()

    df_transf = st.session_state.get("df_transf", pd.DataFrame())
    if df_transf.empty:
        st.info("Nenhuma transferência encontrada para o período/filtros.")
    else:
        df_entradas_all = df_transf[df_transf["TipoDado"] == "ENTRADA"].copy()
        df_saidas_all = df_transf[df_transf["TipoDado"] == "SAIDA"].copy()

        meses_colunas = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

        filiais_card = sorted(set(
            df_entradas_all["FilialDestino"].unique().tolist()
            + df_saidas_all["FilialOrigem"].unique().tolist()
        ))

        def fmt_saldo_card(v):
            if v > 0:
                return f"+ {formatar_moeda(v)}"
            elif v < 0:
                return f"- {formatar_moeda(abs(v))}"
            else:
                return formatar_moeda(0)

        cards_data = []
        for filial in filiais_card:
            ent_v = df_entradas_all[df_entradas_all["FilialDestino"] == filial]["Valor"].sum()
            sai_v = df_saidas_all[df_saidas_all["FilialOrigem"] == filial]["Valor"].sum()
            saldo_v = ent_v - sai_v
            nome = NOMES_FILIAIS.get(int(filial), f"Filial {filial}")
            cor = "#10b981" if saldo_v >= 0 else "#ef4444"
            cards_data.append((f"💰 Saldo {nome}", saldo_v, cor))

        for i in range(0, len(cards_data), 5):
            chunk = cards_data[i:i+5]
            cols = st.columns(5)
            for j, (nome, valor, cor) in enumerate(chunk):
                with cols[j]:
                    st.markdown(f'<div class="card-item" style="border-left: 5px solid {cor}; background-color: #FFFFFF;"><div class="card-label" style="color: {cor};" title="{nome}">{nome}</div><div class="card-value" style="color: {cor};">{fmt_saldo_card(valor)}</div></div>', unsafe_allow_html=True)

        st.write("")

        filiais_envolvidas = sorted(set(
            df_entradas_all["FilialDestino"].unique().tolist()
            + df_saidas_all["FilialOrigem"].unique().tolist()
        ))

        if filiais_envolvidas:
            nomes_tabs = [NOMES_FILIAIS.get(int(f), f"Filial {f}") for f in filiais_envolvidas]
            sub_tabs = st.tabs(nomes_tabs)

            for sub_tab, filial in zip(sub_tabs, filiais_envolvidas):
                with sub_tab:
                    nome_filial = NOMES_FILIAIS.get(int(filial), f"Filial {filial}")

                    st.markdown(f"### 📥 ENTRADAS em {nome_filial}")
                    df_ent = df_entradas_all[df_entradas_all["FilialDestino"] == filial]
                    if df_ent.empty:
                        st.info("Nenhuma entrada no período.")
                    else:
                        df_pivot_e = df_ent.pivot_table(index="FilialOrigem", columns='Mes_Nome', values='Valor', aggfunc='sum')
                        for m in meses_colunas:
                            if m not in df_pivot_e.columns: df_pivot_e[m] = 0.0
                        df_pivot_e = df_pivot_e[meses_colunas]
                        df_pivot_e['Total'] = df_pivot_e.sum(axis=1)
                        df_pivot_e = df_pivot_e.fillna(0).sort_index()
                        linha_total_e = df_pivot_e.sum().to_frame().T
                        linha_total_e.index = ['TOTAL']
                        df_final_e = pd.concat([df_pivot_e, linha_total_e])
                        df_display_e = df_final_e.copy()
                        df_display_e.index = ["TOTAL" if i == "TOTAL" else NOMES_FILIAIS.get(int(i), f"Filial {i}") for i in df_display_e.index]
                        df_display_e.index.name = "Filial Origem"
                        def fmt_br_e(x):
                            if pd.isna(x) or x == 0: return "-"
                            return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        def hl_e(row):
                            if row.name == 'TOTAL': return ['font-weight: bold; color: #2563eb; background-color: #eff6ff;'] * len(row)
                            return [''] * len(row)
                        st.dataframe(df_display_e.style.format(fmt_br_e).apply(hl_e, axis=1), use_container_width=True)

                    st.write("")

                    st.markdown(f"### 📤 SAÍDAS de {nome_filial}")
                    df_sai = df_saidas_all[df_saidas_all["FilialOrigem"] == filial]
                    if df_sai.empty:
                        st.info("Nenhuma saída no período.")
                    else:
                        df_pivot_s = df_sai.pivot_table(index="FilialDestino", columns='Mes_Nome', values='Valor', aggfunc='sum')
                        for m in meses_colunas:
                            if m not in df_pivot_s.columns: df_pivot_s[m] = 0.0
                        df_pivot_s = df_pivot_s[meses_colunas]
                        df_pivot_s['Total'] = df_pivot_s.sum(axis=1)
                        df_pivot_s = df_pivot_s.fillna(0).sort_index()
                        linha_total_s = df_pivot_s.sum().to_frame().T
                        linha_total_s.index = ['TOTAL']
                        df_final_s = pd.concat([df_pivot_s, linha_total_s])
                        df_display_s = df_final_s.copy()
                        df_display_s.index = ["TOTAL" if i == "TOTAL" else NOMES_FILIAIS.get(int(i), f"Filial {i}") for i in df_display_s.index]
                        df_display_s.index.name = "Filial Destino"
                        def fmt_br_s(x):
                            if pd.isna(x) or x == 0: return "-"
                            return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        def hl_s(row):
                            if row.name == 'TOTAL': return ['font-weight: bold; color: #2563eb; background-color: #eff6ff;'] * len(row)
                            return [''] * len(row)
                        st.dataframe(df_display_s.style.format(fmt_br_s).apply(hl_s, axis=1), use_container_width=True)

                    st.write("")

                    st.markdown(f"### 💰 SALDO em {nome_filial} (Entradas − Saídas)")

                    tot_ent_mes = {m: (df_ent[df_ent["Mes_Nome"] == m]["Valor"].sum() if not df_ent.empty else 0.0) for m in meses_colunas}
                    tot_sai_mes = {m: (df_sai[df_sai["Mes_Nome"] == m]["Valor"].sum() if not df_sai.empty else 0.0) for m in meses_colunas}

                    tot_ent_ano = sum(tot_ent_mes.values())
                    tot_sai_ano = sum(tot_sai_mes.values())
                    saldo_ano = tot_ent_ano - tot_sai_ano

                    saldo_dict = {
                        "📥 Total Entradas": {**tot_ent_mes, "Total": tot_ent_ano},
                        "📤 Total Saídas": {**tot_sai_mes, "Total": tot_sai_ano},
                        "💰 Saldo": {**{m: tot_ent_mes[m] - tot_sai_mes[m] for m in meses_colunas}, "Total": saldo_ano},
                    }
                    df_saldo = pd.DataFrame(saldo_dict).T
                    df_saldo = df_saldo[meses_colunas + ["Total"]]
                    df_saldo.index.name = "Descrição"

                    def fmt_br_saldo(x):
                        if pd.isna(x) or x == 0: return "-"
                        return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                    def hl_saldo(row):
                        base = [''] * len(row)
                        if row.name == "💰 Saldo":
                            base = [
                                'font-weight: bold; background: #f0fdf4; color: ' + ('#dc2626' if (isinstance(v, (int, float)) and v < 0) else '#16a34a')
                                for v in row.values
                            ]
                        elif row.name == "📥 Total Entradas":
                            base = ['color: #16a34a; font-weight: 600;'] * len(row)
                        elif row.name == "📤 Total Saídas":
                            base = ['color: #dc2626; font-weight: 600;'] * len(row)
                        return base

                    st.dataframe(
                        df_saldo.style.format(fmt_br_saldo).apply(hl_saldo, axis=1),
                        use_container_width=True
                    )

# ==========================================
# ABA TRIBUTOS
# ==========================================
with tab_tributos:
    if "dt_ini_trib" not in st.session_state: st.session_state["dt_ini_trib"] = hoje.replace(day=1)
    if "dt_fim_trib" not in st.session_state: st.session_state["dt_fim_trib"] = hoje

    with st.container(border=True):
        c1, c2, c_acoes = st.columns([1, 1, 2.5], vertical_alignment="bottom")
        data_ini_t = c1.date_input("De:", key="dt_ini_trib", format="DD/MM/YYYY")
        data_fim_t = c2.date_input("Até:", key="dt_fim_trib", format="DD/MM/YYYY")

        with c_acoes:
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                btn_atualizar_trib = st.button("🔄 Atualizar", use_container_width=True, type="primary", key="btn_atualizar_trib")
            with col_b2:
                st.button("🧹 Limpar", use_container_width=True, on_click=limpar_tributos, key="btn_limpar_trib")
            with col_b3:
                pdf_bytes_t = st.session_state.get("pdf_bytes_trib")
                if pdf_bytes_t:
                    ts = datetime.now(tz_br).strftime("%Y%m%d %H%M%S") if tz_br else datetime.now().strftime("%Y%m%d %H%M%S")
                    st.download_button(label="📄 Gerar PDF", data=pdf_bytes_t, file_name=f"Acompanhamento Gerencial - Tributos {ts}.pdf", mime="application/pdf", use_container_width=True, key="btn_pdf_trib")
                else:
                    st.button("📄 Gerar PDF", disabled=True, use_container_width=True, key="btn_pdf_trib_disabled")

    _foi_primeira_carga_trib = "df_trib" not in st.session_state
    if _foi_primeira_carga_trib or btn_atualizar_trib:
        try:
            with st.spinner("Carregando dados tributários..."):
                df_trib = buscar_tributos(data_ini_t.strftime("%Y-%m-%d"), data_fim_t.strftime("%Y-%m-%d"))
                if not df_trib.empty:
                    df_trib["CodFilial"] = pd.to_numeric(df_trib["CodFilial"], errors="coerce").fillna(0).astype(int)
                    cols_numeric = ["VendasBruto", "VendasLiquidoDesconto", "ICMS_Vendas", "DevolucaoVendas", "TransfEnvTotal", "TransfEnvTrib", "TransfEnvNaoTrib", "ICMS_TransfEnv", "ComprasTotal", "ComprasTrib", "ComprasNaoTrib", "ICMS_Compras", "TransfRecTotal", "TransfRecTrib", "TransfRecNaoTrib", "ICMS_TransfRec", "TributosAntecipados"]
                    for c in cols_numeric:
                        df_trib[c] = pd.to_numeric(df_trib[c], errors="coerce").fillna(0)
                    tem_movimento = ((df_trib["VendasBruto"] > 0) | (df_trib["ComprasTotal"] > 0) | (df_trib["TransfEnvTotal"] > 0) | (df_trib["TransfRecTotal"] > 0) | (df_trib["TributosAntecipados"] != 0))
                    df_trib = df_trib[tem_movimento].copy()
                    if not df_trib.empty:
                        df_trib["vendasLiquido"] = df_trib["VendasLiquidoDesconto"] - df_trib["DevolucaoVendas"]
                        df_trib["tributoVendasIntegral"] = df_trib["ICMS_Vendas"]
                        df_trib["pctVendasEfetivo"] = (df_trib["ICMS_Vendas"] / df_trib["VendasBruto"] * 100).fillna(0)
                        df_trib["tributoVendasAdicional"] = 0.0
                        df_trib["pctAdicional"] = 0.0
                        df_trib["icmsTransfEnv"] = df_trib["ICMS_TransfEnv"]
                        df_trib["pctTransfEnvEfetivo"] = (df_trib["ICMS_TransfEnv"] / df_trib["TransfEnvTotal"] * 100).fillna(0)
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
                            ("Tributo Vendas Integral", "tributoVendasIntegral", {"fmt": lambda v, f: f"{formatar_numero(v)} ({f['pctVendasEfetivo']:.2f}%)"}),
                            ("Tributo Vendas Adicional", "tributoVendasAdicional", {"fmt": lambda v, f: f"{formatar_numero(v)} ({f['pctAdicional']:.2f}%)"}),
                            ("Valor Transferências Enviadas", "TransfEnvTotal", {}),
                            ("Tributo Transferências Enviadas", "icmsTransfEnv", {"fmt": lambda v, f: f"{formatar_numero(v)} ({f['pctTransfEnvEfetivo']:.2f}%)"}),
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
                        rows_resultado = [("Resultado", "resultado", {"bold": True, "cls": "resultado"})]
                        pdf_bytes = gerar_pdf_tributos(colunas, rows_saidas, rows_entradas, rows_resultado, atacado, pb, srb, data_ini_t, data_fim_t)
                        st.session_state["pdf_bytes_trib"] = pdf_bytes
                        st.session_state["df_trib"] = df_trib
                    else:
                        st.session_state["df_trib"] = df_trib
                        st.session_state["pdf_bytes_trib"] = None
                else:
                    st.session_state["df_trib"] = df_trib
                    st.session_state["pdf_bytes_trib"] = None
        except Exception as e:
            st.error(f"Erro ao carregar tributos: {e}")
            st.stop()

    if _foi_primeira_carga_trib: st.rerun()

    df_trib = st.session_state.get("df_trib", pd.DataFrame())
    if df_trib.empty:
        st.info("Nenhum dado encontrado para o período.")
    else:
        atacado = df_trib[df_trib["CodFilial"] == 5]
        pb = df_trib[df_trib["CodFilial"].isin([1, 2, 3])].sort_values("NomeFilial")
        srb = df_trib[df_trib["CodFilial"] == 4]
        colunas = pd.concat([atacado, pb, srb])
        rows_saidas = [
            ("Valor Vendas Bruto", "VendasBruto", {}),
            ("Valor Devolução Vendas", "DevolucaoVendas", {"cls": "devolucao"}),
            ("Valor Vendas Líquido", "vendasLiquido", {"bold": True}),
            ("Tributo Vendas Integral", "tributoVendasIntegral", {"fmt": lambda v, f: f"{formatar_numero(v)} ({f['pctVendasEfetivo']:.2f}%)"}),
            ("Tributo Vendas Adicional", "tributoVendasAdicional", {"fmt": lambda v, f: f"{formatar_numero(v)} ({f['pctAdicional']:.2f}%)"}),
            ("Valor Transferências Enviadas", "TransfEnvTotal", {}),
            ("Tributo Transferências Enviadas", "icmsTransfEnv", {"fmt": lambda v, f: f"{formatar_numero(v)} ({f['pctTransfEnvEfetivo']:.2f}%)"}),
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
        rows_resultado = [("Resultado", "resultado", {"bold": True, "cls": "resultado"})]

        saldo_atacado = atacado["resultado"].sum() if not atacado.empty else 0
        saldo_pb = pb["resultado"].sum() if not pb.empty else 0
        saldo_srb = srb["resultado"].sum() if not srb.empty else 0
        saldo_cons = saldo_atacado + saldo_pb + saldo_srb

        c_cards = st.columns(4)
        def render_card_trib(col, title, val):
            cor = "#16a34a" if val >= 0 else "#dc2626"
            with col:
                st.markdown(f'<div class="card-item" style="border-left: 5px solid {cor}; background-color: #FFFFFF;"><div class="card-label" style="color: {cor}; white-space: normal;">{title}</div><div class="card-value" style="color: {cor};">{formatar_moeda(val)}</div></div>', unsafe_allow_html=True)
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