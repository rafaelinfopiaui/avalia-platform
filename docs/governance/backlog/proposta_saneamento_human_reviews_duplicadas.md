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

| id | actor_id | action | created_at |
|---|---|---|---|
| `b12db6d4-3b44-42ca-aa9a-99748fc4b982` | `cabba145-18bc-40a1-9faa-489f4bfda018` | REVIEW_APPROVE | 2026-09-23 22:53:35.114334 |
| `4f737eab-3ba0-40af-8738-ae847377ba34` | `cabba145-18bc-40a1-9faa-489f4bfda018` | REVIEW_APPROVE | 2026-09-23 22:55:15.907615 |
| `cad4d910-8c91-4a7e-9714-266fac3f7ee6` | `cabba145-18bc-40a1-9faa-489f4bfda018` | REVIEW_APPROVE | 2026-09-23 22:58:47.636134 |

O procedimento de aprovação deve registrar também `before_json` e `after_json` desses 3 eventos no relatório pré-operação. Mesmo com a correlação forte acima, não alegamos FK inexistente: a associação continua lógica/temporal. Total afetado pela preservação: **3 linhas em `human_reviews` + 3 linhas em `audit_events`**, todas relativas ao mesmo job; apenas as 2 revisões equivalentes excedentes serão movidas, e nenhum evento de auditoria será tocado.

## 2. Confirmação de equivalência considerando todos os campos relevantes

Campos comparados nas 3 linhas: `job_id`, `reviewer_id`, `decision`, `final_total`, `final_scores_json` (comparação textual completa, não apenas por amostragem), `justification`. **Todos idênticos**, exceto `id` (chave primária, esperado ser distinto) e `created_at` (timestamp de cada reenvio, esperado ser distinto).

Isso corresponde exatamente ao critério de equivalência já implementado em `core/app/main.py::_review_is_equivalent` (mesmo `reviewer_id`, `decision`, `final_scores` normalizados, `justification` normalizada None/""). As 3 linhas são o **mesmo ato de decisão humana**, registrado 3 vezes pela ausência histórica de idempotência (antes da correção de `BL-AV-1-10`) — não há divergência de nota, decisão ou revisor. **Não há caso conflitante nesta base hoje.**

## 3. Regra proposta para selecionar a revisão ativa

Como as 3 linhas são equivalentes (não conflitantes), a escolha de qual linha permanece como "ativa" em `human_reviews` é neutra em conteúdo — qualquer uma delas expressa a mesma decisão. A regra proposta, para ter um critério objetivo e auditável:

> **Manter a linha de menor `created_at`** (a primeira decisão registrada, `31d31b5c-...`, 2026-09-23 22:53:35), por ser a que primeiro teria sido aceita caso a idempotência já existisse na época.

Esta regra só é segura porque o caso real é equivalente. **Se algum grupo futuro (nesta base ou em outra) for classificado como conflitante** (decisões realmente diferentes), esta regra automática **não se aplica** — a escolha da linha vencedora nesse caso exige decisão explícita de Rafael, registrada nominalmente, não uma regra automática por data. Nenhum caso conflitante existe hoje, mas o script de diagnóstico (seção 6) verifica isso antes de qualquer escrita e interrompe se encontrar um.

## 4. Preservação das demais revisões e referências de auditoria

Nenhuma linha é apagada (`DELETE`) em nenhum momento. Proposta:

- Criar tabela de arquivo `human_reviews_superseded`, com a mesma estrutura de `human_reviews` mais duas colunas: `superseded_reason` (texto, ex.: `"duplicate-equivalent-review-pre-BL-AV-1-10"`) e `superseded_at` (timestamp da operação de saneamento).
- Mover (não copiar e apagar — mover atomicamente dentro de uma transação: `INSERT INTO human_reviews_superseded SELECT ..., 'motivo', now() FROM human_reviews WHERE id IN (...)` seguido de `DELETE FROM human_reviews WHERE id IN (...)`, ambos na mesma transação) as 2 linhas não-vencedoras (`8a9c2ba6-...` e `9459489c-...`) para essa tabela de arquivo.
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
2. Dentro da transação, adquirir `LOCK TABLE human_reviews IN SHARE ROW EXCLUSIVE MODE;`, que conflita com `INSERT`/`UPDATE`/`DELETE` concorrentes (ao contrário de `SELECT ... FOR UPDATE`, que bloqueia apenas as linhas já encontradas e **não** impediria um novo INSERT para o mesmo `job_id`).
3. Após adquirir o lock de tabela, repetir o diagnóstico completo de equivalência e as assertions nominais dos IDs/conteúdos esperados; só então mover as linhas.
4. Manter a aplicação e todos os writers parados desde antes do backup final até o `COMMIT`, pós-checks, aplicação da `UniqueConstraint` e verificação da constraint — não liberar escrita no intervalo entre saneamento e migração.
5. Após a constraint existir e os pós-checks passarem, liberar a aplicação para escrita. A proteção aplicativa integrada em `main` é uma camada adicional, mas não substitui o lock/maintenance window deste procedimento.

## 7. Comandos, verificações posteriores e plano de recuperação

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
**conflitante** — a operação para e Rafael decide manualmente antes de qualquer escrita.

**Assertions nominais obrigatórias imediatamente antes da escrita (já sob lock de tabela):**
- o único grupo duplicado continua sendo `4f56a10b-...`;
- contém exatamente os três IDs inventariados na seção 1;
- a linha ativa candidata `31d31b5c-...` mantém todos os campos esperados;
- as outras duas linhas são semanticamente equivalentes (`distinct_* = 1` em todas as dimensões).
Qualquer desvio aborta a transação.

### 7.2 Tabela de arquivo (DDL explícito, versionado e executado antes da migração de unicidade)

Não usar `CREATE TABLE ... LIKE INCLUDING ALL`: após a migração, isso poderia copiar por engano a
unicidade de `job_id` para a tabela de arquivo. Também **não** criar uma migration Alembic
descendente de `7b1d6d853f20`: ela não poderia rodar antes do saneamento que permite a própria
`7b1d6d853f20`.

**Sequência proposta, objetiva:** após aprovação deste plano, criar em branch/PR um script SQL
versionado separado (proposta de caminho: `core/scripts/av_s02_saneamento_human_reviews.sql`) que
contém, na ordem: `BEGIN`, lock de tabela, diagnóstico/assertions, DDL abaixo, INSERT/DELETE,
pós-checks e `COMMIT`. O script é revisado/testado no banco restaurado isolado antes de qualquer
uso em `avalia_dev`. Assim a criação da tabela acontece **na mesma transação e imediatamente antes
do INSERT**, sem depender da cadeia Alembic. A migração `7b1d6d853f20` só é executada depois do
`COMMIT` desse script, ainda com writers parados.

DDL explícito, sem FK/unique que impeça preservar o histórico:

```sql
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
```

Se a tabela já existir, o script **não** deve seguir silenciosamente: consultar `information_schema`
e `pg_catalog` e comparar colunas, tipos, PK, índices e ausência de unicidade em `job_id`; qualquer
divergência executa `ROLLBACK` antes de mover dados. O arquivo SQL versionado e sua revisão no PR
fornecem a rastreabilidade; não há schema drift ad-hoc fora do controle de versão.

### 7.3 Saneamento transacional (por grupo equivalente confirmado)

```sql
BEGIN;

-- Impede INSERT/UPDATE/DELETE concorrentes durante diagnóstico+saneamento+migração.
LOCK TABLE human_reviews IN SHARE ROW EXCLUSIVE MODE;

-- Repetir agora, sob lock, o diagnóstico completo e as assertions da seção 7.1.
-- Qualquer divergência -> ROLLBACK imediato.

-- Move as 2 linhas não-vencedoras para o arquivo, com colunas explícitas.
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
)
RETURNING id;
-- Assertion obrigatória: exatamente estes 2 IDs retornados. Caso contrário: ROLLBACK.

DELETE FROM human_reviews
WHERE id IN (
    '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
    '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
)
RETURNING id;
-- Assertion obrigatória: exatamente os mesmos 2 IDs retornados. Caso contrário: ROLLBACK.

-- Rodar os pós-checks 7.4(a-d) AINDA DENTRO desta transação.
-- Só COMMIT se todos retornarem os valores esperados.
COMMIT;
```

A migração `7b1d6d853f20` deve ser aplicada enquanto a aplicação/writers permanecem parados,
imediatamente após este `COMMIT`; se ela falhar, não liberar writers — seguir o plano de
recuperação da seção 7.5.

### 7.4 Verificações pós-saneamento (antes de considerar a operação concluída)

```sql
-- (a) Nenhum grupo duplicado deve restar
SELECT job_id, COUNT(*) FROM human_reviews GROUP BY job_id HAVING COUNT(*) > 1;
-- esperado: 0 linhas

-- (b) A linha vencedora ainda existe, com o conteúdo original
SELECT * FROM human_reviews WHERE id = '31d31b5c-05c7-4206-b2ff-43b2eda14026';
-- esperado: 1 linha, dados idênticos aos do inventário original (seção 1)

-- (c) As 2 linhas movidas estão preservadas no arquivo, com o motivo registrado
SELECT id, job_id, superseded_reason, superseded_at FROM human_reviews_superseded
WHERE job_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0';
-- esperado: 2 linhas (8a9c2ba6-... e 9459489c-...)

-- (d) Nenhum AuditEvent foi tocado: validar nominalmente os 3 IDs e conteúdos-chave,
-- não apenas uma contagem ampla por resource_id.
SELECT id, actor_id, action, resource_type, resource_id,
       before_json, after_json, created_at
FROM audit_events
WHERE id IN (
    'b12db6d4-3b44-42ca-aa9a-99748fc4b982',
    '4f737eab-3ba0-40af-8738-ae847377ba34',
    'cad4d910-8c91-4a7e-9714-266fac3f7ee6'
)
ORDER BY created_at;
-- esperado: exatamente esses 3 IDs, mesmo actor_id, REVIEW_APPROVE,
-- resource_type=CorrectionJob, resource_id=4f56a10b-..., e before_json/after_json
-- idênticos ao relatório pré-operação da seção 1.

-- (e) Contexto da aplicação continua funcional para este job
-- (verificação via API real: GET /v1/correction-jobs/4f56a10b-3a44-4df5-9047-adef7546a3c0/context
--  deve continuar retornando human_review com os dados da linha vencedora)
```

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
)
RETURNING id;
-- esperado: 2 IDs exatos

DELETE FROM human_reviews_superseded
WHERE id IN (
    '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
    '9459489c-dd8e-4f33-936a-bc76cb7d5f0b'
)
RETURNING id;
-- esperado: os mesmos 2 IDs
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
