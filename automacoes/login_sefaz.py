from core.navegador import iniciar_navegador, fechar_navegador
from core.acoes import acessar, clicar, digitar, entrar_em_iframe
import os

def login():

    playwright, browser, context, page = iniciar_navegador(headless=True, slow_mo=50)

    try:
        
        acessar(page, "https://sefaz.pb.gov.br/servirtual", wait_until="domcontentloaded")

        iframe = entrar_em_iframe(page, '//*[@id="atf-login"]/iframe')

        digitar(iframe, '//*[@id="form-cblogin-username"]/div/input', os.getenv("SEFAZ_USERNAME"), limpar=False)
        digitar(iframe, '//*[@id="form-cblogin-password"]/div[1]/input', os.getenv("SEFAZ_PASSWORD"), limpar=False)

        clicar(iframe, '//*[@id="form-cblogin-password"]/div[2]/input[2]')

    except Exception as e:
        print(f"Automação falhou: {e}")

    finally:
        return playwright, browser, context, page