import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import calendar

# 1. Conexão com o Banco de Dados
URL = "https://iorjkyxjjogqtjdlmyhv.supabase.co"
KEY = "sb_publishable_M1aCKJu_pYJaFLgPP7Nlqw_C9qXfI6L"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="MSCGYM - Gestão de Ponto", layout="wide")

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

# --- MENU LATERAL ---
with st.sidebar:
    st.title("🚀 MSCGYM Ponto")
    pagina = st.radio("Navegação", ["Bater Ponto", "Folha de Ponto", "Cadastro de Funcionários", "Relatórios"])
    st.divider()
    
    # Busca funcionários e seus detalhes
    res_func = supabase.table("funcionarios").select("*").execute()
    dados_func = res_func.data if res_func.data else []
    lista_nomes = [f['nome'] for f in dados_func]
    
    if pagina != "Cadastro de Funcionários":
        if not lista_nomes:
            st.warning("⚠️ Cadastre um funcionário primeiro!")
            selecionado = None
        else:
            selecionado = st.selectbox("Funcionário Ativo", lista_nomes)
            # Pega os dados do funcionário selecionado para usar depois
            info_func = next(item for item in dados_func if item["nome"] == selecionado)
            hoje = date.today()
            mes = st.selectbox("Mês de Referência", list(range(1, 13)), index=hoje.month - 1)
            ano = st.number_input("Ano", value=hoje.year, step=1)

# --- PÁGINA: BATER PONTO (ESTILO DASHBOARD) ---
if pagina == "Bater Ponto" and selecionado:
    # Centralizando o conteúdo com colunas
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        st.markdown(f"<h2 style='text-align: center;'>👋 Olá, {selecionado}!</h2>", unsafe_allow_html=True)
        
        # Card de Horário Atual
        agora = datetime.now()
        hoje_str = agora.strftime('%Y-%m-%d')
        
        st.markdown(f"""
            <div style="background-color: #007BFF; padding: 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px;">
                <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">{agora.strftime('%d de %B de %Y')}</p>
                <h1 style="margin: 0; font-size: 3.5rem;">{agora.strftime('%H:%M')}</h1>
            </div>
        """, unsafe_allow_html=True)

        # Busca dados de hoje
        res = supabase.table("registros_ponto").select("*").eq("usuario", selecionado).eq("data", hoje_str).execute()
        reg_hoje = res.data[0] if res.data else None

        # Lógica de Próxima Marcação
        proxima = "Entrada"
        cor_botao = "#28a745" # Verde
        if reg_hoje:
            if not reg_hoje.get('saida_almoco'): 
                proxima = "Saída Almoço"
                cor_botao = "#ffc107" # Amarelo
            elif not reg_hoje.get('retorno_almoco'): 
                proxima = "Retorno Almoço"
                cor_botao = "#17a2b8" # Azul claro
            elif not reg_hoje.get('saida'): 
                proxima = "Saída Final"
                cor_botao = "#dc3545" # Vermelho
            else: proxima = "Concluído"

        # Botão estilizado
        if proxima == "Concluído":
            st.success("✨ Jornada finalizada! Bom descanso.")
        else:
            # CSS personalizado para o botão de batida
            st.markdown(f"""
                <style>
                div.stButton > button:first-child {{
                    background-color: {cor_botao};
                    color: white;
                    height: 80px;
                    font-size: 20px;
                    font-weight: bold;
                    border-radius: 15px;
                    border: none;
                    transition: 0.3s;
                }}
                div.stButton > button:first-child:hover {{
                    transform: scale(1.02);
                    filter: brightness(1.1);
                }}
                </style>
            """, unsafe_allow_html=True)
            
            if st.button(f"CLIQUE AQUI PARA REGISTRAR:\n{proxima.upper()}", use_container_width=True):
                hora_atual = agora.strftime('%H:%M')
                if not reg_hoje:
                    payload = {"usuario": selecionado, "data": hoje_str, "entrada": hora_atual, "horas_extras": -8.0}
                    supabase.table("registros_ponto").insert(payload).execute()
                else:
                    campo_map = {"Saída Almoço": "saida_almoco", "Retorno Almoço": "retorno_almoco", "Saída Final": "saida"}
                    payload = {campo_map[proxima]: hora_atual}
                    if proxima == "Saída Final":
                        e = datetime.strptime(reg_hoje['entrada'], "%H:%M").time()
                        sa = datetime.strptime(reg_hoje['saida_almoco'], "%H:%M").time()
                        ra = datetime.strptime(reg_hoje['retorno_almoco'], "%H:%M").time()
                        total = calcular_horas(e, sa, ra, agora.time())
                        payload["horas_trabalhadas"] = total
                        payload["horas_extras"] = round(total - 8.0, 2)
                    supabase.table("registros_ponto").update(payload).eq("id", reg_hoje['id']).execute()
                st.balloons()
                st.rerun()

        # Linha do tempo (Visualização do que já foi batido)
        st.write("---")
        st.write("### 📝 Resumo de Hoje")
        m1, m2, m3, m4 = st.columns(4)
        
        def format_metric(valor):
            return f"<p style='font-size: 1.2rem; font-weight: bold; color: #007BFF; margin:0;'>{valor or '--:--'}</p>"

        with m1: st.markdown(f"Entrada<br>{format_metric(reg_hoje.get('entrada') if reg_hoje else None)}", unsafe_allow_html=True)
        with m2: st.markdown(f"Almoço<br>{format_metric(reg_hoje.get('saida_almoco') if reg_hoje else None)}", unsafe_allow_html=True)
        with m3: st.markdown(f"Retorno<br>{format_metric(reg_hoje.get('retorno_almoco') if reg_hoje else None)}", unsafe_allow_html=True)
        with m4: st.markdown(f"Saída<br>{format_metric(reg_hoje.get('saida') if reg_hoje else None)}", unsafe_allow_html=True)

# --- PÁGINA: FOLHA DE PONTO (COM ANEXOS) ---
elif pagina == "Folha de Ponto" and selecionado:
    st.subheader(f"📅 Folha e Justificativas: {selecionado}")
    
    num_dias = calendar.monthrange(int(ano), mes)[1]
    dias_do_mes = [date(int(ano), mes, d) for d in range(1, num_dias + 1)]
    
    res = supabase.table("registros_ponto").select("*").eq("usuario", selecionado).execute()
    dados_existentes = {datetime.strptime(d['data'], '%Y-%m-%d').date(): d for d in res.data}

    # Cabeçalho
    c1, c2, c3, c4, c5, c6 = st.columns([1, 4, 1, 1, 1, 1])
    
    for dia in dias_do_mes:
        reg = dados_existentes.get(dia, {})
        with st.expander(f"📅 {dia.strftime('%d/%m - %a')} {'(📄 Doc)' if reg.get('url_comprovante') else ''}"):
            col_h, col_doc = st.columns([2, 1])
            
            with col_h:
                st.write("**Horários**")
                ce1, ce2, ce3, ce4 = st.columns(4)
                ent = ce1.time_input("E", value=datetime.strptime(reg.get('entrada', "08:00"), "%H:%M"), key=f"e_{dia}")
                sa = ce2.time_input("SA", value=datetime.strptime(reg.get('saida_almoco', "12:00"), "%H:%M"), key=f"sa_{dia}")
                ra = ce3.time_input("RA", value=datetime.strptime(reg.get('retorno_almoco', "13:00"), "%H:%M"), key=f"ra_{dia}")
                sf = ce4.time_input("SF", value=datetime.strptime(reg.get('saida', "17:00"), "%H:%M"), key=f"sf_{dia}")
            
            with col_doc:
                st.write("**Justificativa/Atestado**")
                arquivo = st.file_uploader("Subir Doc", type=['pdf', 'jpg', 'png'], key=f"file_{dia}")
                tipo_doc = st.selectbox("Tipo", ["Nenhum", "Atestado Médico", "Declaração", "Outros"], key=f"tipo_{dia}")
                
                if reg.get('url_comprovante'):
                    st.link_button("Ver Documento Atual", reg['url_comprovante'])

            if st.button("Salvar Dia", key=f"save_{dia}"):
                url_final = reg.get('url_comprovante')
                
                # Lógica de Upload para o Storage
                if arquivo:
                    file_path = f"{selecionado}/{dia}_{arquivo.name}"
                    supabase.storage.from_("comprovantes").upload(file_path, arquivo.getvalue(), {"upsert": "true"})
                    url_final = supabase.storage.from_("comprovantes").get_public_url(file_path)

                total = calcular_horas(ent, sa, ra, sf)
                payload = {
                    "usuario": selecionado, "data": str(dia), 
                    "entrada": str(ent)[:5], "saida_almoco": str(sa)[:5], 
                    "retorno_almoco": str(ra)[:5], "saida": str(sf)[:5], 
                    "horas_trabalhadas": total, "horas_extras": round(total - 8.0, 2),
                    "url_comprovante": url_final,
                    "tipo_documento": tipo_doc
                }
                
                if dia in dados_existentes:
                    supabase.table("registros_ponto").update(payload).eq("id", reg['id']).execute()
                else:
                    supabase.table("registros_ponto").insert(payload).execute()
                
                st.success("Dados e documento salvos!")
                st.rerun()

# --- PÁGINA: CADASTRO DE FUNCIONÁRIOS ---
elif pagina == "Cadastro de Funcionários":
    st.subheader("👤 Cadastro de Funcionário")
    with st.form("cad_func", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome Completo")
        cargo = col2.text_input("Cargo")
        
        col3, col4, col5 = st.columns(3)
        tipo = col3.selectbox("Tipo de Contrato", ["CLT", "PJ"])
        salario = col4.number_input("Salário Mensal (R$)", min_value=0.0, format="%.2f")
        v_hora = col5.number_input("Valor/Hora (R$)", min_value=0.0, format="%.2f")
        
        if st.form_submit_button("Salvar Cadastro"):
            if nome:
                supabase.table("funcionarios").insert({
                    "nome": nome, "cargo": cargo, "tipo_contrato": tipo, 
                    "salario_mensal": salario, "valor_hora": v_hora
                }).execute()
                st.success(f"Funcionário {nome} cadastrado!")
                st.rerun()

# --- PÁGINA: RELATÓRIOS ---
elif pagina == "Relatórios" and selecionado:
    st.subheader(f"📊 Financeiro: {selecionado}")
    res = supabase.table("registros_ponto").select("*").eq("usuario", selecionado).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df['data'] = pd.to_datetime(df['data'])
        df_mes = df[(df['data'].dt.month == mes) & (df['data'].dt.year == int(ano))].sort_values("data")
        
        total_horas = df_mes['horas_trabalhadas'].sum()
        pagamento_estimado = total_horas * info_func['valor_hora'] if info_func['tipo_contrato'] == "PJ" else info_func['salario_mensal']

        c_r1, c_r2, c_r3 = st.columns(3)
        c_r1.metric("Horas Trabalhadas", f"{total_horas:.2f} h")
        c_r2.metric("Tipo Contrato", info_func['tipo_contrato'])
        c_r3.metric("Previsão de Pagto", f"R$ {pagamento_estimado:.2f}")
        
        st.divider()
        st.write("### Detalhes das Marcações")
        st.dataframe(df_mes[['data', 'entrada', 'saida', 'horas_trabalhadas', 'horas_extras']], use_container_width=True)
