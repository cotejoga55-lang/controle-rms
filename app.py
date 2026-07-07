import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Sistema Integrado", layout="wide")

def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

@st.cache_data(ttl=300)
def carregar_dados():
    sheet = conectar_banco()
    return sheet.get_all_records()

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

def formatar_status_tempo(data_entrada, status):
    if status == "Separada": return "🟡 **EM PROCESSO DE SEPARAÇÃO**"
    if status == "Em Separação": return "⚠️ **SEPARANDO AGORA**"
    agora = datetime.now()
    diferenca = agora - pd.to_datetime(data_entrada)
    if diferenca > timedelta(hours=24): return f"🔴 **ATRASADA (>24h)**"
    else: return f"🟢 **NO PRAZO**"

if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None
if 'estoque_geral' not in st.session_state: st.session_state['estoque_geral'] = pd.DataFrame()

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
dados = carregar_dados()
df = pd.DataFrame(dados)
df['data_entrada'] = pd.to_datetime(df['data_entrada'], errors='coerce')
df['data_saida'] = pd.to_datetime(df['data_saida'], errors='coerce')
df['data_retirada'] = pd.to_datetime(df['data_retirada'], errors='coerce')
es_admin = (st.session_state['perfil_logado'] == "Admin")

with st.sidebar:
    st.markdown(f"### 👤 Perfil: **{st.session_state['perfil_logado']}**")
    with st.expander("📦 Controle de RM's", expanded=True):
        opcoes_rm = ["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"] if es_admin else ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"]
        aba_ativa = st.radio("Selecione:", opcoes_rm + ["📥 Estoque Geral", "📑 Emitir Separação"], key="aba_selecionada")
    st.divider()
    if st.button("🚪 Sair", use_container_width=True): 
        st.session_state['perfil_logado'] = None
        st.rerun()

aba = st.session_state.aba_selecionada
st.title(f"📦 {aba}")
st.divider()

if aba == "📊 Dashboard":
    avisos = df[df['cobranca'].str.contains("está cobrando|Comentario adicionado", case=False, na=False)]
    if not avisos.empty:
        with st.popover(f"🔔 NOTIFICAÇÕES ({len(avisos)})"):
            for _, row in avisos.iterrows():
                st.warning(f"{row['cobranca']} na RM {row['numero_rm']}!")
                if st.button(f"Limpar {row['numero_rm']}", key=f"clr_ntf_{row['id']}"):
                    sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, "")
                    st.rerun()
    c1, c2, c3 = st.columns(3)
    c1.metric("Aberto", len(df[df['status'] == 'Aberta']))
    c2.metric("Concluída", len(df[df['status'] == 'Concluída']))
    c3.metric("Total", len(df))

elif aba == "📋 Painel":
    df_painel = df[df['status'].isin(['Aberta', 'Em Separação'])]
    for _, row in df_painel.iterrows():
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']} | {formatar_status_tempo(row['data_entrada'], row['status'])}"):
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                with st.popover("🔔 Cobrar"):
                    nome = st.text_input("Quem?", key=f"cob_txt_{row['id']}")
                    if st.button("Confirmar", key=f"btn_cob_{row['id']}"):
                        sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, f"{nome} está cobrando"); st.rerun()
            with b2:
                if es_admin and row['status'] == 'Aberta' and st.button("⚠️ Em Separação", key=f"em_sep_{row['id']}"):
                    sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 8, "Em Separação"); recarregar_dados()
            with b3:
                if es_admin and st.button("✅ Separada", key=f"sep_{row['id']}"):
                    row_idx = sheet.find(str(row['id']), in_column=1).row
                    sheet.update_cell(row_idx, 5, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    sheet.update_cell(row_idx, 8, "Separada"); recarregar_dados()
            with b4:
                with st.popover("☁️ Comentários"):
                    com = st.text_area("Obs:", value=row.get('comentario', ''), key=f"com_{row['id']}")
                    if st.button("Salvar", key=f"save_{row['id']}"):
                        sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 11, com); st.rerun()

elif aba == "📦 Pend. Retirada":
    st.dataframe(df[df['status'] == 'Separada'])

elif aba == "➕ Nova RM":
    with st.form("cad_rm", clear_on_submit=True):
        num = st.text_input("RM", max_chars=8)
        sol = st.text_input("Solicitante")
        if st.form_submit_button("Cadastrar"):
            sheet.append_row([max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1, num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta", ""])
            recarregar_dados()

elif aba == "🔍 Consulta":
    busca = st.selectbox("Pesquisar RM:", options=df['numero_rm'].dropna().astype(str).unique(), index=None)
    if busca: st.write(df[df['numero_rm'].astype(str) == busca])

elif aba == "📊 Histórico":
    st.dataframe(df)

elif aba == "📥 Estoque Geral":
    st.info("Cole os dados (Partnumber | Descrição | Subinventário | Locação | Qtd):")
    txt = st.text_area("Colar dados (Ctrl+V):", height=300)
    if st.button("Processar"):
        if txt:
            linhas = [l.split('\t') for l in txt.split('\n') if l.strip()]
            st.session_state['estoque_geral'] = pd.DataFrame(linhas[1:], columns=linhas[0])
            st.success("Estoque processado!")
    if not st.session_state['estoque_geral'].empty:
        st.dataframe(st.session_state['estoque_geral'])

elif aba == "📑 Emitir Separação":
    busca = st.text_input("Buscar Partnumber:")
    if busca and not st.session_state['estoque_geral'].empty:
        st.table(st.session_state['estoque_geral'][st.session_state['estoque_geral'].iloc[:, 0].astype(str).str.contains(busca, case=False)])
