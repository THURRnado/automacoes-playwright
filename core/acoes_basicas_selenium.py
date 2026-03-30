"""
acoes_basicas_selenium.py
=========================
Primitivas humanizadas de baixo nível: clicar e digitar.
Interface propositalmente próxima ao acoes_camoufox.py para facilitar
o reuso entre os dois backends.

Importa de acoes_selenium.py as funções de comportamento já existentes
(delay_humano, mover_mouse_aleatorio) em vez de duplicá-las.
"""

import time
import random

import undetected_chromedriver as uc
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

from core.acoes_selenium import delay_humano, mover_mouse_aleatorio


# ─── Clique humanizado ────────────────────────────────────────────────────────

def clicar(driver: uc.Chrome, elemento: WebElement, timeout: int = 10):
    """
    Aguarda o elemento ficar clicável, move o mouse até ele de forma
    humanizada e então clica.

    Equivalente ao clicar(page, locator) do camoufox.
    """
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(elemento))

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", elemento)
    delay_humano(0.3, 0.7)

    mover_mouse_aleatorio(driver, elemento)
    delay_humano(0.2, 0.5)

    elemento.click()
    delay_humano(0.3, 0.6)


def clicar_js(driver: uc.Chrome, elemento: WebElement):
    """
    Fallback via JavaScript para elementos que resistem ao clique normal
    (ex.: sobreposição de outro elemento, iframe parcial).
    """
    driver.execute_script("arguments[0].click()", elemento)
    delay_humano(0.3, 0.6)


# ─── Digitação humanizada ─────────────────────────────────────────────────────

def digitar(driver: uc.Chrome, elemento: WebElement, texto: str,
            limpar: bool = True):
    """
    Clica no campo, limpa o conteúdo anterior (opcional) e digita
    caractere a caractere com intervalo aleatório.

    Para campos Angular/React usa o setter nativo + eventos para garantir
    que o framework detecte a mudança — mesmo comportamento de
    preencher_cnpj_angular, mas genérico para qualquer campo.

    Equivalente ao digitar(page, locator, texto) do camoufox.
    """
    clicar(driver, elemento)

    if limpar:
        driver.execute_script("""
            var el = arguments[0];
            var setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            setter.call(el, '');
            el.dispatchEvent(new Event('input',  { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        """, elemento)
        delay_humano(0.2, 0.4)

    for char in texto:
        elemento.send_keys(char)
        time.sleep(random.uniform(0.07, 0.17))

    # Dispara blur para acionar validações onblur dos frameworks
    driver.execute_script(
        "arguments[0].dispatchEvent(new Event('blur', { bubbles: true }))",
        elemento,
    )
    delay_humano(0.4, 0.8)


# ─── Espera explícita genérica ────────────────────────────────────────────────

def aguardar_elemento(driver: uc.Chrome, locator: tuple,
                      timeout: int = 10) -> WebElement | None:
    """
    Aguarda um elemento ficar visível e retorna-o, ou None se expirar.
    Uso: aguardar_elemento(driver, (By.CSS_SELECTOR, "input[name='cpfCnpj']"))
    """
    try:
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
    except TimeoutException:
        return None