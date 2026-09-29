---
id: "EXEC-2026-09-28-02"
tipo: execucao
sprint: "AV-S03"
gerado_em: "2026-09-28T15:51:55-03:00"
executor: "Codex"
status: parcial
commit_referencia: "66c95201daf893fa7b2852e0d94b20314f8d8f34"
---

# Snapshot EXEC-2026-09-28-02 — correções da revisão Antigravity em BL-AV-2-03

> Registro histórico. Não promover automaticamente a baseline.

## 1. Abertura

- objetivo: corrigir os achados bloqueantes 1, 2, 2b e 3 da revisão cruzada independente e adversarial informada por Rafael, e decidir o tratamento seguro do achado 2c;
- escopo autorizado: autorização acadêmica em `core/app/routers/academic.py` e `core/app/main.py`, testes `TestClient` em `core/app/tests/test_academic_authorization.py` e registros obrigatórios;
- fora de escopo: `avalia_dev`, stage, commit, push, tag, deploy e qualquer ação remota;
- branch/upstream/commit: `local/av-s03-recuperacao`, `origin/main`, `66c95201daf893fa7b2852e0d94b20314f8d8f34`;
- working tree inicial: mudanças locais preexistentes da AV-S03 em configuração, aplicação, modelos, schemas, contrato, migração, router, testes e registros da execução anterior;
- lacuna documental: `docs/governance/sprints/sprint_AV-S03_estrutura_academica.md` não existe neste worktree. A busca nas fontes locais não encontrou decisão explícita da seção 5.1 sobre avaliação legada sem turma.

## 2. Entregas por achado

| Achado | Estado | Tratamento |
|---|---|---|
| 1 | implementado e validado localmente | consultas de leitura/mutação passaram a filtrar por escopo antes de decidir existência; recurso ausente e recurso fora do escopo retornam o mesmo `404`; acesso global de administrador foi preservado |
| 2 | implementado e validado localmente | `POST /v1/answers`, `POST /v1/answers/{id}/corrections` e `POST /v1/corrections/{id}/reviews` agora chamam `require_assessment_mutation` |
| 2b | implementado e validado localmente | reatribuição exige autorização de mutação sobre a turma atual, quando houver, antes de validar a nova turma |
| 2c | comportamento seguro confirmado; sem alteração de código | na ausência da decisão explícita solicitada, manteve-se bypass somente para avaliações sem turma; avaliações com `class_group_id` exigem vínculo ativo mesmo com `academic_module_enabled=false` |
| 3 | implementado e validado localmente | testes `TestClient` cobrem colaborador (403), duas rotas sem autenticação (401), anti-oráculo em turma e matrícula (404/404), três escritas com vínculo expirado (403) e reatribuição com vínculo atual expirado (403) |

## 3. Arquivos impactados nesta fatia

| Caminho | Natureza | Item |
|---|---|---|
| `core/app/routers/academic.py` | alterado | BL-AV-2-03; achados 1 e 2b |
| `core/app/main.py` | alterado | BL-AV-2-03; achado 2 |
| `core/app/tests/test_academic_authorization.py` | alterado | BL-AV-2-03; achado 3 |
| `docs/governance/snapshots/snapshot_EXEC-2026-09-28-02_BL-AV-2-03-revisao-antigravity.md` | criado | registro obrigatório |
| `docs/governance/snapshots/latest_execution.md` | alterado | registro obrigatório |
| `docs/governance/executive_technical_dashboard.md` | alterado | registro obrigatório |

## 4. Validações executadas

| Data/fuso | Item | Comando | Ambiente | Tipo | Resultado real |
|---|---|---|---|---|---|
| 2026-09-28 -03 | BL-AV-2-03 | `ruff check app/` | venv local do Core | automatizada | `All checks passed!` |
| 2026-09-28 -03 | BL-AV-2-03 | `python -m pytest app/tests/test_academic_authorization.py -q` | FastAPI `TestClient`; SQLite temporário | integração HTTP automatizada | **13 passed, 0 failed**, 12 warnings, 4.83 s |
| 2026-09-28 -03 | regressão Core | `python -m pytest app/tests -q` | FastAPI `TestClient`; SQLite temporário | automatizada | **61 passed, 0 failed**, 12 warnings, 34.01 s |
| 2026-09-28 -03 | integridade do diff | `git diff --check` | worktree local | automatizada | sem erros |

## 5. Estado final e limites

- `avalia_dev`: não acessado nem alterado;
- stage/commit/push/tag/deploy/ação remota: não realizados;
- README, requisitos/PRD e roadmap: revisados quanto ao escopo desta correção; sem alteração necessária;
- status: achados solicitados implementados e validados localmente; AV-S03 permanece local, parcial e não homologada;
- revisão independente: o achado de origem foi atribuído por Rafael ao Antigravity; esta execução não realizou nova revisão independente;
- baseline: não promovido; permanece sem baseline validado sob a governança.

