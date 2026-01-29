import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import calendar

# 1. Conexão
URL = "https://iorjkyxjjogqtjdlmyhv.supabase.co"
KEY = "sb_publishable_M1aCKJu_pYJaFLgPP7Nlqw_C9qXfI6L"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Folha de Ponto", layout="wide")

# Funções de Apoio
def calcular_horas(e, s_a, r_a, s):
    try:
        # Cálculo simples em horas decimais
        t1 = e.hour + e.minute/60
        t2 = s_a.hour + s_a.minute/60
        t3 = r_a.hour + r_a.minute/60
        t4 = s.hour + s.minute/60
        
        total = (t2 - t1) + (t4 - t3)
        return round(total, 2)
    except:
        return 0.0

st.title("📅 Folha de Ponto Mensal")

# Seleção de Filtros
col_filtros1, col_filtros2, col_filtros3 = st.columns(3)
with col_filtros1:
    funcionario = st.text_input("Nome do Funcionário", value="Mauro")
with col_filtros2:
    hoje = date.today()
    mes = st.selectbox("Mês", list(range(1, 13)), index=hoje.month - 1)
with col_filtros3:
    ano = st.number_input("Ano", value=hoje.year)

# Gerar dias do mês selecionado
num_dias = calendar.monthrange(ano, mes)[1]
dias_do_mes = [date(ano, mes, d) for d in range(1, num_dias + 1)]

# Buscar dados existentes no Supabase para este funcionário/mês
res = supabase.table("registros_ponto").select("*").eq("usuario", funcionario).execute()
dados_existentes = {datetime.strptime(d['data'], '%Y-%m-%d').date(): d for d in res.data}

st.divider()

# Cabeçalho da Tabela
c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 2, 2, 2, 2, 1.5, 1.5])
c1.write("**Data**")
c2.write("**Entrada**")
c3.write("**Saída Almoço**")
c4.write("**Retorno Almoço**")
c5.write("**Saída Final**")
c6.write("**Total**")
c7.write("**Ação**")

# Gerar as linhas horizontais
for dia in dias_do_mes:
    # Se já existir dado, carrega. Se não, valores padrão.
    tem_dado = dia in dados_existentes
    registro = dados_existentes.get(dia, {})
    
    with st.container():
        col_data, col_e, col_sa, col_ra, col_sf, col_total, col_btn = st.columns([1.5, 2, 2, 2, 2, 1.5, 1.5])
        
        col_data.write(dia.strftime("%d/%m (%a)"))
        
        # Campos de entrada alinhados
        ent = col_e.time_input("Ent", value=datetime.strptime(registro.get('entrada', "08:00"), "%H:%M"), key=f"e_{dia}", label_visibility="collapsed")
        sai_a = col_sa.time_input("S_A", value=datetime.strptime(registro.get('saida_almoco', "12:00"), "%H:%M"), key=f"sa_{dia}", label_visibility="collapsed")
        ret_a = col_ra.time_input("R_A", value=datetime.strptime(registro.get('retorno_almoco', "13:00"), "%H:%M"), key=f"ra_{dia}", label_visibility="collapsed")
        sai_f = col_sf.time_input("S_F", value=datetime.strptime(registro.get('saida', "17:00"), "%H:%M"), key=f"sf_{dia}", label_visibility="collapsed")
        
        # Cálculo automático na linha
        total = calcular_horas(ent, sai_a, ret_a, sai_f)
        col_total.write(f"{total}h")
        
        # Botão de Salvar para cada linha
        if col_btn.button("💾", key=f"btn_{dia}"):
            payload = {
                "usuario": funcionario,
                "data": str(dia),
                "entrada": str(ent),
                "saida_almoco": str(sai_a),
                "retorno_almoco": str(ret_a),
                "saida": str(sai_f),
                "horas_trabalhadas": total,
                "horas_extras": round(total - 8.0, 2)
            }
            
            if tem_dado:
                # Atualiza registro existente
                supabase.table("registros_ponto").update(payload).eq("id", registro['id']).execute()
            else:
                # Cria novo
                supabase.table("registros_ponto").insert(payload).execute()
            
            st.toast(f"Dia {dia.day} salvo!", icon="✅")
