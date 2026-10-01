---
id: "AV-S04"
status: execucao_local_autorizada
objetivo_aprovado_por: "Rafael (2026-09-30): decisões 1-7 da seção 3 aprovadas em princípio (rodada 1); detalhamento técnico e achados da revisão independente da rodada 2 endereçados; limites funcionais, compatibilidade de contrato e precisão de migração decididos na rodada 3; implementação continua não autorizada, aguardando conclusão da organização local do diretório avalia-plataform"
consolidador: "Hermes"
baseline_entrada: "main@ba6f4074f49f87461c515081964a2aff6202e6cb (PR #5 + PR #6 integrados em 2026-09-30); execução local autorizada sobre main@73a1a4335a14c25a7fbafcefa9d8d5499709098f (PR #8, organização local, integrado em 2026-10-01)"
depende_de: "AV-S03 (homologada e integrada); independente da coleta manuscrita de AV-S05B"
autorizacao_execucao_local: "Rafael (2026-10-01): autoriza execução LOCAL do planejamento desta sprint (HEAD do PR #7 congelado em 35e7040e7222e583e29645d07238002f0ef24e6e), em branch dedicada `feat/av-s04-multiplas-questoes` dentro de `avalia-plataform`, sem novos worktrees/diretórios externos, sem commit/push, sem merge do PR #7, sem alteração em `avalia_dev`, sem saneamento operacional, sem deploy, sem promoção de baseline e sem retomada do benchmark OCR. Migrações somente em PostgreSQL isolado com dados fictícios; fluxos de interface validados em navegador real. Implementação, correções e revisão independente devem ser concluídas antes da apresentação do pacote final para publicação — sem nova autorização conversacional para essas atividades locais."
---

# AV-S04 — Múltiplas questões por avaliação (planejamento detalhado)

> **REGISTRO DE AUTORIZAÇÃO DE EXECUÇÃO LOCAL (2026-10-01).** Rafael
> autorizou a execução local deste planejamento após a conclusão da
> organização local do diretório `avalia-plataform` (PR #8, merge commit
> `73a1a4335a14c25a7fbafcefa9d8d5499709098f`, integrado em `main`). A
> compatibilidade do plano com `main` atual foi confirmada por
> `git merge-tree --write-tree origin/main origin/docs/av-s04-planejamento`,
> sem conflitos. Esta autorização cobre trabalho local (branch dedicada,
> testes, migração em Postgres isolado, validação em navegador real) e
> **não inclui** commit/push, merge do PR #7, alteração em `avalia_dev`,
> saneamento operacional, deploy, promoção de baseline ou retomada do
> benchmark OCR. O HEAD do PR #7 (`35e7040e7222e583e29645d07238002f0ef24e6e`)
> permanece congelado como referência do planejamento aprovado; nenhuma
> alteração é feita nele ou no PR.

> **ESTE DOCUMENTO É PLANEJAMENTO, NÃO EXECUÇÃO.** Nenhum código de AV-S04
> foi escrito, testado ou integrado. Nenhuma migração foi executada, nem
> isolada nem em `avalia_dev`. Nenhuma implementação está autorizada a
> partir deste documento. Rafael aprovou os 7 pontos de direção da seção 3
> em 2026-09-30; esta rodada detalha cada um deles tecnicamente, conforme
> solicitado, e permanece sujeita a aprovação final antes de `status: ready`
> e a autorização separada de implementação/Git.

## 1. Objetivo e posição na trilha

Permitir que uma avaliação contenha, ordene, edite e publique **múltiplas
questões**, preservando:

- os limites de autorização por vínculo professor↔turma já corrigidos em
  AV-S01/AV-S03;
- o significado histórico de respostas, rubricas, correções e revisões
  humanas já registradas — nenhuma operação permitida pode reescrever o
  contexto de uma correção existente.

Backlog coberto: `BL-AV-3-01` a `BL-AV-3-04` (ver
[`backlog_tecnico_avalia.md`](../backlog/backlog_tecnico_avalia.md) linhas
86–89 e 307–310).

Dependência real: AV-S04 depende tecnicamente da estrutura acadêmica e do
padrão de autorização homologados e integrados em AV-S03
(`DEC-AV-026`/`DEC-AV-027`, PR #3). **Não depende** da coleta manuscrita ou
da investigação de OCR de AV-S05B — eixos tecnicamente independentes.
AV-S05B permanece investigação parcial de OCR/visão local; nenhuma
alteração deste documento modifica esse estado.

## 2. Evidência de código inspecionada

- `core/app/models.py`: `Assessment` já modela relação 1:N com `Question`
  (`Assessment.questions`); `Question` não tem campo de ordenação
  (`position`).
- `core/app/schemas.py`: `AssessmentCreate.question: Optional[QuestionInput]`
  (linha 81) é singular; `AssessmentOut.questions: list[QuestionOut]`
  (linha 95) já é plural; `CorrectionJobContextOut.question: QuestionOut`
  (linha 207) é singular por design — uma correção sempre se refere a
  exatamente uma questão, isso não muda com múltiplas questões.
- `core/app/main.py`: `POST /v1/assessments` (linha 158) cria a partir de
  `payload.question` singular; `PATCH /v1/assessments/{id}` só atualiza
  `title`; `_get_owned_assessment` (linha 182) é o guard de autorização
  reaproveitável para os novos endpoints de coleção.
- `frontend/src/types.ts` (linha 67): `Assessment` já aceita opcionalmente
  tanto `question?: Question` quanto `questions?: Question[]`.
- `frontend/src/services/api.ts`: `updateAssessment` usa `PUT`, Core expõe
  `PATCH` — inconsistência preexistente, corrigida dentro de `BL-AV-3-04`.
- Nenhuma implementação de múltiplas questões foi iniciada.

## 3. Decisões — aprovadas em princípio por Rafael em 2026-09-30, detalhadas nesta rodada

As sete decisões abaixo foram aprovadas em princípio. Não são reabertas
nesta rodada; o que segue é o detalhamento técnico solicitado para cada
uma. Qualquer divergência encontrada durante a implementação deve ser
registrada como achado novo, não como reversão silenciosa destas decisões.

### 3.1 Publicação imutável com clonagem para novo rascunho — APROVADA

Após publicada, uma avaliação (título, ordem/conteúdo das questões e
rubricas) é imutável. Uma mudança exige clonar para um **novo rascunho**.

**O que é copiado na clonagem:**
- `title` (texto livre, pode ser editado no clone antes de nova publicação);
- `class_group_id` (vínculo de turma do rascunho original);
- cada `Question` do original: `statement`, `reference_answer`,
  `max_score`, `position` — como **novas linhas**, com **novos IDs**;
- para cada `Question` clonada, a rubrica mais recente (`Rubric.criteria`)
  é copiada como uma **nova `Rubric`** com `version=1`, `is_published=false`,
  vinculada à nova `Question`.

**O que NÃO é copiado (explicitamente proibido):**
- nenhuma `Answer` do original;
- nenhum `CorrectionJob`/`AIExecutionResult` do original;
- nenhum `HumanReview` do original;
- nenhum `AuditEvent` do original (o clone gera seus próprios eventos de
  auditoria a partir da ação de clonagem).

**Rastreabilidade da origem:**
- adicionar `Assessment.cloned_from_id: Optional[str]` (FK para
  `assessments.id`, nullable, sem cascade de exclusão) — aponta para a
  avaliação publicada que originou o clone;
- a `AuditEvent` da criação do clone registra
  `action="CLONE"`, `resource_type="Assessment"`,
  `before_json={"source_assessment_id": "<id original>"}`;
- `AssessmentOut` passa a expor `cloned_from_id` (somente leitura) para que
  o frontend possa indicar a proveniência sem consulta adicional.
- Toda correção/resposta histórica associada ao original continua
  resolvendo exatamente as `Question`/`Rubric` originais — o clone não
  altera `question_id` de nenhuma `Answer` existente, porque usa IDs novos.

**Risco identificado e mitigado:** se o original tiver `class_group_id`
desativado/expirado no momento da clonagem, o clone herda o valor bruto,
mas a autorização de edição do clone passa pelo mesmo
`require_assessment_mutation` já usado na criação — se o vínculo não
estiver mais ativo, a operação subsequente (não a clonagem em si) deve
falhar com o mesmo `403`/`422` já usado hoje, sem exceção especial para
clones.

**Risco adicional identificado pela revisão independente — seleção não
determinística de rubrica:** `publish_assessment`
(`core/app/main.py:230-232`) seleciona a rubrica a publicar com fallback
`question.rubrics[-1]` (última da lista, em ordem de inserção) quando
nenhuma rubrica está marcada `is_published`. A relação
`Question.rubrics` (`core/app/models.py:214`) não tem `order_by`
explícito — a ordem de uma lista SQLAlchemy sem `order_by` não é
garantida pela ordem de inserção em todos os cenários de carregamento.
Isso já é um comportamento preexistente do fluxo atual (questão única),
mas passa a ser **mais relevante com clonagem**: o `Question` clonado
recebe uma nova `Rubric` (`version=1`, `is_published=false`); se o
professor editar a rubrica do clone mais de uma vez antes de publicar
(criando `version=2`, `version=3`, ...), a seleção de "rubrica mais
recente" no momento da publicação do clone fica sujeita à mesma ambiguidade
de ordenação. **Correção exigida antes da implementação:** adicionar
`order_by=Rubric.version.desc()` (ou `created_at.desc()`) à relação
`Question.rubrics`, ou à query de seleção em `publish_assessment`, para
que "a rubrica mais recente" seja determinística tanto no fluxo original
quanto no fluxo de clone. Esta correção é um débito preexistente, não
introduzido por AV-S04, mas torna-se um pré-requisito de implementação
desta sprint porque os critérios AC-06/AC-07 (abaixo) dependem da seleção
de rubrica estar correta após clonagem.

**Teste de regressão exigido para a clonagem:** clonar uma avaliação
publicada, editar e republicar o clone com uma rubrica diferente da
original, e então verificar que o `CorrectionJobContext` histórico das
respostas da avaliação **original** continua resolvendo a rubrica/versão
original, não a do clone — esse é o cenário mais provável de quebrar
silenciosamente, já que clone e original não compartilham nenhuma FK
além do vínculo unidirecional `cloned_from_id`.

### 3.2 `questions` como contrato canônico, com `question` como entrada legada temporária — APROVADO com compatibilidade (ajustado nesta rodada)

Levantamento completo de consumidores do campo singular `question`/
`payload.question` antes de qualquer remoção, por inspeção direta de
código (não presumido):

**Backend (Python):**
- `core/app/schemas.py:81` — `AssessmentCreate.question` (campo a
  substituir);
- `core/app/schemas.py:207` — `CorrectionJobContextOut.question` (**não
  é o mesmo caso**: é singular por design, pois resolve a questão exata de
  uma correção — fora do escopo desta migração);
- `core/app/main.py:158-165` — cria uma única `Question` a partir de
  `payload.question`;
- `core/app/seed.py:40-55` — script de seed usa a forma singular ao
  instanciar `Question` diretamente (via ORM, não via `AssessmentCreate`) —
  não depende do schema Pydantic, mas precisa de ajuste equivalente se o
  seed passar a exercitar o endpoint HTTP em vez do ORM direto.

**Testes (Python):**
- `core/app/tests/test_core_flow.py:10` — payload HTTP com `"question": {...}`;
- `core/app/tests/test_authorization_boundaries.py:76,176,190` — fixtures e
  asserções sobre `body["question"]`;
- `core/app/tests/test_academic_authorization.py` — cria `Question` via
  ORM direto (não via payload singular do schema);
- `core/app/tests/test_review_idempotency.py` — idem, via ORM direto.

**Scripts de evidência (não produção, mas versionados):**
- `docs/governance/evidence/AV-S02-postgres-isolado/av_pg_http_flow.py`,
  `av_pg_concurrency.py`, `av_pg_concurrency_conflict.py` — chamadas HTTP
  reais com payload `"question": {...}`;
- `docs/governance/evidence/AV-S03/AC-10-scripts/ac10_scenarios.py` e sua
  cópia em `pacote-revisao-20260928/arquivos_novos_raw/` — idem.

**Frontend (TypeScript):**
- `frontend/src/types.ts:67` — `Assessment.question?` já coexiste com
  `questions?`;
- `frontend/src/services/api.ts:114,135` — `createAssessment` envia
  `question` singular no payload de criação;
- `frontend/src/pages/AssessmentEditorPage.tsx:35,85,93-97` — monta o
  payload de criação com `question` singular e resolve
  `saved.question || saved.questions?.[0]` ao ler de volta;
- `frontend/src/pages/AnswerPage.tsx:9,11,13` — resolve
  `assessment?.question || assessment?.questions?.[0]` para decidir qual
  questão responder;
- `frontend/src/pages/ReviewPage.tsx:10,60,104,114,134` — mistura
  `question`/`questions` ao montar e ler o contexto de revisão.

**Documentação/contrato:**
- `docs/contracts/openapi.yaml:504` — `AssessmentCreate.question` como
  `QuestionInput` no schema OpenAPI;
- `docs/contracts/openapi.yaml:389-393` — `CorrectionJobContextOut.question`
  (fora do escopo, ver acima);
- `docs/governance/sprints/sprint_GOV-006_auditoria_governanca.md:105` e
  `docs/governance/snapshots/snapshot_EXEC-2026-09-30-01_gov-006-auditoria.md:84`
  — registros históricos de auditoria que descrevem o estado singular
  **como fato observado na época**; não devem ser reescritos
  retroativamente, apenas o contrato real muda daqui para frente.

**Decisão de Rafael (2026-09-30, rodada 3): implantação conjunta
não confirmada.** Rafael não confirma a premissa de implantação conjunta
de backend e frontend por falta de evidência — exatamente a leitura
cautelosa que a rodada anterior já havia sinalizado como item bloqueante.
Consequência direta: `questions` é adotado como contrato canônico, mas
`question` (singular) é mantido como **entrada legada temporária**, não
removido nesta sprint. Nenhum prazo de remoção é inventado e nenhum
consumidor externo é presumido — a compatibilidade existe porque a
ausência de evidência de implantação conjunta não permite excluir a
hipótese de um consumidor não visível neste repositório, não porque um
consumidor específico foi identificado.

**Desenho da compatibilidade de entrada:**
- `AssessmentCreate` passa a aceitar `questions: Optional[list[QuestionInput]]
  = None` **e** mantém `question: Optional[QuestionInput] = None`, ambos
  opcionais individualmente;
- validação, nesta ordem: (a) se nenhum dos dois for fornecido, falha com
  `422` ("Pelo menos uma questão é obrigatória."); (b) se **ambos** forem
  fornecidos simultaneamente, falha com `422` e mensagem explícita
  ("Forneça `questions` ou `question`, não ambos. `question` está
  depreciado; prefira `questions`."); (c) se apenas `question` for
  fornecido, ele é **normalizado internamente** para `questions =
  [question]` antes de prosseguir — o restante do fluxo de criação (Task
  3 do plano de execução) opera **somente** sobre a forma plural
  normalizada, nunca sobre o campo singular diretamente;
- **semântica de presença, precisada após revisão independente da rodada
  3:** "fornecido" significa não-`None` **e** não-vazio quando aplicável a
  `questions`. Um payload `{"questions": []}` é tratado como equivalente a
  "nenhum dos dois fornecido" (caso a, `422`), não como "questions
  fornecido com zero itens" — isso evita o caso degenerado de uma lista
  vazia escapar da validação de "pelo menos uma questão obrigatória" só
  porque o campo tecnicamente não é `None`. Da mesma forma, um payload
  `{"question": {...}, "questions": []}` é tratado como **apenas
  `question` fornecido** (caso c, aceito e normalizado), não como "ambos
  fornecidos" (caso b) — porque uma lista vazia não carrega dado real que
  justifique a rejeição por ambiguidade. A checagem de "ambos fornecidos"
  (caso b) só dispara quando **ambos** os campos têm conteúdo real
  (`question is not None` e `len(questions or []) > 0`);
- o endpoint registra, via `log_event`, quando o payload legado singular
  foi usado (ex.: `assessment_created_legacy_singular_payload=true`),
  para permitir medir uso real do campo depreciado ao longo do tempo —
  isso é instrumentação de observação, não telemetria externa, e não
  implica em nenhum prazo de descontinuação automática.

**Compatibilidade de saída — adicionada nesta rodada, não coberta pela
redação anterior:** a entrada não é o único ponto de contrato. Antes
desta rodada, a seção só tratava `AssessmentCreate` (entrada); a mesma
cautela de "não presumir implantação conjunta" exige revisar também
`AssessmentOut` (saída), já que um consumidor que ainda lê `question`
singular na resposta também não pode ser presumido ausente:
- `AssessmentOut.questions: list[QuestionOut]` já é plural e **permanece
  canônico** — nenhuma mudança aqui;
- `AssessmentOut` passa a expor adicionalmente um campo computado
  `question: Optional[QuestionOut]` (somente leitura) — **mas não
  simplesmente `questions[0]` sempre**. Correção aplicada após revisão
  independente da rodada 3: um consumidor legado que só lê `question`
  precisa de um sinal de que a visão singular deixou de ser
  representativa, não de um valor silenciosamente arbitrário. Regra
  precisa: `question = questions[0]` **se e somente se** `len(questions)
  == 1`; se `len(questions) == 0`, `question = None`; se `len(questions) >
  1`, `question = None` também — nunca "a primeira de várias", porque
  isso reintroduziria exatamente a ambiguidade que a migração do contrato
  pretende eliminar, apenas deslocada do fallback do frontend para o
  backend. Um consumidor legado que só lê `question` recebe `None` para
  qualquer avaliação com mais de uma questão, o que é um sinal explícito
  de incompatibilidade (campo ausente) em vez de um dado parcial
  silencioso;
- isso significa que, nesta sprint, a resposta da API expõe
  simultaneamente `question` (compatibilidade, derivado, só populado para
  avaliações de exatamente 0 ou 1 questão) e `questions` (canônico,
  sempre correto) — o oposto do que a redação anterior presumia
  implicitamente (que só a entrada precisava de uma ponte).

**Frontend e documentação de uso novo:**
- `frontend/src/types.ts`, `api.ts`, `AssessmentEditorPage.tsx`,
  `AnswerPage.tsx` e `ReviewPage.tsx` são atualizados para **usar e gerar
  somente `questions`** em código novo — o frontend não passa a enviar o
  payload legado singular;
- os fallbacks de leitura `a.question || a.questions?.[0]` no frontend
  são removidos em favor de ler diretamente `questions[0]` (ou iterar
  `questions`), já que o backend garante `questions` sempre populado;
- `docs/contracts/openapi.yaml` documenta `questions` como o campo
  primário de criação, com `question` listado explicitamente como
  **"Depreciado — mantido apenas para compatibilidade de entrada
  legada; não enviar em integrações novas; rejeitado em conjunto com
  `questions` no mesmo payload."**

**Depreciação documentada, sem prazo inventado:**
A documentação (sprint document, OpenAPI, e um changelog interno a criar
em `docs/governance/registers/decisions.md` como nova entrada `DEC-AV-0XX`
no momento da implementação) registra:
- `question` é aceito apenas como entrada; nunca é a forma preferencial;
- a condição futura de remoção **não tem data definida nesta rodada** —
  fica condicionada a uma confirmação operacional futura de que não há
  consumidor dependente do campo singular (seja por telemetria de uso
  real do backend, seja por confirmação explícita de Rafael sobre o
  cenário de implantação), a ser decidida em sprint ou execução
  posterior, não nesta;
- a remoção, quando ocorrer, exigirá sua própria decisão explícita e
  registro `DEC-AV-0XX`, não decorre automaticamente da aprovação desta
  sprint.

**Consumidores externos:** busca em todo o repositório por indícios de
cliente externo, SDK, aplicativo mobile ou versionamento de API (`/v2`,
"integração com terceiro") não retornou nenhuma ocorrência além de
referências institucionais não técnicas. **Isso é um achado de ausência
de evidência dentro do escopo deste repositório, não uma prova de
ausência de consumidor** — uma busca em um único repositório nunca pode
provar que não existe cliente em produção, coleção HTTP salva fora do
controle de versão, ou artefato implantado anterior a este snapshot. Não
há nenhum `Dockerfile`, `docker-compose` ou workflow de deploy neste
repositório — `ci.yml` executa apenas testes/lint/build por componente,
sem nenhum job de deploy. A ausência de evidência de implantação conjunta
é exatamente o motivo pelo qual esta rodada adota compatibilidade
temporária em vez de remoção direta — nenhum consumidor específico foi
identificado ou precisa ser inventado para justificar essa cautela.

Plano de implementação (quando autorizado):
1. `AssessmentCreate` ganha `questions: Optional[list[QuestionInput]] =
   None`, mantém `question: Optional[QuestionInput] = None`, com a
   validação de normalização/rejeição de ambos descrita acima.
2. `AssessmentOut` ganha o campo computado `question` (compatibilidade de
   saída), mantendo `questions` como principal.
3. `core/app/main.py` passa a operar sobre a lista normalizada
   internamente; os testes Python listados acima (`test_core_flow.py`,
   `test_authorization_boundaries.py`) ganham casos cobrindo: payload só
   com `question` (aceito, normalizado), payload só com `questions`
   (aceito), payload com ambos (rejeitado com `422` e mensagem exata),
   payload com nenhum dos dois (rejeitado com `422`).
4. Os três scripts de evidência do AV-S02/AV-S03 **não são alterados**
   nesta sprint — como `question` continua aceito, eles continuam
   funcionando sem modificação; isso é uma simplificação em relação à
   rodada anterior, que previa atualizá-los junto com a remoção do
   contrato singular.
5. `frontend/types.ts`, `api.ts`, `AssessmentEditorPage.tsx`,
   `AnswerPage.tsx`, `ReviewPage.tsx` atualizados para usar `questions`
   exclusivamente em código novo, conforme acima.
6. `docs/contracts/openapi.yaml` documenta ambos os campos com a nota de
   depreciação explícita em `question`.

### 3.3 Endpoints explícitos de coleção — APROVADA

Endpoints propostos (mantidos da rodada anterior, detalhados aqui):

- `POST /v1/assessments/{assessment_id}/questions` — adiciona uma questão.
- `PATCH /v1/questions/{question_id}` — edita uma questão.
- `DELETE /v1/questions/{question_id}` — remove uma questão.
- `PUT /v1/assessments/{assessment_id}/questions/order` — reordena.

**Restrição a rascunhos:** todos os quatro endpoints verificam
`assessment.status == AssessmentStatus.RASCUNHO` antes de qualquer
mutação; se `PUBLICADA`, retornam `409 Conflict` com mensagem explícita
("Avaliação publicada não pode ser alterada; crie um clone.") — nunca
`200` com efeito silencioso nem erro genérico.

**Autorização consistente — corrigido após revisão independente:** a
redação original desta seção dizia que os quatro endpoints reaproveitariam
"a mesma cadeia já usada em `POST /v1/assessments`". Isso estava impreciso:
`POST /v1/assessments` é uma rota de criação, sem avaliação preexistente a
verificar, e por isso só chama `require_active_class_link` diretamente. A
cadeia real usada por toda rota que **muta uma avaliação já existente**
(`update_assessment`, `publish_assessment`, `create_answer`,
`request_correction`) é `require_assessment_mutation`
(`core/app/routers/academic.py:165-171`), que já encapsula: bypass para
`admin`, checagem de `owner_id` e, se `class_group_id` estiver definido,
`require_active_class_link`. Os quatro novos endpoints devem reusar
exatamente `require_assessment_mutation`, não uma cadeia equivalente
reimplementada à mão.

**Resolução de `assessment` nos dois endpoints raiz-questão:**
`PATCH /v1/questions/{question_id}` e `DELETE /v1/questions/{question_id}`
são enraizados em `question_id`, não em `assessment_id`, e por isso não
podem chamar `_get_owned_assessment(db, assessment_id, user)` diretamente —
é preciso resolver `question → assessment` primeiro. O único precedente
hoje para esse caminho é `create_rubric` (`core/app/main.py:260-275`), que
resolve `Question → Assessment` manualmente e então faz uma checagem de
ownership **duplicada e divergente**: primeiro um `if user.role ==
PROFESSOR and assessment.owner_id != user.id: raise 403` inline, e só
depois chama `require_assessment_mutation` (que já faz essa mesma
checagem). Replicar esse padrão duplicaria uma inconsistência existente em
vez de corrigi-la. Proposta: criar um único helper compartilhado —
`_get_assessment_for_question(db, question_id, user) -> tuple[Question,
Assessment]` — que resolve a cadeia e chama `require_assessment_mutation`
uma única vez, usado pelos dois novos endpoints raiz-questão **e** por
`create_rubric` (correção de um débito preexistente identificado nesta
revisão, não introduzido por AV-S04).

**Controle de concorrência — lacuna identificada pela revisão
independente, agora explícita:** nenhuma versão anterior desta seção
especificava bloqueio de linha para os quatro endpoints de mutação de
questão. Como todos competem pela mesma invariante `UniqueConstraint
(assessment_id, position)`, duas chamadas concorrentes (ex.: dois
`PUT .../questions/order` para a mesma avaliação, ou uma reordenação
correndo contra uma exclusão) podem entrelaçar leituras e escritas e
violar a invariante de contiguidade 1..N sem violar a constraint (gerando
um buraco silencioso) ou colidir na constraint de forma não determinística
conforme o nível de isolamento. Decisão técnica adicionada nesta rodada:
toda mutação de posição (adicionar, editar, excluir, reordenar) deve
executar `SELECT ... FOR UPDATE` sobre a linha de `Assessment` (ou sobre o
conjunto de `Question` da avaliação) no início da transação, serializando
mutações concorrentes sobre a mesma avaliação. Isso é consistente para as
quatro operações, não apenas para a reordenação.

### 3.4 `position` persistida com unicidade por avaliação — APROVADA, migração reespecificada nesta rodada

**Schema:** `Question.position: int`, não-nulo, `UniqueConstraint
("assessment_id", "position")`, criado via migração Alembic.

**Backfill — corrigido nesta rodada: o contrato singular não comprova
ausência de múltiplas questões nos dados reais.** A redação anterior
afirmava que o backfill era trivial porque "sob o contrato atual, toda
`Assessment` tem no máximo uma `Question`". Rafael corretamente apontou
que isso confunde uma restrição do **caminho de aplicação atual**
(`AssessmentCreate.question`, usado por `POST /v1/assessments`) com uma
restrição do **schema do banco**. Nada no schema — nem `UniqueConstraint`,
nem `CheckConstraint`, nem trigger — impede hoje que uma `Assessment`
tenha múltiplas `Question`. Caminhos que escrevem `Question` sem passar
pelo endpoint singular já existem no próprio repositório:
`core/app/seed.py` (ORM direto), `core/app/tests/test_academic_authorization.py`
e `test_review_idempotency.py` (ORM direto em fixtures de teste). Isso não
prova que existam múltiplas questões por avaliação em algum ambiente real,
mas também não permite presumir o contrário sem verificar.

**Correção aplicada — verificação obrigatória antes de decidir o
backfill:** a migração deve começar por uma consulta de verificação real
contra o banco alvo, **antes** de qualquer decisão de que o backfill é
trivial:

```sql
SELECT assessment_id, COUNT(*) AS total
FROM questions
GROUP BY assessment_id
HAVING COUNT(*) > 1;
```

- Se o resultado for vazio, `position = 1` para toda `Question` existente
  é correto **porque foi verificado**, não porque foi presumido a partir
  do contrato de API.
- Se o resultado não for vazio, as avaliações retornadas usam a ordem
  `created_at ASC, id ASC` (ver abaixo) como critério de desempate real,
  não apenas defensivo.
- Essa consulta deve ser executada em ambiente de teste isolado (Postgres
  16, mesma versão usada em `ci.yml`) como parte da validação desta
  sprint antes da implementação, e novamente contra o ambiente real no
  momento da migração — nenhuma das duas execuções está autorizada nesta
  rodada, que é só de planejamento.

**`created_at` como critério de desempate — mantido, agora como mecanismo
primário, não apenas defensivo:** como a hipótese de unicidade não está
comprovada, a coluna `created_at` deixa de ser "infraestrutura defensiva
para um caso futuro hipotético" e passa a ser o mecanismo real de
desempate, caso a verificação acima encontre avaliações com múltiplas
questões. Se `created_at` for adicionada via `server_default=now()`, o
`UPDATE` de backfill das linhas existentes deve, na medida do possível,
aproximar a ordem real de criação: usar `AuditEvent` do tipo
`action="CREATE", resource_type="Assessment"` (já existente,
`main.py:168-176`) como aproximação do instante de criação da avaliação
pai, com `id` como desempate final para `Question`s da mesma avaliação
sem nenhuma fonte de ordem melhor disponível. Essa aproximação deve ser
registrada explicitamente na migração como heurística, não como ordem
cronológica exata.

**Precisão da estratégia de lock/validação — corrigida nesta rodada:** a
redação anterior recomendava genericamente "`NOT VALID` + `VALIDATE
CONSTRAINT`" para a migração como um todo, sem distinguir a quais
constraints isso se aplica. No PostgreSQL, `NOT VALID` seguido de
`VALIDATE CONSTRAINT` é suportado nativamente apenas para constraints
`CHECK` e `FOREIGN KEY` — **não existe `NOT VALID` para `UNIQUE
constraint`** adicionada via `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE`.
Usar essa técnica como solução genérica para a unicidade de
`(assessment_id, position)` estaria tecnicamente incorreto. A
especificação correta, por constraint:

1. **`Question.position NOT NULL`** (e `Question.created_at NOT NULL`,
   se adicionada): usar o padrão suportado pelo Postgres para evitar
   escaneamento completo bloqueante —
   `ALTER TABLE questions ADD CONSTRAINT questions_position_not_null CHECK (position IS NOT NULL) NOT VALID;`
   seguido de
   `ALTER TABLE questions VALIDATE CONSTRAINT questions_position_not_null;`
   e só então
   `ALTER TABLE questions ALTER COLUMN position SET NOT NULL;`
   — o Postgres (12+) reconhece a `CHECK` já validada e evita o
   escaneamento completo da tabela ao aplicar `SET NOT NULL`, reduzindo o
   tempo de lock exclusivo. **Esta é a parte da migração onde `NOT
   VALID`/`VALIDATE CONSTRAINT` se aplica de fato.**
2. **`UniqueConstraint (assessment_id, position)`**: não usa `NOT VALID`.
   O padrão de baixo lock correto é construir o índice único
   concorrentemente e depois anexá-lo como constraint:
   `CREATE UNIQUE INDEX CONCURRENTLY ix_questions_assessment_position ON questions (assessment_id, position);`
   (não pode rodar dentro de uma transação — precisa ser um passo Alembic
   não-transacional) seguido de
   `ALTER TABLE questions ADD CONSTRAINT uq_questions_assessment_position UNIQUE USING INDEX ix_questions_assessment_position;`
   (operação rápida, apenas metadado, porque o índice já existe
   construído). **Risco de falha a cuidar na implementação (apontado pela
   revisão independente da rodada 3):** se a construção `CONCURRENTLY` for
   interrompida (erro, timeout, cancelamento), o Postgres pode deixar um
   índice marcado `INVALID` em vez de limpá-lo automaticamente; antes de
   tentar novamente, a migração precisa verificar e, se necessário, hard
   `DROP INDEX` o índice inválido remanescente — não presumir que uma
   nova tentativa de `CREATE UNIQUE INDEX CONCURRENTLY` com o mesmo nome
   simplesmente funciona por cima de um índice inválido anterior.

**Onde isso será validado:** antes de qualquer execução contra `avalia_dev`
ou qualquer ambiente compartilhado — não autorizada nesta rodada — a
migração completa (consulta de verificação, backfill, `CHECK NOT VALID` +
`VALIDATE` + `SET NOT NULL`, `CREATE UNIQUE INDEX CONCURRENTLY` + `ADD
CONSTRAINT USING INDEX`) deve ser executada e cronometrada em um Postgres
16 isolado e descartável (mesma versão de `ci.yml`), com um dataset de
teste que inclua deliberadamente pelo menos um caso de avaliação com
múltiplas `Question`s pré-existentes (inserido via ORM direto, simulando
os caminhos de `seed.py`/testes), para exercitar o ramo de desempate por
`created_at`/`id` e não apenas o caso trivial.

**Reordenação transacional — concorrência e offset explicitados:**
- a transação de reordenação começa com `SELECT ... FOR UPDATE` sobre a
  avaliação (mesmo lock exigido na seção 3.3 para as quatro operações),
  eliminando a corrida entre duas chamadas de reordenação concorrentes ou
  entre reordenação e exclusão/adição simultânea;
- o endpoint de reordenação recebe a lista completa de `question_id` na
  nova ordem; valida que contém exatamente os IDs atuais da avaliação, sem
  repetição e sem faltantes, antes de qualquer escrita;
- a troca é feita em uma única transação de banco: todas as `position` são
  atualizadas atomicamente; para nunca violar a unicidade mesmo
  transitoriamente, um offset temporário de magnitude
  `max_position_atual + total_de_questoes_da_avaliacao + 1` é somado a
  todas as posições antes de aplicar os valores finais — essa magnitude é
  garantidamente livre de colisão dado o teto de 50 questões por avaliação
  proposto na seção 3.7;
- em caso de qualquer erro durante a transação, rollback integral — nenhum
  estado parcial de reordenação é persistido.

**Exclusão de questão e novo cálculo de posição — mesmo lock aplicado:**
- ao excluir uma questão de um rascunho, a mesma trava de linha da
  avaliação (`SELECT ... FOR UPDATE`) é adquirida antes de recompactar as
  posições das questões remanescentes, na mesma transação da exclusão,
  para preservar a `UniqueConstraint` e manter 1..N contíguo mesmo quando
  uma exclusão corre contra uma adição ou reordenação simultânea;
- exclusão é bloqueada se resultaria em zero questões e a avaliação for
  publicável nesse estado incompleto (ver 3.6 sobre avaliação incompleta) —
  **decisão explícita necessária**: a exclusão da última questão de um
  rascunho é permitida (rascunho pode ficar temporariamente vazio), mas a
  **publicação** exige pelo menos uma questão (regra já coberta por 3.7).

**Rollback:** qualquer falha de validação (IDs inconsistentes, posição
duplicada após o cálculo, violação de constraint) aborta a transação
inteira; nenhuma escrita parcial do rascunho é permitida.

### 3.5 Associação explícita resposta↔questão e seleção na interface — APROVADA, com limites explícitos de escopo

- `AnswerInput.question_id` já existe e continua obrigatório;
  `AnswerPage.tsx` deixa de usar o fallback
  `assessment?.question || assessment?.questions?.[0]` e passa a exigir
  seleção explícita da questão pelo usuário antes de habilitar o envio.
- **Esta decisão explicitamente NÃO decide:**
  - se um aluno pode enviar mais de uma resposta para a mesma questão
    (restrição de tentativas/reenvio);
  - se existe unicidade implícita aluno↔questão (hoje não existe nenhuma
    constraint nesse sentido em `Answer`, e esta sprint não cria uma);
  - qualquer modelo de identidade de "aluno" além do já existente
    (`student_name_fake`, texto livre, sem FK para `Student` nas
    respostas — essa é uma lacuna preexistente, não introduzida por
    AV-S04, e permanece fora de escopo).
- Se Rafael quiser restringir reenvio ou introduzir unicidade
  aluno↔questão no futuro, isso é uma decisão de produto separada, a ser
  tratada em sprint própria, não implicitamente dentro de AV-S04.

### 3.6 Pontuação máxima derivada da soma dos máximos das questões — APROVADA, com tratamento explícito de avaliação incompleta

- `assessment_max_score` (campo computado, não persistido) é definido como
  a soma de `Question.max_score` de todas as questões da avaliação.
- **Avaliação incompleta (zero questões):** `assessment_max_score = 0`.
  Uma avaliação com zero questões **não pode ser publicada** (ver 3.7);
  o valor `0` é exibido no rascunho apenas como indicação informativa de
  estado incompleto, nunca usado para calcular proporção/nota.
- **Distinção obrigatória de nomenclatura:** `assessment_max_score`
  (pontuação máxima possível, derivada) nunca deve ser confundido com a
  nota obtida por um aluno em uma resposta/correção individual
  (`AIExecutionOut.overall_confidence`, `CriterionScoreOut.score`, ou
  qualquer agregação de correção) — são conceitos diferentes: o primeiro é
  propriedade da avaliação (quanto vale no total), o segundo é resultado
  de uma correção específica (quanto um aluno tirou). O frontend deve
  rotular os dois valores de forma inequívoca (ex.: "Pontuação máxima da
  avaliação" vs. "Nota obtida nesta correção") para não repetir a
  ambiguidade que já existe implicitamente na UI atual de questão única.
- Nenhum campo persistido redundante é criado para o total; é sempre
  calculado on-the-fly a partir das questões atuais, o que também significa
  que o total de uma avaliação **publicada** é fixo (porque as questões
  publicadas são imutáveis), e o total de um **rascunho** pode mudar
  conforme questões são adicionadas/removidas/editadas.

### 3.7 Mínimo de uma questão para publicação; limites de máximo e tamanho — APROVADO integralmente nesta rodada, com escopo de aplicação precisado

**Mínimo (aprovado):** publicação exige pelo menos 1 questão com rubrica
válida (critério já coberto pelo AC-04 existente).

**Máximo de questões por avaliação — aprovado: 50 por avaliação.**
Não existe hoje nenhum teste de carga, benchmark de payload ou limite
configurado no FastAPI/Pydantic para o tamanho da lista `questions`. O
valor de 50 é um **limite funcional de produto**, não uma capacidade
comprovada por teste de carga — é generoso para o caso de uso real
(prova/avaliação acadêmica dificilmente ultrapassa esse número) e evita
payloads desproporcionais sem restringir nenhum uso legítimo conhecido.

**Tamanho de campo de texto — aprovado: 10.000 caracteres, aplicado
somente aos campos textuais longos explicitamente identificados abaixo,
não indiscriminadamente.** Rafael corrigiu o escopo de aplicação: o
limite de 10.000 caracteres **não** se aplica a `title` da avaliação, a
nenhum identificador (`id`, `assessment_id`, `question_id`, etc.), nem a
qualquer campo que já tenha ou deva ter um limite menor e mais específico.
A tabela abaixo precisa o escopo exato:

| Campo | Tipo/uso | Limite aplicado nesta sprint | Justificativa |
|---|---|---|---|
| `QuestionInput.statement` | enunciado da questão, texto longo | `max_length=10000` (novo) | campo textual longo explicitamente citado por Rafael como alvo do limite |
| `QuestionInput.reference_answer` | resposta de referência, texto longo | `max_length=10000` (novo) | idem — campo textual longo explicitamente citado |
| `AssessmentCreate.title` / `AssessmentUpdate.title` | título curto da avaliação | **não alterado nesta sprint** — nenhum limite imposto por AV-S04 | título é identificador funcional curto, não um campo de texto longo; aplicar 10.000 caracteres aqui seria exatamente o uso indiscriminado que Rafael vetou. Se um limite for desejado para `title`, é uma decisão de produto separada (provavelmente um limite bem menor, ex. 200-300 caracteres), fora do escopo desta sprint. |
| `RubricCriterionInput.name` | nome curto do critério | **não alterado** — já é um campo curto por convenção de uso (sem limite hoje), não um campo de texto longo | mesmo raciocínio: não é um dos campos de texto longo citados no pedido |
| `RubricCriterionInput.description` | descrição do critério, pode ser mais longa que `name` mas é tipicamente mais curta que um enunciado de questão completo | **não alterado nesta sprint** — fora da lista de campos explicitamente identificados; se Rafael quiser um limite aqui, deve ser decidido à parte, não herdado automaticamente do limite de `statement`/`reference_answer` | preserva o princípio de não aplicar o mesmo limite a campos de propósito diferente |
| `max_score` (`Question`, `RubricCriterion`) | numérico, já `Numeric(6,2)` no banco | **limite existente preservado**: já restrito pelo tipo de coluna (até 9999.99) e por `Field(gt=0)` no Pydantic | este é exatamente o caso de "limite menor já existente" que deve ser preservado, não substituído por um limite de caracteres (não se aplica, é numérico) |
| `id` / `*_id` (todos os identificadores) | UUID gerado internamente (`gen_uuid`) | **não alterado; não é campo de entrada de usuário** | identificadores não são texto livre fornecido por usuário; aplicar `max_length=10000` aqui não faria sentido semântico e não foi o que Rafael pediu |

**Escopo explícito desta tabela — adicionado após revisão independente da
rodada 3:** esta tabela cobre apenas os campos tocados pelo caminho de
criação de `Question`/`Rubric` desta sprint. Ela **não** revisita outros
campos de texto livre já existentes no sistema fora deste caminho —
notadamente `AnswerInput.text` (resposta do aluno) e
`HumanReviewInput.justification` (justificativa de revisão humana) — que
não têm `max_length` hoje e não foram considerados nesta rodada. Isso não
é uma omissão silenciosa: é um limite de escopo explícito. Se Rafael
quiser revisar limites desses campos, é uma decisão separada, fora de
AV-S04.

**Testes exigidos (adicionados nesta rodada, antes ausentes):**
- teste do limite de quantidade: avaliação com exatamente 50 questões é
  aceita (`201`); avaliação com 51 questões é rejeitada (`422`) com
  mensagem explícita referenciando o limite;
- teste do limite de tamanho, para `statement` **e** separadamente para
  `reference_answer`: texto de exatamente 10.000 caracteres é aceito;
  texto de 10.001 caracteres é rejeitado com `422`;
- teste negativo explícito confirmando que `title` **não** é afetado pelo
  limite de 10.000 caracteres (ex.: um título de 500 caracteres, abaixo de
  10.000, não deve ser usado como prova de conformidade — o teste deve
  cobrir que nenhum `max_length` foi introduzido para `title` nesta
  sprint, não apenas que um valor curto passa);
- teste confirmando que `max_score` continua validado por `Field(gt=0)` e
  pelo limite numérico de `Numeric(6,2)`, sem interferência do novo limite
  de caracteres (que não se aplica a campos numéricos).

**Diferenciação explícita mantida:** os dois valores (50 questões; 10.000
caracteres para `statement`/`reference_answer`) são **limites funcionais
aprovados por decisão de produto**, não **capacidade comprovada por
teste de carga real** — nenhum teste de performance/carga foi executado
para validar esses números sob volume ou concorrência. Os testes listados
acima comprovam o **comportamento funcional correto no limite exato**
(aceitar/rejeitar), não a capacidade do sistema sob carga. Essa distinção
deve ser preservada na documentação de implementação: "testado" aqui
significa "o limite funciona como especificado", não "o sistema suporta
50 questões de 10.000 caracteres cada sob carga de produção".

## 4. Critérios de aceite atualizados para revisão da sprint

- **AC-01 / BL-AV-3-01:** professor com vínculo ativo à turma cria um
  rascunho com pelo menos duas questões ordenadas, cada uma com sua
  própria pontuação máxima e rubrica.
- **AC-02 / BL-AV-3-01:** `GET /v1/assessments/{id}` retorna cada questão
  exatamente uma vez, ordenada por `position` crescente.
- **AC-03 / BL-AV-3-02:** (critério herdado da rodada 2, não alterado nesta
  rodada 3 — mantido aqui apenas por numeração sequencial, sem relação com
  os itens (a)-(c) desta rodada) questões de rascunho podem ser
  adicionadas, editadas, removidas e reordenadas apenas pelo dono
  autorizado via `require_assessment_mutation` (reutilizado diretamente,
  não reimplementado); a mesma operação por outro professor retorna `403`
  sem alterar estado.
- **AC-04 / BL-AV-3-02:** a publicação falha atomicamente com `422` quando
  qualquer questão não tiver rubrica válida, quando o total da rubrica
  divergir da pontuação máxima da questão, ou quando a avaliação tiver
  zero questões.
- **AC-05 / BL-AV-3-02:** após publicada, título, conteúdo/ordem das
  questões e rubricas retornam `409` em qualquer tentativa de mutação pelos
  endpoints públicos; a única via de alteração é clonar para novo
  rascunho.
- **AC-06 / BL-AV-3-02 (clonagem):** clonar uma avaliação publicada cria um
  novo rascunho com novos IDs de questão/rubrica, `cloned_from_id`
  apontando para o original, e **nenhuma** `Answer`/`CorrectionJob`/
  `HumanReview`/`AuditEvent` do original copiada; o original permanece
  publicado e inalterado.
- **AC-07 / BL-AV-3-03:** uma resposta e correção criadas para uma questão
  publicada continuam expondo o mesmo enunciado, contexto de referência e
  versão de rubrica após qualquer operação permitida posteriormente,
  incluindo clonagem e republicação do clone com rubrica diferente — teste
  obrigatório: clonar, editar e republicar o clone, depois confirmar que o
  `CorrectionJobContext` histórico das respostas do **original** continua
  resolvendo a rubrica/versão original.
- **AC-08 / BL-AV-3-03:** o endpoint de contexto de revisão resolve a
  questão e rubrica exatas associadas à correção via `question_id`
  pinado, não "a primeira questão" da avaliação; e a seleção de "rubrica
  mais recente" em `publish_assessment` passa a usar ordenação explícita
  (`Rubric.version.desc()` ou `created_at.desc()`) em vez de depender da
  ordem de inserção da lista.
- **AC-09 / BL-AV-3-04:** o OpenAPI expõe `questions: list[QuestionInput]`
  como campo canônico de criação e `question: QuestionInput` explicitamente
  documentado como entrada legada depreciada (rejeitada em conjunto com
  `questions`); documenta `409` para mutação pós-publicação e `422` para
  violação dos limites funcionais (máximo de questões, tamanho de campo) e
  para payload com ambos os campos ou nenhum deles; os tipos do frontend
  usam exclusivamente `questions` em código novo, com o campo
  `question` computado de saída disponível para leitura de
  compatibilidade mas não usado para gerar novos payloads.
- **AC-10:** o frontend permite criar e editar pelo menos dois blocos de
  questão/rubrica, reordená-los visivelmente (persistindo via o endpoint
  transacional de reordenação), publicar apenas quando válido, exibir
  `assessment_max_score` rotulado de forma inequívoca em relação a nota
  obtida, e selecionar explicitamente uma questão para responder (sem
  fallback implícito).
- **AC-11:** reordenação transacional comprovada por teste cobrindo troca
  simples de duas posições, exclusão de uma questão intermediária com
  recompactação de posições, e rollback integral quando o payload de
  reordenação é inconsistente (ID repetido, faltante ou de outra
  avaliação).
- **AC-12:** teste de limite comprovando o comportamento exato nos valores
  aprovados — 50 questões aceitas/51 rejeitadas (`422`); 10.000 caracteres
  aceitos/10.001 rejeitados (`422`) em `statement` e, separadamente, em
  `reference_answer` — mais um teste negativo explícito de que `title` não
  recebeu nenhum `max_length` nesta sprint, e um teste confirmando que
  `max_score` continua validado por `Field(gt=0)` e pelo limite numérico
  de `Numeric(6,2)`, sem qualquer interferência do novo limite de
  caracteres (fechando a lacuna identificada pela revisão independente da
  rodada 3: a seção 3.7 já exigia esse teste, mas o AC original não o
  incluía).
- **AC-13:** todos os testes existentes de Core, AI Engine e frontend
  permanecem verdes; verificação operacional concreta: `GET
  /v1/assessments/{id}` para uma avaliação de questão única pré-existente
  continua retornando `200`, com `position=1` e o mesmo conteúdo de
  questão de antes da migração — não apenas "legível" em termos vagos. O
  valor real de `position` (trivial ou com desempate por
  `created_at`/`id`) é determinado pela consulta de verificação (`GROUP
  BY assessment_id HAVING COUNT(*) > 1`) executada contra o banco alvo
  antes da migração, não presumido do contrato de API.
- **AC-14:** os quatro endpoints de mutação de questão (adicionar, editar,
  excluir, reordenar) usam `require_assessment_mutation` como única cadeia
  de autorização, com um helper compartilhado para resolver
  `question_id → assessment` nos dois endpoints raiz-questão; teste
  cobrindo que `create_rubric` passa a usar o mesmo helper, eliminando a
  checagem de ownership duplicada hoje existente.
- **AC-15:** teste de concorrência comprovando que duas chamadas
  simultâneas de reordenação, ou uma reordenação simultânea a uma
  exclusão, sobre a mesma avaliação, não produzem posição duplicada nem
  buraco na sequência 1..N — via lock de linha (`SELECT ... FOR UPDATE`)
  adquirido no início de cada transação de mutação de posição.
- **AC-16:** `POST /v1/assessments` aceita `question` singular (payload
  legado) e o normaliza para `questions=[question]` antes de prosseguir;
  aceita `questions` plural diretamente; rejeita com `422` e mensagem
  explícita um payload contendo ambos os campos **com conteúdo real**
  (`question` não-nulo e `questions` não-vazio simultaneamente); rejeita
  com `422` um payload sem nenhum dos dois **ou com `questions: []`**
  (lista vazia tratada como equivalente a "não fornecido", não como
  "fornecido com zero itens"); um payload com `question` preenchido e
  `questions: []` é tratado como apenas `question` fornecido (aceito e
  normalizado), não como ambos fornecidos. `AssessmentOut` expõe
  `question` igual a `questions[0]` apenas quando `len(questions) == 1`,
  e `None` quando `len(questions)` for `0` ou maior que `1` — nunca "a
  primeira de várias" — além de `questions` (sempre canônico e completo).
- **AC-17:** o uso do payload legado singular é registrado via
  `log_event` de forma distinguível do uso do payload canônico plural
  — este é o único comportamento testável de AC-17; a ausência de prazo
  de descontinuação automática é uma decisão de governança registrada em
  prosa (seção 3.2), não um comportamento de código verificável por teste
  e não faz parte do critério de aceite em si.
- **AC-18:** antes de executar a migração de `position` em qualquer
  ambiente, a consulta de verificação (`GROUP BY assessment_id HAVING
  COUNT(*) > 1`) é executada contra um Postgres 16 isolado contendo pelo
  menos um caso de teste com múltiplas `Question`s por `Assessment`
  (inserido via ORM direto, simulando os caminhos existentes de
  `seed.py`/fixtures de teste); o backfill resultante é comprovado correto
  tanto no caso trivial quanto no caso de desempate por `created_at`/`id`;
  a criação da `UniqueConstraint (assessment_id, position)` usa
  `CREATE UNIQUE INDEX CONCURRENTLY` seguido de `ADD CONSTRAINT ... USING
  INDEX`, não `NOT VALID` (que não se aplica a `UNIQUE`); a coluna
  `position NOT NULL` usa o padrão `CHECK ... NOT VALID` + `VALIDATE
  CONSTRAINT` + `SET NOT NULL` para reduzir o tempo de lock exclusivo.

## 5. Plano de execução detalhado (arquivo de trabalho)

O plano de execução tarefa-a-tarefa (testes, arquivos, riscos, comandos)
permanece preservado em:

`/Users/rafaeloliveira/Projeto Estágio/.hermes/plans/2026-09-30_170000-av-s04-multiplas-questoes.md`

Este sprint document é a referência canônica de governança; o arquivo
acima é o rascunho de trabalho que a originou e precisa ser atualizado
para refletir as seções 3 e 4 revisadas (position/backfill com
`created_at`, clonagem com `cloned_from_id`, limites funcionais, novos
ACs) antes do início de qualquer implementação — está marcado como
pendência na seção 6.

## 6. O que este planejamento não autoriza (status original de planejamento — ver autorização de execução local abaixo)

> **Nota de atualização (2026-10-01):** a lista abaixo descrevia os limites
> enquanto o documento era apenas planejamento. Rafael autorizou execução
> LOCAL em 2026-10-01 (ver cabeçalho e seção 9). Os itens abaixo que diziam
> respeito à autorização de código/migração local foram superados pela
> autorização de execução local; os itens relativos a Git remoto, `avalia_dev`,
> deploy, saneamento operacional e benchmark OCR continuam vigentes sem
> alteração.

- ~~Não autoriza abrir branch de implementação de código de AV-S04.~~
  Superado: branch `feat/av-s04-multiplas-questoes` aberta em 2026-10-01
  sob autorização explícita de execução local.
- ~~Não autoriza migração Alembic real, nem contra ambiente isolado nem
  contra `avalia_dev`...~~ Superado parcialmente: migração contra
  PostgreSQL isolado com dados fictícios está autorizada; migração contra
  `avalia_dev` ou qualquer ambiente compartilhado continua **não
  autorizada**.
- ~~Não autoriza alteração de `core/app/models.py`, `schemas.py`,
  `main.py`, ou qualquer arquivo de frontend/scripts de evidência...~~
  Superado: essas alterações estão autorizadas localmente, na branch
  dedicada, seguindo exatamente o plano das seções 3 e 5.
- Não promove baseline, não faz deploy, não executa saneamento
  operacional, não reorganiza diretórios. **(vigente, sem alteração)**
- Não torna a coleta manuscrita de AV-S05B pré-requisito de AV-S04, nem o
  inverso. AV-S05B permanece investigação parcial. **(vigente)**
- O arquivo de trabalho em `.hermes/plans/` deve ser atualizado para
  refletir a rodada 3 antes do início da implementação de código (ver
  pendência na seção 8).
- Esta autorização de execução local **não inclui**: commit, push, merge
  do PR #7, qualquer ação remota, alteração em `avalia_dev`, saneamento
  operacional, deploy, promoção de baseline ou retomada do benchmark OCR.

## 7. Revisão independente

Revisão independente obtida de um subagente que não redigiu este plano,
focada exclusivamente em compatibilidade, histórico, autorização e
migração — parecer completo preservado em
`docs/governance/evidence/AV-S04/revisao_independente_2026-09-30.md`.

Veredito do revisor: a seção 3 é tecnicamente precisa contra o código real
(linhas e comportamento conferidos), mas apontou lacunas que foram
corrigidas nesta mesma rodada, antes da publicação:

| Achado do revisor | Severidade | Tratamento aplicado nesta rodada |
|---|---|---|
| 3.3 descrevia uma cadeia de autorização que não corresponde a nenhuma função real; o guard correto é `require_assessment_mutation`, não a cadeia de `POST /v1/assessments` | média | Seção 3.3 reescrita citando `require_assessment_mutation` explicitamente |
| Endpoints raiz-questão (`PATCH`/`DELETE /v1/questions/{id}`) não podem chamar `_get_owned_assessment` diretamente; precedente existente (`create_rubric`) já duplica a checagem de ownership | média | Seção 3.3 propõe helper único `_get_assessment_for_question`, reutilizado também por `create_rubric`; novo AC-14 |
| Nenhum controle de concorrência especificado para add/edit/delete/reorder sobre a mesma invariante de posição | média | Seção 3.4 agora exige `SELECT ... FOR UPDATE` nas quatro operações; novo AC-15 |
| Backfill de `position`/`created_at` descrito como se resolvesse uma ambiguidade real, quando os dados de hoje têm no máximo 1 questão por avaliação | baixa | Seção 3.4 reescrita para declarar o backfill como trivial (`position=1`) nos dados atuais, com a lógica de desempate como infraestrutura defensiva apenas |
| Risco de lock/downtime na migração de `position`/`UniqueConstraint` não quantificado | baixa | Seção 3.4 recomenda `NOT VALID` + `VALIDATE CONSTRAINT` separado |
| Offset do reorder transacional sem magnitude especificada; sem lock de concorrência | média | Seção 3.4 especifica magnitude do offset e exige o mesmo lock de linha |
| Clonagem não revisitava a seleção não determinística de rubrica (`question.rubrics[-1]` sem `order_by`), relevante para republicação de clone | média | Seção 3.1 exige `order_by` explícito antes da implementação; novo teste de regressão exigido; AC-07/AC-08 atualizados |
| "Nenhum consumidor externo" e "implantação conjunta" são leituras de ausência de evidência, não provas — não há nenhum artefato de deploy no repositório para corroborar a segunda premissa | baixa | Seção 3.2 reescrita para declarar isso explicitamente; confirmação de Rafael tratada como item bloqueante do DoR, não opcional |

Nenhum achado do revisor contestou as 7 decisões de direção aprovadas por
Rafael; todos foram correções de precisão técnica e preenchimento de
lacunas de detalhamento, aplicadas sem reabrir as decisões em si.

## 7b. Revisão independente da rodada 3 (compatibilidade, migração, limites)

Revisão independente adicional, limitada exclusivamente às mudanças desta
rodada (compatibilidade `question`/`questions`, precisão da migração de
`position`, escopo dos limites de 50 questões/10.000 caracteres) —
decisões das rodadas 1-2 (clonagem, helper de autorização, concorrência,
ordenação de rubrica) não foram reabertas nem reavaliadas. Veredito do
revisor: as mudanças desta rodada são tecnicamente sólidas e representam
uma melhoria real de precisão, com 6 achados aplicados aqui antes da
publicação:

| Achado do revisor | Severidade | Tratamento aplicado |
|---|---|---|
| `AssessmentOut.question` sempre igual a `questions[0]` reintroduziria a mesma ambiguidade que a migração pretende eliminar, só deslocada para o backend, quando houver mais de uma questão | média | Seção 3.2 corrigida: `question` só é populado quando `len(questions) == 1`; é `None` para 0 ou 2+ questões, nunca "a primeira de várias" |
| Semântica de presença (`questions: []`) não estava definida para os casos "nenhum fornecido" e "ambos fornecidos" | baixa | Seção 3.2 e AC-16 agora definem explicitamente: lista vazia conta como "não fornecido" |
| Não há nota sobre limpeza de índice `INVALID` remanescente se `CREATE UNIQUE INDEX CONCURRENTLY` for interrompido | baixa | Seção 3.4 adiciona nota de `DROP INDEX` antes de nova tentativa |
| Tabela de limites de caracteres não declarava seu próprio limite de escopo (campos fora do caminho de criação de Question/Rubric, como `AnswerInput.text`) | baixa | Seção 3.7 ganha nota explícita de escopo |
| AC-03 estava atribuído à rodada 3 sem conter nenhuma mudança desta rodada | média | AC-03 anotado como herdado da rodada 2, sem relação com os itens desta rodada |
| Seção 3.7 exigia teste de não-interferência em `max_score`, mas nenhum AC cobria isso | média | AC-12 ampliado para incluir esse teste |
| AC-13 usava "legível" sem definição operacional testável | baixa | AC-13 reescrito com verificação HTTP concreta (`GET` retorna `200`, `position=1`, mesmo conteúdo) |
| AC-17 misturava comportamento testável (log) com política não testável (ausência de prazo) | baixa | AC-17 reescrito para isolar apenas o comportamento de log como critério de aceite |

Parecer completo preservado em
`docs/governance/evidence/AV-S04/revisao_independente_rodada3_2026-09-30.md`.

## 8. Checklist de Definition of Ready (ainda em aberto)

- [x] decisões de direção da seção 3 (1-7) aprovadas por Rafael em
      2026-09-30;
- [x] revisão independente da rodada 2 obtida e achados endereçados;
- [x] valores de limite funcional (50 questões; 10.000 caracteres,
      aplicados somente a `statement`/`reference_answer`) aprovados por
      Rafael com escopo precisado (rodada 3);
- [x] decisão de compatibilidade tomada: `questions` canônico, `question`
      mantido como entrada legada sem prazo de remoção definido (rodada 3)
      — a premissa de implantação conjunta não foi confirmada, por isso a
      compatibilidade foi adotada em vez da remoção direta;
- [x] mecanismo de migração reespecificado com precisão técnica por
      constraint (rodada 3) — ainda não executado;
- [x] revisão independente da rodada 3 (mudanças desta rodada) obtida e
      achados endereçados (seção 7b);
- [x] `status` deste documento alterado para `execucao_local_autorizada`
      por decisão explícita de Rafael (2026-10-01);
- [x] base Git exata e trabalho local pendente registrados no momento da
      abertura da execução: branch `feat/av-s04-multiplas-questoes`,
      criada a partir de `main@73a1a4335a14c25a7fbafcefa9d8d5499709098f`
      (PR #8 integrado), checkout principal sem worktrees adicionais;
- [x] compatibilidade do plano com `main` atual confirmada por
      `git merge-tree --write-tree origin/main origin/docs/av-s04-planejamento`,
      sem conflitos;
- [ ] arquivo de trabalho em `.hermes/plans/` atualizado para refletir
      esta rodada antes do início da implementação;
- [ ] ambientes de teste e procedimento de validação em navegador
      definidos;
- [ ] arquivos/responsáveis e revisores independentes nomeados;
- [x] conclusão da organização local do diretório `avalia-plataform`
      (consolidação de worktrees/checkouts) — concluída via PR #8,
      merge commit `73a1a4335a14c25a7fbafcefa9d8d5499709098f`;
- [x] autorização de execução local registrada nesta rodada (2026-10-01);
      autorizações de commit/push, merge do PR #7 e ações remotas
      permanecem pendentes, fora desta autorização.

## 9. Execução local — coordenação de agentes e registro de ferramentas (2026-10-01)

**Checkout e branch:**
- repositório: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform` (sem novo worktree);
- branch dedicada: `feat/av-s04-multiplas-questoes`, criada a partir de `main@73a1a4335a14c25a7fbafcefa9d8d5499709098f`;
- nenhum commit/push realizado durante a execução local; integração ao histórico Git fica para autorização separada.

**Responsabilidades e coordenação (preenchido durante a execução; nenhuma edição concorrente no mesmo arquivo):**

| Tarefa | Responsável (agente/modelo) | Arquivos/escopo | Revisor independente |
|---|---|---|---|
| Fase 1 — backend (schema compat, position, clonagem, endpoints de coleção, limites, migração Alembic) | Codex CLI (codex-cli 0.150.1, via `codex exec --sandbox workspace-write`) | `core/app/main.py`, `core/app/models.py`, `core/app/schemas.py`, `core/alembic/versions/a9f4c2e71b06_*.py`, `docs/contracts/openapi.yaml`; ajuste mínimo de payload em `core/app/tests/test_academic_authorization.py` | subagente interno (`delegate_task`, mesmo backend de modelo desta sessão) — revisão em andamento, resultado registrado em `fase1_revisao_independente.txt` quando concluída |

Regra de coordenação: cada tarefa é atribuída a um único agente por vez; nenhum outro agente edita os mesmos arquivos até a tarefa ser concluída e revisada. Revisão de cada entrega feita por agente/modelo diferente do autor da implementação, nunca autorrevisão.

**Ferramentas/modelos efetivamente utilizados:** registrados nesta seção à medida que a execução avança, com nome do backend (ex.: Claude Code, Codex CLI, delegate_task/subagente interno) e o escopo exato de cada despacho — nunca presumidos ou genéricos.

**Limites reafirmados nesta execução local:**
- migração Alembic executada e cronometrada somente contra PostgreSQL 16 isolado, com dados fictícios;
- fluxos de interface validados em navegador real (Chrome via CDP ou equivalente), contra backend real + banco isolado;
- nenhuma ação contra `avalia_dev`;
- nenhum commit, push ou ação remota;
- nenhuma reabertura ou alteração do PR #7;
- nenhuma retomada do benchmark OCR (AV-S05B);

## 10. Encerramento da execução local (2026-10-01) — estado real

**Rodadas de revisão independente (sempre por agente diferente do autor):**

1. Rodada 1 (Fase 1, só backend inicial): **REPROVADO** — ausência de testes novos cobrindo os ACs da sprint; `delete_question` sem proteção contra `Answer` existente (órfã silenciosa em SQLite, risco de erro não tratado em Postgres).
2. Correções da rodada 1 aplicadas (Codex): proteção síncrona de `delete_question` (checagem prévia 409), migração com padrão `CHECK NOT VALID`+`VALIDATE`+`SET NOT NULL` também para `created_at`, suíte `test_assessment_multiple_questions.py` criada/ampliada para 20 testes (Fase 2b, Codex).
3. Rodada 2 (estado completo: backend+migração+frontend+navegador): **REPROVADO** — único bloqueador objetivo: race condition TOCTOU real entre `delete_question` e `create_answer`, confirmada empiricamente em PostgreSQL real (reprodução determinística e via threads HTTP), podendo propagar `IntegrityError` não tratada (`500`) em vez de `409`. Todos os demais ACs (01–18) CUMPRIDOS nesta rodada.
4. Correção aplicada (Hermes, mesma sessão que recebeu o achado): `try/except IntegrityError` em `delete_question` em torno de `db.delete`/`db.flush`, com rollback e o mesmo `409` de domínio. TDD próprio: RED confirmado (script determinístico + teste pytest revertido), GREEN confirmado (4x script determinístico, 5x via threads HTTP reais, suíte completa). Novo teste de regressão permanente: `test_ac11_delete_create_answer_race_returns_409`. Relatório: `docs/governance/evidence/AV-S04/pacote-execucao-local/correcao_race_delete_create_answer_2026-10-01.md`.
5. Rodada 3 (revisão independente da correção, agente diferente do autor da correção): **APROVADO** — reprodução própria e independente da race contra PostgreSQL real (script próprio, não reaproveitado), 5/5 GREEN pós-correção, RED confirmado revertendo a correção, teste de regressão inspecionado linha a linha e confirmado não-tautológico, diff isolado em `main.py` confirmado como exatamente o bloco try/except de 7 linhas (nenhuma outra alteração de produção desde a rodada 2).

**Estado final por critério de aceite (AC-01 a AC-18):** todos CUMPRIDOS, conforme consolidado nas rodadas 2 e 3 de revisão independente (ver relatórios completos no pacote de evidências).

**Testes automatizados:** suíte backend completa `89 passed` (68 pré-existentes + 21 da sprint, incluindo o teste de regressão da race), `ruff check` limpo. Frontend: `npm run lint` e `npm run build` limpos. Navegador real (Playwright/Chrome, script `browser_av_s04_flow.js`): fluxo completo (criação com 2+ questões, reordenação persistida, publicação com seleção explícita de questão, clonagem com navegação) — `BROWSER_REAL_CHROME_GREEN`. Migração PostgreSQL 16 isolada: cenários fresh/recovery-de-índice-inválido/checkpoint-válido — `ALL GREEN`, reexecutado múltiplas vezes nesta sessão (não apenas relatado por terceiro). Concorrência `SELECT...FOR UPDATE` (reorder×reorder): validado em Postgres real — `POSTGRES_FOR_UPDATE_CONCURRENCY_GREEN`.

**Pendências reais (não bloqueantes para o estado local, mas não cobertas nesta sprint):**
- `create_answer` continua sem lock explícito próprio no `Assessment` — a proteção contra a race com `delete_question` vem do tratamento de `IntegrityError`, que é suficiente para a invariante de integridade referencial, mas não serializa outras combinações hipotéticas de mutação concorrente envolvendo `Answer` fora do escopo desta sprint (ex.: duas `Answer` concorrentes para a mesma questão — fora de escopo, não especificado nos ACs).
- `AssessmentOut`/`Question` em `frontend/src/types.ts` mantêm campos legados `question?`/`rubric?` no typing por compatibilidade de leitura — não usados para montar payloads novos; não é bug, é a decisão de compatibilidade da seção 3.
- Nenhum commit, push, merge do PR #7 ou ação remota foi realizado nesta execução local, conforme autorização (`DEC-AV-028`). A integração ao histórico Git requer autorização separada e explícita de Rafael, com revisão do diff exato antes de qualquer `git add`/`commit`.

**Pacote recuperável:** `docs/governance/evidence/AV-S04/pacote-execucao-local/`, incluindo inventário com checksums (`inventario_checksums_2026-10-01.md`, regenerado após a correção final), relatórios de cada rodada, scripts de validação PostgreSQL reexecutáveis, e evidência de navegador real.

- pacote recuperável local mantido em localização durável dentro do projeto (não em `/tmp`), incluindo arquivos novos e base Git, até a apresentação final para decisão de publicação.
