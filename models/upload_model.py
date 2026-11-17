import sqlite3

from database.db import get_db_connection


class UploadModel:

    @staticmethod
    def save_file(filename, filepath):
        """Registra o arquivo no banco. Retorna None se o nome já existir."""
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO uploads (filename, filepath)
                VALUES (?, ?)
            ''', (filename, filepath))
            conn.commit()
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
        return True

    @staticmethod
    def delete_by_filename(filename):
        """Remove o registro (usado para desfazer se a gravação em disco falhar)."""
        conn = get_db_connection()
        conn.execute('DELETE FROM uploads WHERE filename = ?', (filename,))
        conn.commit()
        conn.close()

    @staticmethod
    def find_by_filename(filename):
        conn = get_db_connection()
        file = conn.execute('SELECT * FROM uploads WHERE filename = ?', (filename,)).fetchone()
        conn.close()
        return file
