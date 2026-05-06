#!/usr/bin/env python3
"""
acoes_selenium.py
=================
Funções auxiliares de interação humana, navegação, preenchimento de
formulários e detecção de resultados. Sem estado global — recebem o
driver como parâmetro.
"""

import os
import re
import time
import base64
import random
import shutil

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError as e:
    print(f"[ERRO] Dependência não instalada: {e}")
    print("       Execute primeiro:  instalar.bat")
    raise

from core.configs_selenium import EMITIDAS_DIR, DEFAULT_DOWNLOADS


# ─── Helpers de temporização ──────────────────────────────────────────────────

def delay_humano(min_s: float = 0.5, max_s: float = 1.2):
    time.sleep(random.uniform(min_s, max_s))


# ─── Simulação de comportamento humano ───────────────────────────────────────

def mover_mouse_aleatorio(driver: uc.Chrome, elemento=None):
    """Move o mouse de forma humanizada sobre um elemento ou pela janela."""
    actions = ActionChains(driver)
    if elemento:
        actions.move_to_element_with_offset(
            elemento, random.randint(-40, 40), random.randint(-20, 20)
        ).perform()
        delay_humano(0.15, 0.4)
        actions = ActionChains(driver)
        actions.move_to_element(elemento).perform()
    else:
        w = driver.execute_script("return window.innerWidth")
        h = driver.execute_script("return window.innerHeight")
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, max(200, w - 100))
            y = random.randint(100, max(200, h - 100))
            driver.execute_script(
                "document.dispatchEvent(new MouseEvent('mousemove', "
                "{clientX: arguments[0], clientY: arguments[1], bubbles: true}));",
                x, y
            )
            delay_humano(0.2, 0.6)


def rolar_pagina(driver: uc.Chrome, scrolls: int = None):
    """Rola a página de forma humanizada."""
    n = scrolls or random.randint(3, 6)
    for _ in range(n):
        dist = random.randint(80, 280)
        driver.execute_script(f"window.scrollBy({{top: {dist}, behavior: 'smooth'}})")
        delay_humano(0.6, 1.4)
    delay_humano(0.5, 1.0)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'})")
    delay_humano(0.5, 1.0)


def simular_leitura(driver: uc.Chrome, segundos: float):
    """
    Simula o comportamento humano de 'ler' a página durante X segundos:
    movimentos de mouse, rolagem e pausas aleatórias.
    """
    fim = time.time() + segundos
    while time.time() < fim:
        acao = random.choice(["scroll", "mouse", "pause"])
        if acao == "scroll":
            dist = random.randint(60, 200) * random.choice([1, -1])
            driver.execute_script(
                f"window.scrollBy({{top: {dist}, behavior: 'smooth'}})"
            )
            delay_humano(0.8, 2.0)
        elif acao == "mouse":
            mover_mouse_aleatorio(driver)
            delay_humano(0.5, 1.5)
        else:
            delay_humano(1.0, 3.0)


# ─── Navegação e página ───────────────────────────────────────────────────────

def aguardar_spa(driver: uc.Chrome, timeout: int = 30) -> bool:
    fim = time.time() + timeout
    while time.time() < fim:
        try:
            if driver.execute_script("return document.readyState") == "complete":
                time.sleep(0.5)
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def aceitar_cookies(driver: uc.Chrome):
    try:
        btn = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH,
                "//button[contains(normalize-space(text()),'Aceitar')]"
            ))
        )
        mover_mouse_aleatorio(driver, btn)
        delay_humano(0.4, 0.8)
        btn.click()
        print("  → Cookies aceitos.")
        delay_humano(0.8, 1.5)
    except TimeoutException:
        pass


# ─── Localização de elementos ─────────────────────────────────────────────────

def encontrar_campo_cnpj(driver: uc.Chrome):
    seletores = [
        (By.CSS_SELECTOR, "input[placeholder*='CNPJ']"),
        (By.CSS_SELECTOR, "input[formcontrolname='cnpj']"),
        (By.CSS_SELECTOR, "input[formcontrolname='CNPJ']"),
        (By.CSS_SELECTOR, "input[id*='cnpj' i]"),
        (By.XPATH, "//input[@type='text' or @type='tel' or not(@type)]"),
    ]
    for locator in seletores:
        try:
            campo = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located(locator)
            )
            if campo.is_displayed() and campo.is_enabled():
                print(f"    Campo CNPJ: {locator[1]}")
                return campo
        except (TimeoutException, NoSuchElementException):
            continue
    return None


def encontrar_botao_emitir(driver: uc.Chrome):
    seletores = [
        (By.XPATH, "//button[contains(normalize-space(text()), 'Emitir Certidão')]"),
        (By.XPATH, "//button[contains(normalize-space(text()), 'Emitir')]"),
        (By.XPATH, "//button[contains(normalize-space(text()), 'Consultar')]"),
        (By.XPATH, "//button[@type='submit']"),
    ]
    for locator in seletores:
        try:
            btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable(locator))
            if btn.is_displayed():
                print(f"    Botão: '{btn.text.strip()}'")
                return btn
        except (TimeoutException, NoSuchElementException):
            continue
    return None


# ─── Preenchimento de formulário ──────────────────────────────────────────────

def preencher_cnpj_angular(driver: uc.Chrome, campo, cnpj: str):
    mover_mouse_aleatorio(driver, campo)
    delay_humano(0.3, 0.6)
    campo.click()
    delay_humano(0.3, 0.5)
    # Limpa via JS e dispara eventos Angular
    driver.execute_script("""
        var el = arguments[0];
        var setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, '');
        el.dispatchEvent(new Event('input',  { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    """, campo)
    delay_humano(0.3, 0.5)
    for char in cnpj:
        campo.send_keys(char)
        time.sleep(random.uniform(0.08, 0.18))
    delay_humano(0.8, 1.5)


# ─── PDF e downloads ──────────────────────────────────────────────────────────

def salvar_pdf(driver: uc.Chrome, caminho: str) -> bool:
    try:
        resultado = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "paperWidth": 8.27, "paperHeight": 11.69,
            "marginTop": 0.4, "marginBottom": 0.4,
            "marginLeft": 0.4, "marginRight": 0.4,
            "scale": 1.0,
        })
        with open(caminho, "wb") as f:
            f.write(base64.b64decode(resultado["data"]))
        return True
    except Exception as exc:
        print(f"    [!] Falha ao gerar PDF: {exc}")
        return False


def _snapshot_pasta(pasta: str) -> set:
    """Retorna o conjunto de arquivos existentes na pasta (ou vazio se não existe)."""
    if os.path.isdir(pasta):
        return set(os.listdir(pasta))
    return set()


def aguardar_download(antes_emitidas: set, antes_downloads: set,
                      cnpj: str, timestamp: str, timeout: int = 60) -> str | None:
    """
    Aguarda o download do PDF, que pode ir para EMITIDAS_DIR (via CDP) ou
    para a pasta Downloads padrão do Windows como fallback.

    Monitora ambas as pastas, aguarda .crdownload desaparecer, renomeia
    o arquivo para o padrão CND_CNPJ_TS.pdf e retorna o caminho final.
    """
    destino = os.path.join(EMITIDAS_DIR, f"CND_{cnpj}_{timestamp}.pdf")
    fim = time.time() + timeout
    ultimo_aviso = 0

    while time.time() < fim:
        for pasta, antes in [(EMITIDAS_DIR, antes_emitidas),
                              (DEFAULT_DOWNLOADS, antes_downloads)]:
            if not os.path.isdir(pasta):
                continue
            agora   = set(os.listdir(pasta))
            novos   = agora - antes
            em_prog = [f for f in novos if f.lower().endswith(".crdownload")]
            pdfs    = [f for f in novos if f.lower().endswith(".pdf")]

            if em_prog and time.time() - ultimo_aviso > 5:
                print("    Download em andamento, aguardando...")
                ultimo_aviso = time.time()

            if pdfs and not em_prog:
                src = os.path.join(pasta, sorted(pdfs)[0])
                if src != destino:
                    os.makedirs(EMITIDAS_DIR, exist_ok=True)
                    shutil.move(src, destino)
                return destino

        time.sleep(1)

    return None


# ─── Detecção de diálogos e resultados ───────────────────────────────────────

def tratar_dialogo_cnd_valida(driver: uc.Chrome) -> bool:
    """
    Detecta o modal 'Certidão Válida Encontrada' e clica em 'Emitir Nova Certidão'.
    Retorna True se o diálogo foi encontrado e tratado.
    """
    seletores_btn_nova = [
        (By.XPATH, "//button[contains(normalize-space(text()), 'Emitir Nova Certidão')]"),
        (By.XPATH, "//button[contains(normalize-space(text()), 'Emitir Nova')]"),
        (By.XPATH, "//mat-dialog-container//button[last()]"),
    ]
    for locator in seletores_btn_nova:
        try:
            btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable(locator))
            if btn.is_displayed():
                print("  → Diálogo 'Certidão Válida' detectado — clicando 'Emitir Nova Certidão'")
                mover_mouse_aleatorio(driver, btn)
                delay_humano(0.4, 0.8)
                btn.click()
                delay_humano(1.5, 2.5)
                return True
        except (TimeoutException, NoSuchElementException):
            continue
    return False


def aguardar_resultado(driver: uc.Chrome, janela_original: str,
                       timeout: int = 45) -> str:
    """Aguarda resultado do fluxo SEM diálogo (emissão direta)."""
    fim = time.time() + timeout
    while time.time() < fim:
        if len(driver.window_handles) > 1:
            return "nova_janela"
        try:
            corpo = driver.find_element(By.TAG_NAME, "body").text.lower()
            if any(k in corpo for k in ["certidão emitida", "certidao emitida",
                                         "negativa de débitos", "regularidade fiscal",
                                         "válida até", "certidão negativa"]):
                return "inline_sucesso"
            if "023" in corpo or "tente novamente" in corpo:
                return "erro_023"
            if any(k in corpo for k in ["débitos", "pendência", "irregular",
                                         "não foi possível"]):
                return "inline_erro"
        except Exception:
            pass
        time.sleep(0.8)
    return "timeout"


def limpar_cnpj(cnpj: str) -> str:
    """Remove formatação e valida que o CNPJ tem 14 dígitos."""
    digits = re.sub(r"\D", "", cnpj)
    if len(digits) != 14:
        raise ValueError(f"CNPJ inválido: '{cnpj}' — deve ter 14 dígitos.")
    return digits