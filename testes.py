import os
import zipfile
import urllib.request
import ssl

PASTA_PACOTE = "uploads/certificado_digital/pacote_completo_cadeias"
URL_PACOTE = "https://www.gov.br/iti/pt-br/assuntos/repositorio/certificados-das-acs-da-icp-brasil-arquivo-unico-compactado"


def baixar_pacote_cadeias() -> str:
    """
    Baixa o pacote completo de cadeias da ICP-Brasil se ainda não existir.
    Retorna o caminho da pasta com os certificados extraídos.
    """
    os.makedirs(PASTA_PACOTE, exist_ok=True)

    # Verifica se já foi baixado e extraído anteriormente
    certs_existentes = [f for f in os.listdir(PASTA_PACOTE) if f.endswith((".crt", ".cer", ".pem"))]
    if certs_existentes:
        print(f"Pacote já existe com {len(certs_existentes)} certificados em '{PASTA_PACOTE}', pulando download.")
        return PASTA_PACOTE

    print("Baixando pacote completo de cadeias da ICP-Brasil...")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Primeiro busca a URL real do arquivo compactado na página
    import urllib.parse
    from html.parser import HTMLParser

    class LinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                for attr, val in attrs:
                    if attr == "href" and val and (".zip" in val or ".tar" in val):
                        self.links.append(val)

    with urllib.request.urlopen(URL_PACOTE, context=ctx) as response:
        html = response.read().decode("utf-8", errors="ignore")

    parser = LinkParser()
    parser.feed(html)

    if not parser.links:
        raise Exception("Não foi possível encontrar o link do arquivo compactado na página da ICP-Brasil.")

    url_arquivo = parser.links[0]
    if not url_arquivo.startswith("http"):
        url_arquivo = "https://www.gov.br" + url_arquivo

    print(f"URL do pacote encontrada: {url_arquivo}")

    caminho_zip = os.path.join(PASTA_PACOTE, "pacote_cadeias.zip")
    urllib.request.urlretrieve(url_arquivo, caminho_zip)
    print("Download concluído, extraindo...")

    with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
        zip_ref.extractall(PASTA_PACOTE)

    os.remove(caminho_zip)
    print(f"Pacote extraído em: {PASTA_PACOTE}")

    return PASTA_PACOTE