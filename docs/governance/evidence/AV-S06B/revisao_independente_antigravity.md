# Revisão Independente de Código — AV-S06B (Recebimento e Armazenamento de Imagens)

- **Revisor independente:** Antigravity (Google DeepMind)
- **Implementador:** Claude Code
- **Verificador do rito:** Hermes
- **Data da revisão:** 2026-10-14 (horário local: 2026-10-14T00:35:00-03:00)
- **Branch revisada:** `feat/av-s06b-recebimento-armazenamento-imagens`
- **Ambiente de execução dos testes:** macOS, Python 3.11.11, Pillow 12.3.0, PostgreSQL 16 (local)

---

## 1. Veredito

**APROVADO**

A implementação da sprint `AV-S06B` cumpre integralmente os requisitos de escopo, os critérios de aceite AC-01 a AC-10 e as diretrizes de segurança da governança. Não foram encontradas vulnerabilidades de path traversal, vazamento de rotas públicas, desvios de autorização, bypass de validação de conteúdo ou orfandade de arquivos/registros. A correção anterior feita pelo Hermes para o bug de abertura no Pillow (`KeyError('MPO')`) foi inspecionada, validada e comprovada em runtime como correta e necessária.

Foram identificadas duas observações menores não-bloqueantes de qualidade de código (ordenação de imports na migração Alembic e aviso de deprecation de `Config` no Pydantic V2), documentadas na Seção 6.

---

## 2. Execução Independente de Testes e Lint

### 2.1. Testes Automatizados (Pytest)

- **Comando executado:**
  ```bash
  cd core && .venv/bin/python -m pytest app/tests -q
  ```
- **Resultado:**
  - **136 passed, 14 warnings in 57.84s**
  - **Testes novos (`app/tests/test_answer_images.py`):** 26 casos executados e aprovados (100%).
  - **Testes pré-existentes:** 110 casos executados e aprovados (0 regressões).

- **Execução detalhada dos testes novos (`test_answer_images.py`):**
  ```bash
  cd core && .venv/bin/python -m pytest app/tests/test_answer_images.py -v
  ```
  - `test_owner_uploads_valid_png_with_correct_metadata` -> PASSED
  - `test_owner_uploads_valid_jpeg` -> PASSED
  - `test_admin_can_upload` -> PASSED
  - `test_upload_to_missing_answer_returns_404` -> PASSED
  - `test_other_professor_cannot_upload` -> PASSED
  - `test_upload_without_token_returns_401` -> PASSED
  - `test_class_assessment_requires_active_link` -> PASSED
  - `test_forged_image_content_type_is_rejected[random-bytes]` -> PASSED
  - `test_forged_image_content_type_is_rejected[pdf]` -> PASSED
  - `test_forged_image_content_type_is_rejected[executable]` -> PASSED
  - `test_declared_type_diverging_from_content_is_rejected` -> PASSED
  - `test_real_gif_is_rejected_even_when_declared_as_png` -> PASSED
  - `test_empty_or_missing_file_is_rejected` -> PASSED
  - `test_oversized_upload_rejected_by_content_length` -> PASSED
  - `test_oversized_upload_rejected_while_streaming` -> PASSED
  - `test_adversarial_filename_is_metadata_only` -> PASSED
  - `test_sanitize_original_filename` -> PASSED
  - `test_unavailable_storage_dir_leaves_no_record` -> PASSED
  - `test_failure_finalizing_file_leaves_no_record_and_no_file` -> PASSED
  - `test_commit_failure_removes_stored_file` -> PASSED
  - `test_owner_downloads_original_bytes` -> PASSED
  - `test_other_professor_cannot_download_or_list` -> PASSED
  - `test_list_returns_newest_first` -> PASSED
  - `test_images_are_never_public` -> PASSED
  - `test_upload_does_not_create_correction_job` -> PASSED
  - `test_images_module_has_no_ocr_or_correction_references` -> PASSED

### 2.2. Linter (Ruff)

- **Comando executado:**
  ```bash
  cd core && .venv/bin/ruff check --config ../ruff.toml app
  ```
- **Resultado:**
  - `All checks passed!` (0 erros no pacote `app`).

---

## 3. Inspeção Crítica de Segurança

| Dimensão de Segurança | Veredito | Evidência e Análise |
|---|---|---|
| **Path Traversal** | **CONFIRMADO SEGURO** | **Arquivo:Linha:** `core/app/routers/images.py:178` (`storage_filename = f"{uuid.uuid4()}.{extension}"`).<br>O nome do arquivo no disco é exclusivamente um UUIDv4 com extensão derivada do formato detectado internamente pelo Pillow. O nome enviado pelo cliente (`upload.filename`) é higienizado (`images.py:109-112`) e salvo **apenas** na coluna do banco de dados `AnswerImage.original_filename` (`models.py:272`). Nunca é interpolado em chamadas de I/O (`open`, `Path`, `os.*`).<br>Além disso, o endpoint de download (`images.py:287`) aplica defesa em profundidade: `path = (storage_dir / image.storage_filename).resolve(); if path.parent != storage_dir or not path.is_file(): raise HTTPException(404)`. Testes adversariais com sequências `../../../etc/passwd` e caracteres de controle comprovaram que nenhum arquivo vaza do diretório autorizado. |
| **Autorização e Vínculo** | **CONFIRMADO SEGURO** | **Arquivo:Linha:** `core/app/routers/images.py:82-95` (`_get_authorized_answer`).<br>Todos os 3 endpoints (`POST /v1/answers/{id}/images`, `GET /v1/answers/{id}/images`, `GET /v1/answer-images/{id}/download`) invocam `_get_authorized_answer`, que reaplica estritamente `_get_owned_assessment` e `require_assessment_mutation`.<br>- Usuário não autenticado: HTTP 401.<br>- Professor não dono da avaliação: HTTP 403.<br>- Avaliação vinculada a turma (`class_group_id`): exige vínculo docente ativo (`ProfessorClassLink`), retornando 403 caso ausente.<br>Nenhum caminho de bypass identificado. |
| **Validação de Conteúdo Real e Bug MPO** | **CONFIRMADO SEGURO** | **Arquivo:Linha:** `core/app/routers/images.py:51-58, 119-138`.<br>A validação do arquivo não confia no `Content-Type` HTTP nem na extensão declarada. O arquivo é analisado pelo Pillow via `Image.open(path, formats=_OPEN_FORMATS)` com `img.verify()` e captura de `DecompressionBombWarning`. Arquivos não-imagem com cabeçalhos forjados (binários aleatórios, PDFs, executáveis MZ) falham na verificação e retornam HTTP 422.<br>**Avaliação da correção do bug MPO pelo Hermes:** No Pillow 12.x, passar `"MPO"` no parâmetro `formats` de `Image.open` levanta `KeyError('MPO')` porque MPO não é um plugin de abertura registrado pelo nome em `Image.OPEN` (é aberto via plugin JPEG e identificado dinamicamente). A separação implementada entre `_OPEN_FORMATS = ["JPEG", "PNG"]` (para `Image.open`) e `_ALLOWED_FORMATS = {"JPEG": ..., "MPO": ..., "PNG": ...}` é **correta, completa e sem regressão**, permitindo fotos reais de celulares (iPhone/Android que usam marcadores MPO) serem validadas e mapeadas para `image/jpeg` sem falhas. |
| **Limite de Tamanho** | **CONFIRMADO SEGURO** | **Arquivo:Linha:** `core/app/routers/images.py:206-215, 161-167`.<br>Proteção em duas camadas:<br>1. *Defesa prévia:* recusa imediata com HTTP 413 se `Content-Length > 10MB + 64KB` antes de ler o corpo ou alocar em disco.<br>2. *Defesa em streaming:* durante a leitura em chunks de 64KB (`_CHUNK_SIZE`), a contagem cumulativa interrompe o processamento com HTTP 413 assim que atinge o limite, e a cláusula `finally` remove o arquivo temporário parcial (`tmp_path.unlink()`). Nenhum arquivo excessivo é gravado. |
| **Registros Órfãos / Arquivos Soltos** | **CONFIRMADO SEGURO** | **Arquivo:Linha:** `core/app/routers/images.py:158-185, 238-245`.<br>Garante atomicidade em caso de falhas:<br>- Falha na decodificação ou validação: o arquivo `.part` temporário é deletado no `finally`.<br>- Falha na finalização (`os.replace`): o arquivo temporário é deletado e erro 500 é retornado.<br>- Falha no banco (`db.commit()`): o bloco `except` executa `db.rollback()`, deleta o arquivo em disco via `(_storage_dir() / storage_filename).unlink(missing_ok=True)` e lança HTTP 500.<br>- Downgrade de migração: `d5e3a7c19f42` recusa o downgrade com `RuntimeError` se a tabela contiver linhas, impedindo a perda de rastreabilidade de arquivos armazenados. |
| **Exposição Pública de Arquivos** | **CONFIRMADO SEGURO** | **Arquivo:Linha:** `core/app/main.py:73-80`.<br>Nenhum `StaticFiles` ou `Mount` de arquivos estáticos está registrado. O único caminho de acesso é o endpoint autenticado `GET /v1/answer-images/{id}/download`.<br>O schema público `AnswerImageOut` (`schemas.py:161`) **não expõe** o campo `storage_filename`. O endpoint de download retorna os headers `X-Content-Type-Options: nosniff` e `Cache-Control: private, no-store`. Caso o arquivo físico esteja ausente, o erro retornado é uma mensagem genérica sem vazar caminhos do servidor. |
| **OCR e Correção Automática** | **CONFIRMADO (ZERO)** | **Arquivo:Linha:** `core/app/routers/images.py` e `core/app/tests/test_answer_images.py:420-448`.<br>Não há qualquer chamada, import ou referência a OCR, Tesseract, IA, `CorrectionJob`, `AIExecution` ou `BackgroundTasks`. O upload é estritamente de recebimento e persistência. |
| **Privacidade de Logs** | **CONFIRMADO SEGURO** | **Arquivo:Linha:** `core/app/routers/images.py:154, 181, 213, 243, 247-254, 289`.<br>Os logs registram unicamente: `correlation_id`, `answer_id`, `image_id`, `user_id`, `content_type`, `size_bytes`, `stage` e `reason`. Nunca registram bytes da imagem, caminhos no disco ou o `original_filename` fornecido pelo cliente. |

---

## 4. Teste Real de Integração HTTP com PostgreSQL Isolado

Conforme facultado no item 5 das instruções, foi executado um teste de ponta a ponta com servidor HTTP real (`uvicorn`) e banco de dados PostgreSQL isolado.

- **Banco isolado criado para o teste:** `av_s06b_review_agy_20261014`
- **Bancos protegidos:** `avalia_dev` e `avalia_apresentacao_demo_20261002` **não foram tocados**.
- **Aplicação de Migrações (Alembic):**
  - Migração de `e1b02279b1a5` até `d5e3a7c19f42` aplicada com sucesso (`alembic upgrade head`).
  - Teste de downgrade em banco vazio: reverteu com sucesso.
  - Re-upgrade para `head`: concluído com sucesso.
  - Teste de recusa de downgrade com registros existentes: tentou `alembic downgrade -1` com 1 registro em `answer_images` -> abortou com `RuntimeError: answer_images contém registros; downgrade recusado...` (código de saída 1).
- **Testes HTTP reais executados contra o servidor:**
  1. `POST /v1/auth/login` -> **HTTP 200** (autenticação de professor)
  2. `POST /v1/answers/{id}/images` (upload de PNG válido) -> **HTTP 201**
     - Retorno: `id`, `answer_id`, `original_filename`, `content_type: image/png`, `size_bytes: 181`, `sha256_hash`, `uploaded_by_id`. O campo `storage_filename` não foi exposto.
  3. `GET /v1/answers/{id}/images` (listagem de imagens) -> **HTTP 200**
  4. `GET /v1/answer-images/{id}/download` (download com token) -> **HTTP 200**
     - Conteúdo binário recebido idêntico ao original; headers `content-type: image/png` e `x-content-type-options: nosniff` confirmados.
  5. `GET /v1/answer-images/{id}/download` (download anônimo) -> **HTTP 401**
  6. `POST /v1/answers/{id}/images` (upload forjado com texto fingindo ser JPEG) -> **HTTP 422**
- **Encerramento do ambiente de teste:**
  - O banco de dados `av_s06b_review_agy_20261014` foi dropado (`dropdb`) logo após a finalização dos testes.
  - O diretório temporário de armazenamento em disco foi removido.
  - A integridade dos bancos locais pré-existentes foi verificada e preservada.

---

## 5. Avaliação dos Critérios de Aceite da Sprint (AC-01 a AC-10)

| ID | Critério | Situação | Observações |
|---|---|---|---|
| **AC-01** | Upload de imagem válida (JPEG/PNG) pelo professor dono | **Aprovado** | Coberto por testes unitários e teste HTTP real. |
| **AC-02** | Rejeição (403) para professor sem vínculo/propriedade | **Aprovado** | Validado em `test_other_professor_cannot_upload` e `test_class_assessment_requires_active_link`. |
| **AC-03** | Rejeição (401) sem autenticação | **Aprovado** | Validado em `test_upload_without_token_returns_401` e teste HTTP real. |
| **AC-04** | Rejeição (422) de arquivo não-imagem com Content-Type forjado | **Aprovado** | Validado com bytes aleatórios, PDF e executável PE. |
| **AC-05** | Rejeição (413) de arquivo acima do limite de tamanho antes de gravação completa | **Aprovado** | Validado em camada de header e em streaming chunked. |
| **AC-06** | Nome adversarial não causa path traversal | **Aprovado** | Nome em disco usa UUID do servidor; original é puro metadado sanitizado. |
| **AC-07** | Falha de armazenamento não deixa registro órfão | **Aprovado** | Rollback e exclusão de arquivo testados em falhas simuladas de I/O e DB commit. |
| **AC-08** | Recuperação restrita ao dono/vinculado ou admin | **Aprovado** | Validado em download e listagem; 403 para terceiros. |
| **AC-09** | Nenhuma imagem exposta por URL pública / rota estática | **Aprovado** | Sem mounts estáticos; download exige token JWT. |
| **AC-10** | Zero OCR e zero disparo de correção automática | **Aprovado** | Nenhum job criado; análise sintática confirma ausência de dependências de IA/OCR. |

---

## 6. Defeitos e Observações Encontradas

Nenhum defeito impeditivo ou de vulnerabilidade de segurança foi encontrado. Registram-se duas observações de manutenção de código:

1. **Ordenação de imports na migração Alembic (`core/alembic/versions/d5e3a7c19f42_add_answer_images.py:11:1`):**
   - *Descrição:* O linter `ruff` aponta `I001 [*] Import block is un-sorted or un-formatted` na migração nova (ocorrência comum também presente nas migrações históricas do projeto).
   - *Sugestão de correção:* Ajustar a ordem dos imports:
     ```python
     from typing import Sequence, Union

     import sqlalchemy as sa
     from alembic import op
     ```
2. **Uso de classe interna `Config` no Pydantic V2 (`core/app/schemas.py:161`):**
   - *Descrição:* `AnswerImageOut` utiliza `class Config: from_attributes = True`, seguindo o padrão pré-existente nos demais schemas do arquivo, o que gera o aviso `PydanticDeprecatedSince20: Support for class-based config is deprecated, use ConfigDict instead`.
   - *Sugestão de correção (para futura padronização do módulo schemas):* Migrar gradualmente para `model_config = ConfigDict(from_attributes=True)`.

---

## 7. Declaração de Conformidade com Limites de Governança

- **Operações Git:** Não foi executado nenhum `git add`, `git stage`, `git commit`, `git push`, `git merge`, nem criação de branches ou worktrees.
- **Bancos de dados:** Os bancos de dados `avalia_dev` e `avalia_apresentacao_demo_20261002` **não sofreram nenhuma conexão ou alteração**. O teste de integração utilizou um banco temporário exclusivo (`av_s06b_review_agy_20261014`) que já foi completamente removido (`dropdb`).
- **Código de produção:** O código de produção não foi alterado durante esta revisão independente.

### Estado atual do Git (`git status --short`)

```
 M .gitignore
 M core/app/config.py
 M core/app/main.py
 M core/app/models.py
 M core/app/schemas.py
 M core/requirements.txt
 M docs/governance/registers/decisions.md
?? core/alembic/versions/d5e3a7c19f42_add_answer_images.py
?? core/app/routers/images.py
?? core/app/tests/test_answer_images.py
?? docs/governance/evidence/AV-S06B/
?? docs/governance/evidence/resumo_sessao_2026-10-13_avalia.txt
?? docs/governance/snapshots/snapshot_EXEC-2026-10-14-01_abertura_av-s06b.md
?? docs/governance/sprints/sprint_AV-S06B_recebimento_armazenamento_imagens.md
```
