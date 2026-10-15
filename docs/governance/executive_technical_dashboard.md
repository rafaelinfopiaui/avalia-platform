# Dashboard Executivo de Evolução Técnica — AvalIA

> Atualização: 2026-10-01 (abertura da execução LOCAL de `AV-S04`, `DEC-AV-028`, após organização local via PR #8 integrado em `main`) · Fonte canônica versionada em Markdown · Estado: `AV-S03` encerrada (12/12 AC, integrada em `main`); PR #4 integrado em `main` (`a5974b1`, CI pós-merge verde); PR #2 fechado sem merge, conteúdo necessário preservado. `AV-S04` (múltiplas questões) teve seu planejamento (PR #7, HEAD `35e7040e7222e583e29645d07238002f0ef24e6e`) autorizado para execução LOCAL em branch dedicada `feat/av-s04-multiplas-questoes`, sem commit/push/merge; `AV-S05` (importação CSV) permanece **apenas planejado** — nenhuma evidência de execução localizada nas fontes inspecionadas (Git, worktrees, código) nesta auditoria. `AV-S05B` (investigação de OCR/visão local — **distinta de `AV-S05`**) é uma entrega experimental e documental parcial, publicada na branch `docs/av-s05b-investigacao` (PR #5 em rascunho), ainda não integrada a `main`: protocolo congelado, benchmark de texto impresso executado (Tesseract, EasyOCR, moondream:v2), revisão cruzada independente (Codex + Antigravity CLI) do benchmark, revisão independente do texto do ADR-009 pelo Antigravity CLI (APROVADO COM RESSALVAS, correções aplicadas) e conferência limitada dessas correções, agora versionadas no PR #5. Estado: **9 de 11 critérios de aceite obrigatórios atendidos, 2 parcialmente atendidos (AC-02, eixo manuscrito sem evidência de coleta localizada; AC-05, apenas imagem vazia testada, escrita totalmente ilegível não testada)** — classificada como **entrega parcial de investigação**, não como benchmark integral concluído; Tesseract/EasyOCR candidatos para próximo experimento, nenhuma solução aprovada para uso; ADR-009 permanece rascunho; esforço humano de revisão ainda não medido; coleta manuscrita autorizada e com protocolo pré-registrado, sem evidência de fotografia ou coleta iniciada localizada no filesystem nesta auditoria. Nenhum código de produção alterado; a única ação Git/remota posterior foi a publicação documental autorizada em PR rascunho, sem merge; nenhuma alteração em `avalia_dev`, nenhum deploy, nenhuma promoção de baseline, nenhuma nova sprint.

## 1. Leitura executiva

O AvalIA possui uma demonstração experimental herdada, organizada em Core API, AI Engine local e frontend. Nas execuções GOV-001 a GOV-004, foram instituídos o rito de governança, o backlog e a trilha técnica "Operação de uma turma" (incluindo a Etapa 4B — entrada por imagem), e reconciliado o sequenciamento com as decisões já aprovadas por Rafael. Em 2026-09-23 (GOV-005), Rafael homologou essa governança com duas ressalvas explícitas — (1) precedência normativa de documento define comportamento esperado, evidência datada define estado observado, divergências sempre registradas, nunca resolvidas só por precedência; (2) esta homologação não promove `BASELINE-001` — e aprovou o escopo da primeira sprint funcional, `AV-S01`, autorizando sua execução com 7 refinamentos de escopo, autorização e critérios de aceite. Nenhum código foi alterado nesta execução; a autorização cobre apenas os 6 itens de `AV-S01`, não as demais 18 sprints da trilha.

## 2. Referências de estado

| Referência | Estado | Link |
|---|---|---|
| Última execução registrada | EXEC-2026-10-14-12 — demonstração do fluxo integrado com IA local REAL (ambiente descartável): foto → transcrição MANUAL → confirmação → solicitação explícita de análise → resultado real (Ollama, `qwen2.5:7b-instruct-q4_K_M`, `engine_mode=real`) → revisão humana. Correlação completa `answer_id`→`job_id`→`AIExecution`→`HumanReview` confirmada no banco; confirmação não disparou análise automaticamente (gap real de 15s até o clique explícito); origem permaneceu MANUAL; ambiente descartável (banco + storage + Chrome) removido ao final; bancos protegidos intactos. Não é OCR nem avaliação formal de qualidade pedagógica; não altera o numerador. Reconciliação do numerador (19→22) publicada na mesma rodada — ver `RECONCILIACAO-2026-10-14-01`/`DEC-AV-042`. Ver §12 para o detalhamento completo da sprint (anteriores: AV-S06B backend integrado em main b818961, DEBT-AV-014 integrado em e8b0864 via PR #17, AV-S03B, GOV-007 — na cadeia do ponteiro) | [ponteiro](snapshots/latest_execution.md) |
| Configuração de orquestração de agentes (não funcional) | `GOV-007` — distribuição de trabalho entre Claude Code (executor principal), Antigravity (segundo executor/revisor cruzado) e Codex (auditorias pontuais); ver `DEC-AV-031`; documentação publicada em PR draft #12 (https://github.com/rafaelinfopiaui/avalia-platform/pull/12), sem merge | [documentação de evidência](evidence/GOV-007-distribuicao-clis/mecanismo_cobranca_hermes_claude_code.md) |
| PR #2 (`docs/av-s02-encerramento-planos-operacionais`) | **fechado sem merge**; conteúdo necessário preservado em `main` via PR #4 | [snapshot de reconciliação](snapshots/snapshot_RECONCILIACAO-2026-09-29-02_desvio-processo-2026-09-24.md) |
| PR #4 (`docs/av-s03-encerramento-integracao`) | **integrado em `main`** via merge commit `a5974b1`, CI pós-merge verde | https://github.com/rafaelinfopiaui/avalia-platform/pull/4 |
| Último baseline validado sob esta governança | nenhum promovido (explicitamente não promovido por esta homologação) | [ponteiro](snapshots/latest_validated_baseline.md) |
| Baseline herdado candidato | inspeção documental/Git de 2026-09-21 | [BASELINE-001](snapshots/snapshot_BASELINE-001_estado-herdado.md) |
| Sprint funcional encerrada | `AV-S01` — homologada por Rafael em 2026-09-23 com `DEBT-AV-009` aceito como débito residual aberto | [documento da sprint](sprints/sprint_AV-S01_autorizacao_retomada_revalidacao.md) |
| Sprint funcional encerrada | `AV-S02` — **homologada por Rafael em 2026-09-24** (escopo dos 5 commits da branch `feat/av-s01-s02-consolidacao`); `DEBT-AV-011` (migração operacional em `avalia_dev`) e saneamento de duplicatas aceitos como débitos residuais | [documento da sprint](sprints/sprint_AV-S02_ci_visual_isolamento_testes.md) §19.6 |
| Sprint funcional encerrada | `AV-S03` — **homologada por Rafael em 2026-09-29** (`DEC-AV-027`), integrada a `main` via merge commit `c391865` (PR #3); `DEBT-AV-012` aceito como débito residual | [documento da sprint](sprints/sprint_AV-S03_estrutura_academica.md) |
| Auditoria de governança encerrada | `GOV-006` — reconciliação do numerador (14/70) e publicação em pilha de Pacote B (AV-S05B, PR #5) e Pacote A (GOV-006, PR #6); ambos os PRs **integrados a `main`** em 2026-09-30 (merge commits `baa7ccb` e `ba6f407`), CI pós-merge verde em ambos | [documento GOV-006](sprints/sprint_GOV-006_auditoria_governanca.md) |
| Execução local autorizada, sprint em andamento | `AV-S04` — múltiplas questões por avaliação; planejamento canônico publicado em 2026-09-30 (PR #7); execução LOCAL autorizada em 2026-10-01 (`DEC-AV-028`) em branch dedicada `feat/av-s04-multiplas-questoes`; implementação concluída e revisada LOCALMENTE em 2026-10-01 (revisão independente final **APROVADO**, 3ª rodada, após 2 rodadas de REPROVADO com correções objetivas); sem commit/push/merge — integração ao histórico Git pendente de autorização explícita separada | [documento da sprint](sprints/sprint_AV-S04_multiplas_questoes.md) |
| Preparação operacional integrada, P4 executado e DEBT-AV-011 resolvido | `AV-OPER-001` — atualização de `avalia_dev`: saneamento de duplicatas + 3 migrações pendentes integrados a `main` via PR #10 (merge commit `9310b54`, CI pós-merge verde); **P4 (execução real) executado em 2026-10-02 contra a instância LOCAL de `avalia_dev`** — saneamento aplicado, 3 migrações aplicadas (`version_num=a9f4c2e71b06`), todos os pós-checks (a)-(g) confirmados, nenhuma falha; reconciliação de contagens e conservação de dados confirmadas; `DEBT-AV-011`/`BL-AV-1-10` **resolvidos** (numerador 14→15); **P5 (ativação de flags) permanece NÃO autorizado/NÃO executado** | [snapshot de execução real](snapshots/snapshot_EXEC-2026-10-02-01_execucao-real-p4-avalia-dev.md) |
| Execução documental ativa | GOV-005 | [snapshot](snapshots/snapshot_EXEC-2026-09-23-02_GOV-005.md) |
| Trilha proposta (não aprovada, exceto AV-S01) | "Operação de uma turma" (5 fases, com Etapa 4B — entrada por imagem priorizada sobre CSV) | [documento da trilha](backlog/trilha_operacao_de_turma.md) §11 |

## 3. Estado por componente

| Componente | Implementação observada | Validação atual nesta execução | Fonte |
|---|---|---|---|
| Core API | BL-AV-2-03 (autorização por vínculo professor–turma) tecnicamente concluído e aprovado sem ressalvas após 3 rodadas de revisão independente; estrutura acadêmica da AV-S03 homologada por Rafael (`DEC-AV-026`/`DEC-AV-027`) e **integrada a `main`** via PR #3 (`c391865`) | revisão independente: focal 20/20 e Core 68/68 em duas execuções consecutivas; confirmação local final: Core 68/68, 12 warnings, Ruff `All checks passed!`; SQLite temporário + FastAPI `TestClient` | [última execução](snapshots/latest_execution.md) |
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
| BL-AV-2-03 (encerramento local) | autorização por vínculo professor–turma | tecnicamente concluído; todos os achados das 3 rodadas corrigidos sem regressão | terceira revisão cruzada independente e adversarial pelo Antigravity: **APROVADO SEM RESSALVAS**; focal 20/20; Core 68/68 duas vezes; confirmação Codex: Ruff limpo e Core 68/68 | **homologado tecnicamente por Rafael (`DEC-AV-026`, 2026-09-28) e, junto da entrega completa da AV-S03, integrado a `main` via PR #3 (`DEC-AV-027`, 2026-09-29)** |

**Trilha proposta "Operação de uma turma":** 8 etapas + 1 sub-etapa (4B), 3 marcos, lidos em 5 fases de execução desde GOV-004 (§11 da trilha), 19 sprints propostas (AV-S01 a AV-S13 e AV-S05B a AV-S10B). `AV-S01`, `AV-S02`, `AV-S03` e `AV-S04` foram homologadas e integradas a `main`; `AV-S05B` parcialmente executada (investigação experimental, texto impresso medido, manuscrito pendente); `AV-S05` permanece apenas planejada, sem nenhuma evidência de execução localizada nas fontes inspecionadas (ver GOV-006); as demais 14 sprints permanecem não autorizadas.

Progresso funcional desta trilha: **22 de 70 itens homologados e integrados** — o denominador é o backlog canônico em [`backlog/backlog_tecnico_avalia.md`](backlog/backlog_tecnico_avalia.md). Numerador nominal (cada item conta uma vez, homologação + integração comprovadas, sem inferir uma da outra):

| # | ID | Homologação | Integração | Observação |
|---|---|---|---|---|
| 1 | `BL-AV-1-01` | AV-S01, `DEC-AV-003` (2026-09-23) | PR #1 (`main`) | — |
| 2 | `BL-AV-1-02` | AV-S01, `DEC-AV-003` (2026-09-23) | PR #1 (`main`) | — |
| 3 | `BL-AV-1-03` | AV-S01, `DEC-AV-003` (2026-09-23) | PR #1 (`main`) | — |
| 4 | `BL-AV-1-04` | AV-S01, `DEC-AV-003` (2026-09-23) | PR #1 (`main`) | — |
| 5 | `BL-AV-1-07` | AV-S01, `DEC-AV-003` (2026-09-23) | PR #1 (`main`) | validação com IA simulada, sem alegação de inferência real |
| 6 | `BL-AV-1-08` | AV-S01, `DEC-AV-003` (2026-09-23) | PR #1 (`main`) | — |
| 7 | `BL-AV-1-05` | `DEC-AV-022` (2026-09-24) | PR #1 (`main`) | `DEBT-AV-004` resolvido sem ressalva |
| 8 | `BL-AV-1-06` | `DEC-AV-022` (2026-09-24) | PR #1 (`main`) | `DEBT-AV-005` resolvido sem ressalva; CI remota 3/3 verde |
| 9 | `BL-AV-1-09` | `DEC-AV-022` (2026-09-24) | PR #1 (`main`) | `DEBT-AV-009` resolvido |
| 10 | `BL-AV-2-01` | `DEC-AV-027` (2026-09-29, entrega funcional completa da AV-S03) | PR #3 (`main`, merge `c391865`) | — |
| 11 | `BL-AV-2-02` | `DEC-AV-027` (2026-09-29) | PR #3 (`main`) | migração `c4a8b2d91e37`, guard de downgrade testado; aplicação operacional real a `avalia_dev` confirmada em 2026-10-02 (P4) |
| 12 | `BL-AV-2-03` | `DEC-AV-026` (2026-09-28, técnica) + `DEC-AV-027` (2026-09-29, integração) | PR #3 (`main`) | 3 rodadas de revisão adversarial, APROVADO SEM RESSALVAS |
| 13 | `BL-AV-2-04` | `DEC-AV-027` (2026-09-29) | PR #3 (`main`) | `DEBT-AV-012` (dupla configuração de flag) aceito como débito residual — não bloqueia a homologação já concedida |
| 14 | `BL-AV-2-05` | `DEC-AV-027` (2026-09-29, marco da sprint) | PR #3 (`main`) | 12/12 critérios de aceite da AV-S03 executados e confirmados |
| 15 | `BL-AV-1-10` | Código: `DEC-AV-022` (2026-09-24). Migração operacional: Rafael (2026-10-02, autorização P4 explícita, execução exclusiva no banco local `avalia_dev`) | PR #1 (`main`, código); migração `7b1d6d853f20` aplicada operacionalmente em 2026-10-02 | `DEBT-AV-011` resolvido: `UniqueConstraint uq_human_reviews_job_id` confirmada presente em `avalia_dev` por `pg_get_constraintdef` nesta sessão. Reconciliação de contagens e conservação de dados em `evidence/AV-OPER-001-avalia-dev-preparacao/P4-execucao-real-2026-10-02/06_reconciliacao_contagens.md`. Execução restrita à instância **local** de `avalia_dev` (não produção remota) |
| 16 | `BL-AV-3-01` | Código: `DEC-AV-029` (2026-10-01, homologação da entrega funcional de AV-S04, AC-01/AC-02 cumpridos, `sprint_AV-S04...md` §10-11). Migração operacional: Rafael (2026-10-02, autorização P4) | PR #9 (`main`, merge `9ab6e43`, verificado `MERGED` nesta sessão); migração `a9f4c2e71b06` aplicada operacionalmente em 2026-10-02 como parte da mesma cadeia de P4 | **Incluído no numerador nesta rodada** — critério de Rafael: entrega já homologada (`DEC-AV-029`) não deve ficar fora do progresso global só por a migração operacional ter sido tratada em rodada separada (P4); ambas as condições agora comprovadas |
| 17 | `BL-AV-3-02` | Código: `DEC-AV-029` (AC-03/04/05/06 cumpridos). Migração operacional: Rafael (2026-10-02) | PR #9 (`main`, merge `9ab6e43`); migração `a9f4c2e71b06` aplicada | Idem linha 16 |
| 18 | `BL-AV-3-03` | Código: `DEC-AV-029` (AC-07/08 cumpridos). Migração operacional: Rafael (2026-10-02) | PR #9 (`main`, merge `9ab6e43`); migração `a9f4c2e71b06` aplicada | Idem linha 16 |
| 19 | `BL-AV-3-04` | Código: `DEC-AV-029` (AC-09 cumprido — contrato OpenAPI atualizado, não depende de migração) | PR #9 (`main`, merge `9ab6e43`) | Idem linha 16, exceto que este item não depende de migração operacional — já estava tecnicamente completo desde a integração do PR #9 |
| 20 | `BL-AV-4B-03` | `DEC-AV-036` (2026-10-14, backend/API) + reconciliação `DEC-AV-042`/`RECONCILIACAO-2026-10-14-01` (2026-10-14, interface ponta a ponta) | PR #15 (`main`, merge `b818961`) + PR #18 (`main`, merge `efaa337`, interface) | **Incluído no numerador nesta rodada** — a dependência que bloqueava (`DEC-AV-036`: interface ponta a ponta ausente) está satisfeita desde a integração do PR #18; critério canônico avaliado pelo texto literal, não pela sprint originalmente mapeada |
| 21 | `BL-AV-4B-04` | `DEC-AV-036` (2026-10-14) + reconciliação `DEC-AV-042` (2026-10-14) | PR #15 (`main`, merge `b818961`) + PR #18 (`main`, merge `efaa337`) | Idem linha 20 |
| 22 | `BL-AV-4B-14` | Vínculo: `DEC-AV-036`/`038` (AV-S06B). Bloqueio de correção: `DEC-AV-041` (AV-S08B). Reconciliação: `DEC-AV-042`/`RECONCILIACAO-2026-10-14-01` (2026-10-14) | PR #15/#16 (`main`, vínculo) + PR #18 (`main`, merge `efaa337`, bloqueio) | **Incluído no numerador nesta rodada** — critério canônico (vínculo + bloqueio de correção antes da confirmação) integralmente atendido pela combinação AV-S06B + AV-S08B, antecipando o mapeamento de sprint original (`AV-S09B`), sem alterar o critério nem contar duas vezes |

**Nota sobre `BL-AV-3-01` a `04` (correção desta rodada, 2026-10-02):** a rodada anterior desta reconciliação (nota abaixo) excluiu esses 4 itens do numerador, tratando a aplicação operacional da migração `a9f4c2e71b06` como "fora de escopo da rodada de P4". Rafael corrigiu esse raciocínio: a entrega funcional de AV-S04 já estava homologada por `DEC-AV-029` e integrada via PR #9 (`main`, merge `9ab6e43`, confirmado `MERGED` por `gh pr view 9` nesta sessão, não presumido); "fora do escopo desta rodada" não é motivo para excluir uma entrega já homologada do progresso global, e a migração `a9f4c2e71b06` foi de fato aplicada operacionalmente como parte da mesma cadeia de P4 (ela depende de `c4a8b2d91e37`, aplicada na mesma transação de `alembic upgrade head`). Os 4 itens são incluídos agora.

**Nota sobre `BL-AV-4B-03`/`04`/`14` (reconciliação 2026-10-14, `DEC-AV-042`/`RECONCILIACAO-2026-10-14-01`):** por instrução explícita de Rafael, a reavaliação foi feita pelo critério canônico, não pelo número da sprint. `BL-AV-4B-03`/`04` tinham a homologação de backend concedida (`DEC-AV-036`), mas ficavam fora do numerador por depender de uma interface ponta a ponta que não existia; essa interface passou a existir e a estar integrada com o PR #18 (AV-S08B). `BL-AV-4B-14` estava mapeado para a sprint `AV-S09B`, mas seu critério (vínculo + bloqueio de correção antes da confirmação) foi integralmente satisfeito antes disso, pela combinação de AV-S06B e AV-S08B — o mapeamento de sprint é planejamento, não critério de aceite. Nenhum dos três foi contado antes; nenhum critério foi alterado para viabilizar a inclusão. Em contraste, `BL-AV-4B-10`/`11`/`13`/`15` permanecem fora do numerador porque seus critérios literais (texto **extraído**, fallback após falha de **extração**, elo de **execução OCR**) dependem de capacidades (`BL-AV-4B-07`/`08`, OCR) que ainda não existem — isso não é uma questão de sprint, é ausência real do requisito.

**Indicador separado de itens parciais (fora do numerador, sem ponderação percentual):**

| ID | Situação |
|---|---|
| `BL-AV-4B-01` | levantamento documental concluído (texto impresso e manuscrito); não homologado como decisão arquitetural |
| `BL-AV-4B-20` | benchmark parcialmente executado (texto impresso medido; manuscrito pendente, sem evidência de coleta localizada) |
| `BL-AV-4B-10` | tela de conferência entregue como imagem + rascunho MANUAL (PR #18); critério fala em "texto extraído" — falta extração automática (OCR) |
| `BL-AV-4B-11` | edição/confirmação manual entregue (PR #18); sem OCR não existe "bruto extraído" distinto do digitado |
| `BL-AV-4B-13` | transcrição manual entregue, homologada e integrada (PR #18); acionamento como fallback após falha de extração NÃO comprovado — extração/OCR ainda não existe |
| `BL-AV-4B-15` | imagem e transcrição confirmada→correção→revisão entregues; falta o elo de execução OCR |

Nenhum outro percentual de conclusão é publicado. Maturidade técnica: **não medida**; não existe rubrica AvalIA aprovada.

*(Nota de reconciliação, 2026-09-30, auditoria GOV-006, segunda rodada: a contagem apresentada na primeira rodada desta auditoria (15/70) continha um erro aritmético — o numerador anterior à AV-S03 já havia sido corrigido de 7 para 9 em 2026-09-28 (ver §2 da GOV-006 sobre a origem dessa divergência entre checkouts), não 10; 9 + 5 itens da AV-S03 = **14**, não 15. Corrigido nesta rodada com a lista nominal acima, excluindo explicitamente `BL-AV-1-10` do numerador por seu débito operacional aberto. Base usada: worktree `avalia-plataform-worktrees/av-s03-work`, `main` HEAD `a5974b1`.)*

*(Nota de reconciliação, 2026-10-02: `BL-AV-1-10` movido do indicador de itens parciais para o numerador — 14→15 — após a execução real e validada de P4 contra `avalia_dev` (autorização explícita de Rafael, execução restrita ao banco local). O número "15/70" desta nota coincide numericamente com o "15/70" citado como erro aritmético na nota de 2026-09-30, mas tem causa e composição inteiramente diferentes — não é uma repetição do erro anterior, é um novo total correto após a resolução genuína de `BL-AV-1-10` nesta data. IDs explicitamente listados acima; nenhum numerador presumido.)*

*(Nota de reconciliação, 2026-10-14, `DEC-AV-042`/`RECONCILIACAO-2026-10-14-01`: 19→22, após avaliar `BL-AV-4B-03`/`04`/`14` pelo critério canônico em vez de pela sprint originalmente mapeada — ver linhas 20-22 da tabela acima e a nota correspondente. `BL-AV-4B-10`/`11`/`13`/`15` movidos para este indicador de parciais, com a correção explícita de que `BL-AV-4B-13` havia sido descrito como "coberto integralmente" em `DEC-AV-041` e nos snapshots EXEC-2026-10-14-09/10/11 — texto corrigido aqui, sem reabrir a homologação/integração do PR #18. IDs explicitamente listados; nenhum numerador presumido.)*

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
| Regularizar o estado de `AV-S03` e homologar sua entrega | Rafael revisar a entrega funcional completa da sprint e decidir sobre homologação e integração | **homologada e integrada (2026-09-29)** — `DEC-AV-027`, merge commit `c391865` a `main`, CI remota 3/3 jobs verdes (run [36541693375](https://github.com/rafaelinfopiaui/avalia-platform/actions/runs/36541693375)); `DEBT-AV-012` aceito como débito residual |
| Decidir saneamento das duplicatas legadas de revisão humana (`DEBT-AV-011`) | Rafael decidir sobre a proposta de saneamento (backup, classificação equivalente/conflitante, preservação por arquivo em vez de exclusão) apresentada em `backlog/proposta_saneamento_human_reviews_duplicadas.md` | pendente — proposta apresentada em 2026-09-24, não executada |

## 9. Política de atualização

Atualizar este dashboard ao fim de cada execução/fatia. Todo resultado deve apontar para sprint, snapshot ou evidência. Implementação e validação permanecem separadas; indicadores sem método e denominador ficam “não medido”.

## 10. AV-S03B — módulo acadêmico coerente (2026-10-13/14, execução local em 2 rodadas)

**Não incluído no numerador de 19/70** — `AV-S03B` é um item de robustez
estrutural (resolução de `DEBT-AV-012`/`DEBT-AV-013`), não um item numerado
do backlog canônico `BL-AV-*`. Resumo:

- **Rodada 1 (2026-10-13):** implementado e validado localmente — endpoint
  de capacidades (fonte única de verdade), guardas fail-closed em
  menu/rota/editor, seed fictício idempotente, fluxo completo
  estrutura→avaliação→resposta→correção→revisão em banco isolado (IA
  simulada). 10/10 critérios de aceite avaliados; achado real BLOQUEANTE
  encontrado pela auditoria pontual do Codex (janela de `loading` tratada
  como "desligado") e corrigido na mesma sessão; revisão independente do
  Antigravity: APROVADO COM RESSALVAS (ACH-01, não bloqueante).
- **Rodada 2 (2026-10-14, saneamento dirigido):** Rafael apontou 4 lacunas
  após revisão do relatório da rodada 1 — (1) distinguir "configuração
  desconhecida" de "erro definitivo" (a correção do Codex na rodada 1
  cobriu só a janela de `loading`, não a falha definitiva); (2) resolver
  ACH-01 (UI bloqueava edição/publicação de rascunho legado quando o
  backend não exigia); (3) concluir a retirada de
  `VITE_ACADEMIC_MODULE_ENABLED`; (4) corrigir a precisão das evidências e
  do planejamento registrados. Todas as 4 lacunas saneadas, com evidência
  de integração real (não só leitura de código) e validação visual em
  navegador real. Suíte final: **110 passed** (108 + 2 parametrizados do
  teste de legado). Revisão independente — rodada 2 (Antigravity, escopo
  limitado ao delta): **APROVADO**, zero achados bloqueantes. Codex não
  dispachado nesta rodada (nenhum risco concreto novo).
- `avalia_dev` e `avalia_apresentacao_demo_20261002` verificados intactos
  ao final de ambas as rodadas (mesmas contagens e `version_num`).
- **Ainda não publicado** — branch local `feat/av-s03b-modulo-academico-coerente`,
  sem commit/push, pendente de decisão de Rafael.
- evidência completa:
  [`sprint_AV-S03B_modulo_academico_coerente.md`](sprints/sprint_AV-S03B_modulo_academico_coerente.md),
  [`snapshot_EXEC-2026-10-13-02_abertura_av-s03b.md`](snapshots/snapshot_EXEC-2026-10-13-02_abertura_av-s03b.md)
  (Adendo 2 descreve a rodada 2), `evidence/AV-S03B/`.

## 11. AV-S06B — recebimento/armazenamento de imagens (2026-10-14, execução local, backend/API)

**Não altera o numerador de 19/70** — entrega técnica local, ainda não
homologada. Escopo: itens `BL-AV-4B-03/04/05` (recebimento, armazenamento
privado e recuperação autorizada de imagens de resposta), **somente
backend/API**. Resumo:

- **Implementação (Claude Code, executor principal):** modelo `AnswerImage`,
  migração `answer_images`, router com 3 endpoints (upload, listar, download),
  validação de conteúdo real via Pillow, nome em disco gerado pelo servidor
  (UUID), escrita atômica com rollback, download sempre autenticado, nenhum OCR,
  nenhuma correção automática, logs só com IDs/metadados. O executor não
  conseguiu rodar nada no ambiente dele (permissões) — entregou com os AC
  marcados como "não validado".
- **Correção pontual de defeito real (Hermes):** `KeyError('MPO')` no Pillow
  12.x (passar `"MPO"` em `Image.open(formats=[...])`) quebrava 100% dos uploads
  válidos. Corrigido separando a lista de formatos de abertura do dicionário de
  MIME. Validado e revisado como correto/sem regressão.
- **Verificação independente (Hermes, execução real):** suíte **136 passed, 0
  failed** (110 pré-existentes + 26 novos = 24 funções, 1 parametrizada ×3);
  `ruff check app` limpo; validação real em PostgreSQL isolado + Core via HTTP —
  11/11 checks reais (AC-01 a AC-10 com evidência distinguida por critério na §8
  da sprint: HTTP real / teste automatizado / inspeção).
- **Revisão independente (Antigravity, Gemini 3.8 Flash High — família diferente
  do executor):** **APROVADO**. Execução própria (não reutilizou resultados do
  Hermes): 136 passed, banco isolado próprio, HTTP real, inspeção de segurança
  CONFIRMADO SEGURO em todas as dimensões (path traversal, autorização,
  validação de conteúdo, limite, órfãos, exposição pública, OCR zero, logs).
- **Não entregue nesta fatia:** interface de upload no frontend (backend/API
  apenas; sem validação visual); exclusão de imagens (proposta de política, não
  funcionalidade — sem endpoint nem procedimento).
- **Achados não-bloqueantes (registrados, não tratados para não ampliar escopo):**
  ruff I001 na migração (padrão preexistente em 4 migrações do projeto);
  deprecation de `class Config` no Pydantic V2 (padrão dos schemas existentes).
- **Decisões pendentes de Rafael:** formato/tamanho/retenção/exclusão — propostas
  restritas ao ambiente isolado, não aprovações (ver tabela em `evidence/AV-S06B/`).
- `avalia_dev` e `avalia_apresentacao_demo_20261002` verificados intactos
  (`a9f4c2e71b06`, 16 human_reviews) antes e depois; bancos isolados de
  verificação dropados ao final.
- **Ainda não publicado** — branch local
  `feat/av-s06b-recebimento-armazenamento-imagens`, sem commit/push, pendente de
  decisão de produto + publicação + homologação.
- evidência completa:
  [`sprint_AV-S06B_recebimento_armazenamento_imagens.md`](sprints/sprint_AV-S06B_recebimento_armazenamento_imagens.md),
  [`snapshot_EXEC-2026-10-14-02_execucao_av-s06b.md`](snapshots/snapshot_EXEC-2026-10-14-02_execucao_av-s06b.md),
  `evidence/AV-S06B/` (prompt de execução, parecer independente do Antigravity,
  tabela de decisões, pacote recuperável com checksums).

### 11.1 Complemento — Resposta por imagem (sub-fatia, DEC-AV-037, rodada local)

- escopo: resolver a lacuna contratual identificada na homologação do backend —
  a foto passa a ser a entrada inicial da resposta, sem texto digitado/vazio/fictício;
  correção bloqueada até transcrição confirmada pelo professor;
- modelo/contrato: `Answer.text` nullable + `source` (TEXT/IMAGE) +
  `transcription_status` (AGUARDANDO_TRANSCRICAO/TRANSCRICAO_CONFIRMADA) +
  CheckConstraint; migração com backfill determinístico (legadas -> TEXT/CONFIRMADA);
  endpoint transacional `POST /v1/answers/image`; guard em `request_correction`
  (422 `ANSWER_NOT_TRANSCRIBED`) + defesa em profundidade em `run_correction_job`;
  reuso do backend de imagens homologado (sem ampliar sua homologação);
- interface: tela de resposta por foto (seleção manual dos vínculos, upload
  JPEG/PNG até 10 MiB, estados de carregando/sucesso/erro, listagem e visualização
  por download autenticado, aviso de que a resposta aguarda transcrição e não foi
  corrigida); fluxo textual existente preservado;
- validação: suíte 158 passed (136 + 22, zero regressão); ruff app limpo;
  build+eslint frontend limpos; PostgreSQL isolado (migração/backfill/
  CheckConstraint/downgrade protegido) e HTTP real (upload 201, correção bloqueada
  422 com 0 jobs, 401/403, textual 201/202, download bit-a-bit idêntico);
  desenho revisado antes do código e implementação revisada de forma independente
  pelo Antigravity (ambas aprovadas);
- NÃO entregue nesta fatia: OCR/transcrição/confirmação (a resposta por imagem
  termina legitimamente em "aguardando transcrição"); `BL-AV-4B-05` (retenção/
  exclusão) permanece pendente;
- validação visual (ACI-08) em navegador real: **9/10 cenários PASS**; 1 ressalva
  (estado preservado no backend, mas a tela não reexibe após recarregar) registrada
  como **débito de UX** por decisão de Rafael, sem alteração de código;
- Git: rodada LOCAL — sem stage/commit/push/merge; branch
  `feat/av-s06b-resposta-por-imagem`;
- progresso homologado: permanece **19/70** (esta rodada não altera o numerador;
  homologação pendente);
- evidência: `DEC-AV-037` em [`decisions.md`](registers/decisions.md); sprint §17;
  [`snapshot_EXEC-2026-10-14-03`](snapshots/snapshot_EXEC-2026-10-14-03_abertura_resposta_por_imagem.md)
  e [`snapshot_EXEC-2026-10-14-04`](snapshots/snapshot_EXEC-2026-10-14-04_encerramento_resposta_por_imagem.md);
  `evidence/AV-S06B/` (desenho, pareceres de revisão do desenho e da implementação,
  prompt de execução).

### 11.2 Fatia DEBT-AV-014 — Retomada de respostas por imagem (rodada local)

- escopo: resolver o débito registrado em `technical_debts.md` (`DEBT-AV-014`) e a
  ressalva do cenário 5 de `validacao_visual_resposta_por_imagem.md` — a tela de
  resposta por foto passa a retomar/listar, após recarregar (F5) e em nova sessão,
  as respostas por imagem já persistidas no backend, sem exigir reenvio;
- contrato: `GET /v1/assessments/{id}/image-answers?question_id=<opcional>`,
  SOMENTE leitura, autorizado por **propriedade** (`_get_owned_assessment`, mesmo
  padrão de `get_assessment`/`list_assessments`) — explicitamente SEM
  `require_assessment_mutation` nem `require_active_class_link`, porque é leitura
  histórica e o professor dono deve continuar consultando mesmo sem vínculo ativo
  de turma; questão inexistente ou de outra avaliação -> 404; não-dono -> 403; sem
  token -> 401; `storage_filename` nunca exposto (reuso de `AnswerImageOut`);
- interface: `ImageAnswerPage.tsx` busca os persistidos ao selecionar/trocar
  avaliação ou questão (inclusive ao montar com `?avaliacao=`), une com os envios
  da sessão sem duplicar (dedupe por `answer.id`), limpa a seleção anterior antes
  de buscar (guard de corrida com contador de requisição), e trata estados de
  carregando/vazio/erro-com-repetir; nenhuma ação de correção/nota/IA introduzida;
- validação: suíte **171 passed** (158 + 13 novos; zero regressão), `ruff app`
  limpo, build+tsc do frontend limpos; HTTP real em PostgreSQL isolado cobrindo
  ACD-01 a ACD-05 e ACD-09 (incluindo **ACD-04 leitura histórica**: avaliação com
  `class_group_id` e dono com ZERO `ProfessorClassLink` -> 200); navegador real em
  **2 rodadas independentes com ambientes isolados próprios distintos** (Hermes e
  Antigravity) cobrindo os 5 pontos pedidos por Rafael: retomada em nova sessão,
  retomada após reload, bloqueio 403 para outro professor (inclusive contra
  sondagem por `question_id`), troca de avaliação/questão sem reter dados
  anteriores, e correção ainda bloqueada (422 `ANSWER_NOT_TRANSCRIBED`; para a
  resposta histórica sem vínculo de turma ativo, mutação continua barrada por 403);
- revisão independente: **Antigravity — APROVADO (2026-10-14T08:45), sem defeitos
  bloqueantes**, execução 100% própria em ambiente isolado descartável distinto do
  usado pelo Claude Code e pelo Hermes (parecer completo em
  `evidence/AV-S06B/revisao_debt_014_antigravity.md`);
- integridade: `avalia_dev` (a9f4c2e71b06, 16 `human_reviews`, 29 `answers`) e
  `avalia_apresentacao_demo_20261002` (a9f4c2e71b06, 10 `answers`) auditados
  intactos antes e depois, em ambas as rodadas de verificação independente;
- NÃO entregue nesta fatia: OCR, transcrição manual ou automática, confirmação,
  exclusão/retenção (`BL-AV-4B-05` segue pendente), qualquer ativação operacional;
- Git: rodada LOCAL — sem stage/commit/push/merge; branch
  `feat/av-s06b-debt-014-retomada-respostas-imagem` (base `main` em
  `cf81109655713fac856aab0b26ba36e1bb5f15bc`, SHA do merge do PR #16/DEC-AV-038,
  incorporado ao registro documental desta branch — ver Adendo 2 em
  `snapshot_EXEC-2026-10-14-04` — sem qualquer commit direto em `main`);
- progresso homologado: permanece **19/70** (esta rodada não altera o numerador;
  homologação/publicação pendente de decisão de Rafael);
- evidência: `DEBT-AV-014` em [`technical_debts.md`](registers/technical_debts.md);
  [`snapshot_EXEC-2026-10-14-05`](snapshots/snapshot_EXEC-2026-10-14-05_abertura_debt_014.md)
  e [`snapshot_EXEC-2026-10-14-06`](snapshots/snapshot_EXEC-2026-10-14-06_encerramento_debt_014.md)
  (§5 veredito do Antigravity, §5.1 verificação adicional independente do Hermes);
  `evidence/AV-S06B/` (desenho `desenho_debt_014_retomada.md`, prompt de execução,
  verificação do Hermes, parecer do Antigravity).

## 12. AV-S08B — transcrição manual e confirmação humana (2026-10-14, fatia MANUAL, publicada em PR rascunho)

**Não altera o numerador de 19/70** — entrega técnica publicada em PR
rascunho, ainda não homologada. Escopo: parte MANUAL (sem OCR) de
`BL-AV-4B-13`/`14` (cobertos integralmente) e `BL-AV-4B-10`/`11`/`15`
(cobertos parcialmente — falta a parte de OCR). Resumo:

> **Correção de registro (2026-10-14, `DEC-AV-042`/`RECONCILIACAO-2026-10-14-01`):**
> a frase acima ("`BL-AV-4B-13`/`14` cobertos integralmente") estava
> imprecisa e é preservada aqui apenas como registro histórico do texto
> publicado nesta rodada; ver §4 (numerador) e a nota de reconciliação da
> tabela nominal acima para o estado corrigido: `BL-AV-4B-14` foi de fato
> comprovado integralmente (pela combinação com AV-S06B) e passou ao
> numerador; `BL-AV-4B-13` permanece PARCIAL — a transcrição manual está
> entregue, homologada e integrada, mas o acionamento como fallback após
> falha de extração não foi comprovado (a extração/OCR ainda não existe).

- decisões de produto aprovadas em `DEC-AV-040`: rascunho único atual
  (DP-1), confirmação definitiva nesta fatia sem reabertura (DP-2),
  idempotência/conflito sem disparo automático de correção (DP-3), e
  controle de concorrência explícito por versão;
- backend: migração aditiva (`f2a9c4e6b1d3`, +4 colunas nullable/default em
  `Answer`, downgrade bloqueado se houver dado não-default); 2 endpoints de
  mutação (`PATCH .../manual-transcription/draft`,
  `POST .../manual-transcription/confirm`), lock otimista por
  `transcription_version` via UPDATE condicional em transação (mesmo padrão
  de `Rubric.version`); histórico via `AuditEvent` preservando autoria e
  origem MANUAL; nunca dispara `request_correction` nem cria
  `CorrectionJob` a partir destes 2 endpoints;
- delta posterior, dentro do mesmo escopo autorizado (sem nova decisão de
  produto): botão "Solicitar análise da IA" na tela de resposta por foto,
  visível só após confirmação, reaproveitando `requestCorrection` já
  existente (zero endpoint novo);
- validação: suíte **204 passed, 5 skipped** (zero regressão; os 5 skipped
  são testes de concorrência real contra PostgreSQL — **executados
  localmente pelo autor e por 2 rodadas de revisão independente; a CI atual
  deste repositório não define `AVALIA_TEST_POSTGRES_URL` e os pula**,
  candidato a melhoria de infraestrutura, fora de escopo); `ruff`/`tsc`/
  `build`/`lint` limpos; identidade de conteúdo integral do texto enviado à
  IA comprovada por teste automatizado (comparação exata, não por
  coincidência de tamanho); validação de integração completa (foto →
  rascunho → confirmação → correção → revisão humana final) com **AI
  Engine real em modo simulado explícito**, distinto de inferência real;
- revisão independente: **Antigravity — 4 rodadas** — plano técnico (2x,
  APROVADO COM RESSALVAS cada), implementação completa (APROVADO COM
  RESSALVAS DOCUMENTAIS, sem achado bloqueante), delta de correção
  (APROVADO, sem ressalva bloqueante — revisão restrita ao delta, sem
  reabrir a auditoria geral);
- integridade: `avalia_dev` (a9f4c2e71b06, 16 `human_reviews`) e
  `avalia_apresentacao_demo_20261002` (a9f4c2e71b06) auditados intactos
  antes e depois de toda a execução, em múltiplas rodadas de verificação
  independente;
- NÃO entregue nesta fatia: OCR, extração automática, reabertura
  pós-confirmação, múltiplos rascunhos concorrentes selecionáveis, qualquer
  ativação operacional;
- Git: **publicado em PR rascunho, homologado e integrado** por merge
  commit `efaa337c04070f59e01d217010f17a92b89258ca` (`DEC-AV-041`), branch
  `feat/av-s08b-transcricao-manual` preservada, CI pós-merge 3/3 pass,
  checkout principal atualizado para `main` por fast-forward
  (histórico completo em `snapshot_EXEC-2026-10-14-11`);
- progresso homologado: **22/70** após reconciliação por critério canônico
  (`DEC-AV-042`/`RECONCILIACAO-2026-10-14-01`, 2026-10-14) — `BL-AV-4B-14`
  (bloqueio de correção, entregue nesta fatia) entrou no numerador junto
  com `BL-AV-4B-03`/`04` (AV-S06B, reavaliados na mesma rodada);
  `BL-AV-4B-10`/`11`/`13`/`15` permanecem PARCIAIS, incluindo a correção
  explícita de que `BL-AV-4B-13` NÃO está coberto integralmente (ver nota
  acima);
- evidência: `sprint_AV-S08B_transcricao_manual_confirmacao_humana.md`;
  `evidence/AV-S08B/` (plano técnico, 2 pareceres de revisão do plano,
  prompts de execução, 2 pareceres de revisão da implementação/delta);
  [`snapshot_EXEC-2026-10-14-07`](snapshots/snapshot_EXEC-2026-10-14-07_abertura_av-s08b.md),
  [`snapshot_EXEC-2026-10-14-08`](snapshots/snapshot_EXEC-2026-10-14-08_encerramento_av-s08b.md),
  [`snapshot_EXEC-2026-10-14-09`](snapshots/snapshot_EXEC-2026-10-14-09_conclusao_escopo_av-s08b.md),
  [`snapshot_EXEC-2026-10-14-10`](snapshots/snapshot_EXEC-2026-10-14-10_publicacao_av-s08b.md),
  [`snapshot_EXEC-2026-10-14-11`](snapshots/snapshot_EXEC-2026-10-14-11_homologacao_integracao_av-s08b.md)
  e [`snapshot_RECONCILIACAO-2026-10-14-01`](snapshots/snapshot_RECONCILIACAO-2026-10-14-01_numerador-por-criterio.md)
  (reconciliação completa do numerador).
