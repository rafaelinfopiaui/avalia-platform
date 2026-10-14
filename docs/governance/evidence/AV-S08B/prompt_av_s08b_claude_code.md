# Tarefa: implementar AV-S08B — transcrição manual e confirmação humana

Repo: /Users/rafaeloliveira/Projeto Estágio/avalia-plataform
Branch (já criada e em checkout): feat/av-s08b-transcricao-manual (a partir de main e8b0864)

NÃO faça commit/push/stage. NÃO toque avalia_dev nem avalia_apresentacao_demo_20261002.
NÃO implemente OCR nem transcrição automática. NÃO implemente reabertura pós-confirmação
(fora de escopo desta fatia — decisão DP-2 já fechada: confirmação é definitiva).
Grave seu relatório em local-nao-versionado/claude_report_av_s08b.md (git-ignored).

## Contexto obrigatório — LEIA ANTES DE CODAR
Leia INTEGRALMENTE, nesta ordem:
1. docs/governance/evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md
   (plano técnico completo, já aprovado por Rafael via DEC-AV-040 — contrato dos
   endpoints, modelo de dados, nomenclatura, regras de concorrência, todos os
   critérios de aceite ACD-01 a ACD-17)
2. docs/governance/sprints/sprint_AV-S08B_transcricao_manual_confirmacao_humana.md
   (mapa de impacto, DoD)
3. docs/governance/evidence/AV-S08B/revisao_plano_transcricao_manual_antigravity.md
   e revisao_plano_transcricao_manual_antigravity_v2_concorrencia.md (os 2 pareceres
   do Antigravity sobre o plano — contêm recomendações técnicas específicas de
   implementação, inclusive um exemplo de código SQLAlchemy para o UPDATE condicional
   do lock otimista, na seção "Recomendações Técnicas" do segundo parecer)
4. core/app/models.py (classes Answer, AnswerImage, CorrectionJob, HumanReview,
   AuditEvent, Rubric — para ver o padrão real de Rubric.version)
5. core/app/main.py (endpoints request_correction, review_correction,
   create_text_answer, create_image_answer, list_image_answers — para seguir o
   MESMO estilo/padrão de código já usado no projeto)
6. core/app/routers/academic.py (require_assessment_mutation, _get_owned_assessment
   não está aqui, está em main.py)
7. core/app/tests/test_image_answers_listing.py (padrão de teste já usado na fatia
   anterior — estrutura de fixtures, client, db_session)

## O que fazer (siga o plano técnico à risca — é a fonte de verdade do contrato)

### Backend (core/)
1. Migração Alembic (nova revision) adicionando a `answers`:
   - manual_transcription_draft: Text, nullable
   - transcription_confirmed_by_id: String, FK users.id, nullable
   - transcription_confirmed_at: DateTime, nullable
   - transcription_version: Integer, NOT NULL, default 0
   Mudança puramente aditiva — nenhuma coluna existente alterada, nenhum backfill
   necessário (default 0 cobre linhas existentes).
2. Atualize core/app/models.py (classe Answer) com os 4 campos.
3. Atualize core/app/schemas.py: AnswerOut ganha manual_transcription_draft
   (Optional[str] = None) e transcription_version (int).
4. Dois novos endpoints em core/app/main.py:
   - PATCH /v1/answers/{answer_id}/manual-transcription/draft
   - POST /v1/answers/{answer_id}/manual-transcription/confirm
   Payload de ambos: {"text": str, "expected_version": int}.
   Response: AnswerWithImagesOut.
   Autorização: _get_owned_assessment + require_assessment_mutation (MUTAÇÃO,
   diferente do endpoint de leitura de DEBT-AV-014 — exige vínculo ativo de turma
   quando houver).
   Regras exatas de erro (ver plano §3.3 e §6 para o detalhamento completo):
   - 404: answer/question/assessment inexistente
   - 403: não-dono ou sem vínculo ativo
   - 401: sem token
   - 422 ANSWER_NOT_IMAGE_SOURCE: resposta é source=TEXT
   - 422 ANSWER_TEXT_REQUIRED: confirm com texto vazio/só espaços (draft com texto
     vazio é PERMITIDO — serve para limpar rascunho)
   - 409 TRANSCRIPTION_ALREADY_CONFIRMED: draft ou confirm em resposta já
     confirmada, SALVO confirm idempotente com texto idêntico ao já confirmado
     E expected_version correta (nesse caso 200, sem novo AuditEvent)
   - 409 TRANSCRIPTION_VERSION_CONFLICT: expected_version não bate com
     transcription_version atual — implemente com UPDATE condicional
     (WHERE id=:id AND transcription_version=:expected_version) verificando
     rowcount, dentro de uma transação, exatamente como o exemplo de código do
     parecer v2 do Antigravity. Corpo da resposta de conflito inclui o estado
     atual (rascunho/texto/versão) para o cliente decidir.
   draft: NÃO altera text nem transcription_status. transcription_version += 1
   em todo save bem-sucedido. AuditEvent (resource_type="Answer",
   action="manual_transcription_draft_saved", before_json/after_json com o texto)
   a cada save.
   confirm: text = payload.text; transcription_status = TRANSCRICAO_CONFIRMADA;
   transcription_confirmed_by_id = user.id; transcription_confirmed_at = now();
   transcription_version += 1; manual_transcription_draft limpo (None);
   AuditEvent (action="manual_transcription_confirmed"). NÃO cria CorrectionJob.
   NÃO chama request_correction. Isso é crítico — nenhuma linha de código nova
   deve invocar request_correction nem criar CorrectionJob a partir destes
   2 endpoints.
5. list_image_answers (já existente, DEBT-AV-014) deve continuar funcionando sem
   alteração de comportamento — o fato de AnswerOut ganhar 2 campos novos é
   aditivo e automático via herança de AnswerWithImagesOut.

### Frontend (frontend/)
1. frontend/src/types.ts: AnswerWithImages ganha manual_transcription_draft?
   (string | null) e transcription_version (number).
2. frontend/src/services/api.ts: duas novas funções —
   saveManualTranscriptionDraft(answerId, text, expectedVersion) e
   confirmManualTranscription(answerId, text, expectedVersion), chamando os
   2 endpoints novos.
3. frontend/src/pages/ImageAnswerPage.tsx (ou um componente novo dedicado, à sua
   escolha dentro do espírito do plano): para cada resposta por imagem persistida
   listada, ofereça uma área de "transcrição manual" com:
   - campo de texto (textarea) inicializado com manual_transcription_draft (se
     houver) ou vazio;
   - botão "Salvar rascunho" (chama draft, mantém a tela editável);
   - botão "Confirmar transcrição", que ANTES de confirmar mostra a imagem e o
     texto lado a lado para revisão, com aviso explícito de que a confirmação é
     definitiva nesta versão (requisito de UX do plano §4/§13, decisão DP-2) —
     pode ser um passo de confirmação em 2 cliques ou um modal, à sua escolha,
     desde que o aviso seja visível antes da ação irreversível;
   - after a resposta já confirmada (transcription_status=TRANSCRICAO_CONFIRMADA),
     a área de edição desaparece/desabilita — mostra o texto confirmado como
     somente leitura, com indicação de quem confirmou e quando;
   - mensagens de erro compreensíveis para 409 (conflito de versão — ex. "este
     texto foi alterado em outra sessão; recarregue para ver a versão mais
     recente") e para os demais erros;
   - manter visualização autenticada da imagem já existente (botão Visualizar).
   Não precisa reaproveitar exatamente o componente SentAnswer existente — pode
   criar um componente novo para a área de transcrição, desde que a tela
   continue coerente.

### Testes (core/app/tests/)
Crie core/app/tests/test_manual_transcription.py cobrindo TODOS os ACD-01 a
ACD-17 do plano (lista completa na seção §11). Preste atenção especial a:
- ACD-15/ACD-16: concorrência REAL contra PostgreSQL (duas conexões/threads
  simultâneas, não chamadas sequenciais simulando concorrência) — use o mesmo
  padrão de teste de race condition já usado em AV-S04 para
  delete_question×create_answer, se você encontrar esse teste no histórico do
  repo (git log/grep por "concorrência" ou "race" nos testes existentes), ou
  um padrão equivalente com threading real contra o mesmo banco de teste.
- ACD-17: transcription_version nunca retrocede nem pula com chamada rejeitada.
- Regressão: toda a suíte existente (171 testes) deve continuar passando.

## Ao terminar, no relatório (local-nao-versionado/claude_report_av_s08b.md)
- arquivos alterados/criados;
- mapeamento ACD-01 a ACD-17 ao que foi feito, com nome do teste que cobre cada um;
- comandos para rodar (pytest, ruff, npm run build) — execute-os você mesmo e
  reporte o resultado real, não presuma;
- decisões de implementação tomadas onde o plano deixou espaço (ex. ordem exata
  de verificação de status vs. versão no confirm);
- quaisquer dúvidas ou desvios do plano, com justificativa.
