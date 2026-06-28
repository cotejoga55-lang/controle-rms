import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES E CONEXÃO
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")

# (Aqui você mantém suas funções de banco de dados normalmente)
def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

# =====================================================================
# LÓGICA DE LOGIN (A ÚNICA QUE APARECE ANTES DO LOGIN)
# =====================================================================
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    # TELA DE LOGIN CENTRALIZADA
    _, col_centro, _ = st.columns([1, 2, 1])
    with col_centro:
        st.markdown("<h2 style='text-align: center;'>Controle de RMs</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            user = st.text_input("Usuário")
            pw = st.text_input("Senha", type="password")
            if st.form_submit_button("Fazer Login"):
                if (user == "admin" and pw == "12345") or (user == "visitante" and pw == "123"):
                    st.session_state['logado'] = True
                    st.session_state['perfil'] = "Admin" if user == "admin" else "Visitante"
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos")
    
    # O st.stop() é CRUCIAL aqui. Ele impede que qualquer coisa abaixo seja desenhada
    st.stop() 

# =====================================================================
# ÁREA LOGADA (SÓ É EXIBIDA APÓS O LOGIN)
# =====================================================================
# Agora, como o st.stop() acima bloqueou a execução para quem não logou,
# tudo o que você escrever aqui embaixo aparecerá APENAS para quem está logado.

sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
es_admin = (st.session_state.get('perfil') == "Admin")

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state.get('perfil')}**")
    if st.button("🚪 Sair"):
        st.session_state['logado'] = False
        st.rerun()

st.title("📦 Sistema de Controle de RMs") # O título só aparece aqui

# Lógica das suas abas
tabs = st.tabs(["📊 Dashboard", "📋 Painel", "➕ Nova RM", "📊 Histórico"]) if es_admin else st.tabs(["📊 Dashboard", "📋 Painel", "📊 Histórico"])

with tabs[0]:
    st.subheader("Resumo Operacional")
    # ... (seu código das abas aqui)
