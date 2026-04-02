import os
from core.navegador import iniciar_navegador, fechar_navegador
from core.cert_to_pem_criptography import decifrar_certificado, apagar_certificado_temp, extrair_e_criptografar_pfx
from core.acoes import acessar, clicar, esperar, digitar, aguardar_elemento, salvar_download, limpar
from dotenv import load_dotenv

load_dotenv()

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

        esperar(page, 10)

        acessar(page, 'https://receita.joaopessoa.pb.gov.br/notafiscal/paginas/livrofiscal/relatorioLivroFiscal.jsf')

        esperar(page, 5)

        digitar(page, '//*[@id="frmRelatorio:j_idt104:j_idt107:idStart_input"]', '02/2026')

        digitar(page, '//*[@id="frmRelatorio:j_idt104:j_idt107:idEnd_input"]', '02/2026')

        clicar(page, '//*[@id="frmRelatorio:j_idt104:j_idt131:j_idt136"]/div[2]')

        salvar_download(page, '//*[@id="frmRelatorio:j_idt104:j_idt222"]', nome_arquivo='livro_fiscal_servicos_prestados.pdf')

        clicar(page, '//*[@id="frmRelatorio:j_idt104:j_idt120:idSelectOneMenu"]/div[2]')

        clicar(page, '//*[@id="frmRelatorio:j_idt104:j_idt120:idSelectOneMenu_1"]')

        salvar_download(page, '//*[@id="frmRelatorio:j_idt104:j_idt222"]', nome_arquivo='livro_fiscal_servicos_tomados.pdf')

        acessar(page, 'https://receita.joaopessoa.pb.gov.br/notafiscal/paginas/exportacaonota/exportacaoNota.jsf')

        esperar(page, 5)

        digitar(page, '//*[@id="j_idt102:j_idt106:idStart_input"]', '02/2026')

        digitar(page, '//*[@id="j_idt102:j_idt106:idEnd_input"]', '02/2026')

        limpar(page, '//*[@id="j_idt102:j_idt119:idStart_input"]')

        limpar(page, '//*[@id="j_idt102:j_idt119:idEnd_input"]')

        clicar(page, '//*[@id="j_idt102:j_idt170"]')

        salvar_download(page, '//*[@id="j_idt102:j_idt183:btnDownload"]', nome_arquivo='exportacao_nota_emitidas.xml')

        clicar(page, '//*[@id="j_idt102:j_idt159:j_idt160"]/div/div[2]/div/div[2]')

        clicar(page, '//*[@id="j_idt102:j_idt170"]')

        salvar_download(page, '//*[@id="j_idt102:j_idt183:btnDownload"]', nome_arquivo='exportacao_nota_recebidas.xml')

        esperar(page, 10)

    finally:
        if playwright:
            fechar_navegador(playwright, browser)
        apagar_certificado_temp(cert_path, key_path)