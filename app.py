import streamlit as st

# Configuração simples
st.set_page_config(page_title="Controle de RMs", layout="centered")

# Lógica de Login
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    # Usamos uma coluna central para criar o efeito de janela flutuante
    # O Streamlit centraliza automaticamente se usarmos um layout equilibrado
    _, col_centro, _ = st.columns([1, 2, 1])
    
    with col_centro:
        st.markdown("<h2 style='text-align: center;'>Controle de RMs</h2>", unsafe_allow_html=True)
        
        # O 'st.form' é a forma nativa e correta de fazer login no Streamlit
        with st.form("login_form"):
            user = st.text_input("Usuário")
            pw = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Fazer Login")
            
            if submitted:
                if user == "admin" and pw == "12345":
                    st.session_state['logado'] = True
                    st.rerun()
                elif user == "visitante" and pw == "123":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos")

        st.info("OBS para visitantes: login: visitante / senha: 123")
    
    st.stop() # Bloqueia o carregamento do restante do site

# Área logada
st.title("📦 Sistema de Controle de RMs")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()
