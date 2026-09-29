---
id: "EXEC-2026-09-28-03"
tipo: execucao
sprint: "AV-S03"
gerado_em: "2026-09-28T16:07:16-03:00"
executor: "Codex"
status: parcial
commit_referencia: "66c95201daf893fa7b2852e0d94b20314f8d8f34"
---

# Snapshot EXEC-2026-09-28-03 — correções da segunda revisão Antigravity em BL-AV-2-03

> Registro histórico. Não promover automaticamente a baseline.

## 1. Abertura

- objetivo: corrigir os achados bloqueantes residuais A e B e a lacuna de cobertura C informados por Rafael após a segunda revisão cruzada independente e adversarial atribuída ao Antigravity;
- escopo autorizado: `core/app/routers/academic.py`, testes em `core/app/tests/test_academic_authorization.py` e registros obrigatórios desta fatia;
- fora de escopo: `avalia_dev`, stage, commit, push, tag, deploy e qualquer ação remota;
- branch/upstream/commit: `local/av-s03-recuperacao`, `origin/main`, `66c95201daf893fa7b2852e0d94b20314f8d8f34`;
- working tree inicial: mudanças locais preexistentes da AV-S03 em configuração, aplicação, modelos, schemas, contrato, migração, router, testes e registros anteriores;
- rastreabilidade: BL-AV-2-03; o documento `docs/governance/sprints/sprint_AV-S03_estrutura_academica.md` continua ausente deste worktree.

## 2. Entregas por achado

| Achado | Estado | Tratamento |
|---|---|---|
| A | implementado e validado localmente | `create_enrollment` passou a exigir primeiro o vínculo ativo `RESPONSIBLE`, antes de consultar `Student`; teste envia ID existente e inexistente como `COLLABORATOR` e confirma resposta idêntica (`403` e mesmo corpo) |
| B | implementado e validado localmente | `get_link` filtra `ProfessorClassLink.professor_id == user.id` antes de resolver o ID para professor; ID alheio e ausente colapsam no mesmo `404` e mesmo corpo; acessos do professor dono e do administrador continuam `200` |
| C | implementado e validado localmente | testes parametrizados isolam `settings.academic_module_enabled` com `monkeypatch`: avaliação sem turma retorna `201` com flag desligada e `422` ligada; criação com turma e vínculo ativo retorna `201` nos dois valores; mutação de avaliação já vinculada sem vínculo ativo retorna `403` nos dois valores |

## 3. Arquivos impactados nesta fatia

| Caminho | Natureza | Item |
|---|---|---|
| `core/app/routers/academic.py` | alterado | BL-AV-2-03; achados A e B |
| `core/app/tests/test_academic_authorization.py` | alterado | BL-AV-2-03; achados A, B e C |
| `docs/governance/snapshots/snapshot_EXEC-2026-09-28-03_BL-AV-2-03-segunda-revisao-antigravity.md` | criado | registro obrigatório |
| `docs/governance/snapshots/latest_execution.md` | alterado | registro obrigatório |
| `docs/governance/executive_technical_dashboard.md` | alterado | registro obrigatório |

## 4. Validações executadas

| Data/fuso | Item | Comando | Ambiente | Tipo | Resultado real |
|---|---|---|---|---|---|
| 2026-09-28 -03 | BL-AV-2-03 | `ruff check app/` | venv local do Core | automatizada | `All checks passed!` |
| 2026-09-28 -03 | BL-AV-2-03 | `python -m pytest app/tests/test_academic_authorization.py -q` | FastAPI `TestClient`; SQLite temporário | integração HTTP automatizada | **20 passed, 0 failed**, 12 warnings, 8.53 s |
| 2026-09-28 -03 | regressão Core | `ruff check app/ && python -m pytest app/tests -q` | venv local; FastAPI `TestClient`; SQLite temporário | automatizada | Ruff limpo; **68 passed, 0 failed**, 12 warnings, 36.49 s |
| 2026-09-28 -03 | integridade do diff | `git diff --check` | worktree local | automatizada | sem erros |

## 5. Estado final e limites

- `avalia_dev`: não acessado nem alterado; testes usaram bancos SQLite temporários;
- stage/commit/push/tag/deploy/ação remota: não realizados;
- README, requisitos/PRD e roadmap: revisados quanto ao escopo desta correção; sem alteração necessária;
- status: achados A, B e C implementados e validados localmente; AV-S03 permanece local, parcial e não homologada;
- revisão independente: os achados de origem foram atribuídos por Rafael ao Antigravity; esta execução não realizou nova revisão independente;
- baseline: não promovido; permanece sem baseline validado sob a governança.
