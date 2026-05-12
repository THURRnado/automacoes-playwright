# tests/test_venda_varejo.py
import os
import shutil
import pytest
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.venda_varejo import (
    run,
    DEFAULT_DT_INICIO,
    DEFAULT_DT_FINAL,
    DEFAULT_EMPRESA_IE,
    PROCESS_DIR,
)
from core.login import DOWNLOAD_BASE_PATH


@pytest.fixture(autouse=True)
def sefaz_credentials(monkeypatch):
    monkeypatch.setenv("SEFAZ_USER", os.getenv("SEFAZ_USER", ""))
    monkeypatch.setenv("SEFAZ_PASSWORD", os.getenv("SEFAZ_PASSWORD", ""))


@pytest.fixture()
def cleanup_downloads():
    created_dirs = []
    yield created_dirs
    for d in created_dirs:
        if os.path.exists(d):
            shutil.rmtree(d)


class TestVendaVarejo:

    def test_download_pdf_realizado(self, cleanup_downloads):
        """Testa se o PDF é baixado e salvo corretamente."""
        pdf_path, csv_path = run()
        cleanup_downloads.append(os.path.dirname(os.path.dirname(pdf_path)))

        assert os.path.exists(pdf_path), f"PDF não encontrado: {pdf_path}"
        assert os.path.getsize(pdf_path) > 0, "PDF baixado está vazio"

    def test_download_csv_realizado(self, cleanup_downloads):
        """Testa se o CSV é baixado e salvo corretamente."""
        pdf_path, csv_path = run()
        cleanup_downloads.append(os.path.dirname(os.path.dirname(pdf_path)))

        assert os.path.exists(csv_path), f"CSV não encontrado: {csv_path}"
        assert os.path.getsize(csv_path) > 0, "CSV baixado está vazio"

    def test_arquivos_salvos_no_diretorio_correto(self, cleanup_downloads):
        """Testa se os arquivos são salvos dentro da pasta correta."""
        pdf_path, csv_path = run()
        cleanup_downloads.append(os.path.dirname(os.path.dirname(pdf_path)))

        assert PROCESS_DIR in pdf_path, f"PDF não está na pasta correta: {pdf_path}"
        assert PROCESS_DIR in csv_path, f"CSV não está na pasta correta: {csv_path}"
        assert DOWNLOAD_BASE_PATH in pdf_path, f"PDF fora do caminho base esperado: {pdf_path}"
        assert DOWNLOAD_BASE_PATH in csv_path, f"CSV fora do caminho base esperado: {csv_path}"

    def test_parametros_customizados(self, cleanup_downloads):
        """Testa se run aceita parâmetros customizados sem erros."""
        pdf_path, csv_path = run(
            dt_inicio=DEFAULT_DT_INICIO,
            dt_final=DEFAULT_DT_FINAL,
            empresa_ie=DEFAULT_EMPRESA_IE,
        )
        cleanup_downloads.append(os.path.dirname(os.path.dirname(pdf_path)))

        assert os.path.exists(pdf_path), f"PDF não encontrado com parâmetros customizados: {pdf_path}"
        assert os.path.exists(csv_path), f"CSV não encontrado com parâmetros customizados: {csv_path}"

    def test_credenciais_ausentes(self, monkeypatch):
        """Testa se ValueError é lançado quando as credenciais não estão configuradas."""
        monkeypatch.delenv("SEFAZ_USER", raising=False)
        monkeypatch.delenv("SEFAZ_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="SEFAZ_USER e SEFAZ_PASSWORD"):
            run()

    def test_sem_registros(self, monkeypatch):
        """Testa se ValueError é lançado quando não há registros no período."""
        with pytest.raises(ValueError, match="Nenhum registro encontrado"):
            run(dt_inicio="01/1990", dt_final="01/1990")