import os
import time
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from core.logger import get_logger

logger = get_logger(__name__)

# Timeouts padrão (em ms)
DEFAULT_TIMEOUT = 30_000
SHORT_TIMEOUT   = 5_000


# ──────────────────────────────────────────────
# UTILITÁRIO INTERNO
# ──────────────────────────────────────────────

def _prepare_selector(selector: str) -> str:
    """Adiciona prefixo xpath= se o seletor for XPath."""
    if selector.startswith("/") or selector.startswith("("):
        return f"xpath={selector}"
    return selector


# ──────────────────────────────────────────────
# NAVEGAÇÃO
# ──────────────────────────────────────────────

def goto(page: Page, url: str, wait_until: str = "domcontentloaded") -> None:
    """Navega para uma URL e aguarda o carregamento."""
    logger.info(f"Navegando para: {url}")
    page.goto(url, wait_until=wait_until, timeout=DEFAULT_TIMEOUT)
    logger.debug(f"Página carregada: {page.title()!r}")


def go_back(page: Page) -> None:
    """Volta para a página anterior."""
    logger.debug("Voltando para a página anterior")
    page.go_back(wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)


def reload(page: Page) -> None:
    """Recarrega a página atual."""
    logger.debug(f"Recarregando página: {page.url}")
    page.reload(wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)


# ──────────────────────────────────────────────
# ESPERAS
# ──────────────────────────────────────────────

def wait_for_selector(page: Page, selector: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Aguarda um elemento aparecer no DOM."""
    selector = _prepare_selector(selector)
    logger.debug(f"Aguardando elemento: {selector!r}")
    page.wait_for_selector(selector, timeout=timeout)


def wait_for_selector_hidden(page: Page, selector: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Aguarda um elemento desaparecer do DOM."""
    selector = _prepare_selector(selector)
    logger.debug(f"Aguardando elemento sumir: {selector!r}")
    page.wait_for_selector(selector, state="hidden", timeout=timeout)


def wait_for_navigation(page: Page, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Aguarda a navegação completar."""
    logger.debug("Aguardando navegação completar")
    page.wait_for_load_state("domcontentloaded", timeout=timeout)


def wait_for_network_idle(page: Page, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Aguarda a rede ficar ociosa (útil após requisições AJAX)."""
    logger.debug("Aguardando rede ociosa")
    page.wait_for_load_state("networkidle", timeout=timeout)


def wait(ms: int) -> None:
    """Pausa estática em milissegundos (usar com moderação)."""
    logger.debug(f"Pausa estática de {ms}ms")
    time.sleep(ms / 1000)


def element_exists(page: Page, selector: str, timeout: int = SHORT_TIMEOUT) -> bool:
    """Verifica se um elemento existe na página sem lançar exceção."""
    selector = _prepare_selector(selector)
    try:
        page.wait_for_selector(selector, timeout=timeout)
        logger.debug(f"Elemento encontrado: {selector!r}")
        return True
    except PlaywrightTimeoutError:
        logger.debug(f"Elemento não encontrado: {selector!r}")
        return False


# ──────────────────────────────────────────────
# CLIQUE E INTERAÇÃO
# ──────────────────────────────────────────────

def click(page: Page, selector: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Clica em um elemento."""
    selector = _prepare_selector(selector)
    logger.debug(f"Clicando em: {selector!r}")
    page.wait_for_selector(selector, timeout=timeout)
    page.click(selector)


def click_if_exists(page: Page, selector: str, timeout: int = SHORT_TIMEOUT) -> bool:
    """Clica em um elemento se ele existir. Retorna True se clicou."""
    selector = _prepare_selector(selector)
    if element_exists(page, selector, timeout):
        logger.debug(f"Clique condicional em: {selector!r}")
        page.click(selector)
        return True
    logger.debug(f"Clique condicional ignorado — elemento ausente: {selector!r}")
    return False


def double_click(page: Page, selector: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Duplo clique em um elemento."""
    selector = _prepare_selector(selector)
    logger.debug(f"Duplo clique em: {selector!r}")
    page.wait_for_selector(selector, timeout=timeout)
    page.dblclick(selector)


def hover(page: Page, selector: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Move o mouse sobre um elemento."""
    selector = _prepare_selector(selector)
    logger.debug(f"Hover em: {selector!r}")
    page.wait_for_selector(selector, timeout=timeout)
    page.hover(selector)


# ──────────────────────────────────────────────
# PREENCHIMENTO DE CAMPOS
# ──────────────────────────────────────────────

def fill(page: Page, selector: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Preenche um campo de texto (limpa antes de preencher)."""
    selector = _prepare_selector(selector)
    logger.debug(f"Preenchendo {selector!r} com: {value!r}")
    page.wait_for_selector(selector, timeout=timeout)
    page.fill(selector, value)


def type_slowly(page: Page, selector: str, value: str, delay: int = 50) -> None:
    """Digita caractere por caractere (útil para campos com máscara/autocomplete)."""
    selector = _prepare_selector(selector)
    logger.debug(f"Digitando lentamente em {selector!r}: {value!r}")
    page.wait_for_selector(selector, timeout=DEFAULT_TIMEOUT)
    page.type(selector, value, delay=delay)


def clear_field(page: Page, selector: str) -> None:
    """Limpa o conteúdo de um campo."""
    selector = _prepare_selector(selector)
    logger.debug(f"Limpando campo: {selector!r}")
    page.fill(selector, "")


def select_option(page: Page, selector: str, value: str = None, label: str = None) -> None:
    """Seleciona uma opção em um <select>."""
    selector = _prepare_selector(selector)
    logger.debug(f"Selecionando opção em {selector!r} — value={value!r} label={label!r}")
    page.wait_for_selector(selector, timeout=DEFAULT_TIMEOUT)
    if label:
        page.select_option(selector, label=label)
    elif value:
        page.select_option(selector, value=value)
    else:
        logger.warning(f"select_option chamado sem value nem label para {selector!r}")


def check(page: Page, selector: str) -> None:
    """Marca um checkbox."""
    selector = _prepare_selector(selector)
    logger.debug(f"Marcando checkbox: {selector!r}")
    page.wait_for_selector(selector, timeout=DEFAULT_TIMEOUT)
    page.check(selector)


def uncheck(page: Page, selector: str) -> None:
    """Desmarca um checkbox."""
    selector = _prepare_selector(selector)
    logger.debug(f"Desmarcando checkbox: {selector!r}")
    page.wait_for_selector(selector, timeout=DEFAULT_TIMEOUT)
    page.uncheck(selector)


def press_key(page: Page, selector: str, key: str) -> None:
    """Pressiona uma tecla em um elemento (ex: 'Enter', 'Tab', 'Escape')."""
    selector = _prepare_selector(selector)
    logger.debug(f"Pressionando tecla {key!r} em: {selector!r}")
    page.wait_for_selector(selector, timeout=DEFAULT_TIMEOUT)
    page.press(selector, key)


def get_text(page: Page, selector: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Retorna o texto visível de um elemento."""
    selector = _prepare_selector(selector)
    page.wait_for_selector(selector, timeout=timeout)
    text = page.inner_text(selector).strip()
    logger.debug(f"Texto obtido de {selector!r}: {text!r}")
    return text


def get_value(page: Page, selector: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Retorna o valor de um campo de input."""
    selector = _prepare_selector(selector)
    page.wait_for_selector(selector, timeout=timeout)
    value = page.input_value(selector).strip()
    logger.debug(f"Valor obtido de {selector!r}: {value!r}")
    return value


# ──────────────────────────────────────────────
# DOWNLOAD DE ARQUIVOS
# ──────────────────────────────────────────────

def download_file(page: Page, trigger_selector: str, filename: str, dest_dir: str) -> str:
    """
    Clica em um elemento e aguarda o download do arquivo.

    Args:
        page:             instância da Page do Playwright
        trigger_selector: seletor do botão/link que dispara o download
        filename:         nome com que o arquivo será salvo (ex: "extrato_2024_01.pdf")
        dest_dir:         diretório de destino do arquivo

    Retorna:
        Caminho absoluto do arquivo salvo.
    """
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)

    logger.info(f"Aguardando download de: {filename!r}")
    with page.expect_download() as download_info:
        click(page, trigger_selector)

    download = download_info.value
    download.save_as(dest_path)
    logger.info(f"Arquivo salvo em: {dest_path}")
    return dest_path


# ──────────────────────────────────────────────
# SCREENSHOTS / DEBUG
# ──────────────────────────────────────────────

def screenshot(page: Page, filename: str, dest_dir: str = "debug") -> str:
    """
    Tira um screenshot da página atual.

    Args:
        page:     instância da Page do Playwright
        filename: nome do arquivo (ex: "erro_login.png")
        dest_dir: diretório de destino (padrão: 'debug' na raiz do projeto)

    Retorna:
        Caminho absoluto do screenshot salvo.
    """
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)
    page.screenshot(path=dest_path, full_page=True)
    logger.debug(f"Screenshot salvo em: {dest_path}")
    return dest_path


def screenshot_on_error(page: Page, context_name: str, dest_dir: str = "debug") -> str:
    """
    Tira um screenshot com timestamp para capturar erros.
    Útil em blocos except para diagnóstico.

    Args:
        page:         instância da Page do Playwright
        context_name: nome descritivo do contexto (ex: "login", "extrato")
        dest_dir:     diretório de destino

    Retorna:
        Caminho absoluto do screenshot salvo.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"erro_{context_name}_{timestamp}.png"
    logger.warning(f"Capturando screenshot de erro: {filename}")
    return screenshot(page, filename, dest_dir)