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
                    elif usuario == "visitante" and senha == "123":
                        st.session_state['perfil_logado'] = "Visitante"; st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
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
    idx_consulta, idx_historico = 4, 5
else:
    tabs = st.tabs(["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"])
    idx_consulta, idx_historico = 3, 4

with tabs[0]:
    df_raw = pd.DataFrame(sheet.get_all_records())
    cobrancas = df_raw[df_raw['cobranca'] == 'COBRADO']
    if not cobrancas.empty:
        with st.popover(f"🔔 NOTIFICAÇÕES ({len(cobrancas)})"):
            for _, row in cobrancas.iterrows():
                st.warning(f"RM {row['numero_rm']} COBRADA!")
                if st.button(f"Limpar {row['numero_rm']}", key=f"clr_{row['id']}"):
                    sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, "")
                    st.rerun()
    else: st.write("🔔 Sem novas cobranças.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Aberto", len(df[df['status'] == 'Aberta']))
    c2.metric("Concluída", len(df[df['status'] == 'Concluída']))
    c3.metric("Total", len(df))
    st.divider()
    
    nomes_meses = {1: 'JANEIRO', 2: 'FEVEREIRO', 3: 'MARÇO', 4: 'ABRIL', 5: 'MAIO', 6: 'JUNHO', 7: 'JULHO', 8: 'AGOSTO', 9: 'SETEMBRO', 10: 'OUTUBRO', 11: 'NOVEMBRO', 12: 'DEZEMBRO'}
    meses_disponiveis = sorted(list(set(df['data_entrada'].dt.to_period('M').dropna())))
    opcoes = [f"{nomes_meses[m.month].capitalize()} - {m.year}" for m in meses_disponiveis]
    mes_escolhido = st.selectbox("Mês:", opcoes)
    if mes_escolhido:
        partes = mes_escolhido.split(" - ")
        m_num = list(nomes_meses.values()).index(partes[0].upper()) + 1
        ano = int(partes[1])
        c_r1, c_r2 = st.columns(2)
        c_r1.metric("Separadas", len(df[(df['data_entrada'].dt.month == m_num) & (df['data_entrada'].dt.year == ano)]))
        c_r2.metric("Retiradas", len(df[(df['data_retirada'].dt.month == m_num) & (df['data_retirada'].dt.year == ano)]))

with tabs[1]:
    for _, row in df[df['status'] == 'Aberta'].iterrows():
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']}"):
            if st.button("🔔 Cobrar", key=f"cobrar_{row['id']}"):
                sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, "COBRADO")
                st.rerun()
            if es_admin and st.button(f"✅ Separada", key=f"sep_{row['id']}"):
                sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 8, "Separada")
                recarregar_dados()

with tabs[2]:
    for _, row in df[df['status'] == 'Separada'].iterrows():
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']}"):
            if es_admin:
                with st.form(f"ret_{row['id']}"):
                    quem = st.text_input("Quem retirou?")
                    if st.form_submit_button("Confirmar"):
                        sheet.update(range_name=f"E{sheet.find(str(row['id']), in_column=1).row}:H{sheet.find(str(row['id']), in_column=1).row}", 
                                     values=[[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), quem, "Concluída"]])
                        recarregar_dados()

if es_admin:
    with tabs[3]:
        with st.form("cad", clear_on_submit=True):
            num = st.text_input("RM", max_chars=8); sol = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                sheet.append_row([max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1, num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta", ""])
                recarregar_dados()

with tabs[idx_consulta]:
    busca = st.text_input("RM:", key="b")
    if st.button("Pesquisar"):
        res = df[df['numero_rm'].astype(str) == str(busca).strip()]
        if not res.empty:
            rm = res.iloc[0]
            with st.popover("Detalhes", use_container_width=True):
                if rm['status'] == 'Aberta':
                    if st.button("🔔 Cobrar", key="c_c"):
                        sheet.update_cell(sheet.find(str(rm['id']), in_column=1).row, 9, "COBRADO")
                        st.rerun()
                else: st.write(f"RM: {rm['numero_rm']} | Status: {rm['status']}")

with tabs[idx_historico]:
    st.markdown("<h3 style='text-align: center;'>📊 Histórico Completo</h3>", unsafe_allow_html=True)
    col_esq, col_centro, col_dir = st.columns([1, 8, 1])
    with col_centro:
        # Centralizando dados via CSS injetado
        st.markdown("""<style>table{margin-left: auto; margin-right: auto; text-align: center;}</style>""", unsafe_allow_html=True)
        st.dataframe(df[['numero_rm', 'data_retirada', 'quem_retirou', 'status']], use_container_width=True)
        if es_admin:
            with st.form("d"):
                sel = {r['id']: st.checkbox(f"RM: {r['numero_rm']}", key=f"d_{r['id']}") for _, r in df.iterrows()}
                if st.form_submit_button("🗑️ Deletar"):
                    for i, s in sel.items():
                        if s: sheet.delete_rows(sheet.find(str(i), in_column=1).row)
                    recarregar_dados()
