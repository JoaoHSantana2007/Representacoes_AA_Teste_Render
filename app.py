## atualmente utiliza:
## mesclav3.py

import streamlit as st
from linkbusca import obter_link_busca
from analise import analisar_links, gerar_tabela

st.title("Scanner Representações - MD")

palavras_fixas = [
    "instituir", "institui", "representantes",
    "indicacao", "indicações", "indicacoes",
    "ficam designados", "fica designado",
    "ficam designadas", "fica designada",
    "grupo de trabalho", "grupo de trabalhos",
    "grupo de trabalaho", "grupo trabalho",
    "comite", "comitê", "comites", "comitês",
    "comissao", "comissão", "comissoes", "comissões"
]

entrada = st.text_input(
    "Digite palavras-chave adicionais (opcional)",
    ""
)
palavras_usuario = [p.strip() for p in entrada.split(",") if p.strip()]
palavras = list(set(palavras_fixas + palavras_usuario))

st.caption("Inclui automaticamente: instituir, institui, representantes, indicação, ficam designados, grupo de trabalho, comitê, comissão (e todas suas variações)")

if st.button("Verificar TODOS os resultados"):
    status = st.empty()
    progress = st.progress(0)

    # Buscamos o link da pesquisa de hoje
    # Funcao do arquivo linkbusca.py
    url_busca = obter_link_busca() 

    # Analisamos os arquivos
    # Funcao do arquivo analise.py
    resumo = analisar_links(url_busca, palavras, status=status, progress=progress)

    # Geramos tabela
    # Funcao do arquivo analise.py
    styled_df = gerar_tabela(resumo)

    st.subheader("📊 Resultado")
    st.markdown(styled_df.to_html(escape=False), unsafe_allow_html=True)

    st.markdown(
        f"<p style='color:gray; font-size:12px;'>Palavras pesquisadas: {', '.join(palavras)}</p>",
        unsafe_allow_html=True
    )