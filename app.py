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
                entrar = st.form_submit_button("Entrar", use_container_width=True)
                if entrar:
                    if usuario == "pdc" and senha == "123":
                        st.session_state['perfil_logado'] = "Admin"
                        st.rerun()
                    elif usuario == "visitante" and senha == "123":
                        st.session_state['perfil_logado'] = "Visitante"
                        st.rerun()
                    else:
                        st.error("Usuário ou senha inválidos.")
    st.stop()

# --- LÓGICA E DADOS ---
sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
es_admin = (st.session_state['perfil_logado'] == "Admin")

# Conversão de datas para cálculo
df['data_entrada'] = pd.to_datetime(df['data_entrada'], errors='coerce')
df['data_retirada'] = pd.to_datetime(df['data_retirada'], errors='coerce')

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
    
    # Cálculos de Alerta
    pendentes = df[df['status'] == 'Separada']
    agora = datetime.now()
    vencidas = pendentes[pendentes['data_entrada'] < (agora - timedelta(hours=48))]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RMs em Aberto", len(df[df['status'] == 'Aberta']))
    c2.metric("Aguardando Retirada", len(pendentes))
    c3.metric("RMs Concluídas", len(df[df['status'] == 'Concluída']))
    c4.metric("RMs Vencidas (>48h)", len(vencidas), delta_color="inverse")
    
    if len(vencidas) > 0:
        st.error(f"🚨 ATENÇÃO: Existem {len(vencidas)} RMs aguardando retirada há mais de 48 horas!")
        st.dataframe(vencidas[['numero_rm', 'solicitante', 'data_entrada']], use_container_width=True)
    
    st.divider()
    st.subheader("🔎 Relatório por Mês")
    nomes_meses = {1: 'JANEIRO', 2: 'FEVEREIRO', 3: 'MARÇO', 4: 'ABRIL', 5: 'MAIO', 6: 'JUNHO', 7: 'JULHO', 8: 'AGOSTO', 9: 'SETEMBRO', 10: 'OUTUBRO', 11: 'NOVEMBRO', 12: 'DEZEMBRO'}
    meses_disponiveis = sorted(list(set(df['data_entrada'].dt.to_period('M').dropna())))
    opcoes = [f"{nomes_meses[m.month]} - {m.year}" for m in meses_disponiveis]
    mes_escolhido = st.selectbox("Selecione o Mês:", opcoes)
    
    if mes_escolhido:
        partes = mes_escolhido.split(" - ")
        mes_num = list(nomes_meses.values()).index(partes[0]) + 1
        ano = int(partes[1])
        separadas = df[(df['data_entrada'].dt.month == mes_num) & (df['data_entrada'].dt.year == ano)]
        retiradas = df[(df['data_retirada'].dt.month == mes_num) & (df['data_retirada'].dt.year == ano)]
        c_r1, c_r2 = st.columns(2)
        c_r1.metric("Total Separadas", len(separadas))
        c_r2.metric("Total Retiradas", len(retiradas))

# --- DEMAIS ABAS (PAINEL, RETIRADA, NOVA RM, CONSULTA, HISTÓRICO) ---
# [O código das outras abas permanece idêntico ao que validamos anteriormente]
with tabs[1]:
    for _, row in df[df['status'] == 'Aberta'].iterrows():
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']}"):
            if es_admin and st.button(f"✅ Marcar como SEPARADA", key=f"sep_{row['id']}"):
                cell = sheet.find(str(row['id']), in_column=1)
                sheet.update_cell(cell.row, 8, "Separada")
                recarregar_dados()

with tabs[2]:
    for _, row in df[df['status'] == 'Separada'].iterrows():
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']} | Separada em: {row['data_entrada']}"):
            if es_admin:
                with st.form(f"form_ret_{row['id']}"):
                    quem = st.text_input("Quem retirou?")
                    if st.form_submit_button("Confirmar Retirada"):
                        agora_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cell = sheet.find(str(row['id']), in_column=1)
                        sheet.update(range_name=f"E{cell.row}:H{cell.row}", values=[[agora_ts, agora_ts, quem, "Concluída"]])
                        recarregar_dados()

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
    busca = st.text_input("Nº da RM:", key="input_busca")
    if st.button("Pesquisar", key="btn_pesq"):
        res = df[df['numero_rm'].astype(str) == str(busca).strip()]
        if not res.empty:
            rm = res.iloc[0]
            val = lambda x: x if (x and str(x).strip() != "") else "PENDENTE"
            with st.popover("Detalhes", use_container_width=True):
                if rm['status'] == 'Aberta':
                    st.warning("⚠️ STATUS: ABERTA - AGUARDANDO SEPARAÇÃO.")
                else:
                    st.write(f"**RM:** {val(rm['numero_rm'])} | **STATUS:** {val(rm['status'])}")
                    st.write(f"**QUEM RETIROU:** {val(rm['quem_retirou'])}")

with tabs[idx_historico]:
    st.dataframe(df, use_container_width=True)
    if es_admin:
        with st.form("form_deletar"):
            selecoes = {row['id']: st.checkbox(f"RM: {row['numero_rm']} | ID: {row['id']}", key=f"del_{row['id']}") for _, row in df.iterrows()}
            if st.form_submit_button("🗑️ Deletar Selecionados"):
                for id_rm, sel in selecoes.items():
                    if sel:
                        cell = sheet.find(str(id_rm), in_column=1)
                        sheet.delete_rows(cell.row)
                recarregar_dados()
