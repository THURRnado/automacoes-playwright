import os

from core.navegador import iniciar_navegador, fechar_navegador
from core.cert_to_pem_criptography import decifrar_certificado, apagar_certificado_temp, extrair_e_criptografar_pfx
from core.acoes import (
    acessar, clicar, esperar, aguardar_elemento, clicar_js, elemento_existe,
    digitar, limpar, salvar_download, verificar_toast
)
from dotenv import load_dotenv
import logging
from datetime import date, datetime
from calendar import monthrange

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FERNET_KEY = os.getenv("FERNET_KEY")

caminho_cert = os.getenv('CAMINHO_CERTIFICADO')
senha_cert = os.getenv('SENHA_CERTIFICADO')


def _competencia_anterior() -> str:
    hoje = date.today()
    if hoje.month == 1:
        return f"01/{hoje.year - 1}"
    return f"{hoje.month - 1:02d}/{hoje.year}"


def _navegar_ate_guia(page, retido_na_fonte: bool = False):
    """
    Refaz todo o caminho até a tela da guia: menu, entrada, ajuste de competência,
    (opcionalmente) marca 'Retido na Fonte', e carrega as notas.
    Espera a tela inicial (bemVindo.jsf) já estar carregada antes de chamar.
    """
    clicar_js(page, "18639", expandir_apenas=True)

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    clicar_js(page, "18642")

    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass

    aguardar_elemento(page, '//*[contains(@id, "idGuiaCompetencia_input")]')
    competencia_guia = page.locator('//*[contains(@id, "idGuiaCompetencia_input")]').input_value().strip()

    hoje = datetime.now()
    mes_ant = hoje.month - 1 if hoje.month > 1 else 12
    ano_ant = hoje.year if hoje.month > 1 else hoje.year - 1
    mes_anterior = f"{mes_ant:02d}/{ano_ant}"

    if competencia_guia != mes_anterior:
        logger.info(f"Competência da guia ({competencia_guia}) diferente do mês anterior ({mes_anterior}), alterando...")
        mes_num = int(mes_anterior.split('/')[0])
        ano_alvo = int(mes_anterior.split('/')[1])
        ultimo_dia = monthrange(ano_alvo, mes_num)[1]

        curr_mes = int(competencia_guia.split('/')[0])
        curr_ano = int(competencia_guia.split('/')[1])
        meses_diff = (curr_ano - ano_alvo) * 12 + (curr_mes - mes_num)

        clicar(page, '//*[contains(@id, "idGuiaCompetencia")]//button[contains(@class, "ui-datepicker-trigger")]')
        aguardar_elemento(page, '//*[contains(@id, "idGuiaCompetencia_panel")]')

        for _ in range(abs(meses_diff)):
            btn = 'ui-datepicker-prev' if meses_diff > 0 else 'ui-datepicker-next'
            page.evaluate(f'document.querySelector("[id*=\'idGuiaCompetencia_panel\'] .{btn}").click()')
            esperar(page, 0.3)

        page.evaluate(f'''
            var tds = document.querySelectorAll('[id*="idGuiaCompetencia_panel"] td:not(.ui-datepicker-other-month) a');
            for (var a of tds) {{
                if (a.textContent.trim() === "{ultimo_dia}") {{ a.click(); break; }}
            }}
        ''')

        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

    # Marca 'Retido na Fonte' ANTES de carregar as notas, pois influencia o carregamento
    if retido_na_fonte:
        logger.info("Marcando 'Retido na Fonte' antes de carregar as notas...")
        clicar(page, '//input[@value="RNF" and @data-p-label="Tipo Recolhimento"]/ancestor::div[contains(@class, "ui-radiobutton")]//div[contains(@class, "ui-radiobutton-box")]')
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

    clicar(page, '//a[contains(@class, "jarch-btn-search") and contains(., "Carregar Notas")]')
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass


def _verificar_e_emitir_guia(guia_page, nome_arquivo: str) -> bool:
    """
    Lê o valor da guia e, se houver valor, emite, baixa o PDF e fecha o dialog.
    Retorna True se emitiu (e portanto o site redirecionou para a tela inicial),
    False se não havia valor a emitir (segue na mesma tela).
    """
    aguardar_elemento(guia_page, '//*[contains(@class, "hbggreen")]//h3')
    valor_guia = guia_page.locator('//*[contains(@class, "hbggreen")]//h3').inner_text().strip()

    if valor_guia == "R$ 0,00":
        logger.info(f"Guia sem valor ({nome_arquivo}), nada a emitir.")
        return False

    logger.info(f"Guia com valor {valor_guia}, emitindo PDF ({nome_arquivo})...")

    pdf_bytes_holder = []

    def _capturar_guia(route):
        try:
            response = route.fetch()
        except Exception:
            route.continue_()
            return
        body = response.body()
        if "application/pdf" in response.headers.get("content-type", ""):
            pdf_bytes_holder.append(body)
        route.fulfill(response=response)

    guia_page.route("**/dynamiccontent.properties.jsf**", _capturar_guia)

    try:
        with guia_page.expect_response(
            lambda r: "application/pdf" in r.headers.get("content-type", ""),
            timeout=30000
        ):
            clicar(guia_page, '//*[contains(@class, "paneldatamaster__button-notask")]')
            if elemento_existe(guia_page, '//button[contains(@class, "swal-button--confirm")]', timeout=10000):
                clicar(guia_page, '//button[contains(@class, "swal-button--confirm")]')
    finally:
        guia_page.unroute("**/dynamiccontent.properties.jsf**", _capturar_guia)

    if not pdf_bytes_holder:
        raise Exception(f"PDF da guia não capturado dentro do timeout ({nome_arquivo})")

    pasta = os.path.abspath("temp_downloads")
    os.makedirs(pasta, exist_ok=True)
    caminho_guia = os.path.join(pasta, nome_arquivo)
    with open(caminho_guia, "wb") as f:
        f.write(pdf_bytes_holder[0])
    logger.info(f"Guia salva em: {caminho_guia}")

    # Fecha o dialog de visualização do PDF, se estiver aberto
    _BTN_FECHAR_DIALOG = '//*[contains(@id, "dialogVisualizacaoGuia")]//a[contains(@class, "ui-dialog-titlebar-close")]'
    if elemento_existe(guia_page, _BTN_FECHAR_DIALOG, timeout=10000):
        logger.info("Fechando dialog de visualização da guia...")
        clicar(guia_page, _BTN_FECHAR_DIALOG)
        try:
            aguardar_elemento(guia_page, '//*[contains(@id, "dialogVisualizacaoGuia")]', state="hidden", timeout=10000)
        except Exception:
            logger.warning("Dialog não confirmou fechamento dentro do timeout, seguindo mesmo assim.")
    else:
        logger.info("Dialog de visualização não encontrado, nada a fechar.")

    return True


def executar_automacao():

    # No django isso seria pegando do banco, isso só rodo uma vez para cada cert de cada empresa
    cert_enc, key_enc = extrair_e_criptografar_pfx(caminho_cert, senha_cert, FERNET_KEY)

    # certificado = Certificado.objects.get(usuario=usuario)
    cert_path, key_path = decifrar_certificado(
        bytes(cert_enc),
        bytes(key_enc),
        FERNET_KEY
    )

    playwright, browser, page = None, None, None

    try:
        playwright, browser, _, page = iniciar_navegador(
            cert_path=cert_path,
            key_path=key_path,
            cert_origin="https://receita.joaopessoa.pb.gov.br"
        )

        # --- LOGIN VIA CERTIFICADO DIGITAL ---
        acessar(page, 'https://receita.joaopessoa.pb.gov.br/notafiscal/paginas/portal/index.html#/login')
        clicar(page, '//*[@id="app"]/div/main/div/div/div/div[3]/div[2]/div/div[3]/a')
        page.wait_for_url('**/bemVindo.jsf**', timeout=90000)

        competencia = _competencia_anterior()

        # --- LIVRO FISCAL ---
        with page.expect_response(
            lambda r: 'relatorioLivroFiscal.jsf' in r.url,
            timeout=30000
        ) as response_info:
            acessar(page, 'https://receita.joaopessoa.pb.gov.br/notafiscal/paginas/livrofiscal/relatorioLivroFiscal.jsf', wait_until="load")
        resp = response_info.value
        if resp.status >= 400:
            raise Exception(f"Servidor retornou HTTP {resp.status} para o Livro Fiscal")

        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        if 'relatorioLivroFiscal.jsf' not in page.url:
            raise Exception(f"Redirecionado inesperadamente para: {page.url}")

        aguardar_elemento(page, '//*[contains(@id, "idStart_input")]')
        digitar(page, '//*[contains(@id, "idStart_input")]', competencia)
        digitar(page, '//*[contains(@id, "idEnd_input")]', competencia)

        # Livro Fiscal - Serviços Prestados (seleção padrão do Agrupamento)
        try:
            salvar_download(
                page,
                '//a[contains(@class, "ui-commandlink") and contains(@class, "btn-info") and contains(., "Download")]',
                nome_arquivo='livro_fiscal_servicos_prestados.pdf',
                timeout=20000
            )
        except Exception:
            toast = verificar_toast(page)
            if toast:
                logger.info(f"Toast livro prestados: '{toast}'")
            else:
                raise

        # Livro Fiscal - Serviços Tomados
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        aguardar_elemento(page, '//div[contains(@id, "idSelectOneMenu") and .//select[@data-p-label="Agrupamento"]]')
        clicar(page, '//div[contains(@id, "idSelectOneMenu") and .//select[@data-p-label="Agrupamento"]]//div[contains(@class, "ui-selectonemenu-trigger")]')
        aguardar_elemento(page, '//li[contains(@id, "idSelectOneMenu_") and normalize-space(.)="Serviços Tomados"]')
        clicar(page, '//li[contains(@id, "idSelectOneMenu_") and normalize-space(.)="Serviços Tomados"]')
        try:
            salvar_download(
                page,
                '//a[contains(@class, "ui-commandlink") and contains(@class, "btn-info") and contains(., "Download")]',
                nome_arquivo='livro_fiscal_servicos_tomados.pdf',
                timeout=20000
            )
        except Exception:
            toast = verificar_toast(page)
            if toast:
                logger.info(f"Toast livro tomados: '{toast}'")
            else:
                raise

        # --- EXPORTAÇÃO DE NOTAS ---
        with page.expect_response(
            lambda r: 'exportacaoNota.jsf' in r.url,
            timeout=30000
        ) as response_info:
            acessar(page, 'https://receita.joaopessoa.pb.gov.br/notafiscal/paginas/exportacaonota/exportacaoNota.jsf', wait_until="load")
        resp = response_info.value
        if resp.status >= 400:
            raise Exception(f"Servidor retornou HTTP {resp.status} para a Exportação de Notas")

        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        if 'exportacaoNota.jsf' not in page.url:
            raise Exception(f"Redirecionado inesperadamente para: {page.url}")

        aguardar_elemento(page, '//input[@data-p-label="Inicio" and contains(@id, "idStart_input")]')
        digitar(page, '//input[@data-p-label="Inicio" and contains(@id, "idStart_input")]', competencia)
        digitar(page, '//input[@data-p-label="Fim" and contains(@id, "idEnd_input")]', competencia)
        limpar(page, '//input[@data-p-label="Data Inicio" and contains(@id, "idStart_input")]')
        limpar(page, '//input[@data-p-label="Data Fim" and contains(@id, "idEnd_input")]')
        _BTN_DOWNLOAD = '//a[contains(@id, "btnDownload") and not(contains(@id, "btnDownloadFinal"))]'

        clicar(page, '//a[contains(@class, "btn-info") and contains(., "Gerar Relação Notas")]')

        # Exportação - Notas Emitidas
        try:
            if elemento_existe(page, _BTN_DOWNLOAD, timeout=15000):
                try:
                    salvar_download(
                        page, _BTN_DOWNLOAD,
                        nome_arquivo='exportacao_nota_emitidas.xml',
                        timeout=20000
                    )
                except Exception:
                    toast = verificar_toast(page)
                    if toast:
                        logger.info(f"Toast exportação emitidas: '{toast}'")
                    else:
                        raise
            else:
                toast = verificar_toast(page)
                if toast:
                    logger.info(f"Toast exportação emitidas (sem dialog): '{toast}'")
        finally:
            try:
                page.evaluate("if (typeof hideMessageProcess === 'function') hideMessageProcess();")
            except Exception:
                pass
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass

        # Exportação - Notas Recebidas
        clicar(page, '//input[@value="R" and @data-p-label="Serviço"]/ancestor::div[contains(@class, "ui-radiobutton")]//div[contains(@class, "ui-radiobutton-box")]')
        clicar(page, '//a[contains(@class, "btn-info") and contains(., "Gerar Relação Notas")]')
        try:
            if elemento_existe(page, _BTN_DOWNLOAD, timeout=15000):
                try:
                    salvar_download(
                        page, _BTN_DOWNLOAD,
                        nome_arquivo='exportacao_nota_recebidas.xml',
                        timeout=20000
                    )
                except Exception:
                    toast = verificar_toast(page)
                    if toast:
                        logger.info(f"Toast exportação recebidas: '{toast}'")
                    else:
                        raise
            else:
                toast = verificar_toast(page)
                if toast:
                    logger.info(f"Toast exportação recebidas (sem dialog): '{toast}'")
        finally:
            try:
                page.evaluate("if (typeof hideMessageProcess === 'function') hideMessageProcess();")
            except Exception:
                pass
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass

        # --- GUIA NORMAL ---
        _navegar_ate_guia(page, retido_na_fonte=False)
        emitiu_normal = _verificar_e_emitir_guia(page, "guia.pdf")

        # --- GUIA RETIDO NA FONTE ---
        if emitiu_normal:
            # Emitiu a guia normal → o site redirecionou para a tela inicial.
            # Espera a tela inicial e refaz o caminho completo, já marcando Retido na Fonte.
            logger.info("Guia normal emitida, refazendo caminho para Retido na Fonte...")
            page.wait_for_url('**/bemVindo.jsf**', timeout=90000)
            _navegar_ate_guia(page, retido_na_fonte=True)
        else:
            # Guia normal sem valor → continuamos na tela da guia, sem redirecionamento.
            # Como o 'Retido na Fonte' deve ser marcado antes de carregar as notas,
            # marcamos aqui e recarregamos as notas na mesma tela.
            logger.info("Guia normal sem valor, marcando Retido na Fonte na mesma tela...")
            clicar(page, '//input[@value="RNF" and @data-p-label="Tipo Recolhimento"]/ancestor::div[contains(@class, "ui-radiobutton")]//div[contains(@class, "ui-radiobutton-box")]')
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            clicar(page, '//a[contains(@class, "jarch-btn-search") and contains(., "Carregar Notas")]')
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass

        _verificar_e_emitir_guia(page, "guia_retido_fonte.pdf")

        esperar(page, 10)

    finally:
        if playwright:
            fechar_navegador(playwright, browser)
        apagar_certificado_temp(cert_path, key_path)
