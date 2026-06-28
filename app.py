import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO E CSS FINAL ---
st.set_page_config(page_title="Controle de RMs", layout="centered")

st.markdown("""
<style>
    /* Janela Flutuante (Card) */
    .login-box {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        max-width: 380px;
        margin: 50px auto;
        border: 1px solid #e0e0e0;
    }
    /* Campos de input com largura fixa (aprox. 13 dígitos) */
    .stTextInput > div > div > input {
        max-width: 250px !important;
    }
    /* Botão azul robusto */
    div.stButton > button {
        width: 100% !important;
        background-color: #2e7bb0 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        padding: 12px !important;
        border-radius: 5px !important;
        margin-top: 15px !important;
    }
    h2 { color: #2e7bb0; text-align: center; margin-bottom: 25px; }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE LOGIN ---
if 'perfil_logado' not in st.session_state:
    st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("<h2>FAZER LOGIN DA CONTA</h2>", unsafe_allow_html=True)
    
    usuario = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Fazer Login"):
        if usuario == "admin" and senha == "12345":
            st.session_state['perfil_logado'] = "Admin"
            st.rerun()
        elif usuario == "visitante" and senha == "123":
            st.session_state['perfil_logado'] = "Visitante"
            st.rerun()
        else:
            st.error("Dados inválidos.")
            
    st.markdown("<br><p style='font-size: 12px; color: #777;'><b>OBS:</b><br>Login: visitante<br>Senha: 123</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- ÁREA LOGADA ---
# (Seu código de Dashboard, Painel, etc., vem aqui)
st.title("📦 Controle de RMs")
if st.sidebar.button("🚪 Sair"):
    st.session_state['perfil_logado'] = None
    st.rerun()
