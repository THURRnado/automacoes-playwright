from playwright.sync_api import sync_playwright
import os

def iniciar_navegador(headless: bool = False, slow_mo: int = 0, pasta_downloads: str = "uploads"):
    playwright = sync_playwright().start()
    
    browser = playwright.chromium.launch(
        headless=headless,
        slow_mo=slow_mo,
        args=["--disable-pdf-viewer"]
    )
    
    context = browser.new_context(
        viewport={"width": 1080, "height": 720},
        accept_downloads=True,
    )
    
    page = context.new_page()
    
    # Armazena o caminho para uso nas funções de download
    pasta = os.path.abspath(pasta_downloads)
    os.makedirs(pasta, exist_ok=True)
    page._downloads_path = pasta
    
    return playwright, browser, context, page


def fechar_navegador(playwright, browser):
    browser.close()
    playwright.stop()