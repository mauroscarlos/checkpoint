import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# 1. Conexão (Puxe dos Secrets para ficar seguro)
URL = "https://iorjkyxjjogqtjdlmyhv.supabase.co"
KEY = "sb_publishable_M1aCKJu_pYJaFLgPP7Nlqw_C9qXfI6L"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Controle de Ponto", layout="wide")

st.title("⏱️ Controle de Ponto - MSCGYM")

# Menu lateral para navegação
menu = st.sidebar.selectbox("Ir para:", ["Registrar Ponto", "Consultar Histórico"])

if menu == "Registrar Ponto":
    with st.form("form_ponto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Funcionário")
            data = st.date_input("Data", datetime.now())
        with col2:
            ent = st.time_input("Entrada", value=datetime.strptime("08:00", "%H:%M"))
            sai_alm = st.time_input("Saída Almoço", value=datetime.strptime("12:00", "%H:%M"))
        
        col3, col4 = st.columns(2)
        with col3:
            ret_alm = st.time_input("Retorno Almoço", value=datetime.strptime("13:00", "%H:%M"))
        with col4:
            sai = st.time_input("Saída Final", value=datetime.strptime("17:00", "%H:%M"))

        btn_registrar = st.form_submit_button("Salvar Registro")

    if btn_registrar:
        # Lógica de cálculo
        t_entrada = datetime.combine(data, ent)
        t_saida_alm = datetime.combine(data, sai_alm)
        t_retorno_alm = datetime.combine(data, ret_alm)
        t_saida_final = datetime.combine(data, sai)

        # Horas totais - Almoço
        turno_1 = (t_saida_alm - t_entrada).total_seconds() / 3600
        turno_2 = (t_saida_final - t_retorno_alm).total_seconds() / 3600
        total_horas = turno_1 + turno_2
        
        # Banco de horas (Considerando jornada de 8h)
        # Se trabalhar 9h, sobra 1h extra. Se trabalhar 7h, fica -1h.
        saldo = total_horas - 8.0

        dados = {
            "usuario": nome,
            "data": str(data),
            "entrada": str(ent),
            "saida_almoco": str(sai_alm),
            "retorno_almoco": str(ret_alm),
            "saida": str(sai),
            "horas_trabalhadas": round(total_horas, 2),
            "horas_extras": round(saldo, 2)
        }

        try:
            supabase.table("registros_ponto").insert(dados).execute()
            st.success(f"Ponto de {nome} registrado com sucesso!")
            st.info(f"Horas: {total_horas:.2f}h | Saldo: {saldo:+.2f}h")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

elif menu == "Consultar Histórico":
    st.subheader("📋 Registros Armazenados")
    res = supabase.table("registros_ponto").select("*").execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        # Ajustando a ordem das colunas para ficar legível
        df = df[['usuario', 'data', 'entrada', 'saida', 'horas_trabalhadas', 'horas_extras']]
        st.dataframe(df, use_container_width=True)
        
        # Resumo do Banco de Horas
        total_banco = df['horas_extras'].sum()
        st.divider()
        st.metric("Saldo Geral do Banco de Horas", f"{total_banco:.2f} Horas")
