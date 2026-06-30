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

# Função de Cores para o Tempo
def formatar_status_tempo(data_entrada, status):
    if status == "Separada":
        return "🟡 **EM PROCESSO DE RETIRADA**"
    
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
    pendentes = df[df['status'] == 'Separada']
    vencidas_48h = pendentes[pd.to_datetime(pendentes['data_entrada']) < (datetime.now() - timedelta(hours=48))]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RMs em Aberto", len(df[df['status'] == 'Aberta']))
    c2.metric("Aguardando Retirada", len(pendentes))
    c3.metric("RMs Concluídas", len(df[df['status'] == 'Concluída']))
    c4.metric("Vencidas (>48h)", len(vencidas_48h))
    
    if not vencidas_48h.empty:
        st.error(f"🚨 {len(vencidas_48h)} RMs pendentes de retirada há mais de 48h!")

# --- ABA 1: PAINEL (Separação) ---
with tabs[1]:
    st.subheader("Gestão de RMs em Aberto")
    for _, row in df[df['status'] == 'Aberta'].iterrows():
        # Aplica a cor baseada no tempo
        cor_status = formatar_status_tempo(row['data_entrada'], row['status'])
        with st.expander(f"RM: {row['numero_rm']} | {cor_status}"):
            st.write(f"**Solicitante:** {row['solicitante']} | **Entrada:** {row['data_entrada']}")
            if es_admin and st.button(f"✅ Marcar como SEPARADA", key=f"sep_{row['id']}"):
                sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 8, "Separada")
                recarregar_dados()

# --- ABA 2: PEND. RETIRADA (Amarelo) ---
with tabs[2]:
    st.subheader("RMs em Processo de Separação")
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

# --- ABAS 3, 4 e 5: NOVA RM, CONSULTA, HISTÓRICO ---
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

with tabs[idx_consulta]:
    busca = st.text_input("Nº da RM:")
    if st.button("Pesquisar"):
        res = df[df['numero_rm'].astype(str) == str(busca).strip()]
        if not res.empty:
            st.success("RM encontrada!")
            st.write(res.iloc[0])

with tabs[idx_historico]:
    st.dataframe(df, use_container_width=True)
    if es_admin:
        with st.form("form_del"):
            sel = {r['id']: st.checkbox(f"RM {r['numero_rm']}", key=r['id']) for _, r in df.iterrows()}
            if st.form_submit_button("🗑️ Deletar"):
                for i, s in sel.items():
                    if s: sheet.delete_rows(sheet.find(str(i), in_column=1).row)
                recarregar_dados()
