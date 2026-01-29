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

# --- CSS Corrigido para reduzir espaço e compactar ---
st.markdown("""
    <style>
    /* Reduz o espaço entre colunas */
    [data-testid="column"] {
        padding: 0px 2px !important;
    }
    /* Reduz o espaço entre linhas do Streamlit */
    [data-testid="stVerticalBlock"] {
        gap: 0rem !important;
    }
    /* Diminui a altura dos inputs de tempo */
    input[type="time"] {
        padding: 2px !important;
        height: 30px !important;
    }
    /* Botão menor */
    .stButton>button {
        padding: 0px 5px !important;
        height: 30px !important;
        line-height: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Funções de Apoio
def calcular_horas(e, s_a, r_a, s):
    try:
        t1 = e.hour + e.minute/60
        t2 = s_a.hour + s_a.minute/60
        t3 = r_a.hour + r_a.minute/60
        t4 = s.hour + s.minute/60
        total = (t2 - t1) + (t4 - t3)
        return round(total, 2)
    except:
        return 0.0

# --- MENU LATERAL ---
with st.sidebar:
    st.title("🛠️ Configurações")
    funcionario = st.text_input("Funcionário", value="Mauro")
    hoje = date.today()
    mes = st.selectbox("Mês", list(range(1, 13)), index=hoje.month - 1)
    ano = st.number_input("Ano", value=hoje.year, step=1)
    st.divider()
    aba = st.radio("Navegação", ["Folha Mensal", "Resumo Banco de Horas"])

# Gerar dias do mês
num_dias = calendar.monthrange(int(ano), mes)[1]
dias_do_mes = [date(int(ano), mes, d) for d in range(1, num_dias + 1)]

# Buscar dados existentes
res = supabase.table("registros_ponto").select("*").eq("usuario", funcionario).execute()
dados_existentes = {datetime.strptime(d['data'], '%Y-%m-%d').date(): d for d in res.data}

if aba == "Folha Mensal":
    st.subheader(f"📅 Folha: {funcionario} - {mes:02d}/{int(ano)}")
    
    # Cabeçalho da Tabela (Pesos das colunas para alinhamento)
    c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1.8, 1.8, 1.8, 1.8, 0.8, 0.8])
    c1.caption("Data")
    c2.caption("Entrada")
    c3.caption("S. Almoço")
    c4.caption("R. Almoço")
    c5.caption("Saída")
    c6.caption("Total")
    c7.caption("Salvar")

    # Gerar as linhas
    for dia in dias_do_mes:
        registro = dados_existentes.get(dia, {})
        tem_dado = dia in dados_existentes
        is_fds = dia.weekday() >= 5

        with st.container():
            col_data, col_e, col_sa, col_ra, col_sf, col_total, col_btn = st.columns([1, 1.8, 1.8, 1.8, 1.8, 0.8, 0.8])
            
            # Data
            data_label = dia.strftime("%d/%m %a")
            if is_fds:
                col_data.markdown(f"<p style='color: #999; margin:0;'>{data_label}</p>", unsafe_allow_html=True)
            else:
                col_data.write(data_label)
            
            # Inputs (label_visibility="collapsed" para não ocupar espaço)
            ent = col_e.time_input("E", value=datetime.strptime(registro.get('entrada', "08:00"), "%H:%M"), key=f"e_{dia}", label_visibility="collapsed")
            sai_a = col_sa.time_input("SA", value=datetime.strptime(registro.get('saida_almoco', "12:00"), "%H:%M"), key=f"sa_{dia}", label_visibility="collapsed")
            ret_a = col_ra.time_input("RA", value=datetime.strptime(registro.get('retorno_almoco', "13:00"), "%H:%M"), key=f"ra_{dia}", label_visibility="collapsed")
            sai_f = col_sf.time_input("SF", value=datetime.strptime(registro.get('saida', "17:00"), "%H:%M"), key=f"sf_{dia}", label_visibility="collapsed")
            
            total = calcular_horas(ent, sai_a, ret_a, sai_f)
            col_total.write(f"{total}h")
            
            if col_btn.button("💾", key=f"btn_{dia}"):
                payload = {
                    "usuario": funcionario,
                    "data": str(dia),
                    "entrada": str(ent)[:5], # Salva apenas HH:mm
                    "saida_almoco": str(sai_a)[:5],
                    "retorno_almoco": str(ret_a)[:5],
                    "saida": str(sai_f)[:5],
                    "horas_trabalhadas": total,
                    "horas_extras": round(total - 8.0, 2)
                }
                if tem_dado:
                    supabase.table("registros_ponto").update(payload).eq("id", registro['id']).execute()
                else:
                    supabase.table("registros_ponto").insert(payload).execute()
                st.toast(f"Dia {dia.day} salvo!", icon="✅")

elif aba == "Resumo Banco de Horas":
    st.subheader(f"📊 Banco de Horas: {funcionario}")
    if res.data:
        df = pd.DataFrame(res.data)
        saldo_total = df['horas_extras'].sum()
        st.metric("Saldo Acumulado", f"{saldo_total:.2f} h")
        st.dataframe(df.sort_values(by="data"), use_container_width=True)
