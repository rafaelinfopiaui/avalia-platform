# Evidência — Verificação independente do Hermes (DEBT-AV-014, retomada de respostas por imagem)

> Rodada LOCAL. Sem stage/commit/push. Ambiente isolado descartável. Navegador real
> (Chromium/CDP). Evidências sanitizadas. Branch:
> feat/av-s06b-debt-014-retomada-respostas-imagem (base main cf81109).

## 1. Ambiente

- Banco PostgreSQL descartável: `av_s06b_debt014_visual_hermes` (migrado a head
  `e7c3f1a8b2d4`; dropado ao final). Não usou `avalia_dev` nem apresentação.
- Core em `127.0.0.1:8197` (`ACADEMIC_MODULE_ENABLED=false`, `ai_engine=false`, sem
  OCR). Vite em `127.0.0.1:5274`. Chromium de automação em `9337`.
- Seed: prof1 (dono) + prof2 (não-dono); Avaliação A publicada (2 questões) com
  **2 respostas por imagem JÁ persistidas** (semeadas no banco, não enviadas pela
  UI) — para provar a retomada. Mais, ao vivo, uma avaliação com `class_group_id` e
  dono SEM `ProfessorClassLink` (ACD-04).

## 2. Verificação automatizada (execução real do Hermes)

| Item | Comando | Resultado |
|---|---|---|
| Testes novos do endpoint | `pytest app/tests/test_image_answers_listing.py -q` | **13 passed** |
| Suíte completa (regressão, ACD-10) | `pytest app/tests -q` | **171 passed, 0 failed** (158 anteriores + 13) |
| Lint backend | `ruff check --config ../ruff.toml app` | All checks passed |
| Build frontend | `npm run build` (tsc + vite) | sucesso, 0 erros |

## 3. Verificação HTTP real (Postgres isolado + Core)

| ACD | Cenário | Resultado |
|---|---|---|
| ACD-01 | lista respostas IMAGE da avaliação com estado + imagens; não inclui textuais | **PASS** (HTTP 200, n=2, todas source=IMAGE/AGUARDANDO_TRANSCRICAO, ≥1 imagem) |
| ACD-02 | filtro por `question_id` (1 resultado); questão inexistente/de outra avaliação -> 404 | **PASS** (200 n=1; 404) |
| ACD-03 | sem token -> 401; não-dono -> 403 | **PASS** (401; 403) |
| ACD-05 | `storage_filename` nunca exposto no corpo | **PASS** (ausente) |
| ACD-04 | **leitura histórica**: avaliação com `class_group_id`, dono com ZERO `ProfessorClassLink` -> **200** com a resposta | **PASS** (vínculos do dono=0, HTTP 200, n=1) — leitura por propriedade, sem exigir vínculo ativo |

Logs do servidor confirmaram os status reais (200/404/401/403) e eventos
sanitizados (só IDs).

## 4. Verificação em navegador real (os pontos pedidos por Rafael)

| Cenário | Resultado (evidência observada) |
|---|---|
| **Retomada em NOVA SESSÃO** | **PASS** — login fresco, ao selecionar a Avaliação A aparecem as **2 respostas por imagem persistidas** (semeadas, não enviadas na sessão): "Aluno A (persistido) — Questão 1" e "Aluno B (persistido) — Questão 2", ambas "AGUARDANDO TRANSCRIÇÃO", com imagem listada e botão Visualizar |
| **Retomada após RELOAD** | **PASS** — F5 em `/respostas/foto?avaliacao=<id>` reexibe as 2 respostas persistidas; sem query, mostra o estado inicial de orientação |
| **Leitura histórica** | **PASS** (HTTP, §3 ACD-04) — dono sem vínculo ativo lê a avaliação com turma |
| **Bloqueio para outro professor** | **PASS** — prof2 (não-dono) recebe 403 no GET (§3 ACD-03); não consegue sondar questões |
| **Troca de avaliação/questão sem dados anteriores** | **PASS** — filtrar Questão 1 passou de 2 cards para 1 ("Aluno A — Questão 1"), limpando o card da Questão 2; enunciado atualizou; nada da seleção anterior permaneceu |
| **Correção ainda bloqueada sem transcrição** | **PASS** — a tela de resposta por foto não tem botão de correção/análise/nota/IA (só "Enviar foto da resposta" e "Atualizar lista"); o backend mantém 422 `ANSWER_NOT_TRANSCRIBED` (ACD-09, por teste) |
| Visualização por download autenticado | **PASS** — "Visualizar" baixa via blob autenticado; imagem renderiza (`naturalWidth` real da imagem semeada) |
| Estados (inicial/carregando/vazio/erro) | **PASS** — estado inicial "Selecione uma avaliação…"; seção renomeada para "Respostas por foto desta seleção" |

## 5. Integridade

- Bancos protegidos **intactos** antes e depois: `avalia_dev` (a9f4c2e71b06, 16
  human_reviews) e `avalia_apresentacao_demo_20261002` (a9f4c2e71b06). Sem migração
  operacional, sem escrita neles.
- Ambiente desta rodada (Core, Vite, Chromium, banco, storage, scripts) encerrado e
  removido. Portas 8197/5274/9337 livres.

## 6. Diff local (sem stage/commit/push)

Código (3 arquivos): `core/app/main.py` (+40, novo `GET
/v1/assessments/{id}/image-answers`, somente leitura, autorização por propriedade);
`frontend/src/pages/ImageAnswerPage.tsx` (+69/-9, busca/retomada + estados + limpeza
na troca); `frontend/src/services/api.ts` (+6, `listImageAnswers`). Testes novos:
`core/app/tests/test_image_answers_listing.py`.

## 7. Ressalvas desta fatia

- Nenhuma ressalva funcional nos cenários pedidos (todos comprovados).
- **Correção (2026-10-14, pós-parecer do Antigravity):** a observação registrada
  nesta linha sobre desempate em empate de `created_at` não constitui débito — o
  `ORDER BY` do endpoint já inclui `Answer.id`/`AnswerImage.id` como critério de
  desempate explícito e determinístico (`core/app/main.py:727,734`), confirmado
  pelo parecer do Antigravity (`revisao_debt_014_antigravity.md` §8.1). A
  observação original (sobre o teste assumir `created_at` estritamente crescente)
  descrevia apenas um cenário teórico de timestamp empatado nunca observado na
  prática; não há ação pendente.
- Revisão independente do Antigravity: **APROVADO** (ver `revisao_debt_014_antigravity.md`).

Progresso homologado permanece **19/70**; AV-S05B parcial; BL-AV-4B-05 pendente.
