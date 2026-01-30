import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import calendar
import pytz
from fpdf import FPDF

# 1. Conexão com o Banco de Dados
URL = "https://iorjkyxjjogqtjdlmyhv.supabase.co"
KEY = "sb_publishable_M1aCKJu_pYJaFLgPP7Nlqw_C9qXfI6L"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="MSCGYM - Gestão de Ponto", layout="wide")

# Fuso Horário de Brasília
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- CSS para Interface Compacta ---
st.markdown("""
    <style>
    [data-testid="column"] { padding: 0px 2px !important; }
    [data-testid="stVerticalBlock"] { gap: 0rem !important; }
    input[type="time"] { padding: 2px !important; height: 30px !important; }
    .stButton>button { padding: 0px 5px !important; height: 32px !important; width: 100%; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
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
    pdf.ln(20)
    pdf.cell(95, 0, "", border="T")
    pdf.cell(5, 0, "")
    pdf.cell(90, 0, "", border="T", ln=True)
    pdf.cell(95, 10, "Assinatura do Funcionário", align="C")
    pdf.cell(95, 10, "Responsável MSCGYM", align="C")
    return pdf.output()

# --- MENU LATERAL ---
with st.sidebar:
    st.title("🚀 MSCGYM Ponto")
    pagina = st.radio("Navegação", ["Bater Ponto", "Folha de Ponto", "Manutenção de Ponto", "Cadastro de Funcionários", "Relatórios"])
    st.divider()
    res_func = supabase.table("funcionarios").select("*").execute()
    dados_func = res_func.data if res_func.data else []
    lista_nomes = [f['nome'] for f in dados_func]
    if pagina != "Cadastro de Funcionários":
        if not lista_nomes:
            st.warning("⚠️ Cadastre um funcionário primeiro!")
            selecionado = None
        else:
            selecionado = st.selectbox("Funcionário Ativo", lista_nomes)
            info_func = next(item for item in dados_func if item["nome"] == selecionado)
            hoje = datetime.now(fuso_br).date()
            mes = st.selectbox("Mês de Referência", list(range(1, 13)), index=hoje.month - 1)
            ano = st.number_input("Ano", value=hoje.year, step=1)

# --- PÁGINA: BATER PONTO ---
if pagina == "Bater Ponto" and selecionado:
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

# --- PÁGINA: FOLHA DE PONTO ---
elif pagina == "Folha de Ponto" and selecionado:
    st.subheader(f"📅 Folha: {selecionado}")
    num_dias = calendar.monthrange(int(ano), mes)[1]
    dias_do_mes = [date(int(ano), mes, d) for d in range(1, num_dias + 1)]
    res = supabase.table("registros_ponto").select("*").eq("usuario", selecionado).execute()
    dados_existentes = {datetime.strptime(d['data'], '%Y-%m-%d').date(): d for d in res.data}
    for dia in dias_do_mes:
        reg = dados_existentes.get(dia, {})
        with st.expander(f"📅 {dia.strftime('%d/%m - %a')} {'(📄 Doc)' if reg.get('url_comprovante') else ''}"):
            col_h, col_doc = st.columns([2, 1])
            with col_h:
                c_e1, c_e2, c_e3, c_e4 = st.columns(4)
                ent = c_e1.time_input("E", value=datetime.strptime(reg.get('entrada', "08:00"), "%H:%M"), key=f"e_{dia}")
                sa = c_e2.time_input("SA", value=datetime.strptime(reg.get('saida_almoco', "12:00"), "%H:%M"), key=f"sa_{dia}")
                ra = c_e3.time_input("RA", value=datetime.strptime(reg.get('retorno_almoco', "13:00"), "%H:%M"), key=f"ra_{dia}")
                sf = c_e4.time_input("SF", value=datetime.strptime(reg.get('saida', "17:00"), "%H:%M"), key=f"sf_{dia}")
            with col_doc:
                arquivo = st.file_uploader("Subir Doc", type=['pdf', 'jpg', 'png'], key=f"file_{dia}")
                tipo_doc = st.selectbox("Tipo", ["Nenhum", "Atestado Médico", "Declaração", "Outros"], key=f"tipo_{dia}")
            if st.button("Salvar Dia", key=f"save_{dia}"):
                url_final = reg.get('url_comprovante')
                if arquivo:
                    file_path = f"{selecionado}/{dia}_{arquivo.name}"
                    supabase.storage.from_("comprovantes").upload(file_path, arquivo.getvalue(), {"upsert": "true"})
                    url_final = supabase.storage.from_("comprovantes").get_public_url(file_path)
                total = calcular_horas(ent, sa, ra, sf)
                payload = {"usuario": selecionado, "data": str(dia), "entrada": str(ent)[:5], "saida_almoco": str(sa)[:5], "retorno_almoco": str(ra)[:5], "saida": str(sf)[:5], "horas_trabalhadas": total, "horas_extras": round(total - 8.0, 2), "url_comprovante": url_final, "tipo_documento": tipo_doc}
                if dia in dados_existentes: supabase.table("registros_ponto").update(payload).eq("id", reg['id']).execute()
                else: supabase.table("registros_ponto").insert(payload).execute()
                st.success("Salvo!"); st.rerun()

# --- PÁGINA: MANUTENÇÃO DE PONTO ---
elif pagina == "Manutenção de Ponto" and selecionado:
    st.subheader(f"🛠️ Manutenção: {selecionado}")
    col_data_edit = st.date_input("Selecione o dia", value=datetime.now(fuso_br).date())
    res = supabase.table("registros_ponto").select("*").eq("usuario", selecionado).eq("data", str(col_data_edit)).execute()
    reg_edit = res.data[0] if res.data else None
    with st.form("form_manutencao"):
        c1, c2 = st.columns(2)
        e = c1.time_input("Entrada", value=datetime.strptime(reg_edit.get('entrada', "08:00") if reg_edit else "08:00", "%H:%M"))
        sa = c2.time_input("Saída Almoço", value=datetime.strptime(reg_edit.get('saida_almoco', "12:00") if reg_edit else "12:00", "%H:%M"))
        c3, c4 = st.columns(2)
        ra = c3.time_input("Retorno Almoço", value=datetime.strptime(reg_edit.get('retorno_almoco', "13:00") if reg_edit else "13:00", "%H:%M"))
        sf = c4.time_input("Saída Final", value=datetime.strptime(reg_edit.get('saida', "17:00") if reg_edit else "17:00", "%H:%M"))
        if st.form_submit_button("🔨 SALVAR"):
            total = calcular_horas(e, sa, ra, sf)
            payload = {"usuario": selecionado, "data": str(col_data_edit), "entrada": str(e)[:5], "saida_almoco": str(sa)[:5], "retorno_almoco": str(ra)[:5], "saida": str(sf)[:5], "horas_trabalhadas": total, "horas_extras": round(total - 8.0, 2)}
            if reg_edit: supabase.table("registros_ponto").update(payload).eq("id", reg_edit['id']).execute()
            else: supabase.table("registros_ponto").insert(payload).execute()
            st.success("Ajustado!"); st.rerun()
    if reg_edit:
        if st.button("❌ EXCLUIR REGISTRO"):
            supabase.table("registros_ponto").delete().eq("id", reg_edit['id']).execute()
            st.warning("Apagado!"); st.rerun()

# --- PÁGINA: CADASTRO ---
elif pagina == "Cadastro de Funcionários":
    st.subheader("👤 Cadastro")
    with st.form("cad_func", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome"); car = c2.text_input("Cargo")
        tipo = st.selectbox("Contrato", ["CLT", "PJ"])
        sal = st.number_input("Salário", min_value=0.0); vh = st.number_input("Valor/Hora", min_value=0.0)
        if st.form_submit_button("Salvar"):
            supabase.table("funcionarios").insert({"nome": n, "cargo": car, "tipo_contrato": tipo, "salario_mensal": sal, "valor_hora": vh}).execute()
            st.success("Cadastrado!"); st.rerun()

# --- PÁGINA: RELATÓRIOS ---
elif pagina == "Relatórios" and selecionado:
    st.subheader(f"📊 Relatórios: {selecionado}")
    tabs = st.tabs(["📄 Folha Mensal", "💰 Banco de Horas"])
    res = supabase.table("registros_ponto").select("*").eq("usuario", selecionado).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df['data'] = pd.to_datetime(df['data'])
        df_mes = df[(df['data'].dt.month == mes) & (df['data'].dt.year == int(ano))].sort_values("data")
        with tabs[0]:
            c1, c2, c3 = st.columns(3)
            c1.metric("Horas", f"{df_mes['horas_trabalhadas'].sum():.2f}h")
            c2.metric("Saldo", f"{df_mes['horas_extras'].sum():.2f}h")
            pdf_bytes = gerar_pdf_folha(info_func, df_mes, f"{mes:02d}/{int(ano)}")
            st.download_button("📥 Baixar PDF", pdf_bytes, f"Folha_{selecionado}.pdf", "application/pdf")
            st.dataframe(df_mes[['data', 'entrada', 'saida', 'horas_trabalhadas', 'horas_extras', 'tipo_documento']], use_container_width=True)
        with tabs[1]:
            saldo_total = df['horas_extras'].sum()
            st.metric("Saldo Geral", f"{saldo_total:.2f}h")
            st.metric("Valor Estimado", f"R$ {saldo_total * info_func.get('valor_hora', 0):.2f}")
