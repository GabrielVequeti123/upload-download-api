import logging
import os
import sys

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

import config
from database.db import init_db
from routes.download_route import download_bp
from routes.upload_route import upload_bp


def configurar_logs():
    """Logs no terminal (o Render mostra isso na aba Logs) e também em arquivo."""
    formato = logging.Formatter("%(asctime)s - %(message)s")
    logger = logging.getLogger("uploads")
    if logger.handlers:  # evita duplicar handlers
        return
    logger.setLevel(logging.INFO)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formato)
    logger.addHandler(console)

    try:
        os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
        arquivo = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
        arquivo.setFormatter(formato)
        logger.addHandler(arquivo)
    except OSError:
        logger.warning("Não foi possível criar o arquivo de log; usando só o terminal.")


configurar_logs()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.json.ensure_ascii = False  # acentos legíveis no JSON ("não" em vez de "n\u00e3o")

# O Render coloca um proxy na frente do app. Sem isso, o IP registrado no log seria o do proxy.
# x_for=1: confia em UM proxy (o do Render).
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
init_db()

app.register_blueprint(upload_bp, url_prefix='/uploads')
app.register_blueprint(download_bp, url_prefix='/downloads')


@app.route('/', methods=['GET'])
def index():
    """Rota raiz: mostra que a API está no ar e quais endpoints existem."""
    return jsonify({
        "api": "Upload & Download de arquivos",
        "status": "online",
        "endpoints": {
            "upload": "POST /uploads/upload (form-data, campo 'file')",
            "download": "GET /downloads/download/<filename>",
            "health": "GET /health",
        },
        "tipos_permitidos": sorted(config.EXTENSOES_PERMITIDAS),
        "tamanho_maximo_kb": config.TAMANHO_MAXIMO_KB,
    })


@app.route('/health', methods=['GET'])
def health():
    """Usado pelo Render para saber se o serviço está saudável."""
    return jsonify({"status": "ok"}), 200


# ---- Erros sempre em JSON (em vez de páginas HTML) ----
@app.errorhandler(404)
def erro_404(_):
    return jsonify({"erro": "Rota não encontrada"}), 404


@app.errorhandler(405)
def erro_405(_):
    return jsonify({"erro": "Método não permitido para esta rota"}), 405


@app.errorhandler(413)
def erro_413(_):
    return jsonify({"erro": "Requisição muito grande"}), 413


@app.errorhandler(500)
def erro_500(_):
    return jsonify({"erro": "Erro interno do servidor"}), 500


if __name__ == '__main__':
    # Só para desenvolvimento local. Em produção o Render usa o gunicorn (veja render.yaml).
    # O modo debug fica DESLIGADO por padrão: ele expõe o código e permite executar comandos.
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug)
