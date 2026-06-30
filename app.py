import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

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

# --- INTERFACE E LOGIN ---
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

# --- LÓGICA E ABAS ---
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
    tabs = st.tabs(["📊 Dashboard", "📋 Painel", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"])
    idx_consulta, idx_historico = 3, 4
else:
    tabs = st.tabs(["📊 Dashboard", "📋 Painel", "🔍 Consulta", "📊 Histórico"])
    idx_consulta, idx_historico = 2, 3

# --- ABA 0: DASHBOARD ---
with tabs[0]:
    st.subheader("Resumo Operacional")
    c1, c2, c3 = st.columns(3)
    c1.metric("RMs em Aberto", len(df[df['status'] == 'Aberta']))
    c2.metric("RMs Concluídas", len(df[df['status'] == 'Concluída']))
    c3.metric("Total de RMs", len(df))
    
    st.divider()
    st.subheader("Produtividade Mensal")
    
    df_concluidas = df[df['status'] == 'Concluída'].copy()
    df_concluidas['data_retirada'] = pd.to_datetime(df_concluidas['data_retirada'], errors='coerce')
    meses_ano = pd.period_range(start='2026-01', end='2026-12', freq='M')
    
    if not df_concluidas.empty:
        df_concluidas['mes'] = df_concluidas['data_retirada'].dt.to_period('M')
        dados_agrupados = df_concluidas.groupby('mes').size()
    else:
        dados_agrupados = pd.Series(0, index=meses_ano)
    
    dados_finais = dados_agrupados.reindex(meses_ano, fill_value=0)
    dados_finais.index = [m.strftime('%b') for m in dados_finais.index]
    
    fig = px.bar(
        x=dados_finais.index, y=dados_finais.values,
        labels={'x': 'Mês', 'y': 'Concluídas'},
        color_discrete_sequence=['#007bff']
    )
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# --- ABA 1: PAINEL ---
with tabs[1]:
    st.subheader("Gestão de RMs em Aberto")
    for _, row in df[df['status'] == 'Aberta'].iterrows():
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']}"):
            if es_admin:
                if st.button(f"✅ Concluir RM {row['numero_rm']}", key=f"btn_{row['id']}"):
                    st.session_state[f'concluir_{row["id"]}'] = True
                if st.session_state.get(f'concluir_{row["id"]}'):
                    with st.form(f"form_{row['id']}"):
                        quem = st.text_input("Quem retirou?")
                        if st.form_submit_button("Confirmar"):
                            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            cell = sheet.find(str(row['id']), in_column=1)
                            sheet.update(range_name=f"E{cell.row}:H{cell.row}", values=[[agora, agora, quem, "Concluída"]])
                            recarregar_dados()
            else:
                st.write("Apenas Administradores podem concluir.")

# --- ABA 2: NOVA RM (Admin) ---
if es_admin:
    with tabs[2]:
        with st.form("form_cadastro", clear_on_submit=True):
            num = st.text_input("Número da RM")
            sol = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                novo_id = max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1
                sheet.append_row([novo_id, num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta"])
                st.success("Cadastrado!")
                recarregar_dados()

# --- ABA: CONSULTA RÁPIDA ---
with tabs[idx_consulta]:
    st.subheader("🔍 Consultar Status de RM")
    c1, c2 = st.columns([3, 1])
    with c1:
        busca_rm = st.text_input("Digite o número da RM:", key="input_busca")
    with c2:
        st.write("###") 
        btn_pesquisar = st.button("Pesquisar", key="btn_pesquisar_rm")
    
    if btn_pesquisar and busca_rm:
        df_str = df.copy()
        df_str['numero_rm_str'] = df_str['numero_rm'].astype(str).str.strip()
        resultado = df_str[df_str['numero_rm_str'] == str(busca_rm).strip()]
        
        if not resultado.empty:
            rm = resultado.iloc[0]
            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(f"**RM:** {rm['numero_rm']} | **Status:** {rm['status']}")
        else:
            st.error("RM não encontrada.")

# --- ABA FINAL: HISTÓRICO ---
with tabs[idx_historico]:
    st.dataframe(df, use_container_width=True)
