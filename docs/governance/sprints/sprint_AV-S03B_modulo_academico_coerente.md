---
id: "AV-S03B"
status: planejada
objetivo_aprovado_por: Rafael (2026-10-13, nesta conversa)
consolidador: "Hermes"
baseline_entrada: "main HEAD 822570e (merge PR #13), working tree limpo"
---

# AV-S03B — Módulo acadêmico coerente e pronto para ativação

> Identificador escolhido por não renumerar nenhuma sprint existente (AV-S01 a
> AV-S05B já ocupadas) e por ser, em essência, um fechamento estrutural de débito
> da Etapa 2 (estrutura acadêmica, AV-S03), não uma nova etapa funcional da
> trilha. Segue o padrão de sufixo "B" já usado para a sub-linha de OCR
> (AV-S05B..AV-S10B), aqui aplicado a uma sub-entrega de robustez da Etapa 2.

## 1. Objetivo e valor esperado

Eliminar a causa raiz comum de `DEBT-AV-012` e `DEBT-AV-013` (duas fontes de
configuração do módulo acadêmico, sem fonte única de verdade) introduzindo um
endpoint de capacidades do backend consultado pelo frontend, estender a guarda
de `ACADEMIC_MODULE_ENABLED`/capacidade a `Layout.tsx` (menu) e `AcademicPage.tsx`
(rota), preservar integralmente autorização por vínculo, avaliações legadas e
histórico, e demonstrar o fluxo completo estrutura acadêmica → avaliação com
múltiplas questões → resposta → correção → revisão humana com dados fictícios
reproduzíveis e idempotentes em banco isolado. Resultado observável: módulo
acadêmico "coerente e pronto para ativação" — nenhuma rota/tela acessível
quando desligado (nem por omissão/falha de configuração), nenhuma regressão no
fluxo legado, prontidão documentada para uma decisão futura de ativação em
ambiente operacional (não incluída nesta sprint).

## 2. Origem

| Fonte/requisito | Trecho ou decisão aplicável | Link |
|---|---|---|
| `DEBT-AV-012` | dupla configuração de flag sem fonte única de verdade; solução recomendada pelo Codex (endpoint de capacidades) | [`technical_debts.md`](../registers/technical_debts.md) linha `DEBT-AV-012` |
| `DEBT-AV-013` | menu e `AcademicPage.tsx` não respeitam a flag | [`technical_debts.md`](../registers/technical_debts.md) linha `DEBT-AV-013` |
| Pedido desta conversa (2026-10-13) | autorização explícita de planejamento e implementação local desta fatia, com limites detalhados | corpo da conversa; registrado em `DEC-AV-032` |
| `DEC-AV-023`/`DEC-AV-027` | escolhas de domínio da AV-S03 (vínculo, avaliações legadas nullable, autorização por vínculo) — preservar sem alteração | [`decisions.md`](../registers/decisions.md) |

Lacunas de fonte: nenhuma — item já previsto como débito residual explícito,
não é requisito novo nem contraditório ao PRD.

## 3. Escopo

Incluído:
- endpoint `GET /v1/config/capabilities` no Core, fonte única de verdade,
  derivado diretamente de `settings.academic_module_enabled` (sem duplicar
  lógica), sem expor segredo;
- contexto de capacidades no frontend (`CapabilitiesContext`), substituindo o
  uso direto de `VITE_ACADEMIC_MODULE_ENABLED`/`isAcademicModuleEnabled()`
  como fonte de decisão de UI, com **falha/ausência de resposta tratada como
  módulo desligado** (fail-closed), nunca como ligado;
- guarda em `Layout.tsx` (ocultar item de menu "Gestão Acadêmica") e em
  `AcademicPage.tsx` (bloquear a rota/tela mesmo via acesso direto por URL)
  quando o módulo está desligado ou o estado da capacidade é desconhecido;
- preservação integral de `AssessmentEditorPage.tsx` (comportamento idêntico,
  agora lido do contexto em vez do env estático) e de toda a autorização por
  vínculo/avaliações legadas em `core/app/routers/academic.py` e `main.py`
  (nenhuma alteração funcional nessas regras);
- script de seed fictício, idempotente e reproduzível, restrito por guarda de
  nome de banco a um banco isolado novo (não `avalia_dev`, não
  `avalia_apresentacao_demo_20261002`), cobrindo o fluxo completo (estrutura
  acadêmica → avaliação multi-questão → resposta → correção → revisão humana)
  e incluindo uma avaliação legada (`class_group_id` nulo) para prova de
  preservação;
- testes automatizados do endpoint de capacidades e das guardas de frontend
  (na medida do que a suíte de frontend permitir sem introduzir framework
  novo não autorizado — ver débito registrado em `DEBT-AV-013`/sessão
  2026-10-13, ausência de suíte de frontend);
- validação real: módulo ligado/desligado, falha ao obter capacidades, acesso
  direto às rotas, perfis/vínculos autorizados e não autorizados, fluxo
  acadêmico completo, fluxo legado preservado, idempotência do seed — em
  PostgreSQL isolado e navegador real.

Fora de escopo (explicitamente, por limite desta rodada):
- qualquer escrita, seed ou ativação de `ACADEMIC_MODULE_ENABLED`/P5 em
  `avalia_dev`;
- deploy, promoção de baseline, dados reais de alunos;
- alteração do laboratório `avalia-github-lab`;
- stage/commit/push/merge;
- OCR/entrada por imagem, processamento em lote, revisão/resultados ampliados
  e avaliação da IA — tratados em sprints próprias futuras (ver §13 e
  resposta em chat sobre sequência restante);
- novo benchmark de OCR (AV-S05B permanece exatamente como está, parcial).

## 4. Baseline e estado de abertura

- último baseline validado: nenhum promovido sob esta governança;
- última execução registrada: `EXEC-2026-10-13-01` (diagnóstico) e seu Adendo 1
  (religamento de ambiente + fix `AnswerPage.tsx` + stage de `DEBT-AV-013`);
- commit/branch/upstream no início desta sprint: `main`, `up to date with
  origin/main`, HEAD `822570e` (merge PR #13);
- working tree no início desta sprint: limpo (`git status --short` vazio) —
  o fix de `AnswerPage.tsx` e o registro de `DEBT-AV-013` já foram integrados
  ao `main` via PR #13 antes desta sprint começar;
- dependências e bloqueantes: nenhum bloqueante novo; `BKL-AV-001` (CNE)
  continua aberto e não afeta esta sprint (uso exclusivo de dados fictícios).

## 5. Backlog e DoR

| ID | Descrição | Responsável | DoR | Estado |
|---|---|---|---|---|
| BL-AV-S03B-01 | Endpoint `GET /v1/config/capabilities` (backend, fonte única) | Claude Code | ready | planejado |
| BL-AV-S03B-02 | `CapabilitiesContext` + guarda em `Layout.tsx`/`AcademicPage.tsx`/`AssessmentEditorPage.tsx` (frontend) | Claude Code | ready | planejado |
| BL-AV-S03B-03 | Script de seed fictício idempotente, banco isolado novo, fluxo completo + caso legado | Claude Code | ready | planejado |
| BL-AV-S03B-04 | Testes automatizados (backend) + verificação manual documentada (frontend) | Claude Code | ready | planejado |
| BL-AV-S03B-05 | Revisão independente de código e contrato | Antigravity | ready | planejado |
| BL-AV-S03B-06 | Validação visual independente em navegador real | Antigravity | ready | planejado |
| BL-AV-S03B-07 | Auditoria pontual do risco "flag não substitui autorização / falha não habilita indevidamente" | Codex | ready | planejado |

## 6. Mapa de impacto

| Item | Criar | Alterar | Não tocar |
|---|---|---|---|
| BL-AV-S03B-01 | `core/app/routers/config.py` (novo) | `core/app/main.py` (`include_router`) | `core/app/routers/academic.py` (lógica de autorização existente) |
| BL-AV-S03B-02 | `frontend/src/context/CapabilitiesContext.tsx` | `frontend/src/services/api.ts`, `frontend/src/components/Layout.tsx`, `frontend/src/pages/AcademicPage.tsx`, `frontend/src/pages/AssessmentEditorPage.tsx`, `frontend/src/App.tsx` | `frontend/src/pages/AnswerPage.tsx`, `ReviewPage.tsx`, `CorrectionPage.tsx` |
| BL-AV-S03B-03 | `core/scripts/seed_academic_capability_demo.py` (novo) | nenhum script existente | `core/scripts/seed_academic_multi_question_demo.py` (preservado, não reaproveitado) |
| BL-AV-S03B-04 | `core/app/tests/test_capabilities.py` (novo) | nenhum teste existente | demais suítes |

Mudança fora do mapa exige registro prévio em Ajustes de Percurso (§14).

## 7. Delegação

| Item | Executor | Objetivo | Arquivos/escopo | Critérios | Limites | Evidência esperada |
|---|---|---|---|---|---|---|
| BL-AV-S03B-01..04 | Claude Code (CLI real, `claude -p`, branch dedicada no checkout principal) | implementar e testar localmente | ver mapa de impacto §6 | AC-01 a AC-10 (§8) | sem commit/push; sem tocar `avalia_dev`; sem alterar `avalia-github-lab` | diff completo + saída de testes + relatório |
| BL-AV-S03B-05/06 | Antigravity CLI (`agy -p`, somente leitura para revisão de código; navegador real para validação visual) | revisão independente + validação visual | diff produzido por Claude Code | aprovado/reprovado com citação arquivo:linha | não editar código; não substituir a validação visual do Hermes, complementar | parecer escrito + evidência visual |
| BL-AV-S03B-07 | Codex (`codex exec`, auditoria pontual) | auditar especificamente o risco "ausência/falha de config habilita indevidamente" e a separação flag≠autorização | endpoint de capacidades + pontos de enforcement no backend | achado BLOQUEANTE/NÃO BLOQUEANTE citado | auditoria pontual, não revisão geral do diff | parecer escrito |

Consolidação canônica: Hermes (orquestrador desta sessão), com verificação
independente própria antes de qualquer registro de "validado".

## 8. Critérios de aceite

> **Correção de precisão (2026-10-14, saneamento dirigido, lacuna 4 do
> Adendo 2 do snapshot):** a versão anterior desta seção afirmava "10/10
> critérios PASSARAM... nenhum critério ficou sem validação end-to-end", o
> que superestimava o tipo de evidência obtido para alguns itens (mistura
> testes unitários com integração real sob o mesmo rótulo "PASSOU") e a
> coluna "Método previsto" de AC-07 citava "Ollama real" desde o
> planejamento original, nunca corrigida após a execução real ter usado
> AI Engine em modo simulado. A tabela abaixo substitui a anterior,
> distinguindo explicitamente: **(auto)** = cobertura por teste
> automatizado; **(integ)** = chamada HTTP real contra um backend rodando;
> **(visual)** = observado em navegador real.

| ID | Critério | Evidência efetivamente produzida | Estado |
|---|---|---|---|
| AC-01 | `GET /v1/config/capabilities` retorna o valor real de `ACADEMIC_MODULE_ENABLED` do backend, sem duplicar lógica no frontend | (auto) `test_capabilities.py`, 3 testes, parametrizado true/false, dentro da suíte completa; (integ) `curl` real contra Core rodando, ambos os estados | **PASSOU** |
| AC-02 | Com módulo desligado, menu "Gestão Acadêmica" não aparece e `/academico` bloqueia acesso direto por URL | (visual) navegador real (Chrome dedicado via CDP), login real: menu ausente, acesso direto a `/academico` redireciona | **PASSOU** |
| AC-03 | Com módulo ligado, menu aparece e `/academico` funciona normalmente para perfis autorizados | (visual) navegador real: menu presente, página carrega, lista avaliações | **PASSOU** |
| AC-04 | Falha ao obter capacidades (endpoint indisponível/erro) e configuração **desconhecida** (carregando) resultam em comportamento fail-closed, nunca ligado; erro definitivo distinto de loading, com retry | (auto) nenhum teste de frontend automatizado (projeto sem framework de teste de frontend); (visual) navegador real nos 5 estados: loading, erro bloqueado via `Network.setBlockedURLs`, sucesso `true`, sucesso `false`, retry a partir do erro — todos observados diretamente, incluindo o clique real em "Tentar novamente" propagando a UI inteira (menu reaparece) | **PASSOU, em duas rodadas** — rodada 1 (achado do Codex) cobriu só a janela de `loading`; rodada 2 (saneamento, 2026-10-14) cobriu a falha **definitiva** (`error`), que a rodada 1 não distinguia de `loading` |
| AC-05 | Acesso direto a rotas do backend sob módulo desligado continua sujeito às mesmas regras de autorização por vínculo já existentes (nenhuma regressão) | (auto) `core/app/routers/academic.py` sem diff algum; suíte de autorização completa passando; (integ) criação sem turma com módulo desligado aceita (RASCUNHO), com módulo ligado rejeita (422) | **PASSOU** |
| AC-06 | Avaliações legadas (`class_group_id` nulo) continuam acessíveis e **editáveis** (não só listadas) pelo proprietário/admin, sem exigir turma, inclusive com o módulo acadêmico ligado | (auto) `test_legacy_draft_without_class_stays_editable_and_publishable_under_flag`, parametrizado true/false; (integ) `PATCH`/`publish` reais contra um rascunho legado com `ACADEMIC_MODULE_ENABLED=true`, 200 em ambos, `class_group_id` permanece `null`; (visual) edição completa de um rascunho legado pela UI (preenchimento de critério + clique em "Salvar rascunho"), sem bloqueio de turma, confirmado por leitura pós-salvamento no backend | **PASSOU, em duas rodadas** — rodada 1 cobriu apenas listagem/leitura (`GET`); rodada 2 (saneamento, resolve ACH-01) cobre mutação real (edição e publicação) |
| AC-07 | Fluxo completo estrutura acadêmica → avaliação multi-questão → resposta → correção → revisão humana funciona de ponta a ponta com o seed fictício, em banco isolado | (integ) banco isolado dedicado, Core real, **AI Engine em modo SIMULADO** (explicitamente rotulado `SIMULATED_MODE` na resposta) — login → listagem → resposta → correção → revisão humana `APPROVE`, `final_total=2.00` | **PASSOU — integração real com IA simulada nesta rodada.** Evidência anterior de inferência real via Ollama (sessão de 2026-10-05, registrada em `snapshot_EXEC-2026-10-13-01...md`) não foi reexecutada nem reproduzida nesta sprint; **não é atribuída a esta execução** |
| AC-08 | Seed é idempotente: executar duas vezes não duplica dados e a segunda execução relata `DEMO_SEED_ALREADY_VALID` (ou equivalente) | (integ) 1ª execução real: `DEMO_SEED_CREATED_AND_VALID`; 2ª execução real: `DEMO_SEED_ALREADY_VALID`, sem duplicar | **PASSOU** |
| AC-09 | Script de seed recusa explicitamente `avalia_dev` e `avalia_apresentacao_demo_20261002` (guarda de nome de banco) | (auto) `test_seed_capability_demo_guard.py`, 20 casos (travessia de path, credencial/query-string spoofing), dentro da suíte completa; (integ) execução real apontando para ambos os bancos protegidos, recusada com `RuntimeError` antes de qualquer `create_engine` | **PASSOU** |
| AC-10 | Perfis e vínculos autorizados/não autorizados preservam o comportamento já homologado em AV-S03 (professor dono, professor não-vinculado, admin, vínculo expirado) | (auto) suíte de autorização completa, inalterada; (integ) segundo professor (não vinculado) recebe 403 em avaliação acadêmica e em legada, lista vazia em `GET /v1/assessments` | **PASSOU** |

**Resumo corrigido:** 10/10 critérios PASSARAM. A evidência é mista por
critério — **não** uniformemente "automatizada E visual" como a versão
anterior desta tabela afirmava: AC-02/03 são evidência exclusivamente
visual (sem teste automatizado de frontend, por ausência de framework);
AC-04 e AC-06 tiveram sua primeira rodada incompleta (cobriam só parte do
estado — loading mas não erro definitivo; leitura mas não mutação) e só
alcançaram cobertura completa após uma segunda rodada de saneamento;
AC-07 usa IA simulada, não Ollama real. Nenhum critério ficou **sem**
evidência, mas o tipo de evidência varia e está explicitado acima, não
generalizado.

## 9. Definition of Done

- [ ] AC-01 a AC-10 avaliados com evidência real;
- [ ] mudanças vinculadas a `BL-AV-S03B-01..07`;
- [ ] validações com comando/data/ambiente/resultado;
- [ ] falhas e não executados visíveis;
- [ ] `DEBT-AV-012`/`DEBT-AV-013` com estado atualizado (resolvido ou
  parcialmente resolvido, sem inferir homologação);
- [ ] snapshot de encerramento criado;
- [ ] dashboard atualizado;
- [ ] closure gate preenchido;
- [ ] homologação de Rafael registrada somente se e quando ocorrer — esta
  sprint, por si, **não homologa nem integra nada**.

## 10. Validações previstas

| Item/AC | Comando ou procedimento | Ambiente | Tipo |
|---|---|---|---|
| AC-01 | `pytest core/app/tests/test_capabilities.py -v` | SQLite de teste | automatizada |
| AC-02/03/04 | navegador real (Chrome dedicado via CDP), login real, módulo ligado/desligado/falha simulada | banco isolado novo | visual |
| AC-05/06/10 | `pytest core/app/tests -q` (suíte completa) + chamadas HTTP diretas com tokens reais de perfis distintos | PostgreSQL isolado | automatizada + integração |
| AC-07 | fluxo HTTP completo encadeado (login → estrutura → avaliação → resposta → correção → polling → revisão) | PostgreSQL isolado + AI Engine (ver nota de precisão abaixo da tabela) | integração real |
| AC-08/09 | executar `seed_academic_capability_demo.py` duas vezes; tentar apontar para `avalia_dev`/`avalia_apresentacao_demo_20261002` e confirmar recusa | PostgreSQL isolado | automatizada |

> **Nota de precisão (2026-10-14):** a linha de AC-07 acima, escrita no
> planejamento original da sprint, citava "Ollama real" como ambiente. A
> execução real usou AI Engine em modo **simulado**, explicitamente
> rotulado na resposta (`SIMULATED_MODE`) — suficiente para validar o
> fluxo acadêmico (objetivo desta sprint), mas não uma revalidação de
> inferência real. Texto original preservado na linha acima como registro
> do planejamento; resultado real documentado em §8, AC-07.

## 11. Riscos e mitigação

| Risco | Probabilidade/impacto qualitativo | Mitigação | Dono |
|---|---|---|---|
| Fail-closed mal implementado (falha de rede interpretada como "ligado") | baixo/alto | teste AC-04 explícito simulando endpoint fora do ar | Claude Code + Codex (auditoria pontual) |
| Guarda de frontend divergir da guarda de backend (UI permite o que o backend rejeita, ou vice-versa) | médio/médio | AC-05/06 cruzam as duas camadas com integração real, não só leitura de código | Hermes (verificação independente) |
| Seed idempotente colidir com bancos isolados já existentes (`av_s04_*`, `avalia_apresentacao_demo_20261002`) | baixo/médio | guarda de nome de banco restrita a um padrão novo e dedicado; AC-09 testa a recusa explícita | Claude Code |
| Antigravity sem validação visual própria nesta rodada (limitação já registrada em sessões anteriores) | médio/baixo | Hermes faz validação visual independente própria além da revisão de código do Antigravity | Hermes |

## 12. Estimativas

Não estimado em story points/horas, por ausência de velocity sob esta
governança. Tamanho qualitativo: M (média) — um endpoint novo, um contexto de
frontend, duas guardas de UI, um script de seed, sem alteração de schema.

## 13. Critérios de encerramento

Esta sprint encerra quando AC-01 a AC-10 estiverem avaliados com evidência
real (aprovados ou explicitamente reprovados/pendentes) e o pacote completo
(diff + testes + pareceres independentes + relatório) estiver pronto para a
decisão de Rafael sobre publicação (stage/commit/push/PR). Não encerra com
"X% do backlog concluído" como critério — apenas comprovação funcional real,
conforme instrução desta rodada.

A sequência restante até a conclusão completa da trilha (OCR/entrada por
imagem, processamento em lote, revisão/resultados, avaliação da IA) é tratada
como proposta de sequenciamento no corpo da resposta em chat desta sessão, não
como parte do escopo executável desta sprint.

## 14. Ajustes de percurso

| Data/fuso | Mudança | Motivo | Impacto | Decisão/autorização |
|---|---|---|---|---|

## 15. Execução e review

**Executado em 2026-10-13, mesma sessão de abertura.**

### Implementação (Claude Code, `claude -p --continue`, sessão não interativa no checkout principal)

- Backend: `GET /v1/config/capabilities` (`core/app/routers/config.py`), 3 testes.
- Frontend: `CapabilitiesContext.tsx` (fail-closed em 3 camadas), guardas em
  `Layout.tsx` e `AcademicPage.tsx`, troca de fonte em
  `AssessmentEditorPage.tsx`, `isAcademicModuleEnabled()` removida de `api.ts`.
- Seed: `seed_academic_capability_demo.py`, guarda de banco por
  `sqlalchemy.engine.make_url()` (corrigida após falha real de teste — a
  primeira versão usava `urlsplit` manual, vulnerável a travessia de path;
  `test_seed_capability_demo_guard.py` pegou o defeito), 20 casos de teste.
- Limitação da sessão não interativa do Claude Code: a camada de permissões
  negou execução de `pytest`/`tsc`/`psql`/`createdb` (sessão sem aprovação
  interativa). Toda verificação dinâmica (suíte, tipos, lint, integração,
  visual) foi feita de forma independente por Hermes.

### Revisão independente (Antigravity, `agy -p --dangerously-skip-permissions`)

Veredito: **APROVADO COM RESSALVAS**. Achado único (ACH-01, NÃO BLOQUEANTE):
validação de turma no editor não distingue criação vs. edição de legado —
comportamento preexistente de AV-S03, fora do escopo autorizado desta sprint.
Execução própria da suíte: 108 passed. Parecer completo:
`docs/governance/evidence/AV-S03B/antigravity_review_av_s03b.md`.

### Auditoria pontual (Codex, `codex exec --sandbox read-only`)

Foco: "flag não substitui autorização; falha de configuração não habilita
indevidamente". Veredito inicial: **RISCO CONFIRMADO** — achado real
BLOQUEANTE: `AssessmentEditorPage.tsx` tratava "capacidade desconhecida
(carregando)" de forma idêntica a "confirmadamente desligado", permitindo
chamar `listClassGroups()` e considerar o formulário completo sem turma
durante a janela de carregamento (o backend ainda protegia com 422, mas a
UI prometia algo que o servidor recusaria). Parecer completo:
`docs/governance/evidence/AV-S03B/codex_audit_av_s03b.md`.

**Achado corrigido na mesma sessão** (Claude Code, segunda rodada):
`AssessmentEditorPage.tsx` passou a desestruturar `loading` do contexto e
aplicar três guardas (efeito de listagem de turmas, função `persist()`,
render — formulário substituído por spinner enquanto carregando). Verificado
independentemente por Hermes: 108 passed, `tsc --noEmit` limpo, `eslint`
limpo, e confirmado visualmente em navegador real com `loading` da chamada
de capabilities artificialmente atrasado (`Page.addScriptToEvaluateOnNewDocument`
interceptando `fetch`): formulário não aparece, spinner "Verificando
configuração do módulo acadêmico…" é mostrado até a resposta real chegar.

O outro achado do Codex classificado como "BLOQUEANTE" (endpoint mais
permissivo com módulo desligado) foi avaliado e identificado como
comportamento INTENCIONAL pré-existente de `DEC-AV-023` (módulo desligado =
fluxo legado, por design, não uma falha de segurança) — não corrigido,
registrado para rastreabilidade em
`docs/governance/evidence/AV-S03B/codex_audit_av_s03b.md`.

### Verificação independente final (Hermes) — rodada 1

Validação end-to-end real em banco isolado `av_s03b_capacidades_hermes`
(criado e destruído nesta sessão), Core e AI Engine (modo simulado) reais,
navegador real via Chrome dedicado (CDP, porta 9337): todos os 10 critérios
de aceite (§8) confirmados com evidência real. `avalia_dev` e
`avalia_apresentacao_demo_20261002` verificados intactos antes e depois
(contagens e `version_num` idênticos).

### Rodada 2 — saneamento dirigido (2026-10-14, mesma sessão)

Rafael revisou o relatório geral da rodada 1 e apontou 4 lacunas concretas
(ver `snapshot_EXEC-2026-10-13-02...md`, Adendo 2, para o texto completo
do pedido). Resumo da execução:

**Lacuna 1 (distinguir configuração desconhecida de desligada após erro
definitivo) e Lacuna 2 (ACH-01 — legado bloqueado por turma):** Claude Code
(`claude -p`, mesma branch, sem stage/commit). `CapabilitiesContext.tsx`
ganhou `error` distinto de `loading` e uma função `retry()`.
`AssessmentEditorPage.tsx` ganhou um branch de render dedicado para erro
definitivo (mensagem + "Tentar novamente", formulário fora da árvore) e a
derivação `isLegacyAssessmentWithoutClass`/`classGroupRequired`, que exige
turma apenas na criação de avaliação nova, não na edição/publicação de um
rascunho legado já existente — alinhando a UI à regra real do backend
(`update_assessment`/`publish_assessment` nunca exigiram turma,
`create_assessment` exige só na criação). Teste novo
`test_legacy_draft_without_class_stays_editable_and_publishable_under_flag`
(parametrizado true/false). Claude Code não conseguiu executar nenhum
comando nesta sessão (permissões negadas) — relatório correto em admitir
isso sem alegar "passou".

**Lacuna 3 (retirada de `VITE_ACADEMIC_MODULE_ENABLED`):** mesma sessão,
removida de `frontend/.env.example` e das duas invocações em
`run_avalia_dev_update_dry_run.sh`; procedimento de P5 em
`plano_atualizacao_avalia_dev_av-s04_2026-10-01.md` atualizado com notas
datadas (texto histórico preservado, não apagado); P5 não executado.

**Lacuna 4 (precisão das evidências):** tratada diretamente por Hermes —
ver `snapshot_EXEC-2026-10-13-02...md` Adendo 2, itens 1-5 (tabela de
critérios de aceite reescrita em §8 mapeando evidência real por item;
AC-07 corrigido para "IA simulada nesta rodada"; matriz de linha de
chegada formalizada como proposta explícita; escopo do bloqueio da
amostra manuscrita corrigido para não abranger toda a Fase 2).

**Verificação independente (Hermes), fora do sandbox de qualquer agente:**
- `pytest core/app/tests -q`: **110 passed**, 0 failed;
- `npx tsc --noEmit`: 0 erros; `npx eslint src`: 0 erros/avisos;
- **integração real** (banco isolado `av_s03b_capacidades_hermes2`, criado
  e destruído nesta sessão): rascunho legado criado com módulo desligado,
  Core reiniciado com módulo ligado (mesmo banco), `PATCH` real → 200,
  `publish` real → 200, `class_group_id` permanece `null` em ambos —
  confirma por execução, não só leitura de código, que o backend nunca
  exigiu turma para mutação de legado;
- **visual** (navegador real, Chrome dedicado via CDP): os 5 estados da
  Lacuna 1 observados diretamente — sucesso `true` (formulário exige
  turma), sucesso `false` (legado sem bloqueio), `loading` (spinner),
  erro definitivo bloqueado via `Network.setBlockedURLs` (tela de erro +
  "Tentar novamente", nenhum formulário gravável), e o clique real em
  "Tentar novamente" propagando a reconsulta para toda a UI (menu
  reaparece); edição completa de um rascunho legado pela UI (preenchimento
  de critério + "Salvar rascunho") confirmada persistida no backend.

**Revisão independente — rodada 2 (Antigravity, `agy -p`):** escopo
limitado ao delta desta rodada (sem repetir auditoria geral). Execução
própria: 110 passed, tsc/eslint limpos. Respondeu às 5 perguntas dirigidas
confirmando: erro definitivo bloqueia toda escrita (3 pontos
independentes); ACH-01 corrigido sem abrir brecha para avaliação nova;
teste novo cobre o comportamento sem lacuna; Q1 (publicar legado sem
turma) é pergunta de produto genuína, corretamente não decidida sozinha;
Q2 (limpar seletor de turma já vinculada) é decisão técnica já resolvida
corretamente, não pendência de produto. **Veredito: APROVADO** (para o
delta desta rodada). Zero achados bloqueantes. Parecer completo:
`docs/governance/evidence/AV-S03B/antigravity_review_av_s03b_rodada2_saneamento.md`.

**Codex não foi dispachado nesta rodada** — nenhum risco concreto novo
surgiu que justificasse auditoria pontual (conforme limite explícito desta
rodada: "Codex somente se aparecer um risco concreto").

### Rodada 3 — publicação (2026-10-14, mesma sessão)

Rafael autorizou concluir a preparação e publicar `AV-S03B` em PR
rascunho, sem merge e sem ativação operacional, com 4 condições:

1. **Q1 resolvida como manutenção do comportamento vigente.** Avaliações
   legadas sem turma continuam podendo ser editadas e publicadas conforme
   o contrato atual do backend (nenhuma exigência retroativa de turma
   introduzida). Uma eventual mudança futura (exigir turma antes de
   publicar legado) depende de proposta separada — **não é bloqueante
   desta entrega**. Rafael decidiu Q1 diretamente, substituindo o status
   de "pergunta de produto em aberto" por "decidida: manter vigente".
2. **Duas mensagens obsoletas do seed de referência corrigidas**
   (`core/scripts/seed_academic_multi_question_demo.py:88-96` e
   `:318-324`) — alteração exclusivamente textual, confirmada por `git
   diff` e `python -m py_compile`; nenhum guard, lógica, dado ou critério
   de validação alterado; evidências arquivadas de execuções passadas
   preservadas sem edição (texto de saída real daquelas execuções, não
   geradas por este script). Suíte completa (110 passed) reexecutada —
   não como re-ensaio do dry-run (dispensado explicitamente por Rafael
   por ser alteração textual), mas como confirmação geral de que nada
   quebrou.
3. **Build de produção do frontend executado no estado final** —
   pendência explícita apontada por Rafael (rodadas anteriores só
   confirmaram `tsc --noEmit`/`eslint`, não `npm run build`). Ver §15
   para o resultado real.
4. **Publicação**: stage seletivo por paths, commits organizados por
   finalidade, push da branch, PR rascunho contra `main`, checks do HEAD
   publicado acompanhados. Ver §15 para URL do PR, SHA e resultado dos
   checks.

**Precisão de P5 (precondição explícita de Rafael, registrada aqui):** o
procedimento de P5 atualizado nas rodadas anteriores (ver
`plano_atualizacao_avalia_dev_av-s04_2026-10-01.md` §4.2/4.4) pressupõe
que o **frontend em produção já seja o build desta sprint** (consultando
`GET /v1/config/capabilities` em runtime). Um frontend **antigo**, já
compilado antes de `AV-S03B`, continua precisando do rebuild com
`VITE_ACADEMIC_MODULE_ENABLED` para refletir a flag — ele não adquire a
capacidade de runtime automaticamente só porque o procedimento documentado
mudou. Esta distinção está registrada explicitamente e não foi apagada do
procedimento; P5 não foi executado nesta rodada.

`avalia_dev` e `avalia_apresentacao_demo_20261002` verificados intactos
ao final de todas as 3 rodadas (mesmas contagens e `version_num`).

## 16. Closure gate

Referenciar o fechamento criado a partir de
[sprint_closure_template.md](../templates/sprint_closure_template.md) ao
encerrar esta sprint. **Esta sprint está tecnicamente concluída, validada
localmente e publicada em PR rascunho** (ver §15, rodada 3, para URL/SHA),
mas segue sem homologação, sem merge e sem integração — essas três
distinções permanecem exclusivamente a cargo de Rafael. A publicação em
PR rascunho NÃO constitui homologação nem integração; são estados
diferentes e registrados separadamente nesta seção e em
`registers/decisions.md`.
