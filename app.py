import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES E CSS (LAYOUT COMPACTO)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")

st.markdown("""
<style>
    /* Limita a largura dos inputs para simular o tamanho de 9-10 dígitos */
    .stTextInput > div > div > input {
        max-width: 150px !important;
    }
    /* Centraliza o container de login */
    .login-box {
        max-width: 300px;
        margin: 0 auto;
        padding: 20px;
        border: 1px solid #333;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# FUNÇÕES
# =====================================================================
def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

# =====================================================================
# LOGIN
# =====================================================================
if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.title("FAZER LOGIN DA CONTA")
    
    with st.container():
        usuario = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Fazer Login"):
            if usuario == "admin" and senha == "12345":
                st.session_state['perfil_logado'] = "Admin"
                st.rerun()
            elif usuario == "visitante" and senha == "123":
                st.session_state['perfil_logado'] = "Visitante"
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    st.stop()

# =====================================================================
# ÁREA LOGADA
# =====================================================================
sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
es_admin = (st.session_state['perfil_logado'] == "Admin")

if st.sidebar.button("🚪 Sair"):
    st.session_state['perfil_logado'] = None
    st.rerun()

st.title("📦 Sistema de Controle de RMs")
tabs = st.tabs(["📊 Dashboard", "📋 Painel", "➕ Nova RM", "📊 Histórico"]) if es_admin else st.tabs(["📊 Dashboard", "📋 Painel", "📊 Histórico"])

with tabs[0]:
    st.subheader("Resumo Operacional")
    c1, c2, c3 = st.columns(3)
    c1.metric("RMs em Aberto", len(df[df['status'] == 'Aberta']))
    c2.metric("RMs Concluídas", len(df[df['status'] == 'Concluída']))
    c3.metric("Total de RMs", len(df))

with tabs[1]:
    st.subheader("Gestão de RMs em Aberto")
    abertas = df[df['status'] == 'Aberta']
    for _, row in abertas.iterrows():
        with st.expander(f"RM: {row['numero_rm']} - Solicitante: {row['solicitante']}"):
            if es_admin:
                if st.button(f"✅ Concluir", key=f"btn_{row['id']}"):
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
                st.write("Acesso restrito.")

if es_admin:
    with tabs[2]:
        with st.form("cad", clear_on_submit=True):
            n = st.text_input("Número da RM")
            s = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                novo_id = max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1
                sheet.append_row([novo_id, n, s, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta"])
                recarregar_dados()

with tabs[-1]:
    st.dataframe(df, use_container_width=True)
