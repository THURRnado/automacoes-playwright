#!/usr/bin/env python3
"""
joao_pessoa_selenium.py
=======================
Automação de login no portal de Nota Fiscal de João Pessoa.

Empresa para uso:
    - NOME : ABC DISTRIBUIDORA JOAO PESSOA LTDA
    - CNPJ : 04813255000124
    - IE   : 161339387

Uso:
    python joao_pessoa_selenium.py
"""

import os
import time

from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from core.configs_selenium import criar_driver
from core.acoes_selenium import simular_leitura, mover_mouse_aleatorio, delay_humano
from core.acoes_basicas_selenium import clicar, clicar_js, digitar, aguardar_elemento

load_dotenv()

# ─── Constantes ───────────────────────────────────────────────────────────────

CNPJ       = "04813255000124"
URL_WARMUP = "https://www.google.com.br"
URL_LOGIN  = (
    "https://receita.joaopessoa.pb.gov.br/notafiscal/paginas/portal/"
    "index.html#/login"
)
MAX_TENTATIVAS_CAPTCHA = 3


# ─── Helpers de captcha ───────────────────────────────────────────────────────

def _captcha_tem_desafio(driver) -> bool:
    """Retorna True se o reCAPTCHA abriu o modal de desafio (bframe)."""
    try:
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//iframe[contains(@src, 'bframe')]")
            )
        )
        return True
    except TimeoutException:
        return False


def _campo_cnpj(driver):
    return aguardar_elemento(driver, (By.CSS_SELECTOR, "input[name='cpfCnpj']"))


def _campo_senha(driver):
    return aguardar_elemento(driver, (By.CSS_SELECTOR, "input[name='senha']"))


def _preencher_credenciais(driver, cnpj: str, senha: str):
    """Preenche CNPJ e senha na página de login."""
    input_cnpj = _campo_cnpj(driver)
    input_senha = _campo_senha(driver)

    digitar(driver, input_cnpj, cnpj)
    delay_humano(1.0, 2.0)
    digitar(driver, input_senha, senha)
    simular_leitura(driver, 2.0)


# ─── Fluxo principal ──────────────────────────────────────────────────────────

def executar_automacao():
    senha = os.getenv("SENHA_ABC")
    if not senha:
        raise EnvironmentError(
            "Variável SENHA_ABC não encontrada. "
            "Verifique o arquivo .env na raiz do projeto."
        )

    driver = criar_driver()

    try:
        # ── 1. Warm-up ───────────────────────────────────────────────────────
        print("Aquecendo sessão...")
        driver.get(URL_WARMUP)
        simular_leitura(driver, 4.0)

        # ── 2. Página de login ───────────────────────────────────────────────
        print("Acessando página de login...")
        driver.get(URL_LOGIN)
        simular_leitura(driver, 3.0)

        # ── 3. Credenciais ───────────────────────────────────────────────────
        print("Digitando credenciais...")
        _preencher_credenciais(driver, CNPJ, senha)

        # ── 4. reCAPTCHA ─────────────────────────────────────────────────────
        for tentativa in range(1, MAX_TENTATIVAS_CAPTCHA + 1):
            print(f"Tentativa captcha {tentativa}/{MAX_TENTATIVAS_CAPTCHA}...")

            iframe_captcha = aguardar_elemento(
                driver,
                (By.XPATH, "//iframe[@title='reCAPTCHA']"),
                timeout=10,
            )
            if iframe_captcha is None:
                print("  [!] iframe do reCAPTCHA não encontrado.")
                break

            driver.switch_to.frame(iframe_captcha)
            checkbox = aguardar_elemento(
                driver,
                (By.CSS_SELECTOR, "#recaptcha-anchor"),
                timeout=5,
            )

            mover_mouse_aleatorio(driver)
            if checkbox:
                try:
                    clicar(driver, checkbox)
                except Exception:
                    clicar_js(driver, checkbox)

            driver.switch_to.default_content()
            delay_humano(2.0, 3.0)

            if _captcha_tem_desafio(driver):
                print("  → Desafio detectado — recarregando página e repetindo...")
                driver.get(URL_LOGIN)
                simular_leitura(driver, 3.0)
                _preencher_credenciais(driver, CNPJ, senha)
                continue

            print("  ✔ Captcha resolvido.")
            break
        else:
            print("  ✖ Não foi possível resolver o captcha após as tentativas.")
            driver.save_screenshot("erro_captcha.png")
            return False

        # ── 5. Login ─────────────────────────────────────────────────────────
        print("Clicando em Entrar...")
        btn_entrar = aguardar_elemento(
            driver,
            (By.XPATH, "//button[normalize-space(text())='Entrar']"),
            timeout=10,
        )
        if btn_entrar is None:
            print("  [!] Botão Entrar não encontrado.")
            driver.save_screenshot("erro_btn_entrar.png")
            return False

        clicar(driver, btn_entrar)
        simular_leitura(driver, 5.0)

        # ── 6. Verifica login ─────────────────────────────────────────────────
        url_atual = driver.current_url
        if "login" in url_atual.lower():
            print("  ✖ Ainda na página de login — credenciais recusadas ou erro.")
            driver.save_screenshot("erro_login.png")
            return False

        print(f"  ✔ Login efetuado com sucesso. URL: {url_atual}")
        return True

    except Exception as exc:
        print(f"Erro na automação: {exc}")
        try:
            driver.save_screenshot("erro_inesperado.png")
        except Exception:
            pass
        return False

    finally:
        try:
            driver.quit()
        except Exception:
            pass