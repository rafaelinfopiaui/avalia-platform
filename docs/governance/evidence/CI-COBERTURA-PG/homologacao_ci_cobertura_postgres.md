---
id: "homologacao_ci_cobertura_postgres"
tema: "Melhoria de CI — cobertura real dos testes de concorrência PostgreSQL — homologação"
data: "2026-10-15 (America/Sao_Paulo)"
decisor: "Rafael"
pr: "#21"
branch: "ci/cobertura-postgres-concorrencia"
---

# Homologação — cobertura dos testes de concorrência PostgreSQL na CI

## Objeto

Step novo "Run PostgreSQL concurrency tests (real Postgres, not SQLite)"
no job `core` do `.github/workflows/ci.yml` (só adição), que executa os
10 testes `test_pg_*` de concorrência real contra bancos descartáveis
exclusivos no serviço PostgreSQL da CI, com guard anti-skip-silencioso.
Fecha a lacuna registrada em DEC-AV-041 e DEC-AV-043 (a CI rodava SQLite
e os `test_pg_*` ficavam SKIPPED).

## Base da homologação (conferência limitada, sem reauditoria)

- **HEAD homologado:** 15be6184b9ff61261834095250202be2501fe2ff (PR #21).
- **Diff restrito:** só `.github/workflows/ci.yml` (116 inserções, 0
  remoções) + governança; **nenhum** arquivo de produto ou de teste
  alterado; suíte SQLite preservada.
- **Checks do HEAD (run 38732325676):** Core API, AI Engine, Frontend —
  todos **success**.
- **Distinção explícita por banco (log literal):**
  - Step **SQLite** "Run core tests": `232 passed, 10 skipped` — os 10
    skipped são os `test_pg_*`, skip **esperado** nesse step.
  - Step **PostgreSQL** "Run PostgreSQL concurrency tests":
    `TOTAL {tests:10, failures:0, errors:0, skipped:0}`; guard "OK: 10
    casos de concorrência PostgreSQL executados e aprovados (0 skipped)";
    5 casos de exclusão de imagens + 5 de transcrição; 2 bancos
    descartáveis criados e dropados.
- **Sem bloqueantes:** PR mergeable=MERGEABLE, mergeState=CLEAN.

## Autoria real (preservada)

- **Hermes (orquestrador)** implementou o step e validou por execução
  local e remota.
- **Antigravity** (CLI `agy`, modelo "Gemini 3.8 Flash High" — família
  distinta) revisou o delta: APROVADO COM RESSALVAS; 2 achados de
  severidade BAIXA (defesa em profundidade) incorporados.
- **Claude Code** estava **indisponível** (sessão OAuth expirada); não foi
  o executor desta melhoria. Reautenticação permanece separada, para
  retomada futura. Nenhuma autenticação/credencial/provedor foi alterada.

## Decisão

Homologada a melhoria de CI de cobertura PostgreSQL. A lacuna remota está
**tecnicamente resolvida e comprovada por run real** (38731695435 e
38732325676). Integração autorizada por merge commit no PR #21,
preservando a branch.

## Limites preservados

- Não altera regras de produto; não amplia para migração geral da suíte.
- Bancos protegidos (`avalia_dev`, apresentação) jamais tocados — a CI usa
  só seu serviço postgres efêmero.
- Sem migração operacional, P5, OCR, remoção física, deploy ou baseline.
- Numerador **22/70** e **BL-AV-4B-05 parcial** preservados (esta melhoria
  é de infraestrutura de CI; não altera o numerador de critérios).
