---
id: "evidencia_validacao_local_ci_cobertura_pg"
tema: "Validação LOCAL do step de CI de concorrência PostgreSQL"
data: "2026-10-15 (America/Sao_Paulo)"
base: "main cde87cc74f37dfca6136a1c8eeeb5489318045e2"
branch: "ci/cobertura-postgres-concorrencia"
---

# Evidência — validação local do step de CI (concorrência PostgreSQL)

> Esta é validação **LOCAL** da LÓGICA do step. A execução remota real no
> GitHub Actions **não foi** feita (sem publicação nesta rodada) e a lacuna
> remota **não** é declarada resolvida — ver §5.

## 1. Mudança

`.github/workflows/ci.yml`: **só adição** (113 inserções, 0 remoções,
confirmado por `git diff`). Um step novo "Run PostgreSQL concurrency
tests (real Postgres, not SQLite)" no job `core`, APÓS o step SQLite
"Run core tests" (preservado intacto — ACD-CI-01/08). Nenhum arquivo de
produto ou de teste alterado.

## 2. Inventário coletado (não presumido)

10 casos PostgreSQL guardados por `AVALIA_TEST_POSTGRES_URL`:
- `test_answer_image_deletion.py`: 5 (delete-vs-confirm; concurrent_deletes[2]/[8];
  restore-após-confirmação-409; restore-vs-confirm).
- `test_manual_transcription.py`: 5 (drafts[2]/[8]; confirms[2]/[8];
  confirm_and_draft_never_reopen).

## 3. Decisão de design (descoberta por execução local, não presumida)

- A fixture `pg_engine` de `test_answer_image_deletion.py` **exige**
  `alembic upgrade head` (assert `alembic_version == b8d3e5f7a2c4`).
- A fixture `pg_engine` de `test_manual_transcription.py` usa
  `Base.metadata.create_all` e **`drop_all` no teardown** — destruiria o
  schema do outro arquivo se compartilhassem banco.
- As fixtures têm **guarda interna**: o nome do banco deve conter "test"
  e não pode ser `avalia_dev`/`postgres` (protege bancos reais).
- **Portanto o step usa DOIS bancos descartáveis separados**, ambos com
  "test" no nome: `avalia_test_ci_img_<run_id>` (migrado via alembic) e
  `avalia_test_ci_txn_<run_id>` (create_all). Isso foi comprovado:
  rodar os dois arquivos no mesmo banco → `relation "organizations" does
  not exist` (drop_all do segundo); em bancos separados → 10 passed.

## 4. Resultados da validação local (execução real)

Simulação fiel da LÓGICA do step contra PostgreSQL local (usuário local
no lugar das credenciais do serviço da CI; o resto idêntico):

- **Caminho feliz:** `pg_img.xml {tests:5, failures:0, errors:0,
  skipped:0}` + `pg_txn.xml {tests:5, ...}` → **TOTAL 10 tests, 0
  failures, 0 errors, 0 skipped**; guard imprime "OK: 10 casos ...
  executados e aprovados (0 skipped)"; bancos descartáveis dropados.
- **Guard negativo (ACD-CI-04):** sem `AVALIA_TEST_POSTGRES_URL` os
  `test_pg_*` ficam **SKIPPED** (confirmado: `5 skipped` por arquivo com
  `-rs`); o guard (`if skipped != 0: exit 1`, e também `errors != 0`,
  `tests != 10`) **falha com exit 1**. Comprovado em dois cenários
  (skipped puro e erro de schema).
- **Sintaxe:** YAML válido (`yaml.safe_load`); bloco `run` do step
  passa `bash -n` (sintaxe shell OK).
- **Bancos protegidos:** nenhum toque; a guarda de nome ("test") e o uso
  de `avalia_dev` apenas como banco administrativo-alvo foram evitados —
  o step usa o banco `postgres` só para `CREATE/DROP DATABASE`, nunca
  `avalia_dev` para testes. Bancos locais de simulação criados e dropados.

Credenciais: o step reusa `avalia_user`/`avalia_password` já declaradas
no serviço postgres do próprio workflow (não são segredo de produção;
nenhum segredo novo; nada de credencial de produção exposto).

## 7. Execução remota — COMPROVADA (run real do GitHub Actions)

> **Status da lacuna: TECNICAMENTE RESOLVIDA** (comprovada por run real),
> ainda **aguardando homologação e integração** (sem merge nesta rodada).

- **Run:** 38731695435 — https://github.com/rafaelinfopiaui/avalia-platform/actions/runs/38731695435
- **HEAD publicado:** c4e71e025d9f8082de46723f63cc6748b7e3c25e (PR #21, rascunho, base main)
- **Jobs:** Core API, AI Engine, Frontend — todos **success**.

Resultados separados (log literal, não só status verde):

- **Step SQLite "Run core tests":** `232 passed, 10 skipped` — os 10
  skipped são os `test_pg_*`, skip **esperado** nesse step. (NÃO
  confundir com o step PostgreSQL.)
- **Step PostgreSQL "Run PostgreSQL concurrency tests":**
  - `test_answer_image_deletion.py` (exclusão de imagens): **5 passed**
    (`delete_last_image_vs_confirm`; `concurrent_deletes[2]`/`[8]`;
    `restore_after_confirmation...409_even_for_admin`;
    `restore_vs_confirm_never_changes_confirmed_image_set`) —
    `5 passed, 28 deselected`.
  - `test_manual_transcription.py` (transcrição): **5 passed**
    (`concurrent_drafts[2]`/`[8]`; `concurrent_confirms[2]`/`[8]`;
    `confirm_and_draft_never_reopen`) — `5 passed, 33 deselected`.
  - JUnit: `pg_img.xml {tests:5, failures:0, errors:0, skipped:0}`;
    `pg_txn.xml {tests:5, ...}`; `TOTAL {tests:10, failures:0, errors:0,
    skipped:0}`.
  - **Guard aprovado:** `OK: 10 casos de concorrência PostgreSQL
    executados e aprovados (0 skipped).`
  - **0 skipped no step PostgreSQL** (as ocorrências da palavra "SKIPPED"
    no log são eco do código do próprio guard, não resultado de teste; o
    resumo do pytest é `5 passed` em cada arquivo, 0 skipped).
  - **Limpeza:** bancos descartáveis `avalia_test_ci_img_38731695435` e
    `avalia_test_ci_txn_38731695435` criados e dropados; o step 8 concluiu
    com **success** sob `set -e` (o bloco de DROP final executou sem erro);
    runner efêmero descartado ao fim do job.

Nenhum banco protegido tocado (a CI usa só seu serviço postgres efêmero).
Guard não foi enfraquecido para obter verde — segue exigindo 10/0/0.

## 5. Revisão independente — CONCLUÍDA (APROVADO COM RESSALVAS, incorporadas)

Nota de executor: o **Claude Code estava indisponível** (OAuth expirado,
`loggedIn: false` — exige login interativo seu; não contornei). Como a
mudança é pequena e totalmente especificada no escopo, e a validação real
é do orquestrador de qualquer forma, **implementei eu (orquestrador)** o
step e validei por execução local; mantive o Antigravity como revisor
independente do delta.

A revisão do Antigravity (modelo "Gemini 3.8 Flash High", família
distinta) **foi concluída**: **APROVADO COM RESSALVAS** — 2 achados de
severidade BAIXA (defesa em profundidade), ambos **incorporados**:
- ACH-01: asserção de segurança (`"test" in name`) replicada no bloco de
  limpeza final;
- ACH-02: `rm -f pg_img.xml pg_txn.xml` antes dos pytests.
Após incorporar: YAML válido, `bash -n` OK, simulação local = 10 tests,
0 skipped, guard "OK". Parecer completo em
`parecer_antigravity_delta_ci.md`.

Houve indisponibilidade transitória de rede antes da revisão (DNS
SERVFAIL do endpoint do Antigravity no resolvedor local; `8.8.8.8`
resolvia — intermitência local, não do serviço). Não troquei de provedor
pago nem usei Codex como revisor geral; aguardei o DNS normalizar e
reexecutei no próprio Antigravity.

## 6. Critérios para conferir a 1ª execução remota (após futura autorização de publicação)

Quando/se autorizado publicar, conferir na run real do GitHub Actions
(NÃO deduzir por nome de job nem presença de serviço):
1. O job `core` tem **dois** steps distintos: "Run core tests" (SQLite,
   `232 passed, 10 skipped`) e "Run PostgreSQL concurrency tests".
2. No step PostgreSQL, a saída (`-v -rsa`) mostra os **10 casos
   `test_pg_*` como PASSED** (5 em cada arquivo), **0 skipped**.
3. O guard imprime "OK: 10 casos de concorrência PostgreSQL executados e
   aprovados (0 skipped)". O step conclui com sucesso só nesse caso.
4. Teste negativo opcional (sanidade do guard): uma alteração que remova
   `AVALIA_TEST_POSTGRES_URL` deve fazer o step **falhar** (não passar
   silenciosamente). Não fazer isso na run oficial — é só a prova
   conceitual do guard.
5. A suíte SQLite permanece verde e inalterada; nenhum banco protegido é
   tocado (a CI usa só seu serviço postgres efêmero).

Só após uma run real satisfazer 1–3 é que a lacuna remota pode ser
declarada resolvida.
