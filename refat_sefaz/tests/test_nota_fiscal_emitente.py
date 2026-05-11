import os
import shutil
import pytest

from services.nota_fiscal_emitente import (
    run_txt,
    run_xml,
    DEFAULT_DT_INICIO,
    DEFAULT_DT_FINAL,
    DEFAULT_EMPRESA_IE,
)
from core.login import DOWNLOAD_BASE_PATH


@pytest.fixture(autouse=True)
def sefaz_credentials(monkeypatch):
    """Garante que as credenciais estão definidas para todos os testes."""
    monkeypatch.setenv("SEFAZ_USER", os.getenv("SEFAZ_USER", ""))
    monkeypatch.setenv("SEFAZ_PASSWORD", os.getenv("SEFAZ_PASSWORD", ""))


@pytest.fixture()
def cleanup_downloads():
    """Remove os diretórios de download criados durante os testes."""
    created_dirs = []
    yield created_dirs
    for d in created_dirs:
        if os.path.exists(d):
            shutil.rmtree(d)


class TestNotaFiscalEmitenteTXT:

    def test_download_txt_realizado(self, cleanup_downloads):
        """Testa se o arquivo TXT é baixado e salvo corretamente."""
        file_path = run_txt()
        cleanup_downloads.append(os.path.dirname(os.path.dirname(file_path)))

        assert os.path.exists(file_path), f"Arquivo não encontrado: {file_path}"
        assert os.path.getsize(file_path) > 0, "Arquivo TXT baixado está vazio"

    def test_txt_salvo_no_diretorio_correto(self, cleanup_downloads):
        """Testa se o arquivo TXT é salvo dentro da pasta correta."""
        file_path = run_txt()
        cleanup_downloads.append(os.path.dirname(os.path.dirname(file_path)))

        assert "nota_fiscal_emitente_txt" in file_path, \
            f"Arquivo não está na pasta correta: {file_path}"
        assert DOWNLOAD_BASE_PATH in file_path, \
            f"Arquivo fora do caminho base esperado: {file_path}"

    def test_txt_parametros_customizados(self, cleanup_downloads):
        """Testa se run_txt aceita parâmetros customizados sem erros."""
        file_path = run_txt(
            dt_inicio=DEFAULT_DT_INICIO,
            dt_final=DEFAULT_DT_FINAL,
            empresa_ie=DEFAULT_EMPRESA_IE,
        )
        cleanup_downloads.append(os.path.dirname(os.path.dirname(file_path)))

        assert os.path.exists(file_path), \
            f"Arquivo não encontrado com parâmetros customizados: {file_path}"

    def test_txt_credenciais_ausentes(self, monkeypatch):
        """Testa se ValueError é lançado quando as credenciais não estão configuradas."""
        monkeypatch.delenv("SEFAZ_USER", raising=False)
        monkeypatch.delenv("SEFAZ_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="SEFAZ_USER e SEFAZ_PASSWORD"):
            run_txt()


class TestNotaFiscalEmitenteXML:

    def test_download_xml_realizado(self, cleanup_downloads):
        """Testa se o arquivo ZIP com XMLs é baixado e salvo corretamente."""
        file_path = run_xml()
        cleanup_downloads.append(os.path.dirname(os.path.dirname(file_path)))

        assert os.path.exists(file_path), f"Arquivo não encontrado: {file_path}"
        assert os.path.getsize(file_path) > 0, "Arquivo ZIP baixado está vazio"

    def test_xml_salvo_no_diretorio_correto(self, cleanup_downloads):
        """Testa se o arquivo ZIP é salvo dentro da pasta correta."""
        file_path = run_xml()
        cleanup_downloads.append(os.path.dirname(os.path.dirname(file_path)))

        assert "nota_fiscal_emitente_xml" in file_path, \
            f"Arquivo não está na pasta correta: {file_path}"
        assert DOWNLOAD_BASE_PATH in file_path, \
            f"Arquivo fora do caminho base esperado: {file_path}"

    def test_xml_credenciais_ausentes(self, monkeypatch):
        """Testa se ValueError é lançado quando as credenciais não estão configuradas."""
        monkeypatch.delenv("SEFAZ_USER", raising=False)
        monkeypatch.delenv("SEFAZ_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="SEFAZ_USER e SEFAZ_PASSWORD"):
            run_xml()