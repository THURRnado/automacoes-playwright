import os
import shutil
import threading
import time
import uuid

from playwright.sync_api import Page, BrowserContext, Browser

from core.browser import create_browser_session, close_browser_session
from core.actions import goto, wait_for_selector
from core.logger import get_logger

from dotenv import load_dotenv
load_dotenv()

logger = get_logger(__name__)

# Constantes
SEFAZ_URL = "https://www.sefaz.pb.gov.br/servirtual"
DOWNLOAD_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "uploads", "sefaz", "pdf"
)

# ID padrao para uso antes da integracao com Django
DEFAULT_USER_ID = 1


def login(user_id: int = DEFAULT_USER_ID, request_id: str = None):
    """
    Realiza login no SEFAZ e retorna a sessao do Playwright.

    Args:
        user_id:    ID do usuario Django (padrao: 1 ate integracao)
        request_id: identificador unico da requisicao (gerado automaticamente se omitido)

    Retorna:
        tuple: (pw, browser, context, page, download_dir)

    Uso:
        pw, browser, context, page, download_dir = login()
        try:
            # seu codigo aqui
        finally:
            close_browser_session(pw, browser)
    """

    # Validar credenciais
    user_name = os.getenv("SEFAZ_USER")
    user_password = os.getenv("SEFAZ_PASSWORD")

    if not user_name or not user_password:
        logger.error("Credenciais nao configuradas nas variaveis de ambiente")
        raise ValueError("SEFAZ_USER e SEFAZ_PASSWORD devem estar configuradas no .env")

    # Gerar request_id unico se nao fornecido
    if request_id is None:
        thread_id = threading.get_ident()
        timestamp = int(time.time() * 1000000)
        request_id = f"{thread_id}_{timestamp}_{uuid.uuid4().hex[:8]}"

    user_id_str = str(user_id)
    download_dir = os.path.join(DOWNLOAD_BASE_PATH, f"{user_id_str}_{request_id}")

    logger.info(f"Iniciando login -- usuario: {user_id_str} | request_id: {request_id}")

    pw = None
    browser = None

    try:
        # Criar diretorio de download isolado para esta execucao
        os.makedirs(download_dir, exist_ok=True)
        logger.debug(f"Diretorio de download criado: {download_dir}")

        # Iniciar sessao do browser
        pw, browser, context, page = create_browser_session()

        # Acessa a pagina do SEFAZ
        logger.debug(f"Acessando SEFAZ: {SEFAZ_URL}")
        goto(page, SEFAZ_URL)

        # Aguarda o iframe de login carregar
        wait_for_selector(page, '#atf-login iframe')
        login_frame = page.frame_locator('#atf-login iframe').first

        logger.debug("Preenchendo credenciais")
        login_frame.locator('#form-cblogin-username input').fill(user_name)
        login_frame.locator('#form-cblogin-password input').first.fill(user_password)

        logger.debug("Submetendo formulario de login")
        login_frame.locator('input[name="btnAvancar"]').click()

        # Aguarda confirmacao login
        login_frame = page.frame_locator('#atf-login iframe').first
        login_frame.locator('#cronometro_div').wait_for(timeout=30_000)
        logger.info(f"Login realizado com sucesso — usuário: {user_id_str}")

        return pw, browser, context, page, download_dir

    except Exception as e:
        logger.error(f"Erro durante login do usuario {user_id_str}: {e}", exc_info=True)

        # Rollback: fecha o browser
        if browser:
            try:
                close_browser_session(pw, browser)
            except Exception as cleanup_error:
                logger.error(f"Erro ao fechar browser no rollback: {cleanup_error}")

        # Rollback: remove diretorio de download criado
        if os.path.exists(download_dir):
            try:
                shutil.rmtree(download_dir)
                logger.info(f"Rollback: diretorio removido apos falha -- {download_dir}")
            except Exception as dir_error:
                logger.error(f"CRITICO: nao foi possivel remover diretorio apos falha: {dir_error}")

        raise