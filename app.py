import streamlit as st

# =====================================================================
# CONFIGURAÇÃO E CSS RADICAL (PARA MANTER O LAYOUT FIXO)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")

st.markdown("""
<style>
    /* Esconde o menu do Streamlit para deixar o visual limpo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Força o fundo da página inteira */
    .stApp {
        background-color: #1a1a1a; 
    }

    /* O Card de Login - Centralizado e com largura fixa */
    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 80vh;
    }
    
    .login-box {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 8px;
        width: 400px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }

    /* Ajuste fino dos inputs dentro do card */
    .stTextInput > div > div > input {
        width: 100% !important;
        padding: 10px !important;
    }

    /* Botão estilizado */
    div.stButton > button {
        width: 100% !important;
        background-color: #2e7bb0 !important;
        color: white !important;
        font-weight: bold;
        border: none;
        padding: 12px;
        border-radius: 4px;
        margin-top: 10px;
    }
    
    h2 { color: #2e7bb0; text-align: center; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# ESTRUTURA DO LOGIN
# =====================================================================
if 'logado' not in st.session_state: st.session_state['logado'] = False

if not st.session_state['logado']:
    st.markdown('<div class="login-wrapper"><div class="login-box">', unsafe_allow_html=True)
    st.markdown("<h2>FAZER LOGIN DA CONTA</h2>", unsafe_allow_html=True)
    
    usuario = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Fazer Login"):
        if usuario == "admin" and senha == "12345":
            st.session_state['logado'] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
            
    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

# =====================================================================
# CONTEÚDO PÓS-LOGIN
# =====================================================================
st.title("📦 Sistema de Controle de RMs")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()
