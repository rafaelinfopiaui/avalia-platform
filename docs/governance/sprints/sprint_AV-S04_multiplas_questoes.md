---
id: "AV-S04"
status: planejamento_detalhado_com_revisao_independente_aguardando_aprovacao_final
objetivo_aprovado_por: "Rafael (2026-09-30): decisões 1-7 da seção 3 aprovadas em princípio; detalhamento técnico e revisão independente desta rodada ainda não homologados; implementação continua não autorizada"
consolidador: "Hermes"
baseline_entrada: "main@ba6f4074f49f87461c515081964a2aff6202e6cb (PR #5 + PR #6 integrados em 2026-09-30)"
depende_de: "AV-S03 (homologada e integrada); independente da coleta manuscrita de AV-S05B"
---

# AV-S04 — Múltiplas questões por avaliação (planejamento detalhado)

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

### 3.2 `questions` como contrato alvo — APROVADA, com levantamento de consumidores

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

**Consumidores externos:** busca em todo o repositório por indícios de
cliente externo, SDK, aplicativo mobile ou versionamento de API (`/v2`,
"integração com terceiro") não retornou nenhuma ocorrência além de
referências institucionais não técnicas. **Isso é um achado de ausência
de evidência dentro do escopo deste repositório, não uma prova de
ausência de consumidor** — uma busca em um único repositório nunca pode
provar que não existe cliente em produção, coleção HTTP salva fora do
controle de versão, ou artefato implantado anterior a este snapshot. A
revisão independente confirmou que não há nenhum `Dockerfile`,
`docker-compose` ou workflow de deploy neste repositório — `ci.yml`
executa apenas testes/lint/build por componente, sem nenhum job de
deploy. Isso significa que a premissa "implantação conjunta
backend/frontend" não tem nenhum artefato de automação para corroborá-la
dentro do repositório: a afirmação de implantação conjunta é inteiramente
não verificável a partir deste código-fonte, não apenas "ainda não
confirmada".

**Proposta — atualização conjunta, sem alias transitório, condicionada à
confirmação operacional de Rafael:**
Como não há consumidor externo evidenciado no repositório nem automação de
deploy desacoplado entre backend e frontend neste código, a evidência
disponível não aponta para a necessidade de compatibilidade transitória
(`question` aceito como alias depreciado). Esta é uma leitura de ausência
de evidência contrária, não uma prova positiva de implantação conjunta —
a confirmação operacional de Rafael sobre como backend e frontend são
hoje efetivamente implantados é uma condição bloqueante de Definition of
Ready, não um item opcional da checklist, antes de autorizar a mudança
de contrato sem alias.

1. `AssessmentCreate.question` é removido e substituído por
   `questions: list[QuestionInput]` (mínimo 1 item) no mesmo PR que
   atualiza `main.py`, os testes Python listados acima, os três scripts de
   evidência do AV-S02/AV-S03, `frontend/types.ts`, `api.ts`,
   `AssessmentEditorPage.tsx`, `AnswerPage.tsx`, `ReviewPage.tsx` e
   `docs/contracts/openapi.yaml`.
2. Nenhum deploy parcial (backend sem frontend ou vice-versa) é usado em
   produção hoje — confirmar essa premissa operacional com Rafael antes da
   implementação, já que não há evidência de pipeline de deploy
   desacoplado inspecionada nesta auditoria de código.
3. Caso essa premissa se revele falsa (existir deploy independente de
   backend/frontend), a decisão de contrato único precisa ser revisitada
   com uma janela de compatibilidade — isso é condição suspensiva
   explícita, não uma reversão da aprovação.

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

### 3.4 `position` persistida com unicidade por avaliação — APROVADA

**Schema:** `Question.position: int`, não-nulo, `UniqueConstraint
("assessment_id", "position")`, criado via migração Alembic.

**Backfill determinístico — corrigido após revisão independente:** a
redação original tratava isso como uma ambiguidade real de ordenação
multi-linha. Não é: sob o contrato atual (singular), toda `Assessment`
existente tem **no máximo uma `Question`**. Isso significa que o backfill
real, para os dados de hoje, é trivial — `position = 1` para toda
`Question` legada, sem nenhuma questão de ordenação a resolver. A lógica
de `created_at`/`id` como critério de desempate é infraestrutura
defensiva apenas para o caso futuro de uma segunda rodada de backfill
após falha parcial (ex.: migração interrompida no meio e reexecutada com
múltiplas questões já criadas pelos novos endpoints) — não resolve uma
ambiguidade presente real. Mesmo assim, se a coluna `created_at` for
adicionada, a migração deve declarar explicitamente como os valores
legados serão populados: usar `server_default=now()` apenas defronta
nova linha; para o `UPDATE` de backfill das linhas existentes, usar
exatamente o mesmo timestamp da migração para todas elas é aceitável
*somente* porque, combinado com `id` como desempate e position=1 fixo
para todas (caso de hoje), nenhuma ordem relativa entre `Question`s de
avaliações diferentes importa — o desempate só seria exercitado dentro de
uma mesma avaliação com múltiplas questões, o que não existe nos dados
legados.

**Risco de lock/downtime:** adicionar uma coluna não-nula com `UPDATE` de
backfill e, em seguida, uma `UniqueConstraint (assessment_id, position)`
em uma tabela referenciada por `Rubric`/`Answer` é um padrão clássico de
lock de tabela no Postgres durante o `UPDATE` e durante a validação da
constraint. Como o volume de `Question` em produção hoje é pequeno (no
máximo uma por avaliação existente), o risco é baixo neste momento, mas a
migração deve, por disciplina, adicionar a constraint como `NOT VALID` e
validar em um passo `VALIDATE CONSTRAINT` separado, para evitar lock
exclusivo prolongado se o volume crescer antes da execução real da
migração.

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

### 3.7 Mínimo de uma questão para publicação; limites de máximo e tamanho — APROVADO o mínimo; valores de máximo propostos nesta rodada, pendentes de confirmação

**Mínimo (aprovado):** publicação exige pelo menos 1 questão com rubrica
válida (critério já coberto pelo AC-04 existente).

**Máximo de questões por avaliação — proposta funcional, não testada:**
Não existe hoje nenhum teste de carga, benchmark de payload ou limite
configurado no FastAPI/Pydantic para o tamanho da lista `questions`. Não
há capacidade comprovada por teste. Proposta de **limite funcional de
produto**, não de capacidade técnica: **50 questões por avaliação**.
Fundamento: é generoso para o caso de uso real (prova/avaliação
acadêmica dificilmente ultrapassa esse número) e evita payloads
desproporcionais sem restringir nenhum uso legítimo conhecido. Isso é uma
proposta de guarda-corpo de produto, a ser confirmada ou ajustada por
Rafael — não foi derivada de nenhum teste de performance.

**Tamanho de campos de texto — proposta funcional, não testada:**
`Question.statement` e `Question.reference_answer` são `Text` no banco
(sem limite de tamanho no schema do banco) e não têm `max_length` no
Pydantic hoje. Não há teste de carga que comprove um limite seguro.
Proposta de limite funcional: **10.000 caracteres** para `statement` e
para `reference_answer` cada, validado via `Field(max_length=10000)` no
Pydantic. Fundamento: cobre com folga qualquer enunciado ou resposta de
referência textual legítima (muito acima de um parágrafo longo), sem
abrir a porta para payloads de tamanho arbitrário usados como vetor de
abuso. Novamente, este número é uma proposta de guarda-corpo funcional,
não um valor derivado de teste de capacidade real do sistema.

**Diferenciação explícita exigida por Rafael:** os dois valores acima
(50 questões; 10.000 caracteres) são **limites funcionais propostos**,
escolhidos por julgamento de produto a partir das restrições existentes
(nenhuma restrição técnica hoje), e não **capacidade comprovada por
teste** — nenhum teste de carga foi executado para validar esses números
especificamente. Caso Rafael aprove, a tarefa de implementação deve criar
um teste que comprove o comportamento no limite exato (ex.: 50 questões
aceitas, 51 rejeitadas com `422`) como parte do Task 1 (testes falhando
antes da implementação).

## 4. Critérios de aceite atualizados para revisão da sprint

- **AC-01 / BL-AV-3-01:** professor com vínculo ativo à turma cria um
  rascunho com pelo menos duas questões ordenadas, cada uma com sua
  própria pontuação máxima e rubrica.
- **AC-02 / BL-AV-3-01:** `GET /v1/assessments/{id}` retorna cada questão
  exatamente uma vez, ordenada por `position` crescente.
- **AC-03 / BL-AV-3-02:** questões de rascunho podem ser adicionadas,
  editadas, removidas e reordenadas apenas pelo dono autorizado via
  `require_active_class_link`/`_get_owned_assessment`; a mesma operação
  por outro professor retorna `403` sem alterar estado.
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
  plural como único contrato de criação (sem campo singular residual) e
  documenta `409` para mutação pós-publicação e `422` para violação dos
  limites funcionais (máximo de questões, tamanho de campo); os tipos do
  frontend removem o fallback singular em `AssessmentEditorPage.tsx`,
  `AnswerPage.tsx` e `ReviewPage.tsx`.
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
  propostos (50 questões aceitas/51 rejeitadas; 10.000 caracteres aceitos/
  10.001 rejeitados), caso os valores numéricos sejam confirmados por
  Rafael antes da implementação.
- **AC-13:** todos os testes existentes de Core, AI Engine e frontend
  permanecem verdes; registros legados de questão única continuam
  legíveis após o backfill de `position`/`created_at`.
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

## 6. O que este planejamento não autoriza

- Não autoriza abrir branch de implementação de código de AV-S04.
- Não autoriza migração Alembic real, nem contra ambiente isolado nem
  contra `avalia_dev`.
- Não autoriza alteração de `core/app/models.py`, `schemas.py`,
  `main.py`, ou qualquer arquivo de frontend/scripts de evidência listados
  na seção 3.2.
- Não promove baseline, não faz deploy, não executa saneamento
  operacional, não reorganiza diretórios.
- Não torna a coleta manuscrita de AV-S05B pré-requisito de AV-S04, nem o
  inverso. AV-S05B permanece investigação parcial.
- Não altera o arquivo de trabalho em `.hermes/plans/` ainda — fica
  marcado como pendência explícita para antes da implementação, não feito
  nesta rodada por não ter sido pedido.

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

## 8. Checklist de Definition of Ready (ainda em aberto)

- [x] decisões de direção da seção 3 (1-7) aprovadas por Rafael em
      2026-09-30;
- [x] revisão independente obtida e achados endereçados no detalhamento
      técnico (seção 7);
- [ ] valores numéricos propostos em 3.7 (50 questões; 10.000 caracteres)
      confirmados ou ajustados por Rafael;
- [ ] premissa operacional de deploy conjunto backend/frontend (seção 3.2)
      confirmada por Rafael — tratada como item bloqueante, não opcional;
- [ ] `status` deste documento alterado para `ready` por decisão explícita
      de Rafael;
- [ ] base Git exata e trabalho local pendente registrados no momento da
      abertura da execução (rito de `execution_policy.md` §3);
- [ ] arquivo de trabalho em `.hermes/plans/` atualizado para refletir
      esta rodada antes do início da implementação;
- [ ] ambientes de teste e procedimento de validação em navegador
      definidos;
- [ ] arquivos/responsáveis e revisores independentes nomeados;
- [ ] autorizações de implementação, Git e ações remotas registradas
      separadamente desta autorização de planejamento.
