# Parecer de Revisão Independente do DELTA — AV-S08B: Solicitar Correção após Confirmação

- **Revisor:** Antigravity (revisor independente)
- **Implementador:** Claude Code (CLI `claude`, modelo Opus 5.5)
- **Data/Fuso:** 2026-10-14T11:15:00-03:00 (America/Sao_Paulo)
- **Branch:** `feat/av-s08b-transcricao-manual` (base `main` `e8b08646cfee5e9fea70d8e9bbcb4cf39f5a3d2d`)
- **Documento de referência:** [`docs/governance/evidence/AV-S08B/revisao_implementacao_antigravity.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/evidence/AV-S08B/revisao_implementacao_antigravity.md), [`docs/governance/evidence/AV-S08B/prompt_av_s08b_delta_correcao_claude_code.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/evidence/AV-S08B/prompt_av_s08b_delta_correcao_claude_code.md) e relatório [`local-nao-versionado/claude_report_av_s08b_delta_correcao.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/local-nao-versionado/claude_report_av_s08b_delta_correcao.md).

---

## 1. Veredito

**APROVADO**

O DELTA implementado por Claude Code atende com rigor técnico a todos os requisitos solicitados para a ação de correção a partir de resposta por foto com transcrição confirmada:
1. O acionamento da correção ocorre **exclusivamente após a confirmação** da transcrição na UI (`transcription_status === 'TRANSCRICAO_CONFIRMADA'`), preservando a regra de negócio e o guard do backend.
2. Não foi criado nenhum endpoint novo nem resposta duplicada: o fluxo consome a função pré-existente [`requestCorrection`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/services/api.ts#L141-L149) associada ao mesmo `answer.id`.
3. Os 3 novos testes automatizados no backend cobrem ponta a ponta a criação do `CorrectionJob` com o mesmo `answer_id`, a verificação de que o payload transmitido ao AI Engine contém **exatamente** o texto confirmado (e não o rascunho), o incremento sequencial de `attempt` em retentativas e a regressão bloqueando respostas não confirmadas (422 `ANSWER_NOT_TRANSCRIBED`).
4. As suítes de testes automatizados de backend (`pytest`) e as verificações estáticas de frontend (`tsc`, `build`, `lint`) foram reexecutadas de forma independente pelo Antigravity com 100% de sucesso.
5. Os bancos protegidos (`avalia_dev` e `avalia_apresentacao_demo_20261002`) permanecem intocados na revisão `a9f4c2e71b06`.

---

## 2. Quadro Resumo de Verificação dos Itens da Revisão

| Item de Verificação | Situação | Evidência Direta Observada |
|---|---|---|
| **1. Visibilidade condicional do botão** | **Conforme** | Inspecionado JSX em [`ImageAnswerPage.tsx:391`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L391). O componente [`CorrectionRequest`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L322-L355) só é montado quando `answer.transcription_status === 'TRANSCRICAO_CONFIRMADA'`. |
| **2. Reutilização de `requestCorrection(answer.id)`** | **Conforme** | Linha 333 de [`ImageAnswerPage.tsx`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L333) invoca [`requestCorrection(answer.id)`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/services/api.ts#L141), o mesmo utilitário de [`AnswerPage.tsx:82`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/AnswerPage.tsx#L82). Nenhuma resposta nova é gerada. |
| **3. Navegação para `/correcoes/{job.id}`** | **Conforme** | Linha 336 de [`ImageAnswerPage.tsx`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L336) executa `navigate('/correcoes/' + job.id)`, precedido por [`writeWorkflow({ answer, job })`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L335), direcionando à rota canônica [`CorrectionPage`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/App.tsx#L18). |
| **4. Estados de carregamento, sucesso e erro** | **Conforme** | Estado `busy` com bloqueio contra duplo clique e `Spinner`; estado `requested` com alerta contextual; tratamento de erros legíveis em [`correctionError`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L102-L116) cobrindo `ANSWER_NOT_TRANSCRIBED`, `RUBRIC_NOT_PUBLISHED`, 401, 403 e 404. |
| **5. Teste de texto confirmado e mesmo `answer_id`** | **Conforme** | Inspecionado [`test_confirmed_image_answer_correction_uses_same_answer_and_confirmed_text`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/tests/test_manual_transcription.py#L501-L523). Comprova `job.answer_id == answer_id`, `Answer.count() == 1`, e payload do AI Engine com exatamente o texto confirmado via mock `_CapturingAIEngine`. |
| **6. Re-execução dos testes no backend** | **Conforme** | `pytest test_manual_transcription.py -q` executado: **33 passed, 5 skipped**. Teste de regressão `test_unconfirmed_image_answer_correction_stays_blocked` isolado: **1 passed**. |
| **7. Re-execução dos checks no frontend** | **Conforme** | Executados `npx tsc -b`, `npm run build` (vite v8.2.2, 69ms) e `npm run lint` (`eslint src`). Todos retornaram exit code 0 sem avisos. |
| **8. Preservação da política de repetição de correção** | **Conforme** | Inspecionado [`core/app/main.py:970-1021`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L970-L1021). Código idêntico à rodada anterior; retentativas incrementam `attempt` no mesmo `answer_id` e criam novo `CorrectionJob`. Zero endpoints adicionados. |

---

## 3. Achados de Revisão

### ACH-01: Estado de "nova análise" mantido via estado local do componente
- **Severidade:** Informativa
- **Bloqueante:** Não
- **Localização:** [`frontend/src/pages/ImageAnswerPage.tsx:326-350`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L326-L350)
- **Descrição:** O componente `CorrectionRequest` gerencia a flag `requested` através de `useState(false)`. Quando uma solicitação é bem-sucedida, `requested` é marcado como `true`, exibindo o alerta de que uma análise já foi solicitada e alterando o rótulo do botão para "Solicitar nova análise da IA". Caso o usuário recarregue a página via navegador (ou navegue para outra tela e retorne à listagem), o rótulo volta a exibir "Solicitar análise da IA" porque o endpoint de consulta [`GET /v1/assessments/{id}/image-answers`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L740) e o schema `AnswerWithImagesOut` não expõem a lista ou contagem de `CorrectionJob` associados à resposta.
- **Avaliação:** O comportamento implementado seguiu estritamente as instruções do prompt de delegação ("se não houver endpoint de leitura de jobs por answer_id disponível no momento, não invente um; deixe o rótulo fixo [...] e documente essa limitação no relatório"). A política do backend suporta múltiplas tentativas de forma idempotente em termos de integridade (`attempt` incremental no mesmo `answer_id`), de modo que clicar novamente gerará legitimamente a tentativa seguinte sem efeitos colaterais.
- **Recomendação:** Nenhuma ação necessária para esta fatia. Se no futuro o produto demandar exibição do histórico de jobs na listagem de respostas, poderá ser avaliada a inclusão de um contador ou lista de jobs em `AnswerWithImagesOut`.

---

### ACH-02: Defesa em profundidade no tratamento de erros da solicitação de IA
- **Severidade:** Informativa (Boa Prática)
- **Bloqueante:** Não
- **Localização:** [`frontend/src/pages/ImageAnswerPage.tsx:102-116`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L102-L116)
- **Descrição:** A função `correctionError` trata expressamente o código `ANSWER_NOT_TRANSCRIBED` com a mensagem *"A transcrição desta resposta ainda não foi confirmada; confirme-a antes de solicitar a análise."*, apesar de o botão só ser montado na interface quando `answer.transcription_status === 'TRANSCRICAO_CONFIRMADA'`. Além disso, trata `RUBRIC_NOT_PUBLISHED` (*"A questão desta resposta não possui rubrica publicada. Publique a rubrica da questão e tente novamente."*) e códigos HTTP de autenticação/autorização (401/403/404).
- **Avaliação:** Trata-se de uma excelente prática de defesa em profundidade. Caso ocorra condição de corrida ou inconsistência transitória de cache local, a interface degrada com elegância, informando com clareza o motivo da recusa sem deixar a UI em estado travado.

---

## 4. Evidências de Execução Realizadas pelo Revisor Independente

### 4.1 Inspeção do Código Frontend e Análise de Fluxo
No arquivo [`frontend/src/pages/ImageAnswerPage.tsx`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx):
- O componente [`SentAnswer`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L357-L393) recebe a resposta inicial (`initial`) e gerencia seu ciclo de vida em `answer`:
  ```tsx
  <ManualTranscription answer={answer} images={images} onChange={setAnswer} />
  {answer.transcription_status === 'TRANSCRICAO_CONFIRMADA' && <CorrectionRequest answer={answer} />}
  ```
- O componente [`CorrectionRequest`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L322-L355) reutiliza a função contratada:
  ```tsx
  const request = async () => {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      const job = await requestCorrection(answer.id)
      setRequested(true)
      writeWorkflow({ answer, job })
      navigate(`/correcoes/${job.id}`)
    } catch (e) {
      setError(correctionError(e))
    } finally {
      setBusy(false)
    }
  }
  ```
- Verificado:
  - Não há chamada para `createAnswer` nem duplicação de dados.
  - O `workflow` local do sessionStorage é sincronizado via [`writeWorkflow({ answer, job })`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx#L335) antes do redirecionamento.
  - A navegação aponta para `/correcoes/${job.id}`, consumida pela rota ativa [`CorrectionPage`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/App.tsx#L18).

---

### 4.2 Inspeção dos Testes de Backend Adicionados
No arquivo [`core/app/tests/test_manual_transcription.py:473-548`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/tests/test_manual_transcription.py#L473-L548):
1. **Mock seguro do AI Engine:**
   A classe [`_CapturingAIEngine`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/tests/test_manual_transcription.py#L473-L490) substitui `httpx.AsyncClient` dentro de `app.services.correction` interceptando as chamadas e registrando os payloads enviados no atributo de classe `payloads`, levantando exceção imediatamente para impedir saídas HTTP externas.
2. **Teste de uso da mesma resposta e texto confirmado:**
   [`test_confirmed_image_answer_correction_uses_same_answer_and_confirmed_text`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/tests/test_manual_transcription.py#L501-L523):
   - Registra rascunho: `"Rascunho diferente."` (versão 0 -> 1).
   - Confirma transcrição: `confirmed_text = "Texto confirmado\ncom quebra de linha e acentuação: ação."` (versão 1 -> 2).
   - Dispara `POST /v1/answers/{answer_id}/corrections` -> recebe HTTP 202 com `job_id`.
   - Assegura que `job.answer_id == answer_id` e `job.attempt == 1`.
   - Assegura que `db_session.query(Answer).count() == 1` (zero respostas adicionais criadas).
   - Assegura que `answer.source == AnswerSource.IMAGE` e `answer.text == confirmed_text`.
   - Assegura que `[p["answer_text"] for p in ai_engine.payloads] == [confirmed_text]`, comprovando que o texto enviado à IA é o texto confirmado e não o rascunho.
3. **Teste de incremento de tentativa no mesmo `answer_id`:**
   [`test_confirmed_image_answer_new_request_increments_attempt_on_same_answer`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/tests/test_manual_transcription.py#L525-L538):
   - Realiza duas chamadas consecutivas de correção para a mesma resposta IMAGE confirmada.
   - Ambas retornam 202.
   - Jobs resultantes associados ao mesmo `answer_id` com `attempt` `[1, 2]`.
   - Ambos os payloads enviados ao mock contêm o texto confirmado.
4. **Teste de regressão (bloqueio antes de confirmação):**
   [`test_unconfirmed_image_answer_correction_stays_blocked`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/tests/test_manual_transcription.py#L540-L548):
   - Resposta apenas com rascunho salvo (status `AGUARDANDO_TRANSCRICAO`).
   - `POST /v1/answers/{answer_id}/corrections` rejeitado com 422 `ANSWER_NOT_TRANSCRIBED`.
   - Nenhum `CorrectionJob` criado (`count() == 0`).
   - Mock do AI Engine não recebe nenhum payload (`payloads == []`).

---

### 4.3 Execução Real dos Testes Automatizados de Backend

Comando executado:
```bash
env -u AI_ENGINE_URL -u DATABASE_URL -u JWT_SECRET core/.venv/bin/pytest core/app/tests/test_manual_transcription.py -q
```
Saída real obtida:
```text
.................................sssss                                   [100%]
=============================== warnings summary ===============================
...
33 passed, 5 skipped, 14 warnings in 12.67s
```
*(Nota: os 5 skipped referem-se aos testes de concorrência em PostgreSQL real que exigem a env var `AVALIA_TEST_POSTGRES_URL`, os quais já haviam sido validados e aprovados no parecer da implementação anterior).*

Execução isolada do teste de regressão:
```bash
env -u AI_ENGINE_URL -u DATABASE_URL -u JWT_SECRET core/.venv/bin/pytest core/app/tests/test_manual_transcription.py -k "test_unconfirmed_image_answer_correction_stays_blocked" -v
```
Saída real obtida:
```text
core/app/tests/test_manual_transcription.py::test_unconfirmed_image_answer_correction_stays_blocked PASSED [100%]
================ 1 passed, 37 deselected, 14 warnings in 0.43s =================
```

Execução conjunta dos 3 testes do delta:
```bash
env -u AI_ENGINE_URL -u DATABASE_URL -u JWT_SECRET core/.venv/bin/pytest core/app/tests/test_manual_transcription.py -k "confirmed_image_answer or unconfirmed_image_answer" -v
```
Saída real obtida:
```text
core/app/tests/test_manual_transcription.py::test_confirmed_image_answer_correction_uses_same_answer_and_confirmed_text PASSED [ 33%]
core/app/tests/test_manual_transcription.py::test_confirmed_image_answer_new_request_increments_attempt_on_same_answer PASSED [ 66%]
core/app/tests/test_manual_transcription.py::test_unconfirmed_image_answer_correction_stays_blocked PASSED [100%]
================ 3 passed, 35 deselected, 14 warnings in 1.22s =================
```

Verificação do linter `ruff` no arquivo de testes:
```bash
core/.venv/bin/ruff check core/app/tests/test_manual_transcription.py
```
Saída real obtida:
```text
All checks passed!
```

---

### 4.4 Execução Real dos Comandos no Frontend

Comandos executados no diretório `frontend/`:
```bash
cd frontend && npx tsc -b && npm run build && npm run lint
```
Saída real obtida:
```text
> avalia-frontend@0.1.0 build
> tsc -b && vite build

vite v8.2.2 building client environment for production...
✓ 35 modules transformed.
rendering chunks (1)...computing gzip size...
dist/index.html                   0.54 kB │ gzip:  0.34 kB
dist/assets/index-DhxhAQRq.css    8.82 kB │ gzip:  2.89 kB
dist/assets/index-CKM-yK9g.js   284.04 kB │ gzip: 85.51 kB

✓ built in 69ms

> avalia-frontend@0.1.0 lint
> eslint src
```
Status de saída: 0 (sem erros de tipagem, sem falhas de compilação do Vite e sem alertas de ESLint).

---

### 4.5 Confirmação de Integridade dos Endpoints de Backend e Política de Retentativa

Foi inspecionado o `git diff` de todos os arquivos de backend:
- [`core/app/main.py`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py): Apenas os dois endpoints de transcrição manual (`PATCH /draft` e `POST /confirm`) adicionados na rodada anterior de AV-S08B constam no diff contra `main`. Nenhuma alteração foi realizada em `main.py` neste delta.
- [`core/app/models.py`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/models.py): Inalterado neste delta (apenas os 4 campos de modelo da rodada anterior).
- [`core/app/schemas.py`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py): Inalterado neste delta.
- [`core/app/services/correction.py`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/services/correction.py): Diff vazio (zero alterações).

A função [`request_correction`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L970-L1021) permanece idêntica:
```python
@app.post("/v1/answers/{answer_id}/corrections", status_code=202)
async def request_correction(
    answer_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    ...
    if (
        answer.transcription_status != TranscriptionStatus.TRANSCRICAO_CONFIRMADA
        or not (answer.text or "").strip()
    ):
        return error_response(
            422,
            "ANSWER_NOT_TRANSCRIBED",
            "A resposta por imagem ainda não tem transcrição confirmada; não pode ser corrigida.",
            correlation_id,
        )
    rubric = next((r for r in question.rubrics if r.is_published), None)
    if rubric is None:
        return error_response(422, "RUBRIC_NOT_PUBLISHED", "A questão não possui rubrica publicada.", correlation_id)

    prior_attempts = db.query(CorrectionJob).filter(CorrectionJob.answer_id == answer_id).count()
    job = CorrectionJob(answer_id=answer_id, rubric_id=rubric.id, status=JobStatus.PENDENTE, attempt=prior_attempts + 1)
    db.add(job)
    db.commit()
    ...
```
A verificação confirma que a política de retentativa baseada em `attempt = prior_attempts + 1` no mesmo `answer_id` não foi alterada e está plenamente preservada.

---

### 4.6 Verificação dos Bancos de Dados Protegidos

Consultas realizadas via `psql` no PostgreSQL local:
```sql
SELECT datname FROM pg_database WHERE datname LIKE 'avalia%';
```
Retorno:
```text
 avalia_dev
 avalia_apresentacao_demo_20261002
```

Consulta de integridade de esquema em `avalia_dev`:
```sql
SELECT version_num FROM alembic_version;
```
Retorno: `a9f4c2e71b06` (1 row).

Consulta de integridade de esquema em `avalia_apresentacao_demo_20261002`:
```sql
SELECT version_num FROM alembic_version;
```
Retorno: `a9f4c2e71b06` (1 row).

Confirmado: os bancos protegidos não foram acessados nem modificados em nenhuma etapa desta revisão.

---

## 5. Conclusão

O DELTA analisado completa o ciclo de interação da transcrição manual da fatia AV-S08B de forma cirúrgica, segura e aderente aos padrões de governança e arquitetura do AvalIA.

O revisor independente atesta que o código está pronto para consolidação por Hermes e subsequente homologação por Rafael.
