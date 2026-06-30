import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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

def formatar_status_tempo(data_entrada, status):
    if status == "Separada":
        return "🟡 **EM PROCESSO DE SEPARAÇÃO (AGUARDANDO RETIRADA)**"
    agora = datetime.now()
    diferenca = agora - pd.to_datetime(data_entrada)
    if diferenca > timedelta(hours=24):
        return f"🔴 **ATRASADA (>24h)**"
    else:
        return f"🟢 **NO PRAZO (<24h)**"

# --- LOGIN ---
if 'perfil_logado' not in st.session_state: 
    st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    col1, col_meio, col3 = st.columns([2, 1, 2])
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
                    else:
                        st.error("Usuário ou senha inválidos.")
    st.stop()

# --- LÓGICA E DADOS ---
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
    idx_consulta, idx_historico = 4, 5
else:
    tabs = st.tabs(["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"])
    idx_consulta, idx_historico = 3, 4

# --- ABA 0: DASHBOARD ---
with tabs[0]:
    st.subheader("Resumo Operacional")
    
    # Sino de Notificação
    cobrancas = df[df['cobranca'] == 'COBRADO']
    if len(cobrancas) > 0:
        with st.popover("🔔 NOTIFICAÇÕES PENDENTES"):
            for _, row in cobrancas.iterrows():
                st.warning(f"O NÚMERO DA RM {row['numero_rm']} FOI COBRADA!")
                if st.button(f"Limpar notificação RM {row['numero_rm']}", key=f"clear_{row['id']}"):
                    cell = sheet.find(str(row['id']), in_column=1)
                    sheet.update_cell(cell.row, 9, "")
                    recarregar_dados()
    else:
        st.write("🔔 Sem novas cobranças.")
        
    c1, c2, c3 = st.columns(3)
    c1.metric("RMs em Aberto", len(df[df['status'] == 'Aberta']))
    c2.metric("RMs Concluídas", len(df[df['status'] == 'Concluída']))
    c3.metric("Total de RMs", len(df))

# --- ABA 1: PAINEL ---
with tabs[1]:
    st.subheader("Gestão de RMs em Aberto")
    for _, row in df[df['status'] == 'Aberta'].iterrows():
        cor_status = formatar_status_tempo(row['data_entrada'], row['status'])
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']} | {cor_status}"):
            if es_admin and st.button(f"✅ Marcar como SEPARADA", key=f"sep_{row['id']}"):
                sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 8, "Separada")
                recarregar_dados()

# --- ABA 2: PEND. RETIRADA ---
with tabs[2]:
    st.subheader("RMs Separadas - Aguardando Retirada")
    for _, row in df[df['status'] == 'Separada'].iterrows():
        st.markdown("🟡 **EM PROCESSO DE SEPARAÇÃO (AGUARDANDO RETIRADA)**")
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']}"):
            if es_admin:
                with st.form(f"form_ret_{row['id']}"):
                    quem = st.text_input("Quem retirou?")
                    if st.form_submit_button("Confirmar Retirada"):
                        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cell = sheet.find(str(row['id']), in_column=1)
                        sheet.update(range_name=f"E{cell.row}:H{cell.row}", values=[[agora, agora, quem, "Concluída"]])
                        recarregar_dados()

# --- DEMAIS ABAS ---
if es_admin:
    with tabs[3]:
        with st.form("form_cadastro", clear_on_submit=True):
            num = st.text_input("RM (8 dígitos)", max_chars=8)
            sol = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                if len(num) == 8 and num.isdigit():
                    novo_id = max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1
                    sheet.append_row([novo_id, num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta", ""])
                    recarregar_dados()

with tabs[idx_consulta]:
    st.subheader("🔍 Consultar Status")
    busca = st.text_input("Nº da RM:", key="input_busca")
    if st.button("Pesquisar"):
        res = df[df['numero_rm'].astype(str) == str(busca).strip()]
        if not res.empty:
            rm = res.iloc[0]
            with st.popover("Detalhes", use_container_width=True):
                if rm['status'] == 'Aberta':
                    st.warning("⚠️ STATUS: ABERTA - AGUARDANDO SEPARAÇÃO.")
                    if st.button("🔔 Cobrar esta RM"):
                        cell = sheet.find(str(rm['id']), in_column=1)
                        sheet.update_cell(cell.row, 9, "COBRADO")
                        st.success("Cobrança registrada!")
                        st.rerun()
                else:
                    st.write(f"**RM:** {rm['numero_rm']} | **STATUS:** {rm['status']}")
        else:
            st.error("RM não encontrada.")

with tabs[idx_historico]:
    st.subheader("📊 Histórico Completo")
    st.dataframe(df, use_container_width=True)
    if es_admin:
        with st.form("form_deletar"):
            selecoes = {row['id']: st.checkbox(f"RM: {row['numero_rm']} | ID: {row['id']}", key=f"del_{row['id']}") for _, row in df.iterrows()}
            if st.form_submit_button("🗑️ Deletar Selecionados"):
                for id_rm, sel in selecoes.items():
                    if sel:
                        sheet.delete_rows(sheet.find(str(id_rm), in_column=1).row)
                recarregar_dados()
