---
id: GOV-003
tipo: implantacao-documental
status: concluida_aguardando_homologacao
abertura: "2026-09-21"
responsavel_consolidacao: Hermes
homologacao: pendente_Rafael
depende_de: GOV-002
altera_escopo_de: GOV-002
---

# GOV-003 — Incorporação do requisito de entrada por imagem (OCR/visão local assistida)

> Execução exclusivamente documental. Altera o planejamento autorizado em GOV-002 (adiciona escopo, não remove). Não implementa, não instala dependência, não altera serviço, não executa migração, não publica mudança.

## 1. Objetivo

Incorporar ao planejamento da trilha "Operação de uma turma" um requisito explícito de entrada de respostas por imagem, incluindo manuscritas, com OCR/visão local, confrontando-o com o PRD e registrando a atualização de escopo sem reescrever silenciosamente o histórico de GOV-002.

## 2. Escopo autorizado

- confrontar o requisito com o PRD e registrar se já estava previsto, adiado ou fora do escopo original;
- criar a Etapa 4B no backlog canônico e no documento de trilha, com seus itens, decisões, mapa de sequência e dependências;
- propor sprints próprias (AV-S05B a AV-S10B) na proposta de sprints, sem renumerar as sprints existentes;
- registrar disputa de recursos entre OCR/visão e correção local como decisão explícita, não como escolha técnica silenciosa;
- atualizar dashboard, registros de decisões e snapshot;
- não implementar nenhum componente de OCR/visão, não instalar dependência, não iniciar benchmark real.

## 3. Confronto com o PRD (resumo — detalhe em `backlog/backlog_tecnico_avalia.md` §1.1)

- RF-06 (entrada de respostas) previa apenas "Digitação/CSV/API"; imagem não constava do fluxo esperado.
- P0 (MVP obrigatório) excluía explicitamente "OCR manuscrito".
- P2 (evolução) já previa "OCR/HTR experimental" — portanto o requisito de Rafael **antecipa um item já existente no roadmap**, não introduz algo alheio ao PRD.
- §5.1 (fora do escopo do primeiro ciclo) exclui "Reconhecimento manuscrito em produção" — limite preservado nesta trilha: o fluxo é assistido, com confirmação humana obrigatória antes da correção, nunca produção autônoma.

**Classificação do item:** antecipação controlada de proposta já prevista no PRD (P2/experimental), não invenção de requisito nem contradição do documento de origem.

## 4. Artefatos alterados

1. `docs/governance/backlog/backlog_tecnico_avalia.md` — nova seção 1.1 (confronto com PRD) e 1.2 (reconciliação com GOV-002); nova Etapa 4B com 19 itens (`BL-AV-4B-01` a `19`);
2. `docs/governance/backlog/trilha_operacao_de_turma.md` — marcos, diagrama de sequência, entregas, critérios de entrada/saída do Marco 2, atividades antecipáveis, tabela de decisões e nova seção 10 (registro de mudança de escopo) atualizados; nenhuma seção anterior removida;
3. `docs/governance/backlog/proposta_sprints_operacao_de_turma.md` — 6 novas sprints propostas (AV-S05B a AV-S10B) na tabela e na seção de sequenciamento; premissas atualizadas;
4. `docs/governance/registers/decisions.md` — 6 novas decisões (`DEC-AV-016` a `021`);
5. `docs/governance/executive_technical_dashboard.md` — trilha proposta atualizada (novo denominador de itens, sem contabilizar como entrega);
6. este registro de execução e o snapshot de fechamento.

## 5. Critérios de aceite

- requisito confrontado com o PRD, com classificação explícita (previsto/adiado/fora de escopo) e trecho citado;
- fluxo funcional das 7 etapas do usuário refletido no backlog, sem presumir automatização da correção antes da confirmação;
- backlog A–F do usuário mapeado a itens rastreáveis com tipo, prioridade, dependências e critérios de aceite;
- decisões do usuário registradas como pendentes, associadas aos itens que bloqueiam, sem presumir resposta;
- disputa de recursos entre OCR/visão e correção tratada como decisão/ADR, não como implementação silenciosa;
- histórico de GOV-002 preservado — nenhum item removido ou renumerado;
- dashboard atualizado sem contabilizar capacidade entregue;
- nenhuma aprovação atribuída a Rafael;
- nenhuma alteração funcional/operacional, nenhuma dependência instalada.

## 6. Backlog desta execução

| ID | Entrega | Estado |
|---|---|---|
| GOV-003-01 | Confronto com o PRD registrado | implementado; validação documental concluída |
| GOV-003-02 | Etapa 4B no backlog canônico (19 itens) | implementado; validação documental concluída |
| GOV-003-03 | Atualização do documento de trilha (marcos, sequência, decisões) | implementado; validação documental concluída |
| GOV-003-04 | Sprints AV-S05B a AV-S10B na proposta de sprints | implementado; validação documental concluída |
| GOV-003-05 | 6 novas decisões no registro canônico | implementado; validação documental concluída |
| GOV-003-06 | Dashboard atualizado | implementado; validação documental concluída |
| GOV-003-07 | Snapshot e validação final | concluído; evidências no snapshot EXEC-2026-09-21-03 |
| GOV-003-08 | Homologação da atualização de escopo | pendente; fora da autoridade do executor (decisão de Rafael) |

## 7. Ajustes de percurso

Nenhum registrado além da própria natureza desta execução (ajuste de escopo solicitado por Rafael, tratado com o rito completo de atualização, não como correção silenciosa).

## 8. Encerramento

**Estado da execução:** concluída documentalmente, aguardando homologação de Rafael.

**Snapshot:** [`EXEC-2026-09-21-03`](../snapshots/snapshot_EXEC-2026-09-21-03_GOV-003.md).

**Closure gate aplicado:**

- confronto com o PRD registrado com trechos e linhas citados: atendido;
- fluxo funcional das 7 etapas do usuário refletido no backlog sem automatizar correção antes da confirmação: atendido (`BL-AV-4B-14`, regra transversal da Etapa 4B);
- backlog A–F mapeado a itens rastreáveis: atendido (19 itens, `BL-AV-4B-01` a `19`);
- decisões do usuário registradas como pendentes, associadas aos itens que bloqueiam: atendido (`DEC-AV-016` a `021`);
- disputa de recursos OCR/visão vs. correção tratada como decisão, não implementação silenciosa: atendido (`BL-AV-4B-17`);
- histórico de GOV-002 preservado sem remoção/renumeração: atendido, verificado por inspeção de diff;
- mudanças limitadas a Markdown de backlog/trilha/registros/dashboard/sprints: atendido por inspeção de paths;
- código, dependências, banco, infraestrutura e serviços: sem alteração;
- commit, push, tag, deploy e alteração remota: não realizados;
- homologação por Rafael: pendente, sem aprovação presumida.

README, requisitos/PRD e ADRs foram revisados; nenhum exigiu alteração além da leitura de confronto já registrada no snapshot — o PRD fonte não foi alterado (está fora do repositório).

A próxima ação é a revisão desta atualização de escopo por Rafael, incluindo a decisão sobre a ordem relativa entre CSV e imagem (`DEC-AV-016`) e as demais decisões da Etapa 4B. Nenhuma investigação ou implementação foi iniciada.