#!/usr/bin/env python3
"""
configs_selenium.py
===================
Constantes, diretórios, URLs e inicialização do driver Chrome antibot.
"""

import os
import time

try:
    import undetected_chromedriver as uc
    from selenium_stealth import stealth
except ImportError as e:
    print(f"[ERRO] Dependência não instalada: {e}")
    print("       Execute primeiro:  instalar.bat")
    raise

# ─── Diretórios ───────────────────────────────────────────────────────────────

BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
EMITIDAS_DIR      = os.path.join(BASE_DIR, "Emitidas")
SEM_CND_DIR       = os.path.join(BASE_DIR, "Sem CND")
PROFILE_DIR       = os.path.join(BASE_DIR, "chrome_perfil")
DEFAULT_DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")

# ─── URLs ─────────────────────────────────────────────────────────────────────

URL_BASE   = "https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj"
URL_PORTAL = "https://servicos.receitafederal.gov.br/"

# ─── Inicialização do driver ──────────────────────────────────────────────────

def criar_driver() -> uc.Chrome:
    os.makedirs(PROFILE_DIR, exist_ok=True)

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--start-maximized")
    options.add_argument("--lang=pt-BR")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    )

    driver = uc.Chrome(options=options, version_main=146)

    # Aguarda Chrome estabilizar (UCD fecha/reabre aba durante inicialização)
    time.sleep(2)
    driver.get("about:blank")
    time.sleep(1)

    stealth(
        driver,
        languages=["pt-BR", "pt", "en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1,2,3,4,5]
            });
            window.chrome = {runtime: {}};
        """
    })

    driver.execute_cdp_cmd("Browser.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": EMITIDAS_DIR,
    })

    return driver