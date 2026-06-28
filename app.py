import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÃO DE PÁGINA E CSS (LOGIN CENTRALIZADO)
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
# LÓGICA DE CONEXÃO E ESTADO
# =====================================================================
CREDENCIAIS = {"Admin": {"usuario": "admin", "senha": "12345"}, "Visitante": {"usuario": "visitante", "senha": "123"}}

def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None

# =====================================================================
# TELA DE LOGIN (Isolada para não quebrar o layout)
# =====================================================================
if st.session_state['perfil_logado'] is None:
    st.markdown('<div class="login-wrapper"><div class="login-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='color:#2e7bb0;'>FAZER LOGIN</h2>", unsafe_allow_html=True)
    
    usuario = st.text_input("Usuário:")
    senha = st.text_input("Senha:", type="password")
    
    if st.button("Entrar"):
        if usuario == CREDENCIAIS["Admin"]["usuario"] and senha == CREDENCIAIS["Admin"]["senha"]:
            st.session_state['perfil_logado'] = "Admin"
            st.rerun()
        elif usuario == CREDENCIAIS["Visitante"]["usuario"] and senha == CREDENCIAIS["Visitante"]["senha"]:
            st.session_state['perfil_logado'] = "Visitante"
            st.rerun()
        else: st.error("Usuário ou senha inválidos.")
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop() # Bloqueia o restante do código até o login

# =====================================================================
# SISTEMA DE RMs (CARREGA APÓS LOGIN)
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

# --- ABA 1: DASHBOARD ---
with tabs[0]:
    st.subheader("Resumo Operacional")
    col1, col2, col3 = st.columns(3)
    col1.metric("RMs em Aberto", len(df[df['status'] == 'Aberta']))
    col2.metric("RMs Concluídas", len(df[df['status'] == 'Concluída']))
    col3.metric("Total de RMs", len(df))

# --- ABA 2: PAINEL ---
with tabs[1]:
    st.subheader("Gestão de RMs em Aberto")
    abertas = df[df['status'] == 'Aberta']
    for _, row in abertas.iterrows():
        with st.expander(f"RM: {row['numero_rm']} - Solicitante: {row['solicitante']}"):
            if es_admin:
                if st.button(f"✅ Concluir RM {row['numero_rm']}", key=f"btn_{row['id']}"):
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

# --- ABA 3: NOVA RM ---
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

# --- ABA FINAL: HISTÓRICO ---
with tabs[-1]:
    st.dataframe(df, use_container_width=True)
