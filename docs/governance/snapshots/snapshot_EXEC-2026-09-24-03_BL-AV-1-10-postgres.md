---
id: EXEC-2026-09-24-03
tipo: execucao
sprint: AV-S02
gerado_em: "2026-09-24T08:15:00-03:00"
executor: "Hermes"
status: implementada_validada_localmente
commit_referencia: 0be691e12e9d5d6f3ffc989237739f6559d8dacd
---

# Snapshot EXEC-2026-09-24-03 — migração sem deduplicação automática + validação em PostgreSQL isolado

> Registro histórico. Não promove baseline nem homologa o resultado.

## 1. Abertura

- objetivo: atender aos 4 encaminhamentos de Rafael sobre a AV-S02: (1) reescrever a migração de `BL-AV-1-10` para NÃO deduplicar automaticamente, apenas detectar e abortar; (2) validar em PostgreSQL isolado (não apenas SQLite); (3) submeter a mudança a revisão por agente distinto do autor; (4) preparar pacote Git (arquivos/diffs exatos, sem pedir nova autorização para a preparação);
- escopo: `core/alembic/versions/7b1d6d853f20_add_unique_human_review_job_id.py` (reescrita completa), validação em Postgres isolado, revisão independente, proposta separada de saneamento de duplicatas, auditoria de banco por evidência, atualização de sprint/backlog/débitos/dashboard, preparo de pacote Git;
- fora de escopo: aplicação da migração ao `avalia_dev` operacional, saneamento de duplicatas legadas, commit/push/tag/deploy, início de outra sprint;
- Git: `main`, HEAD/upstream `0be691e12e9d5d6f3ffc989237739f6559d8dacd`; working tree seguiu suja com as mudanças preexistentes de AV-S01/AV-S02, preservadas;
- baseline: nenhum promovido.

## 2. Entregas

| Item | Estado | Entrega |
|---|---|---|
| Migração sem deduplicação automática | validado localmente (SQLite + PostgreSQL isolado) | `upgrade()` detecta duplicatas por `job_id` (SQL portável SQLite/Postgres) e levanta `RuntimeError` com diagnóstico (job_id/contagem/ids) sem tocar em nenhum dado; só cria a `UniqueConstraint` quando não há duplicatas |
| Validação em PostgreSQL isolado | concluída | cluster PostgreSQL 16 provisionado via `initdb`/`pg_ctl` em `/tmp/av_pg_isolated` (porta 55432), nunca `avalia_dev`; migração testada com e sem duplicatas; aplicação real (`uvicorn`) exercitada via HTTP: reenvio equivalente, decisão conflitante, 10 threads concorrentes idênticas (1 revisão final) e 6 threads concorrentes mistas APPROVE/ALTER (3×200+3×409, 1 revisão final) |
| Revisão por agente distinto do autor | concluída (Claude Code); tentativa adicional (Antigravity CLI) sem resultado | Claude Code (`claude-sonnet-5`, `firstParty`, CLI `2.1.260`) leu o arquivo linha a linha e reexecutou os mesmos testes em cluster PostgreSQL e SQLite próprios; parecer **aprovado incondicionalmente**. Segunda tentativa de verificação por Antigravity CLI foi aberta em paralelo, mas travou por ~20 minutos sem progresso ("localização do arquivo") e foi interrompida por Hermes; registrada como tentativa sem resultado, não como aprovação adicional |
| Proposta de saneamento (não executada) | preparada, dependente de aprovação | `docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md`: diferencia duplicatas equivalentes de conflitantes; exige backup completo + export da tabela; propõe mover (não apagar) linhas excedentes para tabela de arquivo `human_reviews_superseded`; nenhuma ação executada |
| Auditoria de banco por evidência | concluída | tabela na sprint (§8.1): identifica que a validação visual pós-fix (AC-04/AC-10) usou `avalia_dev` real mas não isolado, distinto da validação de migração/concorrência desta fatia (Postgres genuinamente isolado) |
| Origem do aviso de fallback | registrada como NÃO CONFIRMADA | ausência do aviso textual nos logs de sessão e compatibilidade com uma hipótese não constituem prova da camada onde ocorreu; separado da execução comprovada do Claude Code nesta fatia |

## 3. Arquivos impactados nesta fatia

- `core/alembic/versions/7b1d6d853f20_add_unique_human_review_job_id.py` (reescrita completa, autor Hermes);
- `docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md` (novo);
- `docs/governance/sprints/sprint_AV-S02_ci_visual_isolamento_testes.md` (§8.1 nova, AC-09 atualizado, seção de migração reescrita, DoD/A1/B5 atualizados, resultado consolidado atualizado);
- `docs/governance/backlog/backlog_tecnico_avalia.md` (`BL-AV-1-10` com estado detalhado);
- `docs/governance/registers/technical_debts.md` (`DEBT-AV-011` atualizado; `DEBT-AV-004`/`DEBT-AV-005` reconciliados ao estado real do lint/CI local);
- `docs/governance/executive_technical_dashboard.md` e `docs/governance/snapshots/` (este snapshot).

README, requisitos/PRD e roadmap foram revisados; nenhuma alteração adicional necessária. Frontend, AI Engine e workflow CI não foram tocados nesta fatia (já corrigidos/validados na fatia anterior, `EXEC-2026-09-24-02` e antes).

## 4. Validações reais

Ambiente: macOS local, Core `.venv`, SQLite descartável e PostgreSQL 16 isolado (`initdb`/`pg_ctl`, `/tmp/av_pg_isolated`, porta 55432), America/Sao_Paulo. `avalia_dev` nunca acessado em escrita.

| Data/fuso | Comando/procedimento | Tipo | Resultado real |
|---|---|---|---|
| 2026-09-24 ~07:50 -03 | `alembic upgrade head` em SQLite temporário sem duplicatas | automatizada/migração isolada | exit 0; constraint criada |
| 2026-09-24 ~07:52 -03 | `alembic upgrade head` em SQLite temporário com 3 duplicatas fictícias inseridas manualmente | automatizada/migração isolada | `RuntimeError` com diagnóstico; 3 linhas intactas; `alembic_version` não avançou; constraint não criada |
| 2026-09-24 ~07:55 -03 | `initdb`/`pg_ctl start` de PostgreSQL 16 isolado, porta 55432 | preparação de ambiente | exit 0; servidor confirmado via `select version()` |
| 2026-09-24 ~07:57 -03 | `alembic upgrade head` em Postgres isolado, banco sem duplicatas | automatizada/migração isolada | exit 0; constraint `uq_human_reviews_job_id` confirmada via `\d human_reviews` |
| 2026-09-24 ~07:58 -03 | inserção manual de 3 duplicatas fictícias em banco Postgres isolado separado + `alembic upgrade head` | automatizada/migração isolada | `RuntimeError` com diagnóstico idêntico ao SQLite; 3 linhas intactas; `alembic_version` permaneceu em `e1b02279b1a5`; constraint não criada |
| 2026-09-24 ~08:00 -03 | `uvicorn` real (Core + AI Engine simulado) contra Postgres isolado; HTTP real: login, criação de avaliação/questão/rubrica, publicação, resposta, correção, 2 submissões de revisão equivalentes, 1 submissão conflitante, leitura do contexto | integração real | 1ª/2ª submissão: 200, mesmo `id`/`created_at`; submissão conflitante: 409 preservando original; contexto expõe `human_review` completo; 1 única linha no banco |
| 2026-09-24 ~08:01 -03 | 10 threads reais (`threading`) disparando a mesma decisão simultaneamente contra o mesmo job, via `httpx` | integração real/concorrência | 10×200, mesmo `id` em todas; 1 única linha no banco; log da aplicação `human_review_registered` ocorreu 1 vez |
| 2026-09-24 ~08:02 -03 | 6 threads reais com decisões alternadas (APPROVE/ALTER) contra o mesmo job novo | integração real/concorrência | 3×200 (equivalentes) + 3×409 (conflitantes); 1 única linha final no banco (APPROVE) |
| 2026-09-24 ~08:05 -03 | Revisão independente por Claude Code: leitura linha a linha + reexecução própria dos testes de migração em SQLite e em cluster PostgreSQL criado por ele mesmo | inspeção de código + automatizada | parecer "aprovado incondicionalmente"; nenhum caminho de perda de dados identificado |
| 2026-09-24 ~08:10 -03 | tentativa de segunda revisão independente por Antigravity CLI | tentativa sem resultado | processo travado ~20 min em "localização do arquivo"; interrompido por Hermes sem produzir parecer |
| 2026-09-24 ~08:20 -03 | `env -u AI_ENGINE_URL -u DATABASE_URL -u JWT_SECRET .venv/bin/pytest app/tests -q` (SQLite, suíte completa) | automatizada | exit 0; 42 passed, 13 warnings |
| 2026-09-24 ~08:21 -03 | `.venv/bin/ruff check --config ../ruff.toml app` (Core) | automatizada/lint | exit 0; `All checks passed!` |
| 2026-09-24 ~08:22 -03 | `git diff --check` (raiz) | automatizada/estática | exit 0, sem saída |
| 2026-09-24 ~08:23 -03 | `SELECT COUNT(*) FROM human_reviews` em `avalia_dev` antes/depois de toda a sessão | verificação de integridade | 8 linhas antes e depois — nenhuma alteração no banco operacional |
| 2026-09-24 ~08:25 -03 | `pg_ctl stop` + remoção de `/tmp/av_pg_isolated` | limpeza de ambiente | cluster isolado encerrado e removido |

## 5. Limites e estado final

- `avalia_dev`: não migrado; contagem de `human_reviews` idêntica (8) antes e depois desta fatia — as 3 duplicatas legadas do job `4f56a10b-...` permanecem intactas e não tratadas;
- migração: agora comprovadamente incapaz de apagar/alterar/escolher dados, validada em SQLite e em PostgreSQL genuinamente isolado, nos dois casos com e sem duplicatas;
- revisão independente: obtida de Claude Code (agente distinto do autor Hermes), com testes empíricos próprios; segunda tentativa (Antigravity CLI) não produziu resultado;
- saneamento de duplicatas: proposta apresentada, não executada, dependente de aprovação explícita de Rafael;
- origem do aviso de fallback: registrada como não confirmada, não decidida por inferência;
- pacote Git: relação de arquivos e diffs exatos apresentados na resposta a Rafael desta fatia (não duplicados neste snapshot para evitar divergência de fonte única);
- homologação: pendente de Rafael;
- Git/remoto: nenhum commit, push, tag, deploy ou ação remota;
- status: implementada e validada localmente (incluindo PostgreSQL isolado); CI remota e homologação geral de AV-S02 continuam pendentes; nenhuma outra sprint iniciada.
