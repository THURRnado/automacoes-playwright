import logging
from playwright.sync_api import Page
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def acessar(page: Page, url: str, timeout: int = 30000, wait_until: str = "networkidle") -> bool:
    try:
        logger.info(f"Navegando para: {url}")
        page.goto(url, timeout=timeout, wait_until=wait_until)
        logger.info(f"Página carregada: {page.title()}")
        return True
    except Exception as e:
        logger.error(f"Erro ao acessar {url}: {e}")
        return False


def clicar(page: Page, xpath: str, timeout: int = 10000) -> bool:
    try:
        logger.info(f"Clicando em: {xpath}")
        page.locator(f"xpath={xpath}").click(timeout=timeout)
        return True
    except Exception as e:
        logger.error(f"Erro ao clicar em {xpath}: {e}")
        return False


def digitar(page, xpath: str = None, texto: str = "", limpar: bool = True, timeout: int = 10000, name: str = None) -> bool:
    try:
        if name:
            seletor = f"xpath=//input[@name='{name}']"
        else:
            seletor = f"xpath={xpath}"
        logger.info(f"Digitando '{texto}' em: {seletor}")
        elemento = page.locator(seletor)
        elemento.wait_for(timeout=timeout)
        if limpar:
            elemento.clear()
        elemento.type(texto)
        return True
    except Exception as e:
        logger.error(f"Erro ao digitar em {seletor}: {e}")
        return False


def aguardar_elemento(page: Page, xpath: str, timeout: int = 10000) -> bool:
    try:
        logger.info(f"Aguardando elemento: {xpath}")
        page.locator(f"xpath={xpath}").wait_for(state="visible", timeout=timeout)
        return True
    except Exception as e:
        logger.error(f"Elemento não encontrado {xpath}: {e}")
        return False


def obter_texto(page: Page, xpath: str, timeout: int = 10000) -> str | None:
    try:
        elemento = page.locator(f"xpath={xpath}")
        elemento.wait_for(state="visible", timeout=timeout)
        texto = elemento.inner_text()
        logger.info(f"Texto obtido de {xpath}: '{texto}'")
        return texto
    except Exception as e:
        logger.error(f"Erro ao obter texto de {xpath}: {e}")
        return None


def selecionar_opcao(page: Page, xpath: str, valor: str, timeout: int = 10000) -> bool:
    try:
        logger.info(f"Selecionando '{valor}' em: {xpath}")
        page.locator(f"xpath={xpath}").select_option(valor, timeout=timeout)
        return True
    except Exception as e:
        logger.error(f"Erro ao selecionar opção em {xpath}: {e}")
        return False
    

def entrar_em_iframe(page: Page, xpath: str, timeout: int = 10000):
    try:
        logger.info(f"Entrando no iframe: {xpath}")
        frame = page.frame_locator(f"xpath={xpath}")
        return frame
    except Exception as e:
        logger.error(f"Erro ao entrar no iframe {xpath}: {e}")
        return None
    

def esperar(page: Page, segundos: float) -> None:
    logger.info(f"Aguardando {segundos} segundos...")
    page.wait_for_timeout(segundos * 1000)


def salvar_download(page: Page, xpath: str, pasta: str = "uploads", frame=None) -> bool:
    try:
        os.makedirs(pasta, exist_ok=True)
        alvo = frame if frame else page
        with page.expect_download() as download_info:
            clicar(alvo, xpath)
        download = download_info.value
        caminho = os.path.join(os.path.abspath(pasta), download.suggested_filename)
        download.save_as(caminho)
        logger.info(f"Download salvo em: {caminho}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar download: {e}")
        return False
    

def baixar_pdf_url(page: Page, url: str, nome_arquivo: str = "documento.pdf", pasta: str = "uploads") -> bool:
    try:
        os.makedirs(pasta, exist_ok=True)
        response = page.request.get(url)
        caminho = os.path.join(os.path.abspath(pasta), nome_arquivo)
        with open(caminho, "wb") as f:
            f.write(response.body())
        logger.info(f"PDF salvo em: {caminho}")
        return True
    except Exception as e:
        logger.error(f"Erro ao baixar PDF: {e}")
        return False