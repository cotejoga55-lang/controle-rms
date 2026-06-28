import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO E CSS ---
st.set_page_config(page_title="Controle de RMs", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #121212; color: #FFFFFF !important; }
    h1, h2, h3, h4, label, p { color: #FFFFFF !important; text-align: center !important; }
    .stTextInput > div > div > input { max-width: 400px; margin-left: auto; margin-right: auto; display: block; }
    div.stButton > button { 
        width: 200px !important; margin: 0 auto !important; display: block !important;
        background-color: #000000 !important; color: #FFFFFF !important;
        font-weight: bold !important; border: 2px solid #ffffff !important;
    }
    .metric-card { background-color: #1e1e1e; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #333; transition: 0.3s; margin: 10px; }
    .metric-card:hover { background-color: #333; transform: scale(1.03); }
    .stDataFrame { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

# --- LÓGICA DE LOGIN ---
if 'perfil_logado' not in st.session_state:
    st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.title("🔑 Login - Controle de RMs")
    usuario = st.text_input("Usuário:")
    senha = st.text_input("Senha:", type="password")
    
    if st.button("ENTRAR"):
        if usuario == "admin" and senha == "12345":
            st.session_state['perfil_logado'] = "Admin"
            st.rerun()
        elif usuario == "visitante" and senha == "123":
            st.session_state['perfil_logado'] = "Visitante"
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# --- LÓGICA PRINCIPAL (APÓS LOGIN) ---
sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
es_admin = (st.session_state['perfil_logado'] == "Admin")

if st.sidebar.button("🚪 Sair"):
    st.session_state['perfil_logado'] = None
    st.rerun()

st.title("📦 Sistema de Controle de RMs")
tabs = st.tabs(["📊 Dashboard", "📋 Painel", "➕ Nova RM", "📊 Histórico"]) if es_admin else st.tabs(["📊 Dashboard", "📋 Painel", "📊 Histórico"])

with tabs[0]:
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><h3>RMs Abertas</h3><h1>{len(df[df["status"] == "Aberta"])}</h1></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h3>RMs Concluídas</h3><h1>{len(df[df["status"] == "Concluída"])}</h1></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h3>Total de RMs</h3><h1>{len(df)}</h1></div>', unsafe_allow_html=True)

with tabs[1]:
    for _, row in df[df['status'] == 'Aberta'].iterrows():
        id_rm = str(row['id'])
        with st.expander(f"RM: {row['numero_rm']} | Solicitante: {row['solicitante']}"):
            if es_admin:
                if st.button(f"✅ Concluir RM {id_rm}", key=f"btn_{id_rm}"):
                    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cell = sheet.find(id_rm, in_column=1)
                    sheet.update(range_name=f"E{cell.row}:H{cell.row}", values=[[agora, agora, "Admin", "Concluída"]])
                    recarregar_dados()
            else: 
                st.write("Apenas Administradores podem concluir.")

if es_admin:
    with tabs[2]:
        with st.form("cad", clear_on_submit=True):
            n, s = st.text_input("Número da RM"), st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                novo_id = max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1
                sheet.append_row([novo_id, n, s, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta"])
                recarregar_dados()

with tabs[-1]: 
    st.dataframe(df, use_container_width=True)
