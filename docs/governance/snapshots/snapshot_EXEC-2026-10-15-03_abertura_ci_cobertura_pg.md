---
id: "EXEC-2026-10-15-03"
tipo: execucao
sprint: "Melhoria de CI — cobertura real dos testes de concorrência PostgreSQL"
gerado_em: "2026-10-15T09:10:00-03:00"
executor: "Hermes (orquestrador) + Claude Code (implementação) + Antigravity (revisão de delta)"
status: "ABERTURA — planejamento + implementação LOCAL autorizados; sem publicação"
base: "main cde87cc74f37dfca6136a1c8eeeb5489318045e2"
branch: "ci/cobertura-postgres-concorrencia"
---

# Snapshot EXEC-2026-10-15-03 — abertura: cobertura PostgreSQL na CI

Rafael autorizou planejamento e implementação **LOCAL** de uma melhoria
que acrescenta a execução dos testes de concorrência PostgreSQL já
existentes à CI, sem publicação nesta rodada.

- **Lacuna de origem:** a CI roda SQLite; os 10 casos `test_pg_*`
  (`@requires_postgres`) ficam skipped (ver `DEC-AV-041`/`DEC-AV-043`).
- **Escopo/ACD:** `evidence/CI-COBERTURA-PG/escopo_ci_cobertura_postgres.md`.
- **Estado de partida reconfirmado:** `main` local == remoto ==
  `cde87cc74f37dfca6136a1c8eeeb5489318045e2`; working tree limpo; bancos
  protegidos intactos (`avalia_dev` em `a9f4c2e71b06`).
- **Branch dedicada:** `ci/cobertura-postgres-concorrencia` (checkout
  principal, sem worktree).

## Limite preservado
Esta rodada NÃO publica. A execução remota real no GitHub Actions só é
comprovável por uma run real (dependente de publicação futura
autorizada). A lacuna remota NÃO será declarada resolvida até isso.
Numerador **22/70**; `BL-AV-4B-05` permanece **parcial**. Sem
stage/commit/push/merge, bancos protegidos, migração operacional, P5,
OCR, remoção física, deploy ou baseline nesta rodada.
