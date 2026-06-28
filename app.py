import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# CONFIGURAÇÕES DE ACESSO
# =====================================================================
CREDENCIAIS = {
    "Admin": {"usuario": "admin", "senha": "12345"},
    "Visitante": {"usuario": "visitante", "senha": "123"}
}

# =====================================================================
# CONFIGURAÇÕES DE E-MAIL
# =====================================================================
EMAIL_REMETENTE = "seu_email_bot@gmail.com"
SENHA_REMETENTE = "sua_senha_de_app_aqui"
LISTA_NOTIFICACAO = ["equipe1@empresa.com", "chefe@empresa.com"]

def enviar_email(assunto, corpo):
    try:
        msg = MIMEText(corpo, 'html')
        msg['Subject'] = assunto
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = ", ".join(LISTA_NOTIFICACAO)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
            server.sendmail(EMAIL_REMETENTE, LISTA_NOTIFICACAO, msg.as_string())
    except Exception:
        pass 

# =====================================================================
# CONEXÃO GOOGLE SHEETS (ATUALIZADA PARA STREAMLIT CLOUD)
# =====================================================================
def conectar_banco():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # Pega as credenciais do "Secrets" do Streamlit Cloud
        creds_dict = st.secrets["gcp"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("controle_rms").sheet1
        return sheet
    except Exception as e:
        st.error(f"Erro ao conectar com a Planilha: {e}. Verifique se as credenciais estão no 'Secrets'.")
        st.stop()

def ler_dados(sheet):
    dados = sheet.get_all_records()
    if not dados:
        return pd.DataFrame(columns=['id', 'numero_rm', 'solicitante', 'data_entrada', 'data_saida', 'data_retirada', 'quem_retirou', 'status'])
    return pd.DataFrame(dados)

def adicionar_linha(sheet, numero_rm, solicitante, data_entrada, status):
    dados = sheet.get_all_records()
    if dados:
        maior_id = max([int(r['id']) for r in dados if str(r['id']).isdigit()] + [0])
        novo_id = maior_id + 1
    else:
        novo_id = 1
    sheet.append_row([novo_id, numero_rm, solicitante, data_entrada, "", "", "", status])

def atualizar_linha_completa(sheet, id_rm, numero_rm, solicitante, data_entrada, data_saida, data_retirada, quem_retirou, status):
    cell = sheet.find(str(id_rm), in_column=1)
    if cell:
        valores = [
            str(id_rm), str(numero_rm), str(solicitante), str(data_entrada),
            str(data_saida) if pd.notna(data_saida) and data_saida else "",
            str(data_retirada) if pd.notna(data_retirada) and data_retirada else "",
            str(quem_retirou) if pd.notna(quem_retirou) and quem_retirou else "",
            str(status)
        ]
        sheet.update(range_name=f"A{cell.row}:H{cell.row}", values=[valores])

def deletar_linha(sheet, id_rm):
    cell = sheet.find(str(id_rm), in_column=1)
    if cell:
        sheet.delete_rows(cell.row)

# =====================================================================
# TELA DE LOGIN E INTERFACE (O RESTANTE DO SEU CÓDIGO)
# =====================================================================
st.set_page_config(page_title="Controle de RMs", layout="wide")

if 'perfil_logado' not in st.session_state:
    st.session_state['perfil_logado'] = None

if st.session_state['perfil_logado'] is None:
    st.title("🔑 Login - Sistema de Controle de RMs")
    col_login, _ = st.columns([1, 2])
    with col_login:
        usuario_input = st.text_input("Usuário:")
        senha_input = st.text_input("Senha:", type="password")
        if st.button("Acessar Sistema", use_container_width=True):
            if usuario_input == CREDENCIAIS["Admin"]["usuario"] and senha_input == CREDENCIAIS["Admin"]["senha"]:
                st.session_state['perfil_logado'] = "Administrador"
                st.rerun()
            elif usuario_input == CREDENCIAIS["Visitante"]["usuario"] and senha_input == CREDENCIAIS["Visitante"]["senha"]:
                st.session_state['perfil_logado'] = "Visitante"
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    st.stop()

with st.sidebar:
    st.write(f"👤 Perfil: **{st.session_state['perfil_logado']}**")
    if st.button("🚪 Sair da Conta"):
        st.session_state['perfil_logado'] = None
        st.rerun()

st.title("📦 Sistema de Controle de RMs")
sheet = conectar_banco()
df = ler_dados(sheet)

# [O RESTO DO SEU CÓDIGO DE PROCESSAMENTO E ABAS SEGUE AQUI IGUAL...]
# (Como o código é longo, apenas certifique-se de manter as funções de 
# interface que você já tinha abaixo desta linha)