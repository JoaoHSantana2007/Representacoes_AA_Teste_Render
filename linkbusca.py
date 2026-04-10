from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def obter_link_busca():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

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