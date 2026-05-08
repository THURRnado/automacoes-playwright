import os
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from core.logger import get_logger

logger = get_logger(__name__)

# Detecta automaticamente se está em produção (Linux) ou desenvolvimento (Windows)
IS_HEADLESS = os.name != "nt"  # True no Linux, False no Windows

# Diretório padrão de downloads (pasta uploads do projeto)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")


def get_launch_options() -> dict:
    """Retorna as opções de lançamento do browser otimizadas."""
    args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-background-networking",
        "--disable-default-apps",
        "--disable-sync",
        "--disable-translate",
        "--disable-notifications",
        "--no-first-run",
        "--no-default-browser-check",
        "--mute-audio",
        "--disable-pdf-viewer",
    ]

    return {
        "headless": IS_HEADLESS,
        "args": args,
        "slow_mo": 0 if IS_HEADLESS else 100,
        "downloads_path": UPLOADS_DIR,
        "chromium_sandbox": False,
    }


def get_context_options() -> dict:
    """Retorna as opções do contexto do browser."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)

    return {
        "accept_downloads": True,
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
        "viewport": {"width": 1280, "height": 720},
        "java_script_enabled": True,
        "bypass_csp": True,
        "ignore_https_errors": True,
    }


def create_browser_session() -> tuple[sync_playwright, Browser, BrowserContext, Page]:
    """
    Cria e retorna uma sessão completa do Playwright.

    Retorna:
        (playwright, browser, context, page)

    Uso:
        pw, browser, context, page = create_browser_session()
        try:
            # seu código aqui
        finally:
            close_browser_session(pw, browser)
    """
    mode = "headless" if IS_HEADLESS else "com interface"
    logger.info(f"Iniciando sessão do browser — modo: {mode}")

    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(**get_launch_options())
        logger.debug("Browser Chromium iniciado com sucesso")

        context = browser.new_context(**get_context_options())
        logger.debug(f"Contexto criado — downloads em: {UPLOADS_DIR}")

        # Bloqueia recursos desnecessários para agilizar a automação
        context.route("**/*", _block_unnecessary_resources)

        page = context.new_page()

        # Ignora diálogos automáticos (alerts, confirms, prompts)
        page.on("dialog", lambda dialog: (
            logger.debug(f"Diálogo ignorado automaticamente: [{dialog.type}] {dialog.message}"),
            dialog.dismiss()
        ))

        logger.info("Sessão do browser criada com sucesso")
        return pw, browser, context, page

    except Exception as e:
        logger.error(f"Falha ao criar sessão do browser: {e}")
        raise


def _block_unnecessary_resources(route) -> None:
    """Bloqueia tipos de recursos que não são necessários para a automação."""
    blocked_types = {"image", "media", "font"}
    if route.request.resource_type in blocked_types:
        logger.debug(f"Recurso bloqueado: [{route.request.resource_type}] {route.request.url[:80]}")
        route.abort()
    else:
        route.continue_()


def close_browser_session(pw: sync_playwright, browser: Browser) -> None:
    """Encerra o browser e o Playwright de forma segura."""
    logger.info("Encerrando sessão do browser")
    try:
        browser.close()
        logger.debug("Browser encerrado")
    except Exception as e:
        logger.warning(f"Erro ao fechar browser: {e}")
    finally:
        pw.stop()
        logger.debug("Playwright finalizado")