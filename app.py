import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CSS FORÇADO (Otimizado para o seu desenho)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="centered")

st.markdown("""
<style>
    /* O container principal que centraliza tudo */
    .main-login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
    }
    
    /* A caixa de login em si */
    .login-box {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        width: 350px !important; /* Largura fixa como no seu desenho */
        text-align: center;
        border: 1px solid #ddd;
    }
    
    /* Força os inputs a terem tamanho consistente */
    .stTextInput > div > div > input {
        width: 100% !important;
        text-align: center;
    }
    
    /* Botão Azul */
    div.stButton > button {
        width: 100% !important;
        background-color: #2e7bb0 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 5px !important;
        margin-top: 20px !important;
    }
    
    h2 { color: #2e7bb0; margin-bottom: 25px; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# LÓGICA DE LOGIN
# =====================================================================
if 'perfil_logado' not in st.session_state:
    st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.markdown('<div class="main-login-wrapper"><div class="login-box">', unsafe_allow_html=True)
    st.markdown("<h2>FAZER LOGIN DA CONTA</h2>", unsafe_allow_html=True)
    
    usuario = st.text_input("Email", placeholder="Digite seu usuário")
    senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
    
    if st.button("Fazer Login"):
        if usuario == "admin" and senha == "12345":
            st.session_state['perfil_logado'] = "Admin"
            st.rerun()
        elif usuario == "visitante" and senha == "123":
            st.session_state['perfil_logado'] = "Visitante"
            st.rerun()
        else:
            st.error("Credenciais inválidas.")
            
    st.markdown("""
        <div style='margin-top: 20px; font-size: 12px; color: #777;'>
        OBS: Visitante: visitante / 123
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# ÁREA LOGADA
# =====================================================================
st.title("📦 Controle de RMs")
if st.sidebar.button("🚪 Sair"):
    st.session_state['perfil_logado'] = None
    st.rerun()
