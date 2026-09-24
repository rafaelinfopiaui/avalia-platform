---
id: EXEC-2026-09-21-03
tipo: execucao
sprint: GOV-003
gerado_em: "2026-09-21T16:45:54-03:00"
executor: Hermes
status: concluida_aguardando_homologacao
commit_referencia: 0be691e12e9d5d6f3ffc989237739f6559d8dacd
---

# Snapshot EXEC-2026-09-21-03 — Entrada por imagem e transcrição assistida

> Registro histórico da execução documental GOV-003. Altera o planejamento de GOV-002 (adiciona escopo), não promove baseline, não aprova sprint, não registra homologação de Rafael.

## 1. Abertura

- objetivo: incorporar ao planejamento um requisito explícito de entrada de respostas por imagem (incluindo manuscritas) com OCR/visão local, confrontado com o PRD;
- escopo: atualização documental do backlog, da trilha, da proposta de sprints, dos registros de decisões e do dashboard;
- fora de escopo: qualquer implementação, instalação de biblioteca de OCR/visão, execução de benchmark real, alteração de serviço/banco/infraestrutura, commit/push/tag/deploy;
- repositório: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform`;
- remoto: `https://github.com/rafaelinfopiaui/avalia-platform.git`;
- branch/commit no início desta execução: `main` / `0be691e12e9d5d6f3ffc989237739f6559d8dacd`;
- working tree no início: idêntico ao final de GOV-002 (`README.md` modificado; `AGENTS.md` e `docs/governance/` não rastreados; `docs/roteiro-apresentacao-supervisor.md` não rastreado e preexistente), confirmado por `git status --short --branch` e `find docs/governance -type f` antes de qualquer edição;
- alterações preexistentes protegidas: toda a árvore de GOV-001/GOV-002, mantida intacta e apenas complementada;
- delegação: nenhuma; execução e consolidação por Hermes.

## 2. Confronto com o PRD (evidência)

Fonte: `/Users/rafaeloliveira/Downloads/PRD_AvalIA_v1.0_Completo.docx` (mesmo arquivo já confirmado em GOV-002 — 315.436 bytes, modificado 2026-09-06T15:11, controle "versão 1.0", "01/09/2026"). Busca textual por termos (`ocr`, `htr`, `manuscrit`, `imagem`, `foto`, `scanner`, etc.) sobre a extração completa do documento (3.699 linhas). Trechos relevantes:

| Linha | Trecho | Classificação |
|---|---|---|
| 258–260 | P0 (MVP obrigatório): inclui "respostas digitais/CSV"; exclui "OCR manuscrito, redações longas, cobrança, aplicativo nativo" | excluído do MVP obrigatório |
| 264–265 | P2 (evolução): inclui "OCR/HTR experimental" | já previsto no roadmap, como evolução |
| 271–272 | 5.1 Fora do escopo do primeiro ciclo: "Reconhecimento manuscrito em produção" | excluído apenas em produção, não a investigação/experimentação |
| 462–464 | RF-06: "Fluxo esperado: Digitação/CSV/API → validação → deduplicação → persistência → fila" | imagem não constava do fluxo de RF-06 como escrito |

Conclusão registrada: antecipação controlada de item já previsto (P2/experimental), não invenção nem contradição do PRD. Detalhe completo em `backlog/backlog_tecnico_avalia.md` §1.1.

## 3. Entregas

| Item | Estado | Entrega | Evidência |
|---|---|---|---|
| GOV-003-01 | implementado e validado documentalmente | confronto com o PRD registrado, com trechos e linhas citados | [`backlog_tecnico_avalia.md`](../backlog/backlog_tecnico_avalia.md) §1.1 |
| GOV-003-02 | implementado e validado documentalmente | Etapa 4B, 19 itens (`BL-AV-4B-01` a `19`) | [`backlog_tecnico_avalia.md`](../backlog/backlog_tecnico_avalia.md) §2 e §4 |
| GOV-003-03 | implementado e validado documentalmente | trilha atualizada (marcos, sequência, entregas, critérios, decisões, §10 mudança de escopo) | [`trilha_operacao_de_turma.md`](../backlog/trilha_operacao_de_turma.md) |
| GOV-003-04 | implementado e validado documentalmente | 6 sprints propostas (AV-S05B a AV-S10B) | [`proposta_sprints_operacao_de_turma.md`](../backlog/proposta_sprints_operacao_de_turma.md) |
| GOV-003-05 | implementado e validado documentalmente | 6 decisões novas (`DEC-AV-016` a `021`) | [`registers/decisions.md`](../registers/decisions.md) |
| GOV-003-06 | implementado e validado documentalmente | dashboard atualizado (novo denominador de 66 itens, sem contar como entrega) | [`executive_technical_dashboard.md`](../executive_technical_dashboard.md) |
| GOV-003-07 | implementado e validado documentalmente | este snapshot e verificação de consistência | este documento |
| GOV-003-08 | pendente | homologação da atualização de escopo | decisão exclusiva de Rafael; não ocorreu nesta execução |

## 4. Não entregas e limites

- nenhuma implementação de OCR/visão foi realizada; nenhuma biblioteca foi instalada; nenhum benchmark real foi executado;
- nenhuma das 6 novas decisões (`DEC-AV-016` a `021`) foi tomada — todas permanecem pendentes de Rafael;
- a ordem relativa entre a Etapa 4 (CSV) e a Etapa 4B (imagem) não foi decidida (`DEC-AV-016`);
- nenhuma sprint pré-existente (AV-S01 a AV-S13) foi renumerada, removida ou teve seu conteúdo alterado;
- o item de disputa de recursos entre OCR/visão e correção (`BL-AV-4B-17`) foi registrado como decisão pendente, não resolvido.

## 5. Arquivos impactados

### Criados

- `docs/governance/sprints/sprint_GOV-003_entrada_por_imagem.md`;
- `docs/governance/snapshots/snapshot_EXEC-2026-09-21-03_GOV-003.md` (este arquivo).

### Alterados

- `docs/governance/backlog/backlog_tecnico_avalia.md` (+ seções 1.1, 1.2 e Etapa 4B com 19 itens);
- `docs/governance/backlog/trilha_operacao_de_turma.md` (marcos, diagrama, entregas, critérios de entrada/saída do Marco 2, atividades antecipáveis, tabela de decisões, seção 8 e nova seção 10);
- `docs/governance/backlog/proposta_sprints_operacao_de_turma.md` (+ 6 sprints propostas, premissas atualizadas);
- `docs/governance/registers/decisions.md` (+6 itens: `DEC-AV-016` a `021`);
- `docs/governance/executive_technical_dashboard.md`;
- `docs/governance/snapshots/latest_execution.md` (ponteiro atualizado nesta execução).

Nenhum arquivo de código, manifesto de dependências, banco, infraestrutura, serviço ou configuração operacional foi alterado. Nenhum item de GOV-002 (débitos, bloqueantes, decisões, sprints, itens de backlog originais) foi removido ou reescrito — apenas complementado.

## 6. Validações executadas

Ambiente: macOS, repositório local, branch `main`, fuso `-03:00`.

| Data/fuso | Comando/procedimento | Tipo | Resultado real |
|---|---|---|---|
| 2026-09-21T16:41:19 | busca textual por termos relacionados a OCR/imagem sobre a extração completa do PRD (3.699 linhas, offsets paginados) | inspeção de documento | 58 e depois 10 linhas relevantes localizadas; 4 trechos citados na tabela da seção 2 |
| 2026-09-21T16:41:19 | leitura das linhas 245–294 e 1040–1079 do PRD para contexto | inspeção de documento | confirma classificação P0/P2/§5.1 e ausência de menção a imagem no controle de segurança/privacidade |
| ver adendo abaixo | validação de links/frontmatter/diff | validação documental automatizada | registrada em adendo, após a conclusão das edições |

Nenhum teste automatizado (pytest/build) foi executado nesta sessão — não fazia parte do escopo desta atualização de planejamento.

## 7. Decisões, débitos e bloqueantes desta execução

- decisões novas: `DEC-AV-016` a `DEC-AV-021` — [registro canônico](../registers/decisions.md);
- nenhum débito ou bloqueante novo foi registrado nesta execução (a investigação de OCR ainda não foi iniciada; não há achado de código a registrar até `BL-AV-4B-01` ocorrer).

Nenhuma decisão foi atribuída a Rafael durante esta execução; todas permanecem `pendente`.

## 8. Estado final

- status da execução: **concluída documentalmente, aguardando homologação**;
- sprint funcional ativa: nenhuma;
- baseline promovido: não;
- alterações desta execução: locais, não staged, não commitadas;
- alterações preexistentes (GOV-001, GOV-002 e `docs/roteiro-apresentacao-supervisor.md`): preservadas;
- homologação por Rafael: pendente.

## 9. Documentação revisada

- backlog e trilha de GOV-002: revisados e complementados, não reescritos;
- requisitos/PRD: revisado especificamente para o confronto desta atualização; nenhuma alteração no arquivo fonte (fora do repositório, não versionado);
- ADRs: revisados; sem alteração necessária — o novo ADR de motor/modelo de OCR (`BL-AV-4B-02`) é item de investigação futura, não desta execução;
- README: não alterado nesta execução.

## 10. Próxima ação

Rafael revisar o confronto com o PRD, a Etapa 4B, as 6 novas decisões (`DEC-AV-016` a `021`) e as 6 sprints propostas; decidir a ordem relativa entre CSV e imagem (`DEC-AV-016`) e os demais itens que bloqueiam o início de `BL-AV-4B-01`. Nenhuma investigação ou implementação será iniciada sem essa decisão.

## 11. Adendo de validação final

**2026-09-21T16:47-03:00 — Hermes.** Após concluir as edições de backlog, trilha, sprints, decisões, dashboard e sprint/snapshot desta execução:

- `python3 /tmp/validate_avalia_governance.py`: exit 0; **27** arquivos Markdown lidos, **122** links locais verificados, **0** links quebrados, **0** erros de frontmatter;
- `git diff --check`: exit 0;
- contagem real de itens do backlog: `grep -c '^| BL-AV-' backlog_tecnico_avalia.md` → **66** (confirma o denominador citado no dashboard: 47 da trilha original + 19 da Etapa 4B);
- contagem real de sprints na tabela: `grep -c '^| AV-S' proposta_sprints_operacao_de_turma.md` → **19** (confirma AV-S01 a AV-S13 + AV-S05B a AV-S10B);
- `git status --short --branch`: apenas `README.md` modificado (rastreado, herdado de GOV-001); `AGENTS.md` e `docs/governance/` (incluindo os novos arquivos desta execução) não rastreados; `docs/roteiro-apresentacao-supervisor.md` continua não rastreado e preexistente;
- inventário completo de paths alterados/novos filtrado contra os quatro prefixos autorizados: **nenhum path fora do escopo autorizado**;
- `git diff --cached --name-only`: vazio — nenhum arquivo staged;
- nenhum commit, push, tag ou deploy realizado.

O adendo confirma que a atualização de escopo desta execução (GOV-003) não introduziu nenhuma alteração fora do escopo documental e preservou integralmente o histórico de GOV-001/GOV-002.
