# Pacote de revisão para publicação — AV-S01 + AV-S02 consolidadas

Status: **PROPOSTA PARA REVISÃO. Nenhum `git add`, `commit`, `push`, `tag`, `deploy`, migração
operacional ou promoção de baseline foi executado.** Este documento e os arquivos irmãos em
`docs/governance/evidence/AV-S02-review-package/` existem apenas para você revisar antes de
autorizar a etapa remota.

Commit de referência (HEAD, inalterado durante toda a trilha): `0be691e12e9d5d6f3ffc989237739f6559d8dacd` (branch `main`).

Destino proposto (apenas registrado, não criado): branch `feat/av-s01-s02-consolidacao`, com Pull
Request para `main`, sem merge automático.

## Organização adotada (conforme sua instrução)

Os 4 commits propostos abaixo agrupam por **finalidade integrada**, não por sprint isolada — várias
mudanças de AV-S01 e AV-S02 tocam os mesmos arquivos (ex.: `core/app/main.py`,
`frontend/src/pages/ReviewPage.tsx`), e separar por sprint geraria commits incompletos (código que
não compila/não passa testes isoladamente). Cada commit abaixo relaciona explicitamente quais itens
e sprints ele contempla.

1. **Commit 1 — Funcionalidades integradas AV-S01 + AV-S02** (contratos, migração, frontend, testes) — 16 arquivos
2. **Commit 2 — Isolamento dos testes do AI Engine + configuração/ajustes de lint** (depende do commit 1 só por ordem cronológica de arquivo, não por conteúdo — pode ser reordenado se preferir) — 23 arquivos
3. **Commit 3 — Workflow de CI** (depende dos commits 1 e 2, pois referencia comandos/lint que eles introduzem) — 1 arquivo
4. **Commit 4 — Governança e evidências** (documenta e referencia os 3 commits anteriores; deveria vir por último para descrever um estado já consistente) — 72 arquivos

`docs/roteiro-apresentacao-supervisor.md` foi deliberadamente excluído de todos os 4 commits,
conforme sua instrução — permanece como arquivo não rastreado (`??`), fora deste pacote.

---

## Commit 1 — Funcionalidades integradas AV-S01 + AV-S02

**Itens/sprints contemplados:**
- `AV-S01`: autorização por vínculo (4 rotas), endpoint de contexto `GET /v1/correction-jobs/{id}/context`, retomada via API no frontend, suíte de regressão (`test_authorization_boundaries.py`), correção do `SessionGuard` para preservar querystring no redirect pós-login.
- `AV-S02` / `BL-AV-1-10`: política de decisão humana única por `CorrectionJob` — migração com detecção de duplicatas (sem deduplicação automática, corrigida em 2026-09-24 por exigência de Rafael), reenvio equivalente, conflito 409, contrato OpenAPI atualizado, UI em modo somente leitura quando já há decisão.

**Inventário (16 arquivos: 12 modificados + 4 novos):**

Modificados (tracked):
- `README.md`
- `core/README.md`
- `core/app/main.py`
- `core/app/models.py`
- `core/app/schemas.py`
- `docs/contracts/openapi.yaml`
- `core/app/tests/conftest.py`
- `core/app/tests/test_core_flow.py`
- `frontend/src/App.tsx`
- `frontend/src/pages/ReviewPage.tsx`
- `frontend/src/services/api.ts`
- `frontend/src/types.ts`

Novos:
- `core/alembic/versions/7b1d6d853f20_add_unique_human_review_job_id.py`
- `core/app/tests/test_review_idempotency.py`
- `core/app/tests/test_authorization_boundaries.py`
- `AGENTS.md`

**Diffs completos:** ver `docs/governance/evidence/AV-S02-review-package/commit1_tracked.diff`
(arquivos modificados) e `commit1_new_files.diff` (arquivos novos, formato diff contra `/dev/null`).

**Dependências:** nenhuma dependência de outro commit deste pacote. É a base funcional sobre a
qual os commits 2 e 3 constroem verificação (lint/CI).

**Testes/evidências relacionadas:** Core 42/42 (`pytest app/tests -q`); validação em PostgreSQL
16 isolado e descartável para a migração e para idempotência sob concorrência real (ver
`docs/governance/evidence/AV-S02-postgres-isolado/`); revisão independente da migração por Claude
Code (aprovado incondicionalmente); revalidação visual real pós-fix (Chrome via CDP, screenshots
em `docs/governance/evidence/AV-S02-final/`).

---

## Commit 2 — Isolamento dos testes do AI Engine + lint

**Itens/sprints contemplados:**
- `AV-S02` / `BL-AV-1-09`: isolamento de 2 testes do caminho real de reparo de JSON da variável
  global `AI_ENGINE_MODE` (`ai-engine/tests/test_schema_repair_and_fallback.py`), **incluído
  explicitamente nesta relação conforme sua instrução** — estava ausente da relação anterior.
- `AV-S02` / item 3 da sua instrução original: lint mínimo e explícito, Ruff (Python, Core + AI
  Engine) e ESLint (frontend), com as correções mecânicas reais que o lint apontou (reordenação de
  imports, 1 variável não usada, quebras de linha).

**Inventário (23 arquivos: 20 modificados + 3 novos):**

Modificados (tracked):
- `ai-engine/tests/test_schema_repair_and_fallback.py` — **correção funcional de BL-AV-1-09** (2 linhas de `monkeypatch.setattr(settings, "ai_engine_mode", "real")`)
- `ai-engine/app/cascade.py`
- `ai-engine/app/confidence.py`
- `ai-engine/app/config.py`
- `ai-engine/app/main.py`
- `ai-engine/app/ollama_client.py`
- `ai-engine/app/prompts/__init__.py`
- `ai-engine/app/prompts/prompt_v1.py`
- `ai-engine/app/rules.py`
- `ai-engine/app/schemas.py`
- `core/app/config.py`
- `core/app/db.py`
- `core/app/deps.py`
- `core/app/logging_utils.py`
- `core/app/security.py`
- `core/app/services/correction.py`
- `core/app/seed.py`
- `core/requirements-dev.txt`
- `frontend/package.json`
- `frontend/package-lock.json`

Novos:
- `ruff.toml`
- `ai-engine/requirements-dev.txt`
- `frontend/eslint.config.js`

**Diffs completos:** `docs/governance/evidence/AV-S02-review-package/commit2_tracked.diff` e
`commit2_new_files.diff`.

**Dependências:** nenhuma dependência de conteúdo do commit 1 (arquivos diferentes, exceto
`test_schema_repair_and_fallback.py`, que é isolado do que o commit 1 toca). O motivo de vir depois
do commit 1 na ordenação é apenas narrativo (funcionalidade antes de qualidade/verificação), não
uma dependência técnica real — poderia ser reordenado com Rafael sem quebrar nada.

**Justificativa das ferramentas/regras de lint** (para constar, já registrado na sprint):
- Ruff, regras `E`/`F`/`I` (pycodestyle errors, pyflakes, isort), `line-length=120`. Escolhido por
  ser rápido e padrão de mercado atual; conjunto mínimo deliberado para não gerar reformatação
  ampla.
- ESLint `^10.11.0` (flat config, formato mantido desde a série 9) + `typescript-eslint` `^8.70.1`
  (recomendado, não "strict") + `eslint-plugin-react-hooks` `^7.1.1` (regra `exhaustive-deps` como
  warning, não error) + `eslint-plugin-react-refresh` `^0.5.7`. Versões confirmadas por leitura
  direta de `frontend/package.json`/`package-lock.json`. Escolhido por
  ser o padrão atual para projetos Vite+React+TS.
- Nenhuma regra de formatação (aspas, ponto-e-vírgula, indentação) foi habilitada — isso é escopo
  de formatter, não de lint, e evitaria reformatação ampla não solicitada.

**Testes/evidências relacionadas:** `ruff check` limpo em Core e AI Engine (nos dois modos de
invocação usados pela CI); `npm run lint` limpo; `npm run build` limpo; suítes Core/AI Engine
(padrão e `AI_ENGINE_MODE=simulated` global) 100% verdes após as correções mecânicas do lint.

---

## Commit 3 — Workflow de CI

**Itens/sprints contemplados:**
- `AV-S02` / `BL-AV-1-06`: workflow mínimo de CI (`DEBT-AV-005`).

**Inventário (1 arquivo, novo):**
- `.github/workflows/ci.yml`

**Diffs completos:** `docs/governance/evidence/AV-S02-review-package/commit3_ci.diff`.

**Dependências:** depende do conteúdo dos commits 1 e 2 — o workflow executa `pytest`
(commit 1), `ruff check` e `npm run lint` (commit 2). Sem esses dois commits antes, os jobs do
workflow falhariam por ausência de configuração/dependências. Por isso vem depois na ordenação,
com dependência técnica real, não apenas narrativa.

**Gatilhos do workflow (`on:`):** `push` e `pull_request` para a branch `main` (conforme YAML —
ver arquivo completo para os gatilhos exatos configurados).

**Jobs / checks esperados no GitHub Actions:**
1. **`core`** — Python 3.11, serviço `postgres:16` disponível (não exercitado pelos testes atuais,
   que usam SQLite — registrado como observação, não bloqueante), `pip install -r requirements.txt
   -r requirements-dev.txt`, `ruff check --config ../ruff.toml app`, depois
   `pytest app/tests -q`.
2. **`ai-engine`** — Python 3.11, `pip install`, `ruff check`, depois `pytest -q` em dois passos
   nomeados: ambiente padrão e `AI_ENGINE_MODE=simulated` global.
3. **`frontend`** — Node, `npm ci`, `npm run lint`, `npm run build`.

Nenhum job de deploy, release, publish ou uso de segredo de produção está presente — confirmado por
leitura direta do YAML e por execução local de cada comando individualmente (ver commit 2).

**Status declarado:** `DEBT-AV-005` permanece **aberto** até a execução remota real no GitHub
Actions (validação local não substitui execução remota, conforme sua instrução prévia).

---

## Commit 4 — Governança e evidências

**Itens/sprints contemplados:** toda a documentação de governança acumulada (GOV-001 a GOV-005,
AV-S01, AV-S02), incluindo esta fatia de ajustes (migração sem deduplicação automática, validação
em PostgreSQL isolado, proposta de saneamento, pacote de revisão atual).

**Inventário:** árvore completa de `docs/governance/` — 72 arquivos (recontados por `find` no
momento deste ajuste, incluindo o próprio pacote de revisão e o snapshot desta fatia), listados
integralmente em `docs/governance/evidence/AV-S02-review-package/commit4_governance_files.txt`
(lista gerada por comando real `find`, não digitada manualmente). Inclui:
- políticas, templates, registros (`decisions.md`, `technical_debts.md`, `blockers.md`);
- sprints (`sprint_AV-S01...md`, `sprint_AV-S02...md`, `sprint_GOV-...md`);
- backlog (`backlog_tecnico_avalia.md`, `proposta_saneamento_human_reviews_duplicadas.md` — proposta, não execução);
- snapshots (todos, incluindo o desta fatia, `EXEC-2026-09-24-03`);
- `executive_technical_dashboard.md`;
- `evidence/` — 19 capturas de tela (AV-S01, AV-S02, AV-S02-final) + `evidence/AV-S02-postgres-isolado/`
  (scripts sanitizados de reprodução da validação em PostgreSQL isolado, criados nesta fatia).

**Excluído deste commit e de todos os outros:** `docs/roteiro-apresentacao-supervisor.md`, por sua
instrução explícita.

**Diffs completos:** `docs/governance/evidence/AV-S02-review-package/commit4_governance_new_files.diff`
(todos os arquivos são novos/untracked; PNGs aparecem corretamente marcados como `Binary files ...
differ`, sem conteúdo textual reproduzido).

**Dependências:** referencia os 3 commits anteriores (cita seus arquivos, resultados de teste e
diffs) — por isso deve vir por último, para descrever um estado já consistente. Não há dependência
de build/execução, apenas narrativa/documental.

---

## Confirmação de ausência de segredos e artefatos temporários

- Nenhum arquivo de `.env` real está incluído em nenhum dos 4 commits (`.env` permanece fora do
  controle de versão, como já era antes desta sessão).
- `frontend/package-lock.json`: inspecionado o diff completo — as únicas ocorrências de "token"
  são o nome do pacote npm `js-tokens` (falso positivo), sem credenciais reais.
- Scripts de evidência da validação PostgreSQL (`docs/governance/evidence/AV-S02-postgres-isolado/*.py`):
  a senha de teste fictícia foi removida do código-fonte e substituída por
  `os.environ["AV_TEST_PASSWORD"]`, lida em runtime, nunca hardcoded no arquivo.
- Nenhum diretório `/tmp`, arquivo `.db` temporário, cache de venv, `node_modules/` ou processo em
  execução está incluído em qualquer commit — todos os artefatos temporários usados nesta sessão
  (`/tmp/av_pg_isolated`, `/tmp/*.db`, servidores `uvicorn`) foram encerrados e removidos antes
  deste pacote ser preparado.
- Migração operacional: **não aplicada** a `avalia_dev` em nenhum momento; `SELECT COUNT(*) FROM
  human_reviews` permanece em 8 linhas, idêntico ao estado anterior a toda esta fatia.

## Localização dos scripts e evidências reproduzíveis dos testes PostgreSQL

`docs/governance/evidence/AV-S02-postgres-isolado/`:
- `README.md` — procedimento completo de reprodução (provisionar cluster isolado, aplicar
  migração, subir aplicação real, executar os 3 scripts, encerrar e remover o cluster).
- `av_pg_http_flow.py` — reenvio equivalente + decisão conflitante via HTTP real.
- `av_pg_concurrency.py` — 10 threads reais, mesma decisão, valida 1 única `HumanReview` persistida.
- `av_pg_concurrency_conflict.py` — 6 threads reais, decisões alternadas, valida 3×200/3×409 e 1
  linha final.

Nenhum desses scripts inclui ambiente, banco ou credencial real — todos operam contra um cluster
PostgreSQL temporário e descartável, criado e destruído pelo próprio procedimento documentado.

## O que este pacote NÃO faz

- Não executa `git add`, `commit`, `push`, `tag` ou `deploy`.
- Não cria a branch `feat/av-s01-s02-consolidacao` — apenas a registra como destino proposto.
- Não aplica a migração `7b1d6d853f20` a `avalia_dev`.
- Não autoriza nem executa o saneamento de duplicatas (`proposta_saneamento_human_reviews_duplicadas.md`
  continua não autorizado).
- Não promove baseline nem inicia outra sprint.
- Não homologa o fechamento de `AV-S02`.
