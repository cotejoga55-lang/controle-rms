import streamlit as st

# =====================================================================
# CONFIGURAÇÃO DE PÁGINA
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="centered")

# =====================================================================
# CSS CUSTOMIZADO PARA O VISUAL COMPACTO
# =====================================================================
st.markdown("""
<style>
    /* Fundo da página */
    .stApp {
        background-color: #1a1a1a;
    }

    /* Estilo do Card (A "Janela Flutuante") */
    .login-box {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        width: 100%;
        max-width: 400px; /* Define a largura máxima da janela */
        margin: 50px auto; /* Centraliza a janela na página */
    }

    /* Estilo do Título dentro da caixa */
    .login-title {
        color: #2e7bb0;
        text-align: center;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 25px;
    }

    /* Força os inputs a respeitarem a largura do card */
    .stTextInput > div > div > input {
        width: 100% !important;
    }

    /* Botão Azul Estilizado */
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
# LÓGICA DE LOGIN (SESSION STATE)
# =====================================================================
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

# Se NÃO estiver logado, exibe o formulário centralizado
if not st.session_state['logado']:
    # Usamos colunas vazias para centralizar o bloco da login-box
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">FAZER LOGIN DA CONTA</div>', unsafe_allow_html=True)
        
        usuario = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Fazer Login"):
            # Lógica de validação simples
            if usuario == "admin" and senha == "12345":
                st.session_state['logado'] = True
                st.rerun()
            else:
                st.error("Email ou senha incorretos.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Impede que o restante do app seja renderizado antes do login
    st.stop()

# =====================================================================
# CONTEÚDO PÓS-LOGIN (Área Logada)
# =====================================================================
st.title("📦 Sistema de Controle de RMs")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()
