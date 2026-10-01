# AV-S04 — recuperação da migração após falha no índice concorrente

- Data/fuso: 2026-10-01, America/Fortaleza (UTC-03:00)
- Executor: Codex, execução local solicitada por Rafael
- Branch observada: `feat/av-s04-multiplas-questoes`
- Referência Git observada: `73a1a4335a14c25a7fbafcefa9d8d5499709098f`
- Banco protegido: `avalia_dev` não foi acessado nem alterado

## RED

O defeito foi confirmado por inspeção do fluxo original: o primeiro
`autocommit_block()` confirma as colunas, o backfill e os `SET NOT NULL`; uma
falha em `CREATE UNIQUE INDEX CONCURRENTLY` deixa a revisão Alembic em
`c4a8b2d91e37`, fazendo a próxima execução tentar novamente
`ADD COLUMN created_at` e resultar em `DuplicateColumn`.

A reprodução real solicitada não pôde ser repetida nesta sessão. As duas rotas
de execução foram bloqueadas pelo sandbox antes de qualquer conexão/criação de
banco:

1. PostgreSQL 16 local, socket e TCP: `Operation not permitted` ao conectar;
2. cluster PostgreSQL 16 descartável em `/private/tmp`, socket próprio e TCP
   desativado: `initdb` falhou antes de criar o cluster com
   `could not create shared memory segment`, `shmget(..., size=56, ...):
   Operation not permitted`, mesmo com `shared_memory_type=mmap` e
   `dynamic_shared_memory_type=mmap`.

Portanto, o RED descrito pelo solicitante continua sendo evidência histórica de
execução independente; esta sessão não o promove a reprodução própria.

## Correção implementada

Arquivo: `core/alembic/versions/a9f4c2e71b06_add_question_position_and_clone.py`.

- retomada idempotente dos checkpoints compatíveis de colunas, nulabilidade,
  checks auxiliares, índice, unique constraint, coluna de clonagem e FK;
- rejeição explícita de objetos homônimos incompatíveis;
- detecção do índice nominal via `pg_class`/`pg_index` e remoção somente quando
  ele tem a forma esperada e está `INVALID`, usando
  `DROP INDEX CONCURRENTLY` em `autocommit_block()`;
- reutilização de índice válido exato sem `CREATE INDEX IF NOT EXISTS`;
- reconhecimento da unique constraint já anexada, cujo índice foi renomeado
  pelo PostgreSQL;
- query `GROUP BY` obrigatória e backfill determinístico
  `created_at ASC, id ASC` preservados;
- padrão `CHECK NOT VALID` + `VALIDATE` + `SET NOT NULL` preservado quando a
  coluna ainda é nullable;
- downgrade preservado para o estado integralmente migrado.

## Validação

Runner reexecutável criado em
`docs/governance/evidence/AV-S04/pacote-execucao-local/validate_migration_recovery.sh`.
Ele inicializa um cluster PostgreSQL 16 temporário, desliga TCP, usa apenas
nomes com prefixo `av_s04_migration_`, recusa explicitamente `avalia_dev`,
executa A/B/C e destrói somente o diretório temporário validado.

- A fresh: **não executado**, bloqueado no `initdb` pelo sandbox;
- B recovery-invalid-index: **não executado**, mesmo bloqueio;
- C checkpoint-valid-index: **não executado**, mesmo bloqueio;
- import/compilação Python da revisão: passou;
- ruff solicitado: passou (`All checks passed!`).

Não há alegação de GREEN real A/B/C nesta evidência. A próxima ação é executar
o runner em ambiente que permita PostgreSQL 16 local e anexar sua saída real.

## Reconciliação — 2026-10-01 (execução direta via terminal Hermes)

O bloqueio de sandbox relatado acima afetava apenas a rota de execução do
Codex CLI (`codex exec --sandbox workspace-write`), que roda em bubblewrap
sem acesso a `shmget`/sockets. Fora dessa rota, o runner foi executado
diretamente (sem sandbox adicional) com sucesso, usando o PostgreSQL 16
(Homebrew) já instalado localmente e acessível como `current_user` sem senha:

```text
$ bash docs/governance/evidence/AV-S04/pacote-execucao-local/validate_migration_recovery.sh
...
A GREEN
=== B recovery-invalid-index ===
...
ERROR:  could not create unique index "ix_questions_assessment_position"
DETAIL:  Key (assessment_id, "position")=(a1, 1) is duplicated.
...
B GREEN
=== C checkpoint-valid-index ===
...
C GREEN
=== ruff ===
All checks passed!
ALL GREEN
```

Execução repetida uma segunda vez na mesma sessão para confirmar
determinismo: resultado idêntico (`A GREEN`, `B GREEN`, `C GREEN`,
`All checks passed!`, `ALL GREEN`).

Adicionalmente, `run_postgres_row_lock_validation.sh` (validação de
`SELECT ... FOR UPDATE` via FastAPI `TestClient` + threads contra o mesmo
PostgreSQL isolado) também foi reexecutado com sucesso:

```text
SECOND_REQUEST_BLOCKED_WHILE_FIRST_HELD_LOCK=True
REQUEST_STATUSES=[200, 200]
FINAL_POSITIONS=[1, 2, 3, 4, 5]
POSTGRES_FOR_UPDATE_CONCURRENCY_GREEN
```

Conclusão: o GREEN A/B/C e o GREEN de row-lock são, a partir desta
reconciliação, resultado de execução real e reproduzida (duas vezes para a
migração, uma vez para o row-lock), não mais apenas relato de terceiro não
verificado. AC-15 (concorrência) e AC-18 (migração Postgres) estão cobertos
por evidência Postgres real, não apenas SQLite smoke test.
