import streamlit as st

# 1. CONFIGURAÇÃO E CSS (Oculta o que não deve aparecer na tela de login)
st.set_page_config(page_title="Controle de RMs", layout="wide")

st.markdown("""
<style>
    /* Esconde elementos do Streamlit para manter o design limpo */
    #MainMenu, header, footer {visibility: hidden;}
    .stApp {background-color: #1a1a1a;}
    
    /* Centralizador da caixa de login */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 80vh;
    }
    .login-box {
        background: white;
        padding: 30px;
        border-radius: 8px;
        width: 350px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# 2. LÓGICA DE ESTADO (Login)
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

# 3. TELA DE LOGIN (Mostra apenas se NÃO estiver logado)
if not st.session_state['logado']:
    st.markdown('<div class="login-container"><div class="login-box">', unsafe_allow_html=True)
    st.markdown("### FAZER LOGIN DA CONTA")
    
    usuario = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Fazer Login"):
        if usuario == "admin" and senha == "12345":
            st.session_state['logado'] = True
            st.rerun()
        else:
            st.error("Dados incorretos!")
            
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop() # PARA A EXECUÇÃO AQUI, O RESTO NÃO APARECE

# 4. ÁREA LOGADA (Só aparece se o Login for validado)
st.title("📦 Sistema de Controle de RMs")

# Exemplo de como organizar seu conteúdo aqui
abas = st.tabs(["Dashboard", "Painel de RMs", "Configurações"])

with abas[0]:
    st.subheader("Visão Geral")
    st.write("Seu painel administrativo vai aqui.")

with abas[1]:
    st.subheader("Gerenciamento de RMs")
    # Sua lógica de tabelas, banco de dados, etc...
    
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()
