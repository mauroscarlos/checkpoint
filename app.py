import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date, time
import calendar
import pytz

# 1. Conexão Segura
URL = "https://iorjkyxjjogqtjdlmyhv.supabase.co"
KEY = "sb_publishable_M1aCKJu_pYJaFLgPP7Nlqw_C9qXfI6L"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="MSCGYM - Gestão de Ponto", layout="wide")
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- CSS PARA MENU ESTILIZADO (SEM BOLINHAS) ---
st.markdown("""
<style>
    div[role="radiogroup"] span[data-baseweb="radio"] { display: none !important; }
    div[role="radiogroup"] label {
        background-color: #f1f3f5 !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        margin-bottom: 8px !important;
        border: 1px solid #d1d3d4 !important;
        display: block !important;
        width: 100% !important;
        cursor: pointer !important;
    }
    div[role="radiogroup"] input:checked + label {
        background-color: #007BFF !important;
        color: white !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Funções de Apoio ---
def calcular_total_horas(row):
    try:
        def to_float(t_str):
            h, m = map(int, str(t_str).split(':'))
            return h + m/60
        t1 = to_float(row['Entrada'])
        t2 = to_float(row['S.Almoco'])
        t3 = to_float(row['R.Almoco'])
        t4 = to_float(row['Saida'])
        return round((t2 - t1) + (t4 - t3), 2)
    except: return 0.0

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_logado = None

if not st.session_state.autenticado:
    st.title("🔐 MSCGYM - Login")
    res_f = supabase.table("funcionarios").select("*").execute()
    lista_u = [f['nome'] for f in res_f.data] if res_f.data else []
    with st.form("login"):
        user = st.selectbox("Usuário", lista_u)
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            dados = next((f for f in res_f.data if f['nome'] == user), None)
            if dados and str(dados.get('senha')) == senha:
                st.session_state.autenticado = True
                st.session_state.usuario_logado = dados
                st.rerun()
            else: st.error("Acesso Negado")
    st.stop()

u = st.session_state.usuario_logado
eh_admin = u.get('perfil') == 'admin'

with st.sidebar:
    st.title("🚀 MSCGYM")
    pagina = st.radio("Navegação", ["🏠 Bater Ponto", "📅 Folha (Excel)", "👤 Cadastro"])
    if eh_admin:
        st.divider()
        hj = datetime.now(fuso_br)
        mes_sel = st.selectbox("Mês", list(range(1, 13)), index=hj.month - 1)
        ano_sel = st.number_input("Ano", value=hj.year)
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

# --- PÁGINA: FOLHA ESTILO EXCEL ---
if pagina == "📅 Folha (Excel)" and eh_admin:
    st.subheader(f"📊 Planilha de Ajustes - {mes_sel:02d}/{ano_sel}")
    
    res_func = supabase.table("funcionarios").select("nome").execute()
    alvo = st.selectbox("Selecione o Funcionário", [f['nome'] for f in res_func.data])

    # 1. Montar estrutura do mês
    num_dias = calendar.monthrange(int(ano_sel), mes_sel)[1]
    df_vazio = pd.DataFrame({
        "Data": [date(int(ano_sel), mes_sel, d) for d in range(1, num_dias + 1)],
        "Entrada": ["08:00"] * num_dias,
        "S.Almoco": ["12:00"] * num_dias,
        "R.Almoco": ["13:00"] * num_dias,
        "Saida": ["17:00"] * num_dias
    })

    # 2. Carregar dados reais
    res_p = supabase.table("registros_ponto").select("*").eq("usuario", alvo).execute()
    if res_p.data:
        for r in res_p.data:
            dt_r = datetime.strptime(r['data'], '%Y-%m-%d').date()
            idx = df_vazio.index[df_vazio['Data'] == dt_r]
            if not idx.empty:
                df_vazio.loc[idx, "Entrada"] = str(r.get('entrada'))[:5]
                df_vazio.loc[idx, "S.Almoco"] = str(r.get('saida_almoco'))[:5]
                df_vazio.loc[idx, "R.Almoco"] = str(r.get('retorno_almoco'))[:5]
                df_vazio.loc[idx, "Saida"] = str(r.get('saida'))[:5]

    st.info("💡 Você pode digitar os horários diretamente nas células como no Excel.")
    
    # 3. O EDITOR ESTILO EXCEL
    df_editado = st.data_editor(
        df_vazio,
        column_config={
            "Data": st.column_config.DateColumn("Dia", disabled=True, format="DD/MM/YYYY"),
            "Entrada": st.column_config.TextColumn("Entrada", help="Formato HH:MM"),
            "S.Almoco": st.column_config.TextColumn("Saída Almoço"),
            "R.Almoco": st.column_config.TextColumn("Retorno Almoço"),
            "Saida": st.column_config.TextColumn("Saída Final"),
        },
        hide_index=True,
        use_container_width=True
    )

    if st.button("💾 SALVAR TODA A PLANILHA", use_container_width=True, type="primary"):
        with st.spinner("Atualizando registros..."):
            for _, row in df_editado.iterrows():
                total = calcular_total_horas(row)
                payload = {
                    "usuario": alvo, "data": str(row['Data']),
                    "entrada": row['Entrada'], "saida_almoco": row['S.Almoco'],
                    "retorno_almoco": row['R.Almoco'], "saida": row['Saida'],
                    "horas_trabalhadas": total, "horas_extras": round(total - 8.0, 2)
                }
                # Upsert (Insere se não existe, atualiza se existe)
                supabase.table("registros_ponto").upsert(payload, on_conflict="usuario,data").execute()
            st.success("Planilha atualizada com sucesso!")

# --- PÁGINA: BATER PONTO (SIMPLIFICADA) ---
elif pagina == "🏠 Bater Ponto":
    st.subheader("⌚ Ponto em Tempo Real")
    agora = datetime.now(fuso_br)
    st.write(f"### {agora.strftime('%H:%M:%S')}")
    if st.button("REGISTRAR AGORA", use_container_width=True):
        # Lógica de inserção simples aqui...
        st.balloons()

# --- PÁGINA: CADASTRO ---
elif pagina == "👤 Cadastro":
    st.write("Configurações de usuários aqui.")
