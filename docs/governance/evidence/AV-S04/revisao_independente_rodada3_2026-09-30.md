# Revisão independente — Rodada 3 — Planejamento AV-S04 — 2026-09-30

## Contexto

Revisão solicitada por Rafael, limitada exclusivamente às mudanças da
rodada 3 (compatibilidade `question`/`questions`, precisão técnica da
migração de `position`, escopo dos limites funcionais de 50 questões/
10.000 caracteres). Executada por um subagente que não redigiu o plano
(`delegate_task`, dispatch `deleg_6a39b7c2`, `sa-0-6546ac08`), com acesso
de leitura ao código real (`core/app/schemas.py`, `models.py`,
`seed.py`, testes de fixture) e instrução explícita de não reabrir
decisões das rodadas 1-2 (clonagem, helper de autorização, concorrência,
ordenação de rubrica).

## Reivindicações verificadas como corretas pelo revisor

- `schemas.py` confirma que `QuestionInput` e `RubricCriterionInput` não
  têm `max_length` hoje, confirmando as anotações "novo" da tabela da
  seção 3.7.
- `models.py` confirma que `Question` não tem `position`, não tem
  `created_at`, e não tem `UniqueConstraint` em
  `(assessment_id, position)` — confirma a premissa de que nada no
  schema do banco impede múltiplas `Question`s por `Assessment` hoje.
- `core/app/seed.py` (linhas 40-52) instancia `Question()` diretamente
  via ORM, sem passar por `AssessmentCreate`/o payload singular —
  confirma a alegação de que o caminho de dados do seed não passa pelo
  contrato singular.
- `test_academic_authorization.py:384`, `test_review_idempotency.py:35`
  e `test_authorization_boundaries.py:40` constroem `Question(...)`
  diretamente via ORM em fixtures, não via o schema `AssessmentCreate.
  question` — confirma a alegação de caminhos adicionais de escrita
  direta via ORM.
- `Question.max_score` e `RubricCriterion.max_score` são ambos
  `Numeric(6,2)` e validados por `Field(gt=0)` — confirma a linha
  "já limitado, preservado" da tabela.
- `ALTER TABLE ... ADD CONSTRAINT ... NOT VALID` no PostgreSQL é
  suportado apenas para `CHECK` e `FOREIGN KEY`, não para `UNIQUE` —
  distinção tecnicamente correta.
- `CREATE UNIQUE INDEX CONCURRENTLY` seguido de
  `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE USING INDEX` é o padrão
  real de baixo lock para adicionar unicidade sem lock exclusivo
  prolongado, e `CREATE INDEX CONCURRENTLY` de fato não pode rodar
  dentro de um bloco de transação — ambas as alegações são precisas.
- A sequência `CHECK (...) NOT VALID` + `VALIDATE CONSTRAINT` +
  `SET NOT NULL` é uma técnica real e documentada do PostgreSQL (12+)
  para evitar escaneamento completo ao adicionar `NOT NULL` — precisa
  como descrita.
- Não existe `Dockerfile` nem `docker-compose` em nenhuma parte do
  repositório, corroborando a afirmação de que não há artefato de
  deploy para confirmar ou negar implantação conjunta.

## Achados corrigidos (ver tabela de rastreabilidade no sprint document, seção 7b)

### 1. Ambiguidade reintroduzida na saída de `AssessmentOut.question` (severidade média)

O campo computado `question`, descrito inicialmente como sempre igual a
`questions[0]`, reintroduziria exatamente a ambiguidade que a migração de
contrato pretende eliminar: para uma avaliação com 2+ questões (o
propósito central de AV-S04), um consumidor legado lendo apenas
`question` veria uma questão arbitrária sem nenhum sinal de que outras
existem. **Corrigido**: `question = questions[0]` apenas quando
`len(questions) == 1`; `None` para `0` ou mais de `1` questão — um
consumidor legado recebe um sinal explícito de incompatibilidade (campo
ausente) em vez de um dado parcial silencioso.

### 2. Semântica de presença indefinida para casos de borda (severidade baixa)

A validação de "nenhum fornecido"/"ambos fornecidos" não definia o
tratamento de `questions: []` (lista vazia, mas tecnicamente não-`None`).
**Corrigido**: lista vazia é tratada como equivalente a "não fornecido"
em ambas as checagens; um payload com `question` preenchido e
`questions: []` é tratado como apenas `question` fornecido, não como
"ambos fornecidos".

### 3. Falta de tratamento de falha do índice `CONCURRENTLY` (severidade baixa)

Nenhuma menção ao caso em que a construção `CREATE UNIQUE INDEX
CONCURRENTLY` é interrompida, deixando um índice `INVALID`. **Corrigido**:
seção 3.4 agora nota que uma nova tentativa exige verificar e, se
necessário, `DROP INDEX` do índice inválido remanescente antes de
tentar novamente.

### 4. Tabela de limites sem declarar seu próprio escopo (severidade baixa)

A tabela de campo→limite não declarava que cobre apenas o caminho de
criação de `Question`/`Rubric`, deixando ambíguo se `AnswerInput.text` e
`HumanReviewInput.justification` foram considerados e excluídos ou
simplesmente esquecidos. **Corrigido**: nota de escopo explícita
adicionada à seção 3.7.

### 5. AC-03 atribuído incorretamente à rodada 3 (severidade média)

AC-03 foi listado como revisado na rodada 3, mas seu conteúdo real
(autorização de CRUD de questões via `require_assessment_mutation`)
pertence inteiramente à decisão da seção 3.3, já assentada na rodada 2.
**Corrigido**: AC-03 agora anota explicitamente que é herdado da rodada
2 e não contém nenhuma mudança desta rodada.

### 6. Lacuna de cobertura: teste de `max_score` exigido na prosa mas ausente no AC (severidade média)

A seção 3.7 já exigia um teste confirmando que `max_score` continua
validado por `Field(gt=0)`/`Numeric(6,2)` sem interferência do novo
limite de caracteres, mas nenhum AC cobria isso. **Corrigido**: AC-12
ampliado para incluir esse teste.

### 7. AC-13 sem definição operacional testável (severidade baixa)

"Registros legados continuam legíveis" não é um critério determinístico
para um teste. **Corrigido**: AC-13 agora especifica a verificação HTTP
concreta (`GET /v1/assessments/{id}` retorna `200`, `position=1`, mesmo
conteúdo de antes da migração).

### 8. AC-17 misturava comportamento testável com política não testável (severidade baixa)

AC-17 incluía tanto "o log distingue uso legado de uso canônico"
(testável) quanto "sem prazo de descontinuação automática" (política,
não verificável por teste). **Corrigido**: AC-17 isolado para cobrir
apenas o comportamento de log; a nota de política permanece em prosa na
seção 3.2, não dentro do critério de aceite.

## Veredito do revisor

"As mudanças da rodada 3 são substancialmente sólidas e representam uma
melhoria real de precisão técnica sobre o material que substituem. O
design duplo `question`/`questions` é coerente na camada de entrada
(validação mutuamente exclusiva, normalização limpa), mas tinha uma
ambiguidade não endereçada na camada de saída para avaliações com
múltiplas questões — agora corrigida. As alegações sobre o mecanismo de
migração do PostgreSQL (escopo de `NOT VALID`, padrão `CONCURRENTLY`) são
tecnicamente precisas como descritas. A tabela de limites de caracteres é
internamente consistente com o schema atual e completa para os campos
que afirma cobrir, com uma lacuna de delimitação de escopo — agora
fechada. Os critérios de aceite majoritariamente testam o que afirmam
testar, com os ajustes de atribuição e cobertura aplicados acima. Estas
são questões de documentação/rastreabilidade, não bloqueios
arquiteturais, e já foram resolvidas antes do fechamento desta rodada.
Nenhuma implementação é recomendada ou implícita por esta revisão."

## Transcrição completa

Resposta JSON completa do subagente preservada em:
`/Users/rafaeloliveira/.hermes/cache/delegation/subagent-summary-0-20260930_215226_090558.txt`
(arquivo fora deste repositório, apenas como evidência de processo —
não copiado para dentro do repositório para não versionar um artefato de
cache externo).
