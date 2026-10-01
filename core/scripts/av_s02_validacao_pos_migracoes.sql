-- Validação pós-saneamento + pós-migrações, somente leitura.
\set ON_ERROR_STOP on
SET search_path=public,pg_catalog;
DO $$ DECLARE d text:=current_database();o text:=current_setting('avalia.allow_sanitation',true); BEGIN
 IF d~'^av_s02_saneamento_[A-Za-z0-9_-]+$' THEN NULL;
 ELSIF d='avalia_dev' AND o='AV_S02_SANITATION_20261001' THEN NULL;
 ELSE RAISE EXCEPTION 'Guard recusou banco % (opt-in=%)',d,COALESCE(o,'<null>'); END IF;
END $$;
DO $$ DECLARE vdup int;vwin int;varc int;va int;vver text;vrows int; BEGIN
 SELECT COUNT(*) INTO vdup FROM(SELECT job_id FROM public.human_reviews GROUP BY job_id HAVING COUNT(*)>1)x;
 SELECT COUNT(*) INTO vwin FROM public.human_reviews WHERE id='31d31b5c-05c7-4206-b2ff-43b2eda14026'
 AND job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0' AND reviewer_id='cabba145-18bc-40a1-9faa-489f4bfda018'
 AND decision='APPROVE' AND final_total=2.00
 AND final_scores_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb
 AND COALESCE(justification,'')='' AND created_at=TIMESTAMP '2026-09-23 22:53:35.110755';
 SELECT COUNT(*) INTO varc FROM public.human_reviews_superseded WHERE id IN(
 '8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c','9459489c-dd8e-4f33-936a-bc76cb7d5f0b')
 AND job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
 AND superseded_reason='duplicate-equivalent-review-pre-BL-AV-1-10';
 SELECT COUNT(*) INTO va FROM public.audit_events a JOIN(VALUES
 ('b12db6d4-3b44-42ca-aa9a-99748fc4b982',TIMESTAMP '2026-09-23 22:53:35.114334'),
 ('4f737eab-3ba0-40af-8738-ae847377ba34',TIMESTAMP '2026-09-23 22:55:15.907615'),
 ('cad4d910-8c91-4a7e-9714-266fac3f7ee6',TIMESTAMP '2026-09-23 22:58:47.636134'))e(id,ts) ON a.id=e.id
 WHERE a.actor_id='cabba145-18bc-40a1-9faa-489f4bfda018' AND a.action='REVIEW_APPROVE'
 AND a.resource_type='CorrectionJob' AND a.resource_id='4f56a10b-3a44-4df5-9047-adef7546a3c0'
 AND a.before_json::jsonb='{"53548671-87e7-4784-a7f3-27ce80b66355":"1.00","f99920d8-2368-491c-b82e-f976b6e598c0":"1.00"}'::jsonb
 AND a.after_json::jsonb='[{"criterion_id":"53548671-87e7-4784-a7f3-27ce80b66355","score":"1.00"},{"criterion_id":"f99920d8-2368-491c-b82e-f976b6e598c0","score":"1.00"}]'::jsonb AND a.created_at=e.ts;
 SELECT COUNT(*),MIN(version_num) INTO vrows,vver FROM public.alembic_version;
 IF vdup<>0 OR vwin<>1 OR varc<>2 OR va<>3 OR vrows<>1 OR vver IS DISTINCT FROM 'a9f4c2e71b06'
 THEN RAISE EXCEPTION 'Validação dados/version falhou dup %,win %,arc %,audit %,version rows % value %',vdup,vwin,varc,va,vrows,vver; END IF;
END $$;
DO $$ DECLARE v int; BEGIN
 SELECT COUNT(*) INTO v FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace
 WHERE n.nspname='public' AND(
 (t.relname='human_reviews' AND c.conname='uq_human_reviews_job_id' AND c.contype='u' AND c.convalidated)
 OR(t.relname='questions' AND c.conname='uq_questions_assessment_position' AND c.contype='u' AND c.convalidated)
 OR(t.relname='assessments' AND c.conname='fk_assessments_class_group_id' AND c.contype='f' AND c.convalidated)
 OR(t.relname='assessments' AND c.conname='fk_assessments_cloned_from_id' AND c.contype='f' AND c.convalidated));
 IF v<>4 THEN RAISE EXCEPTION 'Constraints-chave esperadas 4, encontradas %',v; END IF;
END $$;
DO $$ DECLARE v int; BEGIN
 SELECT COUNT(*) INTO v FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid JOIN pg_class t ON t.oid=i.indrelid JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='public' AND t.relname='questions' AND NOT i.indisvalid;
 IF v<>0 THEN RAISE EXCEPTION 'Índices INVALID em questions: %',v; END IF;
END $$;
DO $$ DECLARE v int; BEGIN
 SELECT COUNT(*) INTO v FROM(SELECT assessment_id FROM public.questions GROUP BY assessment_id
 HAVING MIN(position)<>1 OR MAX(position)<>COUNT(*) OR COUNT(DISTINCT position)<>COUNT(*))x;
 IF v<>0 THEN RAISE EXCEPTION 'Avaliações com posições inválidas: %',v; END IF;
END $$;
SELECT 'POST_MIGRATION_VALIDATION_GREEN' result;
