from playwright.sync_api import sync_playwright
import os

def iniciar_navegador(
    headless: bool = False,
    slow_mo: int = 0,
    pasta_downloads: str = "uploads",
    cert_path: str = None,
    key_path: str = None,
    cert_origin: str = None,
):
    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=headless,
        slow_mo=slow_mo,
        args=["--disable-pdf-viewer"]
    )

    client_certificates = []
    if cert_path and key_path and cert_origin:
        client_certificates.append({
            "origin": cert_origin,
            "certPath": cert_path,
            "keyPath": key_path,
        })

    context = browser.new_context(
        locale="pt-BR",
        viewport={"width": 1366, "height": 768},
        accept_downloads=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        client_certificates=client_certificates or None,
    )

    page = context.new_page()

    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    pasta = os.path.abspath(pasta_downloads)
    os.makedirs(pasta, exist_ok=True)
    page._downloads_path = pasta

    return playwright, browser, context, page


def fechar_navegador(playwright, browser):
    browser.close()
    playwright.stop()