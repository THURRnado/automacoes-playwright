import re
import os
from browserforge.fingerprints import Screen
from camoufox.sync_api import Camoufox
from core.acoes_camoufox import delay, simular_leitura, clicar, digitar

"""
INSTALAÇÃO:
    pip install camoufox
    pip install camoufox[geoip]
    python -m camoufox fetch

NO SERVIDOR:

    sudo apt-get update
    sudo apt-get install -y \
    xvfb \
    libgtk-3-0 \
    libx11-xcb1 \
    libdbus-glib-1-2 \
    libxt6 \
    libasound2 \
    libxrandr2 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxss1

Empresa para uso: 
    - NOME: ABC DISTRIBUIDORA JOAO PESSOA LTDA
    - CNPJ: 04813255000124
    - IE: 161339387
"""

PASTA_DOWNLOADS = os.path.abspath("uploads")


def executar_automacao():
    cnpj = "04813255000124"

    with Camoufox(
        headless=False,
        geoip=True,
        locale=["pt-BR", "pt", "en-US"],
        os="windows",
        screen=Screen(max_width=1366, max_height=768),
    ) as browser:
        page = browser.new_page()

        try:
            # 1. WARM-UP: Google antes de ir à Receita
            print("Aquecendo sessão via Google...")
            page.goto("https://www.google.com.br", wait_until="domcontentloaded", timeout=30000)
            simular_leitura(page, segundos=4.0)

            # 2. PORTAL PRINCIPAL DA RECEITA
            print("Acessando portal principal...")
            page.goto(
                "https://servicos.receitafederal.gov.br/",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            simular_leitura(page, segundos=6.0)

            # 3. PÁGINA DE CERTIDÕES
            print("Acessando página de emissão de CND...")
            page.goto(
                "https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            simular_leitura(page, segundos=4.0)

            # 4. BANNER LGPD (se aparecer)
            try:
                btn_cookies = page.get_by_role("button", name=re.compile("Aceitar", re.IGNORECASE))
                if btn_cookies.is_visible(timeout=3000):
                    print("Aceitando cookies...")
                    clicar(page, btn_cookies)
                    delay(1.0, 2.0)
            except Exception:
                pass

            # 5. PREENCHER CNPJ
            print("Preenchendo CNPJ...")
            input_cnpj = page.locator("input[name='niContribuinte']")
            digitar(page, input_cnpj, cnpj)
            simular_leitura(page, segundos=2.0)

            # 6. CLICAR EM EMITIR
            print("Clicando em Emitir...")
            botao_emitir = page.get_by_role("button", name=re.compile("Emitir", re.IGNORECASE)).first
            clicar(page, botao_emitir)

            print("Aguardando processamento...")
            page.wait_for_timeout(4000)

            # 7. MODAL "CERTIDÃO VÁLIDA" + CAPTURA DO DOWNLOAD
            # O clique em "Emitir Nova" é o que dispara o download,
            # então o expect_download envolve exatamente esse clique.
            try:
                btn_nova = page.get_by_role("button", name=re.compile("Emitir Nova", re.IGNORECASE))
                if btn_nova.is_visible(timeout=5000):
                    print("Modal detectado. Capturando download...")
                    os.makedirs(PASTA_DOWNLOADS, exist_ok=True)

                    with page.expect_download(timeout=30000) as download_info:
                        clicar(page, btn_nova)

                    download = download_info.value
                    nome_arquivo = download.suggested_filename or f"certidao_{cnpj}.pdf"
                    caminho = os.path.join(PASTA_DOWNLOADS, nome_arquivo)
                    download.save_as(caminho)
                    print(f"Certidão salva em: {caminho}")

            except Exception as e:
                print(f"Erro ao capturar download: {e}")

        except Exception as e:
            print(f"Automação falhou: {e}")


if __name__ == "__main__":
    executar_automacao()