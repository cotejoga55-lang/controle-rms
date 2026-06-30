import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Controle de RMs", layout="wide")

def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

def formatar_status_tempo(data_entrada, status):
    if status == "Separada":
        return "🟡 **EM PROCESSO DE SEPARAÇÃO**"
    agora = datetime.now()
    diferenca = agora - pd.to_datetime(data_entrada)
    if diferenca > timedelta(hours=24):
        return f"🔴 **ATRASADA (>24h)**"
    else:
        return f"🟢 **NO PRAZO**"

if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None
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
                        st.session_state['perfil_logado'] = "Admin"; st.rerun()
                    elif usuario == "cummins" and senha == "1234":
                        st.session_state['perfil_logado'] = "Visitante"; st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
            st.markdown("<div style='text-align: center;'><small>Se você é um solicitador de RM</small><br><b>usuario: cummins</b><br><b>senha: 1234</b></div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Sistema elaborado por Kevin.</p>", unsafe_allow_html=True)
    st.stop()

sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
df['data_entrada'] = pd.to_datetime(df['data_entrada'], errors='coerce')
df['data_retirada'] = pd.to_datetime(df['data_retirada'], errors='coerce')
es_admin = (st.session_state['perfil_logado'] == "Admin")

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state['perfil_logado']}**")
    if st.button("🚪 Sair"):
        st.session_state['perfil_logado'] = None
        st.rerun()

st.title("📦 Sistema de Controle de RMs")

if es_admin:
    tabs = st.tabs(["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"])
else:
    tabs = st.tabs(["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"])

def mostrar_conteudo(nome_tab):
    if nome_tab == "📊 Dashboard":
        # ... (Mantido o código anterior para Dashboard)
        pass 
    elif nome_tab == "📋 Painel":
        # ... (Mantido o código anterior para Painel)
        pass
    elif nome_tab == "📦 Pend. Retirada":
        # ... (Mantido o código anterior para Pend. Retirada)
        pass
    elif nome_tab == "➕ Nova RM":
        # ... (Mantido o código anterior para Nova RM)
        pass

    elif nome_tab == "🔍 Consulta":
        st.subheader("🔍 Consultar RM")
        # Campo com limite de caracteres
        busca = st.text_input("Digite a RM (8 dígitos):", max_chars=8)
        
        if st.button("Pesquisar"):
            if len(busca) != 8 or not busca.isdigit():
                st.error("Erro: A RM deve conter exatamente 8 dígitos numéricos.")
            else:
                res = df[df['numero_rm'].astype(str) == str(busca).strip()]
                if not res.empty:
                    rm = res.iloc[0]
                    with st.container(border=True):
                        st.write(f"**RM:** {rm['numero_rm']} | **Solicitante:** {rm['solicitante']}")
                        if rm['status'] == 'Aberta':
                            st.write("Status: **Aberta**")
                            if st.button("🔔 Cobrar", key="c_c"):
                                sheet.update_cell(sheet.find(str(rm['id']), in_column=1).row, 9, "COBRADO")
                                st.rerun()
                        elif rm['status'] == 'Separada':
                            st.write("Status: 🟡 **Separada aguardando retirada**")
                        else:
                            st.write(f"Status: **{rm['status']}**")
                else: 
                    st.warning("RM não encontrada.")

    elif nome_tab == "📊 Histórico":
        st.markdown("<h3 style='text-align: center;'>📊 Histórico Completo</h3>", unsafe_allow_html=True)
        col_c = st.columns([1, 8, 1])[1]
        with col_c:
            df_hist = df.copy()
            if not es_admin: df_hist = df_hist[df_hist['status'] == 'Concluída']
            st.markdown(f"<div style='text-align: center;'>{df_hist[['numero_rm', 'data_retirada', 'quem_retirou', 'status']].fillna('Pendente').to_html(index=False)}</div>", unsafe_allow_html=True)
            if es_admin:
                with st.form("d"):
                    sel = {r['id']: st.checkbox(f"RM: {r['numero_rm']}", key=f"d_{r['id']}") for _, r in df.iterrows()}
                    if st.form_submit_button("🗑️ Deletar"):
                        for i, s in sel.items():
                            if s: sheet.delete_rows(sheet.find(str(i), in_column=1).row)
                        recarregar_dados()

if es_admin:
    nomes = ["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"]
else:
    nomes = ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"]

for i, nome in enumerate(nomes):
    with tabs[i]: mostrar_conteudo(nome)
