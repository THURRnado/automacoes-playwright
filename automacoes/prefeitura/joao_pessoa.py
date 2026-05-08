import os
from core.navegador import iniciar_navegador, fechar_navegador
from core.cert_to_pem_criptography import decifrar_certificado, apagar_certificado_temp, extrair_e_criptografar_pfx
from core.acoes import acessar, clicar, esperar, digitar, aguardar_elemento, salvar_download_ou_toast, limpar, clicar_js, tirar_screenshot
from dotenv import load_dotenv
import logging
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FERNET_KEY = os.getenv("FERNET_KEY")

caminho_cert = os.getenv('CAMINHO_CERTIFICADO')
senha_cert = os.getenv('SENHA_CERTIFICADO')


def executar_automacao():

    # No django isso seria pegando do banco, isso só rodo uma vez para cada cert de cada empresa
    cert_enc, key_enc = extrair_e_criptografar_pfx(caminho_cert, senha_cert, FERNET_KEY)

    # certificado = Certificado.objects.get(usuario=usuario)
    cert_path, key_path = decifrar_certificado(
        bytes(cert_enc),
        bytes(key_enc),
        FERNET_KEY
    )

    playwright, browser, context, page = None, None, None, None

    try:
        playwright, browser, context, page = iniciar_navegador(
            cert_path=cert_path,
            key_path=key_path,
            cert_origin="https://receita.joaopessoa.pb.gov.br"
        )

        acessar(page, 'https://receita.joaopessoa.pb.gov.br/notafiscal/paginas/portal/index.html#/login')

        clicar(page, '//*[@id="app"]/div/main/div/div/div/div[3]/div[2]/div/div[3]/a')

        page.wait_for_url('**/bemVindo.jsf**', timeout=90000)

        acessar(page, 'https://receita.joaopessoa.pb.gov.br/notafiscal/paginas/livrofiscal/relatorioLivroFiscal.jsf', wait_until="load")
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        aguardar_elemento(page, '//*[@id="frmRelatorio:j_idt104:j_idt107:idStart_input"]')
        digitar(page, '//*[@id="frmRelatorio:j_idt104:j_idt107:idStart_input"]', '02/2026')

        digitar(page, '//*[@id="frmRelatorio:j_idt104:j_idt107:idEnd_input"]', '02/2026')

        clicar(page, '//*[@id="frmRelatorio:j_idt104:j_idt131:j_idt136"]/div[2]')

        salvar_download_ou_toast(page, '//*[@id="frmRelatorio:j_idt104:j_idt222"]', nome_arquivo='livro_fiscal_servicos_prestados.pdf')

        clicar(page, '//*[@id="frmRelatorio:j_idt104:j_idt120:idSelectOneMenu"]/div[2]')

        clicar(page, '//*[@id="frmRelatorio:j_idt104:j_idt120:idSelectOneMenu_1"]')

        salvar_download_ou_toast(page, '//*[@id="frmRelatorio:j_idt104:j_idt222"]', nome_arquivo='livro_fiscal_servicos_tomados.pdf')

        acessar(page, 'https://receita.joaopessoa.pb.gov.br/notafiscal/paginas/exportacaonota/exportacaoNota.jsf', wait_until="load")
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        aguardar_elemento(page, '//*[@id="j_idt102:j_idt106:idStart_input"]')
        digitar(page, '//*[@id="j_idt102:j_idt106:idStart_input"]', '02/2026')

        digitar(page, '//*[@id="j_idt102:j_idt106:idEnd_input"]', '02/2026')

        limpar(page, '//*[@id="j_idt102:j_idt119:idStart_input"]')

        limpar(page, '//*[@id="j_idt102:j_idt119:idEnd_input"]')

        clicar(page, '//*[@id="j_idt102:j_idt170"]')

        salvar_download_ou_toast(page, '//*[@id="j_idt102:j_idt183:btnDownload"]', nome_arquivo='exportacao_nota_emitidas.xml')

        clicar(page, '//*[@id="j_idt102:j_idt159:j_idt160"]/div/div[2]/div/div[2]')

        clicar(page, '//*[@id="j_idt102:j_idt170"]')

        salvar_download_ou_toast(page, '//*[@id="j_idt102:j_idt183:btnDownload"]', nome_arquivo='exportacao_nota_recebidas.xml')

        # Gerenciar guias

        '''clicar_js(page, "18640")

        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        aguardar_elemento(page, '//*[@id="j_idt99:listEntityDataTableGuia:idDataTableList_data"]/tr[1]')
        tds = page.locator('//*[@id="j_idt99:listEntityDataTableGuia:idDataTableList_data"]/tr[1]/td').all()

        td_3 = tds[3].inner_text().strip()
        td_8 = tds[8].inner_text().strip().lower()

        mes_atual = datetime.now().strftime("%m/%Y")

        if td_3 != mes_atual:
            logger.info(f"Competência {td_3} diferente do mês atual {mes_atual}, pulando...")
        else:
            if td_8 == "emitida":
                logger.info("Guia já emitida, nada a fazer.")
            else:
                pass'''

        # Emitir guia
        ''''clicar_js(page, "18642")
        esperar(page, 5)

        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        aguardar_elemento(page, '//*[@id="j_idt99:j_idt220:commandLinkSaveNoTask"]')
        respostas = []

        def capturar(response):
            respostas.append(f"{response.status} {response.headers.get('content-type', '')} {response.url}")

        page.on("response", capturar)
        clicar(page, '//*[@id="j_idt99:j_idt220:commandLinkSaveNoTask"]')
        esperar(page, 3)
        page.remove_listener("response", capturar)

        for r in respostas:
            print(r)

        # Debug: ver o que aparece na tela após o clique
        tirar_screenshot(page, "modal_apos_clique")

        # Inspecionar HTML do dialog visível
        html_dialog = page.evaluate("""
            () => {
                const dialogs = document.querySelectorAll('.ui-dialog');
                return Array.from(dialogs)
                    .filter(d => d.style.display !== 'none' && d.offsetParent !== null)
                    .map(d => d.outerHTML.substring(0, 2000));
            }
        """)
        for i, h in enumerate(html_dialog):
            print(f"--- Dialog {i} ---")
            print(h)'''

        esperar(page, 10)

    finally:
        if playwright:
            fechar_navegador(playwright, browser)
        apagar_certificado_temp(cert_path, key_path)