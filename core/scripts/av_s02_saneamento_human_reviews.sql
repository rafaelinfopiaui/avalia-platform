-- ============================================================================
-- av_s02_saneamento_human_reviews.sql
-- Saneamento fail-closed do único grupo de HumanReview duplicadas conhecido.
-- Base: proposta local de 676 linhas (commit aa8031a), incorporando as 9
-- melhorias GOV-006 e os bloqueadores da revisão independente desta rodada.
--
-- Execução isolada:
--   psql -v ON_ERROR_STOP=1 -f av_s02_saneamento_human_reviews.sql <URL>
-- Execução futura contra avalia_dev (AINDA NÃO AUTORIZADA) exige também:
--   PGOPTIONS='-c avalia.allow_sanitation=AV_S02_SANITATION_20261001'
--
-- Não usar --single-transaction: este arquivo controla BEGIN/COMMIT.
-- ============================================================================
\set ON_ERROR_STOP on
SET search_path = public, pg_catalog;

-- Guard em duas camadas: nome ancorado para isolados; avalia_dev exige
-- opt-in de sessão exato, além da futura autorização operacional externa.
DO $$
DECLARE
    v_dbname text := current_database();
    v_opt_in text := current_setting('avalia.allow_sanitation', true);
BEGIN
    IF v_dbname ~ '^av_s02_saneamento_[A-Za-z0-9_-]+$' THEN
        RAISE NOTICE 'Guard isolado OK: %', v_dbname;
    ELSIF v_dbname = 'avalia_dev'
          AND v_opt_in = 'AV_S02_SANITATION_20261001' THEN
        RAISE NOTICE 'Guard avalia_dev + opt-in explícito OK';
    ELSE
        RAISE EXCEPTION 'Guard recusou banco % (opt-in=%)', v_dbname, COALESCE(v_opt_in, '<null>');
    END IF;
END $$;

-- Diagnóstico textual pré-transação (somente leitura).
WITH normalized AS (
    SELECT hr.*,
           COALESCE(hr.justification, '') AS justification_norm,
           COALESCE((
               SELECT jsonb_agg(
                   jsonb_build_object(
                       'criterion_id', elem->>'criterion_id',
                       'score', (elem->>'score')::numeric
                   ) ORDER BY elem->>'criterion_id'
               )
               FROM jsonb_array_elements(hr.final_scores_json::jsonb) elem
           ), '[]'::jsonb) AS scores_norm
    FROM public.human_reviews hr
), duplicate_groups AS (
    SELECT job_id, COUNT(*) review_count,
           COUNT(DISTINCT reviewer_id) distinct_reviewers,
           COUNT(DISTINCT decision) distinct_decisions,
           COUNT(DISTINCT final_total) distinct_totals,
           COUNT(DISTINCT scores_norm) distinct_scores,
           COUNT(DISTINCT justification_norm) distinct_justifications
    FROM normalized GROUP BY job_id HAVING COUNT(*) > 1
)
SELECT * FROM duplicate_groups ORDER BY job_id;

BEGIN;
SET LOCAL search_path = public, pg_catalog;

-- DDL faz parte da MESMA transação do saneamento. Se qualquer assertion
-- falhar, a criação da tabela/índice também sofre rollback: sem drift residual.
DO $$
DECLARE
    v_table_exists boolean;
    v_schema_ok boolean;
BEGIN
    SELECT to_regclass('public.human_reviews_superseded') IS NOT NULL INTO v_table_exists;
    IF NOT v_table_exists THEN
        CREATE TABLE public.human_reviews_superseded (
            id VARCHAR PRIMARY KEY,
            job_id VARCHAR NOT NULL,
            reviewer_id VARCHAR NOT NULL,
            decision public.reviewdecision NOT NULL,
            final_total NUMERIC(6,2) NOT NULL,
            final_scores_json TEXT NOT NULL,
            justification TEXT,
            created_at TIMESTAMP NOT NULL,
            superseded_reason TEXT NOT NULL,
            superseded_at TIMESTAMP NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_human_reviews_superseded_job_id
            ON public.human_reviews_superseded(job_id);
    ELSE
        SELECT
            (SELECT COUNT(*) = 10 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='human_reviews_superseded')
            AND NOT EXISTS (
                SELECT 1 FROM (VALUES
                    ('id','character varying','varchar','NO'),
                    ('job_id','character varying','varchar','NO'),
                    ('reviewer_id','character varying','varchar','NO'),
                    ('decision','USER-DEFINED','reviewdecision','NO'),
                    ('final_total','numeric','numeric','NO'),
                    ('final_scores_json','text','text','NO'),
                    ('justification','text','text','YES'),
                    ('created_at','timestamp without time zone','timestamp','NO'),
                    ('superseded_reason','text','text','NO'),
                    ('superseded_at','timestamp without time zone','timestamp','NO')
                ) expected(column_name,data_type,udt_name,is_nullable)
                LEFT JOIN information_schema.columns actual
                  ON actual.table_schema='public'
                 AND actual.table_name='human_reviews_superseded'
                 AND actual.column_name=expected.column_name
                 AND actual.data_type=expected.data_type
                 AND actual.udt_name=expected.udt_name
                 AND actual.is_nullable=expected.is_nullable
                WHERE actual.column_name IS NULL)
            AND EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='public' AND table_name='human_reviews_superseded'
                  AND column_name='final_total' AND numeric_precision=6 AND numeric_scale=2)
            AND EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='public' AND table_name='human_reviews_superseded'
                  AND column_name='superseded_at' AND column_default='now()')
            AND EXISTS (
                SELECT 1 FROM pg_constraint c
                JOIN pg_class t ON t.oid=c.conrelid
                JOIN pg_namespace n ON n.oid=t.relnamespace
                JOIN pg_attribute a ON a.attrelid=t.oid AND a.attname='id'
                WHERE n.nspname='public' AND t.relname='human_reviews_superseded'
                  AND c.contype='p' AND c.conkey=ARRAY[a.attnum]::smallint[])
            AND NOT EXISTS (
                SELECT 1 FROM pg_index i
                JOIN pg_class t ON t.oid=i.indrelid
                JOIN pg_namespace n ON n.oid=t.relnamespace
                JOIN pg_attribute a ON a.attrelid=t.oid AND a.attname='job_id'
                WHERE n.nspname='public' AND t.relname='human_reviews_superseded'
                  AND i.indisunique AND i.indnkeyatts=1
                  AND i.indexprs IS NULL AND i.indpred IS NULL
                  AND i.indkey::text=a.attnum::text)
            AND EXISTS (
                SELECT 1 FROM pg_index i
                JOIN pg_class t ON t.oid=i.indrelid
                JOIN pg_class idx ON idx.oid=i.indexrelid
                JOIN pg_am am ON am.oid=idx.relam
                JOIN pg_namespace n ON n.oid=t.relnamespace
                JOIN pg_attribute a ON a.attrelid=t.oid AND a.attname='job_id'
                WHERE n.nspname='public' AND t.relname='human_reviews_superseded'
                  AND idx.relname='ix_human_reviews_superseded_job_id'
                  AND am.amname='btree' AND NOT i.indisunique
                  AND i.indisvalid AND i.indisready AND i.indnkeyatts=1
                  AND i.indexprs IS NULL AND i.indpred IS NULL
                  AND i.indkey::text=a.attnum::text)
        INTO v_schema_ok;
        IF NOT v_schema_ok THEN
            RAISE EXCEPTION 'human_reviews_superseded existe com schema incompatível';
        END IF;
    END IF;
END $$;

-- Ordem fixa de locks para evitar deadlocks. SHARE ROW EXCLUSIVE conflita
-- com RowExclusive (INSERT/UPDATE/DELETE) nas três tabelas durante toda a
-- transação. Após COMMIT, a continuidade de writers parados é necessária.
LOCK TABLE public.audit_events IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE public.human_reviews IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE public.human_reviews_superseded IN SHARE ROW EXCLUSIVE MODE;

-- Baseline integral de auditoria: prova que todos os campos esperados estão
-- presentes antes de qualquer DML em human_reviews. AuditEvent não recebe
-- nenhum DML neste script e permanece bloqueada até o pós-check integral.
DO $$
DECLARE v_count int;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM public.audit_events a
    JOIN (VALUES
      ('b12db6d4-3b44-42ca-aa9a-99748fc4b982', TIMESTAMP '2026-09-23 22:53:35.114334'),
      ('4f737eab-3ba0-40af-8738-ae847377ba34', TIMESTAMP '2026-09-23 22:55:15.907615'),
      ('cad4d910-8c91-4a7e-9714-266fac3f7ee6', TIMESTAMP '2026-09-23 22:58:47.636134')
    ) e(id,created_at) ON a.id=e.id
    WHERE a.actor_id='cabba145-18bc-40a1-9faa-489f4bfda018'
      AND a.action='REVIEW_APPROVE' AND a.resource_type='CorrectionJob'
      AND a.resource_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
      AND a.before_json::jsonb='{"53548671-87e7-4784-a7f3-27ce80b66355":"1.00","f99920d8-2368-491c-b82e-f976b6e598c0":"1.00"}'::jsonb
      AND a.after_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb
      AND a.created_at=e.created_at;
    IF v_count <> 3 THEN
        RAISE EXCEPTION 'Baseline integral de audit_events divergente: esperado 3, encontrado %', v_count;
    END IF;
END $$;

-- Máquina de estados idempotente fail-closed.
-- Estado pré: exatamente 3 ativas nominais, 0 arquivadas.
-- Estado pós: exatamente a vencedora ativa, 2 arquivadas nominais, sem duplicata.
SELECT
  (
    (SELECT COUNT(*) FROM public.human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0')=3
    AND (SELECT COUNT(*) FROM public.human_reviews_superseded WHERE id IN
      ('8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b'))=0
  ) AS is_pre,
  (
    (SELECT COUNT(*) FROM public.human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0')=1
    AND EXISTS (SELECT 1 FROM public.human_reviews WHERE id='31d31b5c-05c7-4206-b2ff-43b2eda14026')
    AND (SELECT COUNT(*) FROM public.human_reviews_superseded s JOIN (VALUES
      ('8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',TIMESTAMP '2026-09-23 22:55:15.904278'),
      ('9459489c-dd8e-4f33-936a-bc76cb7d5f0b',TIMESTAMP '2026-09-23 22:58:47.630896'))e(id,ts) ON s.id=e.id
      WHERE s.job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
        AND s.reviewer_id='cabba145-18bc-40a1-9faa-489f4bfda018'
        AND s.decision='APPROVE' AND s.final_total=2.00
        AND s.final_scores_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb
        AND COALESCE(s.justification,'')='' AND s.created_at=e.ts
        AND s.superseded_reason='duplicate-equivalent-review-pre-BL-AV-1-10')=2
    AND (SELECT COUNT(*) FROM public.human_reviews_superseded
      WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0')=2
    AND NOT EXISTS (SELECT 1 FROM public.human_reviews GROUP BY job_id HAVING COUNT(*)>1)
  ) AS is_post
\gset

\if :is_post
  -- Estado pós exato: validações integrais finais ainda ocorrem abaixo? Não:
  -- psql salta diretamente para esta assertion e encerra como no-op.
  DO $$
  DECLARE v_ok int;
  BEGIN
    SELECT COUNT(*) INTO v_ok FROM public.human_reviews
    WHERE id='31d31b5c-05c7-4206-b2ff-43b2eda14026'
      AND job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
      AND reviewer_id='cabba145-18bc-40a1-9faa-489f4bfda018'
      AND decision='APPROVE' AND final_total=2.00
      AND final_scores_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb
      AND COALESCE(justification,'')=''
      AND created_at=TIMESTAMP '2026-09-23 22:53:35.110755';
    IF v_ok<>1 THEN RAISE EXCEPTION 'Estado pós aparente, mas vencedora divergente'; END IF;
  END $$;
  COMMIT;
  \echo SANITATION_ALREADY_COMPLETE_VALID_NOOP
  \quit
\endif

\if :is_pre
  -- segue
\else
  DO $$ BEGIN RAISE EXCEPTION 'Estado parcial/divergente: não é pré nem pós-saneamento exato; nenhuma alternativa automática'; END $$;
\endif

-- Assertions pré-escrita, sob locks.
DO $$
DECLARE
    v_group_count int; v_count int; v_ids text[]; v_earliest text;
    v_duplicate_criteria int;
    v_dr int; v_dd int; v_dt int; v_ds int; v_dj int;
BEGIN
    SELECT COUNT(*) INTO v_group_count FROM (
      SELECT job_id FROM public.human_reviews GROUP BY job_id HAVING COUNT(*)>1
    ) g;
    IF v_group_count<>1 OR NOT EXISTS (
      SELECT 1 FROM public.human_reviews GROUP BY job_id
      HAVING COUNT(*)>1 AND job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
    ) THEN RAISE EXCEPTION 'Conjunto de grupos duplicados não é exatamente o grupo nominal'; END IF;

    SELECT COUNT(*), array_agg(id::text ORDER BY id::text)
      INTO v_count,v_ids FROM public.human_reviews
      WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0';
    IF v_count<>3 OR v_ids<>ARRAY[
      '31d31b5c-05c7-4206-b2ff-43b2eda14026',
      '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',
      '9459489c-dd8e-4f33-936a-bc76cb7d5f0b']::text[]
    THEN RAISE EXCEPTION 'IDs/quantidade divergentes: count %, ids %',v_count,v_ids; END IF;

    SELECT id INTO v_earliest FROM public.human_reviews
      WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
      ORDER BY created_at,id LIMIT 1;
    IF v_earliest<>'31d31b5c-05c7-4206-b2ff-43b2eda14026'
    THEN RAISE EXCEPTION 'Vencedora por menor created_at,id mudou: %',v_earliest; END IF;

    SELECT COUNT(*) INTO v_duplicate_criteria FROM public.human_reviews hr
      WHERE hr.job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
        AND EXISTS (SELECT 1 FROM jsonb_array_elements(hr.final_scores_json::jsonb) e
                    GROUP BY e->>'criterion_id' HAVING COUNT(*)>1);
    IF v_duplicate_criteria<>0 THEN RAISE EXCEPTION 'criterion_id repetido em % revisões',v_duplicate_criteria; END IF;

    WITH normalized AS (
      SELECT reviewer_id,decision,final_total,COALESCE(justification,'') j,
        COALESCE((SELECT jsonb_agg(jsonb_build_object(
          'criterion_id',e->>'criterion_id','score',(e->>'score')::numeric)
          ORDER BY e->>'criterion_id') FROM jsonb_array_elements(final_scores_json::jsonb)e),'[]'::jsonb) s
      FROM public.human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0')
    SELECT COUNT(DISTINCT reviewer_id),COUNT(DISTINCT decision),COUNT(DISTINCT final_total),
           COUNT(DISTINCT s),COUNT(DISTINCT j) INTO v_dr,v_dd,v_dt,v_ds,v_dj FROM normalized;
    IF v_dr<>1 OR v_dd<>1 OR v_dt<>1 OR v_ds<>1 OR v_dj<>1
    THEN RAISE EXCEPTION 'Grupo conflitante (reviewer %,decision %,total %,scores %,justification %); nenhuma alternativa automática',v_dr,v_dd,v_dt,v_ds,v_dj; END IF;
END $$;

-- Arquivamento integral antes da remoção.
INSERT INTO public.human_reviews_superseded(
 id,job_id,reviewer_id,decision,final_total,final_scores_json,justification,created_at,superseded_reason,superseded_at)
SELECT id,job_id,reviewer_id,decision,final_total,final_scores_json,justification,created_at,
 'duplicate-equivalent-review-pre-BL-AV-1-10',now()
FROM public.human_reviews WHERE id IN(
 '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b');

DO $$ DECLARE v_m int; BEGIN
  SELECT COUNT(*) INTO v_m FROM public.human_reviews h
  FULL JOIN public.human_reviews_superseded s USING(id)
  WHERE COALESCE(h.id,s.id) IN('8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b')
    AND (h.id IS NULL OR s.id IS NULL OR h.job_id IS DISTINCT FROM s.job_id
      OR h.reviewer_id IS DISTINCT FROM s.reviewer_id OR h.decision IS DISTINCT FROM s.decision
      OR h.final_total IS DISTINCT FROM s.final_total OR h.final_scores_json IS DISTINCT FROM s.final_scores_json
      OR h.justification IS DISTINCT FROM s.justification OR h.created_at IS DISTINCT FROM s.created_at);
  IF v_m<>0 OR (SELECT COUNT(*) FROM public.human_reviews_superseded WHERE id IN(
    '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b'))<>2
  THEN RAISE EXCEPTION 'Cópia arquivada incompleta/divergente antes do DELETE'; END IF;
END $$;

DELETE FROM public.human_reviews WHERE id IN(
 '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b');

-- Pós-checks integrais ainda sob os três locks.
DO $$ DECLARE v_dup int;v_win int;v_arc int;v_audit int; BEGIN
  SELECT COUNT(*) INTO v_dup FROM(SELECT job_id FROM public.human_reviews GROUP BY job_id HAVING COUNT(*)>1)x;
  SELECT COUNT(*) INTO v_win FROM public.human_reviews WHERE id='31d31b5c-05c7-4206-b2ff-43b2eda14026'
   AND job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
   AND reviewer_id='cabba145-18bc-40a1-9faa-489f4bfda018' AND decision='APPROVE'
   AND final_total=2.00 AND final_scores_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb
   AND COALESCE(justification,'')='' AND created_at=TIMESTAMP '2026-09-23 22:53:35.110755';
  SELECT COUNT(*) INTO v_arc FROM public.human_reviews_superseded WHERE id IN(
   '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b')
   AND superseded_reason='duplicate-equivalent-review-pre-BL-AV-1-10';
  SELECT COUNT(*) INTO v_audit FROM public.audit_events a JOIN(VALUES
   ('b12db6d4-3b44-42ca-aa9a-99748fc4b982',TIMESTAMP '2026-09-23 22:53:35.114334'),
   ('4f737eab-3ba0-40af-8738-ae847377ba34',TIMESTAMP '2026-09-23 22:55:15.907615'),
   ('cad4d910-8c91-4a7e-9714-266fac3f7ee6',TIMESTAMP '2026-09-23 22:58:47.636134'))e(id,ts) ON a.id=e.id
   WHERE a.actor_id='cabba145-18bc-40a1-9faa-489f4bfda018' AND a.action='REVIEW_APPROVE'
   AND a.resource_type='CorrectionJob' AND a.resource_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
   AND a.before_json::jsonb='{"53548671-87e7-4784-a7f3-27ce80b66355":"1.00","f99920d8-2368-491c-b82e-f976b6e598c0":"1.00"}'::jsonb
   AND a.after_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb AND a.created_at=e.ts;
  IF v_dup<>0 OR v_win<>1 OR v_arc<>2 OR v_audit<>3
  THEN RAISE EXCEPTION 'Pós-check falhou dup %,win %,arc %,audit %',v_dup,v_win,v_arc,v_audit; END IF;
END $$;
COMMIT;
\echo SANITATION_APPLIED_GREEN
