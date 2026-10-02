# Reconciliação de contagens — execução real de P4 (2026-10-02)

## 1. Contagens antes e depois, com evidência

| Tabela | Antes (backup final + diagnóstico real) | Depois (estado atual, confirmado) | Evidência |
|---|---|---|---|
| `human_reviews` | **18** | **16** | Antes: `ASSERTION_OK_RESTORED_HUMAN_REVIEWS=18` em `01_validacao_backup_final_isolado.txt:14` (restore do backup final capturado às 10:15:44) e confirmado de novo pelo diagnóstico real em `02_diagnostico_real.txt` (3 linhas no grupo duplicado, 15 outras não listadas mas presentes — o total de 18 é a contagem agregada do restore, não a soma manual das linhas do diagnóstico, que só lista o grupo duplicado). Depois: `SELECT COUNT(*) FROM human_reviews` executado nesta sessão = 16 |
| `human_reviews_superseded` | **0 (tabela não existia)** | **2** | Antes: `to_regclass('public.human_reviews_superseded')` retornou vazio em toda verificação pré-saneamento desta sessão e das sessões anteriores (seção 1 do snapshot `EXEC-2026-10-02-01`). Depois: `SELECT COUNT(*) FROM human_reviews_superseded` = 2, confirmado em `03_saneamento_real.txt:17` (`INSERT 0 2`) |
| `audit_events` | **36** | **36** | Antes: `ASSERTION_OK_RESTORED_AUDIT_EVENTS=36` em `01_validacao_backup_final_isolado.txt:15`. Depois: `SELECT COUNT(*) FROM audit_events` = 36, confirmado nesta sessão. **Nenhuma mudança** — o saneamento não toca `audit_events` (confirmado também pelo script, que nunca executa DML nessa tabela) |

**Aritmética do saneamento:** 18 (antes) − 2 (arquivadas) = 16 (ativas depois). 0 + 2 (arquivadas) = 2. Soma total (ativas + arquivadas) permanece 18 em ambos os momentos — nenhuma linha foi perdida, apenas movida de `human_reviews` para `human_reviews_superseded`.

## 2. IDs das duas linhas arquivadas e da vencedora

Confirmado por leitura direta de `human_reviews_superseded` nesta sessão e cruzado com o CSV capturado do backup final (`avalia_dev_P4_execucao_real_20261002_101544_human_reviews.csv`, checksum SHA-256 revalidado antes desta reconciliação: `OK`):

| Papel | ID | `job_id` | `created_at` (preservado) | `superseded_reason` |
|---|---|---|---|---|
| Vencedora (permanece em `human_reviews`) | `31d31b5c-05c7-4206-b2ff-43b2eda14026` | `4f56a10b-3a44-4df5-9047-adef7546a3c0` | `2026-09-23 22:53:35.110755` | — |
| Arquivada 1 | `8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c` | `4f56a10b-3a44-4df5-9047-adef7546a3c0` | `2026-09-23 22:55:15.904278` | `duplicate-equivalent-review-pre-BL-AV-1-10` |
| Arquivada 2 | `9459489c-dd8e-4f33-936a-bc76cb7d5f0b` | `4f56a10b-3a44-4df5-9047-adef7546a3c0` | `2026-09-23 22:58:47.630896` | `duplicate-equivalent-review-pre-BL-AV-1-10` |

Estes 3 IDs são exatamente os 3 IDs nominais documentados em todas as rodadas anteriores de planejamento e revisão (plano consolidado, pareceres de revisão independente, proposta de 676 linhas) — nenhum ID novo ou inesperado.

## 3. Diferença histórica (18 vs. as "8 revisões" mencionadas em registros anteriores)

**O histórico anterior registrava `human_reviews=8` em múltiplos snapshots datados de 2026-09-24** (`snapshot_EXEC-2026-09-24-03_BL-AV-1-10-postgres.md:64/69`, `snapshot_EXEC-2026-09-24-04_pacote-revisao.md:60`, `snapshot_EXEC-2026-09-24-05_pr-ci-remota.md:74`, `snapshot_EXEC-2026-09-24-07_integracao-main.md:59`, `AV-S02-review-package/00_pacote_revisao.md:217-218`) — todas essas verificações foram feitas entre aproximadamente 08:05 e 09:44 (-03) do dia 2026-09-24.

Reconstituindo a tabela por `created_at` nesta sessão (somente leitura, sem alterar nada), as linhas com `created_at` anterior a `2026-09-24 09:44:00` (o horário da última verificação histórica que registrou "8 linhas") são exatamente **7**, não 8:

```
7950de4e-... | 6659e4b6-... | 2026-09-09 11:37:26
91d33e3b-... | f6fe7abd-... | 2026-09-10 08:40:26
ecc32db2-... | f0368eb0-... | 2026-09-11 19:21:44
216ddf32-... | c69d2d26-... | 2026-09-23 19:25:50
31d31b5c-... | 4f56a10b-... | 2026-09-23 22:53:35  (vencedora)
8a9c2ba6-... | 4f56a10b-... | 2026-09-23 22:55:15  (arquivada 1)
9459489c-... | 4f56a10b-... | 2026-09-23 22:58:47  (arquivada 2)
```

Isso é 7 linhas distintas, não 8. **Esta sessão não consegue reconciliar esse número exato** com os registros históricos a partir dos dados hoje disponíveis — é possível que a contagem "8" nos snapshots de 2026-09-24 já incluísse uma oitava linha criada em algum momento próximo (o próprio histórico documenta um job de teste visual, `d3c7335e-419e-4d72-90c2-dbde7100c42c`, criado às `2026-09-24 10:05:19`, **depois** da última verificação de "8 linhas" às 09:44 — portanto não é essa linha), ou que algum dos registros históricos tenha contado de forma ligeiramente diferente (ex.: incluindo uma linha com timestamp muito próximo ao corte, ou um erro de contagem manual). Nenhuma evidência nesta sessão permite determinar qual das duas possibilidades é correta, e **nenhuma autoria ou causa é atribuída** a essa diferença de 1 linha — ela não afeta o saneamento executado (que tratou exatamente o grupo `4f56a10b-...`, sempre com 3 linhas, documentado de forma consistente em toda a trilha desde 2026-09-24).

**As 10 linhas restantes** (das 18 totais pré-saneamento) têm `created_at` entre `2026-09-25 10:54` e `2026-09-25 18:44` — um dia depois da última verificação histórica de "8 linhas". Duas delas (`947923f7-...` e `d3376947-...`) estão associadas a `CorrectionJob`s cujas `Answer`s apontam para avaliações nominalmente conhecidas na governança (`Estruturas de Dados — Apresentação`, `Estruturas de Dados — Avaliação 1`); as outras 8 têm `student_name_fake` genérico (`"Aluno fictício"`/variações) sem correspondência textual localizada nos documentos de governança revisados nesta sessão. **Nenhuma dessas 10 linhas foi criada por esta execução de P4** — todas têm `created_at` de 2026-09-25, muito antes desta sessão (2026-10-02), e nenhuma delas foi tocada pelo saneamento (que agiu apenas sobre as 2 linhas arquivadas do grupo `4f56a10b-...`). A origem exata (qual atividade/sessão as criou) não está determinada pelos registros de governança disponíveis — fica registrada aqui como lacuna de rastreabilidade histórica, não como achado desta execução de P4, e sem atribuição de causa não comprovada.

**Conclusão da reconciliação:** a contagem de 18 (antes de P4) é real, verificada por duas fontes independentes (restore do backup final + diagnóstico direto), e é maior que as "8 linhas" documentadas até 2026-09-24 porque 10 linhas adicionais foram criadas em 2026-09-25 (um dia depois), por atividade não precisamente identificada nos registros revisados nesta sessão. A diferença de 1 linha entre a última contagem histórica exata (7, reconstituída por timestamp) e o número frequentemente citado nos documentos ("8") não foi resolvida por esta reconciliação e é registrada como tal — sem inventar uma explicação.

## 4. Conservação confirmada

- **Apenas as duas linhas previstas saíram da tabela ativa**: confirmado por `SELECT COUNT(*) FROM human_reviews WHERE id IN ('8a9c2ba6-...', '9459489c-...')` = 0 (não estão mais ativas) e pela contagem líquida (18→16, exatamente −2). Nenhuma das outras 16 linhas foi alterada ou removida.
- **Conteúdo arquivado corresponde integralmente ao original**: comparação campo a campo entre o CSV pré-saneamento (capturado do próprio `avalia_dev` antes da transação, como parte do backup final) e o conteúdo atual de `human_reviews_superseded` — `reviewer_id`, `decision`, `final_total`, `final_scores_json`, `justification` e `created_at` são idênticos byte a byte para as 2 linhas arquivadas. O próprio script de saneamento já executa essa comparação coluna-a-coluna internamente antes do `DELETE` (linha do script `av_s02_saneamento_human_reviews.sql`, já revisada e aprovada em 3 rodadas independentes) — esta sessão reconfirma externamente, por leitura direta, o mesmo resultado.
- **Vencedora e demais registros preservados**: `31d31b5c-...` confirmada presente com os mesmos `created_at`/`final_total`/`final_scores_json`; as outras 15 linhas de `human_reviews` (incluindo as 10 de 2026-09-25 e as 5 restantes de antes) não foram tocadas — contagem líquida de −2 confirma isso aritmeticamente.
- **Auditoria permaneceu inalterada**: `audit_events` segue em 36 antes e depois; os 3 `AuditEvent`s nominais associados ao job saneado (`b12db6d4-...`, `4f737eab-...`, `cad4d910-...`) têm `created_at` idênticos ao inventário pré-operação, confirmados por leitura direta nesta sessão e já registrados no snapshot `EXEC-2026-10-02-01`.

Nenhuma nova escrita foi feita em `avalia_dev` durante esta reconciliação — todas as consultas acima são `SELECT`, e os valores "antes" vêm de evidência já preservada (logs de execução e backup final), não de uma nova captura.
