import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. CONFIGURAÇÕES INICIAIS
st.set_page_config(page_title="Controle de RMs", layout="wide")

# 2. LÓGICA DE ESTADO
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
    st.session_state['perfil'] = None

# =====================================================================
# BLOCO 1: TELA DE LOGIN
# =====================================================================
if not st.session_state['logado']:
    _, col_centro, _ = st.columns([1, 2, 1])
    with col_centro:
        st.markdown("<h2 style='text-align: center;'>Controle de RMs</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            user = st.text_input("Usuário")
            pw = st.text_input("Senha", type="password")
            if st.form_submit_button("Fazer Login"):
                if (user == "admin" and pw == "12345"):
                    st.session_state['logado'] = True
                    st.session_state['perfil'] = "Admin"
                    st.rerun()
                elif (user == "visitante" and pw == "123"):
                    st.session_state['logado'] = True
                    st.session_state['perfil'] = "Visitante"
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos")
    
    # IMPORTANTE: st.stop() aqui garante que NADA abaixo seja lido
    st.stop() 

# =====================================================================
# BLOCO 2: ÁREA LOGADA (Só é lido se o código passar do st.stop() acima)
# =====================================================================

# FUNÇÕES DE BANCO (Só rodam depois de logar)
def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

# CARREGA DADOS APENAS APÓS O LOGIN
sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
es_admin = (st.session_state['perfil'] == "Admin")

# INTERFACE LOGADA
st.title("📦 Sistema de Controle de RMs")

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state['perfil']}**")
    if st.button("🚪 Sair"):
        st.session_state['logado'] = False
        st.rerun()

tabs = st.tabs(["📊 Dashboard", "📋 Painel", "➕ Nova RM", "📊 Histórico"]) if es_admin else st.tabs(["📊 Dashboard", "📋 Painel", "📊 Histórico"])

# --- (O RESTO DO SEU CÓDIGO DE ABAS VAI AQUI) ---
with tabs[0]:
    st.subheader("Resumo Operacional")
    # ... resto do código ...
