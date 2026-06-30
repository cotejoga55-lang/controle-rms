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
            st.markdown("<div style='text-align: center;'><small>Se você é um solicitador de RM</small><br><b>usuario: cummins</b><br><b>senha: 1234</b></div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Sistema elaborado por Kevin.</p>", unsafe_allow_html=True)
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
        st.divider()
        
        df_sep = df[df['status'] == 'Separada'].copy()
        df_sep['data_retirada'] = pd.to_datetime(df_sep['data_retirada'])
        agora = obter_hora_brasil()
        dentro_prazo = df_sep[(agora - df_sep['data_retirada']) <= timedelta(hours=72)]
        fora_prazo = df_sep[(agora - df_sep['data_retirada']) > timedelta(hours=72)]
        cp1, cp2 = st.columns(2)
        cp1.metric("Dentro do prazo (72h)", len(dentro_prazo))
        cp2.metric("Fora do prazo (>72h)", len(fora_prazo))
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
            c_r1.metric("Separadas no Mês", len(df[(df['data_entrada'].dt.month == m_num) & (df['data_entrada'].dt.year == ano)]))
            c_r2.metric("Retiradas no Mês", len(df[(df['data_retirada'].dt.month == m_num) & (df['data_retirada'].dt.year == ano)]))

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
                        row_idx = sheet.find(str(row['id']), in_column=1).row
                        sheet.update(range_name=f"H{row_idx}:I{row_idx}", values=[["Separada", obter_hora_brasil().strftime("%Y-%m-%d %H:%M:%S")]])
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
                if pd.notnull(row['data_retirada']):
                    diff = obter_hora_brasil() - row['data_retirada']
                    if diff > timedelta(hours=72): st.error("⚠️ Rm foi separada a mais de 72 horas")
                    else: st.success("🟢 Separada dentro das 72 horas")
                if es_admin:
                    with st.form(f"ret_{row['id']}"):
                        quem = st.text_input("Quem retirou?")
                        if st.form_submit_button("Confirmar"):
                            row_idx = sheet.find(str(row['id']), in_column=1).row
                            sheet.update(range_name=f"E{row_idx}:H{row_idx}", values=[[obter_hora_brasil().strftime("%Y-%m-%d %H:%M:%S"), obter_hora_brasil().strftime("%Y-%m-%d %H:%M:%S"), quem, "Concluída"]])
                            recarregar_dados()

    elif nome_tab == "➕ Nova RM":
        with st.form("cad", clear_on_submit=True):
            num = st.text_input("RM (8 dígitos)", max_chars=8)
            sol = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                sheet.append_row([len(df)+1, num, sol, obter_hora_brasil().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta", ""])
                st.success("RM cadastrada!"); recarregar_dados()

    elif nome_tab == "🔍 Consulta":
        busca = st.text_input("RM:", max_chars=8)
        if st.button("Pesquisar"):
            res = df[df['numero_rm'].astype(str) == str(busca)]
            if not res.empty: st.write(f"Status: {res.iloc[0]['status']}")
            else: st.warning("Não encontrada.")

    elif nome_tab == "📊 Histórico":
        st.markdown("<h3 style='text-align: center;'>📊 Histórico Completo</h3>", unsafe_allow_html=True)
        col_c = st.columns([1, 8, 1])[1]
        with col_c:
            df_hist = df.copy()
            if not es_admin: df_hist = df_hist[df_hist['status'] == 'Concluída']
            st.markdown(f"<div style='text-align: center;'>{df_hist[['numero_rm', 'data_retirada', 'quem_retirou', 'status']].fillna('Pendente').to_html(index=False)}</div>", unsafe_allow_html=True)
            if es_admin:
                with st.form("d"):
                    sel = {r['id']: st.checkbox(f"RM: {r['numero_rm']}", key=f"d_{r['id']}") for _, r in df.iterrows()}
                    if st.form_submit_button("🗑️ Deletar"):
                        for i, s in sel.items():
                            if s: sheet.delete_rows(sheet.find(str(i), in_column=1).row)
                        recarregar_dados()

for i, nome in enumerate(nomes := ["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"] if es_admin else ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"]):
    with tabs[i]: mostrar_conteudo(nome)
