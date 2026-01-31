import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import calendar
import pytz
from fpdf import FPDF

# 1. Conexão
URL = "https://iorjkyxjjogqtjdlmyhv.supabase.co"
KEY = "sb_publishable_M1aCKJu_pYJaFLgPP7Nlqw_C9qXfI6L"

supabase = create_client(URL, KEY)

st.set_page_config(page_title="MSCGYM - Gestão Segura", layout="wide")

fuso_br = pytz.timezone('America/Sao_Paulo')

# --- FUNÇÕES DE APOIO ---
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
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, f"Relatório de Frequência: {mes_ano}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f" Funcionário: {funcionario_info['nome']}", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 8, f" Cargo: {funcionario_info.get('cargo', 'N/A')}", border=0)
    pdf.cell(95, 8, f" Contrato: {funcionario_info.get('tipo_contrato', 'N/A')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 9)
    colunas = ["Data", "Entrada", "S.Alm", "R.Alm", "Saída", "Total", "Saldo"]
    larguras = [25, 25, 25, 25, 25, 30, 30]
    for i, col in enumerate(colunas):
        pdf.cell(larguras[i], 8, col, border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for _, row in df_mes.iterrows():
        pdf.cell(larguras[0], 7, row['data'].strftime('%d/%m/%Y'), border=1, align="C")
        pdf.cell(larguras[1], 7, str(row['entrada']), border=1, align="C")
        pdf.cell(larguras[2], 7, str(row['saida_almoco']), border=1, align="C")
        pdf.cell(larguras[3], 7, str(row['retorno_almoco']), border=1, align="C")
        pdf.cell(larguras[4], 7, str(row['saida']), border=1, align="C")
        pdf.cell(larguras[5], 7, f"{row['horas_trabalhadas']}h", border=1, align="C")
        pdf.cell(larguras[6], 7, f"{row['horas_extras']:+.2f}h", border=1, align="C")
        pdf.ln()
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 10, f"Total de Horas no Mês: {df_mes['horas_trabalhadas'].sum():.2f}h", ln=True, align="R")
    return pdf.output()

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_logado = None

if not st.session_state.autenticado:
    st.title("🔐 MSCGYM - Acesso Restrito")
    with st.form("login_form"):
        res_func = supabase.table("funcionarios").select("*").execute()
        lista_usuarios = [f['nome'] for f in res_func.data] if res_func.data else []
        
        user = st.selectbox("Selecione seu nome", lista_usuarios)
        senha = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Entrar"):
            dados_user = next((f for f in res_func.data if f['nome'] == user), None)
            if dados_user and dados_user.get('senha') == senha:
                st.session_state.autenticado = True
                st.session_state.usuario_logado = dados_user
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

# --- SE CHEGOU AQUI, ESTÁ LOGADO ---
u = st.session_state.usuario_logado
selecionado = u['nome']
eh_admin = u.get('perfil') == 'admin'

with st.sidebar:
    st.title("🚀 MSCGYM")
    st.write(f"Logado como: **{selecionado}**")
    
    opcoes = ["Bater Ponto"]
    if eh_admin:
        opcoes += ["Folha de Ponto", "Manutenção de Ponto", "Cadastro de Funcionários", "Relatórios"]
    
    pagina = st.radio("Navegação", opcoes)
    
    if st.button("Sair / Logout"):
        st.session_state.autenticado = False
        st.rerun()

    if eh_admin:
        st.divider()
        hoje = datetime.now(fuso_br).date()
        mes = st.selectbox("Mês Referência", list(range(1, 13)), index=hoje.month - 1)
        ano = st.number_input("Ano", value=hoje.year, step=1)

# --- PÁGINAS (Mantendo a lógica anterior, mas filtrando pelo logado) ---

if pagina == "Bater Ponto":
    _, col_central, _ = st.columns([1, 2, 1])
    with col_central:
        st.markdown(f"<h2 style='text-align: center;'>👋 Olá, {selecionado}!</h2>", unsafe_allow_html=True)
        agora = datetime.now(fuso_br)
        hoje_str = agora.strftime('%Y-%m-%d')
        st.markdown(f"""<div style="background-color: #007BFF; padding: 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">{agora.strftime('%d de %B de %Y')}</p>
            <h1 style="margin: 0; font-size: 3.5rem;">{agora.strftime('%H:%M')}</h1></div>""", unsafe_allow_html=True)
        
        res = supabase.table("registros_ponto").select("*").eq("usuario", selecionado).eq("data", hoje_str).execute()
        reg_hoje = res.data[0] if res.data else None
        
        # ... (Restante da lógica de bater ponto igual à anterior) ...
        proxima = "Entrada"
        cor_botao = "#28a745"
        if reg_hoje:
            if not reg_hoje.get('saida_almoco'): proxima, cor_botao = "Saída Almoço", "#ffc107"
            elif not reg_hoje.get('retorno_almoco'): proxima, cor_botao = "Retorno Almoço", "#17a2b8"
            elif not reg_hoje.get('saida'): proxima, cor_botao = "Saída Final", "#dc3545"
            else: proxima = "Concluído"

        if proxima == "Concluído":
            st.success("✨ Jornada finalizada!")
        else:
            st.markdown(f"<style>div.stButton > button {{ background-color: {cor_botao} !important; color: white !important; height: 80px; font-weight: bold; border-radius: 15px; }}</style>", unsafe_allow_html=True)
            if st.button(f"REGISTRAR {proxima.upper()}", use_container_width=True):
                hora_atual = agora.strftime('%H:%M')
                if not reg_hoje:
                    supabase.table("registros_ponto").insert({"usuario": selecionado, "data": hoje_str, "entrada": hora_atual, "horas_extras": -8.0}).execute()
                else:
                    campo_map = {"Saída Almoço": "saida_almoco", "Retorno Almoço": "retorno_almoco", "Saída Final": "saida"}
                    payload = {campo_map[proxima]: hora_atual}
                    if proxima == "Saída Final":
                        e = datetime.strptime(reg_hoje['entrada'], "%H:%M").time()
                        sa = datetime.strptime(reg_hoje['saida_almoco'], "%H:%M").time()
                        ra = datetime.strptime(reg_hoje['retorno_almoco'], "%H:%M").time()
                        total = calcular_horas(e, sa, ra, agora.time())
                        payload.update({"horas_trabalhadas": total, "horas_extras": round(total - 8.0, 2)})
                    supabase.table("registros_ponto").update(payload).eq("id", reg_hoje['id']).execute()
                st.balloons(); st.rerun()

# --- PÁGINAS ADMINISTRATIVAS (Somente Admin vê) ---
elif pagina == "Folha de Ponto" and eh_admin:
    st.subheader(f"📅 Folha: {selecionado}")
    # ... (Lógica da Folha de Ponto igual à anterior) ...
    # Nota: Aqui o admin pode ver a sua própria ou a de outros se adicionarmos um selectbox extra.
    pass

elif pagina == "Manutenção de Ponto" and eh_admin:
    st.subheader(f"🛠️ Manutenção")
    alvo = st.selectbox("Selecione o Funcionário para Ajuste", [f['nome'] for f in res_func.data])
    # ... (Lógica da Manutenção igual à anterior, usando 'alvo' no lugar de 'selecionado') ...
    pass

elif pagina == "Cadastro de Funcionários" and eh_admin:
    st.subheader("👤 Gestão de Usuários")
    with st.form("cad_func"):
        n = st.text_input("Nome")
        s = st.text_input("Senha de Acesso", value="1234")
        p = st.selectbox("Perfil", ["funcionario", "admin"])
        # ... outros campos (salário, etc) ...
        if st.form_submit_button("Cadastrar"):
            supabase.table("funcionarios").insert({"nome": n, "senha": s, "perfil": p}).execute()
            st.success("Salvo!"); st.rerun()

elif pagina == "Relatórios" and eh_admin:
    # ... Lógica de Relatórios ...
    pass
