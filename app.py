import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES E CSS (AJUSTE DE 9 DÍGITOS)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")

st.markdown("""
<style>
    /* Ajuste fixo para os campos de entrada (aproximadamente 9-10 caracteres) */
    .stTextInput > div > div > input {
        width: 150px !important;
        margin: 0 !important;
    }
    /* Centralizar o formulário no lado direito */
    .login-container { display: flex; flex-direction: column; align-items: flex-start; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# FUNÇÕES E LÓGICA
# =====================================================================
def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

# =====================================================================
# LOGIN
# =====================================================================
if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.title("🔑 Login - Sistema de Controle de RMs")
    
    col_esq, col_dir = st.columns([1, 1])
    
    with col_esq:
        st.subheader("Bem-vindo")
        st.write("Utilize suas credenciais para acessar o painel de controle de RMs.")
        
    with col_dir:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        usuario = st.text_input("USUÁRIO:")
        senha = st.text_input("SENHA:", type="password")
        if st.button("ENTRAR"):
            if usuario == "admin" and senha == "12345":
                st.session_state['perfil_logado'] = "Admin"
                st.rerun()
            elif usuario == "visitante" and senha == "123":
                st.session_state['perfil_logado'] = "Visitante"
                st.rerun()
            else: 
                st.error("Usuário ou senha incorretos.")
        st.markdown('</div>', unsafe_allow_html=True)
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
    for _, row in df[df['status'] == 'Aberta'].iterrows():
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
            else: st.write("Acesso restrito.")

if es_admin:
    with tabs[2]:
        with st.form("cad", clear_on_submit=True):
            n, s = st.text_input("Número da RM"), st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                novo_id = max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1
                sheet.append_row([novo_id, n, s, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta"])
                recarregar_dados()

with tabs[-1]: st.dataframe(df, use_container_width=True)
