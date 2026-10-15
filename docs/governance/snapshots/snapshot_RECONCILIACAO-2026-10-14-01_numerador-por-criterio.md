---
id: "RECONCILIACAO-2026-10-14-01"
tipo: reconciliacao
tema: "Reconciliação por critério canônico (não por sprint): BL-AV-4B-03/04/10/11/13/14/15 — cobertura combinada AV-S06B + AV-S08B"
gerado_em: "2026-10-14T16:10:00-03:00"
executor: "Hermes"
status: "reconciliação documental; não altera homologação nem integração já concluídas do PR #18"
base: "main efaa337c04070f59e01d217010f17a92b89258ca (PR #18 integrado)"
---

# Reconciliação RECONCILIACAO-2026-10-14-01 — numerador por critério canônico, não por sprint

> Autorizado por Rafael nesta rodada: avaliar a cobertura combinada das
> entregas já homologadas da AV-S06B (`DEC-AV-036`/`038`/`039`) e da fatia
> MANUAL da AV-S08B (`DEC-AV-041`), item por item do backlog canônico,
> sem usar o número da sprint originalmente mapeada como motivo isolado
> para manter um item pendente. Não reabre homologação nem integração já
> concluídas (PR #15/#16/#17/#18, todos integrados em `main`).

## Método

Para cada item: leitura do critério canônico completo em
`backlog/backlog_tecnico_avalia.md`, confronto com evidência de código real
(arquivo/linha) e com os registros de homologação (`decisions.md`). Nenhum
critério foi reescrito; nenhuma evidência nova foi produzida nesta rodada
(reconciliação documental, sem execução).

## 1. BL-AV-4B-03 — Recebimento e armazenamento de imagens

**Critério canônico completo** (`backlog_tecnico_avalia.md:358`): formatos,
tamanho, resolução e quantidade de páginas suportados; validação do
conteúdo real do arquivo (não apenas a extensão declarada).

| Elemento | Evidência |
|---|---|
| Formatos | JPEG/PNG apenas; detecção pelo conteúdo real via Pillow (`core/app/routers/images.py:121-138`, `Image.open(..., formats=_OPEN_FORMATS)` + `img.verify()`), não pela extensão declarada |
| Tamanho | limite configurável (`answer_image_max_bytes`), checado por `Content-Length` declarado E pelos bytes efetivamente lidos (dupla defesa, `core/app/routers/images.py:202-214`) |
| Proteção contra decompression bomb | `Image.DecompressionBombWarning`/`Error` tratados explicitamente (`images.py:122-134`) |
| Quantidade de páginas | 1 imagem = 1 resposta de 1 questão (`DEC-AV-018`, "uma resposta de uma questão por foto"); múltiplas páginas **não fazem parte do escopo decidido** — `DEC-AV-019` (suporte a múltiplas páginas) permanece formalmente pendente, mas isso não é uma lacuna de BL-AV-4B-03, é escopo explicitamente não assumido por decisão já tomada (`DEC-AV-018`) |
| Validação do conteúdo real | tipo declarado comparado ao detectado; discrepância rejeitada com 422 (`images.py:170-177`, "Tipo declarado do arquivo diverge do conteúdo real") |

**Homologação**: `DEC-AV-036` (2026-10-14) — backend/API homologado.
**Integração**: PR #15, merge `b818961`, em `main`.

**Motivo de bloqueio original** (`DEC-AV-036`): "`BL-AV-4B-03` e `BL-AV-4B-04`
têm o backend homologado, mas permanecem **não encerrados** enquanto não
houver a interface que torna o fluxo utilizável de ponta a ponta."

**Reavaliação desta rodada**: a dependência citada (interface completa,
ponta a ponta) está satisfeita desde a integração do PR #18 — fluxo real
hoje em `main`: upload da foto (`POST /v1/answers/image`) → listagem/retomada
(`GET /v1/assessments/{id}/image-answers`, DEBT-AV-014 resolvido) → tela de
conferência com rascunho/confirmação manual (`ImageAnswerPage.tsx`) →
solicitação explícita de correção (`POST /v1/answers/{id}/corrections`,
bloqueada até confirmação) → revisão humana (`HumanReview`, já existente).
Todos os elos estão em `main`, homologados individualmente
(`DEC-AV-036`/`038`/`039`/`041`) e integrados.

**Pendência remanescente**: nenhuma quanto ao critério canônico em si.
`DEC-AV-019` (múltiplas páginas) continua formalmente pendente, mas é
decisão de escopo futuro, não requisito não atendido desta entrega.

**Elegibilidade ao numerador**: **ELEGÍVEL** — critério canônico
integralmente atendido pela combinação AV-S06B (backend) + AV-S08B
(interface ponta a ponta), sem decisão de produto nova necessária.

## 2. BL-AV-4B-04 — Controle de acesso, preservação do original, metadados

**Critério canônico completo** (`backlog_tecnico_avalia.md:359`): controle
de acesso por professor/avaliação; preservação do arquivo original;
registro de vínculo, autoria e data.

| Elemento | Evidência |
|---|---|
| Controle de acesso | `_get_authorized_answer` → `_get_owned_assessment` + `require_assessment_mutation` (mesmo padrão de autorização por propriedade da Etapa 1), `core/app/routers/images.py:82-95` |
| Preservação do arquivo original | `original_filename` armazenado só como metadado (nunca usado em path); conteúdo gravado sob `storage_filename` gerado pelo servidor (`core/app/models.py:312-313`); hash `sha256_hash` registrado para integridade (`models.py:316`) |
| Vínculo | `AnswerImage.answer_id` (FK obrigatória) |
| Autoria | `AnswerImage.uploaded_by_id` (FK para `users.id`, obrigatória) |
| Data | `AnswerImage.created_at` |

**Homologação**: `DEC-AV-036` (2026-10-14).
**Integração**: PR #15, merge `b818961`, `main`.

**Motivo de bloqueio original**: idêntico ao de BL-AV-4B-03 (interface
ponta a ponta ausente).

**Reavaliação**: mesma conclusão do item 1 — a interface ponta a ponta
existe e está integrada desde o PR #18. Nenhum requisito do critério
canônico de BL-AV-4B-04 depende de OCR, transcrição ou qualquer item ainda
não entregue.

**Pendência remanescente**: nenhuma quanto ao critério canônico.

**Elegibilidade ao numerador**: **ELEGÍVEL** — critério canônico
integralmente atendido.

## 3. BL-AV-4B-14 — Vínculo + bloqueio de correção antes da confirmação

**Critério canônico completo** (`backlog_tecnico_avalia.md:378`): vincular
a resposta confirmada ao aluno, à avaliação e à questão correta; impedir
que a correção assistida inicie antes da confirmação humana da
transcrição.

| Elemento | Evidência |
|---|---|
| Vínculo ao aluno | `student_name_fake` (identificação manual, mesmo mecanismo já usado em todo o produto para resposta textual — `DEC-AV-021`: seleção manual de avaliação/questão/aluno, sem identificação automática na primeira versão; não é uma lacuna desta entrega, é a decisão de produto já vigente para toda a trilha) |
| Vínculo à avaliação/questão | `question_id` (FK obrigatória, `core/app/main.py:630`), autorização por propriedade da avaliação (`_get_owned_assessment`) |
| Bloqueio de correção antes da confirmação | guard explícito em `request_correction` (`core/app/main.py:989-998`): `transcription_status != TRANSCRICAO_CONFIRMADA` ou texto vazio → 422 `ANSWER_NOT_TRANSCRIBED`, **antes** de criar qualquer `CorrectionJob`. Testado (suíte AV-S08B, ACD correspondente) |

**Homologação**: vínculo (`question_id`/propriedade) já homologado desde
`DEC-AV-036`/`038` (AV-S06B); bloqueio de correção homologado em
`DEC-AV-041` (AV-S08B, fatia MANUAL).

**Integração**: PR #15/#16 (vínculo) + PR #18 (bloqueio), todos em `main`.

**Nota de mapeamento**: o backlog canônico lista este item na coluna de
sprint-alvo como `AV-S09B` (ver `backlog_tecnico_avalia.md:108`). Por
instrução explícita desta rodada, isso não é usado como motivo isolado
para manter o item pendente — o critério funcional foi integralmente
satisfeito pela combinação AV-S06B (vínculo) + AV-S08B (bloqueio), de
forma antecipada em relação ao sequenciamento original do backlog. O
mapeamento de sprint no backlog é indicativo de planejamento, não um
requisito de aceite em si.

**Pendência remanescente**: nenhuma quanto ao texto literal do critério
canônico (vínculo + bloqueio). Identificação automática de aluno/questão
permanece fora de escopo por decisão já tomada (`DEC-AV-021`), não é uma
lacuna desta avaliação.

**Elegibilidade ao numerador**: **ELEGÍVEL** — critério canônico
integralmente atendido pela combinação AV-S06B + AV-S08B, antecipando o
sequenciamento de sprint originalmente proposto, sem alterar o critério em
si nem contar o item duas vezes (este é a primeira vez que BL-AV-4B-14
entra no numerador).

## 4. BL-AV-4B-10 — Tela de conferência lado a lado

**Critério canônico completo**: tela de conferência exibindo imagem e
**texto extraído** lado a lado.

| Elemento | Evidência |
|---|---|
| Imagem + texto lado a lado | entregue — `ImageAnswerPage.tsx`, rascunho manual exibido junto à imagem |
| Texto **extraído** (por OCR/visão) | **ausente** — não existe nenhum componente de extração automática nesta trilha ainda (`BL-AV-4B-07`/`08`, ambos `proposto`) |

**Pendência remanescente**: o texto hoje exibido é 100% digitado pelo
professor, não extraído por nenhum mecanismo automático. O critério fala
textualmente em "texto extraído" — requisito ausente.

**Elegibilidade ao numerador**: **NÃO elegível** — permanece **PARCIAL**.

## 5. BL-AV-4B-11 — Edição/confirmação; preservar bruto extraído, corrigido, histórico

**Critério canônico completo**: edição e confirmação da transcrição pelo
professor; preservação de texto bruto **extraído**, texto corrigido e
histórico da confirmação.

| Elemento | Evidência |
|---|---|
| Edição + confirmação pelo professor | entregue (`PATCH .../manual-transcription/draft`, `POST .../manual-transcription/confirm`) |
| Histórico da confirmação | entregue via `AuditEvent` (autoria + timestamp) |
| Texto bruto **extraído** distinto do corrigido | **ausente** — sem OCR, não existe um "bruto extraído" diferente do texto digitado; há apenas um rascunho e um texto confirmado, ambos de origem manual |

**Pendência remanescente**: a distinção canônica entre bruto extraído e
texto corrigido pelo professor não existe nesta fatia, porque não há
extração automática que produza um bruto a ser corrigido.

**Elegibilidade ao numerador**: **NÃO elegível** — permanece **PARCIAL**.

## 6. BL-AV-4B-13 — Transcrição manual quando a extração falhar

**Critério canônico completo** (`backlog_tecnico_avalia.md:374`):
transcrição manual quando a extração falhar. Mesmo princípio de RN-017 (IA
indisponível → correção manual) aplicado à falha do componente de OCR.

**Correção desta rodada** (documento já mergeado em `main` via `DEC-AV-041`
e snapshots EXEC-2026-10-14-09/10/11 afirmava "cobertos integralmente" —
impreciso):

| Elemento | Evidência |
|---|---|
| Transcrição manual disponível | entregue e homologada — o professor sempre pode digitar/confirmar manualmente |
| Transcrição manual **como fallback após falha de extração** | **não comprovado** — não existe ainda nenhuma tentativa de extração automática (`BL-AV-4B-07`/`08` propostos, não implementados); hoje a transcrição é manual **por padrão**, não por um fallback acionado após uma falha real de OCR |

**Pendência remanescente**: o comportamento específico de fallback
(extração tentada → falha detectada e diferenciada de ausência de texto →
transição explícita para modo manual) depende de `BL-AV-4B-07`/`08`
existirem primeiro. Hoje não há nada do qual "falhar".

**Elegibilidade ao numerador**: **NÃO elegível** — a transcrição manual em
si está entregue, homologada e integrada, mas o critério específico
("quando a extração falhar") não foi comprovado, porque a extração em si
não existe ainda. Permanece **PARCIAL**.

## 7. BL-AV-4B-15 — Cadeia imagem → OCR → transcrição confirmada → correção → revisão

| Elo | Estado |
|---|---|
| imagem | entregue (AV-S06B) |
| execução OCR | **ausente** |
| transcrição confirmada | entregue (AV-S08B, manual) |
| correção | entregue (bloqueio + solicitação explícita) |
| revisão humana | já existia (`HumanReview`) |

**Pendência remanescente**: falta o elo de execução OCR.

**Elegibilidade ao numerador**: **NÃO elegível** — permanece **PARCIAL**
(requisito existente parcial, como já classificado no backlog).

## 8. Itens não reavaliados nesta rodada (fora do escopo autorizado)

- `BL-AV-4B-05` (retenção/exclusão operacional) — permanece **pendente**,
  conforme já registrado; decisão (`DEC-AV-013` aplicada a imagens) não
  tomada.
- `AV-S05B` (benchmark OCR) — permanece **parcial** (manuscrito pendente).
- `BL-AV-4B-01/02/06/07/08/09/12/16/17/18/19/20/21` — não entram nesta
  reconciliação; nenhum deles foi entregue pelas sprints AV-S06B/AV-S08B.

## 9. Resultado consolidado

| ID | Elegibilidade | Motivo |
|---|---|---|
| `BL-AV-4B-03` | **ELEGÍVEL** — entra no numerador | interface ponta a ponta agora existe (PR #18); nenhum requisito do critério canônico pendente |
| `BL-AV-4B-04` | **ELEGÍVEL** — entra no numerador | idem |
| `BL-AV-4B-14` | **ELEGÍVEL** — entra no numerador | vínculo + bloqueio de correção, ambos comprovados; mapeamento de sprint não é critério de aceite |
| `BL-AV-4B-10` | NÃO elegível | falta extração automática (texto não é "extraído") |
| `BL-AV-4B-11` | NÃO elegível | falta distinção bruto extraído vs. corrigido (sem OCR) |
| `BL-AV-4B-13` | NÃO elegível | falta o próprio OCR cuja falha dispararia o fallback |
| `BL-AV-4B-15` | NÃO elegível | falta o elo de execução OCR |

**Numerador resultante**: 19 + 3 = **22/70**.

Itens acrescentados ao numerador nesta reconciliação (nominal, cada um
contado exatamente uma vez, nenhum já presente na lista anterior de
19 itens do dashboard): `BL-AV-4B-03`, `BL-AV-4B-04`, `BL-AV-4B-14`.

## 10. Não alterado por esta reconciliação

Nenhuma homologação ou integração já concluída foi reaberta. Nenhum
critério canônico foi reescrito. `BL-AV-4B-05` e `AV-S05B` permanecem
exatamente como estavam. Nenhum stage/commit/push/merge foi executado
fora da branch documental `docs/reconciliacao-numerador-av-s06b-av-s08b`
(ver política de branch desta rodada).
