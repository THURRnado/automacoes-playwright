# services/relat_omis_inad.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.login import login
from core.browser import close_browser_session
from core.actions import goto, fill, click, wait_for_network_idle
from core.logger import get_logger

logger = get_logger(__name__)

CONSULTA_URL = (
    "https://www4.sefaz.pb.gov.br/atf/cob/COBf_OmiGeralConsGenericaContribuinte.do"
    "?idSERVirtual=S&h=https://www.sefaz.pb.gov.br/ser/servirtual/credenciamento/info"
)

PROCESS_DIR = "relat_omis_inad"

DEFAULT_EMPRESA_IE = "161339387"


def run(
    empresa_ie: str = DEFAULT_EMPRESA_IE,
) -> str:
    """
    Executa o processo de download do relatório de Omissão/Inadimplência no SEFAZ.

    Args:
        empresa_ie: Inscrição estadual da empresa

    Retorna:
        Caminho absoluto do arquivo PDF baixado.
    """
    logger.info(f"Iniciando Relatório Omissão/Inadimplência — IE: {empresa_ie}")

    pw, browser, context, page, download_dir = login()
    process_download_dir = os.path.join(download_dir, PROCESS_DIR)
    os.makedirs(process_download_dir, exist_ok=True)
    logger.debug(f"Diretório de download: {process_download_dir}")

    download = None

    try:
        # Acessa a página de consulta
        logger.info(f"Acessando página de consulta: {CONSULTA_URL}")
        goto(page, CONSULTA_URL)

        # Preenche IE no iframe
        logger.debug(f"Preenchendo IE no iframe: {empresa_ie}")
        iframe = page.frame_locator('iframe[name="cmpHumanoInst"]').first
        iframe.locator('input[name="hidNrDocumentocmpHumanoInst"]').fill(empresa_ie)
        iframe.locator('input[name="btnPesquisar"]').click()

        # Aguarda razão social ser preenchida
        logger.debug("Aguardando preenchimento da Razão Social")
        page.wait_for_function(
            """() => {
                const iframe = document.querySelector('iframe[name="cmpHumanoInst"]');
                if (!iframe) return false;
                const campo = iframe.contentDocument.querySelector('input[name="hidNoHumanoInstcmpHumanoInst"]');
                return campo && campo.value !== '';
            }""",
            timeout=30_000,
        )
        logger.debug("Razão Social preenchida — empresa encontrada")

        # Clica em Gerar Arquivo e captura o download
        logger.info("Clicando em Gerar Arquivo — aguardando download do PDF")
        with page.expect_download() as download_info:
            click(page, 'input[name="btnConsultar"]')

        download = download_info.value
        filename = download.suggested_filename or f"relatorio_omissao_{empresa_ie}.do"

        # Garante extensão .pdf
        if not filename.lower().endswith(".pdf"):
            filename = os.path.splitext(filename)[0] + ".pdf"

        dest_path = os.path.join(process_download_dir, filename)
        download.save_as(dest_path)
        logger.info(f"PDF salvo em: {dest_path}")

        return dest_path

    except Exception as e:
        logger.error(f"Erro durante Relatório Omissão/Inadimplência: {e}", exc_info=True)
        raise

    finally:
        if download:
            try:
                download.delete()
            except Exception:
                pass
        close_browser_session(pw, browser)
        logger.info("Sessão encerrada")


if __name__ == "__main__":
    path = run()
    print(f"PDF salvo em: {path}")