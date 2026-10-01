-- Rollback compensatório fail-closed e idempotente do saneamento HumanReview.
-- Uso isolado: psql -v ON_ERROR_STOP=1 -f av_s02_recuperacao_saneamento.sql URL
-- Uso futuro avalia_dev exige PGOPTIONS opt-in (ver script de saneamento).
\set ON_ERROR_STOP on
SET search_path = public, pg_catalog;
DO $$ DECLARE d text:=current_database();o text:=current_setting('avalia.allow_sanitation',true); BEGIN
 IF d~'^av_s02_saneamento_[A-Za-z0-9_-]+$' THEN NULL;
 ELSIF d='avalia_dev' AND o='AV_S02_SANITATION_20261001' THEN NULL;
 ELSE RAISE EXCEPTION 'Guard recusou banco % (opt-in=%)',d,COALESCE(o,'<null>'); END IF;
END $$;
BEGIN;
SET LOCAL search_path=public,pg_catalog;

-- Recuperação pós-constraint exige downgrade prévio. Aborta antes de DML se
-- uq_human_reviews_job_id ainda existir.
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
   JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname='public'
   AND t.relname='human_reviews' AND c.conname='uq_human_reviews_job_id')
 THEN RAISE EXCEPTION 'uq_human_reviews_job_id ainda existe; execute downgrade para e1b02279b1a5 antes da recuperação'; END IF;
 IF to_regclass('public.human_reviews_superseded') IS NULL
 THEN RAISE EXCEPTION 'human_reviews_superseded ausente; não há arquivo confiável para recuperação'; END IF;
END $$;
LOCK TABLE public.audit_events IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE public.human_reviews IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE public.human_reviews_superseded IN SHARE ROW EXCLUSIVE MODE;

-- Baseline integral de auditoria e vencedora, preservados antes de decidir estado.
DO $$ DECLARE va int;vw int; BEGIN
 SELECT COUNT(*) INTO va FROM public.audit_events a JOIN(VALUES
  ('b12db6d4-3b44-42ca-aa9a-99748fc4b982',TIMESTAMP '2026-09-23 22:53:35.114334'),
  ('4f737eab-3ba0-40af-8738-ae847377ba34',TIMESTAMP '2026-09-23 22:55:15.907615'),
  ('cad4d910-8c91-4a7e-9714-266fac3f7ee6',TIMESTAMP '2026-09-23 22:58:47.636134'))e(id,ts) ON a.id=e.id
 WHERE a.actor_id='cabba145-18bc-40a1-9faa-489f4bfda018' AND a.action='REVIEW_APPROVE'
 AND a.resource_type='CorrectionJob' AND a.resource_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
 AND a.before_json::jsonb='{"53548671-87e7-4784-a7f3-27ce80b66355":"1.00","f99920d8-2368-491c-b82e-f976b6e598c0":"1.00"}'::jsonb
 AND a.after_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb AND a.created_at=e.ts;
 SELECT COUNT(*) INTO vw FROM public.human_reviews WHERE id='31d31b5c-05c7-4206-b2ff-43b2eda14026'
 AND job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0' AND reviewer_id='cabba145-18bc-40a1-9faa-489f4bfda018'
 AND decision='APPROVE' AND final_total=2.00
 AND final_scores_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb
 AND COALESCE(justification,'')='' AND created_at=TIMESTAMP '2026-09-23 22:53:35.110755';
 IF va<>3 OR vw<>1 THEN RAISE EXCEPTION 'Baseline incompleto vencedor %, auditoria %',vw,va; END IF;
END $$;

-- Máquina de estados: recoverable (1 ativa + 2 arquivadas), recovered
-- (3 ativas nominais + 0 arquivadas). Qualquer parcial/divergente aborta.
SELECT
 ((SELECT COUNT(*) FROM public.human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0')=1
  AND (SELECT COUNT(*) FROM public.human_reviews_superseded WHERE id IN('8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b'))=2) recoverable,
 ((SELECT COUNT(*) FROM public.human_reviews h JOIN(VALUES
   ('31d31b5c-05c7-4206-b2ff-43b2eda14026',TIMESTAMP '2026-09-23 22:53:35.110755'),
   ('8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',TIMESTAMP '2026-09-23 22:55:15.904278'),
   ('9459489c-dd8e-4f33-936a-bc76cb7d5f0b',TIMESTAMP '2026-09-23 22:58:47.630896'))e(id,ts) ON h.id=e.id
   WHERE h.job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
     AND h.reviewer_id='cabba145-18bc-40a1-9faa-489f4bfda018'
     AND h.decision='APPROVE' AND h.final_total=2.00
     AND h.final_scores_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb
     AND COALESCE(h.justification,'')='' AND h.created_at=e.ts)=3
  AND (SELECT COUNT(*) FROM public.human_reviews
    WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0')=3
  AND (SELECT COUNT(*) FROM public.human_reviews_superseded
    WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0')=0) recovered
\gset
\if :recovered
 COMMIT;
 \echo RECOVERY_ALREADY_COMPLETE_VALID_NOOP
 \quit
\endif
\if :recoverable
 -- segue
\else
 DO $$ BEGIN RAISE EXCEPTION 'Estado parcial/divergente: recuperação automática recusada'; END $$;
\endif

INSERT INTO public.human_reviews(id,job_id,reviewer_id,decision,final_total,final_scores_json,justification,created_at)
SELECT id,job_id,reviewer_id,decision,final_total,final_scores_json,justification,created_at
FROM public.human_reviews_superseded WHERE id IN(
 '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b');

-- Prova restauração integral das 3 linhas, timestamps e conteúdo comum.
DO $$ DECLARE v int;vdup int; BEGIN
 SELECT COUNT(*) INTO v FROM public.human_reviews h JOIN(VALUES
 ('31d31b5c-05c7-4206-b2ff-43b2eda14026',TIMESTAMP '2026-09-23 22:53:35.110755'),
 ('8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c',TIMESTAMP '2026-09-23 22:55:15.904278'),
 ('9459489c-dd8e-4f33-936a-bc76cb7d5f0b',TIMESTAMP '2026-09-23 22:58:47.630896'))e(id,ts) ON h.id=e.id
 WHERE h.job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0' AND h.reviewer_id='cabba145-18bc-40a1-9faa-489f4bfda018'
 AND h.decision='APPROVE' AND h.final_total=2.00
 AND h.final_scores_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb
 AND COALESCE(h.justification,'')='' AND h.created_at=e.ts;
 SELECT COUNT(*) INTO vdup FROM(SELECT job_id FROM public.human_reviews GROUP BY job_id HAVING COUNT(*)>1)x;
 IF v<>3 OR vdup<>1 THEN RAISE EXCEPTION 'Restauração incompleta: linhas %, grupos duplicados %',v,vdup; END IF;
END $$;

-- Compara as duas reinseridas com o arquivo antes de apagá-lo.
DO $$ DECLARE v int; BEGIN
 SELECT COUNT(*) INTO v FROM public.human_reviews h FULL JOIN public.human_reviews_superseded s USING(id)
 WHERE COALESCE(h.id,s.id) IN('8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b')
 AND(h.id IS NULL OR s.id IS NULL OR h.job_id IS DISTINCT FROM s.job_id OR h.reviewer_id IS DISTINCT FROM s.reviewer_id
 OR h.decision IS DISTINCT FROM s.decision OR h.final_total IS DISTINCT FROM s.final_total
 OR h.final_scores_json IS DISTINCT FROM s.final_scores_json OR h.justification IS DISTINCT FROM s.justification
 OR h.created_at IS DISTINCT FROM s.created_at);
 IF v<>0 THEN RAISE EXCEPTION 'Linhas reinseridas divergem do arquivo: %',v; END IF;
END $$;
DELETE FROM public.human_reviews_superseded WHERE id IN(
 '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b');
DO $$ BEGIN
 IF (SELECT COUNT(*) FROM public.human_reviews_superseded WHERE id IN(
  '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b'))<>0
 THEN RAISE EXCEPTION 'Arquivo não foi limpo'; END IF;
END $$;
COMMIT;
\echo RECOVERY_APPLIED_GREEN
