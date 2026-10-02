# Última execução registrada

- execução: [EXEC-2026-10-02-01 — Execução real de P4 contra `avalia_dev`](snapshot_EXEC-2026-10-02-01_execucao-real-p4-avalia-dev.md);
- tipo: execução operacional real, autorizada explicitamente por Rafael
  (2026-10-02), exclusivamente contra a instância LOCAL de `avalia_dev`,
  usando os scripts integrados em `main@9310b545cd332948104edf44e555eff5f2582e4c`
  (PR #10);
- status: saneamento das 3 duplicatas legadas em `human_reviews` aplicado
  (2 arquivadas em `human_reviews_superseded`, vencedora e auditoria
  preservadas); as 3 migrações pendentes (`7b1d6d853f20`, `c4a8b2d91e37`,
  `a9f4c2e71b06`) aplicadas, `version_num=a9f4c2e71b06`; todos os
  pós-checks (a)-(g) confirmados; nenhuma falha; reconciliação de
  contagens (antes/depois, com evidência) concluída a pedido de Rafael;
  `DEBT-AV-011`/`BL-AV-1-10` resolvidos;
- baseline promovido: não;
- ação Git/remota desta execução: nenhuma — documentação local (snapshot,
  reconciliação, atualização de registros de débito/backlog/dashboard)
  pendente de publicação em PR separado, conforme autorização específica
  de Rafael;
- P5 (ativação de `ACADEMIC_MODULE_ENABLED`/`VITE_ACADEMIC_MODULE_ENABLED`),
  seed operacional, deploy e promoção de baseline permanecem
  explicitamente **não autorizados**.

Execução imediatamente anterior: [EXEC-2026-10-01-03 — Retomada da
preparação de `avalia_dev` após interrupção de cota](snapshot_EXEC-2026-10-01-03_retomada-preparacao-avalia-dev.md),
seguida da integração do PR #10 (merge commit `9310b545cd332948104edf44e555eff5f2582e4c`).

Execuções anteriores: [EXEC-2026-10-01-02 — Encerramento da execução local de AV-S04](snapshot_EXEC-2026-10-01-02_encerramento-execucao-av-s04.md), [EXEC-2026-10-01-01 — Abertura da execução local de AV-S04](snapshot_EXEC-2026-10-01-01_abertura-execucao-av-s04.md), [EXEC-2026-09-30-03 — Regularização documental e retirada de worktrees](snapshot_EXEC-2026-09-30-03_organizacao-local.md), [EXEC-2026-09-30-02 — GOV-006 (2ª rodada): reconciliação do numerador nominal e causa comprovada das divergências entre checkouts](snapshot_EXEC-2026-09-30-02_gov-006-reconciliacao.md), [EXEC-2026-09-30-01 — GOV-006 (1ª rodada, numerador com erro aritmético, corrigido na rodada seguinte)](snapshot_EXEC-2026-09-30-01_gov-006-auditoria.md), [EXEC-2026-09-29-04 — AV-S05B: benchmark experimental de OCR/visão local (texto impresso)](snapshot_EXEC-2026-09-29-04_av-s05b-benchmark-ocr.md), [EXEC-2026-09-29-03 — fechamento de AC-05 e reconciliação do conteúdo do PR #2 contra `main`](snapshot_EXEC-2026-09-29-03_ac05-reconciliacao-pr2.md), [EXEC-2026-09-29-02 — homologação de BL-AV-2-04/AV-S03 e integração do PR #3](snapshot_EXEC-2026-09-29-02_homologacao-integracao-av-s03.md), [EXEC-2026-09-29-01 — validação de AC-10, pacote de revisão e PR #3](snapshot_EXEC-2026-09-29-01_ac10-pacote-pr-ci-av-s03.md).

Este ponteiro acompanha a execução mais recente, ainda que parcial ou não homologada. Não confundir com o último baseline validado.
