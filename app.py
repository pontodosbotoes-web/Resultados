import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
from zoneinfo import ZoneInfo

from src.db import carregar_filiais
from src.base import buscar_vendas, buscar_departamentos, buscar_pagamentos, buscar_compras

st.set_page_config(page_title="Acompanhamento Gerencial", layout="wide", page_icon="📊")

# CSS Customizado
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 100% !important; background-color: #0d1117; }
        
        .titulo-pagina { font-size: 24px; font-weight: 700; text-align: center; color: #f0f6fc; padding-bottom: 15px; border-bottom: 2px solid #30363d; margin-bottom: 20px; }
        
        .tema-titulo { font-size: 20px; font-weight: 700; color: #f0f6fc; margin-top: 20px; margin-bottom: 12px; border-bottom: 2px solid #30363d; padding-bottom: 6px; }
        
        .card-item { border-radius: 10px; padding: 12px 14px 6px 14px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; transition: 0.2s; margin-bottom: 10px;}
        .card-item:hover { filter: brightness(1.2); }
        
        .card-label { font-size: 13px; font-weight: 600; color: #c9d1d9; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
        .card-value { font-size: 20px; font-weight: 700; color: #f0f6fc; }
        
        .pct-participacao { font-size: 13px; font-weight: 600; color: #f6ad55; margin-left: 5px; }
        .pct-positiva { font-size: 13px; font-weight: 600; color: #3fb950; margin-left: 5px; }
        .pct-negativa { font-size: 13px; font-weight: 600; color: #f85149; margin-left: 5px; }
        
        .depto-header { font-size: 18px; font-weight: 600; color: #f0f6fc; margin-top: 25px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;}
        .depto-valor { font-size: 16px; color: #58a6ff; font-weight: 700; background: rgba(88,166,255,0.1); padding: 2px 10px; border-radius: 15px;}
    </style>
""", unsafe_allow_html=True)

filiais_dict = carregar_filiais()
filiais_inv = {v: k for k, v in filiais_dict.items()}
NOMES_FILIAIS = {1: "PB - ALECRIM", 2: "PB - VIA DIRETA", 3: "PB - ZONA SUL", 4: "SRB - ZONA NORTE", 5: "PB - ATACADO"}

st.markdown('<div class="titulo-pagina">📊 Acompanhamento Gerencial</div>', unsafe_allow_html=True)

tab_visao, tab_compras = st.tabs(["📊 Visão Geral", "🛒 Compras"])

def formatar_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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


with tab_visao:
    try:
        tz_br = ZoneInfo("America/Sao_Paulo")
    except:
        tz_br = None
    hoje = datetime.now(tz_br).date() if tz_br else date.today()

    with st.form(key="form_filtros"):
        c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1.5, 1], vertical_alignment="bottom")
        
        data_ini = c1.date_input("De:", value=hoje, format="DD/MM/YYYY")
        data_fim = c2.date_input("Até:", value=hoje, format="DD/MM/YYYY")
        h_ini = c3.time_input("Hora:", value=datetime.strptime("00:00", "%H:%M").time())
        h_fim = c4.time_input("Até:", value=datetime.strptime("23:59", "%H:%M").time())
        filial_sel = c5.selectbox("Filial:", ["Todas"] + list(filiais_inv.keys()))
        
        with c6:
            btn = st.form_submit_button("🔄 Atualizar", use_container_width=True, type="primary")

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
# ABA COMPRAS (AGRUPADA POR DEPARTAMENTO)
# ==========================================
with tab_compras:
    with st.form(key="form_compras"):
        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1], vertical_alignment="bottom")
        
        data_ini_c = c1.date_input("De:", value=date(hoje.year, 1, 1), format="DD/MM/YYYY", key="dt_ini_compras")
        data_fim_c = c2.date_input("Até:", value=date(hoje.year, 12, 31), format="DD/MM/YYYY", key="dt_fim_compras")
        filial_c_sel = c3.selectbox("Filial:", ["Todas"] + list(filiais_inv.keys()), key="filial_compras")
        
        with c4:
            btn_compras = st.form_submit_button("🔄 Atualizar", use_container_width=True, type="primary")

    filial_cod_c = "" if filial_c_sel == "Todas" else filiais_inv[filial_c_sel]
    
    with st.spinner("Carregando dados de compras..."):
        df_compras = buscar_compras(data_ini_c.strftime("%Y-%m-%d"), data_fim_c.strftime("%Y-%m-%d"), filial_cod_c)
    
    if df_compras.empty:
        st.info("Nenhuma compra encontrada para o período.")
    else:
        # --- PREPARAÇÃO DOS TOTAIS E MESES ---
        tot_val_geral = df_compras["Valor"].sum()
        df_tot_depto = df_compras.groupby("Departamento")["Valor"].sum().reset_index().sort_values("Valor", ascending=False)
        
        meses_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
        df_compras['Mes_Nome'] = df_compras['Mes'].map(meses_map)
        meses_colunas = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

        # --- CARDS NO TOPO (TOTAL E DEPARTAMENTOS) ---
        cards_data = [("💰 Total Comprado", tot_val_geral, "#58a6ff")]
        cores_depto = ["#3fb950", "#d29922", "#9f7aea", "#f687b3", "#38bdf8", "#f0883e", "#f97583", "#4fd1c5"]
        
        for i, row in df_tot_depto.iterrows():
            cor = cores_depto[i % len(cores_depto)]
            cards_data.append((f"📂 {row['Departamento']}", row["Valor"], cor))

        for i in range(0, len(cards_data), 5):
            chunk = cards_data[i:i+5]
            cols = st.columns(5)
            for j, (nome, valor, cor) in enumerate(chunk):
                with cols[j]:
                    r = int(cor[1:3], 16); g = int(cor[3:5], 16); b = int(cor[5:7], 16)
                    bg_color = f"rgba({r}, {g}, {b}, 0.08)"
                    st.markdown(f'''
                        <div class="card-item" style="background-color: {bg_color}; border: 1px solid {cor}; border-left: 4px solid {cor};">
                            <div class="card-label" style="color: {cor};" title="{nome}">{nome}</div>
                            <div class="card-value" style="color: {cor};">{formatar_moeda(valor)}</div>
                        </div>
                    ''', unsafe_allow_html=True)
        
        st.write("")
        st.markdown("---")

        # --- TABELAS SEPARADAS POR DEPARTAMENTO ---
        st.markdown("### 📋 Detalhamento por Departamento")
        
        for _, row in df_tot_depto.iterrows():
            depto = row['Departamento']
            val_depto = row['Valor']
            
            # Título do Departamento com Valor
            st.markdown(f'''
                <div class="depto-header">
                    📂 {depto} <span class="depto-valor">{formatar_moeda(val_depto)}</span>
                </div>
            ''', unsafe_allow_html=True)
            
            df_d = df_compras[df_compras["Departamento"] == depto]
            
            # Pivot: Fornecedores nas linhas, Meses nas colunas, Valor total
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
            df_pivot = df_pivot.fillna(0).sort_values(by='Total', ascending=False)
            
            # Formatação das colunas para Moeda
            col_config = {m: st.column_config.NumberColumn(m, format="R$ %.2f") for m in meses_colunas}
            col_config["Total"] = st.column_config.NumberColumn("Total", format="R$ %.2f")
            
            st.dataframe(df_pivot, use_container_width=True, column_config=col_config)
            st.write("") # Espaçamento entre as tabelas