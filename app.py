import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES E CSS
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")

st.markdown("""
<style>
    /* Estilo do Card Flutuante */
    .login-card {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        max-width: 350px;
        margin: 50px auto;
        color: #333;
    }
    /* Limita a largura dos campos (aprox. 13 dígitos) */
    .stTextInput > div > div > input {
        max-width: 200px !important;
    }
    /* Estilo do Botão */
    div.stButton > button {
        width: 100% !important;
        background-color: #007bff !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px !important;
        margin-top: 10px !important;
    }
    h2 { text-align: center; color: #007bff; margin-bottom: 20px; }
    .stApp { background-color: #f0f2f6; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# FUNÇÕES
# =====================================================================
def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

# =====================================================================
# LOGIN
# =====================================================================
if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown("<h2>Controle de RMs</h2>", unsafe_allow_html=True)
    
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Fazer Login"):
        if usuario == "admin" and senha == "12345":
            st.session_state['perfil_logado'] = "Admin"
            st.rerun()
        elif usuario == "visitante" and senha == "123":
            st.session_state['perfil_logado'] = "Visitante"
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
            
    st.markdown("
