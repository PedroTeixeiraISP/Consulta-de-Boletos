import streamlit as st
import pandas as pd
import os
import re

# 1. Configuração da página e layout do Portal
st.set_page_config(
    page_title="Portal de Boletos - Consulta de Lançamentos",
    page_icon="📑",
    layout="wide"
)

# Estilização visual para tornar o portal profissional
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #1E3A8A;
        font-weight: bold;
    }
    .subtitle {
        text-align: center;
        color: #4B5563;
        margin-bottom: 30px;
    }
    .contact-section {
        background-color: #F3F4F6;
        padding: 20px;
        border-radius: 10px;
        margin-top: 50px;
        border-left: 5px solid #10B981;
    }
    .contact-section a {
        color: #10B981;
        text-decoration: none;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>📑 Portal de Consulta Financeira</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Valide seus dados abaixo para acessar os lançamentos em aberto e boletos.</p>", unsafe_allow_html=True)

# 2. Função segura para carregar a base Excel
@st.cache_data
def carregar_base():
    nome_arquivo = "Boletos do dia.xlsx"
    if os.path.exists(nome_arquivo):
        # Lê a planilha forçando as colunas críticas como texto para não perder zeros ou quebrar formatos
        df = pd.read_excel(nome_arquivo, dtype={'CNPJ/CPF': str, 'Linha Digitável (IPTE)': str})
        # Remove espaços em branco invisíveis no início ou fim dos títulos das colunas
        df.columns = df.columns.str.strip()
        return df
    else:
        st.error(f"⚠️ Erro crítico: O arquivo '{nome_arquivo}' não foi encontrado na raiz do repositório.")
        return None

df_base = carregar_base()

if df_base is not None:
    # 3. Formulário de Validação Inicial por CPF/CNPJ
    with st.form("form_validacao"):
        st.subheader("Acesso ao Painel")
        cpf_cnpj_input = st.text_input("Digite seu CPF ou CNPJ (apenas números):", max_chars=14).strip()
        botao_validar = st.form_submit_button("Consultar Lançamentos")

    if botao_validar:
        if not cpf_cnpj_input:
            st.warning("Por favor, preencha o campo de CPF/CNPJ para realizar a validação.")
        else:
            # Limpa entradas mantendo somente os números digitados
            cpf_cnpj_limpo = re.sub(r'\D', '', cpf_cnpj_input)
            
            # Padroniza a coluna do Excel limpando traços e pontos para uma validação perfeita
            df_base['CPF_LIMPO'] = df_base['CNPJ/CPF'].astype(str).str.replace(r'\D', '', regex=True)
            
            # Realiza o filtro na base de dados buscando correspondência exata
            df_cliente = df_base[df_base['CPF_LIMPO'] == cpf_cnpj_limpo]

            # 4. Exibição da Tabela Dinâmica e Segura
            if not df_cliente.empty:
                responsavel_nome = df_cliente['Responsável'].iloc[0]
                st.success(f"✅ Validação concluída! Olá, {responsavel_nome}. Seguem seus lançamentos abaixo:")
                
                for idx, linha in df_cliente.iterrows():
                    # --- FORMATAÇÃO DE VALORES (Padrão R$ 1.236,25) ---
                    if pd.notnull(linha['Valor Original']) and isinstance(linha['Valor Original'], (int, float)):
                        valor_orig = f"R$ {linha['Valor Original']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    else:
                        valor_orig = f"R$ {linha['Valor Original']}".replace('.', ',') if pd.notnull(linha['Valor Original']) else "-"

                    if pd.notnull(linha['Valor atualizado']) and isinstance(linha['Valor atualizado'], (int, float)):
                        valor_atual = f"R$ {linha['Valor atualizado']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    elif pd.notnull(linha['Valor atualizado']):
                        valor_atual = f"R$ {linha['Valor atualizado']}".replace('.', ',')
                    else:
                        valor_atual = "-"
                    
                    # --- FORMATAÇÃO DA DATA DE COMPETÊNCIA (DD/MM/AAAA) ---
                    data_comp = linha['Mês de Competência']
                    if isinstance(data_comp, pd.Timestamp):
                        data_comp_formatada = data_comp.strftime('%d/%m/%Y')
                    elif isinstance(data_comp, str):
                        data_comp_formatada = data_comp
                    else:
                        data_comp_formatada = str(data_comp)

                    # --- FORMATAÇÃO DA DATA DE VENCIMENTO ---
                    data_venc = linha['Data de Vencimento']
                    if isinstance(data_venc, pd.Timestamp):
                        data_venc = data_venc.strftime('%d/%m/%Y')
                    
                    # --- CÓDIGO DE BARRAS / LINHA DIGITÁVEL COMO TEXTO COMPLETO ---
                    linha_digitavel = ""
                    if pd.notnull(linha['Linha Digitável (IPTE)']):
                        linha_digitavel = str(linha['Linha Digitável (IPTE)']).strip()
                        if linha_digitavel.endswith('.0'):
                            linha_digitavel = linha_digitavel[:-2]
                    
                    # Monta o nome dinâmico do arquivo baseado nas colunas
                    nome_pdf_esperado = f"Boleto - {linha['Responsável']} - {linha['Histórico']}.pdf"
                    caminho_completo_pdf = os.path.join("boletos", nome_pdf_esperado)
                    
                    # Estruturação visual em blocos (tabela responsiva)
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
                        
                        with col1:
                            st.markdown(f"**Histórico:** {linha['Histórico']}")
                            st.markdown(f"**Competência:** {data_comp_formatada}")
                            st.caption(f"Unidade: {linha['UNIDADE']}")
                        with col2:
                            st.markdown(f"**Vencimento:** {data_venc}")
                            st.markdown(f"**Atraso:** {linha['Dias em Atraso']} dias")
                        with col3:
                            st.markdown(f"**Valor Original:** {valor_orig}")
                            st.markdown(f"**Valor Updated/Atualizado:** {valor_atual}")
                        with col4:
                            # 1º: Validação e exibição do Botão de Download no topo da coluna (se o arquivo existir)
                            if os.path.exists(caminho_completo_pdf):
                                with open(caminho_completo_pdf, "rb") as f:
                                    pdf_bytes = f.read()
                                st.download_button(
                                    label="📥 Baixar Boleto PDF",
                                    data=pdf_bytes,
                                    file_name=nome_pdf_esperado,
                                    mime="application/pdf",
                                    key=f"btn_{idx}"
                                )
                            
                            # 2º: Apresenta a linha digitável estruturada logo abaixo do botão (se existir)
                            if linha_digitavel:
                                st.caption("Código de Barras (Linha Digitável):")
                                st.code(linha_digitavel, language="text")
                                
                    st.markdown("---")
            else:
                st.error("❌ Documento não cadastrado ou divergente. Por favor, verifique os dígitos inseridos.")

# 5. Central de Atendimento e Suporte (Whatsapp) no Rodapé fixo
st.markdown("""
    <div class='contact-section'>
        <h4>🛎️ Não conseguiu baixar seu boleto ou precisa de auxílio?</h4>
        <p>Se houver qualquer divergência ou se o botão de baixar boleto não estiver disponível, converse diretamente com nosso setor financeiro pelo WhatsApp nos links abaixo:</p>
        <ul>
            <li><strong>Suporte Financeiro 1:</strong> <a href="https://wa.me/5519971457048" target="_blank">Chamar no WhatsApp: (19) 97145-7048</a></li>
            <li><strong>Suporte Financeiro 2:</strong> <a href="https://wa.me/5519996202422" target="_blank">Chamar no WhatsApp: (19) 99620-2422</a></li>
        </ul>
        <p><small>* Atendimento de segunda a sexta-feira em horário comercial.</small></p>
    </div>
""", unsafe_allow_html=True)
