import streamlit as st

# =====================================================================
# CONFIGURAÇÃO E CSS FINAL (LAYOUT AJUSTÁVEL)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="centered")

st.markdown("""
<style>
    /* Fundo da página */
    .stApp {
        background-color: #1a1a1a;
    }

    /* Container pai para centralizar o conteúdo */
    .outer-wrapper {
        display: flex;
        justify-content: center;
        padding-top: 50px;
    }

    /* A Janela Flutuante (Card) que se ajusta ao conteúdo */
    .login-box {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        display: inline-block; 
        min-width: 350px;      
        max-width: 90%;        
    }

    /* Título */
    .login-title {
        color: #2e7bb0;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 25px;
        text-align: center;
    }

    /* Inputs compactos */
    .stTextInput > div > div > input {
        width: 100% !important;
        max-width: 300px !important;
    }

    /* Botão Azul */
    div.stButton > button {
        width: 100% !important;
        background-color: #2e7bb0 !important;
        color: white !important;
        padding: 10px;
        border-radius: 4px;
        border: none;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# LÓGICA DE LOGIN
# =====================================================================
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.markdown('<div class="outer-wrapper"><div class="login-box">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">FAZER LOGIN DA CONTA</div>', unsafe_allow_html=True)
    
    usuario = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Fazer Login"):
        if usuario == "admin" and senha == "12345":
            st.session_state['logado'] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
            
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# ÁREA LOGADA
# =====================================================================
st.title("📦 Sistema de Controle de RMs")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()
