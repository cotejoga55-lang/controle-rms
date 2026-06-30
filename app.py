import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÕES E CONEXÃO ---
st.set_page_config(page_title="Controle de RMs", layout="wide")

def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

# --- LOGIN ---
if 'perfil_logado' not in st.session_state: 
    st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    col_meio = st.columns([2, 1, 2])[1]
    with col_meio:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>🔑 Login</h3>", unsafe_allow_html=True)
            with st.form("login_form"):
                usuario = st.text_input("Usuário:")
                senha = st.text_input("Senha:", type="password")
                if st.form_submit_button("Entrar", use_container_width=True):
                    if usuario == "pdc" and senha == "123":
                        st.session_state['perfil_logado'] = "Admin"
                        st.rerun()
                    elif usuario == "visitante" and senha == "123":
                        st.session_state['perfil_logado'] = "Visitante"
                        st.rerun()
                    else:
                        st.error("Usuário ou senha inválidos.")
    st.stop()

# --- DADOS ---
sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
es_admin = (st.session_state['perfil_logado'] == "Admin")

# --- ABAS ---
if es_admin:
    tabs = st.tabs(["📊 Dash", "📋 Aberto", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"])
    idx_consulta, idx_historico = 4, 5
else:
    tabs = st.tabs(["📊 Dash", "📋 Aberto", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"])
    idx_consulta, idx_historico = 3, 4

# --- ABA 0: DASH ---
with tabs[0]:
    st.metric("Total de RMs", len(df))

# --- ABA 1: ABERTO (Para separar) ---
with tabs[1]:
    st.subheader("RMs para Separar")
    for _, row in df[df['status'] == 'Aberta'].iterrows():
        with st.expander(f"RM: {row['numero_rm']}"):
            if es_admin:
                if st.button("✅ Marcar como SEPARADA", key=f"sep_{row['id']}"):
                    cell = sheet.find(str(row['id']), in_column=1)
                    sheet.update_cell(cell.row, 8, "Separada")
                    recarregar_dados()

# --- ABA 2: PENDENTE DE RETIRADA ---
with tabs[2]:
    st.subheader("RMs Separadas - Aguardando Retirada")
    for _, row in df[df['status'] == 'Separada'].iterrows():
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']}"):
            if es_admin:
                with st.form(f"form_ret_{row['id']}"):
                    quem = st.text_input("Quem retirou?")
                    if st.form_submit_button("Confirmar Retirada"):
                        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cell = sheet.find(str(row['id']), in_column=1)
                        # Atualiza: Data Retirada, Quem Retirou, Status
                        sheet.update(range_name=f"E{cell.row}:H{cell.row}", values=[[agora, agora, quem, "Concluída"]])
                        recarregar_dados()

# --- ABA 3: NOVA RM ---
if es_admin:
    with tabs[3]:
        with st.form("form_cadastro", clear_on_submit=True):
            num = st.text_input("RM (8 dígitos)", max_chars=8)
            sol = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                if len(num) == 8 and num.isdigit():
                    novo_id = max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1
                    sheet.append_row([novo_id, num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta"])
                    recarregar_dados()

# --- ABA 4/5: CONSULTA ---
with tabs[idx_consulta]:
    busca = st.text_input("Nº da RM:")
    if st.button("Pesquisar"):
        res = df[df['numero_rm'].astype(str) == str(busca)]
        if not res.empty:
            rm = res.iloc[0]
            val = lambda x: x if (x and str(x).strip() != "") else "PENDENTE"
            st.write(f"**RM:** {val(rm['numero_rm'])} | **Status:** {val(rm['status'])}")
            st.write(f"**SOLICITANTE:** {val(rm['solicitante'])}")
            st.write(f"**DATA SEPARAÇÃO:** {val(rm['data_entrada'])}")
            st.write(f"**DATA RETIRADA:** {val(rm['data_retirada'])}")
            st.write(f"**QUEM RETIROU:** {val(rm['quem_retirou'])}")

# --- ABA FINAL: HISTÓRICO ---
with tabs[idx_historico]:
    st.dataframe(df, use_container_width=True)
