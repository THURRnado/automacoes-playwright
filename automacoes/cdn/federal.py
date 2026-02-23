from core.navegador import iniciar_navegador, fechar_navegador
from core.acoes import acessar, clicar, digitar, entrar_em_iframe, salvar_download, esperar

""" Empresa para uso: 
    - NOME: ABC DISTRIBUIDORA JOAO PESSOA LTDA
    - CNPJ: 04813255000124
    - IE: 161339387
"""

def executar_automacao():

    playwright, browser, context, page = iniciar_navegador(headless=False, slow_mo=50)

    try:
        
        acessar(page, "https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj", wait_until="domcontentloaded")

        digitar(page, name='niContribuinte', texto="04813255000124")

        clicar(page, '/html/body/app-root/mf-portal-layout/portal-main-layout/div/main/ng-component/ng-component/app-coleta-parametros-pj/app-coleta-parametros-template/form/div[2]/div[2]/button[2]')

        esperar(page, 5)

    except Exception as e:
        print(f"Automação falhou: {e}")

    finally:
        fechar_navegador(playwright, browser)