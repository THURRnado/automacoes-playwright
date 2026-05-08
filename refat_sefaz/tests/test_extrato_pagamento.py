import os
import shutil
import pytest

from services.extrato_pagamento import run, DEFAULT_DT_INICIO, DEFAULT_DT_FINAL, DEFAULT_EMPRESA_IE
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


class TestExtratoPagamento:

    def test_download_realizado(self, cleanup_downloads):
        """Testa se o arquivo PDF é baixado e salvo corretamente."""
        file_path = run()
        cleanup_downloads.append(os.path.dirname(os.path.dirname(file_path)))

        assert os.path.exists(file_path), f"Arquivo não encontrado: {file_path}"
        assert file_path.endswith(".pdf"), f"Arquivo não é PDF: {file_path}"
        assert os.path.getsize(file_path) > 0, "Arquivo baixado está vazio"

    def test_arquivo_salvo_no_diretorio_correto(self, cleanup_downloads):
        """Testa se o arquivo é salvo dentro da pasta extrato_pagamento."""
        file_path = run()
        cleanup_downloads.append(os.path.dirname(os.path.dirname(file_path)))

        assert "extrato_pagamento" in file_path, \
            f"Arquivo não está na pasta correta: {file_path}"
        assert DOWNLOAD_BASE_PATH in file_path, \
            f"Arquivo fora do caminho base esperado: {file_path}"

    def test_parametros_customizados(self, cleanup_downloads):
        """Testa se o processo aceita parâmetros customizados sem erros."""
        file_path = run(
            dt_inicio=DEFAULT_DT_INICIO,
            dt_final=DEFAULT_DT_FINAL,
            empresa_ie=DEFAULT_EMPRESA_IE,
        )
        cleanup_downloads.append(os.path.dirname(os.path.dirname(file_path)))

        assert os.path.exists(file_path), f"Arquivo não encontrado com parâmetros customizados: {file_path}"

    def test_credenciais_ausentes(self, monkeypatch):
        """Testa se ValueError é lançado quando as credenciais não estão configuradas."""
        monkeypatch.delenv("SEFAZ_USER", raising=False)
        monkeypatch.delenv("SEFAZ_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="SEFAZ_USER e SEFAZ_PASSWORD"):
            run()