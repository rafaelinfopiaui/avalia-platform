# Dashboard Executivo de Evolução Técnica — AvalIA

> Atualização: 2026-09-24 (PR #1 integrado a `main` via merge commit) · Fonte canônica versionada em Markdown · Estado: AV-S02 homologada; PR #1 integrado a `main` (SHA `7f2e0032ac7971ae43db5cc2386da0de321b778f`, merge commit, 6 commits preservados); CI remota em `main` 3/3 jobs verdes; `avalia_dev` AINDA sem a migração (`DEBT-AV-011` residual) — 3 duplicatas preservadas, sem `UniqueConstraint`; próxima sprint elegível proposta (`AV-S03`), não iniciada

## 1. Leitura executiva

O AvalIA possui uma demonstração experimental herdada, organizada em Core API, AI Engine local e frontend. Nas execuções GOV-001 a GOV-004, foram instituídos o rito de governança, o backlog e a trilha técnica "Operação de uma turma" (incluindo a Etapa 4B — entrada por imagem), e reconciliado o sequenciamento com as decisões já aprovadas por Rafael. Em 2026-09-23 (GOV-005), Rafael homologou essa governança com duas ressalvas explícitas — (1) precedência normativa de documento define comportamento esperado, evidência datada define estado observado, divergências sempre registradas, nunca resolvidas só por precedência; (2) esta homologação não promove `BASELINE-001` — e aprovou o escopo da primeira sprint funcional, `AV-S01`, autorizando sua execução com 7 refinamentos de escopo, autorização e critérios de aceite. Nenhum código foi alterado nesta execução; a autorização cobre apenas os 6 itens de `AV-S01`, não as demais 18 sprints da trilha.

## 2. Referências de estado

| Referência | Estado | Link |
|---|---|---|
| Última execução registrada | EXEC-2026-09-24-07, integração do PR #1 a `main` | [ponteiro](snapshots/latest_execution.md) |
| Último baseline validado sob esta governança | nenhum promovido (explicitamente não promovido por esta homologação) | [ponteiro](snapshots/latest_validated_baseline.md) |
| Baseline herdado candidato | inspeção documental/Git de 2026-09-21 | [BASELINE-001](snapshots/snapshot_BASELINE-001_estado-herdado.md) |
| Sprint funcional encerrada | `AV-S01` — homologada por Rafael em 2026-09-23 com `DEBT-AV-009` aceito como débito residual aberto | [documento da sprint](sprints/sprint_AV-S01_autorizacao_retomada_revalidacao.md) |
| Sprint funcional encerrada | `AV-S02` — **homologada por Rafael em 2026-09-24** (escopo dos 5 commits da branch `feat/av-s01-s02-consolidacao`); `DEBT-AV-011` (migração operacional em `avalia_dev`) e saneamento de duplicatas aceitos como débitos residuais | [documento da sprint](sprints/sprint_AV-S02_ci_visual_isolamento_testes.md) §19.6 |
| Execução documental ativa | GOV-005 | [snapshot](snapshots/snapshot_EXEC-2026-09-23-02_GOV-005.md) |
| Trilha proposta (não aprovada, exceto AV-S01) | "Operação de uma turma" (5 fases, com Etapa 4B — entrada por imagem priorizada sobre CSV) | [documento da trilha](backlog/trilha_operacao_de_turma.md) §11 |

## 3. Estado por componente

| Componente | Implementação observada | Validação atual nesta execução | Fonte |
|---|---|---|---|
| Core API | idempotência de revisão humana corrigida; migração NÃO deduplica automaticamente (detecta+aborta, por exigência de Rafael); lint mínimo (Ruff) configurado | 42 passed; Ruff `All checks passed!`; migração validada em SQLite E em PostgreSQL 16 isolado real (com e sem duplicatas); idempotência sob concorrência real confirmada em Postgres (10 e 6 threads) | [última execução](snapshots/latest_execution.md) |
| AI Engine | lint Ruff configurado; fonte não alterada nesta fatia | 21 passed no padrão e 21 passed no modo simulado global; Ruff `All checks passed!` | [última execução](snapshots/latest_execution.md) |
| Frontend | React/Vite/TypeScript e build scripts versionados; retomada via API implementada em AV-S01; decisão persistida exibida em modo somente leitura (BL-AV-1-10); ESLint mínimo configurado | build 0 erros; AC-03 validado com evidência visual real no saneamento de 2026-09-23; AC-04/AC-10 revalidados visualmente pós-fix em 2026-09-24 (Chrome real via CDP); ESLint limpo | [última execução](snapshots/latest_execution.md) |
| Banco/infra local | configuração e documentação presentes | não inspecionados operacionalmente; serviços não alterados | [baseline](snapshots/snapshot_BASELINE-001_estado-herdado.md) |
| Governança | políticas, templates, registros, baseline e dashboard preparados | validação documental desta execução registrada no snapshot GOV-001 | [última execução](snapshots/latest_execution.md) |

## 4. Histórico governado

| Sprint/execução | Tipo | Resultado | Implementação | Validação | Homologação |
|---|---|---|---|---|---|
| Estado anterior | herdado, não convertido em sprint | demonstração experimental existente | registrada em código e documentação histórica | resultados históricos de 09–11/09/2026; não reexecutados nesta sessão | não inferida |
| GOV-001 | implantação documental (governança) | documentação preparada para revisão | artefatos de governança criados | validação documental registrada no snapshot | pendente de Rafael |
| GOV-002 | implantação documental (backlog e trilha) | backlog canônico, trilha e proposta de sprints preparados para revisão | artefatos de planejamento criados; nenhuma sprint funcional iniciada | validação documental registrada no snapshot | pendente de Rafael |
| GOV-003 | atualização de escopo (entrada por imagem) | Etapa 4B, 19 itens novos, 6 sprints propostas, confronto com PRD registrado | artefatos de planejamento criados/alterados; nenhuma sprint funcional iniciada | validação documental registrada no snapshot | pendente de Rafael |
| GOV-004 | reconciliação documental (sequenciamento) | 3 decisões já aprovadas por Rafael (`DEC-AV-016`, `018`, `021`) propagadas ao sequenciamento da trilha em 5 fases; `BL-AV-4B-01/02/20` reposicionados (levantamento vs. benchmark separados) | artefatos de planejamento alterados; nenhuma sprint funcional iniciada | validação documental registrada no snapshot | pendente de Rafael (demais decisões da Etapa 4B) |
| GOV-005 | homologação de governança + aprovação de sprint | GOV-001 a GOV-004 homologados com 2 ressalvas; `AV-S01` aprovada e autorizada (6 itens, 7 refinamentos); `BL-AV-4B-20/21` detalhados por completo | documento de sprint `AV-S01` criado; backlog detalhado; nenhum código alterado | validação documental registrada no snapshot | homologado/aprovado por Rafael nesta execução (governança e escopo de AV-S01, não as demais sprints) |
| AV-S01 (execução + saneamento) | implementação real de código (Core + frontend) + saneamento de lacunas de evidência | autorização por vínculo corrigida em 4 rotas + endpoint de contexto novo; retomada via API no frontend; suíte de regressão (24 casos); saneamento posterior: AC-03 (4 sub-casos) comprovado com validação visual real; causa raiz de `DEBT-AV-009` documentada; identificador de snapshot duplicado reconciliado | Core 35/35; AI Engine 21/21 (padrão)/19/21 (simulado global, débito pré-existente); frontend build 0 erros; AC-03 confirmado por evidência visual real em navegador (Chrome via CDP + Playwright). A validação da IA desta execução foi em modo simulado; não houve revalidação da inferência real/Ollama | verificação independente por Hermes em ambas as fatias; revisões efetivas: backend/contrato por Antigravity CLI, frontend por Codex (3 rodadas), consolidação e guard final por Hermes; Claude Code indisponível (OAuth expirado) | **homologada por Rafael em 2026-09-23 com `DEBT-AV-009` aceito como débito residual aberto; sem autorização de commit/push/tag/deploy/baseline/próxima sprint** |
| AV-S02 (execução local) | isolamento de teste do AI Engine; CI mínima local; correção de whitespace; validação visual completa | `BL-AV-1-09` implementado (diff de 2 linhas, suíte 21/21 nos 2 ambientes); `.github/workflows/ci.yml` criado (3 jobs, sem deploy/secrets); `ReviewPage.tsx:25` corrigido, `git diff --check` global sem erros; 11 capturas reais do fluxo completo com IA simulada rotulada | verificação independente por Hermes em cada item; revisões cruzadas: Antigravity CLI aprovou BL-AV-1-09 incondicionalmente; Codex aprovou BL-AV-1-06 condicionalmente (achado: ausência de lint, sem linter configurado no repo); Codex aprovou a correção de whitespace; Antigravity CLI confirmou o achado de idempotência (`DEBT-AV-011`, severidade alta) como gap real | **implementada e validada localmente; CI remota (`DEBT-AV-005`) e homologação do fechamento pendentes; etapa remota aguardando autorização Git específica** |

**Trilha proposta "Operação de uma turma":** 8 etapas + 1 sub-etapa (4B), 3 marcos, lidos em 5 fases de execução desde GOV-004 (§11 da trilha), 19 sprints propostas (AV-S01 a AV-S13 e AV-S05B a AV-S10B). `AV-S01` foi homologada; `AV-S02` está implementada e validada localmente, aguardando CI remota e homologação; as demais 17 permanecem não autorizadas. Progresso funcional desta trilha: **7 de 70 itens implementados/homologados (10%)** — o denominador é o backlog canônico em [`backlog/backlog_tecnico_avalia.md`](backlog/backlog_tecnico_avalia.md): 68 itens anteriores + `BL-AV-1-09` (implementado nesta execução) + `BL-AV-1-10` (novo, achado de idempotência, proposto). Os 6 itens de `AV-S01` estão homologados; `BL-AV-1-09` está implementado e validado localmente, mas aguarda a mesma homologação de fechamento de `AV-S02` que o restante da sprint. Este percentual descreve o backlog desta trilha, não maturidade técnica ou qualidade pedagógica do produto.

Nenhum outro percentual de conclusão é publicado: 10% usa exclusivamente o denominador versionado de 70 itens e o numerador de 7 itens implementados/homologados. Maturidade técnica: **não medida**; não existe rubrica AvalIA aprovada.

## 5. Entregas desta execução

**GOV-001 (execução anterior):**
- rito de abertura, execução, evidência, snapshot e encerramento;
- política de sprint, DoR e closure gate;
- templates de sprint, snapshot e fechamento;
- baseline herdado com limites explícitos;
- registros canônicos de débitos, bloqueantes e decisões;
- instrução de contexto para agentes e entrada no README;
- separação entre última execução e último baseline validado.

**GOV-002 (esta execução):**
- backlog técnico canônico da trilha "Operação de uma turma" (47 itens, rastreados a requisito/fonte, tipo, prioridade proposta, dependências e critérios de aceite);
- documento de trilha com marcos, sequência, dependências, entregas por etapa e atividades antecipáveis;
- proposta de divisão em 13 sprints (AV-S01 a AV-S13), com a primeira sprint (AV-S01) detalhada em backlog, mapa de impacto, DoR, DoD, testes e riscos;
- 3 novos débitos técnicos e 1 novo bloqueante registrados a partir de achados de leitura estática de código (não reproduzidos em runtime);
- 10 novas decisões pendentes (DEC-AV-006 a DEC-AV-015), cada uma associada aos itens que bloqueia;
- reconciliação explícita com o backlog anterior (`docs/backlog.md`), sem apagar itens omitidos.

Evidência e arquivos: [snapshot GOV-001](snapshots/snapshot_EXEC-2026-09-21-01_GOV-001.md), [snapshot GOV-002](snapshots/snapshot_EXEC-2026-09-21-02_GOV-002.md), [snapshot GOV-003](snapshots/snapshot_EXEC-2026-09-21-03_GOV-003.md), [snapshot GOV-004](snapshots/snapshot_EXEC-2026-09-23-01_GOV-004.md) e [snapshot GOV-005](snapshots/snapshot_EXEC-2026-09-23-02_GOV-005.md).

**GOV-003 (esta execução):**
- confronto do requisito de entrada por imagem com o PRD, classificado como antecipação controlada de item já previsto no roadmap (P2/experimental "OCR/HTR"), não como requisito inventado ou contraditório;
- Etapa 4B — Entrada por imagem e transcrição assistida, com 19 itens novos (`BL-AV-4B-01` a `19`), cobrindo investigação de OCR, recebimento/armazenamento, preparação/extração local, conferência da transcrição, associação/correção e testes;
- 6 novas decisões pendentes (`DEC-AV-016` a `021`), cada uma associada aos itens que bloqueia;
- 6 novas sprints propostas (AV-S05B a AV-S10B), sem renumerar as 13 sprints existentes;
- regra transversal registrada: a correção assistida não inicia automaticamente antes da confirmação humana da transcrição;
- decisão de isolamento de recursos entre processo de OCR/visão e processo de correção local registrada como item de arquitetura próprio (`BL-AV-4B-17`), não como escolha implícita;
- histórico de GOV-001/GOV-002 preservado integralmente — nenhum item removido ou renumerado.

**GOV-004 (esta execução, 2026-09-23):**
- propagação de 3 decisões já aprovadas por Rafael em 2026-09-21 (`DEC-AV-016` — imagem priorizada sobre CSV; `DEC-AV-018` — uma resposta por foto na primeira versão; `DEC-AV-021` — seleção manual pelo professor) ao sequenciamento da trilha, antes desatualizado;
- novo §11 na trilha: sequenciamento em 5 fases (consolidação → investigação de OCR → estrutura acadêmica → primeira entrega por imagem → ampliação operacional, incluindo CSV), sem renumerar nenhum ID de sprint existente;
- separação explícita, no backlog canônico, entre o levantamento técnico inicial de OCR (`BL-AV-4B-01`) e o benchmark comparativo (`BL-AV-4B-20`, novo item), com `BL-AV-4B-02` (decisão arquitetural) reposicionado para depender do benchmark medido, não do levantamento;
- correção de uma referência cruzada inconsistente em `registers/decisions.md` (citava um §11 da trilha que ainda não existia);
- histórico de GOV-001/GOV-002/GOV-003 preservado integralmente — nenhum item removido ou renumerado; seções 1–10 da trilha mantidas como registro histórico.

**GOV-005 (esta execução, 2026-09-23):**
- Rafael homologou GOV-001 a GOV-004 com 2 ressalvas: (1) separação entre precedência normativa (o que documentos definem como esperado) e evidência factual datada (o que a execução real mostra) — divergências entre as duas são sempre registradas, nunca resolvidas declarando conformidade só por precedência de documento; (2) esta homologação é documental e não promove `BASELINE-001`;
- Rafael aprovou o escopo dos 6 itens de `AV-S01` (BL-AV-1-01, 02, 03, 04, 07, 08) e autorizou o início de sua execução, com 7 refinamentos: contrato/revisão do endpoint de retomada antes de implementar; fixtures isoladas sem tocar seed/ambiente; AC-03 detalhado em 4 sub-casos com validação visual dirigida; matriz de autorização com 4 perfis; classificação explícita de tipos de evidência; reconfirmação de disponibilidade dos agentes; documento de sprint com template vigente;
- disponibilidade de agentes reconfirmada nesta sessão: Codex e Antigravity CLI respondem normalmente; Claude Code (subprocess) indisponível por sessão OAuth expirada — papel de revisão arquitetural redistribuído para Antigravity CLI e Hermes, registrado como tal;
- `BL-AV-4B-20` e `BL-AV-4B-21` (criados em 2026-09-22, formalizados em GOV-004) receberam detalhamento narrativo completo (objetivo, critérios de aceite, dependências, riscos, validações) — regularização documental, não autoriza benchmark nem implementação de OCR;
- documento de sprint `sprint_AV-S01_autorizacao_retomada_revalidacao.md` criado, com template vigente, mapa de impacto, delegação por agente, critérios de aceite refinados e Definition of Done;
- esta aprovação cobre exclusivamente `AV-S01` — as demais 18 sprints da trilha continuam não autorizadas para execução.

## 6. Validações e indicadores

| Indicador | Resultado | Escopo |
|---|---|---|
| Links Markdown locais da governança | ver snapshot GOV-001 | documentação criada/alterada nesta execução |
| `git diff --check` | ver snapshot GOV-001 | working tree após implantação |
| Alterações funcionais/operacionais | nenhuma pretendida; conferir lista no snapshot | diff desta execução |
| Testes Core | não executados nesta execução | resultado histórico separado no baseline |
| Testes AI Engine | não executados nesta execução | resultado histórico separado no baseline |
| Build frontend | não executado nesta execução | resultado histórico separado no baseline |
| Teste visual | não executado nesta execução | — |
| Progresso de implementação da próxima trilha | não medido | próxima trilha não planejada |
| Progresso de validação da próxima trilha | não medido | próxima trilha não planejada |
| Score de maturidade | não medido | rubrica inexistente |

## 7. Débitos, bloqueantes e decisões

Fontes canônicas:

- [débitos técnicos](registers/technical_debts.md);
- [bloqueantes](registers/blockers.md);
- [decisões](registers/decisions.md).

Destaques atuais: pendência regulatória impede uso com dados reais; estado funcional atual requer revalidação antes de novo baseline (homologação de GOV-001-004 explicitamente não promove `BASELINE-001`); PRD original está fora do repositório; a trilha "Operação de uma turma" tem sua primeira sprint (`AV-S01`) aprovada e autorizada, com as demais aguardando decisão sobre ambiente-alvo, priorização geral e `DEC-AV-006` a `DEC-AV-015`, `DEC-AV-017`, `019`, `020`.

## 8. Próximos marcos

| Marco | Condição | Estado |
|---|---|---|
| Homologar a governança | Rafael revisar artefatos e decidir sobre GOV-001/BASELINE-001 | **homologada com ressalvas (2026-09-23)** — ver `DEC-AV-001` |
| Homologar o planejamento da trilha | Rafael revisar backlog, trilha (5 fases) e proposta de sprints, incluindo a Etapa 4B (GOV-002/GOV-003/GOV-004) | implícito na homologação de GOV-001-004; escopo de execução limitado a `AV-S01` |
| Decidir demais itens pendentes da Etapa 4B | `DEC-AV-017` (critérios do benchmark), `019`, `020`; demais decisões gerais `DEC-AV-006` a `015` | pendente |
| Executar a primeira sprint aprovada | `AV-S01` aprovada e autorizada (GOV-005, 2026-09-23) | **executada, saneada e homologada por Rafael (2026-09-23); `DEBT-AV-009` aceito como débito residual aberto** |
| Aprovar a segunda sprint (`AV-S02`) | Rafael revisar o plano `AV-S02` (CI mínima, visual completo com IA simulada, isolamento de `DEBT-AV-009`) e decidir sobre os 4 pontos do §15 | **aprovada e executada localmente (2026-09-23); CI remota e homologação do fechamento pendentes** — [documento da sprint](sprints/sprint_AV-S02_ci_visual_isolamento_testes.md) §18/§19 |
| Autorizar a etapa remota de `AV-S02` | Rafael revisar o pacote de revisão e decidir sobre `git add`/`commit`/`push`, criação da branch e abertura do PR | **executado (2026-09-24)** — branch `feat/av-s01-s02-consolidacao`, 4 commits, PR [#1](https://github.com/rafaelinfopiaui/avalia-platform/pull/1) (rascunho), CI remota real 3/3 jobs verdes (run [35997285722](https://github.com/rafaelinfopiaui/avalia-platform/actions/runs/35997285722), commit `36de551e414cba847e9e369bee10701cd142bb87`) |
| Homologar o fechamento de `AV-S02` e autorizar a integração | Rafael revisar o PR #1 e decidir sobre homologação/merge | **homologada e integrada a `main` (2026-09-24)** — merge commit `7f2e0032ac7971ae43db5cc2386da0de321b778f`, CI remota em `main` 3/3 jobs verdes (run [36000432576](https://github.com/rafaelinfopiaui/avalia-platform/actions/runs/36000432576)) |
| Decidir a próxima sprint elegível (`AV-S03`) | Rafael revisar a proposta (Etapa 2 — estrutura acadêmica) e suas dependências reais antes de autorizar o início | **proposta apresentada (2026-09-24), não iniciada** — ver `backlog/trilha_operacao_de_turma.md` §11 (Fase 3) e itens `BL-AV-2-01` a `05` |
| Decidir saneamento das duplicatas legadas de revisão humana (`DEBT-AV-011`) | Rafael decidir sobre a proposta de saneamento (backup, classificação equivalente/conflitante, preservação por arquivo em vez de exclusão) apresentada em `backlog/proposta_saneamento_human_reviews_duplicadas.md` | pendente — proposta apresentada em 2026-09-24, não executada |

## 9. Política de atualização

Atualizar este dashboard ao fim de cada execução/fatia. Todo resultado deve apontar para sprint, snapshot ou evidência. Implementação e validação permanecem separadas; indicadores sem método e denominador ficam “não medido”.
