import logging
import os

from flask import jsonify, request
from werkzeug.utils import secure_filename  # Remove caracteres perigosos do nome (ex: ../../)

from config import (
    EXTENSOES_PERMITIDAS,
    TAMANHO_MAXIMO_ARQUIVO,
    TAMANHO_MAXIMO_KB,
    UPLOAD_FOLDER,
)
from models.upload_model import UploadModel

logger = logging.getLogger("uploads")


class UploadController:

    @staticmethod
    def arquivo_permitido(nome_arquivo):
        """Verifica se a extensão do arquivo é permitida."""
        return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in EXTENSOES_PERMITIDAS

    @staticmethod
    def tamanho_do_arquivo(arquivo):
        """Mede o tamanho real do arquivo enviado (sem depender do Content-Length)."""
        arquivo.stream.seek(0, os.SEEK_END)
        tamanho = arquivo.stream.tell()
        arquivo.stream.seek(0)
        return tamanho

    @staticmethod
    def upload_file():
        """Recebe e processa o upload do arquivo."""

        # Verifica se um arquivo foi enviado
        if 'file' not in request.files:
            logger.warning("Falha no upload: Nenhum arquivo enviado")
            return jsonify({"erro": "Nenhum arquivo enviado"}), 400

        arquivo = request.files['file']

        # Verifica se o nome do arquivo está vazio
        if arquivo.filename == '':
            logger.warning("Falha no upload: Nome do arquivo vazio")
            return jsonify({"erro": "Nome do arquivo vazio"}), 400

        # Limpa o nome e valida a extensão (já no nome limpo, que é o que será salvo)
        nome_arquivo = secure_filename(arquivo.filename)
        if not nome_arquivo or not UploadController.arquivo_permitido(nome_arquivo):
            logger.warning(f"Falha no upload: {arquivo.filename} - Tipo de arquivo não permitido")
            return jsonify({
                "erro": "Tipo de arquivo não permitido!",
                "tipos_permitidos": sorted(EXTENSOES_PERMITIDAS)
            }), 400

        # Verifica o tamanho real do arquivo
        if UploadController.tamanho_do_arquivo(arquivo) > TAMANHO_MAXIMO_ARQUIVO:
            logger.warning(f"Falha no upload: {nome_arquivo} - Tamanho excede {TAMANHO_MAXIMO_KB} KB")
            return jsonify({
                "erro": f"Arquivo excede o tamanho máximo permitido ({TAMANHO_MAXIMO_KB} KB)"
            }), 400

        # Registra no banco (o nome é UNIQUE: não deixa sobrescrever um arquivo existente)
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        if not UploadModel.save_file(nome_arquivo, caminho_arquivo):
            logger.warning(f"Falha no upload: {nome_arquivo} - Arquivo já existe")
            return jsonify({"erro": "Já existe um arquivo com esse nome"}), 409

        # Grava no disco; se falhar, desfaz o registro para não ficar inconsistente
        try:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            arquivo.save(caminho_arquivo)
        except OSError:
            UploadModel.delete_by_filename(nome_arquivo)
            logger.exception(f"Falha no upload: {nome_arquivo} - Erro ao gravar no disco")
            return jsonify({"erro": "Erro ao salvar o arquivo no servidor"}), 500

        logger.info(f"Upload bem-sucedido: {nome_arquivo} | IP: {request.remote_addr}")
        return jsonify({
            "mensagem": "Arquivo salvo com sucesso!",
            "arquivo": nome_arquivo
        }), 200
