# core/caixa_mensagens.py
import os
import re

from core.actions import goto, click, wait
from core.logger import get_logger

logger = get_logger(__name__)

CAIXA_MSG_URL = (
    "https://www4.sefaz.pb.gov.br/atf/seg/SEGf_MinhasMensagens.do"
    "?idSERVirtual=S&h=https://www.sefaz.pb.gov.br/ser/servirtual/credenciamento/info"
)

MAX_TENTATIVAS   = 5
INTERVALO_ESPERA = 15  # segundos


def capturar_msg_id(page) -> tuple[str, str]:
    """
    Captura o ID e a data da primeira mensagem da caixa de mensagens.

    Retorna:
        (msg_id, date_text)
    """
    primeiro_link = page.locator('form div table tbody tr').nth(2).locator('td').nth(5).locator('a')
    date_text = primeiro_link.inner_text().strip()
    href = primeiro_link.get_attribute('href')
    logger.debug(f"Primeira mensagem — data: {date_text!r} | href: {href}")

    match = re.search(r"abrirFilhas\('(\d+)'", href or "")
    if not match:
        raise ValueError(f"Não foi possível extrair ID da mensagem do href: {href!r}")

    msg_id = match.group(1)
    logger.info(f"Mensagem identificada — ID: {msg_id} | Data: {date_text}")

    return msg_id, date_text


def aguardar_e_baixar(page, process_download_dir: str, msg_id: str, date_text: str, ext: str) -> str:
    """
    Aguarda o arquivo ficar disponível na caixa de mensagens, clica para baixar e salva.

    Args:
        page:                instância da Page do Playwright
        process_download_dir: diretório de destino do arquivo
        msg_id:              ID da mensagem pai
        date_text:           data da mensagem (usado apenas para log)
        ext:                 extensão esperada do arquivo ('txt' ou 'zip')

    Retorna:
        Caminho absoluto do arquivo salvo.
    """
    download = None
    try:
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            logger.info(f"Tentativa {tentativa}/{MAX_TENTATIVAS} — aguardando arquivo | Data: {date_text}")
            wait(INTERVALO_ESPERA * 1000)
            page.reload(timeout=60_000)

            # Localiza o link da mensagem pai pelo ID
            link_pai = page.locator(f'a[href*="abrirFilhas(\'{msg_id}\'"]').first
            if not link_pai.is_visible():
                logger.debug(f"Mensagem {msg_id} ainda não disponível — aguardando")
                continue

            # Verifica se a linha do pai tem ícone de anexo (clips)
            # A linha do pai é o tr que contém o link com o msg_id
            linha_pai = page.locator(f'tr:has(a[href*="abrirFilhas(\'{msg_id}\'"])')
            tem_anexo = linha_pai.locator('img[alt="Anexo"]').count() > 0

            if not tem_anexo:
                logger.debug(f"Mensagem {msg_id} ainda sem anexo — aguardando")
                continue

            # Só expande e navega se o anexo já estiver disponível
            ids_antes = set(page.eval_on_selector_all(
                'input[name="chbSqMensagems"]',
                'elements => elements.map(el => el.value)'
            ))

            logger.debug(f"Expandindo mensagem pai: ID {msg_id}")
            link_pai.click()
            page.wait_for_load_state("domcontentloaded")

            # Captura IDs após expandir — os novos são as filhas
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
                goto(page, CAIXA_MSG_URL)
                continue

            # Clica no link de download
            logger.info("Clicando no link de download do anexo")
            with page.expect_download() as download_info:
                click(page, 'a[href*="mostrarArquivo"]')

            download = download_info.value
            filename = download.suggested_filename or f"arquivo.{ext}"
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