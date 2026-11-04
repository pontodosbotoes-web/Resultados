import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
from zoneinfo import ZoneInfo

from src.db import carregar_filiais
from src.base import buscar_visao_geral, buscar_compras

st.set_page_config(page_title="Acompanhamento Gerencial", layout="wide", page_icon="📊")

# CSS customizado para deixar idêntico à imagem
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 100% !important; }
        
        .titulo-pagina { font-size: 1.8rem; font-weight: 700; text-align: center; color: #FAFAFA; margin-bottom: 20px; }
        
        /* Card KPI Customizado */
        .kpi-title { font-size: 0.85rem; color: #94A3B8; margin-bottom: 5px; font-weight: 600; text-transform: uppercase;}
        .kpi-value { font-size: 1.4rem; font-weight: bold; color: #F8FAFC; margin-bottom: 0px; }
        .kpi-pct { font-size: 0.8rem; font-weight: bold; margin-left: 5px; }
        .pct-green { color: #10B981; }
        .pct-red { color: #EF4444; }
        .pct-orange { color: #F59E0B; }
        
        .kpi-card { background-color: #1E293B; border-radius: 8px; padding: 12px; border: 1px solid #334155; height: 100%; }
        .kpi-card-consolidado { border: 2px solid #3B82F6 !important; background-color: #172033; }
    </style>
""", unsafe_allow_html=True)

filiais_dict = carregar_filiais()
filiais_inv = {v: k for k, v in filiais_dict.items()}
NOMES_FILIAIS = {1: "PB - ALECRIM", 2: "PB - VIA DIRETA", 3: "PB - ZONA SUL", 4: "SRB - ZONA NORTE", 5: "PB - ATACADO"}

st.markdown('<div class="titulo-pagina">📊 Acompanhamento Gerencial</div>', unsafe_allow_html=True)

# Abas
tab_visao, tab_compras = st.tabs(["📊 Visão Geral", "🛒 Compras"])

with tab_visao:
    # Correção de Fuso Horário (Brasil)
    try:
        tz_br = ZoneInfo("America/Sao_Paulo")
    except:
        tz_br = None
    hoje = datetime.now(tz_br).date() if tz_br else date.today()

    # Filtros
    c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1.5, 1])
    
    data_ini = c1.date_input("De:", value=hoje, format="DD/MM/YYYY")
    data_fim = c2.date_input("Até:", value=hoje, format="DD/MM/YYYY")
    h_ini = c3.time_input("Hora:", value=datetime.strptime("00:00", "%H:%M").time())
    h_fim = c4.time_input("Até:", value=datetime.strptime("23:59", "%H:%M").time())
    filial_sel = c5.selectbox("Filial:", ["Todas"] + list(filiais_inv.keys()))
    
    # Coloca o botão no final
    with c6:
        st.write("") # Pula uma linha para alinhar
        btn_atualizar = st.button("🔄 Atualizar", use_container_width=True, type="primary")

    filial_cod = "" if filial_sel == "Todas" else filiais_inv[filial_sel]
    h_ini_int = h_ini.hour
    h_fim_int = h_fim.hour
    
    df = buscar_visao_geral(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), h_ini_int, h_fim_int, filial_cod)
    
    if df.empty:
        st.info(f"Nenhuma venda encontrada no período de {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}.")
    else:
        # Agregação global
        tot_vendas = df["ValorVenda"].sum()
        tot_trans = df["QtdVendas"].sum()
        ticket_medio = tot_vendas / tot_trans if tot_trans > 0 else 0

        def render_linha_kpi(titulo, icone, col_valor, formato_moeda=True, is_pct_share=True, is_ticket=False):
            st.markdown(f"### {icone} {titulo}")
            cols = st.columns([1, 1, 1, 1, 1]) # 5 colunas iguais
            
            def mini_grafico(df_filtro, cor):
                if df_filtro.empty: return go.Figure()
                fig = px.area(df_filtro, x="Hora", y=col_valor)
                fig.update_traces(line_color=cor, fillcolor=cor.replace('rgb','rgba').replace(')', ', 0.2)'), line_width=2)
                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=50, xaxis=dict(visible=False), yaxis=dict(visible=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                return fig

            # Card Consolidado
            with cols[0]:
                val_total = df[col_valor].sum() if not is_ticket else ticket_medio
                with st.container():
                    st.markdown(f'<div class="kpi-card kpi-card-consolidado"><div class="kpi-title">🏆 Consolidado</div><div class="kpi-value">{"R$ " if formato_moeda else ""}{val_total:,.2f}</div></div>', unsafe_allow_html=True)
                    df_h = df.groupby("Hora")[col_valor].sum().reset_index()
                    fig = mini_grafico(df_h, "rgb(96, 165, 250)")
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"chart_cons_{titulo}")

            # Cards por Filial
            for i, (cod, nome) in enumerate(NOMES_FILIAIS.items()):
                if i + 1 >= len(cols): break
                df_f = df[df["CodFilial"] == cod]
                val_f = df_f[col_valor].sum() if not is_ticket else (df_f["ValorVenda"].sum() / df_f["QtdVendas"].sum() if df_f["QtdVendas"].sum() else 0)
                
                with cols[i + 1]:
                    with st.container():
                        if is_ticket:
                            var_pct = ((val_f - ticket_medio) / ticket_medio * 100) if ticket_medio else 0
                            cor_pct = "pct-green" if var_pct >= 0 else "pct-red"
                            sinal = "+" if var_pct >= 0 else ""
                            pct_html = f'<span class="kpi-pct {cor_pct}">({sinal}{var_pct:.1f}%)</span>'
                        else:
                            share_pct = (val_f / val_total * 100) if val_total else 0
                            pct_html = f'<span class="kpi-pct pct-orange">({share_pct:.1f}%)</span>'

                        st.markdown(f'<div class="kpi-card"><div class="kpi-title">{nome}</div><div class="kpi-value">{"R$ " if formato_moeda else ""}{val_f:,.2f} {pct_html}</div></div>', unsafe_allow_html=True)
                        
                        df_fh = df_f.groupby("Hora")[col_valor].sum().reset_index()
                        fig_f = mini_grafico(df_fh, "rgb(96, 165, 250)" if not is_ticket else "rgb(245, 158, 11)")
                        st.plotly_chart(fig_f, use_container_width=True, config={'displayModeBar': False}, key=f"chart_{nome}_{titulo}")
            st.write("") 

        # Renderiza os Blocos
        render_linha_kpi("Vendas", "🍞", "ValorVenda")
        render_linha_kpi("Transações", "🛒", "QtdVendas", formato_moeda=False)
        render_linha_kpi("Ticket Médio", "🎫", "ValorVenda", is_ticket=True)

with tab_compras:
    st.write("Em breve: Detalhamento de compras")