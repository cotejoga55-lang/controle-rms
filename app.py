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

sheet = conectar_banco()
dados = carregar_dados()
df = pd.DataFrame(dados)
df['data_entrada'] = pd.to_datetime(df['data_entrada'], errors='coerce')
df['data_saida'] = pd.to_datetime(df['data_saida'], errors='coerce')
df['data_retirada'] = pd.to_datetime(df['data_retirada'], errors='coerce')
es_admin = (st.session_state['perfil_logado'] == "Admin")

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state['perfil_logado']}**")
    if st.button("🚪 Sair", key="btn_sair_fixed"): st.session_state['perfil_logado'] = None; st.rerun()

st.title("📦 Sistema de Controle de RMs")

# CORREÇÃO 1: Definir a lista de abas uma única vez para evitar vazamento visual
lista_abas = ["📊 Dashboard", "📋 Painel", "📦 Pend. Retirada", "➕ Nova RM", "🔍 Consulta", "📊 Histórico"] if es_admin else ["📋 Painel", "📦 Pend. Retirada", "🔍 Consulta", "📊 Histórico"]
tabs = st.tabs(lista_abas)

def mostrar_conteudo(nome_tab):
    if nome_tab == "📊 Dashboard":
        avisos = df[df['cobranca'].str.contains("está cobrando|Comentario adicionado", case=False, na=False)]
        if not avisos.empty:
            with st.popover(f"🔔 NOTIFICAÇÕES ({len(avisos)})"):
                for _, row in avisos.iterrows():
                    st.warning(f"{row['cobranca']} na RM {row['numero_rm']}!")
                    if st.button(f"Limpar {row['numero_rm']}", key=f"clr_ntf_{row['id']}"):
                        sheet.update_cell(sheet.find(str(row['id']), in_column=1).row, 9, ""); st.rerun()
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

    elif nome_tab == "📋 Painel":
        for _, row in df[df['status'].isin(['Aberta', 'Em Separação'])].iterrows():
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

    elif nome_tab == "📦 Pend. Retirada":
        for _, row in df[df['status'] == 'Separada'].iterrows():
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

    elif nome_tab == "📊 Histórico":
        st.markdown("<h3 style='text-align: center;'>📊 Histórico Completo</h3>", unsafe_allow_html=True)
        col_c = st.columns([1, 8, 1])[1]
        with col_c:
            st.markdown(f"<div style='text-align: center;'>{df[['numero_rm', 'data_retirada', 'quem_retirou', 'status']].fillna('Pendente').to_html(index=False)}</div>", unsafe_allow_html=True)
            if es_admin:
                with st.form("form_del_hist"):
                    sel = {r['id']: st.checkbox(f"RM: {r['numero_rm']}", key=f"del_chk_{r['id']}") for _, r in df.iterrows()}
                    if st.form_submit_button("🗑️ Deletar Selecionadas"):
                        for i, s in sel.items():
                            if s: sheet.delete_rows(sheet.find(str(i), in_column=1).row)
                        recarregar_dados()

    elif nome_tab == "➕ Nova RM":
        with st.form("cad_rm", clear_on_submit=True):
            num = st.text_input("RM (8 dígitos)", max_chars=8)
            sol = st.text_input("Solicitante")
            if st.form_submit_button("Cadastrar"):
                sheet.append_row([max([int(r['id']) for r in sheet.get_all_records() if str(r['id']).isdigit()] + [0]) + 1, num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta", ""])
                st.success("RM cadastrada!"); recarregar_dados()

    elif nome_tab == "🔍 Consulta":
        lista_rms = df['numero_rm'].dropna().astype(str).unique().tolist()
        busca = st.selectbox("Pesquisar RM:", options=lista_rms, index=None, placeholder="Digite ou selecione a RM...")
        
        if st.button("Pesquisar"):
            if busca:
                res = df[df['numero_rm'].astype(str) == str(busca).strip()]
                if not res.empty:
                    rm = res.iloc[0]
                    
                    with st.container(border=True):
                        st.markdown(f"### 📦 RM: {rm['numero_rm']}")
                        st.divider()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**👤 Solicitante:** {rm['solicitante']}")
                            
                            # CORREÇÃO 2: Lógica atualizada para a data exibida
                            status_atual = rm['status']
                            
                            if status_atual in ["Separada", "Concluída"] and pd.notna(rm.get('data_saida')) and str(rm.get('data_saida')) != 'NaT':
                                data_formatada = pd.to_datetime(rm['data_saida']).strftime('%d/%m/%Y %H:%M')
                                st.markdown(f"**⏳ Data de Separação:** {data_formatada}")
                            else:
                                data_entrada = rm.get('data_entrada')
                                if pd.notna(data_entrada) and str(data_entrada) != 'NaT':
                                    data_formatada = pd.to_datetime(data_entrada).strftime('%d/%m/%Y %H:%M')
                                else:
                                    data_formatada = "Não registrada"
                                st.markdown(f"**📅 RM adicionada:** {data_formatada}")
                            
                        with col2:
                            if status_atual == "Concluída":
                                icone = "🟢"
                            elif status_atual in ["Em Separação", "Separada"]:
                                icone = "🟡"
                            else:
                                icone = "🔴"
                                
                            st.markdown(f"**📌 Status:** {icone} {status_atual}")
                else: 
                    st.warning("Não encontrada.")
            else:
                st.warning("Por favor, selecione ou digite uma RM válida para pesquisar.")

# Usa a variável lista_abas definida acima para garantir que as abas não se misturem
for i, nome in enumerate(lista_abas):
    with tabs[i]: 
        mostrar_conteudo(nome)
