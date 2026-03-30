#!/usr/bin/env python3
"""
federal_selenium.py
====================
Robô de Emissão de CND Federal
================================
Acessa o portal da Receita Federal, emite a CND para o(s) CNPJ(s)
informado(s) e salva o PDF na pasta "Emitidas".
Caso a CND não seja emitida, salva screenshot em "Sem CND".

Uso:
    python federal_selenium.py <CNPJ>
    python federal_selenium.py 04813255000124
    python federal_selenium.py 04813255000124 11222333000181   (múltiplos)
"""

import os
import sys
import time
import random
from datetime import datetime

from selenium.webdriver.common.by import By

from core.configs_selenium import (
    EMITIDAS_DIR,
    SEM_CND_DIR,
    URL_BASE,
    URL_PORTAL,
    criar_driver,
)
from core.acoes_selenium import (
    delay_humano,
    mover_mouse_aleatorio,
    simular_leitura,
    aguardar_spa,
    aceitar_cookies,
    encontrar_campo_cnpj,
    encontrar_botao_emitir,
    preencher_cnpj_angular,
    salvar_pdf,
    _snapshot_pasta,
    aguardar_download,
    tratar_dialogo_cnd_valida,
    aguardar_resultado,
    limpar_cnpj,
)


# ─── Fluxo de uma tentativa ───────────────────────────────────────────────────

def emitir_cnd_tentativa(driver, cnpj: str, timestamp: str) -> str:
    """
    Executa uma tentativa de emissão de CND. Retorna:
      'sucesso'  — PDF salvo em Emitidas/
      'erro_023' — Token rejeitado (tentar novamente)
      'sem_cnd'  — CNPJ com débitos ou CND indisponível
      'erro'     — Falha inesperada (campo/botão não encontrado)
    """
    janela_original = driver.current_window_handle

    # ── 1. Portal principal (aquece sessão / cookies) ────────────────────────
    print("  → Acessando portal da Receita Federal...")
    driver.get(URL_PORTAL)
    aguardar_spa(driver, timeout=20)
    aceitar_cookies(driver)
    simular_leitura(driver, random.uniform(4, 7))

    # ── 2. Navega para emissão de CND ────────────────────────────────────────
    print("  → Navegando para emissão de CND...")
    driver.get(URL_BASE)
    aguardar_spa(driver, timeout=30)
    aceitar_cookies(driver)
    simular_leitura(driver, random.uniform(5, 9))

    # ── 3. Localiza campo CNPJ ───────────────────────────────────────────────
    campo_ni = encontrar_campo_cnpj(driver)
    if campo_ni is None:
        debug = os.path.join(SEM_CND_DIR, f"DEBUG_{cnpj}_{timestamp}.png")
        driver.save_screenshot(debug)
        print(f"  [ERRO] Campo CNPJ não encontrado. Debug: {debug}")
        return "erro"

    # ── 4. Preenche CNPJ ─────────────────────────────────────────────────────
    print("  → Preenchendo CNPJ...")
    preencher_cnpj_angular(driver, campo_ni, cnpj)
    simular_leitura(driver, random.uniform(3, 5))

    # ── 5. Localiza e clica em Emitir ────────────────────────────────────────
    print("  → Localizando botão Emitir...")
    botao = encontrar_botao_emitir(driver)
    if botao is None:
        debug = os.path.join(SEM_CND_DIR, f"DEBUG_botao_{cnpj}_{timestamp}.png")
        driver.save_screenshot(debug)
        print(f"  [ERRO] Botão não encontrado. Debug: {debug}")
        return "erro"

    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", botao)
    delay_humano(1.0, 2.0)
    mover_mouse_aleatorio(driver, botao)
    delay_humano(0.6, 1.2)

    # Snapshot ANTES de clicar (para detectar novos downloads)
    snap_emitidas  = _snapshot_pasta(EMITIDAS_DIR)
    snap_downloads = _snapshot_pasta(
        os.path.join(os.path.expanduser("~"), "Downloads")
    )

    print("  → Clicando em Emitir Certidão...")
    botao.click()
    time.sleep(3)  # Aguarda diálogo ou navegação

    # ── 6. Detecta diálogo "Certidão Válida Encontrada" ───────────────────────
    dialogo_tratado = False
    try:
        corpo_imediato = driver.find_element(By.TAG_NAME, "body").text.lower()
        if "certidão válida encontrada" in corpo_imediato:
            if tratar_dialogo_cnd_valida(driver):
                dialogo_tratado = True
    except Exception:
        pass

    # ── 7a. Fluxo com diálogo: portal faz download direto do PDF ─────────────
    if dialogo_tratado:
        time.sleep(2)
        if len(driver.window_handles) > 1:
            nova = [w for w in driver.window_handles if w != janela_original][0]
            driver.switch_to.window(nova)
            delay_humano(2.5, 4.0)
            pdf = os.path.join(EMITIDAS_DIR, f"CND_{cnpj}_{timestamp}.pdf")
            salvar_pdf(driver, pdf)
            print(f"  ✔ PDF salvo: {pdf}")
            try:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception:
                pass
            return "sucesso"

        print("  → Aguardando download do PDF (até 60s)...")
        arquivo = aguardar_download(snap_emitidas, snap_downloads, cnpj, timestamp)
        if arquivo:
            print(f"  ✔ PDF baixado: {arquivo}")
            return "sucesso"

        print("  ✖ Download não detectado após 60s.")
        ss = os.path.join(SEM_CND_DIR, f"SemCND_{cnpj}_{timestamp}.png")
        driver.save_screenshot(ss)
        print(f"  → Screenshot: {ss}")
        return "sem_cnd"

    # ── 7b. Fluxo sem diálogo: aguarda resultado na página ───────────────────
    print("  → Aguardando resultado...")
    resultado = aguardar_resultado(driver, janela_original, timeout=45)

    # ── 8. Processa resultado ─────────────────────────────────────────────────
    if resultado == "erro_023":
        print("  ✖ Erro 023: score do token insuficiente.")
        ss = os.path.join(SEM_CND_DIR, f"Erro023_{cnpj}_{timestamp}.png")
        driver.save_screenshot(ss)
        return "erro_023"

    if resultado == "nova_janela":
        nova = [w for w in driver.window_handles if w != janela_original][0]
        driver.switch_to.window(nova)
        delay_humano(2.5, 4.0)
        print("  → Certidão aberta em nova aba.")
        pdf = os.path.join(EMITIDAS_DIR, f"CND_{cnpj}_{timestamp}.pdf")
        salvar_pdf(driver, pdf)
        print(f"  ✔ PDF salvo: {pdf}")
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception:
            pass
        return "sucesso"

    if resultado == "inline_sucesso":
        delay_humano(2.0, 3.0)
        print("  → Certidão na página — salvando PDF...")
        pdf = os.path.join(EMITIDAS_DIR, f"CND_{cnpj}_{timestamp}.pdf")
        salvar_pdf(driver, pdf)
        print(f"  ✔ PDF salvo: {pdf}")
        return "sucesso"

    # timeout / inline_erro: verifica se o download ocorreu mesmo assim
    arquivo = aguardar_download(
        snap_emitidas, snap_downloads, cnpj, timestamp, timeout=10
    )
    if arquivo:
        print(f"  ✔ PDF baixado: {arquivo}")
        return "sucesso"

    corpo = ""
    try:
        corpo = driver.find_element(By.TAG_NAME, "body").text
    except Exception:
        pass
    motivo = ""
    for kw in ["débito", "pendência", "não foi possível", "irregular"]:
        if kw in corpo.lower():
            idx = corpo.lower().find(kw)
            motivo = corpo[max(0, idx - 20):idx + 100].strip()
            break
    print(f"  ✖ CND não emitida.{' Motivo: ' + motivo if motivo else ' (timeout)'}")
    ss = os.path.join(SEM_CND_DIR, f"SemCND_{cnpj}_{timestamp}.png")
    driver.save_screenshot(ss)
    print(f"  → Screenshot: {ss}")
    return "sem_cnd"


# ─── Orquestrador por CNPJ ────────────────────────────────────────────────────

def emitir_cnd(cnpj_raw: str) -> bool:
    """
    Cria o driver, realiza até MAX_TENTATIVAS e retorna True em caso de sucesso.
    O driver é sempre encerrado ao final, com ou sem sucesso.
    """
    os.makedirs(EMITIDAS_DIR, exist_ok=True)
    os.makedirs(SEM_CND_DIR, exist_ok=True)

    try:
        cnpj = limpar_cnpj(cnpj_raw)
    except ValueError as exc:
        print(f"  [ERRO] {exc}")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n{'═'*52}")
    print(f"  CNPJ : {cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}")
    print(f"  Data : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'═'*52}")

    driver = criar_driver()
    MAX_TENTATIVAS = 2

    try:
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            if tentativa > 1:
                espera = random.randint(180, 240)
                print(f"\n  → Aguardando {espera}s antes da tentativa {tentativa}...")
                time.sleep(espera)

            print(f"\n  [Tentativa {tentativa}/{MAX_TENTATIVAS}]")
            resultado = emitir_cnd_tentativa(driver, cnpj, timestamp)

            if resultado == "sucesso":
                return True
            if resultado in ("sem_cnd", "erro"):
                return False
            # erro_023: tenta novamente

        print(f"  ✖ {MAX_TENTATIVAS} tentativas falharam com erro 023.")
        print("    Isso indica que o score do Kasada ainda está baixo.")
        print("    Tente executar o robô novamente daqui a alguns minutos.")
        return False

    except Exception as exc:
        print(f"  [ERRO INESPERADO] {exc}")
        try:
            ss = os.path.join(SEM_CND_DIR, f"Erro_{cnpj}_{timestamp}.png")
            driver.save_screenshot(ss)
            print(f"  → Screenshot: {ss}")
        except Exception:
            pass
        return False

    finally:
        try:
            driver.quit()
        except Exception:
            pass
        try:
            driver.service.process = None
        except Exception:
            pass


# ─── Ponto de entrada ─────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cnpjs = sys.argv[1:]
    resultados = {"ok": [], "falha": []}

    for i, cnpj in enumerate(cnpjs, 1):
        if len(cnpjs) > 1:
            print(f"\n[{i}/{len(cnpjs)}] Processando CNPJ: {cnpj}")
        sucesso = emitir_cnd(cnpj)
        (resultados["ok"] if sucesso else resultados["falha"]).append(cnpj)
        if i < len(cnpjs):
            delay_humano(5.0, 9.0)

    if len(cnpjs) > 1:
        print(f"\n{'═'*52}")
        print(f"  RESUMO FINAL")
        print(f"  ✔ Sucesso : {len(resultados['ok'])} CNPJ(s)")
        print(f"  ✖ Falha   : {len(resultados['falha'])} CNPJ(s)")
        if resultados["falha"]:
            print(f"  Falhas    : {', '.join(resultados['falha'])}")
        print(f"{'═'*52}")


if __name__ == "__main__":
    main()