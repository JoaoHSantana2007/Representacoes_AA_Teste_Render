import re
import base64
import pandas as pd

from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# renomeia o nome do arquivo para evitar caracteres invalidos no nome do arquivo
def renomear(texto: str) -> str:
    REGEX_NOME = re.compile(r'[\\/:*?"<>|]+')
    return REGEX_NOME.sub(" ", str(texto or "documento")).strip().replace(" ", "_") or "documento"

# cria o webdriver do Chrome para acessaro os links e baixar os arquivos em PDF
def criar_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

# imprime a pagina em PDF
def imprimir_pagina_em_pdf(driver, url: str, caminho_saida: Path, timeout: int = 30) -> None:
    driver.get(url)
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
     
    pdf_data = driver.execute_cdp_cmd(
        "Page.printToPDF",
        {
            "printBackground": True,
            "preferCSSPageSize": True,
        },
    )
    caminho_saida.write_bytes(base64.b64decode(pdf_data["data"]))

# faz o downloud dos arquivos em pdf
def baixar_pdf(caminho_csv: str = "relatorio.csv", pasta_saida: str = "downloads_pdfs") -> dict:
    df = pd.read_csv(caminho_csv)
    if "PDF" not in df.columns:
        raise ValueError("Coluna PDF nao encontrada")

    # cria a pasta de destino se nao existir
    destino = Path(pasta_saida)
    destino.mkdir(parents=True, exist_ok=True)

    # limpa a pasta dos pdf 
    for arquivo in destino.glob("*.pdf"):
        try:
            arquivo.unlink()
        except:
            return {
                "mensagem": "Erro ao limpar pasta ",
            }

    if df.empty == True:
        return {
            "mensagem": "CSV vazio",
        }
    
    driver = criar_driver()

    # percorre os links no arquivo csv e baixa os arquivos em pdf
    try:
        for linha in df[["Documento", "PDF"]].fillna("").to_dict("records"):
            nome = renomear(linha["Documento"])
            url = str(linha["PDF"]).strip()
            try:
                caminho = destino / f"{nome}.pdf"
                i = 1
                while caminho.exists():
                    caminho = destino / f"{nome}_{i}.pdf"
                    i += 1

                imprimir_pagina_em_pdf(driver, url, caminho)

            except:
                return {
                    "mensagem": "Erro ao baixar arquivo",
                }
    finally:
        driver.quit()