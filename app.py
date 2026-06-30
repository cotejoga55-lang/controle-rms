import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz

st.set_page_config(page_title="Controle de RMs", layout="wide")

# Define o fuso horário de Brasília
tz = pytz.timezone('America/Sao_Paulo')

def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

def formatar_status_tempo(data_entrada, status):
    if status == "Separada": return "🟡 **EM PROCESSO DE SEPARAÇÃO**"
    if status == "Em Separação": return "⚠️ **SEPARANDO AGORA**"
    agora = datetime.now(tz).replace(tzinfo=None)
    diferenca = agora - pd.to_datetime(data_entrada)
    if diferenca > timedelta(hours=24): return f"🔴 **ATRASADA (>24h)**"
    else: return f"🟢 **NO PRAZO**"

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
                    if usuario == "pdc" and senha == "123": st.session_state['perfil_logado'] = "Admin"; st.rerun()
                    elif usuario == "cummins" and senha == "1234": st.session_state['perfil_logado'] = "Visitante"; st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
    st.stop()

sheet = conectar_banco()
df = pd.DataFrame(sheet.get_all_records())
df['data_entrada'] = pd.to_datetime(df['data_entrada'], errors='coerce')
df['data_retirada'] = pd.to_datetime(df['data_retirada'], errors='coerce')
es_admin = (st.session_state['perfil_logado'] == "Admin")

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state['perfil_logado']}**")
    if st.button("🚪 Sair"): st.session_state['perfil_logado'] = None; st.rerun()

st.title("📦 Sistema de Controle de RMs")
tabs = st.tabs(["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"] if es_admin else ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"])

def mostrar_conteudo(nome_tab):
    if nome_tab == "📊 Dashboard":
        df_raw = pd.DataFrame(sheet.get_all_records())
        avisos = df_raw[df_raw['cobranca'].str.contains("está cobrando|Comentario adicionado", case=False, na=False)]
        if not avisos.empty:
            with st.popover(f"🔔 NOTIFICAÇÕES ({len(avisos)})"):
                for _, row in avisos.iterrows():
                    st.warning(f"{row['cobranca']} na RM {row['numero_rm']}!")
                    if st.button(f"Limpar {row['numero_rm']}", key=f"clr_{row['id']}"):
                        sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, ""); st.rerun()
        c1, c2, c3 = st.columns(3)
        c1.metric("Aberto", len(df[df['status'] == 'Aberta']))
        c2.metric("Concluída", len(df[df['status'] == 'Concluída']))
        c3.metric("Total", len(df))

    elif nome_tab == "📋 Painel":
        for _, row in df[df['status'].isin(['Aberta', 'Em Separação'])].iterrows():
            with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']} | {formatar_status_tempo(row['data_entrada'], row['status'])}"):
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    with st.popover("🔔 Cobrar"):
                        nome = st.text_input("Quem está cobrando?", key=f"cob_{row['id']}")
                        if st.button("Confirmar", key=f"btn_c_{row['id']}"):
                            sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, f"{nome} está cobrando"); st.rerun()
                with b2:
                    if es_admin and row['status'] == 'Aberta':
                        if st.button(f"⚠️ Em Separação", key=f"em_sep_{row['id']}"):
                            sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 8, "Em Separação"); recarregar_dados()
                with b3:
                    if es_admin and st.button(f"✅ Separada", key=f"sep_{row['id']}"):
                        # Salva o status e a data exata da separação agora
                        row_idx = sheet.find(str(row['id']), in_column=1).row
                        sheet.update(range_name=f"H{row_idx}:I{row_idx}", values=[["Separada", datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")]])
                        recarregar_dados()
                with b4:
                    with st.popover("☁️ Comentários"):
                        com = st.text_area("Obs:", value=row.get('comentario', ''), key=f"com_{row['id']}")
                        if st.button("Salvar", key=f"save_{row['id']}"):
                            sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 11, com)
                            sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, "Comentario adicionado"); st.rerun()

    elif nome_tab == "📦 Pend. Retirada":
        for _, row in df[df['status'] == 'Separada'].iterrows():
            with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']}"):
                # Semáforo 72h
                if pd.notnull(row['data_retirada']):
                    diff = datetime.now(tz).replace(tzinfo=None) - row['data_retirada']
                    if diff > timedelta(hours=72): st.error("⚠️ RM separada a mais de 72 horas")
                    else: st.success("🟢 Dentro do prazo (72h)")
                
                if es_admin:
                    with st.form(f"ret_{row['id']}"):
                        quem = st.text_input("Quem retirou?")
                        if st.form_submit_button("Confirmar Retirada"):
                            row_idx = sheet.find(str(row['id']), in_column=1).row
                            sheet.update(range_name=f"E{row_idx}:H{row_idx}", values=[[datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), quem, "Concluída"]])
                            recarregar_dados()

    elif nome_tab == "➕ Nova RM":
        with st.form("cad", clear_on_submit=True):
            num = st.text_input("RM (8 dígitos)", max_chars=8)
            sol = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                sheet.append_row([len(df)+1, num, sol, datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta", ""])
                st.success("RM cadastrada!"); recarregar_dados()

    elif nome_tab == "🔍 Consulta":
        busca = st.text_input("RM:", max_chars=8)
        if st.button("Pesquisar"):
            res = df[df['numero_rm'].astype(str) == str(busca)]
            if not res.empty: st.write(f"Status: {res.iloc[0]['status']}")
            else: st.warning("Não encontrada.")

    elif nome_tab == "📊 Histórico":
        st.table(df[['numero_rm', 'status', 'quem_retirou']])

for i, nome in enumerate(nomes := ["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"] if es_admin else ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"]):
    with tabs[i]: mostrar_conteudo(nome)
