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

st.set_page_config(page_title="MSCGYM - Gestão", layout="wide")
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- CSS PARA REMOVER BOLINHAS E ESTILIZAR MENU ---
st.markdown("""
<style>
    /* Esconde as bolinhas do rádio (incluindo a vermelha) */
    div[role="radiogroup"] span[data-baseweb="radio"] {
        display: none !important;
    }
    
    /* Transforma o texto do menu em botões */
    div[role="radiogroup"] label {
        background-color: #f1f3f5 !important;
        border-radius: 10px !important;
        padding: 12px 20px !important;
        margin-bottom: 8px !important;
        border: 1px solid #d1d3d4 !important;
        display: block !important;
        width: 100% !important;
        cursor: pointer !important;
    }

    /* Botão Selecionado */
    div[role="radiogroup"] input:checked + label {
        background-color: #007BFF !important;
        color: white !important;
        font-weight: bold !important;
        border-color: #0056b3 !important;
    }
    
    /* Efeito de passar o mouse */
    div[role="radiogroup"] label:hover {
        background-color: #e9ecef !important;
        transform: translateX(5px);
        transition: 0.2s;
    }
</style>
""", unsafe_allow_html=True)

# --- Funções de Apoio ---
def formatar_hora_segura(valor):
    if not valor: return "00:00"
    return str(valor)[:5]

def calcular_total_horas(row):
    try:
        def to_min(t_str):
            h, m = map(int, str(t_str).split(':'))
            return h * 60 + m
        t1, t2 = to_min(row['Entrada']), to_min(row['S.Almoco'])
        t3, t4 = to_min(row['R.Almoco']), to_min(row['Saida'])
        return round(((t2 - t1) + (t4 - t3)) / 60, 2)
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

# --- MENU LATERAL ---
with st.sidebar:
    st.title("🚀 MSCGYM")
    st.write(f"Olá, **{u['nome']}**")
    
    # Adicionando Emojis para o menu ficar mais bonito
    opcoes = ["🏠 Bater Ponto"]
    if eh_admin:
        opcoes += ["📅 Folha (Excel)", "📊 Relatórios", "👤 Cadastro"]
    
    pagina = st.radio("Navegação", opcoes)
    
    if eh_admin:
        st.divider()
        hj = datetime.now(fuso_br)
        mes_sel = st.selectbox("Mês Referência", list(range(1, 13)), index=hj.month - 1)
        ano_sel = st.number_input("Ano", value=hj.year)
    
    if st.button("Sair / Logout"):
        st.session_state.autenticado = False
        st.rerun()

# --- 1. PÁGINA: BATER PONTO ---
if pagina == "🏠 Bater Ponto":
    st.subheader("⌚ Ponto em Tempo Real")
    agora = datetime.now(fuso_br)
    hoje_str = agora.strftime('%Y-%m-%d')
    
    st.markdown(f"""<div style="background-color: #007BFF; padding: 20px; border-radius: 15px; text-align: center; color: white;">
        <h1>{agora.strftime('%H:%M:%S')}</h1><p>{agora.strftime('%d/%m/%Y')}</p></div>""", unsafe_allow_html=True)
    
    res = supabase.table("registros_ponto").select("*").eq("usuario", u['nome']).eq("data", hoje_str).execute()
    reg_hoje = res.data[0] if res.data else None
    
    proxima = "Entrada"
    if reg_hoje:
        if not reg_hoje.get('saida_almoco'): proxima = "Saída Almoço"
        elif not reg_hoje.get('retorno_almoco'): proxima = "Retorno Almoço"
        elif not reg_hoje.get('saida'): proxima = "Saída Final"
        else: proxima = "Concluído"

    if proxima != "Concluído":
        if st.button(f"REGISTRAR {proxima.upper()}", use_container_width=True):
            hora_at = agora.strftime('%H:%M')
            if not reg_hoje:
                supabase.table("registros_ponto").insert({"usuario": u['nome'], "data": hoje_str, "entrada": hora_at, "horas_extras": -8.0}).execute()
            else:
                campo = {"Saída Almoço": "saida_almoco", "Retorno Almoço": "retorno_almoco", "Saída Final": "saida"}[proxima]
                payload = {campo: hora_at}
                if proxima == "Saída Final":
                    total = calcular_total_horas({'Entrada': reg_hoje['entrada'], 'S.Almoco': reg_hoje['saida_almoco'], 'R.Almoco': reg_hoje['retorno_almoco'], 'Saida': hora_at})
                    payload.update({"horas_trabalhadas": total, "horas_extras": round(total - 8.0, 2)})
                supabase.table("registros_ponto").update(payload).eq("id", reg_hoje['id']).execute()
            st.rerun()
    else: st.success("Jornada Concluída!")

# --- 2. PÁGINA: FOLHA EXCEL (ADMIN) ---
elif pagina == "📅 Folha (Excel)" and eh_admin:
    st.subheader(f"📊 Planilha de Ajustes - {mes_sel:02d}/{ano_sel}")
    res_func = supabase.table("funcionarios").select("nome").execute()
    alvo = st.selectbox("Selecione o Funcionário", [f['nome'] for f in res_func.data])

    num_dias = calendar.monthrange(int(ano_sel), mes_sel)[1]
    df_base = pd.DataFrame({
        "Data": [date(int(ano_sel), mes_sel, d) for d in range(1, num_dias + 1)],
        "Entrada": ["08:00"] * num_dias, "S.Almoco": ["12:00"] * num_dias,
        "R.Almoco": ["13:00"] * num_dias, "Saida": ["17:00"] * num_dias
    })

    res_p = supabase.table("registros_ponto").select("*").eq("usuario", alvo).execute()
    if res_p.data:
        for r in res_p.data:
            dt_r = datetime.strptime(r['data'], '%Y-%m-%d').date()
            idx = df_base.index[df_base['Data'] == dt_r]
            if not idx.empty:
                df_base.loc[idx, "Entrada"] = formatar_hora_segura(r.get('entrada'))
                df_base.loc[idx, "S.Almoco"] = formatar_hora_segura(r.get('saida_almoco'))
                df_base.loc[idx, "R.Almoco"] = formatar_hora_segura(r.get('retorno_almoco'))
                df_base.loc[idx, "Saida"] = formatar_hora_segura(r.get('saida'))

    df_editado = st.data_editor(df_base, hide_index=True, use_container_width=True)

    if st.button("💾 SALVAR ALTERAÇÕES", use_container_width=True, type="primary"):
        for _, row in df_editado.iterrows():
            t = calcular_total_horas(row)
            payload = {
                "usuario": alvo, "data": str(row['Data']),
                "entrada": row['Entrada'], "saida_almoco": row['S.Almoco'],
                "retorno_almoco": row['R.Almoco'], "saida": row['Saida'],
                "horas_trabalhadas": t, "horas_extras": round(t - 8.0, 2)
            }
            supabase.table("registros_ponto").upsert(payload, on_conflict="usuario,data").execute()
        st.success("Dados salvos!"); st.rerun()

# --- 3. PÁGINA: RELATÓRIOS (ADMIN) ---
elif pagina == "📊 Relatórios" and eh_admin:
    st.subheader("📊 Relatórios e Biometria Digital")
    res_f = supabase.table("funcionarios").select("*").execute()
    alvo_r = st.selectbox("Selecione para o Relatório", [f['nome'] for f in res_f.data])
    
    res_p = supabase.table("registros_ponto").select("*").eq("usuario", alvo_r).execute()
    if res_p.data:
        df = pd.DataFrame(res_p.data)
        df['data'] = pd.to_datetime(df['data'])
        df_mes = df[(df['data'].dt.month == mes_sel) & (df['data'].dt.year == int(ano_sel))].sort_values("data")
        
        c1, c2 = st.columns(2)
        c1.metric("Total de Horas", f"{df_mes['horas_trabalhadas'].sum():.2f}h")
        c2.metric("Saldo de Horas Extras", f"{df_mes['horas_extras'].sum():.2f}h")
        
        st.dataframe(df_mes[['data', 'entrada', 'saida', 'horas_trabalhadas', 'horas_extras']], use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado para este período.")

# --- 4. PÁGINA: CADASTRO ---
elif pagina == "👤 Cadastro" and eh_admin:
    st.subheader("👤 Gestão de Funcionários")
    with st.form("cad"):
        n = st.text_input("Nome Completo")
        s = st.text_input("Senha de Acesso", value="1234")
        p = st.selectbox("Perfil", ["funcionario", "admin"])
        if st.form_submit_button("Cadastrar / Atualizar"):
            supabase.table("funcionarios").upsert({"nome": n, "senha": s, "perfil": p}, on_conflict="nome").execute()
            st.success("Pronto!"); st.rerun()
