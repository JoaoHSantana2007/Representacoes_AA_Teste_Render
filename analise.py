from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =========================
# 🎯 PESOS
# =========================
PESOS_POSITIVOS = {
    "fica instituído": 7,
    "será composto": 7,
    "designar os seguintes membros": 7,
    "alterar designações": 7,
    "para compor": 2,
    "comitê": 1,
    "comissao": 1,
    "conselho": 1,
    "grupo de trabalho": 1,
    "grupo de assessoramento": 1,
    "grupo de assessoria": 1,
    "grupo conjunto": 1,
    "grupo especial": 1,
    "grupo técnico": 1,
    "subcomissao": 1,
    "subcomite": 1,
    "subgrupo": 1,
    "designados": 1,
    "designado": 1,
    "nomeados": 1,
    "nomeado": 1,
    "indicados": 1,
    "indicado": 1,
    "membro": 1,
    "representante": 1,
}

PESOS_NEGATIVOS = {
    "incluir": 1,
    "incluído": 1,
    "incluída": 1,
    "substitui": 1,
    "substituído": 1,
    "substituída": 1,
    "excluir": 1,
    "excluído": 1,
    "excluída": 1,
    "regulamenta": 1,
    "institui": 1,
    "estabelece": 1,
    "disposições": 1,
    "resolução": 1,
    "licitação": 1,
}

# =========================
# 🌐 SESSION OTIMIZADA
# =========================
def criar_session():
    session = requests.Session()

    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )

    adapter = HTTPAdapter(max_retries=retries)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })

    return session

SESSION = criar_session()

# =========================
# 📄 TEXTO (RÁPIDO)
# =========================
def pegar_texto_fast(url):
    try:
        response = SESSION.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        paragrafos = soup.find_all(class_="dou-paragraph")

        return " ".join(p.get_text() for p in paragrafos).lower()

    except Exception:
        return ""

# =========================
# 🧠 SCORE
# =========================
def calcular_score(texto):
    score_pos = sum(peso for palavra, peso in PESOS_POSITIVOS.items() if palavra in texto)
    score_neg = sum(peso for palavra, peso in PESOS_NEGATIVOS.items() if palavra in texto)
    return score_pos - score_neg

# =========================
# 🔎 BOTÃO PRÓXIMA
# =========================
def _encontrar_botao_proxima(driver):
    try:
        botao = driver.find_element(By.ID, "rightArrow")
    except Exception:
        return None

    if not botao.is_displayed():
        return None

    classes = (botao.get_attribute("class") or "").lower()
    aria_disabled = (botao.get_attribute("aria-disabled") or "").lower()
    disabled_attr = botao.get_attribute("disabled")

    if "disabled" in classes or aria_disabled == "true" or disabled_attr is not None:
        return None

    return botao

# =========================
# 📄 PAGINAÇÃO
# =========================
def _coletar_links_paginados(driver, max_paginas=200):
    wait = WebDriverWait(driver, 10)
    links_unicos = []
    vistos = set()
    pagina = 1

    while pagina <= max_paginas:
        resultados = driver.find_elements(By.CSS_SELECTOR, "a[href*='/web/dou/']")

        for r in resultados:
            href = r.get_attribute("href")
            if not href or href in vistos:
                continue

            titulo = (r.text or "").strip()
            vistos.add(href)
            links_unicos.append((titulo if titulo else "Sem titulo", href))

        botao_proxima = _encontrar_botao_proxima(driver)
        if not botao_proxima:
            break

        marcador = resultados[0] if resultados else None

        driver.execute_script("arguments[0].click();", botao_proxima)

        try:
            if marcador:
                wait.until(EC.staleness_of(marcador))
        except TimeoutException:
            break

        pagina += 1

    return links_unicos

# =========================
# ⚡ PROCESSAR UM LINK
# =========================
def processar_link(item):
    titulo, link = item

    texto = pegar_texto_fast(link)
    score = calcular_score(texto)

    positivas = [p for p in PESOS_POSITIVOS if p in texto]
    negativas = [p for p in PESOS_NEGATIVOS if p in texto]

    return {
        "Documento": titulo,
        "PDF": f"[PDF]({link})",
        "Score": score,
        "Palavras positivas": ", ".join(positivas),
        "Palavras negativas": ", ".join(negativas),
    }

# =========================
# 🚀 FUNÇÃO PRINCIPAL
# =========================
def analisar_links(url_busca, palavras_usuario, status=None, progress=None):
    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(url_busca)

        links = _coletar_links_paginados(driver)
        total = len(links)

        if status:
            status.markdown(f"🌐 **{total} documentos encontrados**")

        resumo = []

        # 🔥 PARALELIZAÇÃO
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(processar_link, item) for item in links]

            for i, future in enumerate(as_completed(futures)):
                if progress:
                    progress.progress(int((i / max(total, 1)) * 100))

                try:
                    resultado = future.result()
                    resumo.append(resultado)
                except Exception:
                    continue

        if status:
            status.markdown("✅ Finalizado!")

        return resumo

    finally:
        driver.quit()

# =========================
# 📊 TABELA
# =========================
def gerar_tabela(resumo):
    df = pd.DataFrame(resumo)

    if df.empty:
        return df

    def destacar_linha(row):
        score = row["Score"]

        if score >= 5:
            return ["background-color: #e6f4ea"] * len(row)
        elif score > 0:
            return ["background-color: #fff9c4"] * len(row)
        return [""] * len(row)

    return df.style.apply(destacar_linha, axis=1)