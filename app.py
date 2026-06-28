import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES E CREDENCIAIS
# =====================================================================
CREDENCIAIS = {
    "Admin": {"usuario": "admin", "senha": "12345"},
    "Visitante": {"usuario": "visitante", "senha": "123"}
}

def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gcp"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("controle_rms").get_worksheet(0)
        return sheet
    except Exception as e:
        st.error(f"Erro na conexão com Planilha: {e}")
        st.stop()

def ler_dados(sheet):
    dados = sheet.get_all_records()
    if not dados:
        return pd.DataFrame(columns=['id', 'numero_rm', 'solicitante', 'data_entrada', 'data_saida', 'data_retirada', 'quem_retirou', 'status'])
    return pd.DataFrame(dados)

# =====================================================================
# INTERFACE E LOGIN
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")

if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.title("🔑 Login - Sistema de Controle de RMs")
    col1, _ = st.columns([1, 2])
    with col1:
        usuario = st.text_input("Usuário:")
        senha = st.text_input("Senha:", type="password")
        if st.button("Entrar"):
            if usuario == CREDENCIAIS["Admin"]["usuario"] and senha == CREDENCIAIS["Admin"]["senha"]:
                st.session_state['perfil_logado'] = "Administrador"
                st.rerun()
            elif usuario == CREDENCIAIS["Visitante"]["usuario"] and senha == CREDENCIAIS["Visitante"]["senha"]:
                st.session_state['perfil_logado'] = "Visitante"
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
    st.stop()

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state['perfil_logado']}**")
    if st.button("🚪 Sair"):
        st.session_state['perfil_logado'] = None
        st.rerun()

# =====================================================================
# LÓGICA PRINCIPAL
# =====================================================================
st.title("📦 Sistema de Controle de RMs")
sheet = conectar_banco()
df = ler_dados(sheet)

# Funções de manipulação de dados
def adicionar_rm(n, sol, data, status):
    dados = sheet.get_all_records()
    novo_id = max([int(r['id']) for r in dados if str(r['id']).isdigit()] + [0]) + 1
    sheet.append_row([novo_id, n, sol, data, "", "", "", status])

# Definição das Abas
if st.session_state['perfil_logado'] == "Administrador":
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Painel", "➕ Nova RM", "📊 Histórico", "🛠️ Gerenciamento"])
else:
    tab1, tab3 = st.tabs(["📋 Painel", "📊 Histórico"])

with tab1:
    st.subheader("RMs em Aberto")
    st.dataframe(df[df['status'] == 'Aberta'], use_container_width=True)

with tab3:
    st.subheader("Histórico Geral")
    st.dataframe(df, use_container_width=True)

if st.session_state['perfil_logado'] == "Administrador":
    with tab2:
        st.subheader("Cadastrar Nova RM")
        with st.form("nova_rm"):
            num = st.text_input("Número da RM")
            sol = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                adicionar_rm(num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Aberta")
                st.success("Cadastrada!")
                st.rerun()
    with tab4:
        st.subheader("Configurações Administrativas")
        st.write("Aqui você pode gerenciar dados sensíveis.")
