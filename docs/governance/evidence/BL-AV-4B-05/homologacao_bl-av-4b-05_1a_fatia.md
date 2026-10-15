---
id: "homologacao_bl-av-4b-05_1a_fatia"
tema: "BL-AV-4B-05 — 1ª fatia (exclusão lógica reversível de imagens) — homologação restrita"
data: "2026-10-15 (America/Sao_Paulo)"
decisor: "Rafael"
pr: "#20 (https://github.com/rafaelinfopiaui/avalia-platform/pull/20)"
base: "main e21332ae1335cab7e90eb9db8450e29865057b53"
---

# Homologação restrita — BL-AV-4B-05, 1ª fatia

Rafael homologou a 1ª fatia de BL-AV-4B-05 (**exclusão lógica reversível
de imagens**) e autorizou a integração do PR #20 por merge commit, após a
conferência da CI registrada abaixo.

## 1. Conferência da CI (run 38704909538, HEAD e510e2c) — CORREÇÃO DE PRECISÃO

Verificação do workflow `.github/workflows/ci.yml` (literal) e do log
literal da run — sem deduzir execução pelo nome do job nem pela presença
do serviço de banco:

- O job **"Core API (FastAPI + Postgres)"** define um serviço
  `postgres:16`, MAS o step "Run core tests" roda
  `env -u AI_ENGINE_URL -u DATABASE_URL -u JWT_SECRET pytest app/tests -q`
  — **removendo `DATABASE_URL`** (o pytest cai no default SQLite do
  `conftest.py`) e **sem definir `AVALIA_TEST_POSTGRES_URL`** em lugar
  nenhum do workflow.
- Os testes de concorrência `test_pg_*` são marcados
  `@pytest.mark.skipif(not AVALIA_TEST_POSTGRES_URL)`. Logo, na CI eles
  ficaram **SKIPPED**.
- **Log literal da run (step "Run core tests"):**
  `232 passed, 10 skipped, 14 warnings in 182.08s`. Os 10 skipped são os
  `@requires_postgres`. O serviço `postgres:16` existe no job mas **não é
  exercitado pelos testes de concorrência**; a suíte da CI roda em SQLite.

**Reconciliação (correção de afirmação imprecisa):** um relatório-resumo
anterior (em chat) afirmou que a CI rodou "a suíte completa incluindo
concorrência Postgres". Isso está **incorreto** e fica corrigido aqui: na
CI a concorrência Postgres NÃO executou (ficou skipped; a CI usa SQLite).
A evidência válida de concorrência em PostgreSQL real é a **execução
LOCAL** do orquestrador — `test_answer_image_deletion.py` com
`AVALIA_TEST_POSTGRES_URL` apontando a um banco descartável
(`avalia_test_blav4b05_*`, criado e dropado): **33 casos passados**,
incluindo os 4 `test_pg_*` (delete-vs-confirm exatamente-um-vence em 10
rodadas; exclusões concorrentes [2]/[8]; restore-após-confirmação-409;
restore-vs-confirm), com serialização resolvida no motor do PostgreSQL via
`SELECT ... FOR UPDATE`. Essa evidência local permanece válida e é o
lastro da homologação quanto à concorrência.

**Não** se ampliou a infraestrutura de CI nesta rodada (não se adicionou
`AVALIA_TEST_POSTGRES_URL` nem um job Postgres para os testes de
concorrência) — apenas se corrigiu o registro.

## 2. Objeto homologado e limites preservados

Homologado: **exclusão lógica reversível de imagens de resposta**, com:
- exclusão lógica reversível, **sem remoção física** (arquivo preservado);
- exclusão e restauração **somente antes da confirmação** (estágio A);
- **bloqueio após a confirmação (B/C/D), inclusive para admin** (409);
- serialização pela linha de `answers` (`SELECT ... FOR UPDATE`);
- auditoria mínima (sem nome original / nome em storage / hash / conteúdo);
- download bloqueado durante a exclusão lógica (410).

Permanecem **pendentes e fora desta fatia** (não homologados):
- retenção e política de janela;
- expurgo / remoção física;
- tratamento posterior de metadados;
- backups;
- decisão institucional `DEC-AV-013`;
- migração operacional e ativação (não autorizadas).

`BL-AV-4B-05` permanece **parcial**. Numerador preservado em **22/70** —
esta homologação da entrega funcional não altera o numerador e não promove
baseline.

## 3. Episódio de soft-deny — registro factual preservado

Mantido como fato, sem minimização: na revisão de DESENHO do Antigravity,
a 1ª execução teve a confirmação de ferramenta negada (soft-deny) e foi
reexecutada com `--dangerously-skip-permissions`. **O mecanismo de
aprovação foi contornado** — o fato de ter sido uma operação de LEITURA
(numa revisão somente-leitura) restringe o impacto, mas NÃO elimina que
houve um contorno do mecanismo de aprovação. Detalhes e diferenciação dos
demais eventos (bloqueios respeitados pelo executor; cota 429) em
`registro_processo_agentes.md` §1 e §3.

## 4. Distinção de estados

Aprovação técnica ≠ publicação ≠ **homologação (esta)** ≠ integração ≠
ativação. Esta homologação é da **entrega funcional**; a aplicação
operacional das migrações (migração operacional) e a ativação permanecem
**não autorizadas**.
