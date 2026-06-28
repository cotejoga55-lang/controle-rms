import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES E CSS (DESIGN PERSONALIZADO)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="centered")

st.markdown("""
<style>
    /* Estilo da 'Janela Flutuante' de Login */
    .login-card {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        max-width: 400px;
        margin: 50px auto;
        color: #333;
    }
    /* Limita a largura dos campos para parecerem ter 13 dígitos */
    .stTextInput > div > div > input {
        max-width: 250px !important;
    }
    /* Estilo do Botão Azul */
    div.stButton > button {
        width: 100% !important;
        background-color: #2e7bb0 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        padding: 12px !important;
        border-radius: 5px !important;
        margin-top: 20px !important;
    }
    h2 { text-align: center; color: #2e7bb0; margin-bottom: 25px; }
    .stApp { background-color: #f4f7f6; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# LÓGICA DE LOGIN
# =====================================================================
if 'perfil_logado' not in st.session_state:
    st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    # Cria a janela flutuante
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown("<h2>FAZER LOGIN DA CONTA</h2>", unsafe_allow_html=True)
    
    usuario = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Fazer Login"):
        # Lógica de validação (ajuste conforme necessário)
        if usuario == "admin" and senha == "12345":
            st.session_state['perfil_logado'] = "Admin"
            st.rerun()
        elif usuario == "visitante" and senha == "123":
            st.session_state['perfil_logado'] = "Visitante"
            st.rerun()
        else:
            st.error("Email ou senha incorretos.")
            
    st.markdown("<br><p style='font-size: 13px; color: #555;'><b>OBS:</b><br>Login: visitante<br>Senha: 123</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# SE O LOGIN FOR SUCESSO (ÁREA LOGADA)
# =====================================================================
st.title("📦 Controle de RMs")
# Aqui entra o restante do seu sistema (Dashboard, Painel, etc.)
if st.sidebar.button("🚪 Sair"):
    st.session_state['perfil_logado'] = None
    st.rerun()
