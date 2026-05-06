import os
import ssl
import zipfile
import urllib.request
from html.parser import HTMLParser
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization.pkcs12 import load_pkcs12 as load_p12
from cryptography import x509
import tempfile

PASTA_PACOTE = "uploads/certificado_digital/pacote_completo_cadeias"
URL_PACOTE = "https://www.gov.br/iti/pt-br/assuntos/repositorio/certificados-das-acs-da-icp-brasil-arquivo-unico-compactado"


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, val in attrs:
                if attr == "href" and val and (".zip" in val or ".tar" in val):
                    self.links.append(val)


def baixar_pacote_cadeias() -> str:
    """
    Baixa o pacote completo de cadeias da ICP-Brasil se ainda não existir.
    Retorna o caminho da pasta com os certificados extraídos.
    """
    os.makedirs(PASTA_PACOTE, exist_ok=True)

    certs_existentes = [f for f in os.listdir(PASTA_PACOTE) if f.endswith((".crt", ".cer", ".pem"))]
    if certs_existentes:
        print(f"Pacote já existe com {len(certs_existentes)} certificados em '{PASTA_PACOTE}', pulando download.")
        return PASTA_PACOTE

    print("Baixando pacote completo de cadeias da ICP-Brasil...")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(URL_PACOTE, context=ctx) as response:
        html = response.read().decode("utf-8", errors="ignore")

    parser = _LinkParser()
    parser.feed(html)

    if not parser.links:
        raise Exception("Não foi possível encontrar o link do arquivo compactado na página da ICP-Brasil.")

    url_arquivo = parser.links[0]
    if not url_arquivo.startswith("http"):
        url_arquivo = "https://www.gov.br" + url_arquivo

    print(f"URL do pacote encontrada: {url_arquivo}")

    caminho_zip = os.path.join(PASTA_PACOTE, "pacote_cadeias.zip")

    with urllib.request.urlopen(url_arquivo, context=ctx) as response:
        with open(caminho_zip, "wb") as f:
            f.write(response.read())
    print("Download concluído, extraindo...")

    with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
        zip_ref.extractall(PASTA_PACOTE)

    os.remove(caminho_zip)
    print(f"Pacote extraído em: {PASTA_PACOTE}")

    return PASTA_PACOTE


def _buscar_intermediario_local(issuer, pasta: str) -> x509.Certificate | None:
    for root, _, files in os.walk(pasta):
        for arquivo in files:
            if not arquivo.endswith((".crt", ".cer", ".pem")):
                continue
            caminho = os.path.join(root, arquivo)
            try:
                with open(caminho, "rb") as f:
                    dados = f.read()
                try:
                    cert = x509.load_der_x509_certificate(dados)
                except Exception:
                    cert = x509.load_pem_x509_certificate(dados)
                if cert.subject == issuer:
                    return cert
            except Exception:
                continue
    return None


def _montar_cadeia(certificado_principal) -> bytes:
    pasta = baixar_pacote_cadeias()
    cadeia = certificado_principal.public_bytes(Encoding.PEM)
    cert_atual = certificado_principal

    while True:
        if cert_atual.subject == cert_atual.issuer:
            break

        intermediario = _buscar_intermediario_local(cert_atual.issuer, pasta)
        if intermediario is None:
            print(f"Intermediário não encontrado para: {cert_atual.issuer}")
            break

        print(f"Intermediário encontrado: {intermediario.subject}")
        cadeia += intermediario.public_bytes(Encoding.PEM)
        cert_atual = intermediario

    return cadeia


def extrair_e_criptografar_pfx(pfx_path: str, senha: str, fernet_key: str) -> tuple[bytes, bytes]:
    fernet = Fernet(fernet_key.encode())

    with open(pfx_path, "rb") as f:
        pfx_data = f.read()

    p12 = load_p12(pfx_data, senha.encode())

    if p12.additional_certs:
        cert_bytes = p12.cert.certificate.public_bytes(Encoding.PEM)
        for ca_cert in p12.additional_certs:
            cert_bytes += ca_cert.certificate.public_bytes(Encoding.PEM)
    else:
        cert_bytes = _montar_cadeia(p12.cert.certificate)

    key_bytes = p12.key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption()
    )

    return fernet.encrypt(cert_bytes), fernet.encrypt(key_bytes)


def decifrar_certificado(cert_enc: bytes, key_enc: bytes, fernet_key: str) -> tuple[str, str]:
    fernet = Fernet(fernet_key.encode())

    cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    cert_tmp.write(fernet.decrypt(cert_enc))
    cert_tmp.close()

    key_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".key")
    key_tmp.write(fernet.decrypt(key_enc))
    key_tmp.close()

    return cert_tmp.name, key_tmp.name


def apagar_certificado_temp(cert_path: str, key_path: str):
    for path in (cert_path, key_path):
        try:
            os.remove(path)
        except OSError:
            pass