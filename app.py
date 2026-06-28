import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES E CSS (LAYOUT FLEXÍVEL)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="centered")

st.markdown("""
<style>
    /* O card agora se ajusta automaticamente ao conteúdo (auto) */
    .login-box {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        width: 100%;
        max-width: 450px; 
        margin: 50px auto;
        border: 1px solid #e0e0e0;
        box-sizing: border-box;
    }
    /* Campos de input ocupam o espaço disponível, mas mantêm o visual de 13 dígitos */
    .stTextInput > div > div > input {
        width: 100% !important;
    }
    /* Botão estilizado */
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
    h2 { color: #2e7bb0; text-align: center; margin-bottom: 30px; font-size: 24px; }
    .stApp { background-color: #f4f7f6; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# LÓGICA DE LOGIN
# =====================================================================
if 'perfil_logado' not in st.session_state:
    st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    # Div container para envolver todo o conteúdo do login
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
            
    st.markdown("""
        <div style='margin-top: 25px; font-size: 13px; color: #666; border-top: 1px solid #eee; padding-top: 15px;'>
        <b>OBS para visitantes:</b><br>Login: visitante<br>Senha: 123
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# ÁREA LOGADA
# =====================================================================
st.title("📦 Controle de RMs")
if st.sidebar.button("🚪 Sair"):
    st.session_state['perfil_logado'] = None
    st.rerun()
