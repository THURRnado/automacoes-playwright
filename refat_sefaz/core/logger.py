import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado para o módulo informado.

    Uso:
        from core.logger import get_logger
        logger = get_logger(__name__)

    No futuro (integração Django), basta adicionar um FileHandler ou
    substituir o StreamHandler pelo handler do Django aqui, sem alterar
    nenhum outro arquivo do projeto.
    """
    logger = logging.getLogger(name)

    # Evita duplicar handlers se o logger já foi configurado
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Console Handler ──────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(_get_formatter())
    logger.addHandler(console_handler)

    # ── Futuro: File Handler (Django ou standalone) ──────────────────────────
    # Descomente e adapte quando necessário:
    #
    # import os
    # log_dir = os.path.join(BASE_DIR, "logs")
    # os.makedirs(log_dir, exist_ok=True)
    # file_handler = logging.FileHandler(os.path.join(log_dir, f"{name}.log"), encoding="utf-8")
    # file_handler.setLevel(logging.INFO)
    # file_handler.setFormatter(_get_formatter())
    # logger.addHandler(file_handler)

    # Não propaga para o logger raiz (evita logs duplicados)
    logger.propagate = False

    return logger


def _get_formatter() -> logging.Formatter:
    """Formato padrão dos logs."""
    return logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )