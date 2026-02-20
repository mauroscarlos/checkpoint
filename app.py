"""
PontoFlow — Controle de Ponto com Streamlit + Supabase
Arquivo principal: app.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

TZ_BR = ZoneInfo("America/Sao_Paulo")
import io

import db
import calculos as calc

# ── Configuração da página ─────────────────────────────────────────────────

st.set_page_config(
    page_title="PontoFlow",
    page_icon="⏱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado — dark theme idêntico ao HTML original
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=Figtree:wght@300;400;500;600&display=swap');

/* ── Base ── */
html, body, [class*="css"], .stApp {
    font-family: 'Figtree', sans-serif !important;
    background-color: #0e0f13 !important;
    color: #e8eaf0 !important;
}

/* ── App background ── */
.stApp { background: #0e0f13 !important; }
.main .block-container {
    background: #0e0f13 !important;
    padding-top: 2rem;
    max-width: 1200px;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #16181f !important;
    border-right: 1px solid #2a2d3a !important;
}
section[data-testid="stSidebar"] * { color: #e8eaf0 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stNumberInput label {
    color: #7a7f96 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-family: 'DM Mono', monospace !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] input {
    background: #1e2029 !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
}
/* Logo na sidebar */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2 {
    font-family: 'DM Serif Display', serif !important;
    color: #c8f564 !important;
    font-size: 26px !important;
}

/* ── Métricas / stat cards ── */
[data-testid="metric-container"] {
    background: #16181f !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 14px !important;
    padding: 20px !important;
    border-top: 3px solid #c8f564 !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3) !important;
}
[data-testid="metric-container"] label {
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    color: #7a7f96 !important;
    font-family: 'DM Mono', monospace !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 28px !important;
    color: #e8eaf0 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
    color: #7a7f96 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #16181f !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid #2a2d3a !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #7a7f96 !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 18px !important;
    border: none !important;
    font-family: 'Figtree', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(200,245,100,0.12) !important;
    color: #c8f564 !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── Botões ── */
.stButton > button, .stFormSubmitButton > button {
    background: #1e2029 !important;
    color: #e8eaf0 !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 10px !important;
    font-family: 'Figtree', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: #2a2d3a !important;
    border-color: #c8f564 !important;
    color: #c8f564 !important;
}
/* Botão primário (salvar) */
.stFormSubmitButton > button[kind="primaryFormSubmit"],
button[kind="primary"] {
    background: #c8f564 !important;
    color: #0e0f13 !important;
    border: none !important;
    box-shadow: 0 4px 16px rgba(200,245,100,0.2) !important;
}
.stFormSubmitButton > button[kind="primaryFormSubmit"]:hover,
button[kind="primary"]:hover {
    background: #d8ff6e !important;
    color: #0e0f13 !important;
    box-shadow: 0 6px 20px rgba(200,245,100,0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── Inputs, selects, date, time ── */
input, textarea,
[data-baseweb="input"] input,
[data-baseweb="time-picker"] input,
[data-baseweb="select"] input {
    background: #1e2029 !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 9px !important;
    color: #e8eaf0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 14px !important;
}
[data-baseweb="input"], [data-baseweb="base-input"] {
    background: #1e2029 !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 9px !important;
}
[data-baseweb="select"] > div:first-child {
    background: #1e2029 !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 9px !important;
    color: #e8eaf0 !important;
}
/* Dropdown popup */
[data-baseweb="popover"] ul,
[data-baseweb="menu"] {
    background: #1e2029 !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 10px !important;
}
[data-baseweb="menu"] li:hover { background: #2a2d3a !important; }

/* Labels */
.stTextInput label, .stDateInput label, .stTimeInput label,
.stNumberInput label, .stSelectbox label, .stTextArea label {
    color: #7a7f96 !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    font-family: 'Figtree', sans-serif !important;
}

/* ── Formulário (card branco → dark) ── */
[data-testid="stForm"] {
    background: #16181f !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 16px !important;
    padding: 24px !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #2a2d3a !important;
}
.dvn-scroller { background: #16181f !important; }

/* ── Alerts / mensagens ── */
div[data-testid="stSuccess"] {
    background: rgba(200,245,100,0.08) !important;
    border: 1px solid rgba(200,245,100,0.3) !important;
    border-left: 4px solid #c8f564 !important;
    border-radius: 10px !important;
    color: #c8f564 !important;
}
div[data-testid="stError"] {
    background: rgba(255,107,107,0.08) !important;
    border-left: 4px solid #ff6b6b !important;
    border-radius: 10px !important;
}
div[data-testid="stWarning"] {
    background: rgba(245,166,35,0.08) !important;
    border-left: 4px solid #f5a623 !important;
    border-radius: 10px !important;
}
div[data-testid="stInfo"] {
    background: rgba(106,240,200,0.08) !important;
    border-left: 4px solid #6af0c8 !important;
    border-radius: 10px !important;
    color: #6af0c8 !important;
}

/* ── Dividers ── */
hr { border-color: #2a2d3a !important; }

/* ── Subheaders ── */
h1, h2, h3 { color: #e8eaf0 !important; }
.stSubheader, [data-testid="stSubheader"] {
    font-family: 'DM Serif Display', serif !important;
    font-size: 22px !important;
    color: #e8eaf0 !important;
}

/* ── Caption / small text ── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #7a7f96 !important;
    font-size: 12px !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: #1e2029 !important;
    color: #6af0c8 !important;
    border: 1px solid rgba(106,240,200,0.3) !important;
    border-radius: 10px !important;
}
.stDownloadButton > button:hover {
    background: rgba(106,240,200,0.1) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #16181f !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary { color: #f5a623 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0e0f13; }
::-webkit-scrollbar-thumb { background: #2a2d3a; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3a3d4a; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar — configurações ────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding-bottom:24px; border-bottom:1px solid #2a2d3a; margin-bottom:24px">
        <div style="font-family:'DM Serif Display',serif; font-size:28px; color:#c8f564; letter-spacing:-0.5px">PontoFlow</div>
        <div style="font-family:'DM Mono',monospace; font-size:10px; color:#7a7f96; letter-spacing:2px; text-transform:uppercase; margin-top:2px">Controle de Jornada</div>
    </div>
    """, unsafe_allow_html=True)

    carga_h = st.number_input(
        "Carga horária diária (h)", min_value=1, max_value=24,
        value=st.secrets.get("config", {}).get("carga_horaria_padrao", 8),
        step=1,
    )
    dias_semana = st.selectbox(
        "Dias trabalhados / semana", options=[5, 6],
        index=0,
    )

    st.markdown(f"""
    <div style="margin:16px 0; padding:14px; background:#1e2029; border-radius:10px; border:1px solid #2a2d3a">
        <div style="font-size:10px; color:#7a7f96; font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px">Metas</div>
        <div style="font-family:'DM Mono',monospace; color:#e8eaf0; font-size:13px">Diária: <span style="color:#c8f564">{carga_h}h00</span></div>
        <div style="font-family:'DM Mono',monospace; color:#e8eaf0; font-size:13px; margin-top:4px">Semanal: <span style="color:#c8f564">{carga_h * dias_semana}h00</span></div>
    </div>
    """, unsafe_allow_html=True)

    agora_br = datetime.now(TZ_BR)
    st.markdown(f"""
    <div style="margin-top:16px; padding:16px; background:#1e2029; border-radius:10px; border:1px solid #2a2d3a; text-align:center">
        <div style="font-family:'DM Mono',monospace; font-size:30px; color:#c8f564; letter-spacing:3px">{agora_br.strftime('%H:%M')}</div>
        <div style="font-size:11px; color:#7a7f96; margin-top:4px">{agora_br.strftime('%d/%m/%Y')}</div>
    </div>
    """, unsafe_allow_html=True)

CARGA_MIN = carga_h * 60

# ── Carrega dados uma vez por execução do script, disponível para todas as tabs ──
todos = db.listar_pontos()
todos_enr = calc.enriquecer_df(todos, CARGA_MIN) if not todos.empty else todos
hoje = datetime.now(TZ_BR).date()


# ── Tabs principais ────────────────────────────────────────────────────────

tab_reg, tab_manut, tab_hist, tab_rel, tab_banco = st.tabs([
    "⏱ Registrar",
    "✏️ Manutenção",
    "📋 Histórico",
    "📊 Relatórios",
    "🏦 Banco de Horas",
])


# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — REGISTRAR PONTO
# ══════════════════════════════════════════════════════════════════════════

with tab_reg:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#e8eaf0;margin-bottom:20px">Novo Registro de Ponto</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    # Hoje
    reg_hoje = db.buscar_ponto(hoje)
    trab_hoje = calc.calcular_trabalhado(reg_hoje) if reg_hoje else 0
    col1.metric("Hoje trabalhado", calc.minutes_to_hhmm(trab_hoje or 0), f"meta {carga_h}h")

    # Semana
    inicio_semana = hoje - pd.Timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + pd.Timedelta(days=6)
    if not todos.empty:
        df_sem = todos_enr[
            (pd.to_datetime(todos_enr["data"]).dt.date >= inicio_semana) &
            (pd.to_datetime(todos_enr["data"]).dt.date <= fim_semana)
        ]
        trab_sem = int(df_sem["trabalhado_min"].sum())
    else:
        trab_sem = 0
    col2.metric("Esta semana", calc.minutes_to_hhmm(trab_sem))

    # Banco
    if not todos.empty:
        banco_info = calc.calcular_banco(todos, CARGA_MIN)
        saldo = banco_info["saldo"]
    else:
        saldo = 0
    col3.metric("Banco de horas", calc.minutes_to_hhmm(abs(saldo)),
                "a favor" if saldo >= 0 else "em débito",
                delta_color="normal" if saldo >= 0 else "inverse")
    col4.metric("Dias registrados", len(todos))

    st.divider()

    # Formulário
    with st.form("form_registro", clear_on_submit=True):
        c_data, c_obs = st.columns([1, 2])
        with c_data:
            f_data = st.date_input("📅 Data", value=hoje, format="DD/MM/YYYY")
        with c_obs:
            f_obs = st.text_input("💬 Observação (opcional)", placeholder="Ex: Home office, reunião...")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            f_entrada = st.time_input("🟢 Entrada", value=time(8, 0), step=60)
        with c2:
            f_saida_almoco = st.time_input("🍽️ Saída almoço", value=time(12, 0), step=60)
        with c3:
            f_retorno = st.time_input("↩️ Retorno almoço", value=time(13, 0), step=60)
        with c4:
            f_saida = st.time_input("🔴 Saída", value=time(17, 0), step=60)

        submitted = st.form_submit_button("✓ Salvar Registro", type="primary", use_container_width=True)

    if submitted:
        try:
            db.salvar_ponto(
                data=f_data,
                entrada=f_entrada,
                saida_almoco=f_saida_almoco,
                retorno_almoco=f_retorno,
                saida=f_saida,
                obs=f_obs,
            )
            trab = calc.calcular_trabalhado({
                "entrada": f_entrada, "saida": f_saida,
                "saida_almoco": f_saida_almoco, "retorno_almoco": f_retorno
            })
            diff = trab - CARGA_MIN if trab else None
            diff_str = f" | Diferença: {calc.minutes_to_delta(diff)}" if diff is not None else ""
            st.success(f"✓ Ponto salvo! Trabalhado: {calc.minutes_to_hhmm(trab or 0)}{diff_str}")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")


# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — MANUTENÇÃO
# ══════════════════════════════════════════════════════════════════════════

with tab_manut:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#e8eaf0;margin-bottom:4px">✏️ Manutenção de Registros</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#7a7f96;font-size:13px;margin-bottom:20px">Busque um registro por data para editar ou excluir.</div>', unsafe_allow_html=True)

    # Busca
    col_busca, col_btn = st.columns([2, 1])
    with col_busca:
        data_busca = st.date_input("Selecione a data", value=hoje, format="DD/MM/YYYY", key="manut_data")
    with col_btn:
        st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
        buscar = st.button("🔍 Buscar registro", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Resultado
    reg = db.buscar_ponto(data_busca)

    if buscar or "manut_reg" in st.session_state:
        if buscar:
            st.session_state["manut_reg"] = reg
            st.session_state["manut_data_sel"] = data_busca

        reg = st.session_state.get("manut_reg")
        data_sel = st.session_state.get("manut_data_sel", data_busca)

        if reg is None:
            st.warning(f"Nenhum registro encontrado para {data_sel.strftime('%d/%m/%Y')}.")
            st.info("💡 Você pode criar um novo registro pela aba **⏱ Registrar**.")
        else:
            trab_atual = calc.calcular_trabalhado(reg)
            diff_atual = trab_atual - CARGA_MIN if trab_atual else None

            st.divider()
            # Preview do registro atual
            st.markdown(f"**Registro atual — {data_sel.strftime('%d/%m/%Y')} ({data_sel.strftime('%A')})**")
            cc1, cc2, cc3, cc4 = st.columns(4)
            cc1.metric("Entrada", reg.get("entrada") or "—")
            cc2.metric("Saída almoço", reg.get("saida_almoco") or "—")
            cc3.metric("Retorno", reg.get("retorno_almoco") or "—")
            cc4.metric("Saída", reg.get("saida") or "—")

            if trab_atual is not None:
                st.info(
                    f"⏱ Trabalhado: **{calc.minutes_to_hhmm(trab_atual)}** | "
                    f"Diferença: **{calc.minutes_to_delta(diff_atual)}**"
                )

            st.divider()
            st.markdown("**Editar registro:**")

            def parse_time(val) -> time:
                if not val:
                    return time(0, 0)
                try:
                    h, m = str(val)[:5].split(":")
                    return time(int(h), int(m))
                except Exception:
                    return time(0, 0)

            with st.form("form_manutencao"):
                mc1, mc2 = st.columns(2)
                with mc1:
                    m_entrada = st.time_input("Entrada", value=parse_time(reg.get("entrada")), step=60)
                    m_saida_almoco = st.time_input("Saída almoço", value=parse_time(reg.get("saida_almoco")), step=60)
                with mc2:
                    m_retorno = st.time_input("Retorno almoço", value=parse_time(reg.get("retorno_almoco")), step=60)
                    m_saida = st.time_input("Saída", value=parse_time(reg.get("saida")), step=60)

                m_obs = st.text_input("Observação", value=reg.get("obs") or "")

                # Preview do novo cálculo em tempo real
                novo_trab = calc.calcular_trabalhado({
                    "entrada": m_entrada, "saida": m_saida,
                    "saida_almoco": m_saida_almoco, "retorno_almoco": m_retorno,
                })
                if novo_trab is not None:
                    novo_diff = novo_trab - CARGA_MIN
                    st.caption(
                        f"Pré-visualização → Trabalhado: **{calc.minutes_to_hhmm(novo_trab)}** | "
                        f"Diferença: **{calc.minutes_to_delta(novo_diff)}**"
                    )

                btn_salvar, btn_excluir = st.columns([3, 1])
                with btn_salvar:
                    salvar_edit = st.form_submit_button("💾 Salvar alterações", type="primary", use_container_width=True)
                with btn_excluir:
                    excluir_edit = st.form_submit_button("🗑 Excluir registro", use_container_width=True)

            if salvar_edit:
                try:
                    db.salvar_ponto(
                        data=data_sel,
                        entrada=m_entrada,
                        saida_almoco=m_saida_almoco,
                        retorno_almoco=m_retorno,
                        saida=m_saida,
                        obs=m_obs,
                    )
                    st.success("✓ Registro atualizado com sucesso!")
                    del st.session_state["manut_reg"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

            if excluir_edit:
                try:
                    db.excluir_ponto(reg["id"])
                    st.success("🗑 Registro excluído.")
                    del st.session_state["manut_reg"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")

    # Exclusão em massa (expansível)
    with st.expander("⚠️ Zona de perigo — Excluir todos os registros"):
        st.warning("Esta ação é **irreversível** e remove todos os dados do banco.")
        confirma = st.text_input("Digite CONFIRMAR para prosseguir")
        if st.button("🗑 Excluir tudo", type="primary") and confirma == "CONFIRMAR":
            db.excluir_todos()
            st.success("Todos os registros foram removidos.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTÓRICO
# ══════════════════════════════════════════════════════════════════════════

with tab_hist:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#e8eaf0;margin-bottom:20px">📋 Histórico de Registros</div>', unsafe_allow_html=True)

    if todos.empty:
        st.info("Nenhum registro ainda. Comece registrando seus pontos na aba ⏱ Registrar.")
    else:
        # Filtro de mês
        meses_disp = sorted(set(
            pd.to_datetime(todos["data"]).dt.strftime("%Y-%m").tolist()
        ), reverse=True)

        def fmt_mes_label(m):
            y, mo = m.split("-")
            return pd.Timestamp(year=int(y), month=int(mo), day=1).strftime("%B/%Y").capitalize()

        meses_labels = {m: fmt_mes_label(m) for m in meses_disp}
        mes_atual = hoje.strftime("%Y-%m")
        opcoes = ["Todos os meses"] + [meses_labels[m] for m in meses_disp]
        idx_default = next((i+1 for i, m in enumerate(meses_disp) if m == mes_atual), 0)

        filtro_label = st.selectbox("Filtrar por mês", options=opcoes, index=idx_default)
        label_to_key = {v: k for k, v in meses_labels.items()}
        filtro_mes = label_to_key.get(filtro_label)

        # Filtra o dataframe já carregado (sem nova query ao banco)
        if filtro_mes:
            df_hist = todos[pd.to_datetime(todos["data"]).dt.strftime("%Y-%m") == filtro_mes].copy()
        else:
            df_hist = todos.copy()

        df_hist_enr = calc.enriquecer_df(df_hist, CARGA_MIN) if not df_hist.empty else df_hist

        if df_hist_enr.empty:
            st.info("Nenhum registro encontrado para este período.")
        else:
            display = df_hist_enr[[
                "data", "dia_semana", "entrada", "saida_almoco", "retorno_almoco",
                "saida", "trabalhado_fmt", "diferenca_fmt", "obs"
            ]].copy()
            display["data"] = pd.to_datetime(display["data"]).dt.strftime("%d/%m/%Y")
            display.columns = ["Data", "Dia", "Entrada", "Saída Almoço", "Retorno", "Saída", "Trabalhado", "Diferença", "Obs."]
            display = display.fillna("—")

            st.dataframe(display, use_container_width=True, hide_index=True,
                column_config={
                    "Diferença": st.column_config.TextColumn("Diferença"),
                    "Trabalhado": st.column_config.TextColumn("Trabalhado"),
                })

            csv = display.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇ Exportar CSV", data=csv,
                file_name=f"pontoflow_{filtro_mes or 'completo'}.csv", mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════
# TAB 4 — RELATÓRIOS
# ══════════════════════════════════════════════════════════════════════════

with tab_rel:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#e8eaf0;margin-bottom:20px">📊 Relatórios</div>', unsafe_allow_html=True)

    if todos.empty:
        st.info("Nenhum dado disponível ainda. Comece registrando seus pontos.")
    else:
        # Stats gerais
        banco_info = calc.calcular_banco(todos, CARGA_MIN)
        media_diaria = banco_info["total_trabalhado"] // len(todos) if len(todos) else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total trabalhado", calc.minutes_to_hhmm(banco_info["total_trabalhado"]))
        c2.metric("Horas extras", calc.minutes_to_hhmm(banco_info["total_extras"]))
        c3.metric("Faltas (horas)", calc.minutes_to_hhmm(banco_info["total_faltas"]))
        c4.metric("Média diária", calc.minutes_to_hhmm(media_diaria))

        st.divider()

        # Gráfico semanal
        df_sem = calc.resumo_semanal(todos, CARGA_MIN, dias_semana)
        if not df_sem.empty:
            st.markdown("**Horas por semana**")
            cores = ["#c8f564" if v >= m else "#f5a623" if v >= m * 0.8 else "#ff6b6b"
                     for v, m in zip(df_sem["trabalhado_min"], df_sem["meta"])]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_sem["semana"],
                y=df_sem["trabalhado_min"] / 60,
                marker_color=cores,
                text=df_sem["trabalhado_fmt"],
                textposition="outside",
                hovertemplate="<b>Semana %{x}</b><br>Trabalhado: %{text}<extra></extra>",
            ))
            fig.add_hline(
                y=CARGA_MIN * dias_semana / 60,
                line_dash="dash",
                line_color="#7a7f96",
                annotation_text="Meta semanal",
                annotation_position="top right",
            )
            fig.update_layout(
                paper_bgcolor="#0e0f13",
                plot_bgcolor="#16181f",
                font_color="#e8eaf0",
                showlegend=False,
                height=320,
                margin=dict(l=0, r=0, t=20, b=0),
                yaxis_title="Horas",
                xaxis=dict(gridcolor="#2a2d3a"),
                yaxis=dict(gridcolor="#2a2d3a"),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Tabela mensal
        st.markdown("**Detalhamento por mês**")
        df_mes = calc.resumo_mensal(todos, CARGA_MIN)
        if not df_mes.empty:
            def fmt_mes(m):
                y, mo = m.split("-")
                return pd.Timestamp(year=int(y), month=int(mo), day=1).strftime("%B %Y")

            df_mes_disp = df_mes.copy()
            df_mes_disp["mes"] = df_mes_disp["mes"].apply(fmt_mes)
            df_mes_disp["Total"] = df_mes_disp["total_min"].apply(calc.minutes_to_hhmm)
            df_mes_disp["Meta"] = df_mes_disp["meta_min"].apply(calc.minutes_to_hhmm)
            df_mes_disp["Extras"] = df_mes_disp["extras_min"].apply(lambda x: f"+{calc.minutes_to_hhmm(x)}")
            df_mes_disp["Faltas"] = df_mes_disp["faltas_min"].apply(lambda x: f"-{calc.minutes_to_hhmm(x)}")
            df_mes_disp["Saldo"] = df_mes_disp["saldo_min"].apply(calc.minutes_to_delta)

            st.dataframe(
                df_mes_disp[["mes", "dias", "Total", "Meta", "Extras", "Faltas", "Saldo"]].rename(
                    columns={"mes": "Mês", "dias": "Dias"}
                ),
                use_container_width=True,
                hide_index=True,
            )


# ══════════════════════════════════════════════════════════════════════════
# TAB 5 — BANCO DE HORAS
# ══════════════════════════════════════════════════════════════════════════

with tab_banco:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#e8eaf0;margin-bottom:20px">🏦 Banco de Horas</div>', unsafe_allow_html=True)

    if todos.empty:
        st.info("Nenhum dado disponível ainda.")
    else:
        banco_info = calc.calcular_banco(todos, CARGA_MIN)

        # Cards
        c1, c2, c3 = st.columns(3)
        c1.metric("Horas creditadas", calc.minutes_to_hhmm(banco_info["total_extras"]), "horas extras trabalhadas")
        c2.metric("Horas debitadas", calc.minutes_to_hhmm(banco_info["total_faltas"]), "horas em falta")
        saldo = banco_info["saldo"]
        c3.metric(
            "Saldo atual",
            calc.minutes_to_hhmm(abs(saldo)),
            "a favor" if saldo >= 0 else "em débito",
            delta_color="normal" if saldo >= 0 else "inverse",
        )

        st.divider()

        # Gráfico de saldo acumulado
        df_acum = banco_info["df_acumulado"]
        if not df_acum.empty:
            st.markdown("**Evolução do saldo acumulado**")
            cores_linha = ["#6af0c8" if v >= 0 else "#ff6b6b" for v in df_acum["saldo_acum"]]
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=pd.to_datetime(df_acum["data"]).dt.strftime("%d/%m"),
                y=df_acum["saldo_acum"] / 60,
                mode="lines+markers",
                line=dict(color="#c8f564", width=2),
                marker=dict(color=cores_linha, size=8),
                fill="tozeroy",
                fillcolor="rgba(200,245,100,0.08)",
                hovertemplate="<b>%{x}</b><br>Saldo: %{y:.1f}h<extra></extra>",
            ))
            fig2.add_hline(y=0, line_color="#7a7f96", line_dash="dash")
            fig2.update_layout(
                paper_bgcolor="#0e0f13",
                plot_bgcolor="#16181f",
                font_color="#e8eaf0",
                height=280,
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis_title="Horas",
                xaxis=dict(gridcolor="#2a2d3a"),
                yaxis=dict(gridcolor="#2a2d3a"),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.divider()

        # Tabela detalhada
        st.markdown("**Movimentações dia a dia**")
        df_tab = df_acum.copy()
        df_tab["data_fmt"] = pd.to_datetime(df_tab["data"]).dt.strftime("%d/%m/%Y")
        df_tab["Trabalhado"] = df_tab["trabalhado_min"].apply(calc.minutes_to_hhmm)
        df_tab["Meta"] = calc.minutes_to_hhmm(CARGA_MIN)
        df_tab["Diferença"] = df_tab["diferenca_min"].apply(calc.minutes_to_delta)
        df_tab["Saldo Acum."] = df_tab["saldo_acum"].apply(calc.minutes_to_delta)

        st.dataframe(
            df_tab[["data_fmt", "Trabalhado", "Meta", "Diferença", "Saldo Acum."]].rename(
                columns={"data_fmt": "Data"}
            ).sort_values("Data", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
