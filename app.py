import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES E CSS (INTERFACE DARK MODE)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")

def aplicar_estilo():
    st.markdown("""
    <style>
        .stApp { background-color: #121212; color: #FFFFFF; }
        h1, h2, h3, .stMetric, .stDataFrame { text-align: center !important; }
        .metric-card {
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid #333;
            transition: 0.3s;
            margin: 10px;
        }
        .metric-card:hover {
            background-color: #333;
            transform: scale(1.03);
        }
        div.stButton > button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

aplicar_estilo()

CREDENCIAIS = {
    "Admin": {"usuario": "admin", "senha": "12345"},
    "Visitante": {"usuario": "visitante", "senha": "123"}
}

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
    st.title("🔑 Login - Controle de RMs")
    usuario = st.text_input("Usuário:")
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar"):
        if usuario == CREDENCIAIS["Admin"]["usuario"] and senha == CREDENCIAIS["Admin"]["senha"]:
            st.session_state['perfil_logado'] = "Admin"
            st.rerun()
        elif usuario == CREDENCIAIS["Visitante"]["usuario"] and senha == CREDENCIAIS["Visitante"]["senha"]:
            st.session_state['perfil_logado'] = "Visitante"
            st.rerun()
        else: st.error("Usuário ou senha inválidos.")
    st.info("Login Visitante: visitante / 123")
    st.stop()

# =====================================================================
# LÓGICA PRINCIPAL
# =====================================================================
sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
es_admin = (st.session_state['perfil_logado'] == "Admin")

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state['perfil_logado']}**")
    if st.button("🚪 Sair"):
        st.session_state['perfil_logado'] = None
        st.rerun()

st.title("📦 Sistema de Controle de RMs")
tabs = st.tabs(["📊 Dashboard", "📋 Painel", "➕ Nova RM", "📊 Histórico"]) if es_admin else st.tabs(["📊 Dashboard", "📋 Painel", "📊 Histórico"])

# --- DASHBOARD ---
with tabs[0]:
    st.subheader("Resumo Operacional")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><h3>RMs Abertas</h3><h1>{len(df[df["status"] == "Aberta"])}</h1></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h3>RMs Concluídas</h3><h1>{len(df[df["status"] == "Concluída"])}</h1></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h3>Total de RMs</h3><h1>{len(df)}</h1></div>', unsafe_allow_html=True)

# --- PAINEL ---
with tabs[1]:
    st.subheader("Gestão de RMs")
    for _, row in df[df['status'] == 'Aberta
