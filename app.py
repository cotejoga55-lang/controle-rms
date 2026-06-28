import streamlit as st

# Ocultar elementos padrão do Streamlit que esticam o layout
st.markdown("""
<style>
    /* Esconde o menu e o cabeçalho do Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Fundo escuro */
    .stApp {
        background-color: #1a1a1a;
    }
    
    /* Container que centraliza o card */
    .outer-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        width: 100vw;
    }

    /* O CARD FIXO - AQUI ESTÁ O SEGREDO DO TAMANHO */
    .fixed-login-card {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 10px;
        width: 400px; /* Tamanho fixo, não estica */
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        text-align: center;
    }

    /* Força os inputs a não ultrapassarem o card */
    .stTextInput input {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# Lógica de Login
if 'logado' not in st.session_state: st.session_state['logado'] = False

if not st.session_state['logado']:
    # Usamos HTML puro para criar a estrutura e evitar o layout do Streamlit
    st.markdown('<div class="outer-container"><div class="fixed-login-card">', unsafe_allow_html=True)
    st.markdown("<h3>FAZER LOGIN DA CONTA</h3>", unsafe_allow_html=True)
    
    # Inputs
    user = st.text_input("Email")
    pw = st.text_input("Senha", type="password")
    
    if st.button("Fazer Login"):
        if user == "admin" and pw == "12345":
            st.session_state['logado'] = True
            st.rerun()
        else:
            st.error("Credenciais inválidas")
            
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()
