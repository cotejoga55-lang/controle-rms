import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO E CONEXÃO ---
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
        return "🟡 EM PROCESSO DE SEPARAÇÃO"
    agora = datetime.now()
    diferenca = agora - pd.to_datetime(data_entrada)
    if diferenca > timedelta(hours=24):
        return "🔴 ATRASADA (>24h)"
    else:
        return "🟢 NO PRAZO"

if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None

# --- LOGIN ---
if st.session_state['perfil_logado'] is None:
    col_meio = st.columns([2, 1, 2])[1]
    with col_meio:
        with st.container():
            st.write("### Login")
            with st.form("login_form"):
                usuario = st.text_input("Usuário:")
                senha = st.text_input("Senha:", type="password")
                if st.form_submit_button("Entrar"):
                    if usuario == "pdc" and senha == "123":
                        st.session_state['perfil_logado'] = "Admin"; st.rerun()
                    elif usuario == "cummins" and senha == "1234":
                        st.session_state['perfil_logado'] = "Visitante"; st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
    st.stop()

# --- CARREGAMENTO DE DADOS ---
sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
df['data_entrada'] = pd.to_datetime(df['data_entrada'], errors='coerce')
df['data_retirada'] = pd.to_datetime(df['data_retirada'], errors='coerce')
es_admin = (st.session_state['perfil_logado'] == "Admin")

with st.sidebar:
    st.write(f"Perfil: {st.session_state['perfil_logado']}")
    if st.button("Sair"):
        st.session_state['perfil_logado'] = None
        st.rerun()

st.title("Controle de RMs")

if es_admin:
    tabs = st.tabs(["Dashboard", "Painel", "Pend. Retirada", "Nova RM", "Consulta", "Histórico"])
else:
    tabs = st.tabs(["Painel", "Pend. Retirada", "Consulta", "Histórico"])

def mostrar_conteudo(nome_tab):
    if nome_tab == "Dashboard":
        df_raw = pd.DataFrame(sheet.get_all_records())
        cobrancas = df_raw[df_raw['cobranca'] == 'COBRADO']
        if not cobrancas.empty:
            with st.popover(f"Notificações ({len(cobrancas)})"):
                for _, row in cobrancas.iterrows():
                    st.warning(f"RM {row['numero_rm']} COBRADA!")
                    if st.button(f"Limpar {row['numero_rm']}", key=f"clr_{row['id']}"):
                        sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, "")
                        st.rerun()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Aberto", len(df[df['status'] == 'Aberta']))
        c2.metric("Concluída", len(df[df['status'] == 'Concluída']))
        c3.metric("Total", len(df))

    elif nome_tab == "Painel":
        for _, row in df[df['status'] == 'Aberta'].iterrows():
            with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']} | {formatar_status_tempo(row['data_entrada'], row['status'])}"):
                if st.button("Cobrar", key=f"cobrar_{row['id']}"):
                    sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, "COBRADO")
                    st.rerun()
                if es_admin and st.button("Separada", key=f"sep_{row['id']}"):
                    sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 8, "Separada")
                    recarregar_dados()

    elif nome_tab == "Pend. Retirada":
        for _, row in df[df['status'] == 'Separada'].iterrows():
            with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']}"):
                if es_admin:
                    with st.form(f"ret_{row['id']}"):
                        quem = st.text_input("Quem retirou?")
                        if st.form_submit_button("Confirmar"):
                            sheet.update(range_name=f"E{sheet.find(str(row['id']), in_column=1).row}:H{sheet.find(str(row['id']), in_column=1).row}", 
                                       values=[[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), quem, "Concluída"]])
                            recarregar_dados()

    elif nome_tab == "Nova RM":
        with st.form("cad", clear_on_submit=True):
            num = st.text_input("RM (8 dígitos):", max_chars=8)
            sol = st.text_input("Solicitante:")
            if st.form_submit_button("Cadastrar"):
                if len(num) != 8 or not num.isdigit():
                    st.error("Erro: A RM deve conter exatamente 8 dígitos.")
                else:
                    sheet.append_row([max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1, num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta", ""])
                    st.success("Cadastrado!")
                    recarregar_dados()

    elif nome_tab == "Consulta":
        st.write("### Consultar RM")
        lista_rms = df[df['numero_rm'].astype(str).str.len() == 8]['numero_rm'].astype(str).unique().tolist()
        busca = st.selectbox("Selecione a RM (8 dígitos):", [""] + sorted(lista_rms))
        
        if st.button("Pesquisar"):
            if busca and len(busca) == 8:
                res = df[df['numero_rm'].astype(str) == str(busca).strip()]
                if not res.empty:
                    rm = res.iloc[0]
                    st.write(f"RM: {rm['numero_rm']} | Solicitante: {rm['solicitante']}")
                    st.write(f"Status: {rm['status']}")
                else: st.warning("RM não encontrada.")
            else: st.error("Por favor, selecione uma RM com 8 dígitos.")

    elif nome_tab == "Histórico":
        df_hist = df.copy()
        if not es_admin: df_hist = df_hist[df_hist['status'] == 'Concluída']
        st.table(df_hist[['numero_rm', 'data_retirada', 'quem_retirou', 'status']].fillna('Pendente'))

# Execução das abas
nomes = ["Dashboard", "Painel", "Pend. Retirada", "Nova RM", "Consulta", "Histórico"] if es_admin else ["Painel", "Pend. Retirada", "Consulta", "Histórico"]
for i, nome in enumerate(nomes):
    with tabs[i]: mostrar_conteudo(nome)
