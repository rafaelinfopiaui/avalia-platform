# Governança técnica do AvalIA

Este diretório é a fonte canônica do rito de evolução técnica do AvalIA. A governança registra o que foi planejado, executado e comprovado; não substitui o código, os requisitos nem a decisão de produto.

## Autoridade e papéis

- **Rafael:** responsável por priorização, aprovação de planos funcionais, decisões de ampliação de escopo, exceções críticas e homologação.
- **Hermes:** conduz o rito, confere o estado real, coordena execuções autorizadas e consolida evidências e documentação canônica.
- **Agentes delegados:** executam somente o objetivo, arquivos/escopo, critérios de aceite e limites recebidos. Delegação, revisão independente e resultado só podem ser registrados quando ocorrerem de fato.
- **Consolidador:** uma única pessoa/agente, identificada na sprint, integra os registros canônicos e resolve duplicações documentais. Nesta implantação, o consolidador é Hermes.

A aprovação técnica registrada por um agente não equivale à homologação de Rafael. Silêncio, timeout ou aprovação em princípio não equivalem a autorização.

## Leitura obrigatória no início de uma execução

1. este índice e a [política de execução](execution_policy.md);
2. o ponteiro do [último baseline validado](snapshots/latest_validated_baseline.md);
3. o ponteiro da [última execução registrada](snapshots/latest_execution.md);
4. a sprint ativa em [`sprints/`](sprints/), se houver;
5. a [política de sprints](sprint_management_policy.md), a [Definition of Ready](definition_of_ready.md) e o [closure gate](sprint_closure_gate.md) quando houver trabalho planejado.

Depois da leitura, conferir Git, ambiente e fontes vivas. Relatório antigo é evidência histórica, não prova do estado atual.

## Fontes canônicas

| Informação | Fonte canônica |
|---|---|
| Rito da sessão e evidências | [execution_policy.md](execution_policy.md) |
| Planejamento e ciclo de sprint | [sprint_management_policy.md](sprint_management_policy.md) |
| Entrada pronta para execução | [definition_of_ready.md](definition_of_ready.md) |
| Avaliação de encerramento | [sprint_closure_gate.md](sprint_closure_gate.md) |
| Manutenção e precedência documental | [documentation_policy.md](documentation_policy.md) |
| Visão executiva atual | [executive_technical_dashboard.md](executive_technical_dashboard.md) |
| Escopo, backlog e mudanças da sprint | documento em [`sprints/`](sprints/) |
| Estado de uma execução | documento histórico em [`snapshots/`](snapshots/) |
| Débitos | [registers/technical_debts.md](registers/technical_debts.md) |
| Bloqueantes | [registers/blockers.md](registers/blockers.md) |
| Decisões de governança/produto pendentes | [registers/decisions.md](registers/decisions.md) |
| Requisitos implementados/herdados | [`../requisitos-utilizados.md`](../requisitos-utilizados.md) e PRD de origem identificado ali |
| Decisões arquiteturais | [`../adr/`](../adr/) |
| Backlog técnico de uma trilha em planejamento | [`backlog/`](backlog/) |

Dashboard, snapshot e sprint referenciam esses registros; não mantêm listas paralelas completas.

## Estrutura

```text
docs/governance/
├── README.md
├── sprint_management_policy.md
├── definition_of_ready.md
├── sprint_closure_gate.md
├── execution_policy.md
├── documentation_policy.md
├── executive_technical_dashboard.md
├── registers/
├── sprints/
├── snapshots/
├── templates/
└── backlog/
```

## Identificadores

- sprint funcional: definido no primeiro plano funcional homologado; não há numeração funcional instituída nesta implantação;
- implantação ou manutenção de governança: `GOV-NNN`;
- item: `<SPRINT>-NN` ou `GOV-NNN-NN`;
- débito: `DEBT-AV-NNN`;
- bloqueante: `BKL-AV-NNN`;
- decisão: `DEC-AV-NNN`;
- execução/snapshot: `EXEC-AAAA-MM-DD-NN`.

Não renomear registros históricos para adequá-los a convenções posteriores. O desenvolvimento anterior à governança permanece “estado herdado”.

## Templates

- [sprint](templates/sprint_template.md);
- [snapshot de execução](templates/execution_snapshot_template.md);
- [fechamento de sprint](templates/sprint_closure_template.md).

Templates são instrumentos de preenchimento, não evidências. Campos sem comprovação permanecem “não medido”, “não executado”, “não aplicável” ou “pendente”, conforme o caso.

## Estado desta instituição

A implantação documental está registrada em [`sprint_GOV-001_instituicao-governanca.md`](sprints/sprint_GOV-001_instituicao-governanca.md). Ela ficará pronta para homologação, mas não homologada, até manifestação explícita de Rafael.

O planejamento da trilha "Operação de uma turma" (backlog, sequência, proposta de sprints) está registrado em [`sprint_GOV-002_backlog_trilha.md`](sprints/sprint_GOV-002_backlog_trilha.md) e detalhado em [`backlog/`](backlog/). Nenhuma sprint funcional dessa trilha está aprovada.
