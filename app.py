import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Controle de RMs", layout="wide")

def aplicar_estilo():
    st.markdown("""
    <style>
        .stApp { background-color: #121212; color: #FFFFFF !important; }
        h1, h2, h3, h4, label, p { color: #FFFFFF !important; text-align: center !important; }
        .stTextInput > div > div > input { max-width: 400px; margin-left: auto; margin-right: auto; display: block; }
        div.stButton > button { width: 200px !important; margin: 0 auto !important; display: block !important;
            background-color: #000000 !important; color: #FFFFFF !important; font-weight: bold !important; border: 2px solid #ffffff !important; }
        .metric-card { background-color: #1e1e1e; padding: 20px; border-radius: 15px;
            text-align: center; border: 1px solid #333; transition: 0.3s; margin: 10px; }
        .metric-card:hover { background-color: #333; transform: scale(1.03); }
        .stDataFrame { color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

aplicar_estilo()

CREDENCIAIS = {"Admin": {"usuario": "admin", "senha": "12345"}, "Visitante": {"usuario": "visitante", "senha": "123"}}

def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.title("🔑 Login - Controle de RMs")
    _, col_centro, _ = st.columns([1, 2, 1])
    with col_centro:
        usuario = st.text_input("Usuário:")
        senha = st.text_input("Senha:", type="password")
        if st.button("ENTRAR"):
            if usuario == CREDENCIAIS["Admin"]["usuario"] and senha == CREDENCIAIS["Admin"]["senha"]:
                st.session_state['perfil_logado'] = "Admin"; st.rerun()
            elif usuario == CREDENCIAIS["Visitante"]["usuario"] and senha == CREDENCIAIS["Visitante"]["senha"]:
                st.session_state['perfil_logado'] = "Visitante"; st.rerun()
            else: st.error("Usuário ou senha inválidos.")
    st.info("Login Visitante: visitante / 123"); st.stop()
    
