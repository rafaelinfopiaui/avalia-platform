---
id: GOV-002
tipo: implantacao-documental
status: concluida_aguardando_homologacao
abertura: "2026-09-21"
responsavel_consolidacao: Hermes
homologacao: pendente_Rafael
depende_de: GOV-001
---

# GOV-002 — Backlog e trilha de evolução "Operação de uma turma"

> Execução exclusivamente documental. Não implementa, não instala dependência, não altera serviço, não executa migração, não publica mudança.

## 1. Objetivo

Transformar a proposta de trilha recebida de Rafael em backlog técnico rastreável e documento de trilha, preparando — mas não aprovando — o planejamento de sprints futuras sob a governança instituída em GOV-001.

## 2. Escopo autorizado

- criar/atualizar backlog técnico canônico, documento de trilha, proposta de divisão em sprints, registros de débitos/bloqueantes/decisões e o dashboard;
- reconciliar com o backlog anterior sem apagar itens omitidos;
- registrar itens de investigação a partir de leitura estática de código, sem afirmar reprodução em runtime;
- não implementar, não instalar dependência, não alterar serviço, não migrar banco, não fazer deploy/commit/push/tag.

## 3. Artefatos previstos

1. `docs/governance/backlog/backlog_tecnico_avalia.md` — backlog canônico com 47 itens (`BL-AV-*`);
2. `docs/governance/backlog/trilha_operacao_de_turma.md` — objetivo, marcos, sequência, entregas, critérios de entrada/saída, atividades antecipáveis, decisões e itens fora da trilha;
3. `docs/governance/backlog/proposta_sprints_operacao_de_turma.md` — 13 sprints propostas (AV-S01 a AV-S13), com AV-S01 detalhada (backlog, mapa de impacto, DoR, DoD, testes, riscos, closure gate previsto);
4. atualização do dashboard executivo, registrando a trilha como proposta, sem contabilizar como entrega/maturidade;
5. novos registros em `technical_debts.md`, `blockers.md` e `decisions.md`;
6. este registro de execução e o snapshot de fechamento.

## 4. Mapa de impacto

| Área | Caminhos previstos | Natureza |
|---|---|---|
| Backlog e trilha | `docs/governance/backlog/**` | novos documentos Markdown |
| Registros | `docs/governance/registers/*.md` | itens novos adicionados, nada removido |
| Dashboard | `docs/governance/executive_technical_dashboard.md` | seções atualizadas |
| Execução/snapshot | `docs/governance/sprints/sprint_GOV-002_*.md`, `docs/governance/snapshots/snapshot_EXEC-2026-09-21-02_GOV-002.md`, `snapshots/latest_execution.md` | novos/atualizados |
| Código e operação | `core/`, `ai-engine/`, `frontend/`, `infra/`, banco, serviços | sem alteração autorizada |

## 5. Critérios de aceite

- backlog rastreável a requisito/fonte, tipo, prioridade proposta, dependências, critérios de aceite, validações esperadas, riscos, decisões pendentes, etapa/marco/sprint e status real;
- documento de trilha com objetivo, limites, marcos, sequência, entregas, critérios de entrada/saída, atividades antecipáveis, decisões necessárias e itens fora de escopo;
- sprints propostas em estado `PROPOSTA`, nunca aprovadas por presunção; primeira sprint detalhada; demais em nível de sequência;
- dashboard atualizado sem contabilizar itens planejados como entregas ou maturidade;
- backlog anterior reconciliado, com itens mantidos fora da trilha explicitados;
- nenhuma aprovação atribuída a Rafael;
- nenhuma alteração funcional/operacional.

## 6. Fontes institucionais e do produto consultadas

- governança já instituída: `execution_policy.md`, `sprint_management_policy.md`, `definition_of_ready.md`, `sprint_closure_gate.md`, `documentation_policy.md`, registros canônicos, `BASELINE-001`;
- `docs/requisitos-utilizados.md`, `docs/backlog.md`, `docs/arquitetura.md`, ADR-001 a ADR-008, `docs/decisoes-pendencias.md`, `docs/pendencia-regulatoria.md`, `docs/relatorio-entrega.md`, `docs/relatorio-consolidado-avalia-2026-09-10.txt`, `docs/roteiro-apresentacao-supervisor.md`, `docs/roteiro-demo.md`, `docs/contracts/openapi.yaml`;
- código lido nesta execução: `core/app/main.py`, `core/app/deps.py`, `core/app/models.py`, `core/app/schemas.py`, `core/app/services/correction.py`, `core/app/tests/test_core_flow.py`, `frontend/src/services/api.ts`, `frontend/src/services/workflow.ts`, `frontend/src/pages/ReviewPage.tsx`, `frontend/src/pages/CorrectionPage.tsx`, `frontend/src/pages/AssessmentEditorPage.tsx`;
- inspeção de sistema: `find .github -type f` (vazio), `ls -la infra/compose scripts` (vazios);
- PRD: confirmado em `/Users/rafaeloliveira/Downloads/PRD_AvalIA_v1.0_Completo.docx` (315.436 bytes, modificado em 2026-09-06 15:11) e a versão `.pdf` homônima (1.366.951 bytes, modificada em 2026-09-04 14:53). O `.docx` é o mais recente dos dois; não há evidência nesta sessão de uma versão posterior a 06/09/2026, nem confirmação externa de que esta seja "a última versão" no sentido absoluto — apenas a mais recente localizada nesta máquina. Trecho inicial lido confirma título, versão "1.0" e data "01/09/2026" no controle do documento.

## 7. Backlog desta execução

| ID | Entrega | Estado |
|---|---|---|
| GOV-002-01 | Backlog técnico canônico (`backlog_tecnico_avalia.md`) | implementado; validação documental concluída |
| GOV-002-02 | Documento da trilha (`trilha_operacao_de_turma.md`) | implementado; validação documental concluída |
| GOV-002-03 | Proposta de sprints com AV-S01 detalhada (`proposta_sprints_operacao_de_turma.md`) | implementado; validação documental concluída |
| GOV-002-04 | Atualização do dashboard executivo | implementado; validação documental concluída |
| GOV-002-05 | Atualização dos registros de débitos/bloqueantes/decisões | implementado; validação documental concluída |
| GOV-002-06 | Snapshot e validação final | concluído; evidências no snapshot EXEC-2026-09-21-02 |
| GOV-002-07 | Homologação do planejamento | pendente; fora da autoridade do executor (decisão de Rafael) |

## 8. Ajustes de percurso

Nenhum registrado até o momento desta abertura.

## 9. Encerramento

**Estado da execução:** concluída documentalmente, aguardando homologação de Rafael.

**Snapshot:** [`EXEC-2026-09-21-02`](../snapshots/snapshot_EXEC-2026-09-21-02_GOV-002.md).

**Closure gate aplicado:**

- escopo e critérios documentais avaliados: atendidos;
- mudanças limitadas a Markdown de backlog/trilha/registros/dashboard: atendido por inspeção de paths e diff;
- evidências documentais e de inspeção de código com data/procedimento/resultado: atendido no snapshot;
- snapshot e dashboard: atendidos;
- reconciliação com backlog anterior sem apagar itens: atendido (seção 1 do backlog canônico);
- código, dependências, banco, infraestrutura e serviços: sem alteração;
- commit, push, tag, deploy e alteração remota: não realizados;
- revisão independente/delegação: não ocorreram e não são declaradas;
- achados de código (autorização por vínculo, sessionStorage): classificados como investigação/débito não confirmado por runtime, não como diagnóstico concluído;
- homologação por Rafael: pendente, sem aprovação presumida.

README, requisitos/PRD, ADRs e backlog anterior foram revisados; nenhum exigiu alteração nesta execução, pois o trabalho foi de planejamento aditivo, não de mudança de requisito ou capacidade.

A próxima ação é a revisão deste planejamento por Rafael, incluindo as decisões `DEC-AV-006` a `DEC-AV-015`. Nenhuma sprint funcional foi iniciada.