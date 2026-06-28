import streamlit as st

# =====================================================================
# CONFIGURAÇÃO E CSS FINAL (LAYOUT COMPACTO E CENTRALIZADO)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")

st.markdown("""
<style>
    /* Fundo da página */
    .stApp {
        background-color: #1a1a1a;
    }

    /* O Card de Login (A janela branca) */
    .login-box {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 8px;
        width: 400px; /* Largura fixa para manter o visual compacto */
        margin: 50px auto; /* Centraliza a caixa na tela */
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }

    /* Título do Card */
    .login-title {
        color: #2e7bb0;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 25px;
    }

    /* Ajuste para inputs: garante que não se expandam além do container */
    .stTextInput > div > div > input {
        width: 100% !important;
    }

    /* Botão Azul */
    div.stButton > button {
        width: 100% !important;
        background-color: #2e7bb0 !important;
        color: white !important;
        font-weight: bold;
        border: none;
        padding: 12px;
        border-radius: 4px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# LÓGICA DE LOGIN
# =====================================================================
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    # Usamos st.columns para garantir o posicionamento centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">FAZER LOGIN DA CONTA</div>', unsafe_allow_html=True)
        
        usuario = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Fazer Login"):
            if usuario == "admin" and senha == "12345":
                st.session_state['logado'] = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# CONTEÚDO PÓS-LOGIN
# =====================================================================
st.title("📦 Sistema de Controle de RMs")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()
