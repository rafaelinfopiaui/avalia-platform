# AV-S04 — Correção do bug de produção: race delete_question × create_answer

Data/fuso: 2026-10-01, America/Fortaleza (UTC-03:00).

## Origem do achado

A revisão independente final (subagente, delegação `deleg_ef260bff`,
2026-10-01 08:20–08:26) REPROVOU o estado então corrente da sprint por um
bug de produção real, confirmado empiricamente em PostgreSQL 16 real (não
SQLite): uma condição de corrida (TOCTOU) entre `delete_question` e
`create_answer`.

### Bug confirmado pela revisão

- `core/app/main.py` `delete_question` (então nas linhas 436-480): adquire
  `SELECT ... FOR UPDATE` no `Assessment` via `_get_assessment_for_question`,
  faz um `SELECT` simples de verificação de `Answer.question_id`, e então
  `db.delete(question)` + `db.flush()` + `db.commit()` — **sem**
  `try/except` em volta do delete/flush/commit.
- `create_answer` nunca adquire o lock do `Assessment` (`_get_owned_assessment`
  é um `SELECT` simples, sem `FOR UPDATE`) e nunca participa da serialização
  que `delete_question` tenta impor.
- Se uma `Answer` for commitada no intervalo entre o `SELECT` de checagem de
  `delete_question` e o `DELETE` físico, o `DELETE` viola a FK
  `answers_question_id_fkey` e propaga `IntegrityError` não tratada — em
  produção isso seria um `500` cru, não o `409` de domínio esperado.

## RED — reprodução determinística (sem depender de timing de threads)

Script criado:
`docs/governance/evidence/AV-S04/pacote-execucao-local/av_s04_delete_answer_race.py`.

Técnica: chama a função `delete_question` diretamente, mas intercepta
`db.delete(question)` para, na primeira chamada (exatamente o ponto onde o
código já passou pela checagem de `Answer` e está prestes a deletar), commitar
uma `Answer` concorrente através de uma sessão SQLAlchemy independente — abrindo
deterministicamente a mesma janela TOCTOU que threads reais abririam de forma
não determinística. Executado contra PostgreSQL 16 real (`av_s04_race_fix_test`,
banco descartável, migração `a9f4c2e71b06` aplicada do zero).

Antes da correção:
```
RESULT: unhandled IntegrityError: (psycopg2.errors.ForeignKeyViolation) update or
delete on table "questions" violates foreign key constraint
"answers_question_id_fkey" on table "answers"
...
POST-STATE: question_exists=True answer_count=1
OUTCOME=unhandled_IntegrityError
```

RED também reproduzido no teste automatizado `pytest` descrito abaixo, com
SQLite + `PRAGMA foreign_keys=ON` explicitamente habilitado para a conexão de
teste (SQLite não aplica FK por padrão):
```
E       sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
FAILED app/tests/test_assessment_multiple_questions.py::test_ac11_delete_create_answer_race_returns_409
```

## Correção aplicada

Arquivo: `core/app/main.py`, função `delete_question`. O `db.delete(question)`
+ `db.flush()` agora está envolvido em `try/except IntegrityError`, que faz
`db.rollback()` e levanta o mesmo `HTTPException(409, "Questão possui
respostas registradas; não pode ser excluída.")` já usado no caminho
sequencial (checagem prévia), em vez de deixar a exceção se propagar crua.
Este é o mesmo padrão já empregado em `review_correction` (linhas ~812-821)
para outro caso de corrida equivalente.

```python
deleted_position = question.position
try:
    db.delete(question)
    db.flush()
except IntegrityError:
    db.rollback()
    raise HTTPException(
        status_code=409,
        detail="Questão possui respostas registradas; não pode ser excluída.",
    ) from None
if remaining:
    ...
```

`IntegrityError` já estava importado em `core/app/main.py` (linha 11, usado
por `review_correction`), então não houve necessidade de novo import.

## GREEN — confirmação pós-correção

1. Script de reprodução determinística reexecutado 4x contra PostgreSQL real:
   ```
   RESULT: HTTPException status=409 detail='Questão possui respostas registradas; não pode ser excluída.'
   POST-STATE: question_exists=True answer_count=1
   OUTCOME=http_409
   ```
   (4/4 execuções, resultado idêntico e determinístico.)

2. Reprodução via threads HTTP reais (`TestClient`, duas threads, uma chamando
   `DELETE /v1/questions/{id}` e outra `POST /v1/answers` concorrentemente)
   reexecutada 5x contra o mesmo PostgreSQL real:
   ```
   DELETE status: 409
   CREATE ANSWER status: 201
   ```
   (5/5 execuções: a `Answer` concorrente sempre é criada com sucesso — `201` —
   e o `DELETE` sempre retorna `409` de domínio, nunca `500`.)

3. Teste de regressão automatizado adicionado à suíte permanente:
   `core/app/tests/test_assessment_multiple_questions.py::test_ac11_delete_create_answer_race_returns_409`.
   Usa a mesma técnica de interceptação determinística (sem depender de
   timing de threads) contra SQLite com `PRAGMA foreign_keys=ON` habilitado
   explicitamente para a conexão de teste via `sqlalchemy.event.listens_for`,
   reproduzindo a FK enforcement que o SQLite não aplica por padrão.
   - RED confirmado: revertendo temporariamente a correção, este teste falha
     com `sqlite3.IntegrityError: FOREIGN KEY constraint failed`.
   - GREEN confirmado: com a correção, o teste passa.

4. Suíte completa reexecutada após a correção:
   ```
   cd core && .venv/bin/python -m pytest app/tests/test_assessment_multiple_questions.py -v
   → 21 passed (20 anteriores + 1 nova regressão), 13 warnings

   cd core && .venv/bin/python -m pytest app/tests -q
   → 89 passed (68 preexistentes + 21 da sprint), 13 warnings

   cd core && .venv/bin/python -m ruff check --config ../ruff.toml app
   → All checks passed!
   ```

5. Banco descartável `av_s04_race_fix_test` removido ao final (`dropdb`).

## Estado após a correção

- `delete_question` agora protege contra exclusão com `Answer` tanto no
  caminho sequencial simples (checagem prévia, já existente) quanto no
  caminho concorrente (try/except na operação física, corrigido nesta
  fatia) — ambos retornam o mesmo `409` de domínio, nunca `500`.
- `create_answer` permanece sem lock explícito no `Assessment`; a proteção
  agora vem inteiramente do tratamento de `IntegrityError` em
  `delete_question`, que é suficiente porque a FK do banco é a fonte de
  verdade da invariante (qualquer ordem de interleaving entre os dois
  commits é coberta: se `create_answer` committa primeiro, o `SELECT` de
  checagem já o vê; se committa depois do `SELECT` mas antes do `DELETE`
  físico, o `except IntegrityError` o cobre; se committa depois do `DELETE`
  físico ter sucesso, a FK da própria tabela `answers` impediria a criação
  da `Answer` — a questão já não existe).
- Nenhum outro arquivo de produção, migração, frontend ou contrato foi
  alterado nesta correção.
- Autor desta correção: Hermes (mesma sessão que recebeu o achado da
  revisão independente). Por isso uma nova rodada de revisão independente
  (diferente do autor) é necessária antes de qualquer veredito final de
  aprovação — não reutilizar o parecer anterior como aprovação desta
  correção, conforme regra permanente desta sprint.

## Revisão independente da correção (rodada 3, 2026-10-01)

Agente diferente do autor da correção (delegação `deleg_1c904e53`).
Reproduziu a race **com script próprio, não reaproveitado** (técnica
diferente: 2 threads reais via HTTP `TestClient` sincronizadas por
`threading.Event`, patch na classe `Session.delete`, script apagado ao
final — não versionado). RED confirmado revertendo a correção (5/5
`IntegrityError` não tratada); GREEN confirmado com a correção (5/5 → 409,
`Answer` sobrevive); diff isolado em `main.py` confirmado como exatamente o
bloco try/except de 7 linhas. **Veredito: APROVADO.**

## Verificação de duas lacunas concretas adicionais (2026-10-01, pós-aprovação)

A pedido de Rafael, duas perguntas específicas sobre o tratamento foram
verificadas empiricamente (iam além do que as rodadas 2/3 haviam checado
explicitamente — aquelas confirmaram que o `except` *captura* o erro
esperado e retorna 409, mas não haviam verificado o estado da sessão após o
rollback nem a abrangência exata do `except`):

Script: `docs/governance/evidence/AV-S04/pacote-execucao-local/av_s04_gap_check_session_and_scope.py`,
executado contra PostgreSQL 16 real (`av_s04_gap_check`, banco descartável,
removido ao final).

**(A) A sessão/transação fica em estado válido após o rollback?**
Sim. Após o `except IntegrityError: db.rollback()` disparar dentro de
`delete_question`, a mesma instância de `Session` foi reutilizada no mesmo
processo para: um `SELECT` (`db.get(Question, ...)`), outro `SELECT`
(`db.query(Answer)...count()`), e — prova mais forte — um `INSERT` completo
seguido de `db.commit()` de uma entidade não relacionada (`Assessment`),
que persistiu com sucesso. Resultado real:
```
SESSION_USABLE_AFTER_ROLLBACK=True question_survives=True answer_count=1 write_after_rollback_committed=True
```
Isso prova que `db.rollback()` limpa completamente o estado da transação
SQLAlchemy (não deixa a sessão em `PendingRollbackError`), consistente com
o fato de o `Depends(get_db)` em `core/app/db.py` fazer apenas `db.close()`
no `finally` — não depende de nenhum estado adicional de limpeza.

**(B) O `except IntegrityError` captura indiscriminadamente outros erros
de integridade não relacionados?**
Não, por construção do código — verificado tanto por leitura (`inspect.getsource`)
quanto por topologia do schema:
- O bloco `try` contém exclusivamente `db.delete(question)` e `db.flush()`
  — nenhuma outra operação de banco está dentro do escopo do `except`.
  Confirmado programaticamente: `TRY_BLOCK_SPAN=['db.delete(question)', 'db.flush()']`.
- Nenhuma coluna em `core/app/models.py` usa `ondelete=` explícito; a única
  FK que pode disparar durante este `DELETE FROM questions` + cascade ORM
  (`Question.rubrics` tem `cascade="all, delete-orphan"`, que apaga
  `Rubric`/`RubricCriterion` antes, client-side) é `answers.question_id ->
  questions.id` (o caso pretendido) ou, teoricamente,
  `correction_jobs.rubric_id -> rubrics.id`. Mas `CorrectionJob` só é
  criado por `request_correction`, que exige uma `Answer` pré-existente
  para a mesma questão — portanto, se esse segundo caminho disparasse, uma
  `Answer` já existiria de qualquer forma, e a mensagem genérica "Questão
  possui respostas registradas" permaneceria factualmente correta mesmo
  nesse caso extremo. Nenhuma outra tabela referencia `Question` ou
  `Rubric` diretamente.
- Conclusão: o `except IntegrityError` é estruturalmente escopado ao único
  cenário que o código pretende tratar; não há risco concreto de mascarar
  um erro de integridade não relacionado como "409 por resposta
  registrada".

