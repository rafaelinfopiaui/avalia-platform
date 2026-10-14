---
id: "AV-S06B"
status: planejada
objetivo_aprovado_por: Rafael (2026-10-13/14, nesta conversa)
consolidador: "Hermes"
baseline_entrada: "main HEAD 6f8a526 (merge PR #14, AV-S03B integrada)"
---

# AV-S06B — Recebimento e armazenamento de imagens (Etapa 4B, parte 2)

> Identificador já previsto desde GOV-002/GOV-004 (ver
> `trilha_operacao_de_turma.md` §11, Fase 4, e
> `backlog/backlog_tecnico_avalia.md` linhas `BL-AV-4B-03/04/05`). Nenhuma
> sprint anterior renumerada; nenhuma numeração paralela criada.

## 1. Objetivo e valor esperado

Receber, armazenar e recuperar com segurança uma imagem de resposta de
aluno (uma foto por questão, conforme `DEC-AV-018`), preparando o terreno
para a extração de texto (OCR, `AV-S07B`) sem a implementar. Resultado
observável: um professor autenticado, com vínculo ativo na avaliação
correspondente, consegue enviar uma imagem válida, que é armazenada com
metadados de autoria/data/vínculo e pode ser recuperada posteriormente —
sem qualquer OCR real ou simulado, sem disparo de correção automática.

## 2. Origem

| Fonte/requisito | Trecho ou decisão aplicável | Link |
|---|---|---|
| `BL-AV-4B-03` | Recebimento e armazenamento de imagens (formato, tamanho, páginas, validação de conteúdo) | [`backlog_tecnico_avalia.md`](../backlog/backlog_tecnico_avalia.md) linha 97 |
| `BL-AV-4B-04` | Controle de acesso, preservação do original e metadados de vínculo/autoria/data | linha 98 |
| `BL-AV-4B-05` | Retenção, exclusão e proteção de logs contra dado sensível de imagem (decisão) | linha 99 |
| `DEC-AV-018` | uma resposta de uma questão por foto (não prova inteira) | [`decisions.md`](../registers/decisions.md), aprovada 2026-09-21 |
| `DEC-AV-021` | seleção manual pelo professor (avaliação/questão/aluno) | aprovada 2026-09-21 |
| Trilha §11, Fase 4 | `AV-S06B` é a sprint de recebimento/armazenamento, depende da Fase 2 (decisão arquitetural de OCR implementável) só para a Fase 4 inteira avançar até extração — **não** para esta sprint especificamente, que não faz OCR | [`trilha_operacao_de_turma.md`](../backlog/trilha_operacao_de_turma.md) |
| Pedido desta conversa (2026-10-13/14) | autorização explícita de planejamento e execução local dos itens `BL-AV-4B-03/04/05` | corpo da conversa |

Lacunas de fonte: nenhuma — os três itens já estão no backlog canônico
desde GOV-002/GOV-004, sem necessidade de inventar requisito novo.

## 3. Escopo

Incluído:
- endpoint de upload de imagem associada a uma `Answer` existente (ou
  criada no mesmo fluxo), restrito a `multipart/form-data`, com validação
  de tipo declarado E de conteúdo real do arquivo (não confiar só no
  `Content-Type` do cliente);
- armazenamento do arquivo original em disco local (ambiente isolado),
  com nome de arquivo gerado pelo servidor (nunca derivado do nome
  enviado pelo cliente) e caminho previsível apenas internamente;
- modelo de dados novo (`AnswerImage` ou equivalente) registrando:
  `answer_id`, caminho/identificador de armazenamento, nome original
  (metadado, não usado como caminho), tipo MIME real detectado, tamanho
  em bytes, hash de conteúdo (integridade), autor do upload, timestamp;
- autorização por propriedade/vínculo reaplicando exatamente o padrão já
  usado em `create_answer`/`require_assessment_mutation` — mesmo
  professor dono da avaliação (ou admin), mesma regra de vínculo ativo
  quando a avaliação tem turma;
- endpoint de recuperação da imagem (download/preview), autorizado pela
  mesma regra, nunca por URL pública sem autenticação;
- validações de upload: arquivo ausente/vazio, tipo MIME declarado
  divergente do conteúdo real, arquivo corrompido/não decodificável como
  imagem, tamanho acima do limite, nome/caminho de arquivo neutralizado
  (sem path traversal, sem caracteres de controle);
- registro de falha de armazenamento sem deixar metadado "órfão" (sem
  linha no banco referenciando um arquivo que não foi de fato gravado,
  e vice-versa).

Fora de escopo (explicitamente, por limite desta rodada):
- qualquer OCR, extração de texto, real ou simulado (`AV-S07B`);
- qualquer confirmação/edição de transcrição (`AV-S08B`);
- disparo automático de correção a partir da imagem;
- escolha de motor/modelo de OCR (`BL-AV-4B-02`, ainda não decidido,
  aguardando amostra manuscrita — **não bloqueia esta sprint**);
- processamento assíncrono/fila de extração (`BL-AV-4B-21`, `AV-S07B`);
- suporte a múltiplas páginas por resposta (`DEC-AV-019`, pendente);
- suporte a fórmulas/tabelas/desenho/código manuscrito além de texto
  corrido (`DEC-AV-020`, pendente — sem efeito aqui, pois não há OCR);
- qualquer escrita em `avalia_dev`/banco de apresentação, P5, seed
  operacional, deploy, promoção de baseline;
- novo benchmark de OCR.

## 4. Baseline e estado de abertura

- último baseline validado: nenhum promovido sob esta governança;
- última execução registrada: `EXEC-2026-10-13-02` (AV-S03B, integrada
  via PR #14, merge `6f8a526`);
- commit/branch/upstream no início desta sprint: `main`, `up to date com
  origin/main`, HEAD `6f8a526`;
- working tree no início desta sprint: limpo (`git status --short` vazio);
- dependências e bloqueantes: nenhum bloqueante novo; `BKL-AV-001` (CNE)
  aberto, sem efeito (dados fictícios apenas). `BL-AV-4B-02` (decisão
  arquitetural de OCR) permanece não decidido, mas **não bloqueia** esta
  sprint — ver matriz de decisões §7.

## 5. Backlog e DoR

| ID | Descrição | Responsável | DoR | Estado |
|---|---|---|---|---|
| BL-AV-4B-03 | Endpoint de upload + validação de formato/tamanho/conteúdo real | Claude Code | ready | planejado |
| BL-AV-4B-04 | Modelo `AnswerImage`, autorização por vínculo, preservação do original, metadados | Claude Code | ready | planejado |
| BL-AV-4B-05 (parcial) | Retenção/exclusão — decisão de política pendente; implementação desta sprint limitada ao necessário para não deixar arquivo órfão em caso de falha, sem política operacional de retenção automática | Claude Code | refinado — decisão formal de retenção/exclusão de produção pendente de Rafael (ver §7) | planejado |
| — | Revisão independente de código + validação visual | Antigravity | ready | planejado |
| — | Auditoria pontual (somente se risco concreto surgir) | Codex | condicional | planejado |

## 6. Mapa de impacto

| Item | Criar | Alterar | Não tocar |
|---|---|---|---|
| BL-AV-4B-03/04 | `core/app/models.py` (nova classe `AnswerImage`), `core/alembic/versions/` (nova migração), `core/app/routers/images.py` (novo router), `core/app/schemas.py` (schemas de upload/retorno) | `core/app/main.py` (`include_router`), `core/requirements.txt` (adicionar `Pillow` para validação real de conteúdo de imagem) | `core/app/routers/academic.py`, `core/app/routers/config.py` (não tocar) |
| BL-AV-4B-05 (parcial) | diretório de armazenamento local novo (ex.: `core/var/answer_images/`, fora do Git, path configurável por env var) | — | — |
| Frontend (mínimo, se necessário para validação visual) | — | possivelmente `frontend/src/pages/AnswerPage.tsx` (campo de upload), `frontend/src/services/api.ts` (chamada de upload) — **a confirmar durante a execução**, mínimo necessário para demonstrar o fluxo, sem avançar para conferência/OCR | — |

Mudança fora do mapa exige registro prévio em Ajustes de Percurso (§14).

## 7. Decisões necessárias sobre formatos, tamanho, retenção e exclusão

Nenhuma decisão abaixo foi presumida como aprovada. Proposta concreta
(não aprovação) para permitir avançar, com decisão explícita necessária
de Rafael antes de qualquer uso além do ambiente isolado desta sprint:

| Decisão | Proposta de Hermes (não aprovada) | Impacto se não decidida |
|---|---|---|
| Formatos aceitos | JPEG e PNG apenas (formatos de foto de celular mais comuns; evita o universo de formatos de imagem com superfícies de ataque maiores, ex. SVG/GIF animado) | sem decisão, a sprint usa esta proposta **restrita ao ambiente isolado de teste**, não como política de produto definitiva |
| Tamanho máximo | 10 MB por imagem (foto de celular moderna comprimida, com folga) | idem — usado como limite técnico de implementação, revisável |
| Retenção/exclusão (`DEC-AV-013`, já pendente em caráter geral, e `BL-AV-4B-05` especificamente para imagens) | nenhuma política automática de expiração nesta sprint; exclusão só manual/administrativa, sem endpoint de exclusão em massa | `DEC-AV-013` já estava pendente antes desta sprint; não decidida aqui, só reconfirmada como pendência explícita — não bloqueia implementação com dados fictícios |
| Proteção de logs contra dado sensível de imagem | nunca logar o conteúdo binário nem o caminho completo de armazenamento em log de aplicação; logar apenas IDs/metadados não sensíveis | sem decisão formal, a sprint aplica esta prática como implementação, sujeita a revisão |

Estas são propostas de implementação para viabilizar a sprint em ambiente
isolado — não substituem decisão formal de Rafael quando/se o módulo for
para produção com dados reais (subordinado a `BKL-AV-001`, pendência
regulatória do CNE, e a `DEC-AV-013`/`014` gerais).

## 8. Critérios de aceite

| ID | Critério | Método previsto | Estado |
|---|---|---|---|
| AC-01 | Professor dono/vinculado consegue enviar uma imagem válida (JPEG/PNG, dentro do limite) associada a uma resposta de sua própria avaliação | integração real | **validado** — HTTP real (Hermes: POST -> 201, metadados com sha256, `storage_filename` não exposto; Antigravity confirmou em banco próprio) + testes automatizados `test_owner_uploads_valid_png_with_correct_metadata`, `test_owner_uploads_valid_jpeg`, `test_admin_can_upload` |
| AC-02 | Professor sem vínculo/propriedade recebe 403 ao tentar enviar imagem para avaliação de outro professor | integração real | **validado** — HTTP real (Hermes: outro professor -> 403) + teste automatizado `test_other_professor_cannot_upload`, `test_class_assessment_requires_active_link` |
| AC-03 | Requisição sem autenticação é rejeitada (401) | integração real | **validado** — HTTP real (Hermes e Antigravity: sem token -> 401) + teste automatizado `test_upload_without_token_returns_401` |
| AC-04 | Arquivo com `Content-Type` declarado como imagem mas conteúdo real não é imagem válida é rejeitado (ex.: executável renomeado) | integração real | **validado** — HTTP real (Hermes: bytes falsos com `image/png` -> 422) + testes automatizados `test_forged_image_content_type_is_rejected[random-bytes/pdf/executable]`, `test_declared_type_diverging_from_content_is_rejected`, `test_real_gif_is_rejected_even_when_declared_as_png` |
| AC-05 | Arquivo acima do limite de tamanho é rejeitado antes de gravação completa em disco | integração real | **validado por teste automatizado** — `test_oversized_upload_rejected_by_content_length` (1ª defesa, Content-Length) e `test_oversized_upload_rejected_while_streaming` (2ª defesa, streaming; temporário removido). Não exercitado por upload HTTP grande dedicado nesta rodada; coberto pelos dois testes de defesa em camadas |
| AC-06 | Nome de arquivo malicioso (`../../etc/passwd`, caracteres de controle, etc.) não resulta em escrita fora do diretório de armazenamento autorizado | integração real (teste adversarial) | **validado** — HTTP real (Hermes: enviado `../../../etc/passwd.png`; arquivos em disco com nome UUID seguro, nenhum traversal, nenhum arquivo fora do storage) + testes automatizados `test_adversarial_filename_is_metadata_only`, `test_sanitize_original_filename` |
| AC-07 | Falha simulada de armazenamento (ex.: diretório sem permissão) não deixa registro no banco referenciando arquivo inexistente | integração real (falha induzida) | **validado por teste automatizado** (falha induzida por monkeypatch) — `test_unavailable_storage_dir_leaves_no_record`, `test_failure_finalizing_file_leaves_no_record_and_no_file`, `test_commit_failure_removes_stored_file`. Falha de I/O/commit é simulada; não reproduzida por indução real de permissão de FS nesta rodada |
| AC-08 | Imagem armazenada só é recuperável (download/preview) pelo professor dono/vinculado ou admin — outro usuário recebe 403 | integração real | **validado** — HTTP real (Hermes: download do dono -> 200 com bytes idênticos e `content-type` correto; outro professor -> 403) + testes automatizados `test_owner_downloads_original_bytes`, `test_other_professor_cannot_download_or_list` |
| AC-09 | Nenhuma imagem é exposta por URL pública/sem autenticação | integração real + inspeção de código | **validado** — inspeção de código (nenhum `StaticFiles`/`Mount`; download sempre autenticado, headers `nosniff`/`no-store`) + HTTP real (download anônimo -> 401) + teste automatizado `test_images_are_never_public` |
| AC-10 | Nenhum OCR real ou simulado é executado; nenhuma correção é disparada automaticamente a partir do upload | integração real + inspeção de código | **validado** — inspeção (sem import/chamada de OCR/IA/`CorrectionJob`/`BackgroundTasks`) + HTTP real (Hermes: 0 `CorrectionJob` após upload) + testes automatizados `test_upload_does_not_create_correction_job`, `test_images_module_has_no_ocr_or_correction_references` (AST) |

## 9. Definition of Done

- [x] AC-01 a AC-10 avaliados com evidência real (ver §8 e §15.4/15.5);
- [x] mudanças vinculadas a `BL-AV-4B-03/04/05`;
- [x] validações com comando/data/ambiente/resultado (§15.4, §8);
- [x] falhas e não executados visíveis (bug MPO em §15.3; limites de AC-05/07 em §8; exclusão não implementada em §15.7; interface não entregue em §15.1);
- [x] decisões pendentes de formato/tamanho/retenção documentadas como propostas, não aprovações (§7 + tabela de decisões no pacote de entrega);
- [x] snapshot de execução gerado (`snapshot_EXEC-2026-10-14-02_execucao_av-s06b.md`);
- [x] dashboard atualizado, preservando 19/70 até nova homologação;
- [x] closure gate preenchido (§16);
- [ ] homologação de Rafael registrada somente se e quando ocorrer — **pendente** (aguarda decisão de produto + publicação + homologação).

## 10. Validações previstas

| Item/AC | Comando ou procedimento | Ambiente | Tipo |
|---|---|---|---|
| AC-01/02/03 | chamadas HTTP reais com tokens de professores distintos e sem token | PostgreSQL isolado, Core real | integração real |
| AC-04 | upload de arquivo não-imagem com `Content-Type: image/jpeg` forjado | idem | integração real |
| AC-05 | upload de arquivo gerado acima do limite configurado | idem | integração real |
| AC-06 | upload com nome de arquivo adversarial (path traversal) | idem | integração real |
| AC-07 | diretório de armazenamento temporariamente sem permissão de escrita | idem | integração real |
| AC-08/09 | download/preview com token de usuário não autorizado; inspeção de rotas registradas | idem | integração real + inspeção |
| AC-10 | grep por chamadas de OCR/IA no novo código; confirmar que nenhum job de correção é criado pelo endpoint de upload | inspeção de código + integração real | inspeção + integração |

## 11. Riscos e mitigação

| Risco | Probabilidade/impacto qualitativo | Mitigação | Dono |
|---|---|---|---|
| Validação de conteúdo real de imagem insuficiente (confiar só em `Content-Type`) | médio/alto | usar biblioteca de imagem (Pillow) para tentar decodificar o arquivo, não apenas checar extensão/header | Claude Code |
| Path traversal via nome de arquivo enviado pelo cliente | baixo/alto | nome de arquivo gerado pelo servidor (UUID), nome original só como metadado, nunca usado em `open()`/`Path()` | Claude Code + Codex (auditoria pontual, se necessário) |
| Imagem exposta sem autenticação por engano (rota estática mal configurada) | médio/alto | endpoint de download sempre autenticado, nunca servir diretório estático diretamente | Hermes (verificação independente) |
| Registro órfão em caso de falha de gravação | baixo/médio | transação: só commitar o registro no banco após confirmação de escrita em disco bem-sucedida; AC-07 testa isso explicitamente | Claude Code |

## 12. Estimativas

Não estimado em story points/horas, por ausência de velocity sob esta
governança. Tamanho qualitativo: M (média) — um modelo novo, uma
migração, um router novo, validações de segurança de upload.

## 13. Critérios de encerramento

Esta sprint encerra quando AC-01 a AC-10 estiverem avaliados com
evidência real (aprovados ou explicitamente reprovados/pendentes) e o
pacote (diff + testes + revisão independente + relatório) estiver pronto
para decisão de Rafael sobre publicação. Comportamento de upload/
armazenamento/recuperação deve estar demonstrável de ponta a ponta em
ambiente isolado, sem OCR.

## 14. Ajustes de percurso

| Data/fuso | Mudança | Motivo | Impacto | Decisão/autorização |
|---|---|---|---|---|

## 15. Execução e review

Execução local em 2026-10-14 (-03). Autorização: `DEC-AV-035`. Sem
stage/commit/push/merge. Branch `feat/av-s06b-recebimento-armazenamento-imagens`
(checkout principal, sem worktree novo). HEAD `6f8a526`.

### 15.1 Delimitação da entrega (escopo real)

Esta fatia entrega **somente backend/API** (modelo, migração, 3 endpoints,
validação e armazenamento privado). **Não** inclui interface de upload no
frontend — o campo de upload/preview no cliente estava marcado como "a
confirmar" no mapa de impacto (§6) e **não foi implementado nem validado
visualmente nesta rodada**. Nenhuma validação visual de fluxo de interface é
declarada.

### 15.2 Implementação (executor: Claude Code)

Novos: `core/app/routers/images.py` (3 endpoints: `POST /v1/answers/{id}/images`,
`GET /v1/answers/{id}/images`, `GET /v1/answer-images/{id}/download`);
`core/app/tests/test_answer_images.py`; migração
`core/alembic/versions/d5e3a7c19f42_add_answer_images.py` (tabela
`answer_images`). Alterados: `models.py` (classe `AnswerImage`), `schemas.py`
(`AnswerImageOut`, não expõe `storage_filename`), `config.py`
(`ANSWER_IMAGES_STORAGE_DIR`, `ANSWER_IMAGE_MAX_BYTES` default 10 MB), `main.py`
(só registra o router), `requirements.txt` (`Pillow>=10.0`), `.gitignore`
(`/core/var/`). Autorização reaproveitada de `create_answer`
(`_get_owned_assessment` + `require_assessment_mutation`); nome em disco gerado
pelo servidor (UUID); escrita atômica com rollback; download sempre autenticado;
nenhum OCR/correção; logs só com IDs/metadados.

O executor **não conseguiu rodar nada** no ambiente dele (pip/pytest/ruff/banco
bloqueados por permissão) — entregou o código com os 10 AC marcados honestamente
como "NÃO VALIDADO NESTA RODADA". Toda a validação abaixo foi feita por Hermes e
Antigravity.

### 15.3 Correção de defeito real (Hermes, durante a verificação)

Bug real encontrado e corrigido em `core/app/routers/images.py`: o código
passava `"MPO"` na lista de `Image.open(formats=[...])`, o que levanta
`KeyError('MPO')` no Pillow 12.x (MPO não é plugin de abertura registrável por
nome; é reconhecido via plugin JPEG) — isso **quebrava 100% dos uploads
válidos** (JPEG e PNG), não só fotos de câmera. Correção: separar
`_OPEN_FORMATS = ["JPEG", "PNG"]` (lista passada a `Image.open`) do dicionário
`_ALLOWED_FORMATS` (que mantém `MPO -> image/jpeg` só no mapeamento de
resultado). Correção pontual de bug concreto do executor; validada por suíte e
por HTTP real, e revisada independentemente pelo Antigravity como "correta,
completa e sem regressão".

### 15.4 Verificação independente do Hermes (execução real)

- Suíte completa: **136 casos, 136 passed, 0 failed** (comando
  `cd core && .venv/bin/python -m pytest app/tests -q`). Coleta confirma:
  **110 pré-existentes + 26 do AV-S06B = 136**. Os 26 casos novos vêm de **24
  funções `def test_`**, sendo 1 função parametrizada com 3 valores
  (`test_forged_image_content_type_is_rejected[random-bytes/pdf/executable]`),
  o que expande 1 função em 3 casos (+2). O "24 testes" do relatório do executor
  conta funções; "26 casos" é a coleta expandida do pytest. Sem regressão nos
  pré-existentes.
- Lint: **`ruff check --config ../ruff.toml app` -> "All checks passed!"**. Esse
  escopo é o pacote `app/` apenas; a migração nova fica em
  `core/alembic/versions/` (fora de `app/`) e por isso não entra nesse resultado
  — ver achado em §15.6.
- Validação real em **PostgreSQL isolado novo** (`av_s06b_verif_hermes_20261014`,
  dropado ao final): `alembic upgrade head` aplicou a migração; tabela
  `answer_images` criada com FKs (`answers.id`, `users.id`) e índice
  `ix_answer_images_answer_id`; Core real exercitado via HTTP — 11/11 checks reais
  (ver §8, coluna Estado). Bancos protegidos `avalia_dev` e
  `avalia_apresentacao_demo_20261002` verificados intactos (`a9f4c2e71b06`, 16
  human_reviews) antes e depois; porta e storage temporário liberados.

### 15.5 Revisão independente (Antigravity — Gemini 3.8 Flash High)

Família de modelo diferente do executor, para diversidade real. Parecer completo
em `docs/governance/evidence/AV-S06B/revisao_independente_antigravity.md`.
**Veredito: APROVADO.** Execução própria e independente (não reutilizou
resultados do Hermes): suíte própria **136 passed** (110 + 26), ruff limpo em
`app`, banco isolado próprio (`av_s06b_review_agy_20261014`, dropado), HTTP real
(201/200/401/422), teste de migração upgrade/downgrade incluindo recusa de
downgrade com registros. Inspeção de segurança por dimensão — todas CONFIRMADO
SEGURO: path traversal, autorização/vínculo, validação de conteúdo real, limite
de tamanho, registros órfãos, exposição pública, OCR/correção (zero),
privacidade de logs. Validou a correção do MPO como correta/completa/sem
regressão. AC-01 a AC-10 todos Aprovados. Bancos protegidos intactos; nenhuma
ação Git.

### 15.6 Achados não-bloqueantes (registrados, sem tratamento nesta rodada)

1. **`ruff I001` (import block não ordenado) na migração nova**
   (`core/alembic/versions/d5e3a7c19f42_add_answer_images.py:11`). É **padrão
   preexistente do projeto**: `ruff check alembic/versions/` acusa o mesmo I001
   em 4 migrações (as 3 históricas `e1b02279b1a5`, `7b1d6d853f20`,
   `c4a8b2d91e37` e a nova). A migração nova apenas segue a convenção existente.
   Tratamento: **não corrigido nesta rodada** para não ampliar o escopo a
   modernização de migrações históricas; fixável com `ruff --fix` se/quando
   Rafael decidir padronizar as migrações do repositório.
2. **Deprecation de `class Config` no Pydantic V2** em `AnswerImageOut`
   (`core/app/schemas.py`). Segue o padrão já usado por todos os demais schemas
   do arquivo. Tratamento: **não alterado nesta rodada** para não ampliar a
   modernização geral de schemas; migração futura para
   `model_config = ConfigDict(from_attributes=True)` deve ser decisão de
   padronização do módulo inteiro, não desta sprint.

### 15.7 Exclusão de imagens — não implementada

A proposta de "exclusão só manual/administrativa" (§7) é **proposta de política,
não funcionalidade entregue**. Esta rodada entregou apenas **upload, listagem e
download**. **Não existe endpoint de exclusão** nem procedimento documentado de
exclusão nesta entrega. O único comportamento de "não-perda" implementado é a
recusa de `downgrade` da migração quando a tabela tem registros. Criar exclusão
não estava autorizado nesta rodada e não foi feito.

## 16. Closure gate

Estado em 2026-10-14 (-03): **backend/API homologado por Rafael (`DEC-AV-036`)**
e autorizado a integrar por merge commit; **integração registrada abaixo após o
merge**. Verificação independente do Hermes + revisão independente do Antigravity
(APROVADO) concluídas antes da homologação.

Classificação do gate: **concluída com débitos** — o backend/API foi entregue,
validado e homologado, mas a Etapa 4B (recebimento por imagem utilizável de ponta
a ponta) permanece aberta por depender da interface e de decisões ainda pendentes.

Distinções de estado (não confundir):
- **Backend/API**: homologado (`DEC-AV-036`).
- **Integração (merge)**: ver Adendo de integração no snapshot
  `snapshot_EXEC-2026-10-14-02_execucao_av-s06b.md` (SHA integrado + CI pós-merge).
- **Interface de upload**: NÃO entregue (§15.1) — fica como complemento frontend
  da AV-S06B, planejado para próxima autorização.
- **Uso operacional**: migração em bancos protegidos e ativação NÃO autorizados.
- **Retenção/exclusão operacional**: pendentes (`BL-AV-4B-05` em aberto).

Encerramento de backlog (critérios canônicos — não marcar completo item que ainda
exija interface ou requisito ausente):
- `BL-AV-4B-03` (recebimento/armazenamento): backend homologado; **não encerrado**
  — o fluxo só é utilizável com a interface de upload (ainda ausente).
- `BL-AV-4B-04` (controle de acesso/preservação/metadados): backend homologado;
  **não encerrado** pelo mesmo motivo.
- `BL-AV-4B-05` (retenção/exclusão/proteção de logs): **pendente** — só a proteção
  de logs foi entregue; retenção e exclusão operacional não decididas.

`DEC-AV-018` preservada como "uma resposta de uma questão por foto" — não é
unicidade de foto por questão nem proibição de reenvio (o backend permite reenvio;
cada upload cria novo registro, preservando o anterior).

Progresso homologado permanece **19/70**; a integração do backend **não** aumenta
o numerador. `AV-S05B` permanece parcial. O fechamento formal a partir de
[sprint_closure_template.md](../templates/sprint_closure_template.md) só marcará a
Etapa 4B como concluída quando interface + decisões pendentes forem resolvidas.

## 17. Complemento — Resposta por imagem (sub-fatia, 2026-10-14)

Autorização: `DEC-AV-037`. Rodada local (sem publicação). Resolve a lacuna
contratual identificada na homologação do backend (§16): o upload exigia uma
`Answer` pré-existente, mas toda `Answer` exigia `text` não-vazio — não havia
como a foto ser a entrada inicial da resposta. Desenho técnico (revisado de
forma independente pelo Antigravity, APROVADO COM AJUSTES) em
`evidence/AV-S06B/desenho_resposta_por_imagem.md` (v2).

### 17.1 Direção de produto (aprovada)
A foto pode ser a entrada inicial da resposta, sem texto digitado/vazio/fictício.
Resposta por imagem nasce "aguardando transcrição"; correção bloqueada até
transcrição confirmada pelo professor. Fluxo textual existente inalterado.
Nesta fatia NÃO há OCR — a resposta por imagem termina legitimamente em
"aguardando transcrição". `DEC-AV-018` preservada ("uma resposta de uma questão
por foto"; sem unicidade de foto nem proibição de reenvio).

### 17.2 Mudança de contrato (menor coerente)
`Answer.text` -> nullable; novos `Answer.source` (TEXT|IMAGE) e
`Answer.transcription_status` (AGUARDANDO_TRANSCRICAO|TRANSCRICAO_CONFIRMADA);
CheckConstraint `(source='TEXT' AND text IS NOT NULL) OR (source='IMAGE')`;
backfill determinístico (existentes -> TEXT/CONFIRMADA). Novo endpoint
transacional `POST /v1/answers/image` (reuso da validação/gravação homologada de
`routers/images.py`, com o endpoint e o guard em `main.py` para respeitar o teste
AST de isolamento). Guard de correção em `request_correction` (422
`ANSWER_NOT_TRANSCRIBED`) + defesa em profundidade em `run_correction_job`.
Frontend: tela de resposta por foto + listagem/visualização + estados + aviso de
"aguarda transcrição, não corrigida".

### 17.3 Critérios de aceite (resposta por imagem)

| ID | Critério | Método previsto | Estado |
|---|---|---|---|
| ACI-01 | Criar resposta por imagem (JPEG/PNG <=10 MiB) sem texto -> 201; Answer `source=IMAGE`, `transcription_status=AGUARDANDO_TRANSCRICAO`, 1 `AnswerImage` vinculada | integração real | **validado** — HTTP real (Hermes: 201, source=IMAGE/text=None/AGUARDANDO/1 imagem; Antigravity confirmou, arquivo em disco 0600 com nome UUID) + teste `test_image_answer_is_created_without_text_awaiting_transcription` |
| ACI-02 | Pedir correção de resposta por imagem não transcrita -> 422 `ANSWER_NOT_TRANSCRIBED`, nenhum `CorrectionJob` criado | integração real + teste | **validado** — HTTP real (Hermes e Antigravity: 422 + 0 jobs confirmado por consulta ao banco) + teste `test_correction_of_untranscribed_image_answer_is_blocked` |
| ACI-03 | Fluxo textual existente inalterado (criar resposta textual -> 201 `source=TEXT`; pedir correção -> 202) | integração real + regressão | **validado** — HTTP real (201 TEXT/CONFIRMADA; correção 202) + suíte histórica sem regressão (158 passed = 136 + 22) |
| ACI-04 | Autorização no novo endpoint: professor sem vínculo -> 403; sem token -> 401 | integração real | **validado** — HTTP real (Hermes e Antigravity: 401 sem token, 403 sem vínculo) + testes `test_image_answer_without_token_returns_401`, `test_image_answer_by_unrelated_professor_returns_403`, `test_admin_can_create_image_answer` |
| ACI-05 | Falha de commit após gravar arquivo no fluxo transacional -> nenhuma Answer/AnswerImage órfã, nenhum arquivo solto | teste (falha induzida) | **validado por teste** — `test_commit_failure_leaves_no_answer_image_or_file` (monkeypatch commit), `test_file_finalize_failure_leaves_no_records` (monkeypatch os.replace) |
| ACI-06 | Reenvio em `/answers/{id}/images` continua criando nova imagem, preservando anteriores (DEC-AV-018) | teste | **validado por teste** — `test_resend_on_existing_image_answer_preserves_previous` |
| ACI-07 | Migração aplica + backfill determinístico em banco isolado; linhas existentes viram TEXT/CONFIRMADA, nenhuma com text NULL; CheckConstraint ativo | integração real (banco isolado) | **validado** — PostgreSQL isolado (Hermes e Antigravity, bancos próprios dropados): upgrade + backfill (legadas -> TEXT/CONFIRMADA, texto preservado); CheckConstraint ativo (bloqueia TEXT sem texto, permite IMAGE sem texto); downgrade protegido recusa com dados IMAGE sem texto; downgrade limpo + re-upgrade idempotente (Antigravity) |
| ACI-08 | Frontend: estados carregando/sucesso/erro; aviso explícito "aguarda transcrição, não corrigida"; nenhuma menção a nota/IA no upload | validação visual | **validado com ressalva** — validação visual em navegador real (Chromium/CDP) contra ambiente isolado descartável, 9 de 10 cenários PASS (seleção manual + cascata; JPEG e PNG válidos com carregando/sucesso; listagem + visualização por download autenticado via blob, imagem renderizada; ausência de ação de correção na tela de foto vs. textual; rejeição de inválido 422 e >10 MiB no cliente, com mensagem compreensível; troca de avaliação/questão limpa seleção/arquivo; fluxo textual utilizável). **Ressalva (cenário "estado após recarregar"):** o estado "aguardando transcrição" está preservado no **backend** (verificado no banco após reload: `source=IMAGE`/`AGUARDANDO_TRANSCRICAO`/`text` NULL), mas a tela de Resposta por Foto não reexibe as respostas persistidas após F5 (lista "nesta sessão", volátil). Por decisão de Rafael, registrado como **débito de UX** (ver §17.5), sem alteração de código nesta rodada — exigiria endpoint `GET` de listagem inexistente. Evidência: `evidence/AV-S06B/validacao_visual_resposta_por_imagem.md` |
| ACI-09 | Defesa em profundidade: `run_correction_job` com `answer.text` nulo/vazio falha explicitamente antes de chamar o AI Engine | teste | **validado por teste** — `test_run_correction_job_fails_fast_without_calling_ai_engine` (parametrizado; cliente httpx substituído por classe que falha se instanciada) |

### 17.4 Limites desta sub-fatia
Sem OCR, sem transcrição simulada, sem confirmação fictícia, sem exclusão
(BL-AV-4B-05 permanece pendente), sem retenção operacional, sem stage/commit/
push/merge nesta rodada, sem migração operacional em bancos protegidos, sem P5/
seed/deploy/baseline/novo benchmark OCR. Numerador homologado permanece 19/70.

### 17.5 Débito de UX e precisão das pendências (pós-validação visual, 2026-10-14)

**Débito de UX (reexibição após recarregar) — `DEBT-AV-014`.** A tela de Resposta por Foto não
reexibe, após recarregar (F5), as respostas por imagem já persistidas (em estado
"aguardando transcrição") de uma avaliação/questão — a lista é rotulada "enviadas
nesta sessão" (estado volátil). O estado em si **está preservado no backend**
(verificado no banco: `source=IMAGE`/`transcription_status=AGUARDANDO_TRANSCRICAO`/
`text` NULL após reload). Reexibir na UI exigiria um endpoint `GET` de listagem de
respostas por imagem por avaliação/questão, hoje **inexistente**. Decisão de Rafael
(2026-10-14): registrar como débito, **sem alterar código** nesta rodada; a
reexibição fica como pendência para fatia futura. Não afeta recebimento,
armazenamento, autorização nem o bloqueio de correção (todos validados).

**Precisão das pendências.**
- **Confirmação de transcrição:** *não implementada nesta fatia*. A resposta por
  imagem termina legitimamente em "aguardando transcrição".
- **Dependência de OCR (conferida no backlog, não presumida):** a **extração
  automática** de texto (`AV-S07B`, `BL-AV-4B-06..09`) depende da decisão
  arquitetural de OCR (`BL-AV-4B-02`). A atividade de **conferência/confirmação**
  (`AV-S08B`) **não está globalmente bloqueada pelo motor de OCR**: o backlog prevê
  `BL-AV-4B-13` (transcrição manual quando a extração falhar — mesmo princípio de
  RN-017: IA indisponível → entrada manual), um caminho de confirmação que não
  depende tecnicamente do OCR. O planejamento da conferência pode avançar; apenas
  os itens que consomem a saída automática do OCR dependem de `AV-S07B`.
- **Limitação do parsing multipart (distinção precisa):** no endpoint
  `POST /v1/answers/image`, por usar campos declarativos do FastAPI/Starlette, o
  corpo multipart é lido **antes** da checagem de autorização. Isso é **consumo de
  recursos** (buffer temporário do Starlette, em disco do sistema) — **não** é
  gravação no armazenamento persistente da aplicação nem escrita no banco: nenhum
  byte entra no diretório privado de imagens nem em `answer_images` antes da
  autorização. Débito arquitetural não-bloqueante para hardening futuro (ex.:
  checagem de `Content-Length`/limite no proxy); **esta rodada não amplia para
  hardening geral**.
- **`BL-AV-4B-05`** (retenção/exclusão operacional): permanece **pendente**.
