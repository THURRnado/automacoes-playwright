import os
import sys
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.login import login
from core.browser import close_browser_session
from core.actions import goto, fill, click, select_option, wait, wait_for_network_idle
from core.logger import get_logger

logger = get_logger(__name__)

# URLs do processo
CONSULTA_URL = (
    "https://www4.sefaz.pb.gov.br/atf/fis/FISf_ConsultarNFeXml2.do"
    "?idSERVirtual=S&h=https://www.sefaz.pb.gov.br/ser/servirtual/credenciamento/info"
)
CAIXA_MSG_URL = (
    "https://www4.sefaz.pb.gov.br/atf/seg/SEGf_MinhasMensagens.do"
    "?idSERVirtual=S&h=https://www.sefaz.pb.gov.br/ser/servirtual/credenciamento/info"
)

# Pastas de destino
PROCESS_DIR_TXT = "nota_fiscal_emitente_txt"
PROCESS_DIR_XML = "nota_fiscal_emitente_xml"

# Valores fixos para teste (substituir por parâmetros ao integrar ao Django)
DEFAULT_DT_INICIO  = "01/04/2026"
DEFAULT_DT_FINAL   = "30/04/2026"
DEFAULT_EMPRESA_IE = "161339387"

# Configurações de retry da caixa de mensagens
MAX_TENTATIVAS   = 7
INTERVALO_ESPERA = 15  # segundos entre tentativas


def _preencher_formulario(page, dt_inicio: str, dt_final: str, empresa_ie: str, tipo: str) -> tuple[str, str]:
    """
    Preenche o formulário de consulta NF-e e submete.

    Retorna:
        (msg_id, date_text) — ID e data da mensagem gerada na caixa de mensagens.
    """
    option_value = "2" if tipo == "txt" else "3"

    logger.info(f"Acessando página de consulta NF-e — tipo: {tipo.upper()}")
    goto(page, CONSULTA_URL)

    # Preenche datas
    logger.debug(f"Preenchendo período: {dt_inicio} a {dt_final}")
    fill(page, 'input[name="edtDtInicial"]', dt_inicio)
    fill(page, 'input[name="edtDtFinal"]', dt_final)

    # Preenche IE no iframe do emitente
    logger.debug(f"Preenchendo IE no iframe do emitente: {empresa_ie}")
    emit_frame = page.frame_locator('iframe[name="cmpEmit"]').first
    emit_frame.locator('input[name="hidNrDocumentocmpEmit"]').fill(empresa_ie)
    emit_frame.locator('input[name="btnPesquisar"]').click()

    # Aguarda razão social ser preenchida
    logger.debug("Aguardando preenchimento da Razão Social")
    page.wait_for_function(
        """() => {
            const iframe = document.querySelector('iframe[name="cmpEmit"]');
            if (!iframe) return false;
            const campo = iframe.contentDocument.querySelector('input[name="hidNoHumanoInstcmpEmit"]');
            return campo && campo.value !== '';
        }""",
        timeout=30_000,
    )
    logger.debug("Razão Social preenchida — empresa encontrada")

    # Seleciona tipo de arquivo (TXT ou XML)
    logger.debug(f"Selecionando tipo de exibição: {tipo.upper()} (value={option_value})")
    select_option(page, 'select[name="cmbTpExibicao"]', value=option_value)

    # Clica em Consultar (com reCAPTCHA invisible)
    logger.info("Clicando em Consultar — aguardando processamento do SEFAZ")
    click(page, '#btnConsulta')

    # Aguarda o reCAPTCHA processar e a requisição ser enviada
    wait_for_network_idle(page)
    wait(3000)  # margem extra para o reCAPTCHA disparar o callback

    logger.debug("Acessando caixa de mensagens")
    goto(page, CAIXA_MSG_URL)

    # Captura o link da primeira mensagem (mais recente — sempre a gerada agora)
    primeiro_link = page.locator('form div table tbody tr').nth(2).locator('td').nth(5).locator('a')
    date_text = primeiro_link.inner_text().strip()
    href = primeiro_link.get_attribute('href')
    logger.debug(f"Primeira mensagem — data: {date_text!r} | href: {href}")

    # Extrai o ID da mensagem do href: javascript:abrirFilhas('96093893', 3)
    match = re.search(r"abrirFilhas\('(\d+)'", href or "")
    if not match:
        raise ValueError(f"Não foi possível extrair ID da mensagem do href: {href!r}")

    msg_id = match.group(1)
    logger.info(f"Mensagem identificada — ID: {msg_id} | Data: {date_text}")

    return msg_id, date_text


def _aguardar_e_baixar(page, process_download_dir: str, msg_id: str, date_text: str, ext: str) -> str:
    """
    Aguarda o arquivo ficar disponível na caixa de mensagens, clica para baixar e salva.

    Args:
        msg_id:    ID da mensagem pai para localizar na caixa
        date_text: data da mensagem (usado apenas para log)
        ext:       extensão esperada do arquivo ('txt' ou 'zip')
    """
    download = None
    try:
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            logger.info(f"Tentativa {tentativa}/{MAX_TENTATIVAS} — aguardando arquivo | Data: {date_text}")
            wait(INTERVALO_ESPERA * 1000)
            page.reload()

            # Localiza o link da mensagem pai pelo ID
            link_pai = page.locator(f'a[href*="abrirFilhas(\'{msg_id}\'"]').first
            if not link_pai.is_visible():
                logger.debug(f"Mensagem {msg_id} ainda não disponível — aguardando")
                continue

            # Captura todos os IDs de checkbox antes de expandir
            ids_antes = set(page.eval_on_selector_all(
                'input[name="chbSqMensagems"]',
                'elements => elements.map(el => el.value)'
            ))

            # Clica na mensagem pai para expandir as filhas
            logger.debug(f"Expandindo mensagem pai: ID {msg_id}")
            link_pai.click()
            page.wait_for_load_state("domcontentloaded")

            # Captura todos os IDs após expandir — os novos são as filhas
            ids_depois = set(page.eval_on_selector_all(
                'input[name="chbSqMensagems"]',
                'elements => elements.map(el => el.value)'
            ))
            filhas_ids = list(ids_depois - ids_antes)
            logger.debug(f"Filhas encontradas: {filhas_ids}")

            if not filhas_ids:
                logger.debug("Nenhuma filha encontrada após expandir — aguardando")
                continue

            # Navega para cada filha e verifica qual tem o link de download
            filha_com_anexo = None
            for filha_id in filhas_ids:
                ler_url = (
                    f"https://www4.sefaz.pb.gov.br/atf/seg/SEGf_LerMensagem.do"
                    f"?hidsqMensagem={filha_id}&sqMensagemPai={msg_id}"
                )
                logger.debug(f"Verificando filha: ID {filha_id}")
                goto(page, ler_url)

                if page.locator('a[href*="mostrarArquivo"]').is_visible():
                    filha_com_anexo = filha_id
                    logger.debug(f"Filha com anexo encontrada: ID {filha_id}")
                    break

            if not filha_com_anexo:
                logger.debug("Nenhuma filha com anexo encontrada — aguardando")
                # Volta para a caixa de mensagens para tentar novamente
                goto(page, CAIXA_MSG_URL)
                continue

            # Clica no link de download do anexo
            logger.info("Clicando no link de download do anexo")
            with page.expect_download() as download_info:
                click(page, 'a[href*="mostrarArquivo"]')

            download = download_info.value
            filename = download.suggested_filename or f"nota_fiscal_emitente.{ext}"
            dest_path = os.path.join(process_download_dir, filename)
            download.save_as(dest_path)
            logger.info(f"Download concluído: {dest_path}")
            return dest_path

        raise TimeoutError(
            f"Tempo de resposta do SEFAZ PB lento após {MAX_TENTATIVAS} tentativas. "
            "Tente novamente mais tarde."
        )

    finally:
        if download:
            try:
                download.delete()
            except Exception:
                pass


def run_txt(
    dt_inicio: str  = DEFAULT_DT_INICIO,
    dt_final: str   = DEFAULT_DT_FINAL,
    empresa_ie: str = DEFAULT_EMPRESA_IE,
) -> str:
    """
    Solicita e baixa o arquivo TXT de NF-e emitente no SEFAZ.

    Retorna:
        Caminho absoluto do arquivo TXT baixado.
    """
    logger.info(f"Iniciando NF-e emitente TXT — IE: {empresa_ie} | {dt_inicio} a {dt_final}")

    pw, browser, context, page, download_dir = login()
    process_download_dir = os.path.join(download_dir, PROCESS_DIR_TXT)
    os.makedirs(process_download_dir, exist_ok=True)

    try:
        msg_id, date_text = _preencher_formulario(page, dt_inicio, dt_final, empresa_ie, tipo="txt")
        return _aguardar_e_baixar(page, process_download_dir, msg_id, date_text, ext="txt")

    except Exception as e:
        logger.error(f"Erro durante NF-e emitente TXT: {e}", exc_info=True)
        raise

    finally:
        close_browser_session(pw, browser)
        logger.info("Sessão encerrada")


def run_xml(
    dt_inicio: str  = DEFAULT_DT_INICIO,
    dt_final: str   = DEFAULT_DT_FINAL,
    empresa_ie: str = DEFAULT_EMPRESA_IE,
) -> str:
    """
    Solicita e baixa o arquivo ZIP com XMLs de NF-e emitente no SEFAZ.

    Retorna:
        Caminho absoluto do arquivo ZIP baixado.
    """
    logger.info(f"Iniciando NF-e emitente XML — IE: {empresa_ie} | {dt_inicio} a {dt_final}")

    pw, browser, context, page, download_dir = login()
    process_download_dir = os.path.join(download_dir, PROCESS_DIR_XML)
    os.makedirs(process_download_dir, exist_ok=True)

    try:
        msg_id, date_text = _preencher_formulario(page, dt_inicio, dt_final, empresa_ie, tipo="xml")
        return _aguardar_e_baixar(page, process_download_dir, msg_id, date_text, ext="zip")

    except Exception as e:
        logger.error(f"Erro durante NF-e emitente XML: {e}", exc_info=True)
        raise

    finally:
        close_browser_session(pw, browser)
        logger.info("Sessão encerrada")


if __name__ == "__main__":
    path = run_xml()
    print(f"Arquivo TXT salvo em: {path}")