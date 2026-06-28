import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES E CONEXÃO
# =====================================================================
def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds).open("controle_rms").get_worksheet(0)

def ler_dados(sheet):
    dados = sheet.get_all_records()
    return pd.DataFrame(dados) if dados else pd.DataFrame(columns=['id', 'numero_rm', 'solicitante', 'data_entrada', 'data_saida', 'data_retirada', 'quem_retirou', 'status'])

# =====================================================================
# INTERFACE E LÓGICA
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")
st.title("📦 Sistema de Controle de RMs")
sheet = conectar_banco()
df = ler_dados(sheet)

tab1, tab2, tab3 = st.tabs(["📋 Painel", "➕ Nova RM", "📊 Histórico"])

# --- ABA 1: PAINEL (Com opção de Concluir) ---
with tab1:
    st.subheader("RMs em Aberto")
    abertas = df[df['status'] == 'Aberta']
    if not abertas.empty:
        for index, row in abertas.iterrows():
            with st.expander(f"RM: {row['numero_rm']} - Solicitante: {row['solicitante']}"):
                if st.button(f"✅ Marcar como Concluída", key=f"btn_{row['id']}"):
                    st.session_state[f'concluir_{row["id"]}'] = True
                
                if st.session_state.get(f'concluir_{row["id"]}'):
                    with st.form(f"form_{row['id']}"):
                        quem = st.text_input("Quem retirou?")
                        if st.form_submit_button("Confirmar Retirada"):
                            # Atualiza planilha
                            cell = sheet.find(str(row['id']), in_column=1)
                            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            sheet.update(range_name=f"E{cell.row}:H{cell.row}", values=[[agora, agora, quem, "Concluída"]])
                            st.success("Registrado com sucesso!")
                            st.rerun()
    else:
        st.info("Nenhuma RM pendente.")

# --- ABA 2: NOVA RM (Com limpeza automática) ---
with tab2:
    st.subheader("Cadastrar Nova RM")
    with st.form("form_cadastro", clear_on_submit=True): # O clear_on_submit limpa tudo
        num = st.text_input("Número da RM")
        sol = st.text_input("Solicitante")
        if st.form_submit_button("Cadastrar"):
            if num and sol:
                dados = sheet.get_all_records()
                novo_id = max([int(r['id']) for r in dados if str(r['id']).isdigit()] + [0]) + 1
                sheet.append_row([novo_id, num, sol, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "Aberta"])
                st.success("RM cadastrada! Campos limpos para nova entrada.")
            else:
                st.warning("Preencha todos os campos.")

# --- ABA 3: HISTÓRICO ---
with tab3:
    st.subheader("Histórico Geral")
    st.dataframe(df, use_container_width=True)
