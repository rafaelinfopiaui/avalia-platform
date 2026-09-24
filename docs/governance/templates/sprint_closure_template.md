---
sprint: "<SPRINT-ID>"
data_avaliacao: "AAAA-MM-DD"
avaliador_consolidador: "<nome>"
status_resultante: "<concluída|concluída com débitos|parcial|reprovada|bloqueada>"
homologacao_Rafael: pendente
---

# Fechamento — <SPRINT-ID>

## 1. Resultado executivo

- objetivo: <atingido/parcial/não atingido + justificativa>;
- estado: <classificação>;
- homologação: <pendente ou referência explícita>.

## 2. Critérios de aceite

| AC | Resultado | Evidência | Estado factual |
|---|---|---|---|
| <ID> | <resultado> | <link/comando> | validado/não validado/falhou |

## 3. Backlog

| Item | Planejado | Implementado | Validado | Homologado | Observação |
|---|---:|---:|---:|---:|---|
| <ID> | sim | sim/não/parcial | sim/não/parcial | sim/não | <limite> |

## 4. Closure gate

Aplicar [sprint_closure_gate.md](../sprint_closure_gate.md).

| Critério | Nível | Resultado | Evidência/exceção |
|---|---|---|---|
| A1 | crítico | atende/falha/N.A. | <link> |

Critérios críticos falhos: <listar/nenhum>.
Exceções decididas por Rafael: <referência/nenhuma>.

## 5. Validações

| Data/fuso | Comando/procedimento | Ambiente | Tipo | Resultado |
|---|---|---|---|---|
| <data> | <comando> | <ambiente> | <tipo> | <saída real> |

## 6. Débitos, bloqueantes e decisões

Referenciar os registros canônicos; não duplicar inventários.

## 7. Documentação revisada

| Artefato | Resultado |
|---|---|
| sprint | atualizado |
| snapshot | <link> |
| dashboard | atualizado |
| registros | atualizado/sem alteração necessária |
| README | atualizado/sem alteração necessária |
| requisitos/PRD | atualizado/sem alteração necessária |
| roadmap/backlog | atualizado/sem alteração necessária |

## 8. Estado Git e ações operacionais

- branch/commit/working tree: <estado>;
- commit/push/tag/deploy: <não realizados ou referências autorizadas>;
- alterações preexistentes: <preservadas/descrição>.

## 9. Próxima ação autorizável

<insumo ou decisão; não iniciar automaticamente a próxima trilha>.
