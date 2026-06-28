import streamlit as st

import pandas as pd

from datetime import datetime

import gspread

from oauth2client.service_account import ServiceAccountCredentials



# =====================================================================

# CONFIGURAÇÕES E CONEXÃO

# =====================================================================

CREDENCIAIS = {

    "Admin": {"usuario": "admin", "senha": "12345"},

    "Visitante": {"usuario": "visitante", "senha": "123"}

}



def conectar_banco():

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    creds_dict = st.secrets["gcp"]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)



# Função para forçar atualização

def recarregar_dados():

    st.cache_data.clear()

    st.rerun()



# =====================================================================

# INTERFACE E LOGIN

# =====================================================================

import streamlit as st

# Configuração simples
st.set_page_config(page_title="Controle de RMs", layout="centered")

# Lógica de Login
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    # Usamos uma coluna central para criar o efeito de janela flutuante
    # O Streamlit centraliza automaticamente se usarmos um layout equilibrado
    _, col_centro, _ = st.columns([1, 2, 1])
    
    with col_centro:
        st.markdown("<h2 style='text-align: center;'>Controle de RMs</h2>", unsafe_allow_html=True)
        
        # O 'st.form' é a forma nativa e correta de fazer login no Streamlit
        with st.form("login_form"):
            user = st.text_input("Usuário")
            pw = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Fazer Login")
            
            if submitted:
                if user == "admin" and pw == "12345":
                    st.session_state['logado'] = True
                    st.rerun()
                elif user == "visitante" and pw == "123":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos")

        st.info("OBS para visitantes: login: visitante / senha: 123")
    
    st.stop() # Bloqueia o carregamento do restante do site

# Área logada
st.title("📦 Sistema de Controle de RMs")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()



# =====================================================================

# LÓGICA E ABAS

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



# --- ABA 3: NOVA RM (Apenas Admin) ---

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
