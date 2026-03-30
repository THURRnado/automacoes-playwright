import os
from dotenv import load_dotenv
from camoufox.sync_api import Camoufox
from browserforge.fingerprints import Screen
from core.acoes_camoufox import clicar, digitar, delay, simular_leitura, mover_mouse

load_dotenv()

"""
Empresa para uso: 
    - NOME: ABC DISTRIBUIDORA JOAO PESSOA LTDA
    - CNPJ: 04813255000124
    - IE: 161339387
"""

def captcha_tem_desafio(page) -> bool:
    try:
        page.locator("//iframe[contains(@src, 'bframe')]").wait_for(
            state="visible",
            timeout=3000
        )
        return True
    except:
        return False


def executar_automacao():
    cnpj = "04813255000124"
    senha = os.getenv("SENHA_ABC")

    with Camoufox(
        headless=False,
        geoip=True,
        locale=["pt-BR", "pt", "en-US"],
        os="windows",
        screen=Screen(max_width=1366, max_height=768),
    ) as browser:

        page = browser.new_page()

        try:
            # 🔥 1. WARM-UP (ESSENCIAL)
            print("Aquecendo sessão...")
            page.goto("https://www.google.com.br", wait_until="domcontentloaded")
            simular_leitura(page, 4.0)

            # 🔥 2. LOGIN PAGE
            url = "https://receita.joaopessoa.pb.gov.br/notafiscal/paginas/portal/index.html#/login"

            print("Acessando página de login...")
            page.goto(url, wait_until="domcontentloaded")
            simular_leitura(page, 3.0)

            # 🔥 3. CAMPOS
            input_cpf = page.locator("input[name='cpfCnpj']")
            input_senha = page.locator("input[name='senha']")

            print("Digitando credenciais...")
            digitar(page, input_cpf, cnpj)
            delay(1.0, 2.0)

            digitar(page, input_senha, senha)
            simular_leitura(page, 2.0)

            # 🔥 4. CAPTCHA
            for tentativa in range(3):
                print(f"Tentativa captcha {tentativa+1}")

                frame = page.frame_locator("//iframe[@title='reCAPTCHA']")
                checkbox = frame.locator("#recaptcha-anchor")

                mover_mouse(page)
                clicar(page, checkbox)

                delay(2.0, 3.0)

                if captcha_tem_desafio(page):
                    print("Captcha com desafio detectado...")

                    # comportamento humano → navegar novamente
                    page.goto(url, wait_until="domcontentloaded")
                    simular_leitura(page, 3.0)

                    input_cpf = page.locator("input[name='cpfCnpj']")
                    input_senha = page.locator("input[name='senha']")

                    digitar(page, input_cpf, cnpj)
                    delay(1.0, 2.0)
                    digitar(page, input_senha, senha)

                    continue

                break

            # 🔥 5. LOGIN
            print("Clicando em Entrar...")
            btn_entrar = page.get_by_role("button", name="Entrar")
            clicar(page, btn_entrar)

            simular_leitura(page, 5.0)

        except Exception as e:
            print(f"Erro na automação: {e}")