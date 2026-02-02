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

# --- CSS PARA INTERFACE PROFISSIONAL E MENU SEM BOLINHAS ---
st.markdown("""
<style>
    [data-testid="column"] { padding: 0px 5px !important; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; }
    
    /* REMOVENDO AS BOLINHAS DO MENU LATERAL */
    div[role="radiogroup"] span[data-baseweb="radio"] { display: none !important; }
    
    /* TRANSFORMANDO O TEXTO EM BOTÕES LARGOS */
    div[role="radiogroup"] label {
        background-color: #f1f3f5 !important;
        border-radius: 10px !important;
        padding: 12px 20px !important;
        margin-bottom: 10px !important;
        border: 1px solid #d1d3d4 !important;
        transition: all 0.3s ease !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        cursor: pointer !important;
    }

    div[role="radiogroup"] label:hover {
        background-color: #e9ecef !important;
        border-color: #007BFF !important;
        transform: translateX(5px);
    }

    div[role="radiogroup"] input:checked + label {
        background-color: #007BFF !important;
        color: white !important;
        border-color: #0056b3 !important;
        font-weight: bold !important;
        box-shadow: 0px 4px 10px rgba(0, 123, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- Funções de Apoio ---
def calcular_horas(e, s_a, r_a, s):
    try:
        t1 = e.hour + e.minute/60
        t2 = s_a.hour + s_a.minute/60
        t3 = r_a.hour + r_a.minute/60
        t4 = s.hour + s.minute/60
        return round((t2 - t1) + (t4 - t3), 2)
    except: return 0.0

def limpar_hora(valor):
    """Garante que o valor do banco (HH:MM:SS) seja lido apenas como HH:MM"""
    if not valor: return "00:00"
    return str(valor)[:5]

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

u_logado = st.session_state.usuario_logado
eh_admin = u_logado.get('perfil') == 'admin'

with st.sidebar:
    st.title("🚀 MSCGYM")
    st.write(f"Usuário: **{u_logado['nome']}**")
    opcoes = ["🏠 Bater Ponto"]
    if eh_admin:
        opcoes += ["📅 Folha de Ponto", "🛠️ Manutenção de Ponto", "👤 Cadastro de Funcionários", "📊 Relatórios"]
    pagina = st.radio("Navegação", opcoes)
    if eh_admin:
        st.divider()
        hj = datetime.now(fuso_br)
        mes_ref = st.selectbox("Mês", list(range(1, 13)), index=hj.month - 1)
        ano_ref = st.number_input("Ano", value=hj.year, step=1)
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

# --- LÓGICA DAS PÁGINAS ---

if pagina == "🏠 Bater Ponto":
    st.subheader("⌚ Registro de Ponto")
    agora = datetime.now(fuso_br)
    hoje_str = agora.strftime('%Y-%m-%d')
    st.markdown(f"""<div style="background-color: #007BFF; padding: 20px; border-radius: 15px; text-align: center; color: white;">
        <h1>{agora.strftime('%H:%M')}</h1><p>{agora.strftime('%d/%m/%Y')}</p></div>""", unsafe_allow_html=True)
    
    res = supabase.table("registros_ponto").select("*").eq("usuario", u_logado['nome']).eq("data", hoje_str).execute()
    reg_hoje = res.data[0] if res.data else None
    
    proxima = "Entrada"
    if reg_hoje:
        if not reg_hoje.get('saida_almoco'): proxima = "Saída Almoço"
        elif not reg_hoje.get('retorno_almoco'): proxima = "Retorno Almoço"
        elif not reg_hoje.get('saida'): proxima = "Saída Final"
        else: proxima = "Concluído"

    if proxima != "Concluído":
        if st.button(f"REGISTRAR {proxima.upper()}", use_container_width=True):
            hora_atual = agora.strftime('%H:%M')
            if not reg_hoje:
                supabase.table("registros_ponto").insert({"usuario": u_logado['nome'], "data": hoje_str, "entrada": hora_atual, "horas_extras": -8.0}).execute()
            else:
                campo = {"Saída Almoço": "saida_almoco", "Retorno Almoço": "retorno_almoco", "Saída Final": "saida"}[proxima]
                payload = {campo: hora_atual}
                if proxima == "Saída Final":
                    t = calcular_horas(datetime.strptime(limpar_hora(reg_hoje['entrada']), "%H:%M").time(), 
                                       datetime.strptime(limpar_hora(reg_hoje['saida_almoco']), "%H:%M").time(),
                                       datetime.strptime(limpar_hora(reg_hoje['retorno_almoco']), "%H:%M").time(), agora.time())
                    payload.update({"horas_trabalhadas": t, "horas_extras": round(t - 8.0, 2)})
                supabase.table("registros_ponto").update(payload).eq("id", reg_hoje['id']).execute()
            st.rerun()
    else: st.success("Jornada de hoje concluída!")

elif "📅 Folha de Ponto" in pagina and eh_admin:
    st.subheader("📅 Gestão de Folha")
    res_f = supabase.table("funcionarios").select("nome").execute()
    alvo = st.selectbox("Funcionário", [f['nome'] for f in res_f.data])
    num_dias = calendar.monthrange(int(ano_ref), mes_ref)[1]
    res_d = supabase.table("registros_ponto").select("*").eq("usuario", alvo).execute()
    dados = {datetime.strptime(d['data'], '%Y-%m-%d').date(): d for d in res_d.data}
    for d in range(1, num_dias + 1):
        dia = date(int(ano_ref), mes_ref, d)
        reg = dados.get(dia, {})
        with st.expander(f"Dia {d:02d} - {dia.strftime('%a')}"):
            c = st.columns(4)
            ent = c[0].time_input("E", value=datetime.strptime(limpar_hora(reg.get('entrada', "08:00")), "%H:%M"), key=f"e{d}")
            sa = c[1].time_input("SA", value=datetime.strptime(limpar_hora(reg.get('saida_almoco', "12:00")), "%H:%M"), key=f"sa{d}")
            ra = c[2].time_input("RA", value=datetime.strptime(limpar_hora(reg.get('retorno_almoco', "13:00")), "%H:%M"), key=f"ra{d}")
            sf = c[3].time_input("S", value=datetime.strptime(limpar_hora(reg.get('saida', "17:00")), "%H:%M"), key=f"sf{d}")
            if st.button("Salvar", key=f"b{d}"):
                t = calcular_horas(ent, sa, ra, sf)
                p = {"usuario": alvo, "data": str(dia), "entrada": ent.strftime("%H:%M"), "saida_almoco": sa.strftime("%H:%M"), "retorno_almoco": ra.strftime("%H:%M"), "saida": sf.strftime("%H:%M"), "horas_trabalhadas": t, "horas_extras": round(t - 8.0, 2)}
                if reg: supabase.table("registros_ponto").update(p).eq("id", reg['id']).execute()
                else: supabase.table("registros_ponto").insert(p).execute()
                st.rerun()

elif "🛠️ Manutenção de Ponto" in pagina and eh_admin:
    st.subheader("🛠️ Manutenção")
    res_f2 = supabase.table("funcionarios").select("nome").execute()
    alvo_m = st.selectbox("Funcionário", [f['nome'] for f in res_f2.data], key="m_alvo")
    dia_m = st.date_input("Data", value=datetime.now(fuso_br).date())
    res_e = supabase.table("registros_ponto").select("*").eq("usuario", alvo_m).eq("data", str(dia_m)).execute()
    reg_e = res_e.data[0] if res_e.data else None
    with st.form("m_form"):
        c = st.columns(4)
        he = c[0].time_input("Entrada", value=datetime.strptime(limpar_hora(reg_e.get('entrada', "08:00") if reg_e else "08:00"), "%H:%M"))
        hsa = c[1].time_input("S. Almoço", value=datetime.strptime(limpar_hora(reg_e.get('saida_almoco', "12:00") if reg_e else "12:00"), "%H:%M"))
        hra = c[2].time_input("R. Almoço", value=datetime.strptime(limpar_hora(reg_e.get('retorno_almoco', "13:00") if reg_e else "13:00"), "%H:%M"))
        hs = c[3].time_input("Saída", value=datetime.strptime(limpar_hora(reg_e.get('saida', "17:00") if reg_e else "17:00"), "%H:%M"))
        if st.form_submit_button("SALVAR AJUSTE", use_container_width=True):
            t = calcular_horas(he, hsa, hra, hs)
            payload = {"usuario": alvo_m, "data": str(dia_m), "entrada": he.strftime("%H:%M"), "saida_almoco": hsa.strftime("%H:%M"), "retorno_almoco": hra.strftime("%H:%M"), "saida": hs.strftime("%H:%M"), "horas_trabalhadas": t, "horas_extras": round(t - 8.0, 2)}
            if reg_e: supabase.table("registros_ponto").update(payload).eq("id", reg_e['id']).execute()
            else: supabase.table("registros_ponto").insert(payload).execute()
            st.success("Salvo!"); st.rerun()

elif "📊 Relatórios" in pagina and eh_admin:
    st.subheader("📊 Relatórios")
    res_f3 = supabase.table("funcionarios").select("*").execute()
    alvo_r = st.selectbox("Funcionário", [f['nome'] for f in res_f3.data])
    res_p = supabase.table("registros_ponto").select("*").eq("usuario", alvo_r).execute()
    if res_p.data:
        df = pd.DataFrame(res_p.data)
        df['data'] = pd.to_datetime(df['data'])
        df_mes = df[(df['data'].dt.month == mes_ref) & (df['data'].dt.year == int(ano_ref))].sort_values("data")
        st.metric("Total Horas no Mês", f"{df_mes['horas_trabalhadas'].sum():.2f}h")
        st.dataframe(df_mes[['data', 'entrada', 'saida', 'horas_trabalhadas']], use_container_width=True)

elif "👤 Cadastro de Funcionários" in pagina and eh_admin:
    st.subheader("👤 Novo Usuário")
    with st.form("cad"):
        n = st.text_input("Nome")
        s = st.text_input("Senha", value="1234")
        p = st.selectbox("Perfil", ["funcionario", "admin"])
        v = st.number_input("Valor Hora", value=0.0)
        if st.form_submit_button("Cadastrar"):
            supabase.table("funcionarios").insert({"nome": n, "senha": s, "perfil": p, "valor_hora": v}).execute()
            st.success("Cadastrado!"); st.rerun()
