# Importa a função get_db_connection do arquivo database.db
# Essa função serve para conectar com o banco de dados
from database.db import get_db_connection


# Classe que cuida das interações de download com o banco de dados
class DownloadModel:

    @staticmethod  # Pode ser chamada sem precisar criar um objeto da classe
    def find_by_filename(filename):
        """Busca um arquivo pelo nome no banco de dados."""
        conn = get_db_connection()  # Abre uma conexão com o banco de dados
        # Pega todas as informações da tabela uploads onde o nome do arquivo é o informado
        file = conn.execute('SELECT * FROM uploads WHERE filename = ?', (filename,)).fetchone()
        conn.close()  # Fecha a conexão com o banco de dados
        return file  # Retorna o arquivo encontrado (ou None se não achar nada)
