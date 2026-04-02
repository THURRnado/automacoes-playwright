import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
import tempfile
from cryptography.hazmat.primitives.serialization.pkcs12 import load_pkcs12 as load_p12
from cryptography import x509


def extrair_e_criptografar_pfx(pfx_path: str, senha: str, fernet_key: str) -> tuple[bytes, bytes]:
    fernet = Fernet(fernet_key.encode())

    with open(pfx_path, "rb") as f:
        pfx_data = f.read()

    p12 = load_p12(pfx_data, senha.encode())

    # Monta a cadeia completa: certificado principal + intermediários
    cert_bytes = p12.cert.certificate.public_bytes(Encoding.PEM)
    
    if p12.additional_certs:
        for ca_cert in p12.additional_certs:
            cert_bytes += ca_cert.certificate.public_bytes(Encoding.PEM)

    key_bytes = p12.key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption()
    )

    return fernet.encrypt(cert_bytes), fernet.encrypt(key_bytes)


def decifrar_certificado(cert_enc: bytes, key_enc: bytes, fernet_key: str) -> tuple[str, str]:
    """
    Recebe os bytes cifrados do banco e decifra para arquivos temporários.
    Retorna (cert_path, key_path) — use apagar_certificado_temp() após o uso.
    """
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