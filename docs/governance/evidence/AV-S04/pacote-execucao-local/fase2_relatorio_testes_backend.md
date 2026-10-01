# AV-S04 — Fase 2 — relatório da suíte backend

Data da execução: 2026-10-01, fuso America/Fortaleza (`-03:00`).

## Escopo realizado

Foi corrigida e ampliada a suíte
`core/app/tests/test_assessment_multiple_questions.py`, de 12 para 20 testes.
Não houve alteração de código de produção, migração, frontend, contrato ou
governança preexistente. O relatório criado indevidamente em
`docs/governance/snapshots/relatorio_fase2_testes_backend.md` foi removido;
seu inventário histórico de comandos foi substituído pelos resultados reais
reexecutados nesta fatia.

Ambiente: macOS, Python 3.11.16, pytest 9.1.1, banco SQLite temporário por
teste conforme `app/tests/conftest.py`.

## Rastreabilidade AC → testes

| Critério | Teste(s) e evidência backend |
|---|---|
| AC-01/02 | `test_ac01_ac02_create_and_read_ordered_questions`: cria três questões e confirma IDs únicos e ordem integral `1,2,3` no GET. |
| AC-03 | `test_ac03_other_professor_cannot_mutate_draft`: professor distinto recebe 403 e o conteúdo permanece idêntico. |
| AC-04 | `test_ac04_zero_questions_is_atomic` e `test_ac04_rubric_mismatch_is_atomic`: cenários separados, ambos 422, estado `RASCUNHO` e representação integral inalterada; nenhuma rubrica é publicada no mismatch. |
| AC-05 | `test_ac05_published_mutations_return_409`: título, edição, exclusão, reordenação, adição e rubrica retornam 409 após publicação. |
| AC-06 | `test_ac06_clone_excludes_operational_history`: novos IDs e `cloned_from_id`; consultas relacionais comprovam ausência de Answer, CorrectionJob e HumanReview no clone; Answer, job, review e AuditEvent históricos continuam ligados ao original; o clone contém somente seu AuditEvent `CLONE`, com origem exata. |
| AC-07 | `test_ac07_original_context_survives_clone_republication`: cria job pinado, clona, altera questão/rubrica, republica e confirma no GET de contexto o assessment, questão, referência, critério e versão 1 originais, além do `rubric_id` persistido no job. |
| AC-08 | `test_ac08_second_question_context_and_highest_rubric_version`: cria duas versões de rubrica para cada uma de duas questões; publicação marca exatamente a versão 2; job da segunda retorna a segunda questão e nunca a primeira. |
| AC-09/16 | `test_ac09_ac16_payload_truth_table_and_output_cardinality`: cobre plural, singular, ambos com mensagem exata, nenhum, `questions=[]` com mensagem exata e singular + lista vazia; saída singular somente para cardinalidade 1 e `None` para 0 ou mais de 1. A parte de OpenAPI/frontend de AC-09 pertence às fases próprias, não a esta suíte backend. |
| AC-10 | Não aplicável à suíte backend: critério de interface, validado na fase de frontend/navegador. |
| AC-11 | `test_ac11_reorder_rollback_and_delete_recompaction` confirma rollback integral para ID repetido, faltante e de outra avaliação, além de recompactação; `test_ac11_answered_draft_delete_conflict` confirma mensagem exata do 409 e preservação de Question e Answer. |
| AC-12 | Cinco testes separados cobrem 50/51, `statement` 10.000/10.001, `reference_answer` 10.000/10.001, ausência de `max_length` no metadata de `title` mais título longo, `max_score` zero/negativo e metadata SQLAlchemy `Numeric(6,2)`. SQLite não é usado como prova de enforcement de precisão/escala. |
| AC-13 | `test_ac13_legacy_single_question_read`: dado ORM preexistente retorna 200, conteúdo intacto, `position=1` e saída singular compatível; a suíte backend completa também permaneceu verde. |
| AC-14 | `test_ac14_mutations_use_shared_authorization_helpers`: spies comprovam que update, rubric e delete passam pelo mesmo `_get_assessment_for_question` e por `require_assessment_mutation`; add/reorder chamam diretamente `require_assessment_mutation` por `assessment_id`, sem passar pelo helper de questão. |
| AC-15 | `test_ac15_sqlite_concurrency_smoke`: captura status e exceções das duas threads e confirma a invariante `1..N`. É somente smoke em SQLite e **não** prova `SELECT ... FOR UPDATE`. Locks reais devem ser validados por evidência PostgreSQL separada. |
| AC-17 | `test_ac17_legacy_log_payload_is_distinguishable`: forma canônica não emite o evento legado; forma singular emite exatamente `assessment_created_legacy_singular_payload`, com correlation ID não vazio e campos estruturados completos/exatos. |
| AC-18 | Não validado por esta suíte SQLite. Migração, backfill, constraint e comportamento PostgreSQL são objeto de script/evidência PostgreSQL isolada separada. |

## Execuções reais

### Suíte específica

```text
cd core && .venv/bin/python -m pytest app/tests/test_assessment_multiple_questions.py -v
```

Resultado: **20 passed, 13 warnings in 7.84s**. Os 13 warnings são avisos de
depreciação de dependências (Starlette/httpx, AnyIO, `crypt` e configuração
Pydantic v2); não houve warning originado pelo arquivo novo.

### Suíte backend completa

```text
cd core && .venv/bin/python -m pytest app/tests -q
```

Resultado: **88 passed, 13 warnings in 44.18s**.

### Ruff integral de `app`

```text
cd core && .venv/bin/python -m ruff check --config ../ruff.toml app
```

Resultado: **All checks passed!**

## Limites e estado

- Implementado e validado nesta fatia: suíte comportamental backend e lint.
- Não validado por SQLite: semântica real de lock de linha/`FOR UPDATE`,
  concorrência transacional PostgreSQL e migração/constraints de AC-18.
- Essas provas dependem de execução PostgreSQL isolada e evidência separada;
  nenhum resultado desta suíte é apresentado como substituto delas.
- Nenhuma homologação é declarada. Não houve commit, push, merge, deploy ou
  ação remota.
- A política geral prevê snapshot/dashboard no encerramento, mas a autorização
  desta tarefa limitou as escritas ao teste e a este relatório; esses arquivos
  de governança não foram alterados nesta fatia.
