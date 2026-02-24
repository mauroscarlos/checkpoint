"""
FinFlow — Controle Financeiro Pessoal
Streamlit + Supabase
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime
from zoneinfo import ZoneInfo

import db
import calculos as calc

TZ_BR = ZoneInfo("America/Sao_Paulo")

# ── Página ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="FinFlow", page_icon="💰", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=Figtree:wght@300;400;500;600&display=swap');

html, body, [class*="css"], .stApp { font-family:'Figtree',sans-serif!important; background:#0e0f13!important; color:#e8eaf0!important; }
.stApp, .main .block-container { background:#0e0f13!important; max-width:1200px; }

section[data-testid="stSidebar"] { background:#16181f!important; border-right:1px solid #2a2d3a!important; }
section[data-testid="stSidebar"] * { color:#e8eaf0!important; }
section[data-testid="stSidebar"] label { color:#7a7f96!important; font-size:11px!important; text-transform:uppercase; letter-spacing:1.5px; font-family:'DM Mono',monospace!important; }
section[data-testid="stSidebar"] [data-baseweb="select"]>div, section[data-testid="stSidebar"] input { background:#1e2029!important; border:1px solid #2a2d3a!important; border-radius:8px!important; color:#e8eaf0!important; }

[data-testid="metric-container"] { background:#16181f!important; border:1px solid #2a2d3a!important; border-radius:14px!important; padding:20px!important; border-top:3px solid #c8f564!important; }
[data-testid="metric-container"] label { font-size:11px!important; text-transform:uppercase!important; letter-spacing:1.5px!important; color:#7a7f96!important; font-family:'DM Mono',monospace!important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-family:'DM Mono',monospace!important; font-size:26px!important; }

.stTabs [data-baseweb="tab-list"] { background:#16181f!important; border-radius:12px!important; padding:4px!important; border:1px solid #2a2d3a!important; gap:2px!important; }
.stTabs [data-baseweb="tab"] { background:transparent!important; color:#7a7f96!important; border-radius:9px!important; font-weight:600!important; font-size:14px!important; padding:10px 18px!important; border:none!important; }
.stTabs [aria-selected="true"] { background:rgba(200,245,100,0.12)!important; color:#c8f564!important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none!important; }

.stButton>button, .stFormSubmitButton>button { background:#1e2029!important; color:#e8eaf0!important; border:1px solid #2a2d3a!important; border-radius:10px!important; font-family:'Figtree',sans-serif!important; font-weight:600!important; }
.stButton>button:hover { background:#2a2d3a!important; border-color:#c8f564!important; color:#c8f564!important; }
.stFormSubmitButton>button[kind="primaryFormSubmit"], button[kind="primary"] { background:#c8f564!important; color:#0e0f13!important; border:none!important; }
.stFormSubmitButton>button[kind="primaryFormSubmit"]:hover { background:#d8ff6e!important; }

input, textarea, [data-baseweb="input"] input { background:#1e2029!important; border:1px solid #2a2d3a!important; border-radius:9px!important; color:#e8eaf0!important; font-family:'DM Mono',monospace!important; }
[data-baseweb="input"], [data-baseweb="base-input"] { background:#1e2029!important; border:1px solid #2a2d3a!important; border-radius:9px!important; }
[data-baseweb="select"]>div:first-child { background:#1e2029!important; border:1px solid #2a2d3a!important; border-radius:9px!important; color:#e8eaf0!important; }
[data-baseweb="popover"] ul, [data-baseweb="menu"] { background:#1e2029!important; border:1px solid #2a2d3a!important; border-radius:10px!important; }
[data-baseweb="menu"] li:hover { background:#2a2d3a!important; }
.stTextInput label, .stDateInput label, .stNumberInput label, .stSelectbox label, .stTextArea label { color:#7a7f96!important; font-size:12px!important; }
[data-testid="stForm"] { background:#16181f!important; border:1px solid #2a2d3a!important; border-radius:16px!important; padding:24px!important; }
[data-testid="stDataFrame"] { border-radius:12px!important; border:1px solid #2a2d3a!important; }

div[data-testid="stSuccess"] { background:rgba(200,245,100,0.08)!important; border-left:4px solid #c8f564!important; border-radius:10px!important; color:#c8f564!important; }
div[data-testid="stError"]   { background:rgba(255,107,107,0.08)!important; border-left:4px solid #ff6b6b!important; border-radius:10px!important; }
div[data-testid="stWarning"] { background:rgba(245,166,35,0.08)!important; border-left:4px solid #f5a623!important; border-radius:10px!important; }
div[data-testid="stInfo"]    { background:rgba(106,240,200,0.08)!important; border-left:4px solid #6af0c8!important; border-radius:10px!important; }

[data-testid="stExpander"] { background:#16181f!important; border:1px solid #2a2d3a!important; border-radius:12px!important; }
.stDownloadButton>button { background:#1e2029!important; color:#6af0c8!important; border:1px solid rgba(106,240,200,0.3)!important; border-radius:10px!important; }
hr { border-color:#2a2d3a!important; }
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:#0e0f13; }
::-webkit-scrollbar-thumb { background:#2a2d3a; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding-bottom:24px;border-bottom:1px solid #2a2d3a;margin-bottom:24px">
        <div style="font-family:'DM Serif Display',serif;font-size:28px;color:#c8f564">FinFlow</div>
        <div style="font-family:'DM Mono',monospace;font-size:10px;color:#7a7f96;letter-spacing:2px;text-transform:uppercase;margin-top:2px">Controle Financeiro</div>
    </div>""", unsafe_allow_html=True)

    agora_br = datetime.now(TZ_BR)
    st.markdown(f"""
    <div style="padding:16px;background:#1e2029;border-radius:10px;border:1px solid #2a2d3a;text-align:center;margin-bottom:16px">
        <div style="font-family:'DM Mono',monospace;font-size:26px;color:#c8f564;letter-spacing:2px">{agora_br.strftime('%H:%M')}</div>
        <div style="font-size:11px;color:#7a7f96;margin-top:4px">{agora_br.strftime('%d/%m/%Y')}</div>
    </div>""", unsafe_allow_html=True)

# ── Dados globais ──────────────────────────────────────────────────────────
hoje = datetime.now(TZ_BR).date()
todas_transacoes = db.listar_transacoes()
categorias_df = db.listar_categorias()

# ── Tabs ───────────────────────────────────────────────────────────────────
tab_lanc, tab_manut, tab_hist, tab_rel, tab_cat = st.tabs([
    "💸 Lançar", "✏️ Manutenção", "📋 Histórico", "📊 Relatórios", "🏷️ Categorias"
])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — LANÇAR
# ══════════════════════════════════════════════════════════════════════════
with tab_lanc:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#e8eaf0;margin-bottom:20px">💸 Novo Lançamento</div>', unsafe_allow_html=True)

    # Stats do mês atual
    mes_atual_str = hoje.strftime("%Y-%m")
    df_mes = todas_transacoes[todas_transacoes["data"].astype(str).str[:7] == mes_atual_str] if not todas_transacoes.empty else pd.DataFrame()
    res = calc.resumo_periodo(df_mes)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receitas do mês", calc.fmt_brl(res["receitas"]))
    c2.metric("Despesas do mês", calc.fmt_brl(res["despesas"]))
    saldo = res["saldo"]
    c3.metric("Saldo do mês", calc.fmt_brl(abs(saldo)),
              "positivo" if saldo >= 0 else "negativo",
              delta_color="normal" if saldo >= 0 else "inverse")
    c4.metric("Lançamentos", res["total"])

    st.divider()

    with st.form("form_lancamento", clear_on_submit=True):
        col_tipo, col_data = st.columns([1, 1])
        with col_tipo:
            tipo = st.selectbox("Tipo", options=["despesa", "receita"],
                                format_func=lambda x: "💸 Despesa" if x == "despesa" else "💰 Receita")
        with col_data:
            f_data = st.date_input("Data", value=hoje, format="DD/MM/YYYY")

        col_desc, col_val = st.columns([2, 1])
        with col_desc:
            f_desc = st.text_input("Descrição", placeholder="Ex: Supermercado, Salário...")
        with col_val:
            f_valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01, format="%.2f")

        # Categorias filtradas pelo tipo selecionado
        cats_tipo = categorias_df[categorias_df["tipo"] == tipo] if not categorias_df.empty else pd.DataFrame()
        cat_opcoes = {row["id"]: f"{row['icone']} {row['nome']}" for _, row in cats_tipo.iterrows()}
        cat_ids = list(cat_opcoes.keys())
        cat_labels = list(cat_opcoes.values())
        cat_sel = st.selectbox("Categoria", options=cat_ids,
                               format_func=lambda x: cat_opcoes.get(x, "—")) if cat_ids else None

        f_obs = st.text_input("Observação (opcional)", placeholder="Detalhes adicionais...")

        submitted = st.form_submit_button("✓ Salvar Lançamento", type="primary", use_container_width=True)

    if submitted:
        if not f_desc.strip():
            st.error("Preencha a descrição.")
        elif f_valor <= 0:
            st.error("O valor deve ser maior que zero.")
        else:
            try:
                db.salvar_transacao(
                    data=f_data, descricao=f_desc, valor=f_valor,
                    tipo=tipo, categoria_id=cat_sel, observacao=f_obs
                )
                emoji = "💰" if tipo == "receita" else "💸"
                st.success(f"{emoji} Lançamento salvo! {calc.fmt_brl(f_valor)} em {f_desc}")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — MANUTENÇÃO
# ══════════════════════════════════════════════════════════════════════════
with tab_manut:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#e8eaf0;margin-bottom:4px">✏️ Manutenção</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#7a7f96;font-size:13px;margin-bottom:20px">Edite ou exclua lançamentos existentes.</div>', unsafe_allow_html=True)

    if todas_transacoes.empty:
        st.info("Nenhum lançamento ainda.")
    else:
        # Selectbox com descrição + data
        opcoes_trans = {
            int(row["id"]): f"{row['data']} | {row['categoria_icone']} {row['descricao']} — {calc.fmt_brl(float(row['valor']))}"
            for _, row in todas_transacoes.iterrows()
        }
        trans_sel_id = st.selectbox(
            "Selecione o lançamento",
            options=list(opcoes_trans.keys()),
            format_func=lambda x: opcoes_trans.get(x, str(x))
        )

        reg = db.buscar_transacao(trans_sel_id)

        if reg:
            st.divider()

            def get_cat_idx(cat_id, tipo_reg):
                cats = categorias_df[categorias_df["tipo"] == tipo_reg]
                ids = cats["id"].tolist()
                return ids.index(cat_id) if cat_id in ids else 0

            with st.form("form_manut"):
                mc1, mc2 = st.columns([1, 1])
                with mc1:
                    m_tipo = st.selectbox("Tipo", options=["despesa","receita"],
                        index=0 if reg["tipo"] == "despesa" else 1,
                        format_func=lambda x: "💸 Despesa" if x == "despesa" else "💰 Receita")
                    m_data = st.date_input("Data",
                        value=date.fromisoformat(str(reg["data"])[:10]),
                        format="DD/MM/YYYY")
                with mc2:
                    m_valor = st.number_input("Valor (R$)",
                        value=float(reg["valor"]), min_value=0.01, step=0.01, format="%.2f")
                    cats_m = categorias_df[categorias_df["tipo"] == m_tipo]
                    cat_ids_m = cats_m["id"].tolist()
                    cat_labels_m = {row["id"]: f"{row['icone']} {row['nome']}" for _, row in cats_m.iterrows()}
                    cat_idx = get_cat_idx(reg.get("categoria_id"), m_tipo)
                    m_cat = st.selectbox("Categoria", options=cat_ids_m,
                        index=cat_idx, format_func=lambda x: cat_labels_m.get(x,"—")) if cat_ids_m else None

                m_desc = st.text_input("Descrição", value=reg.get("descricao",""))
                m_obs  = st.text_input("Observação", value=reg.get("observacao","") or "")

                b1, b2 = st.columns([3, 1])
                with b1:
                    salvar = st.form_submit_button("💾 Salvar alterações", type="primary", use_container_width=True)
                with b2:
                    excluir = st.form_submit_button("🗑 Excluir", use_container_width=True)

            if salvar:
                try:
                    db.salvar_transacao(m_data, m_desc, m_valor, m_tipo, m_cat, m_obs, trans_id=trans_sel_id)
                    st.success("✓ Lançamento atualizado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

            if excluir:
                try:
                    db.excluir_transacao(trans_sel_id)
                    st.success("🗑 Lançamento excluído.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    with st.expander("⚠️ Zona de perigo — Excluir todos os lançamentos"):
        st.warning("Esta ação remove **todos** os lançamentos e é irreversível.")
        confirma = st.text_input("Digite CONFIRMAR para prosseguir")
        if st.button("🗑 Excluir tudo", type="primary") and confirma == "CONFIRMAR":
            db.excluir_todas_transacoes()
            st.success("Todos os lançamentos removidos.")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTÓRICO
# ══════════════════════════════════════════════════════════════════════════
with tab_hist:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#e8eaf0;margin-bottom:20px">📋 Histórico</div>', unsafe_allow_html=True)

    # DEBUG temporário
    st.caption(f"🔍 {len(todas_transacoes)} transações | colunas: {todas_transacoes.columns.tolist() if not todas_transacoes.empty else 'vazio'}")

    if todas_transacoes.empty:
        st.info("Nenhum lançamento encontrado.")
    else:
        # Filtros
        fc1, fc2, fc3 = st.columns([2, 1, 1])
        with fc1:
            meses_disp = sorted(todas_transacoes["data"].astype(str).str[:7].unique().tolist(), reverse=True)
            opcoes_mes = ["Todos os meses"] + [calc.mes_label(m) for m in meses_disp]
            label_to_mes = {calc.mes_label(m): m for m in meses_disp}
            mes_atual_label = calc.mes_label(mes_atual_str) if mes_atual_str in meses_disp else opcoes_mes[1] if len(opcoes_mes) > 1 else "Todos os meses"
            idx_mes = opcoes_mes.index(mes_atual_label) if mes_atual_label in opcoes_mes else 0
            filtro_mes_label = st.selectbox("Mês", options=opcoes_mes, index=idx_mes)
            filtro_mes = label_to_mes.get(filtro_mes_label)
        with fc2:
            filtro_tipo = st.selectbox("Tipo", options=["Todos","💰 Receita","💸 Despesa"])
        with fc3:
            filtro_cat = st.selectbox("Categoria", options=["Todas"] + sorted(todas_transacoes["categoria_nome"].unique().tolist()))

        # Aplica filtros
        df_f = todas_transacoes.copy()
        if filtro_mes:
            df_f = df_f[df_f["data"].astype(str).str[:7] == filtro_mes]
        if "Receita" in filtro_tipo:
            df_f = df_f[df_f["tipo"] == "receita"]
        elif "Despesa" in filtro_tipo:
            df_f = df_f[df_f["tipo"] == "despesa"]
        if filtro_cat != "Todas":
            df_f = df_f[df_f["categoria_nome"] == filtro_cat]

        if df_f.empty:
            st.info("Nenhum lançamento para os filtros selecionados.")
        else:
            res_f = calc.resumo_periodo(df_f)
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("Receitas", calc.fmt_brl(res_f["receitas"]))
            rc2.metric("Despesas", calc.fmt_brl(res_f["despesas"]))
            rc3.metric("Saldo", calc.fmt_brl(res_f["saldo"]))

            display = df_f[["data","categoria_icone","categoria_nome","descricao","tipo","valor","observacao"]].copy()
            display["data"] = pd.to_datetime(display["data"].astype(str)).dt.strftime("%d/%m/%Y")
            display["tipo"] = display["tipo"].map({"receita":"💰 Receita","despesa":"💸 Despesa"})
            display["valor"] = display["valor"].apply(lambda v: calc.fmt_brl(float(v)))
            display["categoria"] = display["categoria_icone"] + " " + display["categoria_nome"]
            display = display[["data","tipo","categoria","descricao","valor","observacao"]].fillna("—")
            display.columns = ["Data","Tipo","Categoria","Descrição","Valor","Obs."]

            st.dataframe(display, use_container_width=True, hide_index=True)

            csv = display.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇ Exportar CSV", data=csv,
                file_name=f"finflow_{filtro_mes or 'completo'}.csv", mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════
# TAB 4 — RELATÓRIOS
# ══════════════════════════════════════════════════════════════════════════
with tab_rel:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#e8eaf0;margin-bottom:20px">📊 Relatórios</div>', unsafe_allow_html=True)

    if todas_transacoes.empty:
        st.info("Nenhum dado disponível ainda.")
    else:
        # Filtro de período
        meses_r = sorted(todas_transacoes["data"].astype(str).str[:7].unique().tolist(), reverse=True)
        opcoes_r = ["Todos os meses"] + [calc.mes_label(m) for m in meses_r]
        label_to_mes_r = {calc.mes_label(m): m for m in meses_r}
        idx_r = 1 if len(opcoes_r) > 1 else 0
        filtro_r_label = st.selectbox("Período", options=opcoes_r, index=idx_r, key="rel_mes")
        filtro_r = label_to_mes_r.get(filtro_r_label)

        df_r = todas_transacoes.copy()
        if filtro_r:
            df_r = df_r[df_r["data"].astype(str).str[:7] == filtro_r]

        res_r = calc.resumo_periodo(df_r)

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Receitas", calc.fmt_brl(res_r["receitas"]))
        k2.metric("Total Despesas", calc.fmt_brl(res_r["despesas"]))
        k3.metric("Saldo", calc.fmt_brl(res_r["saldo"]))
        k4.metric("Lançamentos", res_r["total"])

        st.divider()

        col_g1, col_g2 = st.columns(2)

        # Despesas por categoria
        with col_g1:
            st.markdown("**Despesas por categoria**")
            df_cat_desp = calc.resumo_por_categoria(df_r, "despesa")
            if not df_cat_desp.empty:
                fig_pizza = go.Figure(go.Pie(
                    labels=[f"{r['categoria_icone']} {r['categoria_nome']}" for _, r in df_cat_desp.iterrows()],
                    values=df_cat_desp["valor"].tolist(),
                    hole=0.5,
                    marker_colors=["#ff6b6b","#f5a623","#c8a0f5","#6af0c8","#c8f564","#7a7f96",
                                   "#ff9f7f","#ffd700","#87ceeb","#98fb98","#dda0dd","#f08080"],
                    textinfo="percent",
                    hovertemplate="<b>%{label}</b><br>%{value:.2f}<br>%{percent}<extra></extra>",
                ))
                fig_pizza.update_layout(
                    paper_bgcolor="#0e0f13", plot_bgcolor="#0e0f13",
                    font_color="#e8eaf0", height=300,
                    margin=dict(l=0,r=0,t=10,b=0), showlegend=True,
                    legend=dict(bgcolor="#16181f", bordercolor="#2a2d3a", borderwidth=1)
                )
                st.plotly_chart(fig_pizza, use_container_width=True)
            else:
                st.info("Sem despesas no período.")

        # Receitas por categoria
        with col_g2:
            st.markdown("**Receitas por categoria**")
            df_cat_rec = calc.resumo_por_categoria(df_r, "receita")
            if not df_cat_rec.empty:
                fig_rec = go.Figure(go.Pie(
                    labels=[f"{r['categoria_icone']} {r['categoria_nome']}" for _, r in df_cat_rec.iterrows()],
                    values=df_cat_rec["valor"].tolist(),
                    hole=0.5,
                    marker_colors=["#c8f564","#6af0c8","#7a7f96","#f5a623"],
                    textinfo="percent",
                    hovertemplate="<b>%{label}</b><br>%{value:.2f}<br>%{percent}<extra></extra>",
                ))
                fig_rec.update_layout(
                    paper_bgcolor="#0e0f13", plot_bgcolor="#0e0f13",
                    font_color="#e8eaf0", height=300,
                    margin=dict(l=0,r=0,t=10,b=0), showlegend=True,
                    legend=dict(bgcolor="#16181f", bordercolor="#2a2d3a", borderwidth=1)
                )
                st.plotly_chart(fig_rec, use_container_width=True)
            else:
                st.info("Sem receitas no período.")

        st.divider()

        # Evolução mensal (barras)
        st.markdown("**Receitas vs Despesas por mês**")
        df_mensal = calc.resumo_mensal(todas_transacoes)
        if not df_mensal.empty:
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(name="Receitas", x=df_mensal["mes_label"],
                y=df_mensal["receita"], marker_color="#c8f564",
                hovertemplate="<b>%{x}</b><br>Receitas: R$ %{y:,.2f}<extra></extra>"))
            fig_bar.add_trace(go.Bar(name="Despesas", x=df_mensal["mes_label"],
                y=df_mensal["despesa"], marker_color="#ff6b6b",
                hovertemplate="<b>%{x}</b><br>Despesas: R$ %{y:,.2f}<extra></extra>"))
            fig_bar.update_layout(
                barmode="group", paper_bgcolor="#0e0f13", plot_bgcolor="#16181f",
                font_color="#e8eaf0", height=300, margin=dict(l=0,r=0,t=10,b=0),
                xaxis=dict(gridcolor="#2a2d3a"), yaxis=dict(gridcolor="#2a2d3a"),
                legend=dict(bgcolor="#16181f", bordercolor="#2a2d3a", borderwidth=1)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Evolução do saldo acumulado
        st.markdown("**Evolução do saldo acumulado**")
        df_evol = calc.evolucao_saldo(todas_transacoes)
        if not df_evol.empty:
            cores = ["#6af0c8" if v >= 0 else "#ff6b6b" for v in df_evol["saldo_acum"]]
            fig_linha = go.Figure()
            fig_linha.add_trace(go.Scatter(
                x=df_evol["data"].astype(str), y=df_evol["saldo_acum"],
                mode="lines+markers", line=dict(color="#c8f564", width=2),
                marker=dict(color=cores, size=7),
                fill="tozeroy", fillcolor="rgba(200,245,100,0.07)",
                hovertemplate="<b>%{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>",
            ))
            fig_linha.add_hline(y=0, line_color="#7a7f96", line_dash="dash")
            fig_linha.update_layout(
                paper_bgcolor="#0e0f13", plot_bgcolor="#16181f",
                font_color="#e8eaf0", height=280, margin=dict(l=0,r=0,t=10,b=0),
                xaxis=dict(gridcolor="#2a2d3a"), yaxis=dict(gridcolor="#2a2d3a"), showlegend=False
            )
            st.plotly_chart(fig_linha, use_container_width=True)

        st.divider()

        # Tabela por categoria
        st.markdown("**Detalhamento por categoria**")
        df_cat_all = calc.resumo_por_categoria(df_r, "despesa")
        if not df_cat_all.empty:
            df_cat_all["categoria"] = df_cat_all["categoria_icone"] + " " + df_cat_all["categoria_nome"]
            df_cat_all["pct"] = df_cat_all["pct"].apply(lambda x: f"{x}%")
            st.dataframe(
                df_cat_all[["categoria","valor_fmt","pct"]].rename(
                    columns={"categoria":"Categoria","valor_fmt":"Total","pct":"% do total"}),
                use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════
# TAB 5 — CATEGORIAS
# ══════════════════════════════════════════════════════════════════════════
with tab_cat:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#e8eaf0;margin-bottom:20px">🏷️ Gerenciar Categorias</div>', unsafe_allow_html=True)

    col_rec, col_desp = st.columns(2)

    for col, tipo_cat, label in [(col_rec, "receita", "💰 Receitas"), (col_desp, "despesa", "💸 Despesas")]:
        with col:
            st.markdown(f"**{label}**")
            cats = categorias_df[categorias_df["tipo"] == tipo_cat]
            if not cats.empty:
                for _, row in cats.iterrows():
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"{row['icone']} {row['nome']}")
                    if c2.button("🗑", key=f"del_cat_{row['id']}"):
                        try:
                            db.excluir_categoria(int(row["id"]))
                            st.success(f"Categoria '{row['nome']}' removida.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
            else:
                st.info("Nenhuma categoria.")

    st.divider()
    st.markdown("**➕ Nova categoria**")
    with st.form("form_cat"):
        cc1, cc2, cc3, cc4 = st.columns([2, 1, 1, 1])
        with cc1:
            c_nome = st.text_input("Nome")
        with cc2:
            c_tipo = st.selectbox("Tipo", options=["despesa","receita"],
                format_func=lambda x: "💸 Despesa" if x == "despesa" else "💰 Receita")
        with cc3:
            c_icone = st.text_input("Ícone", value="📌", max_chars=2)
        with cc4:
            c_cor = st.color_picker("Cor", value="#7a7f96")
        salvar_cat = st.form_submit_button("✓ Criar categoria", type="primary", use_container_width=True)

    if salvar_cat:
        if not c_nome.strip():
            st.error("Informe o nome da categoria.")
        else:
            try:
                db.salvar_categoria(c_nome, c_tipo, c_icone, c_cor)
                st.success(f"✓ Categoria '{c_nome}' criada!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
