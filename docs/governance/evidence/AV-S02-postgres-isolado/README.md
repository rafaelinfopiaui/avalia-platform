# Evidência reproduzível — Validação PostgreSQL isolado de BL-AV-1-10

Scripts usados na validação de idempotência de revisão humana em PostgreSQL genuinamente
isolado (2026-09-24), conforme exigência de Rafael de não aceitar apenas SQLite como prova.
Nenhum ambiente, banco ou credencial real está incluído aqui — apenas os scripts-fonte,
sanitizados, e o procedimento para reproduzir localmente.

**Nenhum destes scripts foi executado contra `avalia_dev` ou qualquer banco operacional.**

## Scripts

- `av_pg_http_flow.py` — fluxo HTTP completo (login, avaliação, questão, rubrica, publicação,
  resposta, correção, revisão) + teste de reenvio equivalente e decisão conflitante via
  `POST /v1/corrections/{job_id}/reviews`.
- `av_pg_concurrency.py` — 10 threads reais disparando a mesma decisão simultaneamente contra o
  mesmo job, validando que exatamente 1 `HumanReview` é persistida sob concorrência real.
- `av_pg_concurrency_conflict.py` — 6 threads reais com decisões alternadas (APPROVE/ALTER)
  contra o mesmo job, validando 409 para as conflitantes e persistência de 1 única linha final.

## Procedimento de reprodução (ambiente isolado e descartável, nunca operacional)

1. Provisionar um cluster PostgreSQL local temporário, nunca reutilizando um banco existente:
   ```
   initdb -D /tmp/av_pg_isolated -U postgres --auth=trust
   pg_ctl -D /tmp/av_pg_isolated -o "-p 55432 -k /tmp/av_pg_isolated" -l /tmp/av_pg_isolated/server.log start
   psql -h /tmp/av_pg_isolated -p 55432 -U postgres -c "CREATE DATABASE av_s02_migration_test;"
   ```
2. Aplicar as migrações do Core apontando `DATABASE_URL` para esse banco isolado (nunca para
   `avalia_dev`):
   ```
   export DATABASE_URL="postgresql+psycopg2://postgres@/av_s02_migration_test?host=/tmp/av_pg_isolated&port=55432"
   alembic upgrade head
   ```
3. Criar um usuário de teste fictício direto via ORM (não há endpoint público de registro):
   ```python
   from app.db import SessionLocal
   from app.models import User, Role
   from app.security import hash_password
   s = SessionLocal()
   s.add(User(email="revisor.pg@example.com", password_hash=hash_password("<defina uma senha de teste>"), role=Role.PROFESSOR))
   s.commit()
   ```
4. Subir a aplicação real contra esse banco isolado (Core + AI Engine em modo simulado):
   ```
   AI_ENGINE_MODE=simulated uvicorn app.main:app --host 127.0.0.1 --port 8011   # ai-engine
   DATABASE_URL=... JWT_SECRET=<qualquer valor de teste> AI_ENGINE_URL=http://127.0.0.1:8011 uvicorn app.main:app --host 127.0.0.1 --port 8010   # core
   ```
5. Exportar a senha de teste como variável de ambiente (nunca hardcoded) e rodar os scripts:
   ```
   export AV_TEST_PASSWORD="<a mesma senha de teste do passo 3>"
   python3 av_pg_http_flow.py
   python3 av_pg_concurrency.py
   python3 av_pg_concurrency_conflict.py
   ```
6. Ao final, encerrar e remover o cluster isolado:
   ```
   pg_ctl -D /tmp/av_pg_isolated stop
   rm -rf /tmp/av_pg_isolated
   ```

## Resultados observados nesta sprint (registrados em `sprint_AV-S02_ci_visual_isolamento_testes.md` §8.1 e snapshot `EXEC-2026-09-24-03`)

- Reenvio equivalente: 2ª submissão retorna a mesma `HumanReview` (mesmo `id`/`created_at`), sem duplicar.
- Decisão conflitante: retorna 409 preservando a decisão original.
- 10 threads concorrentes idênticas: 10×200, 1 única linha persistida.
- 6 threads concorrentes mistas: 3×200 + 3×409, 1 única linha final.

Todos os resultados foram confirmados por consulta SQL direta ao banco isolado, não apenas pelo
status HTTP retornado.
