import os

from flask import jsonify, send_from_directory
from werkzeug.exceptions import NotFound
from werkzeug.utils import secure_filename

from config import UPLOAD_FOLDER
from models.download_model import DownloadModel


class DownloadController:

    @staticmethod
    def download_file(filename):
        """Envia o arquivo pedido como anexo (download), ou 404 em JSON."""
        filename = secure_filename(filename)

        # O arquivo precisa estar registrado no banco...
        if not filename or DownloadModel.find_by_filename(filename) is None:
            return jsonify({"erro": "Arquivo não encontrado"}), 404

        # ...e existir de fato no disco.
        try:
            return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
        except (NotFound, FileNotFoundError):
            return jsonify({"erro": "Arquivo não encontrado"}), 404
