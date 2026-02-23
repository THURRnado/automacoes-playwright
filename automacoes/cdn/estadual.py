from core.navegador import iniciar_navegador, fechar_navegador
from core.acoes import acessar, clicar, digitar, entrar_em_iframe, salvar_download, baixar_pdf_url
from automacoes.login_sefaz import login

""" Empresa para uso: 
    - NOME: ABC DISTRIBUIDORA JOAO PESSOA LTDA
    - CNPJ: 04813255000124
    - IE: 161339387
"""

def executar_automacao():

    playwright, browser, context, page = login()

    try:
        
        acessar(page, "https://www.sefaz.pb.gov.br/servirtual/certidoes/emissao-de-certidao-de-debitos-cidadao", wait_until="domcontentloaded")

        acessar(page, "https://www4.sefaz.pb.gov.br/atf/dia/DIAf_EmitirCertidaoDebito.do?limparSessao=true&h=https://www.sefaz.pb.gov.br/ser/servirtual/credenciamento/info&idSERVirtual=S", wait_until="domcontentloaded")

        digitar(page, xpath='//*[@id="tbCertidao"]/tbody/tr[3]/td[2]/input', texto="161339387")

        salvar_download(page, '//*[@id="tbCaptcha"]/tbody/tr/td/button')

        clicar(page, "https://www4.sefaz.pb.gov.br/atf/dia/DIAf_EmitirCertidaoDebito.do")

    except Exception as e:
        print(f"Automação falhou: {e}")

    finally:
        fechar_navegador(playwright, browser)