import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta

# 1. Conexão com o Supabase (Substitua pelos seus dados do painel Settings > API)
URL = "https://iorjkyxjjogqtjdlmyhv.supabase.co"
KEY = "sb_publishable_M1aCKJu_pYJaFLgPP7Nlqw_C9qXfI6L"
supabase = create_client(URL, KEY)

st.title("⏱️ Controle de Ponto Inteligente")

# 2. Interface de Entrada
with st.form("ponto_form"):
    nome = st.text_input("Nome do Funcionário")
    data = st.date_input("Data do Registro", datetime.now())
    ent = st.time_input("Entrada", value=datetime.strptime("08:00", "%H:%M"))
    sai_alm = st.time_input("Saída Almoço", value=datetime.strptime("12:00", "%H:%M"))
    ret_alm = st.time_input("Retorno Almoço", value=datetime.strptime("13:00", "%H:%M"))
    sai = st.time_input("Saída", value=datetime.strptime("17:00", "%H:%M"))
    
    enviar = st.form_submit_button("Registrar Ponto")

# 3. Lógica de Cálculo
if enviar:
    # Converter para objetos de tempo para calcular
    t1 = datetime.combine(data, ent)
    t2 = datetime.combine(data, sai_alm)
    t3 = datetime.combine(data, ret_alm)
    t4 = datetime.combine(data, sai)
    
    # Horas trabalhadas excluindo o almoço
    total_segundos = (t2 - t1).total_seconds() + (t4 - t3).total_seconds()
    total_horas = total_segundos / 3600
    
    # Cálculo de Extras (Exemplo baseado em jornada de 8h)
    carga_horaria = 8.0
    extras = max(0.0, total_horas - carga_horaria)
    
    # Enviar para o Supabase
    dados = {
        "usuario": nome,
        "data": str(data),
        "entrada": str(ent),
        "saida_almoco": str(sai_alm),
        "retorno_almoco": str(ret_alm),
        "saida": str(sai),
        "horas_trabalhadas": total_horas,
        "horas_extras": extras
    }
    
    response = supabase.table("registros_ponto").insert(dados).execute()
    st.success(f"Ponto registrado! Total: {total_horas:.2f}h | Extras: {extras:.2f}h")
