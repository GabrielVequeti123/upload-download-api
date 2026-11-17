"""Testes da API. Rode com:  python -m unittest discover -v"""
import io
import os
import shutil
import sys
import tempfile
import unittest

# Usa uma pasta temporária para não sujar os dados reais.
_TMP = tempfile.mkdtemp(prefix="api_test_")
os.environ["DATA_DIR"] = _TMP
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from database.db import get_db_connection  # noqa: E402


def arquivo(nome, conteudo=b"ola mundo"):
    return {"file": (io.BytesIO(conteudo), nome)}


class ApiTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(_TMP, ignore_errors=True)

    def up(self, nome, conteudo=b"ola mundo"):
        return self.client.post("/uploads/upload", data=arquivo(nome, conteudo),
                                content_type="multipart/form-data")

    # --- rotas básicas ---
    def test_raiz_e_health(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        r = self.client.get("/health")
        self.assertEqual((r.status_code, r.get_json()), (200, {"status": "ok"}))

    def test_rota_inexistente_retorna_json(self):
        r = self.client.get("/nada")
        self.assertEqual(r.status_code, 404)
        self.assertIn("erro", r.get_json())

    def test_metodo_nao_permitido_retorna_json(self):
        r = self.client.get("/uploads/upload")
        self.assertEqual(r.status_code, 405)
        self.assertIn("erro", r.get_json())

    # --- upload ---
    def test_upload_e_download_ok(self):
        r = self.up("ok.txt", b"conteudo de teste")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["arquivo"], "ok.txt")
        d = self.client.get("/downloads/download/ok.txt")
        self.assertEqual(d.status_code, 200)
        self.assertEqual(d.data, b"conteudo de teste")
        self.assertIn("attachment", d.headers["Content-Disposition"])
        d.close()

    def test_upload_registra_no_banco(self):
        self.up("banco.txt")
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM uploads WHERE filename='banco.txt'").fetchone()
        conn.close()
        self.assertIsNotNone(row)

    def test_sem_arquivo(self):
        r = self.client.post("/uploads/upload", data={}, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)

    def test_nome_vazio(self):
        r = self.up("")
        self.assertEqual(r.status_code, 400)

    def test_extensao_invalida(self):
        r = self.up("virus.exe")
        self.assertEqual(r.status_code, 400)
        self.assertIn("tipos_permitidos", r.get_json())

    def test_arquivo_grande_demais(self):
        r = self.up("grande.txt", b"x" * (31 * 1024))
        self.assertEqual(r.status_code, 400)
        self.assertIn("30 KB", r.get_json()["erro"])

    def test_limite_exato_aceito(self):
        self.assertEqual(self.up("limite.txt", b"x" * (30 * 1024)).status_code, 200)

    def test_requisicao_gigante_413(self):
        r = self.up("enorme.txt", b"x" * (2 * 1024 * 1024))
        self.assertEqual(r.status_code, 413)

    def test_duplicado_retorna_409(self):
        self.assertEqual(self.up("dup.txt").status_code, 200)
        self.assertEqual(self.up("dup.txt").status_code, 409)

    def test_sem_content_length_nao_quebra(self):
        # Bug original: Content-Length ausente causava TypeError (500).
        r = self.client.post("/uploads/upload", data=arquivo("semcl.txt"),
                             content_type="multipart/form-data",
                             headers={"Content-Length": ""})
        self.assertIn(r.status_code, (200, 400))

    def test_nome_so_com_caracteres_invalidos(self):
        r = self.up("日本.txt")
        # secure_filename transforma em "txt" (sem ponto) -> deve ser rejeitado
        self.assertEqual(r.status_code, 400)

    def test_path_traversal_neutralizado(self):
        r = self.up("../../etc/passwd.txt")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["arquivo"], "etc_passwd.txt")

    # --- download ---
    def test_download_inexistente_json(self):
        r = self.client.get("/downloads/download/nao_existe.txt")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json(), {"erro": "Arquivo não encontrado"})

    def test_download_registrado_mas_apagado_do_disco(self):
        self.up("sumiu.txt")
        os.remove(os.path.join(_TMP, "uploads", "sumiu.txt"))
        r = self.client.get("/downloads/download/sumiu.txt")
        self.assertEqual(r.status_code, 404)
        self.assertIn("erro", r.get_json())

    # --- proxy (Render) ---
    def test_ip_real_do_cliente_atras_de_proxy(self):
        import logging
        with self.assertLogs("uploads", level="INFO") as cap:
            self.client.post("/uploads/upload", data=arquivo("proxy.txt"),
                             content_type="multipart/form-data",
                             headers={"X-Forwarded-For": "203.0.113.9"})
        self.assertTrue(any("203.0.113.9" in linha for linha in cap.output))


if __name__ == "__main__":
    unittest.main(verbosity=2)
