import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Controle de RMs", layout="wide")

def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

def formatar_status_tempo(data_entrada, status):
    if status == "Separada":
        return "🟡 **EM PROCESSO DE SEPARAÇÃO**"
    agora = datetime.now()
    diferenca = agora - pd.to_datetime(data_entrada)
    if diferenca > timedelta(hours=24):
        return f"🔴 **ATRASADA (>24h)**"
    else:
        return f"🟢 **NO PRAZO**"

if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None
if st.session_state['perfil_logado'] is None:
    col_meio = st.columns([2, 1, 2])[1]
    with col_meio:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>🔑 Login</h3>", unsafe_allow_html=True)
            with st.form("login_form"):
                usuario = st.text_input("Usuário:")
                senha = st.text_input("Senha:", type="password")
                if st.form_submit_button("Entrar", use_container_width=True):
                    if usuario == "pdc" and senha == "123":
                        st.session_state['perfil_logado'] = "Admin"; st.rerun()
                    elif usuario == "cummins" and senha == "1234":
                        st.session_state['perfil_logado'] = "Visitante"; st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
            st.markdown("<div style='text-align: center;'><small>Se você é um solicitador de RM</small><br><b>usuario: cummins</b><br><b>senha: 1234</b></div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Sistema elaborado por Kevin.</p>", unsafe_allow_html=True)
    st.stop()

sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
df['data_entrada'] = pd.to_datetime(df['data_entrada'], errors='coerce')
df['data_retirada'] = pd.to_datetime(df['data_retirada'], errors='coerce')
es_admin = (st.session_state['perfil_logado'] == "Admin")

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state['perfil_logado']}**")
    if st.button("🚪 Sair"):
        st.session_state['perfil_logado'] = None
        st.rerun()

st.title("📦 Sistema de Controle de RMs")

if es_admin:
    tabs = st.tabs(["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"])
else:
    tabs = st.tabs(["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"])

def mostrar_conteudo(nome_tab):
    # ... (Mantenha o conteúdo anterior de Dashboard, Painel, Pend. Retirada, Nova RM)
    if nome_tab == "📊 Dashboard":
        # (Código omitido para brevidade, mantenha o seu anterior)
        pass 
    elif nome_tab == "📋 Painel":
        # (Código omitido para brevidade, mantenha o seu anterior)
        pass
    elif nome_tab == "📦 Pend. Retirada":
        # (Código omitido para brevidade, mantenha o seu anterior)
        pass
    elif nome_tab == "➕ Nova RM":
        # (Código omitido para brevidade, mantenha o seu anterior)
        pass

    elif nome_tab == "🔍 Consulta":
        st.subheader("🔍 Consultar RM")
        # Cria a sugestão baseada nas RMs existentes
        lista_rms = df['numero_rm'].astype(str).tolist()
        
        # Selectbox funciona como um buscador dinâmico
        busca = st.selectbox("Digite ou selecione a RM (8 dígitos):", [""] + lista_rms)
        
        if busca:
            res = df[df['numero_rm'].astype(str) == str(busca).strip()]
            if not res.empty:
                rm = res.iloc[0]
                with st.container(border=True):
                    st.write(f"**RM:** {rm['numero_rm']} | **Solicitante:** {rm['solicitante']}")
                    if rm['status'] == 'Aberta':
                        st.write("Status: **Aberta**")
                        if st.button("🔔 Cobrar", key="c_c"):
                            sheet.update_cell(sheet.find(str(rm['id']), in_column=1).row, 9, "COBRADO")
                            st.rerun()
                    elif rm['status'] == 'Separada':
                        st.write("Status: 🟡 **Separada aguardando retirada**")
                    else:
                        st.write(f"Status: **{rm['status']}**")
            else:
                st.warning("RM não encontrada.")

    elif nome_tab == "📊 Histórico":
        # (Código do Histórico anterior)
        pass

# Execução das tabs
for i, nome in enumerate(nomes := ["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"] if es_admin else ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"]):
    with tabs[i]: mostrar_conteudo(nome)
