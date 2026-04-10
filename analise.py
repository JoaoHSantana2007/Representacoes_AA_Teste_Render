# pesquisa.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

def pegar_texto(driver):
    paragrafos = driver.find_elements(By.CLASS_NAME, "dou-paragraph")
    return " ".join([p.text for p in paragrafos]).lower()

def verificar_palavras(texto, palavras):
    resultado = {}
    for p in palavras:
        resultado[p] = p.lower() in texto
    return resultado

def analisar_links(url_busca, palavras, status=None, progress=None):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    resumo = []
    detalhes = []
    try:
        if status: status.markdown("🔎 **Filtrando buscas...**")
        if progress: progress.progress(10)

        driver.get(url_busca)
        driver.implicitly_wait(5)

        resultados = driver.find_elements(By.CSS_SELECTOR, "a[href*='/web/dou/']")
        links = [(r.text, r.get_attribute("href")) for r in resultados]
        total_links = len(links)

        if status: status.markdown(f"🌐 **Abrindo resultados... {total_links} encontrados**")
        if progress: progress.progress(20)

        for i, (titulo, link) in enumerate(links):
            if progress:
                progresso = 30 + int((i / total_links) * 60)
                progress.progress(progresso)

            if status:
                status.markdown(
                    f"📊 **Analisando documentos {i+1}/{total_links}**<br><small>{titulo}</small>",
                    unsafe_allow_html=True
                )

            driver.get(link)
            driver.implicitly_wait(5)

            texto = pegar_texto(driver)
            resultado = verificar_palavras(texto, palavras)

            encontradas = [p for p, v in resultado.items() if v]
            qtd = len(encontradas)
            total = len(palavras)

            resumo.append({
                "Documento": titulo,
                "Match": f"{qtd}/{total}",
                "PDF": f"[PDF]({link})",
                "Encontradas": ", ".join(encontradas)
            })

            detalhes.append((titulo, link, resultado))

        if progress: progress.progress(100)
        if status: status.markdown("✅ **Finalizado!**")

        return resumo

    finally:
        driver.quit()

def gerar_tabela(resumo):
    dados_tabela = []
    for r in resumo:
        link_pdf = r["PDF"].split("(")[1].replace(")", "")
        dados_tabela.append({
            "Documento": r["Documento"],
            "Match": r["Match"],
            "PDF": f'<a href="{link_pdf}" target="_blank">pdf</a>',
            "Palavras encontradas": r["Encontradas"]
        })

    df = pd.DataFrame(dados_tabela)
    df["_qtd"] = df["Match"].apply(lambda x: int(x.split("/")[0]))

    def destacar_linha(row):
        if row["_qtd"] > 0:
            return ["background-color: #e6f4ea"] * len(row)
        return [""] * len(row)

    styled_df = df.style.apply(destacar_linha, axis=1)
    styled_df = styled_df.hide(axis="columns", subset=["_qtd"])
    return styled_df