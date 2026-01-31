import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import calendar
import pytz
from fpdf import FPDF

# 1. Conexão Segura
URL = "https://iorjkyxjjogqtjdlmyhv.supabase.co"
KEY = "sb_publishable_M1aCKJu_pYJaFLgPP7Nlqw_C9qXfI6L"

supabase = create_client(URL, KEY)

st.set_page_config(page_title="MSCGYM - Gestão de Ponto", layout="wide")
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- Funções de Apoio ---
def calcular_horas(e, s_a, r_a, s):
    try:
        t1 = e.hour + e.minute/60
        t2 = s_a.hour + s_a.minute/60
        t3 = r_a.hour + r_a.minute/60
        t4 = s.hour + s.minute/60
        return round((t2 - t1) + (t4 - t3), 2)
    except: return 0.0

def gerar_pdf_folha(funcionario_info, df_mes, mes_ano):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "MSCGYM - CONTROLE DE PONTO", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f" Funcionário: {funcionario_info['nome']}", ln=True, fill=True)
    pdf.ln(5)
    return pdf.output()

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_logado = None

if not st.session_state.autenticado:
    st.title("🔐 MSCGYM - Login")
    try:
        res_f = supabase.table("funcionarios").select("*").execute()
        lista_u = [f['nome'] for f in res_f.data] if res_f.data else []
        with st.form("login_form"):
            user = st.selectbox("Selecione seu nome", lista_u)
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                dados_u = next((f for f in res_f.data if f['nome'] == user), None)
                if dados_u and str(dados_u.get('senha')) == senha:
                    st.session_state.autenticado = True
                    st.session_state.usuario_logado = dados_u
                    st.rerun()
                else: st.error("Senha incorreta!")
    except: st.error("Erro ao conectar ao banco.")
    st.stop()

# --- SE CHEGOU AQUI, ESTÁ LOGADO ---
u_logado = st.session_state.usuario_logado
eh_admin = u_logado.get('perfil') == 'admin'

# --- MENU LATERAL ---
with st.sidebar:
    st.title("🚀 MSCGYM")
    st.write(f"Usuário: **{u_logado['nome']}**")
    
    opcoes = ["Bater Ponto"]
    if eh_admin:
        opcoes += ["Folha de Ponto", "Manutenção de Ponto", "Cadastro de Funcionários", "Relatórios"]
    
    pagina = st.radio("Navegação", opcoes)
    
    if eh_admin:
        st.divider()
        hoje_ref = datetime.now(fuso_br)
        mes_ref = st.selectbox("Mês de Referência", list(range(1, 13)), index=hoje_ref.month - 1)
        ano_ref = st.number_input("Ano", value=hoje_ref.year, step=1)
    
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

# --- LÓGICA DAS PÁGINAS ---

# 1. PÁGINA: BATER PONTO

# --- CSS PARA INTERFACE PROFISSIONAL ---
st.markdown("""
<style>
    /* Estilização Geral */
    [data-testid="column"] { padding: 0px 5px !important; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; }
    
    /* REMOVENDO AS BOLINHAS DO MENU */
    div[role="radiogroup"] span[data-baseweb="radio"] {
        display: none !important;
    }
    
    /* TRANSFORMANDO O TEXTO EM BOTÕES */
    div[role="radiogroup"] label {
        background-color: #f1f3f5 !important;
        border-radius: 8px !important;
        padding: 10px 15px !important;
        margin-bottom: 8px !important;
        border: 1px solid #d1d3d4 !important;
        transition: all 0.3s ease !important;
        display: block !important;
        width: 100% !important;
    }

    /* EFEITO AO PASSAR O MOUSE */
    div[role="radiogroup"] label:hover {
        background-color: #e9ecef !important;
        border-color: #007BFF !important;
        transform: translateX(5px);
    }

    /* ITEM SELECIONADO (AZUL MSCGYM) */
    div[role="radiogroup"] input:checked + label {
        background-color: #007BFF !important;
        color: white !important;
        border-color: #0056b3 !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

    # Opção de excluir
    if reg_e:
        with st.expander("🗑️ Excluir Registro"):
            if st.button("CONFIRMAR EXCLUSÃO"):
                supabase.table("registros_ponto").delete().eq("id", reg_e['id']).execute()
                st.warning("Registro removido!")
                st.rerun()

# 3. PÁGINA: RELATÓRIOS (SÓ ADMIN)
elif pagina == "Relatórios" and eh_admin:
    st.subheader("📊 Relatórios Financeiros")
    res_f3 = supabase.table("funcionarios").select("*").execute()
    alvo_r = st.selectbox("Selecione o Funcionário", [f['nome'] for f in res_f3.data])
    info_r = next(f for f in res_f3.data if f['nome'] == alvo_r)
    
    res_p = supabase.table("registros_ponto").select("*").eq("usuario", alvo_r).execute()
    if res_p.data:
        df = pd.DataFrame(res_p.data)
        df['data'] = pd.to_datetime(df['data'])
        df_mes = df[(df['data'].dt.month == mes_ref) & (df['data'].dt.year == int(ano_ref))].sort_values("data")
        st.metric("Total Horas no Mês", f"{df_mes['horas_trabalhadas'].sum():.2f}h")
        st.dataframe(df_mes[['data', 'entrada', 'saida', 'horas_trabalhadas']], use_container_width=True)

# 4. PÁGINA: CADASTRO (SÓ ADMIN)
elif pagina == "Cadastro de Funcionários" and eh_admin:
    st.subheader("👤 Novo Usuário")
    with st.form("cad"):
        n = st.text_input("Nome")
        s = st.text_input("Senha", value="1234")
        p = st.selectbox("Perfil", ["funcionario", "admin"])
        v = st.number_input("Valor Hora (PJ)", value=0.0)
        if st.form_submit_button("Cadastrar"):
            supabase.table("funcionarios").insert({"nome": n, "senha": s, "perfil": p, "valor_hora": v}).execute()
            st.success("Cadastrado!"); st.rerun()
