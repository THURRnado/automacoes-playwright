# services/guia_estadual.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.login import login
from core.browser import close_browser_session
from core.actions import (
    goto, fill, click, wait_for_network_idle, element_exists
)
from core.logger import get_logger

logger = get_logger(__name__)

CONSULTA_URL = (
    "https://www4.sefaz.pb.gov.br/atf/fis/FISf_ConsultarFatura.do"
    "?idSERVirtual=S&h=https://www.sefaz.pb.gov.br/ser/servirtual/credenciamento/info"
)

PROCESS_DIR = "guia_estadual"

DEFAULT_EMPRESA_IE     = "161339387"
DEFAULT_DT_VENC_INICIO = "01/01/2026"
DEFAULT_DT_VENC_FIM    = "31/01/2026"


def run(
    empresa_ie: str     = DEFAULT_EMPRESA_IE,
    dt_venc_inicio: str = DEFAULT_DT_VENC_INICIO,
    dt_venc_fim: str    = DEFAULT_DT_VENC_FIM,
) -> str | None:
    """
    Executa o processo de emissão da guia estadual na SEFAZ.

    Args:
        empresa_ie:      Inscrição estadual da empresa
        dt_venc_inicio:  Data inicial de vencimento no formato DD/MM/AAAA
        dt_venc_fim:     Data final de vencimento no formato DD/MM/AAAA

    Retorna:
        Caminho absoluto do arquivo PDF baixado, ou None se não houver guias.
    """
    logger.info(f"Iniciando guia estadual — IE: {empresa_ie} | vencimento: {dt_venc_inicio} a {dt_venc_fim}")

    pw, browser, context, page, download_dir = login()
    process_download_dir = os.path.join(download_dir, PROCESS_DIR)
    os.makedirs(process_download_dir, exist_ok=True)
    logger.debug(f"Diretório de download: {process_download_dir}")

    download = None

    try:
        logger.info(f"Acessando página: {CONSULTA_URL}")
        goto(page, CONSULTA_URL)

        # Preenche IE no iframe do contribuinte e busca a empresa
        logger.debug(f"Preenchendo IE no iframe: {empresa_ie}")
        iframe = page.frame_locator('iframe[name="cmpContribuinte"]').first
        iframe.locator('input[name="hidNrDocumentocmpContribuinte"]').fill(empresa_ie)
        iframe.locator('input[name="btnPesquisar"]').click()

        # Aguarda razão social ser preenchida (confirma que a empresa foi encontrada)
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

        # Preenche o intervalo de datas de vencimento
        logger.debug(f"Preenchendo data de vencimento: {dt_venc_inicio} a {dt_venc_fim}")
        fill(page, 'input[name="edtDtVencimentoInicial"]', dt_venc_inicio)
        fill(page, 'input[name="edtDtVencimentoFinal"]', dt_venc_fim)

        # Executa a consulta
        logger.info("Clicando em Consultar")
        click(page, 'input[name="btnConsultar"]')
        wait_for_network_idle(page)

        # Verifica se há guias na tabela de resultados
        if not element_exists(page, 'input[name="chbSqFatura"]'):
            logger.info("Nenhuma guia encontrada para os filtros informados")
            return None

        # Seleciona a primeira guia e habilita o botão Emitir
        logger.debug("Selecionando primeira guia")
        page.locator('input[name="chbSqFatura"]').first.click()

        logger.debug("Aguardando botão Emitir ser habilitado")
        page.wait_for_function(
            """() => !document.querySelector('input[name="btnEmitir"]').disabled""",
            timeout=10_000,
        )

        # Emite a guia e captura o download
        # O route intercept em browser.py converte a resposta PDF em attachment
        logger.info("Clicando em Emitir — aguardando download do PDF")
        with page.expect_download() as download_info:
            page.locator('input[name="btnEmitir"]').click()

        download = download_info.value
        filename = download.suggested_filename or "guia_estadual.do"
        if not filename.lower().endswith(".pdf"):
            filename = os.path.splitext(filename)[0] + ".pdf"
        dest_path = os.path.join(process_download_dir, filename)
        download.save_as(dest_path)
        try:
            download.delete()
        except Exception:
            pass
        logger.info(f"PDF salvo em: {dest_path}")

        return dest_path

    except Exception as e:
        logger.error(f"Erro durante guia estadual: {e}", exc_info=True)
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
    result = run()
    if result:
        print(f"PDF salvo em: {result}")
    else:
        print("Não havia guia para os filtros informados")
