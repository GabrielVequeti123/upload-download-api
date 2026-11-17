# API de Upload e Download de Arquivos

API REST desenvolvida em **Python + Flask** para enviar (upload) e baixar (download) arquivos, com registro dos envios em um banco **SQLite**. Projeto de atividade escolar, preparado para deploy no **[Render](https://render.com)**.

🔗 **API publicada:** `https://SEU-SERVICO.onrender.com` *(substitua pelo link real após o deploy)*

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Como executar localmente](#como-executar-localmente)
- [Endpoints](#endpoints)
- [Exemplos de uso](#exemplos-de-uso)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Testes automatizados](#testes-automatizados)
- [Deploy no Render](#deploy-no-render)
- [Limitações conhecidas](#limitações-conhecidas)
- [Correções feitas no código original](#correções-feitas-no-código-original)

---

## Funcionalidades

- Upload de arquivos com validação de **extensão** e **tamanho**.
- Download de arquivos já enviados (como anexo).
- Registro de cada upload no banco SQLite (nome e caminho do arquivo).
- Bloqueio de arquivos com nome duplicado.
- Proteção contra *path traversal* (ex.: `../../arquivo.txt`) usando `secure_filename`.
- Log de todos os uploads (sucessos e falhas) no terminal e no arquivo `uploads.log`.
- Todas as respostas de erro em **JSON**.
- Rota de saúde (`/health`) para monitoramento.

## Tecnologias

| Tecnologia | Uso |
|---|---|
| Python 3.12 | Linguagem |
| Flask 3.1 | Framework web |
| SQLite (`sqlite3`) | Banco de dados |
| Gunicorn | Servidor de produção |
| Render | Hospedagem |

## Estrutura do projeto

O projeto segue o padrão **MVC** (rotas → controllers → models → banco):

```
.
├── app.py                      # Cria o app Flask, registra as rotas e trata erros
├── config.py                   # Configurações (pastas, limites, extensões)
├── requirements.txt            # Dependências
├── render.yaml                 # Configuração de deploy no Render (opcional)
├── routes/
│   ├── upload_route.py         # Rota POST de upload
│   └── download_route.py       # Rota GET de download
├── controllers/
│   ├── upload_controller.py    # Regras de negócio do upload (validações)
│   └── download_controller.py  # Regras de negócio do download
├── models/
│   ├── upload_model.py         # Acesso ao banco: salvar/buscar uploads
│   └── download_model.py       # Acesso ao banco: buscar arquivo por nome
├── database/
│   └── db.py                   # Conexão e criação da tabela SQLite
└── tests/
    └── test_api.py             # Testes automatizados
```

Pastas/arquivos criados automaticamente ao rodar: `uploads/` (arquivos enviados), `database.db` (banco) e `uploads.log` (log). Eles **não** vão para o GitHub (estão no `.gitignore`).

## Como executar localmente

**Pré-requisitos:** Python 3.10 ou superior e `pip`.

```bash
# 1. Clone o repositório
git clone https://github.com/GabrielVequeti123/upload-download-api.git
cd upload-download-api

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows (PowerShell/CMD)

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie a API
python app.py
```

A API ficará disponível em **http://127.0.0.1:5000**.

Para rodar como em produção (Linux/macOS), use o gunicorn:

```bash
gunicorn app:app --bind 0.0.0.0:5000
```

> O `gunicorn` não funciona no Windows; lá use `python app.py`.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Informações da API e lista de endpoints |
| GET | `/health` | Verificação de saúde (`{"status": "ok"}`) |
| POST | `/uploads/upload` | Envia um arquivo |
| GET | `/downloads/download/<filename>` | Baixa um arquivo enviado |

### `POST /uploads/upload`

- **Corpo:** `multipart/form-data` com o campo **`file`**.
- **Extensões permitidas:** `png`, `jpg`, `jpeg`, `gif`, `pdf`, `txt`.
- **Tamanho máximo:** 30 KB por arquivo (configurável, veja [Variáveis de ambiente](#variáveis-de-ambiente)).

| Código | Situação | Resposta |
|---|---|---|
| 200 | Sucesso | `{"mensagem": "Arquivo salvo com sucesso!", "arquivo": "nome.txt"}` |
| 400 | Campo `file` ausente | `{"erro": "Nenhum arquivo enviado"}` |
| 400 | Nome vazio | `{"erro": "Nome do arquivo vazio"}` |
| 400 | Extensão não permitida | `{"erro": "Tipo de arquivo não permitido!", "tipos_permitidos": [...]}` |
| 400 | Arquivo maior que o limite | `{"erro": "Arquivo excede o tamanho máximo permitido (30 KB)"}` |
| 409 | Já existe arquivo com esse nome | `{"erro": "Já existe um arquivo com esse nome"}` |
| 413 | Requisição acima de 1 MB | `{"erro": "Requisição muito grande"}` |

### `GET /downloads/download/<filename>`

| Código | Situação | Resposta |
|---|---|---|
| 200 | Arquivo encontrado | O arquivo, como anexo (download) |
| 404 | Arquivo não existe | `{"erro": "Arquivo não encontrado"}` |

## Exemplos de uso

Substitua `BASE` pela URL local (`http://127.0.0.1:5000`) ou pela URL do Render.

```bash
BASE=http://127.0.0.1:5000

# Status da API
curl $BASE/

# Upload
curl -F "file=@meu_arquivo.txt" $BASE/uploads/upload

# Download (salva com o nome original)
curl -OJ $BASE/downloads/download/meu_arquivo.txt

# Download de arquivo inexistente (404 em JSON)
curl -i $BASE/downloads/download/nao_existe.txt
```

**No Postman / Insomnia:** crie uma requisição `POST` para `/uploads/upload`, aba **Body → form-data**, chave `file` com o tipo **File** e selecione o arquivo.

## Variáveis de ambiente

Todas são opcionais.

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `5000` | Porta ao rodar com `python app.py` (o Render define sozinho) |
| `FLASK_DEBUG` | `0` | `1` liga o modo debug (**nunca use em produção**) |
| `MAX_FILE_SIZE_KB` | `30` | Tamanho máximo de cada arquivo, em KB |
| `DATA_DIR` | pasta do projeto | Onde ficam `uploads/`, `database.db` e `uploads.log` |
| `UPLOAD_FOLDER` | `$DATA_DIR/uploads` | Pasta dos arquivos enviados |
| `DATABASE_PATH` | `$DATA_DIR/database.db` | Caminho do banco SQLite |
| `LOG_FILE` | `$DATA_DIR/uploads.log` | Caminho do arquivo de log |

## Testes automatizados

Usam apenas a biblioteca padrão do Python (nenhuma instalação extra) e uma pasta temporária, sem afetar seus dados:

```bash
python -m unittest discover -v
```

Cobrem: upload e download, validações (extensão, tamanho, nome vazio), arquivo duplicado, 404/405/413 em JSON, `path traversal` e o registro no banco.

## Deploy no Render

### Opção A — Painel do Render (manual)

1. Envie o projeto para um repositório no **GitHub**.
2. No [Render](https://dashboard.render.com), clique em **New + → Web Service** e conecte o repositório.
3. Preencha:

   | Campo | Valor |
   |---|---|
   | Language / Runtime | `Python 3` |
   | Branch | `main` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60` |
   | Instance Type | `Free` |
   | Health Check Path (em *Advanced*) | `/health` |
   | Environment Variable | `PYTHON_VERSION` = `3.12.3` |

4. Clique em **Create Web Service** e aguarde o build. Ao terminar, o Render mostra a URL pública (`https://....onrender.com`).

### Opção B — Blueprint (`render.yaml`)

O arquivo `render.yaml` já está no repositório. No Render: **New + → Blueprint**, selecione o repositório e confirme.

### Testando o link público

```bash
curl https://SEU-SERVICO.onrender.com/health
curl -F "file=@teste.txt" https://SEU-SERVICO.onrender.com/uploads/upload
curl -OJ https://SEU-SERVICO.onrender.com/downloads/download/teste.txt
```

> No plano gratuito o serviço "dorme" após ~15 min sem acesso; a primeira requisição depois disso pode levar cerca de 1 minuto.

## Limitações conhecidas

- **Armazenamento efêmero no plano gratuito do Render:** o sistema de arquivos é apagado a cada novo deploy, reinício ou quando o serviço "acorda". Os arquivos enviados e o `database.db` **não são permanentes**. Para persistência, use um *Persistent Disk* do Render (plano pago) e aponte `DATA_DIR` para o ponto de montagem (ex.: `/var/data`), ou migre para um banco/armazenamento externo (PostgreSQL, S3).
- Não há autenticação: qualquer pessoa com a URL pode enviar e baixar arquivos.
- Não há rota de listagem nem de exclusão de arquivos (fora do escopo da atividade).

## Correções feitas no código original

| Problema | Correção |
|---|---|
| Upload sem `Content-Length` causava **erro 500** (`TypeError`) | O tamanho agora é medido no próprio arquivo, não pelo cabeçalho |
| Mensagem dizia "15 KB", mas o limite real era 30 KB | Mensagem e limite agora vêm da mesma configuração |
| Banco de dados nunca era usado (tabela sempre vazia) | O upload agora registra o arquivo e o download consulta o registro |
| Download inexistente devolvia **HTML**; o `except FileNotFoundError` nunca era acionado | Trata `NotFound` e responde JSON 404 |
| Chaves de erro inconsistentes (`error` / `erro`) | Padronizado para `erro` |
| Arquivo com mesmo nome era **sobrescrito** silenciosamente | Retorna `409 Conflict` |
| Extensão validada no nome original, mas salvo o nome "limpo" (ex.: `日本.txt` virava `txt`) | Valida o nome já sanitizado |
| `debug=True` expunha o código e um console remoto | Debug desligado por padrão |
| Caminhos relativos (`uploads`, `database.db`) | Caminhos absolutos e configuráveis |
| Sem servidor de produção, `requirements.txt` ou porta dinâmica | Adicionados gunicorn, `requirements.txt`, `render.yaml` e `PORT` |
| Logs só em arquivo (efêmero no Render) | Logs também no terminal (aba *Logs* do Render) |
