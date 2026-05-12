# services/cte_destinatario.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.login import login
from core.browser import close_browser_session
from core.actions import goto, fill, click, select_option, wait, wait_for_network_idle
from core.caixa_mensagens import CAIXA_MSG_URL, capturar_msg_id, aguardar_e_baixar
from core.logger import get_logger

logger = get_logger(__name__)

CONSULTA_URL = (
    "https://www4.sefaz.pb.gov.br/atf/fis/FISf_ConsultarCTeGenerica.do"
    "?idSERVirtual=S&h=https://www.sefaz.pb.gov.br/ser/servirtual/credenciamento/info"
)

PROCESS_DIR_TXT = "cte_destinatario_txt"
PROCESS_DIR_XML = "cte_destinatario_xml"

DEFAULT_DT_INICIO  = "01/04/2026"
DEFAULT_DT_FINAL   = "30/04/2026"
DEFAULT_EMPRESA_IE = "161339387"


def _preencher_formulario(page, dt_inicio: str, dt_final: str, empresa_ie: str, tipo: str) -> tuple[str, str]:
    option_value = "2" if tipo == "txt" else "3"

    logger.info(f"Acessando página de consulta CT-e destinatário — tipo: {tipo.upper()}")
    goto(page, CONSULTA_URL)

    logger.debug(f"Preenchendo período: {dt_inicio} a {dt_final}")
    fill(page, 'input[name="edtDtInicial"]', dt_inicio)
    fill(page, 'input[name="edtDtFinal"]', dt_final)

    logger.debug(f"Preenchendo IE no iframe do destinatário: {empresa_ie}")
    dest_frame = page.frame_locator('iframe[name="cmpDest"]').first
    dest_frame.locator('input[name="hidNrDocumentocmpDest"]').fill(empresa_ie)
    dest_frame.locator('input[name="btnPesquisar"]').click()

    logger.debug("Aguardando preenchimento da Razão Social")
    page.wait_for_function(
        """() => {
            const iframe = document.querySelector('iframe[name="cmpDest"]');
            if (!iframe) return false;
            const campo = iframe.contentDocument.querySelector('input[name="hidNoHumanoInstcmpDest"]');
            return campo && campo.value !== '';
        }""",
        timeout=30_000,
    )
    logger.debug("Razão Social preenchida — empresa encontrada")

    logger.debug(f"Selecionando tipo de exibição: {tipo.upper()} (value={option_value})")
    select_option(page, 'select[name="cmbTpExibicao"]', value=option_value)

    logger.debug("Clicando em Recarregar para habilitar o botão Consultar")
    click(page, '#btnRecarregar')

    logger.info("Clicando em Consultar — aguardando processamento do SEFAZ")
    click(page, '#btnConsulta')
    wait_for_network_idle(page)
    wait(3000)

    logger.debug("Acessando caixa de mensagens")
    goto(page, CAIXA_MSG_URL)

    return capturar_msg_id(page)


def run_txt(
    dt_inicio: str  = DEFAULT_DT_INICIO,
    dt_final: str   = DEFAULT_DT_FINAL,
    empresa_ie: str = DEFAULT_EMPRESA_IE,
) -> str:
    """Solicita e baixa o arquivo TXT de CT-e destinatário no SEFAZ."""
    logger.info(f"Iniciando CT-e destinatário TXT — IE: {empresa_ie} | {dt_inicio} a {dt_final}")

    pw, browser, context, page, download_dir = login()
    process_download_dir = os.path.join(download_dir, PROCESS_DIR_TXT)
    os.makedirs(process_download_dir, exist_ok=True)

    try:
        msg_id, date_text = _preencher_formulario(page, dt_inicio, dt_final, empresa_ie, tipo="txt")
        return aguardar_e_baixar(page, process_download_dir, msg_id, date_text, ext="txt")

    except Exception as e:
        logger.error(f"Erro durante CT-e destinatário TXT: {e}", exc_info=True)
        raise

    finally:
        close_browser_session(pw, browser)
        logger.info("Sessão encerrada")


def run_xml(
    dt_inicio: str  = DEFAULT_DT_INICIO,
    dt_final: str   = DEFAULT_DT_FINAL,
    empresa_ie: str = DEFAULT_EMPRESA_IE,
) -> str:
    """Solicita e baixa o arquivo ZIP com XMLs de CT-e destinatário no SEFAZ."""
    logger.info(f"Iniciando CT-e destinatário XML — IE: {empresa_ie} | {dt_inicio} a {dt_final}")

    pw, browser, context, page, download_dir = login()
    process_download_dir = os.path.join(download_dir, PROCESS_DIR_XML)
    os.makedirs(process_download_dir, exist_ok=True)

    try:
        msg_id, date_text = _preencher_formulario(page, dt_inicio, dt_final, empresa_ie, tipo="xml")
        return aguardar_e_baixar(page, process_download_dir, msg_id, date_text, ext="zip")

    except Exception as e:
        logger.error(f"Erro durante CT-e destinatário XML: {e}", exc_info=True)
        raise

    finally:
        close_browser_session(pw, browser)
        logger.info("Sessão encerrada")


if __name__ == "__main__":
    path = run_txt()
    print(f"Arquivo TXT salvo em: {path}")