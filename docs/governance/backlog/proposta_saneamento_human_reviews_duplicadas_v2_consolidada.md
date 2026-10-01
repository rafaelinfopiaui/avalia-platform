<!--
VERSÃO CONSOLIDADA V2 — BASE: proposta local de 676 linhas recuperada do
commit aa8031a (branch docs/av-s02-encerramento-planos-operacionais),
preservada sem sobrescrever a versão integrada de 359 linhas.

Status: preparada para ensaio SOMENTE em PostgreSQL isolado nesta rodada;
NÃO aprovada para execução em avalia_dev. Scripts executáveis locais:
- core/scripts/av_s02_diagnostico_human_reviews.sql
- core/scripts/av_s02_saneamento_human_reviews.sql
- core/scripts/av_s02_validacao_pos_migracoes.sql
- core/scripts/av_s02_recuperacao_saneamento.sql
- core/scripts/run_avalia_dev_update_dry_run.sh

As nove melhorias identificadas em
`docs/governance/evidence/GOV-006/comparacao_proposta_saneamento_676.md`
já estão incorporadas nesta base de 676 linhas. O histórico da versão
integrada de 359 linhas permanece intacto em
`proposta_saneamento_human_reviews_duplicadas.md`; o delta reversível
permanece em `docs/governance/evidence/GOV-006/diff_proposta_saneamento_676_vs_integrada.txt`.
-->

# Procedimento de saneamento de duplicatas + aplicação da migração de unicidade em `avalia_dev`

Status: **PROPOSTA PARA APROVAÇÃO. NADA FOI EXECUTADO.** Nenhum comando deste documento foi
rodado contra `avalia_dev`. Depende de aprovação explícita de Rafael, item por item, antes de
qualquer execução. Após aprovação, a execução real ainda exige autorização específica separada
para o passo de aplicação em produção (seção 9).

## 1. Inventário exato dos registros afetados

Consulta real executada em `avalia_dev` em 2026-09-24 (reproduzível, não fabricada):

```sql
SELECT job_id, COUNT(*) AS review_count
FROM human_reviews
GROUP BY job_id
HAVING COUNT(*) > 1;
```

Resultado: **exatamente 1 grupo duplicado em toda a base**, o job `4f56a10b-3a44-4df5-9047-adef7546a3c0`, com 3 linhas.

```sql
SELECT id, job_id, reviewer_id, decision, final_total, final_scores_json, justification, created_at
FROM human_reviews
WHERE job_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0'
ORDER BY created_at;
```

| id | reviewer_id | decision | final_total | final_scores_json | justification | created_at |
|---|---|---|---|---|---|---|
| `31d31b5c-05c7-4206-b2ff-43b2eda14026` | `cabba145-18bc-40a1-9faa-489f4bfda018` | APPROVE | 2.00 | `[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]` | (vazio) | 2026-09-23 22:53:35.110755 |
| `8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c` | `cabba145-18bc-40a1-9faa-489f4bfda018` | APPROVE | 2.00 | (idêntico ao acima, byte a byte) | (vazio) | 2026-09-23 22:55:15.904278 |
| `9459489c-dd8e-4f33-936a-bc76cb7d5f0b` | `cabba145-18bc-40a1-9faa-489f4bfda018` | APPROVE | 2.00 | (idêntico ao acima, byte a byte) | (vazio) | 2026-09-23 22:58:47.630896 |

Dado fictício de teste (job criado durante a validação visual de AV-S02 com dados de demonstração), não dado real de aluno/professor.

`AuditEvent` correlacionados ao grupo (sem FK direta com `human_reviews`; associação corroborada por `resource_id`, `resource_type`, `action`, `actor_id` e janela temporal):

```sql
SELECT id, actor_id, action, resource_type, resource_id,
       before_json, after_json, created_at
FROM audit_events
WHERE resource_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0'
  AND resource_type = 'CorrectionJob'
  AND action = 'REVIEW_APPROVE'
  AND actor_id = 'cabba145-18bc-40a1-9faa-489f4bfda018'
  AND created_at BETWEEN '2026-09-23 22:53:00' AND '2026-09-23 22:59:30'
ORDER BY created_at;
```

| id | actor_id | action | before_json | after_json | created_at |
|---|---|---|---|---|---|
| `b12db6d4-3b44-42ca-aa9a-99748fc4b982` | `cabba145-18bc-40a1-9faa-489f4bfda018` | REVIEW_APPROVE | scores C1=1.00, C2=1.00 (objeto) | mesmos scores (array) | 2026-09-23 22:53:35.114334 |
| `4f737eab-3ba0-40af-8738-ae847377ba34` | `cabba145-18bc-40a1-9faa-489f4bfda018` | REVIEW_APPROVE | idêntico ao acima, byte a byte | idêntico ao acima, byte a byte | 2026-09-23 22:55:15.907615 |
| `cad4d910-8c91-4a7e-9714-266fac3f7ee6` | `cabba145-18bc-40a1-9faa-489f4bfda018` | REVIEW_APPROVE | idêntico ao acima, byte a byte | idêntico ao acima, byte a byte | 2026-09-23 22:58:47.636134 |

O procedimento de aprovação deve registrar também `before_json` e `after_json` desses 3 eventos no relatório pré-operação. Mesmo com a correlação forte acima, não alegamos FK inexistente: a associação continua lógica/temporal. Total afetado pela preservação: **3 linhas em `human_reviews` + 3 linhas em `audit_events`**, todas relativas ao mesmo job; apenas as 2 revisões equivalentes excedentes serão movidas, e nenhum evento de auditoria será tocado.

## 2. Confirmação de equivalência considerando todos os campos relevantes

Campos comparados nas 3 linhas: `job_id`, `reviewer_id`, `decision`, `final_total`, `final_scores_json` (comparação textual completa, não apenas por amostragem), `justification`. **Todos idênticos**, exceto `id` (chave primária, esperado ser distinto) e `created_at` (timestamp de cada reenvio, esperado ser distinto).

Isso corresponde exatamente ao critério de equivalência já implementado em `core/app/main.py::_review_is_equivalent` (mesmo `reviewer_id`, `decision`, `final_scores` normalizados, `justification` normalizada None/""). As 3 linhas são o **mesmo ato de decisão humana**, registrado 3 vezes pela ausência histórica de idempotência (antes da correção de `BL-AV-1-10`) — não há divergência de nota, decisão ou revisor. **Não há caso conflitante nesta base hoje.**

## 3. Regra proposta para selecionar a revisão ativa

Como as 3 linhas são equivalentes (não conflitantes), a escolha de qual linha permanece como "ativa" em `human_reviews` é neutra em conteúdo — qualquer uma delas expressa a mesma decisão. A regra proposta, para ter um critério objetivo e auditável:

> **Manter a linha de menor `created_at`** (a primeira decisão registrada, `31d31b5c-...`, 2026-09-23 22:53:35), por ser a que primeiro teria sido aceita caso a idempotência já existisse na época.

Esta regra só é segura porque o caso real é equivalente. **Se algum grupo futuro (nesta base ou em outra) for classificado como conflitante** (decisões realmente diferentes), esta regra automática **não se aplica** — a escolha da linha vencedora nesse caso exige decisão explícita de Rafael, registrada nominalmente, não uma regra automática por data. Nenhum caso conflitante existe hoje, mas o script de diagnóstico (seção 6) verifica isso antes de qualquer escrita e interrompe se encontrar um.

## 4. Preservação das demais revisões e referências de auditoria

A estratégia é **copiar para uma tabela de arquivo e, na mesma transação, remover (`DELETE`) as
2 linhas excedentes da tabela ativa** — não é ausência de `DELETE`; é preservação por cópia
antes da remoção, nunca perda de dado. As duas operações (INSERT no arquivo + DELETE da tabela
ativa) ocorrem dentro da mesma transação SQL, de modo que uma falha em qualquer etapa reverte
ambas (ver seção 7.3).

- Criar tabela de arquivo `human_reviews_superseded`, com a mesma estrutura de `human_reviews` mais duas colunas: `superseded_reason` (texto, ex.: `"duplicate-equivalent-review-pre-BL-AV-1-10"`) e `superseded_at` (timestamp da operação de saneamento).
- Copiar as 2 linhas não-vencedoras (`8a9c2ba6-...` e `9459489c-...`) para essa tabela, **comparar integralmente** a cópia contra o conteúdo original ainda presente em `human_reviews` (todas as colunas, não apenas contagem) e só então executar o `DELETE` dessas 2 linhas da tabela ativa — na mesma transação, com verificação executável entre as duas operações (ver seção 7.3).
- A linha vencedora (`31d31b5c-...`) permanece em `human_reviews`, com o mesmo `id` — nenhuma referência futura à sua chave primária é afetada.
- Os 3 `AuditEvent` em `audit_events` **não são tocados** — nenhuma linha de auditoria é movida, apagada ou alterada. `audit_events` já é, por desenho, um log de eventos (não uma fonte de verdade de estado atual), e mover/apagar entradas de auditoria destruiria o histórico de que 3 tentativas de aprovação ocorreram — informação relevante mesmo após o saneamento.

## 5. Backup e validação de restauração em ambiente isolado

1. **Backup completo** (antes de qualquer escrita), com checksum:
   ```
   DUMP=/caminho/fora_do_repo/avalia_dev_pre_saneamento_$(date +%Y%m%d_%H%M%S).dump
   pg_dump -Fc -d avalia_dev -f "$DUMP"
   shasum -a 256 "$DUMP" > "$DUMP.sha256"
   pg_restore --list "$DUMP" > "$DUMP.contents.txt"
   ```
   Armazenado fora do repositório (não versionado). A execução só prossegue se `pg_dump` e
   `pg_restore --list` retornarem exit 0 e o checksum for registrado no relatório.

2. **Export específico da tabela afetada**, independente do backup completo, para auditoria mesmo que o dump completo seja descartado:
   ```
   psql -d avalia_dev -c "\copy (SELECT * FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0') TO '/caminho/fora_do_repo/human_reviews_pre_saneamento.csv' WITH CSV HEADER"
   ```

3. **Validação de restauração em ambiente isolado, antes de tocar `avalia_dev`:**
   ```
   # cluster PostgreSQL isolado e descartável (mesmo padrão já usado para a validação da migração)
   initdb -D /tmp/av_pg_saneamento_test -U postgres --auth=trust
   pg_ctl -D /tmp/av_pg_saneamento_test -o "-p 55433 -k /tmp/av_pg_saneamento_test" -l /tmp/av_pg_saneamento_test/server.log start
   createdb -h /tmp/av_pg_saneamento_test -p 55433 -U postgres avalia_dev_restore_test
   pg_restore -h /tmp/av_pg_saneamento_test -p 55433 -U postgres -d avalia_dev_restore_test /caminho/fora_do_repo/avalia_dev_pre_saneamento_<timestamp>.dump
   # confirmar que o restore reproduz exatamente o estado atual:
   psql -h /tmp/av_pg_saneamento_test -p 55433 -U postgres -d avalia_dev_restore_test -c "SELECT COUNT(*) FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0';"
   # esperado: 3
   ```
4. **O procedimento completo de saneamento (seção 6) é executado primeiro neste banco restaurado isolado**, nunca diretamente em `avalia_dev` na primeira tentativa. Só após confirmar que o resultado é o esperado (seção 7) neste ambiente isolado é que a execução em `avalia_dev` (seção 9) pode ser considerada — e mesmo assim, sujeita a autorização específica separada.
5. Ao final da validação isolada: `pg_ctl -D /tmp/av_pg_saneamento_test stop && rm -rf /tmp/av_pg_saneamento_test`.

## 6. Prevenção de escritas concorrentes durante a operação

Risco real: entre o diagnóstico (leitura) e a escrita (mover+deletar), uma nova `HumanReview` poderia ser inserida para o mesmo `job_id` via a aplicação em produção (ex.: se a proteção aplicativa de idempotência falhar ou um usuário estiver ativamente usando o sistema).

Mitigação proposta (todos os itens obrigatórios, não opcionais):
1. Executar a operação em janela de manutenção comunicada, com **todos os writers confirmadamente parados**: processo(s) Core/uvicorn, workers/background tasks, shells/scripts de escrita e qualquer outra instância conectada com capacidade de INSERT. Registrar `pg_stat_activity` antes da operação e abortar se houver writer não identificado.
2. Dentro da transação, adquirir `LOCK TABLE human_reviews IN SHARE ROW EXCLUSIVE MODE;`, que conflita com `INSERT`/`UPDATE`/`DELETE` concorrentes (ao contrário de `SELECT ... FOR UPDATE`, que bloqueia apenas as linhas já encontradas e **não** impediria um novo INSERT para o mesmo `job_id`). **Este lock é válido apenas durante a transação em aberto — ele é liberado automaticamente no `COMMIT` (ou `ROLLBACK`).** Ele não protege o período entre o `COMMIT` do saneamento e a aplicação da migração: nesse intervalo, a única proteção contra concorrência é a manutenção dos writers parados (item 1), não o lock.
3. Após adquirir o lock de tabela, repetir o diagnóstico completo de equivalência e as assertions nominais dos IDs/conteúdos esperados; só então mover as linhas.
4. Manter a aplicação e todos os writers parados desde antes do backup final até a aplicação da `UniqueConstraint` e a verificação da constraint (seção 8) — não liberar escrita entre o `COMMIT` do saneamento e o `COMMIT`/verificação da migração. Essa continuidade dos writers parados é a proteção real desse intervalo, não o `LOCK TABLE`, que já foi liberado.
5. Após a constraint existir e os pós-checks passarem, liberar a aplicação para escrita. A proteção aplicativa integrada em `main` é uma camada adicional, mas não substitui a janela de manutenção deste procedimento.

## 7. Comandos, verificações posteriores e plano de recuperação

**Execução obrigatória com parada no primeiro erro:** todo o script deve ser executado via
`psql -v ON_ERROR_STOP=1 -f av_s02_saneamento_human_reviews.sql`. A opção `ON_ERROR_STOP=1`
interrompe a execução no primeiro comando que falhar, incluindo qualquer `RAISE EXCEPTION` das
assertions abaixo. O script contém seu próprio `LOCK TABLE`/`COMMIT` explícitos (seção 7.3/7.4) —
por isso **não** usar a flag `--single-transaction` do `psql` (que envolveria todo o script numa
transação implícita e entraria em conflito com o `COMMIT` explícito do próprio script). Se
qualquer `DO $$ ... RAISE EXCEPTION ... END $$;` disparar, a sessão psql aborta imediatamente com
`ON_ERROR_STOP=1` e a transação em aberto sofre rollback automático ao encerrar a conexão sem
`COMMIT` — nenhuma escrita parcial é confirmada.

### 7.1 Script de diagnóstico (somente leitura, primeiro passo, sempre)

```sql
-- Diagnóstico geral: inclui final_total e comparação semântica dos scores.
-- O caso inventariado é byte-a-byte idêntico, mas a regra geral não deve
-- classificar como conflito apenas uma diferença de ordem/formatação JSON.
WITH normalized AS (
    SELECT hr.*,
           COALESCE(hr.justification, '') AS justification_norm,
           COALESCE((
               SELECT jsonb_agg(
                   jsonb_build_object(
                       'criterion_id', elem->>'criterion_id',
                       'score', to_char((elem->>'score')::numeric, 'FM999999990.00')
                   ) ORDER BY elem->>'criterion_id'
               )
               FROM jsonb_array_elements(hr.final_scores_json::jsonb) AS elem
           ), '[]'::jsonb) AS scores_norm
    FROM human_reviews hr
), duplicate_groups AS (
    SELECT job_id,
           COUNT(*) AS review_count,
           COUNT(DISTINCT reviewer_id) AS distinct_reviewers,
           COUNT(DISTINCT decision) AS distinct_decisions,
           COUNT(DISTINCT final_total) AS distinct_totals,
           COUNT(DISTINCT scores_norm) AS distinct_scores,
           COUNT(DISTINCT justification_norm) AS distinct_justifications
    FROM normalized
    GROUP BY job_id
    HAVING COUNT(*) > 1
)
SELECT * FROM duplicate_groups ORDER BY job_id;
```

Se qualquer uma das colunas `distinct_reviewers`, `distinct_decisions`, `distinct_totals`,
`distinct_scores` ou `distinct_justifications` for maior que 1 para algum `job_id`, esse grupo é
**conflitante** — a operação para e Rafael decide manualmente antes de qualquer escrita. Essa
verificação também é executada como assertion real dentro da transação (seção 7.3), não apenas
como consulta manual.

### 7.2 Tabela de arquivo (DDL explícito, versionado e executado antes da migração de unicidade)

Não usar `CREATE TABLE ... LIKE INCLUDING ALL`: após a migração, isso poderia copiar por engano a
unicidade de `job_id` para a tabela de arquivo. Também **não** criar uma migration Alembic
descendente de `7b1d6d853f20`: ela não poderia rodar antes do saneamento que permite a própria
`7b1d6d853f20`.

**Sequência proposta, objetiva:** após aprovação deste plano, criar em branch/PR um script SQL
versionado separado (proposta de caminho: `core/scripts/av_s02_saneamento_human_reviews.sql`) que
contém, na ordem: verificação/criação da tabela de arquivo (bloco `DO $$` desta seção, fora do
`BEGIN` explícito; o `psql` confirma esse comando porque opera em modo autocommit nesse ponto — DDL
PostgreSQL continua transacional), depois a transação explícita `BEGIN` (seção 7.3) com lock de
tabela, diagnóstico/assertions executáveis, INSERT, comparação integral (cópia vs. original),
DELETE, pós-checks executáveis e `COMMIT` (seção 7.4). A migração `7b1d6d853f20` é um passo
separado, executado depois, com `alembic upgrade head`, ainda com os writers parados.

DDL explícito, sem FK/unique que impeça preservar o histórico. A criação é condicional e validada
por assertion executável, não por `IF NOT EXISTS` silencioso:

```sql
DO $$
DECLARE
    v_table_exists boolean;
    v_schema_ok boolean;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_catalog.pg_tables
        WHERE schemaname = 'public' AND tablename = 'human_reviews_superseded'
    ) INTO v_table_exists;

    IF NOT v_table_exists THEN
        CREATE TABLE human_reviews_superseded (
            id VARCHAR PRIMARY KEY,
            job_id VARCHAR NOT NULL,
            reviewer_id VARCHAR NOT NULL,
            decision reviewdecision NOT NULL,
            final_total NUMERIC(6,2) NOT NULL,
            final_scores_json TEXT NOT NULL,
            justification TEXT,
            created_at TIMESTAMP NOT NULL,
            superseded_reason TEXT NOT NULL,
            superseded_at TIMESTAMP NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_human_reviews_superseded_job_id
            ON human_reviews_superseded(job_id);
    ELSE
        -- Tabela já existe: validar schema real, não seguir silenciosamente.
        SELECT
            (SELECT COUNT(*) = 10
             FROM information_schema.columns
             WHERE table_schema = 'public'
               AND table_name = 'human_reviews_superseded')
            AND NOT EXISTS (
                SELECT 1
                FROM (VALUES
                    ('id', 'character varying', 'varchar', 'NO'),
                    ('job_id', 'character varying', 'varchar', 'NO'),
                    ('reviewer_id', 'character varying', 'varchar', 'NO'),
                    ('decision', 'USER-DEFINED', 'reviewdecision', 'NO'),
                    ('final_total', 'numeric', 'numeric', 'NO'),
                    ('final_scores_json', 'text', 'text', 'NO'),
                    ('justification', 'text', 'text', 'YES'),
                    ('created_at', 'timestamp without time zone', 'timestamp', 'NO'),
                    ('superseded_reason', 'text', 'text', 'NO'),
                    ('superseded_at', 'timestamp without time zone', 'timestamp', 'NO')
                ) AS expected(column_name, data_type, udt_name, is_nullable)
                LEFT JOIN information_schema.columns actual
                  ON actual.table_schema = 'public'
                 AND actual.table_name = 'human_reviews_superseded'
                 AND actual.column_name = expected.column_name
                 AND actual.data_type = expected.data_type
                 AND actual.udt_name = expected.udt_name
                 AND actual.is_nullable = expected.is_nullable
                WHERE actual.column_name IS NULL
            )
            AND EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'human_reviews_superseded'
                  AND column_name = 'final_total'
                  AND numeric_precision = 6
                  AND numeric_scale = 2
            )
            AND EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'human_reviews_superseded'
                  AND column_name = 'superseded_at'
                  AND column_default = 'now()'
            )
            AND EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attname = 'id'
                WHERE n.nspname = 'public'
                  AND t.relname = 'human_reviews_superseded'
                  AND c.contype = 'p'
                  AND c.conkey = ARRAY[a.attnum]::smallint[]
            )
            AND NOT EXISTS (
                SELECT 1
                FROM pg_index i
                JOIN pg_class t ON t.oid = i.indrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attname = 'job_id'
                WHERE n.nspname = 'public'
                  AND t.relname = 'human_reviews_superseded'
                  AND i.indisunique
                  AND i.indnkeyatts = 1
                  AND i.indexprs IS NULL
                  AND i.indpred IS NULL
                  AND i.indkey::text = a.attnum::text
            )
            AND EXISTS (
                SELECT 1
                FROM pg_index i
                JOIN pg_class t ON t.oid = i.indrelid
                JOIN pg_class idx ON idx.oid = i.indexrelid
                JOIN pg_am am ON am.oid = idx.relam
                JOIN pg_namespace n ON n.oid = t.relnamespace
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attname = 'job_id'
                WHERE n.nspname = 'public'
                  AND t.relname = 'human_reviews_superseded'
                  AND idx.relname = 'ix_human_reviews_superseded_job_id'
                  AND am.amname = 'btree'
                  AND NOT i.indisunique
                  AND i.indisvalid
                  AND i.indisready
                  AND i.indnkeyatts = 1
                  AND i.indexprs IS NULL
                  AND i.indpred IS NULL
                  AND i.indkey::text = a.attnum::text
            )
        INTO v_schema_ok;

        IF NOT v_schema_ok THEN
            RAISE EXCEPTION 'human_reviews_superseded já existe com schema incompatível (colunas/tipos/nulabilidade/default/PK/índice ou unicidade em job_id divergentes) — abortando antes de qualquer escrita';
        END IF;
    END IF;
END $$;
```

### 7.3 Saneamento (por grupo equivalente confirmado), com assertions executáveis

Abre uma transação explícita, que só é confirmada ao final da seção 7.4 (após todos os
pós-checks). O `LOCK TABLE` abaixo dura exatamente entre este `BEGIN` e o `COMMIT` da seção 7.4.

```sql
BEGIN;

-- Impede INSERT/UPDATE/DELETE concorrentes ATÉ O COMMIT desta transação
-- (o lock é liberado no COMMIT — ver seção 6, item 2).
LOCK TABLE human_reviews IN SHARE ROW EXCLUSIVE MODE;

-- Assertion executável: reconfirma, sob lock, que o único grupo duplicado
-- continua sendo exatamente o esperado, com os 3 IDs inventariados.
DO $$
DECLARE
    v_count int;
    v_ids text[];
    v_distinct_reviewers int;
    v_distinct_decisions int;
    v_distinct_totals int;
    v_distinct_scores int;
    v_distinct_justifications int;
BEGIN
    SELECT COUNT(*), array_agg(id::text ORDER BY id::text)
    INTO v_count, v_ids
    FROM human_reviews
    WHERE job_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0';

    IF v_count != 3 THEN
        RAISE EXCEPTION 'Esperado 3 linhas para job 4f56a10b-..., encontrado %; abortando', v_count;
    END IF;

    IF v_ids != ARRAY[
        '31d31b5c-05c7-4206-b2ff-43b2eda14026',
        '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
        '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
    ]::text[] THEN
        RAISE EXCEPTION 'IDs encontrados (%) não correspondem ao inventário esperado; abortando', v_ids;
    END IF;

    WITH normalized AS (
        SELECT reviewer_id, decision, final_total,
               COALESCE(justification, '') AS justification_norm,
               COALESCE((
                   SELECT jsonb_agg(
                       jsonb_build_object(
                           'criterion_id', elem->>'criterion_id',
                           'score', to_char((elem->>'score')::numeric, 'FM999999990.00')
                       ) ORDER BY elem->>'criterion_id'
                   )
                   FROM jsonb_array_elements(final_scores_json::jsonb) AS elem
               ), '[]'::jsonb) AS scores_norm
        FROM human_reviews
        WHERE job_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0'
    )
    SELECT COUNT(DISTINCT reviewer_id), COUNT(DISTINCT decision),
           COUNT(DISTINCT final_total), COUNT(DISTINCT scores_norm),
           COUNT(DISTINCT justification_norm)
    INTO v_distinct_reviewers, v_distinct_decisions, v_distinct_totals,
         v_distinct_scores, v_distinct_justifications
    FROM normalized;

    IF v_distinct_reviewers != 1 OR v_distinct_decisions != 1
       OR v_distinct_totals != 1 OR v_distinct_scores != 1
       OR v_distinct_justifications != 1 THEN
        RAISE EXCEPTION 'Grupo deixou de ser equivalente sob lock (reviewer %, decision %, total %, scores %, justification %); abortando — decisão manual necessária',
            v_distinct_reviewers, v_distinct_decisions, v_distinct_totals,
            v_distinct_scores, v_distinct_justifications;
    END IF;
END $$;

-- Copia as 2 linhas não-vencedoras para o arquivo, com colunas explícitas.
INSERT INTO human_reviews_superseded (
    id, job_id, reviewer_id, decision, final_total, final_scores_json,
    justification, created_at, superseded_reason, superseded_at
)
SELECT
    id, job_id, reviewer_id, decision, final_total, final_scores_json,
    justification, created_at,
    'duplicate-equivalent-review-pre-BL-AV-1-10', now()
FROM human_reviews
WHERE id IN (
    '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
    '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
);

-- Assertion executável: compara INTEGRALMENTE (todas as colunas de dado, não
-- apenas contagem) a cópia recém-inserida contra o original AINDA presente
-- em human_reviews, ANTES de remover da tabela ativa.
DO $$
DECLARE
    v_mismatches int;
BEGIN
    SELECT COUNT(*) INTO v_mismatches
    FROM human_reviews hr
    JOIN human_reviews_superseded s ON s.id = hr.id
    WHERE hr.id IN ('8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c', '9459489c-dd8e-4f33-936a-bc76cb7d5f0b')
      AND (
          hr.job_id IS DISTINCT FROM s.job_id OR
          hr.reviewer_id IS DISTINCT FROM s.reviewer_id OR
          hr.decision IS DISTINCT FROM s.decision OR
          hr.final_total IS DISTINCT FROM s.final_total OR
          hr.final_scores_json IS DISTINCT FROM s.final_scores_json OR
          hr.justification IS DISTINCT FROM s.justification OR
          hr.created_at IS DISTINCT FROM s.created_at
      );

    IF v_mismatches != 0 THEN
        RAISE EXCEPTION 'Cópia arquivada difere do original em % linha(s); abortando antes do DELETE', v_mismatches;
    END IF;

    IF (SELECT COUNT(*) FROM human_reviews_superseded
        WHERE id IN ('8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c', '9459489c-dd8e-4f33-936a-bc76cb7d5f0b')) != 2 THEN
        RAISE EXCEPTION 'Cópia no arquivo não contém exatamente as 2 linhas esperadas; abortando';
    END IF;
END $$;

-- Só agora, com a cópia confirmada IDÊNTICA ao original, remove da tabela ativa.
DELETE FROM human_reviews
WHERE id IN (
    '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
    '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
);

DO $$
DECLARE
    v_remaining int;
BEGIN
    SELECT COUNT(*) INTO v_remaining
    FROM human_reviews
    WHERE id IN ('8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c', '9459489c-dd8e-4f33-936a-bc76cb7d5f0b');

    IF v_remaining != 0 THEN
        RAISE EXCEPTION 'DELETE não removeu as 2 linhas esperadas da tabela ativa; abortando';
    END IF;
END $$;
```
(sem `COMMIT` aqui — a transação aberta pelo `BEGIN` desta seção continua aberta; o `COMMIT` fica
ao final da seção 7.4, depois dos pós-checks)

### 7.4 Verificações pós-saneamento executáveis (dentro da mesma transação, antes do `COMMIT`)

```sql
DO $$
DECLARE
    v_dup_count int;
    v_winner_count int;
    v_archived_count int;
    v_audit_count int;
BEGIN
    -- (a) Nenhum grupo duplicado deve restar
    SELECT COUNT(*) INTO v_dup_count FROM (
        SELECT job_id FROM human_reviews GROUP BY job_id HAVING COUNT(*) > 1
    ) t;
    IF v_dup_count != 0 THEN
        RAISE EXCEPTION 'Pós-check (a) falhou: ainda há % grupo(s) duplicado(s)', v_dup_count;
    END IF;

    -- (b) A linha vencedora ainda existe com TODOS os campos relevantes intactos
    SELECT COUNT(*) INTO v_winner_count
    FROM human_reviews
    WHERE id = '31d31b5c-05c7-4206-b2ff-43b2eda14026'
      AND job_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0'
      AND reviewer_id = 'cabba145-18bc-40a1-9faa-489f4bfda018'
      AND decision = 'APPROVE'
      AND final_total = 2.00
      AND final_scores_json::jsonb = '[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb
      AND COALESCE(justification, '') = ''
      AND created_at = TIMESTAMP '2026-09-23 22:53:35.110755';
    IF v_winner_count != 1 THEN
        RAISE EXCEPTION 'Pós-check (b) falhou: linha vencedora ausente ou algum campo foi alterado';
    END IF;

    -- (c) As 2 linhas movidas estão preservadas no arquivo, com o motivo registrado
    SELECT COUNT(*) INTO v_archived_count
    FROM human_reviews_superseded
    WHERE job_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0'
      AND superseded_reason = 'duplicate-equivalent-review-pre-BL-AV-1-10';
    IF v_archived_count != 2 THEN
        RAISE EXCEPTION 'Pós-check (c) falhou: esperado 2 linhas arquivadas, encontrado %', v_archived_count;
    END IF;

    -- (d) Nenhum AuditEvent foi tocado: validação nominal dos 3 IDs
    SELECT COUNT(*) INTO v_audit_count
    FROM audit_events
    WHERE id IN (
        'b12db6d4-3b44-42ca-aa9a-99748fc4b982',
        '4f737eab-3ba0-40af-8738-ae847377ba34',
        'cad4d910-8c91-4a7e-9714-266fac3f7ee6'
    )
    AND resource_type = 'CorrectionJob' AND action = 'REVIEW_APPROVE'
    AND resource_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0';
    IF v_audit_count != 3 THEN
        RAISE EXCEPTION 'Pós-check (d) falhou: eventos de auditoria alterados ou ausentes (encontrado %)', v_audit_count;
    END IF;
END $$;

-- Todos os pós-checks passaram sem RAISE EXCEPTION: confirma a transação.
-- Este COMMIT libera o LOCK TABLE adquirido no início da seção 7.3.
COMMIT;
```

A migração `7b1d6d853f20` deve ser aplicada em seguida (passo separado, `alembic upgrade head`),
enquanto os writers permanecem parados — o `LOCK TABLE` já foi liberado pelo `COMMIT` acima; a
proteção contra concorrência nesse intervalo é a continuidade dos writers parados (seção 6,
item 4), não o lock. Se a migração falhar, não liberar writers — seguir o plano de recuperação da
seção 7.5.

Verificação (e) — contexto da aplicação — é executada separadamente, fora da transação SQL, via
chamada HTTP real após o `COMMIT` e a aplicação da migração: `GET
/v1/correction-jobs/4f56a10b-3a44-4df5-9047-adef7546a3c0/context` deve continuar retornando
`human_review` com os dados da linha vencedora.

### 7.5 Plano de recuperação

**Cenário A — falha antes do `COMMIT`:** executar `ROLLBACK`; como mover e remover estão na mesma
transação, `human_reviews` e `human_reviews_superseded` retornam ao estado anterior.

**Cenário B — problema detectado depois do `COMMIT`, antes da migração:** recuperação
compensatória é preferível a restore completo (menor blast radius). Com writers ainda parados:

```sql
BEGIN;
LOCK TABLE human_reviews IN SHARE ROW EXCLUSIVE MODE;

INSERT INTO human_reviews (
    id, job_id, reviewer_id, decision, final_total, final_scores_json,
    justification, created_at
)
SELECT id, job_id, reviewer_id, decision, final_total, final_scores_json,
       justification, created_at
FROM human_reviews_superseded
WHERE id IN (
    '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
    '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
);

DO $$
DECLARE
    v_active_count integer;
    v_archive_count integer;
    v_mismatch_count integer;
BEGIN
    SELECT COUNT(*) INTO v_active_count
    FROM human_reviews
    WHERE id IN (
        '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
        '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
    );

    SELECT COUNT(*) INTO v_archive_count
    FROM human_reviews_superseded
    WHERE id IN (
        '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
        '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
    );

    SELECT COUNT(*) INTO v_mismatch_count
    FROM human_reviews active
    JOIN human_reviews_superseded archived USING (id)
    WHERE active.id IN (
        '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
        '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
    )
      AND (
          active.job_id IS DISTINCT FROM archived.job_id
          OR active.reviewer_id IS DISTINCT FROM archived.reviewer_id
          OR active.decision IS DISTINCT FROM archived.decision
          OR active.final_total IS DISTINCT FROM archived.final_total
          OR active.final_scores_json IS DISTINCT FROM archived.final_scores_json
          OR active.justification IS DISTINCT FROM archived.justification
          OR active.created_at IS DISTINCT FROM archived.created_at
      );

    IF v_active_count <> 2 OR v_archive_count <> 2 OR v_mismatch_count <> 0 THEN
        RAISE EXCEPTION 'Rollback compensatório incompleto antes de limpar o arquivo (ativas %, arquivadas %, divergentes %); abortando',
            v_active_count, v_archive_count, v_mismatch_count;
    END IF;
END $$;

DO $$
DECLARE
    v_deleted integer;
    v_active_count integer;
    v_archive_count integer;
BEGIN
    DELETE FROM human_reviews_superseded
    WHERE id IN (
        '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
        '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
    );
    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    SELECT COUNT(*) INTO v_active_count
    FROM human_reviews
    WHERE id IN (
        '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
        '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
    );

    SELECT COUNT(*) INTO v_archive_count
    FROM human_reviews_superseded
    WHERE id IN (
        '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
        '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
    );

    IF v_deleted <> 2 OR v_active_count <> 2 OR v_archive_count <> 0 THEN
        RAISE EXCEPTION 'Rollback compensatório falhou ao limpar o arquivo (removidas %, ativas %, arquivadas %); abortando',
            v_deleted, v_active_count, v_archive_count;
    END IF;
END $$;

COMMIT;
```

**Cenário C — problema depois da aplicação da constraint:** primeiro fazer `alembic downgrade
e1b02279b1a5` (com writers parados), confirmar que a constraint foi removida, e então executar o
rollback compensatório acima. Qualquer divergência impede liberar writers.

**Restore completo — último recurso, nunca sobre banco ativo:**
1. validar SHA-256 do `.dump` contra checksum registrado no momento do backup;
2. confirmar que não houve escrita posterior ao backup (writers permaneceram parados durante toda
   a janela); se houve, restore completo descartaria dados e exige plano de reconciliação/decisão
   de incidente por Rafael;
3. restaurar primeiro em banco vazio isolado: `createdb ...` + `pg_restore --exit-on-error -d
   <banco_vazio> <dump>`; validar contagens, FKs e o grupo duplicado;
4. só restaurar `avalia_dev` mediante nova autorização explícita, com conexões bloqueadas e banco
   destino recriado/vazio (não usar restore sobre tabelas existentes sem `--clean`/recriação
   planejada);
5. registrar comandos/saídas exatas em snapshot de incidente.

Se a aplicação ficar indisponível além da janela, não liberar writers até a integridade ser
confirmada. Toda execução real gera snapshot próprio; nenhuma verificação é presumida.

## 8. Aplicação da migração `7b1d6d853f20` após o saneamento

Só depois que a seção 7.4(a) confirmar 0 grupos duplicados:

```
cd core
DATABASE_URL="<URL real de avalia_dev>" alembic upgrade head
```

A migração, já validada em SQLite e PostgreSQL isolado (ver `docs/governance/evidence/AV-S02-postgres-isolado/`), deve completar sem erro e criar a `UniqueConstraint uq_human_reviews_job_id`. Verificação pós-migração: `\d human_reviews` deve listar essa constraint.

## 9. O que este documento NÃO decide nem executa

- Não decide a regra de vencedor para um grupo **conflitante** — isso é decisão de produto de Rafael, caso a caso (nenhum caso conflitante existe hoje, mas o script de diagnóstico da seção 7.1 detectaria se existisse).
- Não decide a retenção/expurgo futuro de `human_reviews_superseded`.
- **Não executa nada.** Backup, saneamento e migração em `avalia_dev` permanecem bloqueados até autorização explícita e específica de Rafael — inclusive a validação em ambiente isolado (seção 5.3) só deve ser executada após aprovação deste plano, não antes.

