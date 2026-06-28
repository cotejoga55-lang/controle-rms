import streamlit as st

# Configuração da página para limpar o layout
st.set_page_config(page_title="Controle de RMs", layout="wide")

# CSS para forçar o tamanho fixo da janela e centralizar
st.markdown("""
<style>
    /* Esconde o menu lateral e cabeçalho padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Fundo da tela */
    .stApp {
        background-color: #1a1a1a;
    }
    
    /* Container centralizador */
    .login-page-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        width: 100vw;
    }
    
    /* A JANELA FLUTUANTE (CARD) */
    .login-card {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 10px;
        width: 400px; /* Largura fixa */
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        text-align: center;
    }

    /* Título */
    h2 {
        color: #2e7bb0;
        margin-bottom: 25px;
        font-size: 24px;
    }

    /* Inputs fixos */
    .stTextInput input {
        width: 100% !important;
    }
    
    /* Botão Azul */
    div.stButton > button {
        width: 100% !important;
        background-color: #2e7bb0 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Lógica de Login
if 'logado' not in st.session_state: st.session_state['logado'] = False

if not st.session_state['logado']:
    # Envolve o formulário na nossa div customizada
    st.markdown('<div class="login-page-container"><div class="login-card">', unsafe_allow_html=True)
    st.markdown("<h2>FAZER LOGIN DA CONTA</h2>", unsafe_allow_html=True)
    
    user = st.text_input("Email")
    pw = st.text_input("Senha", type="password")
    
    if st.button("Fazer Login"):
        if user == "admin" and pw == "12345":
            st.session_state['logado'] = True
            st.rerun()
        else:
            st.error("Credenciais incorretas")
            
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop() # Bloqueia o restante da página se não estiver logado

# Conteúdo após login
st.title("📦 Sistema de Controle de RMs")
