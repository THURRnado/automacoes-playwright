# services/venda_varejo.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.login import login
from core.browser import close_browser_session
from core.actions import goto, fill, click, wait_for_network_idle
from core.logger import get_logger

logger = get_logger(__name__)

DOSSIE_URL = (
    "https://www4.sefaz.pb.gov.br/atf/dec/DECf_DossierContribuinte.do"
    "?edtCdFuncao=DEC_381&h=https://www.receita.pb.gov.br/ser/servirtual/credenciamento/info"
)

PROCESS_DIR = "venda_varejo"

DEFAULT_DT_INICIO  = "01/2026"
DEFAULT_DT_FINAL   = "04/2026"
DEFAULT_EMPRESA_IE = "161339387"


def run(
    dt_inicio: str  = DEFAULT_DT_INICIO,
    dt_final: str   = DEFAULT_DT_FINAL,
    empresa_ie: str = DEFAULT_EMPRESA_IE,
) -> tuple[str, str]:
    """
    Executa o processo de download do PDF e CSV de Vendas Varejo no Dossiê do Contribuinte.

    Args:
        dt_inicio:  Período inicial no formato mm/aaaa
        dt_final:   Período final no formato mm/aaaa
        empresa_ie: Inscrição estadual da empresa

    Retorna:
        tuple: (caminho_pdf, caminho_csv)
    """
    logger.info(f"Iniciando Venda Varejo — IE: {empresa_ie} | {dt_inicio} a {dt_final}")

    pw, browser, context, page, download_dir = login()
    process_download_dir = os.path.join(download_dir, PROCESS_DIR)
    os.makedirs(process_download_dir, exist_ok=True)
    logger.debug(f"Diretório de download: {process_download_dir}")

    pdf_download = None
    csv_download = None

    try:
        # Acessa o Dossiê do Contribuinte
        logger.info(f"Acessando Dossiê do Contribuinte: {DOSSIE_URL}")
        goto(page, DOSSIE_URL)

        # Preenche a IE e pesquisa
        logger.debug(f"Preenchendo IE: {empresa_ie}")
        fill(page, 'input[name="edtnrInscrEstadual"]', empresa_ie)
        click(page, 'input[name="btnConsultar"]')
        wait_for_network_idle(page)

        # Clica na aba Vendas-Atacado
        logger.debug("Clicando na aba Vendas-Atacado")
        click(page, 'a[onclick*="consultarVendasAtacado"]')
        wait_for_network_idle(page)

        # Preenche o período
        logger.debug(f"Preenchendo período: {dt_inicio} a {dt_final}")
        fill(page, 'input[name="edtDataInicio"]', dt_inicio)
        fill(page, 'input[name="edtDataFim"]', dt_final)

        # Clica em Consultar
        logger.info("Clicando em Consultar")
        click(page, 'input[name="btnConsultarAbaVendAtac"]')
        wait_for_network_idle(page)

        # Verifica se há registros
        footer_text = page.locator('td.footer').last.inner_text()
        if "0 Registro(s)" in footer_text:
            raise ValueError(f"Nenhum registro encontrado para o período {dt_inicio} a {dt_final}")
        logger.debug(f"Registros encontrados: {footer_text}")

        # ── Download PDF ──────────────────────────────────────────────────────
        logger.info("Gerando PDF — aguardando nova janela")
        with context.expect_page() as blank_page_info, \
             page.expect_download() as pdf_download_info:
            click(page, 'a[onclick*="submeterListagem(1,"]')

        blank_page = blank_page_info.value
        blank_page.close()
        logger.debug("Janela em branco do PDF fechada")

        pdf_download = pdf_download_info.value
        pdf_filename = pdf_download.suggested_filename or "venda_varejo.pdf"
        if not pdf_filename.lower().endswith(".pdf"):
            pdf_filename = os.path.splitext(pdf_filename)[0] + ".pdf"
        pdf_path = os.path.join(process_download_dir, pdf_filename)
        pdf_download.save_as(pdf_path)
        logger.info(f"PDF salvo em: {pdf_path}")

        # ── Download CSV ──────────────────────────────────────────────────────
        logger.info("Gerando CSV — aguardando nova janela")
        with context.expect_page() as blank_page_info, \
             page.expect_download() as csv_download_info:
            click(page, 'a[onclick*="submeterListagem(3,"]')

        blank_page = blank_page_info.value
        blank_page.close()
        logger.debug("Janela em branco do CSV fechada")

        csv_download = csv_download_info.value
        csv_filename = csv_download.suggested_filename or "venda_varejo.csv"
        csv_path = os.path.join(process_download_dir, csv_filename)
        csv_download.save_as(csv_path)
        logger.info(f"CSV salvo em: {csv_path}")

        return pdf_path, csv_path

    except Exception as e:
        logger.error(f"Erro durante Venda Varejo: {e}", exc_info=True)
        raise

    finally:
        if pdf_download:
            try:
                pdf_download.delete()
            except Exception:
                pass
        if csv_download:
            try:
                csv_download.delete()
            except Exception:
                pass
        close_browser_session(pw, browser)
        logger.info("Sessão encerrada")


if __name__ == "__main__":
    pdf, csv = run()
    print(f"PDF salvo em: {pdf}")
    print(f"CSV salvo em: {csv}")