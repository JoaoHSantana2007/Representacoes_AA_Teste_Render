## app.py

from datetime import date

import streamlit as st
from linkbusca import obter_link_busca
from analise import analisar_links, gerar_tabela
from gerar_relatorio import gerar_csv_relatorio
from baixar_pdf import baixar_pdf
from enviar_email import enviar_email_representacoes

st.title("Scanner Representações - MD")

# palavras_fixas = [
#     # estruturas colegiadas
#     "comitê", "comissao", "conselho", "grupo de trabalho",
#     "grupo de assessoramento", "grupo de assessoria",
#     "grupo de assessoria especial", "grupo conjunto",
#     "grupo especial", "grupo técnico", "grupo técnico de trabalho",
#     "grupo temporário", "subcomissao", "subcomite", "subgrupo",

#     # ação típica de representação
#     "designados", "designado", "designar",
#     "nomeados", "nomeado", "nomear",
#     "indicados", "indicado", "indicar",
#     "designa", "nomeia", "indica",

#     # composição de pessoas
#     "titular", "suplente", "membro", "membros",
#     "representante", "representantes",
#     "integrante", "integrantes",

#     # cargos dentro de comitês
#     "coordenador", "coordenadora",
#     "presidente", "vice-presidente",
#     "relator", "secretario", "secretária",

#     # padrões institucionais fortes
#     "ficam designados", "ficam nomeados", "ficam indicados",
#     "para compor", "compor o comite", "compor o conselho",
#     "no âmbito do", "no ambito do",

#     "ficam designados para compor",
#     "ficam designados os representantes",
#     "designados para compor",
#     "composição do comitê",
#     "titular e suplente",
#     "no âmbito do comitê"
# ]

entrada = st.text_input(
    "Digite palavras-chave adicionais (opcional)",
    ""
)
palavras_usuario = [p.strip() for p in entrada.split(",") if p.strip()]
# palavras = list(set(palavras_fixas + palavras_usuario))

# st.caption("Inclui automaticamente: instituir, institui, representantes, indicação, ficam designados, grupo de trabalho, comitê, comissão (e todas suas variações)")

col_data_inicial, col_data_final = st.columns(2)
with col_data_inicial:
    data_inicial = st.date_input("Data inicial", value=date.today(), format="DD/MM/YYYY")
with col_data_final:
    data_final = st.date_input("Data final", value=date.today(), format="DD/MM/YYYY")

if st.button("Verificar TODOS os resultados"):
    if data_inicial > data_final:
        st.error("A data inicial não pode ser maior que a data final.")
        st.stop()

    status = st.empty()
    progress = st.progress(0)

    data_inicial_str = data_inicial.strftime("%d/%m/%Y")
    data_final_str = data_final.strftime("%d/%m/%Y")

    # Buscamos o link da pesquisa de hoje
    # Funcao do arquivo linkbusca.py
    url_busca = obter_link_busca(data_inicial_str, data_final_str)

    # Analisamos os arquivos
    # Funcao do arquivo analise.py
    resumo = analisar_links(url_busca, palavras_usuario, status=status, progress=progress)

    # Geramos relatório CSV
    # Funcao do arquivo gerar_relatorio.py
    gerar_csv_relatorio(resumo)

    # Baixamos os PDFs
    # Funcao do arquivo baixar_pdf.py
    baixar_pdf()  

    # Enviamos email 
    # Funcao do arquivo enviar_email.py
    enviar_email_representacoes()

    # Geramos tabela
    # Funcao do arquivo analise.py
    styled_df = gerar_tabela(resumo)

    st.subheader("📊 Resultado")
    st.markdown(styled_df.to_html(escape=False), unsafe_allow_html=True)

    

    ##st.markdown(
##        f"<p style='color:gray; font-size:12px;'>Palavras pesquisadas: {', '.join(palavras)}</p>",
##        unsafe_allow_html=True
##    )
    st.caption(f"Período consultado: {data_inicial_str} a {data_final_str}")   