---
id: "EXEC-2026-10-14-02"
tipo: execucao
sprint: "AV-S06B"
gerado_em: "2026-10-14T01:20:00-03:00"
executor: "Claude Code (implementação), Hermes (verificação independente + correção pontual), Antigravity (revisão independente, veredito APROVADO)"
status: "aprovacao-tecnica-local-concluida; pendente de decisao de produto, publicacao e homologacao"
commit_referencia: "6f8a526bb5fd5c6014e57cd869065755587b01f6 (main, HEAD; sem novos commits — working tree local)"
---

# Snapshot EXEC-2026-10-14-02 — Execução de AV-S06B (recebimento/armazenamento de imagens)

> Registro histórico. Não promove baseline. Encerra a execução técnica local
> da AV-S06B (continuação do snapshot de abertura EXEC-2026-10-14-01).

## 1. Resumo

Execução local dos itens `BL-AV-4B-03/04/05` (recebimento, armazenamento
privado e recuperação autorizada de imagens de resposta), **somente
backend/API**, sem OCR e sem disparo de correção. Cadeia de agentes real:
Claude Code implementou; Hermes verificou de forma independente (achando e
corrigindo um bug real); Antigravity revisou de forma independente (veredito
APROVADO). Sem stage/commit/push/merge. Branch
`feat/av-s06b-recebimento-armazenamento-imagens`, HEAD `6f8a526`.

## 2. Entregas

| Item | Estado | Entrega | Evidência |
|---|---|---|---|
| BL-AV-4B-03 (recebimento) | implementado e validado localmente | `POST /v1/answers/{id}/images` (multipart, 1 arquivo) | AC-01/03/04/05 (§8 da sprint); HTTP real 201/401/422/413 |
| BL-AV-4B-04 (armazenamento privado) | implementado e validado localmente | armazenamento em disco com nome UUID do servidor, escrita atômica, hash sha256, sem URL pública | AC-06/07/09 (§8); path traversal CONFIRMADO SEGURO (Antigravity) |
| BL-AV-4B-05 (recuperação autorizada) | implementado e validado localmente | `GET /v1/answers/{id}/images`, `GET /v1/answer-images/{id}/download` (autenticados) | AC-08 (§8); download dono 200 / terceiro 403 (HTTP real) |

## 3. Não entregas e lacunas

- **Interface de upload (frontend)**: NÃO entregue. Esta fatia é backend/API
  apenas; o campo de upload/preview no cliente estava "a confirmar" no mapa de
  impacto e não foi implementado nem validado visualmente. Nenhuma validação
  visual de fluxo é declarada.
- **Exclusão de imagens**: NÃO implementada. A "exclusão só manual/
  administrativa" é proposta de política (§7), não funcionalidade entregue. Não
  há endpoint nem procedimento documentado de exclusão. Único comportamento de
  não-perda: recusa de `downgrade` da migração com registros presentes.
- **Decisões de produto** (formato/tamanho/retenção/exclusão): permanecem
  pendentes de Rafael — ver tabela de decisões no pacote de entrega.
- **AC-05 e AC-07**: validados por testes automatizados (limite em 2 camadas;
  falha de I/O/commit por monkeypatch), não por indução real de permissão de FS
  nem upload HTTP grande dedicado nesta rodada.

## 4. Arquivos impactados

| Caminho | Natureza | Item |
|---|---|---|
| `core/app/routers/images.py` | criado (+ correção MPO por Hermes) | 3 endpoints de imagem |
| `core/app/tests/test_answer_images.py` | criado | 24 funções / 26 casos de teste |
| `core/alembic/versions/d5e3a7c19f42_add_answer_images.py` | criado | migração tabela `answer_images` |
| `core/app/models.py` | alterado | classe `AnswerImage` |
| `core/app/schemas.py` | alterado | `AnswerImageOut` (sem `storage_filename`) |
| `core/app/config.py` | alterado | `ANSWER_IMAGES_STORAGE_DIR`, `ANSWER_IMAGE_MAX_BYTES` |
| `core/app/main.py` | alterado | registro do router |
| `core/requirements.txt` | alterado | `Pillow>=10.0` |
| `.gitignore` | alterado | `/core/var/` |
| `docs/governance/sprints/sprint_AV-S06B_...md` | alterado | §8/§9/§15/§16 preenchidas |
| `docs/governance/snapshots/snapshot_EXEC-2026-10-14-02_execucao_av-s06b.md` | criado | este snapshot |
| `docs/governance/evidence/AV-S06B/` | criado | prompt, parecer Antigravity, tabela de decisões, pacote |

## 5. Validações executadas

| Data/fuso | Item/AC | Comando/procedimento | Ambiente | Tipo | Resultado real |
|---|---|---|---|---|---|
| 2026-10-14 | suíte completa | `cd core && .venv/bin/python -m pytest app/tests -q` | venv local, SQLite de teste | automatizado | **136 passed, 0 failed** |
| 2026-10-14 | contagem | `pytest --collect-only -q` | venv local | coleta | 136 total = **110 pré-existentes + 26 AV-S06B** (24 funções; 1 parametrizada ×3 = +2 casos) |
| 2026-10-14 | lint | `ruff check --config ../ruff.toml app` | venv local | automatizado | **All checks passed** (escopo `app/`) |
| 2026-10-14 | lint migração | `ruff check alembic/versions/` | venv local | automatizado | I001 em 4 migrações (3 históricas + a nova) — padrão preexistente; fora do escopo `app/` |
| 2026-10-14 | migração real | `alembic upgrade head` | PostgreSQL isolado `av_s06b_verif_hermes_20261014` | integração real | tabela `answer_images` criada com FKs + índice |
| 2026-10-14 | AC-01..10 HTTP | upload/download/403/401/422 via httpx contra Core real | PostgreSQL isolado + uvicorn | integração real | **11/11 checks reais passaram** |
| 2026-10-14 | correção MPO | isolado + suíte | venv local | automatizado | `KeyError('MPO')` que quebrava todo upload → corrigido; 15 testes que falhavam passaram |
| 2026-10-14 | revisão independente | suíte+HTTP+inspeção próprias | Antigravity, banco isolado próprio | integração + inspeção | **APROVADO**; 136 passed; segurança CONFIRMADO SEGURO em todas as dimensões |
| 2026-10-14 | bancos protegidos | `psql` somente leitura | avalia_dev / apresentação | leitura | intactos `a9f4c2e71b06`, 16 human_reviews, antes e depois |
| 2026-10-14 | teardown | `dropdb`, limpeza de storage, checagem de porta | ambiente de verificação | operacional | bancos isolados dropados, porta livre, nada residual |

## 6. Decisões, débitos e bloqueantes

- decisões: nenhuma nova de Rafael registrada; propostas de formato/tamanho/
  retenção/exclusão apresentadas na tabela de decisões (pacote de entrega), sem
  presumir aprovação; `DEC-AV-013`/`019`/`020` seguem pendentes;
- débitos: 2 achados não-bloqueantes registrados (ruff I001 padrão do projeto nas
  migrações; deprecation de `class Config` no Pydantic V2 padrão dos schemas) —
  NÃO tratados nesta rodada para não ampliar escopo a modernização geral;
- bloqueantes: nenhum novo; `BKL-AV-001` (CNE) aberto, sem efeito (dados fictícios).

## 7. Estado final

- aprovação técnica local: concluída (executor + verificação independente +
  revisão independente APROVADO);
- publicação (PR): não ocorreu — sem stage/commit/push/merge;
- homologação por Rafael: não ocorreu;
- integração/ativação operacional: não ocorreu;
- progresso homologado: permanece **19/70**; `AV-S05B` permanece parcial;
- Git: branch local com working tree não-staged; nenhuma ação remota;
- bancos protegidos: intactos.

## 8. Baseline

- esta execução promove baseline? não;
- último baseline validado permanece: nenhum promovido sob esta governança;
- condição para promoção: inalterada.

## 9. Próxima ação

Apresentar a Rafael o pacote local (diff dos rastreados, conteúdo dos novos,
inventário com checksums, parecer independente) e a tabela de decisões pendentes,
para decisão de produto + publicação. Nenhum stage/commit antes da revisão do
diff exato por Rafael.

## 10. Adendos

### Adendo 1 — Publicação em PR rascunho (2026-10-14, autorizada por Rafael)

Rafael aprovou as decisões de produto desta rodada (formatos JPEG/PNG; limite
10_485_760 bytes = 10 MiB como limite funcional; retenção/exclusão operacional
seguem pendentes; exclusão não implementada; proteção de logs mantida como
requisito técnico) e autorizou publicar a entrega backend/API em PR rascunho,
sem merge nem ativação.

- Ajuste pré-publicação: comentário do limite em `config.py` tornado exato
  (10_485_760 bytes = 10 MiB, não 10 MB decimais). Só comentário; suíte de
  imagens reexecutada (26 passed) e ruff `app` limpo após o ajuste.
- Pacote recuperável enxugado: removidas as cópias redundantes de código
  (`arquivos-novos/`) e o diff recortado; mantidos README, `git_status.txt` e
  `INVENTARIO_CHECKSUMS.sha256` (o código oficial são os arquivos versionados;
  o diff oficial é o do PR).
- Stage seletivo por finalidade, com `git diff --cached` conferido antes de cada
  commit. **4 commits**:
  - `5bed52e` feat(core): modelo AnswerImage, migração, config
  - `d3a607d` feat(core): endpoints upload/listagem/download
  - `8860282` test(core): suíte de imagens + Pillow
  - `875af61` docs(governance): sprint/snapshots/dashboard/evidências
- Push verificado por `git fetch` independente: remoto == local ==
  **`875af61337f8e50cad878f6ca87cf840fcb84b42`**.
- **PR #15** (rascunho): https://github.com/rafaelinfopiaui/avalia-platform/pull/15
  — base `main`, head `875af61`, `isDraft: true`, `mergeable: MERGEABLE`,
  `mergeStateStatus: CLEAN`.
- **Checks do HEAD publicado (run 38512003394): 3/3 PASS** — Core API
  (FastAPI+Postgres) 2m12s, AI Engine, Frontend.
- Checagens de segurança antes do push: nenhum segredo/credencial, nenhuma
  imagem de teste/storage/banco/backup no conjunto; `/core/var/` ignorado;
  relatório do executor em `local-nao-versionado/` (ignorado) não versionado.
- Sem merge, sem ativação operacional, sem migração em bancos protegidos, sem
  P5/deploy/baseline. **Não** há homologação nem integração declaradas.
