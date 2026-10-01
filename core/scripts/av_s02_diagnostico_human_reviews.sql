-- Diagnóstico SOMENTE LEITURA das duplicatas em human_reviews.
-- Executável contra avalia_dev sem risco de escrita:
--   psql -v ON_ERROR_STOP=1 -f av_s02_diagnostico_human_reviews.sql avalia_dev
-- Retorna todos os grupos duplicados e suas dimensões de equivalência.
-- Qualquer distinct_* > 1 classifica o grupo como CONFLITANTE; nesse caso
-- av_s02_saneamento_human_reviews.sql deve abortar e nenhuma escolha
-- automática de vencedor é permitida.

\set ON_ERROR_STOP on
SET search_path = public, pg_catalog;

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
               FROM jsonb_array_elements(hr.final_scores_json::jsonb) AS elem
           ), '[]'::jsonb) AS scores_norm
    FROM public.human_reviews hr
), duplicate_groups AS (
    SELECT job_id,
           COUNT(*) AS review_count,
           COUNT(DISTINCT reviewer_id) AS distinct_reviewers,
           COUNT(DISTINCT decision) AS distinct_decisions,
           COUNT(DISTINCT final_total) AS distinct_totals,
           COUNT(DISTINCT scores_norm) AS distinct_scores,
           COUNT(DISTINCT justification_norm) AS distinct_justifications,
           array_agg(id::text ORDER BY created_at, id) AS ordered_ids
    FROM normalized
    GROUP BY job_id
    HAVING COUNT(*) > 1
)
SELECT *,
       CASE WHEN distinct_reviewers = 1
                  AND distinct_decisions = 1
                  AND distinct_totals = 1
                  AND distinct_scores = 1
                  AND distinct_justifications = 1
            THEN 'EQUIVALENT'
            ELSE 'CONFLICTING — ABORT, NO AUTOMATIC SANITATION'
       END AS classification
FROM duplicate_groups
ORDER BY job_id;

-- Detalhe integral das linhas do grupo nominal conhecido.
SELECT id, job_id, reviewer_id, decision, final_total,
       final_scores_json, justification, created_at
FROM public.human_reviews
WHERE job_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0'
ORDER BY created_at, id;

-- Eventos de auditoria correlacionados — associação lógica/temporal,
-- não FK. A operação de saneamento não toca estas linhas.
SELECT id, actor_id, action, resource_type, resource_id,
       before_json, after_json, created_at
FROM public.audit_events
WHERE resource_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0'
  AND resource_type = 'CorrectionJob'
  AND action = 'REVIEW_APPROVE'
  AND actor_id = 'cabba145-18bc-40a1-9faa-489f4bfda018'
  AND created_at BETWEEN '2026-09-23 22:53:00' AND '2026-09-23 22:59:30'
ORDER BY created_at, id;
