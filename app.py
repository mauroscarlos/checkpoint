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
if pagina == "Bater Ponto":
    _, col_central, _ = st.columns([1, 2, 1])
    with col_central:
        st.markdown(f"<h2 style='text-align: center;'>👋 Olá, {u_logado['nome']}!</h2>", unsafe_allow_html=True)
        agora = datetime.now(fuso_br)
        hoje_str = agora.strftime('%Y-%m-%d')
        st.markdown(f"""<div style="background-color: #007BFF; padding: 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">{agora.strftime('%d/%m/%Y')}</p>
            <h1 style="margin: 0; font-size: 3.5rem;">{agora.strftime('%H:%M')}</h1></div>""", unsafe_allow_html=True)
        
        res = supabase.table("registros_ponto").select("*").eq("usuario", u_logado['nome']).eq("data", hoje_str).execute()
        reg_hoje = res.data[0] if res.data else None
        
        proxima = "Entrada"
        cor_b = "#28a745"
        if reg_hoje:
            if not reg_hoje.get('saida_almoco'): proxima, cor_b = "Saída Almoço", "#ffc107"
            elif not reg_hoje.get('retorno_almoco'): proxima, cor_b = "Retorno Almoço", "#17a2b8"
            elif not reg_hoje.get('saida'): proxima, cor_b = "Saída Final", "#dc3545"
            else: proxima = "Concluído"

        if proxima == "Concluído":
            st.success("✅ Jornada finalizada!")
        else:
            st.markdown(f"<style>div.stButton > button {{ background-color: {cor_b} !important; color: white !important; height: 80px; font-weight: bold; border-radius: 15px; }}</style>", unsafe_allow_html=True)
            if st.button(f"REGISTRAR {proxima.upper()}", use_container_width=True):
                hora_at = agora.strftime('%H:%M')
                if not reg_hoje:
                    supabase.table("registros_ponto").insert({"usuario": u_logado['nome'], "data": hoje_str, "entrada": hora_at, "horas_extras": -8.0}).execute()
                else:
                    campo = {"Saída Almoço": "saida_almoco", "Retorno Almoço": "retorno_almoco", "Saída Final": "saida"}[proxima]
                    payload = {campo: hora_at}
                    if proxima == "Saída Final":
                        total = calcular_horas(datetime.strptime(reg_hoje['entrada'], "%H:%M").time(), 
                                               datetime.strptime(reg_hoje['saida_almoco'], "%H:%M").time(),
                                               datetime.strptime(reg_hoje['retorno_almoco'], "%H:%M").time(), 
                                               agora.time())
                        payload.update({"horas_trabalhadas": total, "horas_extras": round(total - 8.0, 2)})
                    supabase.table("registros_ponto").update(payload).eq("id", reg_hoje['id']).execute()
                st.rerun()

# 2. PÁGINA: MANUTENÇÃO (SÓ ADMIN)
elif pagina == "Manutenção de Ponto" and eh_admin:
    st.subheader("🛠️ Manutenção Administrativa")
    
    # Busca a lista de funcionários atualizada
    res_f2 = supabase.table("funcionarios").select("nome").execute()
    lista_f = [f['nome'] for f in res_f2.data] if res_f2.data else []
    
    col_func, col_data = st.columns(2)
    with col_func:
        alvo = st.selectbox("Selecione o Funcionário", lista_u) # Usando lista do login ou f2
    with col_data:
        dia_m = st.date_input("Data do Ajuste", value=datetime.now(fuso_br).date())
    
    # Busca o registro existente
    res_e = supabase.table("registros_ponto").select("*").eq("usuario", alvo).eq("data", str(dia_m)).execute()
    reg_e = res_e.data[0] if res_e.data else None
    
    st.divider()
    
    with st.form("form_manutencao_horizontal"):
        st.write(f"### 📋 Ajuste de Horários: {alvo}")
        st.caption(f"Data selecionada: {dia_m.strftime('%d/%m/%Y')}")
        
        # Linha Horizontal de Horários
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            h_e = st.time_input("📥 Entrada", 
                               value=datetime.strptime(reg_e.get('entrada', "08:00") if reg_e else "08:00", "%H:%M"),
                               help="Ajuste hora e minutos da entrada")
        with c2:
            h_sa = st.time_input("☕ Saída Almoço", 
                                value=datetime.strptime(reg_e.get('saida_almoco', "12:00") if reg_e else "12:00", "%H:%M"))
        with c3:
            h_ra = st.time_input("🔙 Retorno Almoço", 
                                value=datetime.strptime(reg_e.get('retorno_almoco', "13:00") if reg_e else "13:00", "%H:%M"))
        with c4:
            h_s = st.time_input("🚪 Saída Final", 
                               value=datetime.strptime(reg_e.get('saida', "17:00") if reg_e else "17:00", "%H:%M"))
        
        st.write("") # Espaçador
        
        # Botão de Salvar centralizado
        if st.form_submit_button("💾 SALVAR MANUTENÇÃO", use_container_width=True):
            # Cálculo de horas considerando os minutos exatos
            t = calcular_horas(h_e, h_sa, h_ra, h_s)
            
            p = {
                "usuario": alvo, 
                "data": str(dia_m), 
                "entrada": h_e.strftime("%H:%M"), 
                "saida_almoco": h_sa.strftime("%H:%M"), 
                "retorno_almoco": h_ra.strftime("%H:%M"), 
                "saida": h_s.strftime("%H:%M"), 
                "horas_trabalhadas": t, 
                "horas_extras": round(t - 8.0, 2)
            }
            
            if reg_e:
                supabase.table("registros_ponto").update(p).eq("id", reg_e['id']).execute()
            else:
                supabase.table("registros_ponto").insert(p).execute()
                
            st.success(f"✅ Ponto de {alvo} ajustado com sucesso para {t}h trabalhadas!")
            st.rerun()

    # Zona de exclusão
    if reg_e:
        with st.expander("🗑️ Opções Avançadas"):
            if st.button("EXCLUIR REGISTRO DESTE DIA", type="secondary"):
                supabase.table("registros_ponto").delete().eq("id", reg_e['id']).execute()
                st.warning("Registro excluído.")
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
