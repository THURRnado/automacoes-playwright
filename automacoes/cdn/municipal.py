from core.navegador import iniciar_navegador, fechar_navegador
from core.acoes import acessar, clicar, digitar, entrar_em_iframe, salvar_download

""" Empresa para uso: 
    - NOME: ABC DISTRIBUIDORA JOAO PESSOA LTDA
    - CNPJ: 04813255000124
    - IE: 161339387
"""

def executar_automacao():

    playwright, browser, context, page = iniciar_navegador(headless=False, slow_mo=50)

    try:
        
        acessar(page, "https://receita.joaopessoa.pb.gov.br/dsf_jpa_portal/inicial.do?evento=montaMenu&acronym=EMITIRCERTIDAOFINANCEIRAPES", wait_until="domcontentloaded")

        iframe = entrar_em_iframe(page, '//*[@id="dsf-screen"]')

        digitar(iframe, '//*[@id="cadastroCodigoPesquisaDOC"]', "04813255000124", limpar=False)

        clicar(iframe, '//*[@id="dsf.evt.emitirCertidao"]')

        salvar_download(page, '//*[@id="dsf.evt.emitirCertidao"]', frame=iframe)

    except Exception as e:
        print(f"Automação falhou: {e}")

    finally:
        fechar_navegador(playwright, browser)