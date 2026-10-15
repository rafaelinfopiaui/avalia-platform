---
id: "EXEC-2026-10-15-02"
tipo: execucao
sprint: "BL-AV-4B-05 (retenção e exclusão de imagens) — 1ª fatia: exclusão lógica reversível"
gerado_em: "2026-10-15T05:10:00-03:00"
executor: "Hermes (orquestrador) + Claude Code (implementação) + Antigravity/Gemini (revisão independente)"
status: "IMPLEMENTADO LOCALMENTE E VALIDADO — sem ação Git (sem stage/commit/push/merge); baseline não promovido"
base: "main e21332ae1335cab7e90eb9db8450e29865057b53"
branch: "docs/bl-av-4b-05-plano-retencao-exclusao-imagens"
---

# Snapshot EXEC-2026-10-15-02 — BL-AV-4B-05, 1ª fatia (exclusão lógica reversível de imagens)

> Continuação de EXEC-2026-10-15-01 (planejamento). Rafael decidiu
> D1/D2/D3 e R3, e autorizou implementação LOCAL após revisão dirigida
> do desenho. Esta rodada implementou, validou por execução real e
> submeteu à revisão independente — SEM qualquer ação Git. Reconfirmado
> no início e no fim: `main` local == remoto ==
> `e21332ae1335cab7e90eb9db8450e29865057b53`; bancos protegidos
> intactos.

## 1. Decisões aplicadas (de Rafael)

- **D1** — exclusão lógica reversível, com restauração; **sem** remoção
  física nesta fatia.
- **D2** — exclusão permitida só no estágio A (`AGUARDANDO_TRANSCRICAO`);
  **bloqueada após confirmação (B/C/D), inclusive admin** (mais
  restritiva que a recomendação original do desenho).
- **D3** — sem prazo, sem expurgo físico, sem automação.
- **R3** (ressalva do Antigravity, decidida por Rafael, opção a) —
  restauração também só no estágio A; após confirmação retorna 409
  inclusive admin; conjunto de imagens de transcrição confirmada não é
  alterado silenciosamente.

## 2. O que foi implementado (local, working tree, não commitado)

- Migração `b8d3e5f7a2c4` (aditiva): `answer_images.deleted_at`,
  `deleted_by_id` (FK users), nullable; `down_revision = f2a9c4e6b1d3`;
  downgrade bloqueado se houver exclusão lógica. **Sem** `storage_deleted_at`.
- `DELETE /v1/answer-images/{id}` (exclusão lógica) e
  `POST /v1/answer-images/{id}/restore` (restauração) — guard de estágio A,
  `SELECT ... FOR UPDATE` na linha de `answers` como ponto comum de
  serialização, idempotência por UPDATE condicional, 409
  `ANSWER_IMAGES_LOCKED` em B/C/D inclusive admin.
- `GET /v1/answers/{id}/images/deleted` — projeção mínima
  (`DeletedAnswerImageOut`: id, deleted_at, deleted_by_id), sem download,
  sem hash/nome original.
- Leituras filtram `deleted_at IS NULL`; download de excluída → 410.
- Confirmação de transcrição exige imagem ativa sob o mesmo lock (409
  `ANSWER_HAS_NO_ACTIVE_IMAGE`).
- `AuditEvent` de exclusão/restauração com metadados mínimos (id,
  answer_id, uploaded_by_id, content_type, size_bytes, created_at) —
  nunca nome original/nome em storage/hash/conteúdo.
- Script `core/scripts/blav4b05_diagnostico_imagens.py` — somente leitura
  (detecta registro-sem-arquivo e arquivo-sem-registro).
- Frontend: exclusão só em A, seção de imagens excluídas com restaurar
  (sem visualizar), download bloqueado, confirmação desabilitada sem
  imagem ativa.

## 3. Validação (execução real, pelo orquestrador — não só self-report)

> **Precisão sobre a CI (correção):** a CI deste repositório roda os testes
> em **SQLite** — o workflow faz `env -u DATABASE_URL ... pytest` e **não
> define `AVALIA_TEST_POSTGRES_URL`**. Logo, os testes de concorrência
> `test_pg_*` ficam **SKIPPED na CI** (run `38704909538`: `232 passed, 10
> skipped`). A evidência de concorrência em PostgreSQL real é a **execução
> LOCAL** abaixo, não a CI. Não se deduz execução Postgres pelo nome do job
> nem pela presença do serviço de banco. (Mesma ressalva já registrada em
> `DEC-AV-041`.)

- **pytest geral (SQLite):** 232 passed, 10 skipped.
- **`test_answer_image_deletion.py` com PostgreSQL real** (banco
  descartável `avalia_test_blav4b05_*`, criado e dropado): **33 passed**,
  incluindo 4 de **concorrência real** (ThreadPoolExecutor + sessões
  Postgres independentes; serialização no motor do banco via
  `SELECT FOR UPDATE`; 10 rodadas provam que exatamente um vence em
  delete-vs-confirm).
- **Migração:** upgrade da cadeia completa → `b8d3e5f7a2c4`; downgrade +
  reaplicação OK em Postgres descartável.
- **Frontend:** `npm run build` (tsc+vite) e `npm run lint` (eslint)
  limpos.
- **Navegador real** (Chrome dedicado :9337, Core+Vite isolados, banco
  descartável, dados fictícios): exclusão lógica (banner + seção de
  excluídas com restaurar, sem download), restauração (volta a ativa),
  e ACD-09 (excluídas as 2 ativas → "Confirmar transcrição" desabilitado
  com mensagem "Esta resposta não tem nenhuma imagem ativa. Restaure uma
  imagem excluída antes de confirmar a transcrição."). Ambiente removido
  ao final; bancos protegidos intactos.

## 4. Revisão independente

- **Antigravity** (CLI `agy`), modelo **"Gemini 3.8 Flash (High)"** —
  família DISTINTA do orquestrador (Opus) e do executor (Claude Code):
  **APROVADO**, sem ressalvas, sem defeitos impeditivos; verificou os 10
  itens com citação de arquivo:linha e confirmou que os testes de
  concorrência são reais. Parecer em
  [`parecer_antigravity_implementacao.md`](../evidence/BL-AV-4B-05/parecer_antigravity_implementacao.md).
- A 1ª tentativa de revisão (modelo "Claude Opus 4.6 (Thinking)") foi
  cortada por cota (HTTP 429); não troquei de provedor pago nem usei
  Codex como revisor geral — reexecutei no próprio Antigravity com
  modelo dentro da cota. Episódio registrado em
  [`registro_processo_agentes.md`](../evidence/BL-AV-4B-05/registro_processo_agentes.md).

## 5. Estado resultante e limites

- Nenhum stage/commit/push/merge; nenhum worktree novo; nenhum baseline
  promovido; sem remoção física/expurgo; sem migração operacional; sem
  P5/OCR/deploy.
- Bancos protegidos `avalia_dev` (`a9f4c2e71b06`, 16 human_reviews) e
  `avalia_apresentacao_demo_20261002` intactos; nenhum banco de teste
  sobreviveu; nenhum artefato temporário no working tree.
- **Numerador permanece 22/70.** `BL-AV-4B-05` permanece **parcial**:
  esta 1ª fatia (exclusão lógica reversível) está implementada e validada
  localmente, mas o item canônico completo (retenção, remoção física,
  tratamento posterior de metadados, backups) e a decisão institucional
  `DEC-AV-013` seguem **pendentes**. Esta rodada NÃO reivindica avanço de
  numerador nem homologação formal — entrega local para revisão de Rafael.

## 6. Próximo passo (decisão de Rafael)

Revisar o diff local (11 arquivos alterados + 5 novos). Só mediante sua
autorização separada haverá qualquer ação Git (stage/commit/push/PR).
Fases futuras de BL-AV-4B-05 (remoção física, retenção, backups)
permanecem fora desta fatia.
