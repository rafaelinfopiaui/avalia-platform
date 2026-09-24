---
id: GOV-004
tipo: reconciliacao-documental
status: concluida_aguardando_homologacao
abertura: "2026-09-23"
responsavel_consolidacao: Hermes
homologacao: pendente_Rafael
depende_de: GOV-003
altera_escopo_de: GOV-003
---

# GOV-004 — Reconciliação do sequenciamento com decisões já aprovadas

> Execução exclusivamente documental. Propaga ao planejamento decisões que Rafael já havia tomado em 2026-09-21 (mesma conversa que produziu GOV-003), mas que não haviam sido totalmente refletidas na trilha e na proposta de sprints. Não implementa, não instala dependência, não altera serviço, não executa migração, não publica mudança.

## 1. Objetivo

Corrigir uma inconsistência documental real, encontrada por inspeção nesta sessão: `docs/governance/registers/decisions.md` já registrava `DEC-AV-016`, `DEC-AV-018` e `DEC-AV-021` como `aprovada (2026-09-21, nesta conversa)`, inclusive citando um "§11" de `trilha_operacao_de_turma.md` como o local do resequenciamento aplicado — mas esse §11 não existia; o documento de trilha e a proposta de sprints continuavam a tratar `DEC-AV-016` como pendente. Uma tentativa anterior de reconciliação (sessão de 2026-09-22, não formalizada como sprint/snapshot) havia editado parcialmente o backlog canônico (`BL-AV-4B-01/02`, criação de `BL-AV-4B-20`) mas foi interrompida antes de tocar trilha, sprints, dashboard e snapshot. Esta execução completa essa propagação.

## 2. Escopo autorizado

- criar o §11 da trilha com o sequenciamento em 5 fases descrito por Rafael em 2026-09-21 (consolidação → investigação de OCR → estrutura acadêmica → primeira entrega completa por imagem → ampliação operacional, incluindo CSV);
- corrigir as referências desatualizadas a `DEC-AV-016` como "pendente" em `trilha_operacao_de_turma.md` (§1.2, §7) e `proposta_sprints_operacao_de_turma.md` (§1, §4);
- marcar `DEC-AV-018` e `DEC-AV-021` como aprovadas nas tabelas de decisão da trilha, coerente com `registers/decisions.md`;
- registrar, no backlog canônico, a separação já iniciada em 2026-09-22 entre o levantamento técnico inicial de OCR (`BL-AV-4B-01`) e o benchmark comparativo (`BL-AV-4B-20`), e ajustar a sprint candidata de `BL-AV-4B-20` na tabela-resumo (estava listada em `AV-S06B`, deveria estar em `AV-S05B`, junto do levantamento/decisão arquitetural);
- atualizar dashboard, `latest_execution.md`, este documento de sprint e o snapshot de fechamento;
- não renumerar nenhum ID de sprint ou item de backlog existente;
- não decidir nenhuma das decisões ainda pendentes (`DEC-AV-006` a `015`, `017`, `019`, `020`);
- não implementar nenhum componente de OCR/visão, não instalar dependência, não iniciar benchmark real.

## 3. Origem das decisões propagadas

Não são decisões novas desta execução — foram tomadas por Rafael em 2026-09-21, na mesma conversa que produziu GOV-003, e já estavam registradas em `registers/decisions.md`:

- `DEC-AV-016`: entrada por imagem priorizada em relação à importação CSV;
- `DEC-AV-018`: primeira versão limitada a uma resposta de uma questão por foto (não prova inteira);
- `DEC-AV-021`: professor seleciona manualmente avaliação, questão e aluno (sem identificação automática na primeira versão).

## 4. Artefatos alterados

1. `docs/governance/backlog/backlog_tecnico_avalia.md` — §1.2 atualizada; `BL-AV-4B-20` reposicionado para `AV-S05B` na tabela-resumo;
2. `docs/governance/backlog/trilha_operacao_de_turma.md` — novo §11 (sequenciamento em 5 fases); §1.2 (nota de topo), §6 (atividades antecipáveis) e §7 (tabela de decisões) corrigidos para refletir as decisões já aprovadas;
3. `docs/governance/backlog/proposta_sprints_operacao_de_turma.md` — nota de reconciliação no cabeçalho; §1 (incertezas) e §4 (premissas) corrigidos;
4. `docs/governance/executive_technical_dashboard.md` — seção 1, 2, 4, 5, 7 e 8 atualizadas;
5. `docs/governance/snapshots/latest_execution.md` — ponteiro atualizado;
6. este registro de execução e o snapshot de fechamento.

`docs/governance/registers/decisions.md` não foi alterado nesta execução — já estava correto; a inconsistência estava nos documentos que ele referenciava, não nele.

## 5. Critérios de aceite

- nenhuma referência remanescente trata `DEC-AV-016`, `018` ou `021` como pendente nos documentos de trilha/sprints;
- a referência a "§11" em `registers/decisions.md` passa a apontar para conteúdo real;
- nenhum ID de sprint ou item de backlog é renumerado;
- nenhuma das demais decisões pendentes é resolvida por esta execução;
- histórico de GOV-001/002/003 preservado — nenhuma seção anterior apagada, apenas complementada ou corrigida com nota datada;
- dashboard, `latest_execution.md` e snapshot refletem o mesmo estado;
- nenhuma aprovação de sprint nem homologação atribuída a Rafael.

## 6. Backlog desta execução

| ID | Entrega | Estado |
|---|---|---|
| GOV-004-01 | Diagnóstico da inconsistência (decisions.md vs. trilha/sprints) registrado | implementado; validação documental concluída |
| GOV-004-02 | §11 da trilha (sequenciamento em 5 fases) | implementado; validação documental concluída |
| GOV-004-03 | Correção de referências a DEC-AV-016/018/021 em trilha e sprints | implementado; validação documental concluída |
| GOV-004-04 | Reposicionamento de BL-AV-4B-20 na tabela-resumo do backlog | implementado; validação documental concluída |
| GOV-004-05 | Dashboard e latest_execution.md atualizados | implementado; validação documental concluída |
| GOV-004-06 | Snapshot e validação final | concluído; evidências no snapshot EXEC-2026-09-23-01 |
| GOV-004-07 | Homologação desta reconciliação | pendente; fora da autoridade do executor (decisão de Rafael) |

## 7. Ajustes de percurso

Uma tentativa anterior de reconciliação (sessão de 2026-09-22, sem sprint/snapshot formal) havia editado `backlog_tecnico_avalia.md` (`BL-AV-4B-01/02`, criação de `BL-AV-4B-20`) e ficado incompleta. Esta execução (GOV-004) retoma esse trabalho, completa a propagação às demais fontes canônicas e o formaliza com o rito completo de sprint/snapshot — não é uma correção silenciosa, é o fechamento formal de um trabalho que havia sido iniciado fora do rito.

## 8. Encerramento

**Estado da execução:** concluída documentalmente, aguardando homologação de Rafael.

**Snapshot:** [`EXEC-2026-09-23-01`](../snapshots/snapshot_EXEC-2026-09-23-01_GOV-004.md).

**Closure gate aplicado:**

- inconsistência documental identificada e corrigida, com evidência de antes/depois: atendido;
- sequenciamento em 5 fases registrado, preservando IDs de sprint/item: atendido;
- nenhuma decisão nova tomada por extensão/analogia: atendido — apenas as 3 já aprovadas em 2026-09-21 foram propagadas;
- histórico de GOV-001/002/003 preservado sem remoção/renumeração: atendido, verificado por inspeção de diff;
- mudanças limitadas a Markdown de backlog/trilha/registros/dashboard/sprints: atendido por inspeção de paths;
- código, dependências, banco, infraestrutura e serviços: sem alteração;
- commit, push, tag, deploy e alteração remota: não realizados;
- homologação por Rafael: pendente, sem aprovação presumida.

README, requisitos/PRD e ADRs foram revisados; nenhum exigiu alteração além da leitura já registrada em GOV-003 — o PRD fonte não foi alterado (está fora do repositório).

A próxima ação é Rafael revisar esta reconciliação e decidir sobre as demais decisões pendentes da Etapa 4B (`DEC-AV-017`, `019`, `020`) e gerais (`DEC-AV-006` a `015`), além de homologar GOV-001 a GOV-004 como um todo, antes de qualquer sprint funcional ser aprovada para execução.
