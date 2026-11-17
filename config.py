"""Configurações centralizadas da API.

Tudo pode ser sobrescrito por variáveis de ambiente (útil no Render).
Os caminhos são absolutos para não dependerem da pasta de onde o app é iniciado.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Pasta onde ficam uploads, banco e log. No Render, aponte para o disco
# persistente (ex.: /var/data) com a variável DATA_DIR, se você tiver um.
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(DATA_DIR, "uploads"))
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(DATA_DIR, "database.db"))
LOG_FILE = os.environ.get("LOG_FILE", os.path.join(DATA_DIR, "uploads.log"))

EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "pdf", "txt"}

# Tamanho máximo de cada arquivo (padrão do código original: 30 KB).
TAMANHO_MAXIMO_KB = int(os.environ.get("MAX_FILE_SIZE_KB", "30"))
TAMANHO_MAXIMO_ARQUIVO = TAMANHO_MAXIMO_KB * 1024

# Limite rígido da requisição inteira (proteção contra envios gigantes).
MAX_CONTENT_LENGTH = 1024 * 1024  # 1 MB
