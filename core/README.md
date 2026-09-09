# Core API — AvalIA

FastAPI + SQLAlchemy + Alembic + PostgreSQL. Ver `docs/arquitetura.md` e
`docs/contracts/openapi.yaml` na raiz do repositório para o contexto completo.

## Setup (macOS)

```bash
# Pré-requisitos: Postgres rodando (brew services start postgresql@16)
createdb avalia_dev   # se ainda não existir

cd core
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edite .env se necessário (JWT_SECRET, etc. — nunca commitar .env real)

alembic upgrade head
python -m app.seed        # popula professor + avaliação + respostas fictícias

uvicorn app.main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/v1/health`

## Setup (Windows com WSL2)

Dentro do WSL2 (Ubuntu), os passos são os mesmos do macOS/Linux acima.
Diferenças:
- Instale PostgreSQL dentro do WSL2 (`sudo apt install postgresql`) ou
  aponte `DATABASE_URL` para um Postgres rodando no Windows host
  (`host.docker.internal` não se aplica aqui; use o IP do host Windows
  visível a partir do WSL2, ou rode o Postgres dentro do próprio WSL2 —
  mais simples).
- Use `python3.11` do WSL2, não o Python do Windows.
- Ver `Manual_01_Windows_WSL2_AvalIA` (documento de treinamento da squad,
  fora do escopo desta implementação, mas útil como referência de ambiente).

## Login de demonstração (dados fictícios)

Após `python -m app.seed`:
- E-mail: valor de `SEED_PROFESSOR_EMAIL` no `.env` (padrão `professor@avalia.local`)
- Senha: valor de `SEED_PROFESSOR_PASSWORD` no `.env` (padrão de exemplo,
  **não usar em produção**)

## Testes

```bash
source .venv/bin/activate
env -u AI_ENGINE_URL -u DATABASE_URL -u JWT_SECRET pytest app/tests -q
```
(as variáveis são limpas explicitamente porque os testes usam SQLite em
memória e uma URL de AI Engine inexistente para simular indisponibilidade
de forma determinística; se seu shell já exportou essas variáveis para
outro propósito, isso evita conflito.)

8 testes cobrindo: acesso sem permissão bloqueado, rubrica com soma
incorreta rejeitada, publicação de avaliação válida, pontuação de critério
fora do limite rejeitada, AI Engine indisponível não fabrica resultado,
revisão humana persistida com autor, reprocessamento preserva versões
anteriores.

## Ambientes

`ENV=development|homolog|production` no `.env`. Somente `development` foi
executado e validado nesta entrega.
