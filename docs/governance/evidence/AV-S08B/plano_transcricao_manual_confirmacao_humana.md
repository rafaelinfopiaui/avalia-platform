# Plano técnico — Transcrição manual e confirmação humana (próxima fatia pós-DEBT-AV-014)

> Documento de PLANEJAMENTO + EXECUÇÃO LOCAL autorizada (AV-S08B). Branch
> dedicada `docs/av-s08b-plano-transcricao-manual` (planejamento) e
> `feat/av-s08b-transcricao-manual` (implementação, a criar), ambas no
> checkout principal, sem worktree novo. NÃO publicadas (sem stage/commit/
> push nesta rodada, por instrução explícita de Rafael).
>
> **Revisão limitada do Antigravity concluída (rodada 1, plano completo):**
> APROVADO COM RESSALVAS (2026-10-14T09:35, parecer completo em
> `evidence/AV-S08B/revisao_plano_transcricao_manual_antigravity.md`). As 7
> ressalvas de nomenclatura/contrato (ACH-01 a ACH-07) foram incorporadas a
> este documento — ver §3.1, §3.3, §4 e §11, marcadas inline como "correção
> pós-revisão". A ressalva crítica (ACH-01, lacuna de leitura do rascunho)
> foi a única classificada como bloqueante para implementação; está
> corrigida nesta versão.
>
> **Decisões de produto DP-1/DP-2/DP-3 APROVADAS por Rafael em `DEC-AV-040`
> (2026-10-14)** — ver §2 para o detalhamento de cada decisão aplicada.
> Controle de concorrência por versão (`transcription_version`) exigido
> adicionalmente por Rafael nesta mesma autorização.
>
> **Revisão limitada do Antigravity concluída (rodada 2, só concorrência e
> DP-1/2/3):** APROVADO COM RESSALVA PONTUAL DOCUMENTAL (2026-10-14T09:55,
> parecer completo em
> `evidence/AV-S08B/revisao_plano_transcricao_manual_antigravity_v2_concorrencia.md`).
> Mecanismo de concorrência confirmado tecnicamente correto (transação de
> banco, não lock em memória); DP-2 aplicada com consistência em todas as
> seções técnicas; único achado (ACH-08) era este próprio cabeçalho, já
> corrigido nesta versão do documento.

## 1. Posição na trilha vigente e IDs reais do backlog

Conferido em `docs/governance/backlog/backlog_tecnico_avalia.md` (Etapa 4B,
subseção D "Conferência da transcrição" e parte da subseção E):

| ID | Item real do backlog | Parte coberta por esta fatia |
|---|---|---|
| `BL-AV-4B-10` | Tela de conferência exibindo imagem e texto extraído lado a lado | **Parcial** — nesta fatia não há "texto extraído" (sem OCR); a tela exibe imagem + campo de texto para digitação manual. O layout lado a lado é reaproveitado, não o conteúdo pré-preenchido. |
| `BL-AV-4B-11` | Edição e confirmação da transcrição pelo professor; preservação de texto bruto extraído, texto corrigido e histórico da confirmação | **Parcial** — "texto bruto extraído" não existe sem OCR (ver §7 "Sem invenção de OCR" abaixo); a parte de edição/confirmação/histórico aplicável à origem MANUAL é o escopo real desta fatia. |
| `BL-AV-4B-13` | Transcrição manual quando a extração falhar | **Coberto integralmente nesta fatia** — como não há OCR ainda, toda transcrição desta fatia é manual por definição (não é "quando falhar", é o único caminho disponível hoje). |
| `BL-AV-4B-14` | Vincular a resposta confirmada ao aluno/avaliação/questão; impedir que a correção inicie antes da confirmação humana da transcrição | **Coberto** — já parcialmente garantido pelo guard existente em `request_correction` (`ANSWER_NOT_TRANSCRIBED`); esta fatia fecha o caminho que leva a `TRANSCRICAO_CONFIRMADA` para origem manual. |
| `BL-AV-4B-15` | Preservar a cadeia imagem → execução OCR → transcrição confirmada → correção → revisão | **Parcial** — o elo "execução OCR" não existe nesta fatia (sem OCR); o elo "transcrição confirmada" de origem manual e os elos já existentes (correção → revisão) são preservados e vinculados. |
| `BL-AV-4B-16` | Idempotência/deduplicação em reenvios e retentativas de imagem | **Não coberto nesta fatia** — refere-se a reenvio/retentativa de upload de imagem (já implementado em AV-S06B), não à confirmação de transcrição. Fora de escopo. |

**Itens explicitamente NÃO encerrados por esta fatia** (mais amplos que a parte
manual implementada):
- `BL-AV-4B-10` permanece **não encerrado** — falta o componente de OCR/extração
  automática que pré-preenche o texto; esta fatia entrega apenas a variante
  manual da tela.
- `BL-AV-4B-11` permanece **não encerrado** — falta "texto bruto extraído"
  (requer OCR); esta fatia entrega "texto digitado" e "texto confirmado",
  sem o elo de extração automática.
- `BL-AV-4B-07`, `BL-AV-4B-08`, `BL-AV-4B-09` (preparação/extração local) seguem
  **inteiramente fora de escopo** — dependem de OCR, não autorizado.
- `BL-AV-4B-12` (sinalização de incerteza de leitura) **não se aplica** à
  origem manual (não há "incerteza de leitura" de uma máquina quando quem
  digitou foi o professor) — não é um débito desta fatia, é inaplicável por
  natureza até existir OCR.

Nenhum destes itens será marcado como "encerrado" no backlog ao fim desta
fatia — apenas a fração manual, explicitamente qualificada como tal.

## 2. Decisões de produto — APROVADAS (DEC-AV-040, 2026-10-14)

> Seção reescrita após aprovação de Rafael. As 3 decisões de produto
> identificadas na v1 deste plano foram decididas — ver `DEC-AV-040` em
> `registers/decisions.md` para o registro formal. Nenhuma foi assumida
> unilateralmente; a decisão é de Rafael, registrada e aplicada aqui.

### 2.1 DP-1 — Um rascunho atual por resposta (decidido)
Um único rascunho ATUAL por `Answer`, armazenado em
`manual_transcription_draft` (coluna simples, não lista). Não há múltiplos
rascunhos concorrentes selecionáveis pelo usuário — salvar um novo rascunho
sobrescreve o anterior. O **histórico de alterações** é preservado via
`AuditEvent` (cada `PATCH .../draft` gera um evento com o texto anterior em
`before_json` e o novo em `after_json`), reaproveitando a infraestrutura já
existente — não cria tabela de versionamento dedicada. O rascunho é
recuperável após reload/nova sessão (ver §3.1, "Leitura do rascunho").

### 2.2 DP-2 — Confirmação definitiva, sem reabertura nesta fatia (decidido)
Depois de `POST .../confirm` bem-sucedido, a transcrição não pode ser
reaberta/editada nesta fatia — `transcription_status =
TRANSCRICAO_CONFIRMADA` é terminal. Qualquer tentativa de `draft` ou
`confirm` subsequente para a mesma resposta retorna 409
`TRANSCRIPTION_ALREADY_CONFIRMED` (ver §3.3/§6 — unificado, sem distinção
422/409 entre draft e confirm, já que ambos são agora conflito de estado
terminal). **Requisito de UX decorrente**: antes de confirmar, a interface
DEVE apresentar imagem e texto lado a lado para revisão final e exibir aviso
explícito de que a confirmação encerra a edição nesta versão (critério
ACD-13, atualizado). Retificação pós-confirmação é uma fatia futura
separada (fora de escopo aqui), que — por decisão já registrada — NÃO
sobrescreverá o histórico desta confirmação; apenas adicionará um novo
elo à cadeia preservando o anterior (mesmo princípio de imutabilidade de
`HumanReview` já usado no projeto).

### 2.3 DP-3 — Idempotência, conflito e não-disparo automático (decidido)
- Confirmação repetida com o MESMO conteúdo: idempotente, 200, sem novo
  `AuditEvent` de confirmação (nenhuma duplicação de evento).
- Tentar alterar o texto já confirmado — com conteúdo diferente — retorna
  conflito (409 `TRANSCRIPTION_ALREADY_CONFIRMED`), **independente de já
  existir `CorrectionJob`/`HumanReview` ou não** para a resposta. Nunca
  sobrescreve silenciosamente.
- Confirmar a transcrição NUNCA dispara `request_correction`
  automaticamente — permanece ação HTTP distinta, deliberada, do professor
  (mesmo princípio já garantido na v1 deste plano e confirmado pela revisão
  do Antigravity, ACH blindagem §9).

### 2.4 Requisito adicional desta rodada — controle de concorrência por versão
Não coberto pela v1 do plano; exigido agora por Rafael: salvar rascunho e
confirmar devem verificar a **versão esperada** do recurso antes de mutar,
seguindo o mesmo padrão já usado em `Rubric.version`
(`core/app/models.py:246`, inteiro incremental). Isso impede:
- Sobrescrita silenciosa de rascunho entre abas/sessões (A salva rascunho
  com `version=3`; B, que carregou `version=2`, tenta salvar por cima sem
  saber do update de A — rejeitado).
- Duas confirmações concorrentes produzindo conteúdos finais divergentes ou
  eventos de auditoria duplicados (lock otimista via `version` + transação
  atômica de banco resolve a corrida; apenas uma das duas chamadas
  concorrentes vence, a outra recebe conflito).

Ver §3.1 (modelo) e §6 (contrato de concorrência) para o detalhamento
técnico desta decisão.

## 2.5 Decisões técnicas (resolvidas nesta proposta, dentro do já aprovado)
- Contrato dos dois endpoints de mutação (rota, payload, autorização).
- Modelagem de histórico de edições (reuso de `AuditEvent`, decidido).
- Modelagem de controle de concorrência (campo `version`, mesmo padrão de
  `Rubric.version`).
- Regras de concorrência/idempotência na confirmação (detalhadas em §6).

## 3. Contrato técnico proposto (menor mudança coerente, mesmo padrão do repo)

### 3.1 Modelo de dados

Reaproveita o padrão já existente de `AuditEvent` (tabela genérica de
auditoria com `before_json`/`after_json`) em vez de criar uma tabela nova
dedicada a histórico de transcrição — evita duplicar infraestrutura de
auditoria. Nova tabela proposta apenas para o que `AuditEvent` não cobre
(estado atual do rascunho, que precisa ser consultável sem reconstruir a
partir do log):

```python
# Novo campo em Answer (nullable, só populado para origem MANUAL/IMAGE):
manual_transcription_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
transcription_confirmed_by_id: Mapped[str | None] = mapped_column(
    String, ForeignKey("users.id"), nullable=True
)
transcription_confirmed_at: Mapped[datetime | None] = mapped_column(
    DateTime, nullable=True
)
# Controle de concorrência (DEC-AV-040, requisito novo): mesmo padrão já
# usado por Rubric.version (core/app/models.py:246) — inteiro incremental,
# incrementado a cada mutação bem-sucedida (draft salvo ou confirmação).
transcription_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
```
Nomenclatura revisada (achado ACH-02 do Antigravity): as colunas de
confirmação usam `transcription_confirmed_by_id`/`transcription_confirmed_at`
**sem** prefixo `manual_` — a confirmação é sempre humana, venha o texto de
digitação manual ou (no futuro, fora de escopo) de OCR revisado; prefixar com
`manual_` geraria retrabalho de nomenclatura quando `BL-AV-4B-11` (parte OCR)
for implementado. Só `manual_transcription_draft` mantém o prefixo, porque
esse campo é especificamente o rascunho de digitação manual (distinto de um
eventual rascunho de saída de OCR). `transcription_version` segue o mesmo
raciocínio — nome sem prefixo `manual_`, reutilizável quando OCR existir.

- `text` continua `NULL` até a confirmação (mantém o invariante existente da
  `CheckConstraint` `ck_answers_source_text` sem alteração — IMAGE pode ter
  `text IS NULL`).
- `manual_transcription_draft` guarda o rascunho salvo mas não confirmado
  (distinto de `text`, que só é preenchido na confirmação — ver §3.3).
- `transcription_version` começa em `0` (resposta IMAGE recém-criada, sem
  rascunho nem confirmação); incrementado em +1 a cada `PATCH .../draft`
  bem-sucedido e +1 na confirmação bem-sucedida. O cliente envia a versão
  que acredita ser a atual (`expected_version`) em todo `PATCH`/`POST`
  destes dois endpoints; se não bater com a versão real no banco no momento
  da transação, a mutação é rejeitada com 409 (ver §6, detalhamento do
  controle de concorrência decidido em DEC-AV-040 §2.4).
- Ao confirmar: `text = manual_transcription_draft` (ou o texto enviado na
  própria chamada de confirmação, ver §3.3), `transcription_status =
  TRANSCRICAO_CONFIRMADA`, `transcription_confirmed_by_id = user.id`,
  `transcription_confirmed_at = now()`, `transcription_version += 1`.
- Histórico de versões (rascunhos anteriores e a confirmação) registrado via
  `AuditEvent` (`action="manual_transcription_draft_saved"` /
  `"manual_transcription_confirmed"`, `resource_type="Answer"` — PascalCase,
  seguindo exatamente a convenção já usada em todo o código para
  `Assessment`/`Question`/`Rubric`/`CorrectionJob`, corrigido do rascunho
  inicial deste plano que usava minúsculas —, `before_json`/`after_json` com
  o texto e a versão), reaproveitando a infraestrutura de auditoria já
  existente — sem nova tabela de versionamento dedicada.
- **Leitura do rascunho (correção mandatória, achado crítico ACH-01 da
  revisão do Antigravity):** a primeira versão deste plano não definia
  nenhum caminho de leitura para `manual_transcription_draft`, criando um
  "buraco negro" de gravação sem leitura — o frontend não teria como
  recuperar o rascunho salvo após reload (F5) ou reabertura da tela, o que
  inviabilizaria a UX pretendida. Corrigido: `AnswerOut` (e por herança
  `AnswerWithImagesOut`) passam a incluir os campos opcionais
  `manual_transcription_draft: Optional[str] = None` e
  `transcription_version: int` (sempre presente, default `0`). Como `GET
  /v1/assessments/{id}/image-answers` (DEBT-AV-014, já integrado) já retorna
  `AnswerWithImagesOut` para cada resposta, o rascunho E a versão atual
  ficam disponíveis automaticamente nessa mesma listagem, sem endpoint `GET`
  adicional nem nova requisição — o frontend sempre sabe qual
  `expected_version` enviar na próxima mutação. Isso também corrige a
  afirmação equivocada do rascunho inicial deste plano (§4, versão anterior)
  de que o rascunho "não aparece em nenhuma leitura" — ele passa a aparecer,
  deliberadamente, apenas para o próprio professor dono (a mesma autorização
  por propriedade de DEBT-AV-014 já garante que só quem pode ver a resposta
  vê o rascunho).
- Nenhuma migração em bancos protegidos nesta fase de planejamento; a
  migração Alembic em si só seria aplicada em PostgreSQL isolado na fase de
  implementação (não autorizada ainda).

### 3.2 Autorização (mutação — não é leitura histórica)

Diferente do endpoint de retomada (DEBT-AV-014, leitura), salvar rascunho e
confirmar transcrição são **mutações** e seguem o padrão já usado por
`create_text_answer`/`request_correction`:
```python
assessment = _get_owned_assessment(db, question.assessment_id, user)
require_assessment_mutation(db, user, assessment)  # exige vínculo ativo de turma quando houver
```
Isto é deliberadamente **diferente** do endpoint de leitura histórica da
fatia anterior — mutar uma resposta exige vínculo ativo (mesma regra já
aplicada a `request_correction`/`create_text_answer`/`create_image_answer`),
não é consulta.

### 3.3 Endpoints propostos

```
PATCH /v1/answers/{answer_id}/manual-transcription/draft
  body: { "text": str, "expected_version": int }
  response_model: AnswerWithImagesOut (mesmo DTO já retornado por
    create_image_answer e list_image_answers — consistência de contrato,
    achado ACH-06 do Antigravity)
  - Salva/sobrescreve manual_transcription_draft. NÃO altera `text` nem
    `transcription_status`. `transcription_version += 1` em cada chamada
    bem-sucedida (controle de concorrência, DEC-AV-040 §2.4 — ver §6).
  - 404 resposta/questão/avaliação inexistente; 403 não-dono ou sem vínculo
    ativo; 401 sem token.
  - 422 ANSWER_NOT_IMAGE_SOURCE se a resposta já é TEXT (rascunho manual só
    se aplica a respostas cuja origem é IMAGE, conforme DEC-AV-037).
  - 409 TRANSCRIPTION_ALREADY_CONFIRMED se já confirmada (DP-2, DEC-AV-040 —
    sem reabertura nesta fatia; rascunho é sempre bloqueado após
    confirmação, decisão fechada, não mais condicional a decisão futura).
  - 409 TRANSCRIPTION_VERSION_CONFLICT se `expected_version` não bater com
    `transcription_version` atual no banco (edição concorrente entre
    abas/sessões — requisito novo de DEC-AV-040 §2.4; corpo da resposta
    inclui a versão e o rascunho/texto atuais para o cliente decidir, mesmo
    padrão de "devolver o estado existente" já usado em
    REVIEW_ALREADY_EXISTS).

POST /v1/answers/{answer_id}/manual-transcription/confirm
  body: { "text": str, "expected_version": int }  # texto final; pode vir de draft ou ser enviado direto
  response_model: AnswerWithImagesOut (mesmo DTO; ACH-06)
  - Valida texto não-vazio (mesmo padrão de ANSWER_TEXT_REQUIRED já usado em
    create_text_answer): 422 ANSWER_TEXT_REQUIRED se vazio/só espaços.
  - Rejeita confirmação para source=TEXT com 422 ANSWER_NOT_IMAGE_SOURCE
    (mesmo código do draft — resposta textual já nasce confirmada, nada a
    transcrever; cenário explicitado após revisão, achado ACH-07).
  - Se já confirmada (DP-2, confirmação é definitiva — não há mais
    condicional a "decisão futura", a decisão já foi tomada): ver §6
    "confirmação repetida e edições concorrentes" — mesmo conteúdo é
    idempotente (200, sem novo AuditEvent); conteúdo diferente retorna 409
    TRANSCRIPTION_ALREADY_CONFIRMED com o estado já confirmado no corpo
    (mesmo padrão de REVIEW_ALREADY_EXISTS em review_correction).
  - 409 TRANSCRIPTION_VERSION_CONFLICT se `expected_version` não bater com
    a versão atual — mesmo mecanismo do draft, crítico aqui para impedir
    que duas confirmações concorrentes produzam textos finais divergentes
    (ver §6, DEC-AV-040 §2.4: só uma das duas chamadas concorrentes vence).
  - Em caso de sucesso: text = payload.text; transcription_status =
    TRANSCRICAO_CONFIRMADA; transcription_confirmed_by_id/_at
    preenchidos; transcription_version += 1; AuditEvent de confirmação
    registrado; manual_transcription_draft limpo (não é mais necessário, o
    texto confirmado já está em `text`).
  - NÃO cria CorrectionJob. NÃO chama request_correction. Apenas libera a
    pré-condição que request_correction já verifica (ver §9).
  - 403/404/401 mesmo padrão dos demais endpoints de mutação.
```

Não propõe reaproveitar `PATCH` genérico de `Answer` (não existe hoje) — dois
endpoints de escopo estreito, no mesmo espírito de `create_image_answer`
(endpoint dedicado, não um CRUD genérico).

## 4. Distinção rascunho vs. confirmação explícita

- **Rascunho** (`draft`): estado de trabalho em progresso, pode ser salvo
  várias vezes, nunca aciona `transcription_status` nem preenche `text`.
  **Correção (pós-revisão):** o rascunho É exposto, mas só ao próprio
  professor dono — `GET /v1/assessments/{id}/image-answers` (DEBT-AV-014,
  já integrado) passa a incluir o campo `manual_transcription_draft` no DTO
  retornado, pela mesma autorização por propriedade já existente nesse
  endpoint. Isso é o que torna a retomada do rascunho possível após F5/nova
  sessão (ver §3.1 "Leitura do rascunho" para o detalhe técnico e a correção
  do erro original deste plano).
- **Confirmação explícita** (`confirm`): ação distinta, deliberada, que exige
  o texto completo no momento da chamada (não "confirma o último rascunho
  silenciosamente" — o professor vê e reafirma o texto, mesmo que seja o
  rascunho que acabou de salvar). **Requisito de UX (DEC-AV-040 §2.2):** a
  interface DEVE apresentar imagem e texto lado a lado para revisão final
  antes do clique de confirmar, com aviso explícito de que a ação encerra a
  edição nesta versão do produto. Transição de estado **terminal e
  irreversível nesta fatia** (decidido — DP-2 fechou a questão de reabertura:
  NÃO há reabertura; retificação é fatia futura separada, sem sobrescrever
  o histórico desta confirmação).

## 5. Rejeição de confirmação sem texto válido

Mesmo padrão já usado em `create_text_answer` (`ANSWER_TEXT_REQUIRED`, 422,
`payload.text.strip()` vazio rejeitado). Nenhum texto placeholder, nenhuma
string vazia aceita como "confirmada". A `CheckConstraint` existente
(`ck_answers_source_text`) já impede e continuaria impedindo `source=TEXT`
sem `text` — para `source=IMAGE` confirmado, o endpoint de aplicação garante
o mesmo invariante antes de persistir (constraint de banco não cobre IMAGE
hoje por desenho, igual à PR #16; reforço na camada de aplicação, não no
banco, para não reabrir a migração homologada).

## 6. Confirmação repetida e edições concorrentes (decidido — DEC-AV-040 §2.3/§2.4)

- **Confirmação repetida com o mesmo texto**: idempotente, 200, sem novo
  `AuditEvent` de confirmação (idempotência verdadeira, não apenas retorno de
  sucesso genérico). `expected_version` na chamada repetida deve ser a
  versão JÁ confirmada (o cliente que releu o estado via `GET` antes de
  reenviar) — se o cliente ainda tiver uma versão antiga em cache, recebe
  `TRANSCRIPTION_VERSION_CONFLICT` em vez de reprocessar às cegas.
- **Confirmação repetida com texto diferente**: 409 `TRANSCRIPTION_ALREADY_CONFIRMED`
  com o texto já confirmado no corpo (mesmo padrão de
  `REVIEW_ALREADY_EXISTS` em `review_correction` — devolve o estado existente
  para o cliente decidir, não falha silenciosamente nem sobrescreve). Isto é
  definitivo (DP-2 fechou a questão: sem reabertura nesta fatia).
- **Edições concorrentes de rascunho (lock otimista por versão, decidido)**:
  duas chamadas de `PATCH .../draft` quase simultâneas para a mesma resposta
  — cada uma enviando o `expected_version` que acreditava ser a atual no
  momento em que carregou a tela. A transação de banco (commit atômico,
  `UPDATE ... WHERE id = :id AND transcription_version = :expected_version`)
  garante que só a primeira a chegar realmente commita e incrementa a
  versão; a segunda, ao tentar com a versão agora desatualizada, recebe
  `TRANSCRIPTION_VERSION_CONFLICT` (409) com o rascunho/versão atuais no
  corpo, para o frontend oferecer "recarregar e tentar de novo" ou mesclar
  manualmente — nunca uma sobrescrita silenciosa.
- **Confirmações concorrentes (o cenário mais crítico, explicitamente pedido
  por Rafael)**: duas chamadas de `POST .../confirm` quase simultâneas com
  textos potencialmente diferentes. O mesmo lock otimista por
  `transcription_version` garante que apenas uma commita primeiro (a que
  bater a versão esperada contra a real na transação); a segunda recebe
  `TRANSCRIPTION_VERSION_CONFLICT` (se ainda não sabia que a primeira já
  confirmou) ou `TRANSCRIPTION_ALREADY_CONFIRMED` (se a verificação de
  `transcription_status` acontecer antes da checagem de versão — ordem exata
  de verificação a definir na implementação, mas o resultado observável é
  idêntico: nunca dois `AuditEvent` de confirmação para a mesma resposta,
  nunca dois textos finais divergentes persistidos). Nenhuma condição de
  corrida pode resultar em `text` indefinido entre dois valores possíveis —
  a transação do banco (não um lock em memória da aplicação, que não
  protegeria contra múltiplos processos/réplicas) é a garantia real.
- **Confirmação concorrente com salvamento de rascunho concorrente**: o
  endpoint de confirmação é a fonte de verdade — uma vez confirmado, `draft`
  subsequente é rejeitado com `TRANSCRIPTION_ALREADY_CONFIRMED` (ver acima),
  independentemente de qual `expected_version` o rascunho tardio enviar.

## 7. Sem invenção de "texto bruto de OCR"

Nenhum campo desta fatia se chama ou se comporta como resultado de OCR. O
texto que existe é:
- `manual_transcription_draft`: o que o professor digitou e ainda não
  confirmou (rascunho, mutável).
- `text` (campo já existente em `Answer`): o texto confirmado, final, único
  campo que `request_correction` lê.
Não há "texto extraído automaticamente" em nenhum momento desta fatia — isso
só existiria com OCR (`BL-AV-4B-07`/`08`, fora de escopo). O `AuditEvent` de
cada rascunho salvo preserva a versão anterior (histórico real de edição
humana), não uma simulação de pipeline de extração.

## 8. Comportamento após já existir correção ou revisão (decidido — sem reabertura nesta fatia)

Cenário possível apesar de DP-2 (sem reabertura): como a confirmação é
definitiva, uma vez que `request_correction` é chamado e cria
`CorrectionJob`/`AIExecution`/eventualmente `HumanReview`, **não há caminho
nesta fatia para o professor alterar o texto já confirmado** — a transcrição
confirmada que gerou aquela correção é, por definição, a única versão que
existirá para essa resposta nesta fatia. Isso simplifica bastante o
cenário em relação à v1 deste plano (que avaliava dois ramos dependentes de
DP-2): só existe o ramo "definitivo".

- `CorrectionJob`/`AIExecution`/`HumanReview`, se criados após a confirmação,
  **nunca são afetados** por esta fatia — nenhuma rotina de `draft` ou
  `confirm` os toca, consulta ou invalida (a própria tentativa de `draft`/
  `confirm` pós-confirmação já é barrada por `TRANSCRIPTION_ALREADY_CONFIRMED`
  antes de chegar perto dessas tabelas).
- Retificação de uma transcrição já usada em correção/revisão fica
  explicitamente para a fatia futura de reabertura (fora de escopo aqui);
  quando essa fatia existir, ela deverá — por decisão já registrada em
  DEC-AV-040 §2.2 — adicionar um novo elo preservando o anterior (nunca
  sobrescrever o `AuditEvent` ou o `CorrectionJob` histórico), mesmo
  princípio de imutabilidade já usado para `HumanReview` (`BL-AV-1-10`).
- Rastreabilidade nesta fatia: um único `AuditEvent` de confirmação por
  resposta (dado que não há reabertura), cujo `created_at` é sempre anterior
  a qualquer `CorrectionJob` daquela resposta — a cadeia é estritamente
  linear: rascunho(s) → confirmação (um único evento definitivo) → correção
  → revisão, sem possibilidade de texto confirmado divergir do texto que
  gerou a correção.

## 9. Confirmar transcrição NÃO dispara correção automaticamente

Center explícito, reforçado por Rafael nesta autorização: `confirm` apenas
transiciona `transcription_status` para `TRANSCRICAO_CONFIRMADA`. Isso faz
com que o guard já existente em `request_correction` (que hoje bloqueia com
422 `ANSWER_NOT_TRANSCRIBED`) pare de bloquear — mas a chamada a
`request_correction` continua sendo uma ação HTTP distinta, deliberada,
disparada pelo professor na tela (mesmo botão "Solicitar análise da IA" já
existente no fluxo textual, reaproveitado para a resposta por imagem depois
de confirmada). Nenhum código novo chama `request_correction` a partir do
endpoint de confirmação. A revisão pedagógica final (`review_correction`,
`HumanReview`) permanece, como já é hoje, uma ação humana distinta e
posterior, não afetada por esta fatia.

## 10. Compatibilidade com respostas textuais existentes

- Respostas `source=TEXT` não têm `manual_transcription_draft` nem endpoints
  de rascunho/confirmação aplicáveis — os dois novos endpoints retornam 422
  `ANSWER_NOT_IMAGE_SOURCE` para `source=TEXT` (texto já nasce confirmado,
  `TRANSCRICAO_CONFIRMADA`, no fluxo existente — nada a transcrever).
- `request_correction` não muda de contrato — continua aceitando qualquer
  `Answer` com `transcription_status=TRANSCRICAO_CONFIRMADA` e texto não-vazio,
  seja a origem TEXT (já confirmado desde a criação) ou IMAGE (agora também
  confirmável via esta fatia). Nenhuma branch condicional por `source` dentro
  de `request_correction` além do guard já existente.
- A suíte existente de testes do fluxo textual (ACD-10 da fatia anterior, e
  toda a suíte histórica de `Answer`/`CorrectionJob`) não deve precisar de
  nenhuma alteração — mudança é aditiva (`manual_transcription_draft` nullable,
  dois endpoints novos), não há campo obrigatório novo em `Answer` que quebre
  a criação de resposta textual existente.

## 11. Critérios de aceite propostos (ACD-01..XX desta fatia, formato igual ao de DEBT-AV-014)

> Revisados após achados ACH-01/05/07 do parecer do Antigravity (ACD-01B,
> ACD-02 complementado, ACD-04 especificado, ACD-14, typo corrigido) e após
> as decisões DP-1/2/3 + concorrência de DEC-AV-040 (ACD-07 fechado em vez
> de condicional, ACD-11 reescrito, ACD-15/16/17 novos para concorrência).

| ID | Critério | Método |
|---|---|---|
| ACD-01 | Salvar rascunho de transcrição manual para resposta IMAGE pendente; rascunho não altera `text` nem `transcription_status`; `transcription_version` incrementa a cada save | integração real |
| ACD-01B | `GET /v1/assessments/{id}/image-answers` retorna `manual_transcription_draft` e `transcription_version` quando existentes, permitindo recuperação fiel do rascunho em nova sessão ou após reload (F5) — fecha a lacuna crítica identificada na revisão (ACH-01) | integração real + navegador real |
| ACD-02 | Rascunho (`draft`) e confirmação (`confirm`) rejeitados para resposta TEXT, ambos com 422 ANSWER_NOT_IMAGE_SOURCE | integração real |
| ACD-03 | Confirmar transcrição com texto válido transiciona para TRANSCRICAO_CONFIRMADA, preenche `text`, autoria (`transcription_confirmed_by_id`) e data (`transcription_confirmed_at`) | integração real |
| ACD-04 | Confirmar com texto vazio/só espaços -> 422 ANSWER_TEXT_REQUIRED, nenhuma alteração persistida. Rascunho vazio é PERMITIDO (serve para limpar um rascunho anterior sem confirmar nada) — não aciona ANSWER_TEXT_REQUIRED, que se aplica só a `confirm` | integração real |
| ACD-05 | Autorização: mutação exige propriedade + vínculo ativo de turma (require_assessment_mutation, igual a request_correction); não-dono 403; sem vínculo ativo 403; sem token 401; admin ok | integração real |
| ACD-06 | Confirmação repetida com mesmo texto e `expected_version` correta é idempotente (200, sem novo AuditEvent); com texto diferente -> 409 TRANSCRIPTION_ALREADY_CONFIRMED com estado já confirmado | integração real |
| ACD-07 | Rascunho após confirmação é SEMPRE bloqueado (409 TRANSCRIPTION_ALREADY_CONFIRMED) — definitivo nesta fatia, DP-2 fechou a decisão (sem reabertura) | integração real |
| ACD-08 | Confirmar transcrição NÃO cria CorrectionJob nem dispara request_correction automaticamente; a resposta confirmada só é corrigida por chamada explícita subsequente a /corrections | integração real + inspeção de código (nenhuma chamada interna a request_correction a partir dos novos endpoints) |
| ACD-09 | Após confirmação, request_correction deixa de bloquear por ANSWER_NOT_TRANSCRIBED (passa pelo guard) para a resposta IMAGE | integração real (regressão do guard já existente) |
| ACD-10 | Histórico de rascunhos e confirmação preservado via AuditEvent (before/after), consultável, não apaga versões anteriores | integração real |
| ACD-11 | CorrectionJob/HumanReview pré-existentes NUNCA são apagados, alterados ou re-disparados por qualquer chamada a draft/confirm (não há cenário de reabertura nesta fatia — DP-2 fechou a decisão) | integração real |
| ACD-12 | Fluxo textual existente (ACD-10 da fatia anterior) sem regressão — suíte completa | suíte automatizada |
| ACD-13 | Frontend: tela de conferência mostra imagem + campo de texto editável, distingue claramente "salvar rascunho" de "confirmar"; antes de confirmar, exibe imagem+texto para revisão e aviso de que a confirmação é definitiva (requisito de UX de DEC-AV-040 §2.2); mensagens de erro para os casos acima | validação visual (navegador real) |
| ACD-14 | `draft` e `confirm` para `answer_id` inexistente retornam 404 | integração real |
| ACD-15 | Edição concorrente de rascunho: duas chamadas de `draft` com o mesmo `expected_version` desatualizado (simulando duas abas) — apenas uma commita; a outra recebe 409 TRANSCRIPTION_VERSION_CONFLICT com o estado atual no corpo, sem sobrescrita silenciosa | integração real (requisições concorrentes reais, não apenas sequenciais) |
| ACD-16 | Confirmações concorrentes com textos diferentes e mesmo `expected_version`: exatamente uma confirma (1 AuditEvent de confirmação, 1 `text` final persistido); a outra recebe conflito (409, VERSION_CONFLICT ou ALREADY_CONFIRMED); nunca os dois textos coexistem nem há dois eventos de confirmação | integração real (concorrência real via threads/conexões simultâneas contra PostgreSQL) |
| ACD-17 | `transcription_version` nunca retrocede e nunca pula por efeito de uma chamada rejeitada (apenas mutações bem-sucedidas incrementam) | integração real |

## 12. Papéis de execução (confirmados, sem alteração)

Claude Code permanece executor principal da implementação. Antigravity faz
revisão independente — nesta fase de planejamento (pós-decisão), revisão
**limitada às mudanças de contrato, histórico e concorrência** introduzidas
por DEC-AV-040 (não repete a revisão completa do plano, já concluída —
`APROVADO COM RESSALVAS`, parecer em
`evidence/AV-S08B/revisao_plano_transcricao_manual_antigravity.md`). Na fase
de implementação, Antigravity faz revisão independente completa do código
(mesmo padrão das fatias anteriores). Codex só diante de risco concreto
identificado, não revisão geral.

## 13. Limites desta fatia (reforço explícito)

Fora de escopo, não implementado nesta fatia nem nesta rodada:
- Qualquer OCR, extração automática, preparação de imagem (`BL-AV-4B-06/07/08/09`).
- Sinalização de incerteza de leitura (`BL-AV-4B-12`, inaplicável sem OCR).
- Idempotência de reenvio de imagem (`BL-AV-4B-16`, já é escopo de upload, não desta fatia).
- Reabertura/retificação pós-confirmação (DP-2 fechou: fatia futura separada).
- Múltiplos rascunhos concorrentes selecionáveis (DP-1 fechou: um rascunho atual).
- Qualquer migração operacional em `avalia_dev`/apresentação.
- P5, seed operacional, deploy, promoção de baseline.

Progresso homologado preservado em **19/70**; `AV-S05B` permanece parcial;
`BL-AV-4B-05` permanece pendente até avaliação específica dos critérios
canônicos (não reavaliado por este documento). `BL-AV-4B-10`/`11` seguem
**parciais** — esta fatia entrega a parte manual, não a parte de OCR.
