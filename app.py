import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Controle de RMs", layout="wide")

# Função de conexão mantida
def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def obter_hora_brasil():
    return datetime.utcnow() - timedelta(hours=3)

def recarregar_dados():
    st.cache_data.clear()
    st.rerun()

def formatar_status_tempo(data_entrada, status):
    if status == "Separada": return "🟡 **EM PROCESSO DE SEPARAÇÃO**"
    if status == "Em Separação": return "⚠️ **SEPARANDO AGORA**"
    agora = obter_hora_brasil()
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
df['data_saida'] = pd.to_datetime(df['data_saida'], errors='coerce')
df['data_retirada'] = pd.to_datetime(df['data_retirada'], errors='coerce')
es_admin = (st.session_state['perfil_logado'] == "Admin")

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state['perfil_logado']}**")
    if st.button("🚪 Sair"): st.session_state['perfil_logado'] = None; st.rerun()

st.title("📦 Sistema de Controle de RMs")
tabs = st.tabs(["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"] if es_admin else ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"])

def mostrar_conteudo(nome_tab):
    if nome_tab == "📊 Dashboard":
        c1, c2, c3 = st.columns(3)
        c1.metric("Aberto", len(df[df['status'] == 'Aberta']))
        c2.metric("Concluída", len(df[df['status'] == 'Concluída']))
        c3.metric("Total", len(df))
        st.divider()
        df_sep = df[df['status'] == 'Separada'].copy()
        agora = obter_hora_brasil()
        dentro_prazo = df_sep[(agora - df_sep['data_saida']) <= timedelta(hours=72)]
        fora_prazo = df_sep[(agora - df_sep['data_saida']) > timedelta(hours=72)]
        cp1, cp2 = st.columns(2)
        cp1.metric("Dentro do prazo (72h)", len(dentro_prazo))
        cp2.metric("Fora do prazo (>72h)", len(fora_prazo))

    elif nome_tab == "📋 Painel":
        for _, row in df[df['status'].isin(['Aberta', 'Em Separação'])].iterrows():
            # Chaves únicas com prefixo no expander
            with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']} | {formatar_status_tempo(row['data_entrada'], row['status'])}"):
                b1, b2, b3 = st.columns(3)
                with b1:
                    with st.popover("🔔 Cobrar"):
                        # Chave única para o input de cobrança
                        nome = st.text_input("Quem está cobrando?", key=f"cob_txt_{row['id']}")
                        if st.button("Confirmar", key=f"btn_cob_{row['id']}"):
                            sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, f"{nome} está cobrando"); st.rerun()
                if es_admin and row['status'] == 'Aberta':
                    if b2.button(f"⚠️ Em Separação", key=f"btn_sep_em_{row['id']}"):
                        sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 8, "Em Separação"); recarregar_dados()
                if es_admin and b3.button(f"✅ Separada", key=f"btn_sep_final_{row['id']}"):
                    row_idx = sheet.find(str(row['id']), in_column=1).row
                    # REGISTRA DATA NO CLIQUE
                    sheet.update(range_name=f"E{row_idx}:H{row_idx}", values=[[obter_hora_brasil().strftime("%Y-%m-%d %H:%M:%S"), "Separada", "", ""]])
                    recarregar_dados()

    elif nome_tab == "📦 Pend. Retirada":
        for _, row in df[df['status'] == 'Separada'].iterrows():
            diff = obter_hora_brasil() - pd.to_datetime(row['data_saida'])
            msg = "🟢 Dentro do prazo (72h)" if diff <= timedelta(hours=72) else "🔴 Fora do prazo (>72h)"
            with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']} | {msg}"):
                if diff > timedelta(hours=72): st.error(msg)
                else: st.success(msg)
                if es_admin:
                    with st.form(f"form_ret_{row['id']}"): # Chave única para o formulário
                        quem = st.text_input("Quem retirou?", key=f"ret_in_{row['id']}")
                        if st.form_submit_button("Confirmar"):
                            row_idx = sheet.find(str(row['id']), in_column=1).row
                            sheet.update(range_name=f"F{row_idx}:H{row_idx}", values=[[obter_hora_brasil().strftime("%Y-%m-%d %H:%M:%S"), quem, "Concluída"]])
                            recarregar_dados()

    elif nome_tab == "📊 Histórico":
        st.markdown("<h3 style='text-align: center;'>📊 Histórico</h3>", unsafe_allow_html=True)
        col_c = st.columns([1, 8, 1])[1]
        with col_c:
            st.markdown(f"<div style='text-align: center;'>{df[['numero_rm', 'data_retirada', 'quem_retirou', 'status']].fillna('Pendente').to_html(index=False)}</div>", unsafe_allow_html=True)
            if es_admin:
                with st.form("form_delete"): # Chave única
                    sel = {r['id']: st.checkbox(f"RM: {r['numero_rm']}", key=f"del_chk_{r['id']}") for _, r in df.iterrows()}
                    if st.form_submit_button("🗑️ Deletar"):
                        for i, s in sel.items():
                            if s: sheet.delete_rows(sheet.find(str(i), in_column=1).row)
                        recarregar_dados()

# Renderização final
for i, nome in enumerate(nomes := ["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"] if es_admin else ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"]):
    with tabs[i]: mostrar_conteudo(nome)
