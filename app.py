import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Controle de RMs", layout="wide")

# --- FUNÇÕES ---
def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

# --- LOGIN ---
if 'perfil_logado' not in st.session_state:
    st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.title("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario == "admin" and senha == "12345":
            st.session_state['perfil_logado'] = "Admin"
            st.rerun()
        elif usuario == "visitante" and senha == "123":
            st.session_state['perfil_logado'] = "Visitante"
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")
    st.stop()

# --- LÓGICA PRINCIPAL ---
sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
es_admin = (st.session_state['perfil_logado'] == "Admin")

if st.sidebar.button("Sair"):
    st.session_state['perfil_logado'] = None
    st.rerun()

st.title("Controle de RMs")
tabs = st.tabs(["Dashboard", "Painel", "Nova RM", "Histórico"]) if es_admin else st.tabs(["Dashboard", "Painel", "Histórico"])

with tabs[0]:
    st.subheader("Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("RMs em Aberto", len(df[df["status"] == "Aberta"]))
    c2.metric("RMs Concluídas", len(df[df["status"] == "Concluída"]))
    c3.metric("Total de RMs", len(df))

with tabs[1]:
    st.subheader("Painel de RMs")
    for _, row in df[df['status'] == 'Aberta'].iterrows():
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']}"):
            if es_admin:
                if st.button(f"Concluir RM {row['id']}", key=f"btn_{row['id']}"):
                    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cell = sheet.find(str(row['id']), in_column=1)
                    sheet.update(range_name=f"E{cell.row}:H{cell.row}", values=[[agora, agora, "Admin", "Concluída"]])
                    recarregar_dados()
            else:
                st.write("Acesso restrito.")

if es_admin:
    with tabs[2]:
        with st.form("nova_rm", clear_on_submit=True):
            n = st.text_input("Número da RM")
            s = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                novo_id = max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1
                sheet.append_row([novo_id, n, s, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta"])
                recarregar_dados()

with tabs[-1]:
    st.dataframe(df)
