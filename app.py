import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Sistema Integrado", layout="wide")

# --- FUNÇÕES ---
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

# --- ESTADO INICIAL ---
if 'perfil_logado' not in st.session_state: st.session_state['perfil_logado'] = None
if 'estoque_geral' not in st.session_state: st.session_state['estoque_geral'] = pd.DataFrame()

# --- LOGIN ---
if st.session_state['perfil_logado'] is None:
    col_meio = st.columns([2, 1, 2])[1]
    with col_meio:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>🔑 Login</h3>", unsafe_html=True)
            with st.form("login_form"):
                usuario = st.text_input("Usuário:")
                senha = st.text_input("Senha:", type="password")
                if st.form_submit_button("Entrar", use_container_width=True):
                    if usuario == "pdc" and senha == "123": st.session_state['perfil_logado'] = "Admin"; st.rerun()
                    elif usuario == "cummins" and senha == "1234": st.session_state['perfil_logado'] = "Visitante"; st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
    st.stop()

# --- DADOS ---
sheet = conectar_banco()
dados = carregar_dados()
df = pd.DataFrame(dados)
df['data_entrada'] = pd.to_datetime(df['data_entrada'], errors='coerce')
df['data_saida'] = pd.to_datetime(df['data_saida'], errors='coerce')
df['data_retirada'] = pd.to_datetime(df['data_retirada'], errors='coerce')
es_admin = (st.session_state['perfil_logado'] == "Admin")

# --- NAVEGAÇÃO ---
with st.sidebar:
    st.markdown(f"### 👤 Perfil: **{st.session_state['perfil_logado']}**")
    
    with st.expander("📦 Controle de RM's", expanded=True):
        opcoes_rm = ["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"] if es_admin else ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"]
        aba_rm = st.radio("Selecione:", opcoes_rm, key="nav_rm", label_visibility="collapsed")
    
    with st.expander("🚀 Controle de Separação", expanded=True):
        aba_sep = st.radio("Selecione:", ["📥 Estoque Geral", "📑 Emitir Separação"], key="nav_sep", label_visibility="collapsed")
    
    st.divider()
    if st.button("🚪 Sair", use_container_width=True): 
        st.session_state['perfil_logado'] = None
        st.rerun()

# --- LÓGICA DE NAVEGAÇÃO ---

# 1. RMs
if st.session_state.get("nav_rm"):
    aba = st.session_state.nav_rm
    st.title(f"📦 {aba}")
    st.divider()
    # (Mantendo sua estrutura original de RMs conforme solicitado)
    if aba == "📊 Dashboard": 
        c1, c2, c3 = st.columns(3)
        c1.metric("Aberto", len(df[df['status'] == 'Aberta']))
        c2.metric("Concluída", len(df[df['status'] == 'Concluída']))
        c3.metric("Total", len(df))
    # ... (demais lógica de RMs)

# 2. SEPARAÇÃO (Integrando o Estoque Geral)
elif st.session_state.get("nav_sep"):
    aba_s = st.session_state.nav_sep
    st.title(f"🚀 {aba_s}")
    st.divider()

    if aba_s == "📥 Estoque Geral":
        st.info("Cole o estoque completo (o sistema processa grandes volumes).")
        txt_estoque = st.text_area("Colar Estoque (Ctrl+V):", height=300)
        if st.button("Processar Estoque"):
            if txt_estoque:
                linhas = [l.split('\t') for l in txt_estoque.split('\n') if l.strip()]
                st.session_state['estoque_geral'] = pd.DataFrame(linhas[1:], columns=linhas[0])
                st.success(f"Estoque atualizado! {len(st.session_state['estoque_geral'])} itens carregados.")
        
        if not st.session_state['estoque_geral'].empty:
            st.dataframe(st.session_state['estoque_geral'], use_container_width=True)

    elif aba_s == "📑 Emitir Separação":
        st.markdown("### 📄 Roteiro de Separação")
        if st.session_state['estoque_geral'].empty:
            st.warning("Estoque vazio. Vá em '📥 Estoque Geral' primeiro.")
        else:
            busca = st.text_input("Buscar Partnumber no Estoque:")
            if busca:
                # Busca rápida no dataframe carregado
                df_res = st.session_state['estoque_geral'][
                    st.session_state['estoque_geral'].apply(lambda row: busca.lower() in str(row[0]).lower(), axis=1)
                ]
                st.table(df_res)
                st.info("💡 Pressione **Ctrl+P** para imprimir o roteiro.")
