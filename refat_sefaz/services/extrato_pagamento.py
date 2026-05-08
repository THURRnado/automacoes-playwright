import os

from core.login import login
from core.browser import close_browser_session
from core.actions import goto, fill, click, wait_for_selector, wait_for_network_idle
from core.logger import get_logger

logger = get_logger(__name__)

# URL do processo
EXTRATO_URL = (
    "https://www4.sefaz.pb.gov.br/atf/arr/ARRf_ConsultarExtrPgtoCont.do"
    "?idSERVirtual=S&h=https://www.sefaz.pb.gov.br/ser/servirtual/credenciamento/info"
)

# Pasta de destino do processo
PROCESS_DIR = "extrato_pagamento"

# Valores fixos para teste (substituir por parâmetros ao integrar ao Django)
DEFAULT_DT_INICIO  = "01/01/2026"
DEFAULT_DT_FINAL   = "31/01/2026"
DEFAULT_EMPRESA_IE = "161339387"  # Inscrição estadual da empresa


def run(
    dt_inicio: str  = DEFAULT_DT_INICIO,
    dt_final: str   = DEFAULT_DT_FINAL,
    empresa_ie: str = DEFAULT_EMPRESA_IE,
) -> str:
    """
    Executa o processo de download do extrato de pagamento na SEFAZ.

    Args:
        dt_inicio:  Data inicial no formato DD/MM/AAAA
        dt_final:   Data final no formato DD/MM/AAAA
        empresa_ie: Inscrição estadual da empresa

    Retorna:
        Caminho absoluto do arquivo PDF baixado.
    """
    logger.info(f"Iniciando extrato de pagamento — IE: {empresa_ie} | {dt_inicio} a {dt_final}")

    pw, browser, context, page, download_dir = login()

    process_download_dir = os.path.join(download_dir, PROCESS_DIR)
    os.makedirs(process_download_dir, exist_ok=True)
    logger.debug(f"Diretório de download do processo: {process_download_dir}")

    try:
        # Acessa a página do processo
        logger.info(f"Acessando página do extrato: {EXTRATO_URL}")
        goto(page, EXTRATO_URL)

        # Preenche as datas
        logger.debug(f"Preenchendo período: {dt_inicio} a {dt_final}")
        fill(page, 'input[name="edtDataInicial"]', dt_inicio)
        fill(page, 'input[name="edtDataFinal"]', dt_final)

        # Acessa o iframe do componente contribuinte e preenche a IE
        logger.debug(f"Preenchendo IE no iframe: {empresa_ie}")
        inner_frame = page.frame_locator('iframe[name="cmpContribuinte"]').first
        inner_frame.locator('input[name="hidNrDocumentocmpContribuinte"]').fill(empresa_ie)

        # Clica em Pesquisar
        logger.debug("Clicando em Pesquisar")
        inner_frame.locator('input[name="btnPesquisar"]').click()

        # Aguarda o campo Nome/Razão Social ser preenchido (confirma retorno da pesquisa)
        logger.debug("Aguardando preenchimento da Razão Social")
        page.wait_for_function(
            """() => {
                const iframe = document.querySelector('iframe[name="cmpContribuinte"]');
                if (!iframe) return false;
                const campo = iframe.contentDocument.querySelector('input[name="hidNoHumanoInstcmpContribuinte"]');
                return campo && campo.value !== '';
            }""",
            timeout=30_000,
        )
        logger.debug("Razão Social preenchida — empresa encontrada")

        # Clica em Consultar na página principal
        logger.debug("Clicando em Consultar")
        with context.expect_page() as new_page_info:
            click(page, 'input[name="Submit"]')

        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")

        # Aguarda e salva o download do PDF
        logger.info("Aguardando download do PDF")
        with new_page.expect_download() as download_info:
            pass

        download = download_info.value
        filename = download.suggested_filename or "extrato_pagamento.pdf"
        dest_path = os.path.join(process_download_dir, filename)
        download.save_as(dest_path)
        logger.info(f"Download concluído: {dest_path}")

        # Fecha a nova aba e retorna para a original
        new_page.close()
        page.bring_to_front()
        logger.debug("Nova aba fechada — retornando para aba original")

        return dest_path

    except Exception as e:
        logger.error(f"Erro durante extrato de pagamento: {e}", exc_info=True)
        raise

    finally:
        close_browser_session(pw, browser)
        logger.info("Sessão encerrada")


if __name__ == "__main__":
    path = run()
    print(f"Arquivo salvo em: {path}")