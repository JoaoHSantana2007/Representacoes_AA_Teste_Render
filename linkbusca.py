from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os

def criar_driver():
    options = webdriver.ChromeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # caminhos do Render
    chrome_bin = "/usr/bin/chromium"
    chromedriver_bin = "/usr/bin/chromedriver"

    # verifica se existem
    if os.path.exists(chrome_bin) and os.path.exists(chromedriver_bin):
        options.binary_location = chrome_bin
        service = Service(chromedriver_bin)
        return webdriver.Chrome(service=service, options=options)

    # fallback local
    from webdriver_manager.chrome import ChromeDriverManager
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

def obter_link_busca():

    driver = criar_driver()

    try:
        driver.get("https://www.in.gov.br/materia")

        wait = WebDriverWait(driver, 30)

        # campo de busca
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "search-bar"))
        )

        search_input.clear()
        search_input.send_keys("Ministério da Defesa")

        # pesquisa avançada
        wait.until(
            EC.element_to_be_clickable((By.ID, "toggle-search-advanced"))
        ).click()

        # resultado exato
        wait.until(
            EC.element_to_be_clickable((By.XPATH, "//label[@for='tipo-pesquisa-1']"))
        ).click()

        # personalizado
        wait.until(
            EC.element_to_be_clickable((By.XPATH, "//label[@for='personalizado']"))
        ).click()

        # enter
        search_input.send_keys(Keys.ENTER)

        # espera carregar resultados
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )

        # 🔗 pega o link final da busca
        link_resultado = driver.current_url

        return link_resultado

    finally:
        driver.quit()