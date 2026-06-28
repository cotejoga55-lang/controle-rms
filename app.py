import streamlit as st

# Configuração de Layout
st.set_page_config(page_title="Controle de RMs", layout="wide")

# CSS para forçar a centralização e o tamanho fixo
st.markdown("""
<style>
    .block-container { padding-top: 2rem !important; }
    .stApp { background-color: #1a1a1a; }
    .login-wrapper { display: flex; justify-content: center; align-items: center; height: 80vh; }
    .login-card { background-color: #ffffff; padding: 40px; border-radius: 8px; width: 380px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); text-align: center; }
</style>
""", unsafe_allow_html=True)

# Lógica de Login
if 'logado' not in st.session_state: st.session_state['logado'] = False

# --- TELA DE LOGIN ---
if not st.session_state['logado']:
    st.markdown('<div class="login-wrapper"><div class="login-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='color:#007bff;'>FAZER LOGIN DA CONTA</h2>", unsafe_allow_html=True)
    
    user = st.text_input("Email")
    pw = st.text_input("Senha", type="password")
    
    if st.button("Fazer Login"):
        if user == "admin" and pw == "12345":
            st.session_state['logado'] = True
            st.rerun() # Recarrega para mostrar a tela logada
        else:
            st.error("Credenciais inválidas")
            
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop() # PARA TUDO AQUI

# --- TELA LOGADA (O QUE APARECE DEPOIS) ---
# A partir daqui, o código só roda se logado for True
st.title("📦 Sistema de Controle de RMs")
st.sidebar.success("Bem-vindo!")

# Exemplo de conteúdo logado
tab1, tab2 = st.tabs(["Painel Principal", "Configurações"])

with tab1:
    st.write("Aqui você pode gerenciar suas RMs.")
    # Coloque suas tabelas e lógica de banco de dados aqui
    st.table({"RM": [101, 102], "Status": ["Pendente", "Aprovado"]})

if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()
