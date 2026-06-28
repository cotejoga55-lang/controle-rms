import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES E CONEXÃO
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")
st.markdown("""
<style>
    /* Alvo específico para os inputs de texto */
    .stTextInput > div > div > input {
        max-width: 150px !important; /* Aproximadamente 9-10 caracteres */
    }
</style>
""", unsafe_allow_html=True)
CREDENCIAIS = {
    "Admin": {"usuario": "admin", "senha": "12345"},
    "Visitante": {"usuario": "visitante", "senha": "123"}
}

def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

# =====================================================================
# INTERFACE E LOGIN (LAYOUT 2 COLUNAS)
# =====================================================================
if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.title("🔑 Login - Sistema de Controle de RMs")
    
    # Criando as duas colunas para o layout que você desenhou
    col_esq, col_dir = st.columns([1, 1])
    
    with col_esq:
        st.subheader("Bem-vindo")
        st.write("Utilize esta área para acessar o sistema.")
        st.info("Login Visitante: 'visitante' / '123'")
        
    with col_dir:
        usuario = st.text_input("Usuário:")
        senha = st.text_input("Senha:", type="password")
        if st.button("Entrar"):
            # Verificação direta para evitar erros de leitura de dicionário
            if usuario == "admin" and senha == "12345":
                st.session_state['perfil_logado'] = "Admin"
                st.rerun()
            elif usuario == "visitante" and senha == "123":
                st.session_state['perfil_logado'] = "Visitante"
                st.rerun()
            else: 
                st.error("Usuário ou senha inválidos.")
    
    st.stop() # Interrompe a execução para mostrar apenas o login

# =====================================================================
# LÓGICA E ABAS (APÓS LOGIN)
# =====================================================================
sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
es_admin = (st.session_state['perfil_logado'] == "Admin")

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state['perfil_logado']}**")
    if st.button("🚪 Sair"):
        st.session_state['perfil_logado'] = None
        st.rerun()

st.title("📦 Sistema de Controle de RMs")
tabs = st.tabs(["📊 Dashboard", "📋 Painel", "➕ Nova RM", "📊 Histórico"]) if es_admin else st.tabs(["📊 Dashboard", "📋 Painel", "📊 Histórico"])

# --- DASHBOARD ---
with tabs[0]:
    st.subheader("Resumo Operacional")
    col1, col2, col3 = st.columns(3)
    col1.metric("RMs em Aberto", len(df[df['status'] == 'Aberta']))
    col2.metric("RMs Concluídas", len(df[df['status'] == 'Concluída']))
    col3.metric("Total de RMs", len(df))

# --- PAINEL ---
with tabs[1]:
    st.subheader("Gestão de RMs em Aberto")
    abertas = df[df['status'] == 'Aberta']
    for _, row in abertas.iterrows():
        with st.expander(f"RM: {row['numero_rm']} - Solicitante: {row['solicitante']}"):
            if es_admin:
                if st.button(f"✅ Marcar como Concluída", key=f"btn_{row['id']}"):
                    st.session_state[f'concluir_{row["id"]}'] = True
                if st.session_state.get(f'concluir_{row["id"]}'):
                    with st.form(f"form_{row['id']}"):
                        quem = st.text_input("Quem retirou?")
                        if st.form_submit_button("Confirmar"):
                            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            cell = sheet.find(str(row['id']), in_column=1)
                            sheet.update(range_name=f"E{cell.row}:H{cell.row}", values=[[agora, agora, quem, "Concluída"]])
                            recarregar_dados()
            else:
                st.write("Apenas Administradores podem alterar o status.")

# --- NOVA RM ---
if es_admin:
    with tabs[2]:
        with st.form("form_cadastro", clear_on_submit=True):
            num = st.text_input("Número da RM")
            sol = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                novo_id = max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1
                sheet.append_row([novo_id, num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta"])
                st.success("Cadastrado!")
                recarregar_dados()

# --- HISTÓRICO ---
with tabs[-1]:
    st.dataframe(df, use_container_width=True)
