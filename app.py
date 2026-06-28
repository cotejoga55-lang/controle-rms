import streamlit as st

# =====================================================================
# CONFIGURAÇÃO DE PÁGINA E CSS (FIXO E ESTÁVEL)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")

st.markdown("""
<style>
    .stApp {background-color: #1a1a1a;}
    .login-wrapper { display: flex; justify-content: center; align-items: center; height: 80vh; }
    .login-card { 
        background-color: #ffffff; 
        padding: 40px; 
        border-radius: 8px; 
        width: 380px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# LÓGICA DE LOGIN (VALIDADA E CENTRALIZADA)
# =====================================================================
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.markdown('<div class="login-wrapper"><div class="login-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='color:#2e7bb0;'>FAZER LOGIN DA CONTA</h2>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        user = st.text_input("Email")
        pw = st.text_input("Senha", type="password")
        if st.form_submit_button("Fazer Login"):
            if user == "admin" and pw == "12345":
                st.session_state['logado'] = True
                st.rerun()
            else:
                st.error("Credenciais inválidas")
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop() 

# =====================================================================
# SISTEMA DE RMs (O QUE VOCÊ VAI FAZER LÁ DENTRO)
# =====================================================================
st.title("📦 Sistema de Controle de RMs")

# Estrutura funcional que você vai preencher com sua lógica de banco de dados
tabs = st.tabs(["Dashboard Geral", "Gestão de RMs", "Automação (n8n)", "Configurações"])

with tabs[0]: # Dashboard
    st.subheader("Visão Geral de Performance")
    col1, col2, col3 = st.columns(3)
    col1.metric("RMs Pendentes", "12")
    col2.metric("Processadas Hoje", "8")
    col3.metric("Tempo Médio", "02:30")

with tabs[1]: # Gestão
    st.subheader("Banco de Dados de RMs")
    st.write("Aqui você integra o seu Excel/SQL.")
    # Exemplo de interação que você vai colocar:
    # df = carregar_dados_sql()
    # st.dataframe(df)

with tabs[2]: # Automação
    st.subheader("Conexão com n8n")
    st.write("Status do Webhook: Conectado ✅")
    st.button("Executar Sincronização Manual")

with tabs[3]: # Configurações
    st.subheader("Preferências")
    if st.button("Sair da Conta"):
        st.session_state['logado'] = False
        st.rerun()
