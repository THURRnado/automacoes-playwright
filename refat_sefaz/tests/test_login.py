import os
import shutil
import pytest

from core.login import login, DOWNLOAD_BASE_PATH
from core.browser import close_browser_session


@pytest.fixture(autouse=True)
def sefaz_credentials(monkeypatch):
    """Garante que as credenciais estão definidas para todos os testes."""
    monkeypatch.setenv("SEFAZ_USER", os.getenv("SEFAZ_USER", ""))
    monkeypatch.setenv("SEFAZ_PASSWORD", os.getenv("SEFAZ_PASSWORD", ""))


class TestLogin:

    def test_login_sucesso(self):
        """Testa se o login retorna uma sessão válida e o usuário está autenticado."""
        pw, browser, context, page, download_dir = login()
        try:
            assert page is not None, "Page não foi criada"

            # Após login, o iframe exibe o div de boas-vindas com cronômetro de sessão
            login_frame = page.frame_locator('#atf-login iframe').first
            assert login_frame.locator('#cronometro_div').count() > 0, \
                "Div pós-login não encontrado — login pode ter falhado"

            # Verifica se o botão de Sair está presente (confirma sessão ativa)
            assert login_frame.locator('a.btn-danger').count() > 0, \
                "Botão 'Sair' não encontrado — sessão pode não estar ativa"

        finally:
            close_browser_session(pw, browser)
            if os.path.exists(download_dir):
                shutil.rmtree(download_dir)

    def test_download_dir_criado(self):
        """Testa se o diretório de download é criado corretamente."""
        pw, browser, context, page, download_dir = login()
        try:
            assert os.path.exists(download_dir), f"Diretório de download não foi criado: {download_dir}"
            assert download_dir.startswith(DOWNLOAD_BASE_PATH), "Diretório fora do caminho esperado"
        finally:
            close_browser_session(pw, browser)
            if os.path.exists(download_dir):
                shutil.rmtree(download_dir)

    def test_request_id_customizado(self):
        """Testa se um request_id customizado é usado corretamente no diretório."""
        request_id = "teste_customizado_123"
        pw, browser, context, page, download_dir = login(request_id=request_id)
        try:
            assert request_id in download_dir, "request_id customizado não está no caminho do diretório"
        finally:
            close_browser_session(pw, browser)
            if os.path.exists(download_dir):
                shutil.rmtree(download_dir)

    def test_credenciais_ausentes(self, monkeypatch):
        """Testa se ValueError é lançado quando as credenciais não estão configuradas."""
        monkeypatch.delenv("SEFAZ_USER", raising=False)
        monkeypatch.delenv("SEFAZ_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="SEFAZ_USER e SEFAZ_PASSWORD"):
            login()

    def test_rollback_diretorio_em_falha(self, monkeypatch):
        """Testa se o diretório de download é removido quando o login falha."""
        monkeypatch.setattr("core.login.SEFAZ_URL", "https://url-invalida-que-nao-existe.com")

        with pytest.raises(Exception):
            login()

        # Após a falha, nenhum diretório com prefixo do user_id padrão deve existir
        if os.path.exists(DOWNLOAD_BASE_PATH):
            dirs = [
                d for d in os.listdir(DOWNLOAD_BASE_PATH)
                if d.startswith("1_")
            ]
            assert len(dirs) == 0, f"Diretório não foi removido no rollback: {dirs}"