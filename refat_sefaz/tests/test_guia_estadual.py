import os
import shutil
import pytest

from services.guia_estadual import run, DEFAULT_EMPRESA_IE, DEFAULT_DT_VENC_INICIO, DEFAULT_DT_VENC_FIM
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


class TestGuiaEstadual:

    def test_download_ou_sem_guia(self, cleanup_downloads):
        """Executa o processo e verifica download (se houver guia) ou retorno None."""
        result = run()
        if result is None:
            pytest.skip("Nenhuma guia encontrada — cenário válido")
        cleanup_downloads.append(os.path.dirname(os.path.dirname(result)))

        assert os.path.exists(result), f"Arquivo não encontrado: {result}"
        assert result.endswith(".pdf"), f"Arquivo não é PDF: {result}"
        assert os.path.getsize(result) > 0, "Arquivo baixado está vazio"

    def test_arquivo_salvo_no_diretorio_correto(self, cleanup_downloads):
        """Testa se o arquivo é salvo dentro da pasta guia_estadual."""
        result = run()
        if result is None:
            pytest.skip("Nenhuma guia encontrada — cenário válido")
        cleanup_downloads.append(os.path.dirname(os.path.dirname(result)))

        assert "guia_estadual" in result, f"Arquivo não está na pasta correta: {result}"
        assert DOWNLOAD_BASE_PATH in result, f"Arquivo fora do caminho base esperado: {result}"

    def test_parametros_customizados(self, cleanup_downloads):
        """Testa se o processo aceita parâmetros customizados sem erros."""
        result = run(
            empresa_ie=DEFAULT_EMPRESA_IE,
            dt_venc_inicio=DEFAULT_DT_VENC_INICIO,
            dt_venc_fim=DEFAULT_DT_VENC_FIM,
        )
        if result is None:
            pytest.skip("Nenhuma guia encontrada — cenário válido")
        cleanup_downloads.append(os.path.dirname(os.path.dirname(result)))

        assert os.path.exists(result), f"Arquivo não encontrado com parâmetros customizados: {result}"

    def test_credenciais_ausentes(self, monkeypatch):
        """Testa se ValueError é lançado quando as credenciais não estão configuradas."""
        monkeypatch.delenv("SEFAZ_USER", raising=False)
        monkeypatch.delenv("SEFAZ_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="SEFAZ_USER e SEFAZ_PASSWORD"):
            run()
