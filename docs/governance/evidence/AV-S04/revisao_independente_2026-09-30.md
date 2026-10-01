# Revisão independente — Planejamento AV-S04 — 2026-09-30

## Contexto

Revisão solicitada por Rafael, executada por um subagente que não
redigiu o planejamento (`delegate_task`, dispatch `deleg_cf841444`,
`sa-0-bfdc4db6`), com escopo restrito a: compatibilidade retroativa,
preservação de integridade histórica de correções/revisões, consistência
de autorização e segurança de migração. O subagente teve acesso de
leitura ao repositório real (`core/app/models.py`, `schemas.py`,
`main.py`, `routers/academic.py`, arquivos de frontend) e ao sprint
document então vigente, com instrução explícita de verificar as
afirmações do plano contra o código real em vez de aceitá-las como
corretas.

## Reivindicações do plano verificadas como corretas pelo revisor

- `schemas.py:81` `AssessmentCreate.question: Optional[QuestionInput]` é
  de fato singular.
- `schemas.py:95` `AssessmentOut.questions: list[QuestionOut]` já é
  plural.
- `schemas.py:207` `CorrectionJobContextOut.question` é singular por
  design (uma correção resolve exatamente uma questão) — corretamente
  identificado pelo plano como caso distinto, fora de escopo da migração
  de contrato.
- `main.py:158` cria exatamente uma `Question` a partir de
  `payload.question`; `_get_owned_assessment` (`main.py:182`) é
  reutilizado sem alteração por `get_assessment` e, via
  `require_assessment_mutation`, por `update_assessment`,
  `publish_assessment`, `create_answer` e `request_correction`.
- `Question` não tem `position` nem `created_at` hoje;
  `Assessment.questions` é uma relação 1:N simples sem `order_by`
  explícito — ordem persistida é indefinida até `position` existir.
- `frontend/src/types.ts:66-67` já declara `question?`/`questions?`
  coexistindo, como o plano afirma.
- `api.ts:111-116`: `createAssessment` exige `question` no tipo do
  payload; `updateAssessment` usa `PUT` enquanto `main.py` só expõe
  `PATCH` — ambos os fatos de consumidor citados pelo plano são precisos.
- `AssessmentEditorPage.tsx`, `AnswerPage.tsx`, `ReviewPage.tsx` contêm
  exatamente os padrões de fallback singular/plural citados pelo plano.
- `docs/contracts/openapi.yaml:389-394,502-504` contêm os campos
  singulares `question` referenciados pelo plano, em ambos os schemas.
- Não existe nenhum `Dockerfile`, `docker-compose` ou workflow de deploy
  no repositório; `ci.yml` só executa teste/lint/build por componente,
  sem job de deploy.

## Achados corrigidos (ver tabela de rastreabilidade no sprint document, seção 7)

### 1. Autorização — cadeia imprecisa (severidade média)

A seção 3.3 original dizia que os quatro novos endpoints reaproveitariam
"a mesma cadeia já usada em `POST /v1/assessments`". `POST /v1/assessments`
é uma rota de criação sem avaliação preexistente, e só chama
`require_active_class_link` diretamente. A cadeia real usada por toda
rota que muta uma avaliação já existente é `require_assessment_mutation`
(`routers/academic.py:165-171`), que encapsula bypass de admin, checagem
de `owner_id` e `require_active_class_link` condicional. **Corrigido**:
seção 3.3 agora nomeia `require_assessment_mutation` explicitamente.

### 2. Autorização — resolução de assessment nos endpoints raiz-questão (severidade média)

`PATCH`/`DELETE /v1/questions/{question_id}` não podem chamar
`_get_owned_assessment(assessment_id, ...)` diretamente, pois são
enraizados em `question_id`. O único precedente (`create_rubric`,
`main.py:260-275`) já resolve isso de forma redundante: checagem de
ownership manual inline, seguida de `require_assessment_mutation`
(que repete a mesma checagem). **Corrigido**: proposto helper único
`_get_assessment_for_question`, reutilizado também por `create_rubric`
para eliminar a duplicação existente; novo `AC-14`.

### 3. Migração — backfill descrito como mais arriscado do que é (severidade baixa)

A seção 3.4 original tratava o backfill de `position` como uma
ambiguidade real de ordenação multi-linha. Sob o contrato atual
(singular), toda `Assessment` existente tem no máximo uma `Question` —
o backfill real de hoje é `position=1` para todas, trivial. **Corrigido**:
seção 3.4 declara isso explicitamente; a lógica de desempate por
`created_at`/`id` passa a ser descrita como infraestrutura defensiva para
backfills futuros, não resolução de uma ambiguidade presente.

### 4. Migração — risco de lock/downtime não quantificado (severidade baixa)

Adicionar coluna não-nula + `UPDATE` de backfill + `UniqueConstraint` em
tabela referenciada por `Rubric`/`Answer` é padrão clássico de lock no
Postgres. **Corrigido**: seção 3.4 recomenda `NOT VALID` seguido de
`VALIDATE CONSTRAINT` em passo separado.

### 5. Migração — concorrência no reorder/delete sem especificação (severidade média)

Nenhuma versão anterior especificava lock de linha para reordenação,
exclusão, adição ou edição de questão — todas competem pela mesma
`UniqueConstraint`. Duas chamadas concorrentes podiam gerar posição
duplicada ou buraco silencioso dependendo do isolamento da transação.
**Corrigido**: seção 3.4 exige `SELECT ... FOR UPDATE` sobre a avaliação
no início de toda transação que mute posição; offset do reorder
especificado com magnitude exata; novo `AC-15`.

### 6. Integridade histórica — seleção de rubrica não determinística na clonagem (severidade média)

`publish_assessment` (`main.py:230-232`) usa `question.rubrics[-1]` como
fallback quando nenhuma rubrica está `is_published`; a relação não tem
`order_by`. Isso é preexistente, mas passa a ser mais relevante com
clonagem, pois o clone recebe uma rubrica nova e pode ser editado
múltiplas vezes antes de republicar. **Corrigido**: seção 3.1 agora exige
`order_by` explícito (`version.desc()` ou `created_at.desc()`) antes da
implementação, e um teste de regressão específico: clonar, editar e
republicar o clone com rubrica diferente, depois confirmar que o
`CorrectionJobContext` do **original** continua resolvendo a rubrica
original. `AC-07`/`AC-08` atualizados.

### 7. Compatibilidade — "nenhum consumidor externo" apresentado como mais conclusivo do que a evidência sustenta (severidade baixa)

A redação original da seção 3.2 lia como se a ausência de evidência de
consumidor externo e de deploy desacoplado provasse a ausência real
desses fatores. Uma busca em um único repositório nunca pode provar isso;
e não há nenhum artefato de deploy no repositório para corroborar a
premissa de "implantação conjunta". **Corrigido**: seção 3.2 agora declara
essa distinção explicitamente, e a confirmação operacional de Rafael
passa a ser tratada como item bloqueante do Definition of Ready, não
apenas um item de checklist entre outros.

## Consumidores de `question` singular adicionais encontrados pelo revisor

Nenhum. A busca independente do revisor (grep em todo o repositório por
`question`, mais buscas específicas por indícios de SDK/mobile/terceiros/
deploy) retornou exatamente os mesmos arquivos já listados pelo plano.

## Veredito do revisor

"A seção 3 do plano é tecnicamente precisa contra o código real (números
de linha corretos, distinção correta entre os dois casos de `question`,
identificação correta de que os dados anteriores a S04 têm no máximo uma
questão por avaliação, e um design razoável de publicação imutável +
clonagem que evita reescrever `Answer.question_id` histórico). O plano
deve continuar sendo apenas planejamento: nenhuma implementação, migração
ou ação Git deve prosseguir a partir deste documento." As cinco
recomendações do revisor foram incorporadas ao sprint document nesta
mesma rodada, conforme detalhado acima.

## Transcrição completa

Resposta JSON completa do subagente preservada em:
`/Users/rafaeloliveira/.hermes/cache/delegation/subagent-summary-0-20260930_213057_628399.txt`
(arquivo fora deste repositório, apenas como evidência de processo —
não copiado para dentro do repositório para não versionar um artefato de
cache externo).
