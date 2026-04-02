import logging
from playwright.sync_api import Page, FrameLocator
import os
import random
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def acessar(page: Page, url: str, timeout: int = 30000, wait_until: str = "networkidle"):
    try:
        logger.info(f"Navegando para: {url}")
        page.goto(url, timeout=timeout, wait_until=wait_until)
        logger.info(f"Página carregada: {page.title()}")
    except Exception as e:
        logger.error(f"Erro ao acessar {url}: {e}")
        raise e
 
 
def clicar(alvo, xpath: str, timeout: int = 20000):
    try:
        logger.info(f"Clicando em: {xpath}")
        alvo.locator(f"xpath={xpath}").click(timeout=timeout)
    except Exception as e:
        logger.error(f"Erro ao clicar em {xpath}: {e}")
        raise e


def clicar_por_texto(alvo, texto: str, exato: bool = True, timeout: int = 20000):
    try:
        logger.info(f"Clicando por texto: '{texto}'")
        alvo.get_by_text(texto, exact=exato).click(timeout=timeout)
    except Exception as e:
        logger.error(f"Erro ao clicar por texto '{texto}': {e}")
        raise e
 
 
def digitar(alvo, xpath: str, texto: str = "", timeout: int = 20000):
    """Digita em um elemento localizado por XPath. Sempre limpa antes via fill()."""
    try:
        logger.info(f"Digitando em: xpath={xpath}")
        elemento = alvo.locator(f"xpath={xpath}")
        elemento.wait_for(state="visible", timeout=timeout)
        elemento.fill(texto)
    except Exception as e:
        logger.error(f"Erro ao digitar em xpath={xpath}: {e}")
        raise e
 
 
def digitar_por_name(alvo, name: str, texto: str = "", timeout: int = 20000):
    """Digita em um input localizado pelo atributo name."""
    seletor = f"xpath=//input[@name='{name}']"
    try:
        logger.info(f"Digitando em: {seletor}")
        elemento = alvo.locator(seletor)
        elemento.wait_for(state="visible", timeout=timeout)
        elemento.fill(texto)
    except Exception as e:
        logger.error(f"Erro ao digitar em {seletor}: {e}")
        raise e


def limpar(alvo, xpath: str, timeout: int = 20000):
    try:
        logger.info(f"Limpando campo: {xpath}")
        elemento = alvo.locator(f"xpath={xpath}")
        elemento.wait_for(state="visible", timeout=timeout)
        elemento.fill("")
    except Exception as e:
        logger.error(f"Erro ao limpar campo {xpath}: {e}")
        raise e
 
 
def aguardar_elemento(alvo, xpath: str, state: str = "visible", timeout: int = 20000):
    """
    Aguarda um elemento atingir o estado desejado.
    States válidos: 'attached', 'detached', 'visible', 'hidden'.
    """
    try:
        logger.info(f"Aguardando elemento ({state}): {xpath}")
        alvo.locator(f"xpath={xpath}").wait_for(state=state, timeout=timeout)
    except Exception as e:
        logger.error(f"Elemento não encontrado ({state}) {xpath}: {e}")
        raise e
 
 
def elemento_existe(alvo, xpath: str, timeout: int = 5000) -> bool:
    """Retorna True se o elemento existir e estiver visível, False caso contrário."""
    try:
        alvo.locator(f"xpath={xpath}").wait_for(state="visible", timeout=timeout)
        logger.info(f"Elemento encontrado: {xpath}")
        return True
    except Exception:
        logger.info(f"Elemento não encontrado: {xpath}")
        return False
 
 
def obter_texto(alvo, xpath: str, timeout: int = 10000) -> str:
    try:
        elemento = alvo.locator(f"xpath={xpath}")
        elemento.wait_for(state="visible", timeout=timeout)
        texto = elemento.inner_text()
        logger.info(f"Texto obtido de {xpath}: '{texto}'")
        return texto
    except Exception as e:
        logger.error(f"Erro ao obter texto de {xpath}: {e}")
        raise e
 
 
def selecionar_opcao(alvo, xpath: str, valor: str, timeout: int = 10000):
    try:
        logger.info(f"Selecionando '{valor}' em: {xpath}")
        alvo.locator(f"xpath={xpath}").select_option(valor, timeout=timeout)
    except Exception as e:
        logger.error(f"Erro ao selecionar opção em {xpath}: {e}")
        raise e
 
 
def entrar_em_iframe(page: Page, xpath: str, timeout: int = 10000) -> FrameLocator:
    try:
        logger.info(f"Entrando no iframe: {xpath}")
        page.locator(f"xpath={xpath}").wait_for(state="attached", timeout=timeout)
        frame = page.frame_locator(f"xpath={xpath}")
        return frame
    except Exception as e:
        logger.error(f"Erro ao entrar no iframe {xpath}: {e}")
        raise e
 
 
def esperar(page: Page, segundos: float) -> None:
    logger.info(f"Aguardando {segundos} segundos (Hard Sleep)...")
    page.wait_for_timeout(segundos * 1000)
 
 
def tirar_screenshot(page: Page, nome: str = "screenshot", pasta: str = "temp_screenshots") -> str:
    """
    Salva um screenshot da página atual. Útil para debug em produção.
    Retorna o caminho absoluto da imagem salva.
    """
    try:
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(os.path.abspath(pasta), f"{nome}.png")
        page.screenshot(path=caminho, full_page=True)
        logger.info(f"Screenshot salvo em: {caminho}")
        return caminho
    except Exception as e:
        logger.error(f"Erro ao tirar screenshot '{nome}': {e}")
        raise e
 
 
def salvar_download(page: Page, xpath: str, pasta: str = "temp_downloads", frame=None, timeout: int = 60000, nome_arquivo: str = None) -> str:
    """
    Clica em um elemento que dispara um download e salva o arquivo localmente.
    Retorna o caminho absoluto do arquivo baixado.
    """
    try:
        os.makedirs(pasta, exist_ok=True)
        alvo = frame if frame else page

        with page.expect_download(timeout=timeout) as download_info:
            alvo.locator(f"xpath={xpath}").click()

        download = download_info.value
        nome_final = nome_arquivo if nome_arquivo else download.suggested_filename
        caminho_absoluto = os.path.join(os.path.abspath(pasta), nome_final)
        download.save_as(caminho_absoluto)
        logger.info(f"Download salvo em: {caminho_absoluto}")

        return caminho_absoluto
    except Exception as e:
        logger.error(f"Erro ao salvar download no xpath {xpath}: {e}")
        raise e