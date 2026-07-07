import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Controle de RMs", layout="wide")

# --- FUNÇÕES ORIGINAIS ---
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

# --- LOGIN E SESSÃO ---
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
            with st.expander("ℹ️ Precisa de acesso?"):
                st.markdown("Consulte a sua Rm, segue o perfil para ser utilizado:\n\n**Login:** cummins\n**Senha:** 1234")
    st.markdown("<p style='text-align: center; color: gray;'>Sistema elaborado por Kevin.</p>", unsafe_allow_html=True)
    st.stop()

# --- CARREGAMENTO DE DADOS ---
sheet = conectar_banco()
dados = carregar_dados()
df = pd.DataFrame(dados)
df['data_entrada'] = pd.to_datetime(df['data_entrada'], errors='coerce')
df['data_saida'] = pd.to_datetime(df['data_saida'], errors='coerce')
df['data_retirada'] = pd.to_datetime(df['data_retirada'], errors='coerce')
es_admin = (st.session_state['perfil_logado'] == "Admin")

# --- MENU DE NAVEGAÇÃO ---
if es_admin:
    opcoes_menu = ["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico", "🖨️ Emitir Separação"]
else:
    opcoes_menu = ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"]

with st.sidebar:
    st.markdown(f"### 👤 Perfil: **{st.session_state['perfil_logado']}**")
    st.divider()
    aba_selecionada = st.radio("Navegação do Sistema:", opcoes_menu)
    st.divider()
    if st.button("🚪 Sair", use_container_width=True): 
        st.session_state['perfil_logado'] = None
        st.rerun()

# --- TELA: EMITIR SEPARAÇÃO ---
if aba_selecionada == "🖨️ Emitir Separação":
    st.title("📄 Roteiro de Separação")
    with st.container():
        st.write("---")
        c1, c2 = st.columns(2)
        c1.write(f"**Data de Emissão:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        c2.write("**Local:** PDC - Centro de Distribuição")
        st.write("---")
        
        dados_colados = st.text_area("Cole aqui os dados do Excel (Partnumber | Descrição | Qtd):", height=200, help="Copie do Excel e cole aqui.")
        
        if st.button("Gerar Roteiro"):
            if dados_colados:
                # Processa os dados colados
                linhas = [linha.split('\t') for linha in dados_colados.split('\n') if linha.strip()]
                df_sep = pd.DataFrame(linhas, columns=['Partnumber', 'Descrição', 'Qtd'])
                
                st.subheader("📑 Lista de Separação")
                st.table(df_sep)
                st.success("Roteiro gerado. Utilize Ctrl+P para imprimir em Retrato.")
            else:
                st.warning("Por favor, cole os dados.")

# --- TELAS ORIGINAIS DE RM ---
elif aba_selecionada == "📊 Dashboard":
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
    st.divider()
    nomes_meses = {1: 'JANEIRO', 2: 'FEVEREIRO', 3: 'MARÇO', 4: 'ABRIL', 5: 'MAIO', 6: 'JUNHO', 7: 'JULHO', 8: 'AGOSTO', 9: 'SETEMBRO', 10: 'OUTUBRO', 11: 'NOVEMBRO', 12: 'DEZEMBRO'}
    meses_disponiveis = sorted(list(set(df['data_entrada'].dt.to_period('M').dropna())))
    opcoes = [f"{nomes_meses[m.month].capitalize()} - {m.year}" for m in meses_disponiveis]
    mes_escolhido = st.selectbox("Selecione o Mês:", opcoes)
    if mes_escolhido:
        partes = mes_escolhido.split(" - ")
        m_num = list(nomes_meses.values()).index(partes[0].upper()) + 1
        ano = int(partes[1])
        c_r1, c_r2 = st.columns(2)
        c_r1.metric("Separadas no Mês", len(df[(df['data_entrada'].dt.month == m_num) & (df['data_entrada'].dt.year == ano)]))
        c_r2.metric("Retiradas no Mês", len(df[(df['data_retirada'].dt.month == m_num) & (df['data_retirada'].dt.year == ano)]))

elif aba_selecionada == "📋 Painel":
    df_painel = df[df['status'].isin(['Aberta', 'Em Separação'])]
    if df_painel.empty: st.info("Nenhuma RM em aberto ou em separação no momento.")
    for _, row in df_painel.iterrows():
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']} | {formatar_status_tempo(row['data_entrada'], row['status'])}"):
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                with st.popover("🔔 Cobrar"):
                    nome = st.text_input("Quem está cobrando?", key=f"cob_txt_{row['id']}")
                    if st.button("Confirmar", key=f"btn_cob_{row['id']}"):
                        sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, f"{nome} está cobrando"); st.rerun()
            with b2:
                if es_admin and row['status'] == 'Aberta':
                    if st.button(f"⚠️ Em Separação", key=f"em_sep_{row['id']}"):
                        sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 8, "Em Separação"); recarregar_dados()
            with b3:
                if es_admin and st.button(f"✅ Separada", key=f"sep_{row['id']}"):
                    row_idx = sheet.find(str(row['id']), in_column=1).row
                    sheet.update_cell(row_idx, 5, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    sheet.update_cell(row_idx, 8, "Separada"); recarregar_dados()
            with b4:
                with st.popover("☁️ Comentários"):
                    com = st.text_area("Obs:", value=row.get('comentario', ''), key=f"com_{row['id']}")
                    if st.button("Salvar", key=f"save_{row['id']}"):
                        sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 11, com)
                        sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, "Comentario adicionado"); st.rerun()

elif aba_selecionada == "📦 Pend. Retirada":
    df_pendente = df[df['status'] == 'Separada']
    if df_pendente.empty: st.info("Nenhuma RM pendente de retirada.")
    for _, row in df_pendente.iterrows():
        tempo_decorrido = datetime.now() - pd.to_datetime(row['data_saida'])
        is_atrasado = tempo_decorrido > timedelta(hours=72)
        label = "🔴 Separada a mais de 72 horas" if is_atrasado else "🟢 Separada recentemente"
        with st.expander(f"RM: {row['numero_rm']} - {row['solicitante']} | {label}"):
            if is_atrasado: st.error(label)
            else: st.success(label)
            if es_admin:
                with st.form(key=f"ret_form_{row['id']}"):
                    quem = st.text_input("Quem retirou?", key=f"quem_in_{row['id']}")
                    if st.form_submit_button("Confirmar"):
                        row_idx = sheet.find(str(row['id']), in_column=1).row
                        sheet.update(range_name=f"F{row_idx}:H{row_idx}", values=[[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), quem, "Concluída"]])
                        recarregar_dados()

elif aba_selecionada == "➕ Nova RM":
    with st.form("cad_rm", clear_on_submit=True):
        num = st.text_input("RM (8 dígitos)", max_chars=8)
        sol = st.text_input("Solicitante")
        if st.form_submit_button("Cadastrar"):
            sheet.append_row([max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1, num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta", ""])
            st.success("RM cadastrada!"); recarregar_dados()

elif aba_selecionada == "🔍 Consulta":
    lista_rms = df['numero_rm'].dropna().astype(str).unique().tolist()
    busca = st.selectbox("Pesquisar RM:", options=lista_rms, index=None, placeholder="Digite ou selecione a RM...", key="sb_pesquisa_rm")
    if st.button("Pesquisar", key="btn_pesquisa_rm", use_container_width=True):
        if busca: st.session_state['ultima_busca_rm'] = str(busca).strip()
        else: st.warning("Por favor, selecione ou digite uma RM válida.")
    if 'ultima_busca_rm' in st.session_state and st.session_state['ultima_busca_rm']:
        res = df[df['numero_rm'].astype(str) == st.session_state['ultima_busca_rm']]
        if not res.empty:
            rm = res.iloc[0]
            with st.container(border=True):
                st.markdown(f"### 📦 RM: {rm['numero_rm']}")
                st.divider()
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**👤 Solicitante:** {rm['solicitante']}")
                    data_entrada = rm.get('data_entrada')
                    if pd.notna(data_entrada): st.markdown(f"**📅 Data:** {pd.to_datetime(data_entrada).strftime('%d/%m/%Y %H:%M')}")
                with c2:
                    status_atual = rm['status']
                    icone = "🟢" if status_atual == "Concluída" else ("🟡" if status_atual in ["Em Separação", "Separada"] else "🔴")
                    st.markdown(f"**📌 Status:** {icone} {status_atual}")
        else: st.warning("RM não encontrada.")

elif aba_selecionada == "📊 Histórico":
    st.markdown("<h3 style='text-align: center;'>📊 Histórico Completo</h3>", unsafe_allow_html=True)
    st.dataframe(df[['numero_rm', 'data_retirada', 'quem_retirou', 'status']].fillna('Pendente'), use_container_width=True)
    if es_admin:
        with st.form("form_del_hist"):
            sel = {r['id']: st.checkbox(f"RM: {r['numero_rm']}", key=f"del_chk_{r['id']}") for _, r in df.iterrows()}
            if st.form_submit_button("🗑️ Deletar Selecionadas", use_container_width=True):
                for i, s in sel.items():
                    if s: sheet.delete_rows(sheet.find(str(i), in_column=1).row)
                recarregar_dados()
