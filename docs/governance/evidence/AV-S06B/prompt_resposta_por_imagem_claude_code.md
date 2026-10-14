# Tarefa: implementar RESPOSTA POR IMAGEM (complemento AV-S06B) — AvalIA

Você está no checkout principal do repo `avalia-plataform`, na branch já criada e
com checkout feito: `feat/av-s06b-resposta-por-imagem`. NÃO crie worktree, NÃO
crie outra branch, NÃO faça git add/commit/push/merge. NÃO toque nos bancos
`avalia_dev` nem `avalia_apresentacao_demo_20261002`. Implementação local apenas.

## Leia primeiro, por completo (fonte da verdade)
- `docs/governance/evidence/AV-S06B/desenho_resposta_por_imagem.md` (v2 — o desenho
  aprovado; a seção 12 lista ajustes obrigatórios ACH-01..06 + extras)
- `docs/governance/evidence/AV-S06B/revisao_desenho_antigravity.md` (parecer)
- `docs/governance/sprints/sprint_AV-S06B_recebimento_armazenamento_imagens.md` §17
  (critérios de aceite ACI-01..ACI-09)
- `core/app/models.py` (Answer, AnswerImage, enums existentes p/ seguir o padrão)
- `core/app/main.py` (create_answer ~576; request_correction ~636; padrão de
  _get_owned_assessment / require_assessment_mutation / error_response / log_event)
- `core/app/routers/images.py` (funções de validação/gravação de imagem a REUSAR)
- `core/app/services/correction.py` (run_correction_job — defesa em profundidade)
- `core/app/schemas.py`, `frontend/src/types.ts`, `frontend/src/pages/` e o
  arquivo de API do frontend (padrão de chamadas)

## Direção de produto (DEC-AV-037) — NÃO desviar
A foto é a entrada inicial da resposta, SEM texto digitado/vazio/fictício.
Resposta por imagem nasce "aguardando transcrição"; correção BLOQUEADA até
transcrição confirmada. NÃO implemente OCR, transcrição simulada nem confirmação
fictícia — nesta fatia a resposta por imagem termina legitimamente aguardando
transcrição. Fluxo textual existente permanece inalterado em contrato. Preserve
DEC-AV-018 ("uma resposta de uma questão por foto"; reenvio permitido, sem
unicidade de foto nem proibição de reenvio).

## Backend — implementar exatamente conforme o desenho v2

1. Enums novos em models.py: `AnswerSource` (TEXT|IMAGE) e `TranscriptionStatus`
   (AGUARDANDO_TRANSCRICAO|TRANSCRICAO_CONFIRMADA), seguindo o padrão dos enums
   existentes (str, enum.Enum).
2. Modelo Answer: `text` -> nullable=True; adicionar `source` (default TEXT) e
   `transcription_status` (default TRANSCRICAO_CONFIRMADA). Adicionar
   CheckConstraint `(source='TEXT' AND text IS NOT NULL) OR (source='IMAGE')`.
3. Migração Alembic nova (down_revision = a cabeça atual d5e3a7c19f42): `text`
   nullable; colunas `source`/`transcription_status` com tipos ENUM nomeados do
   Postgres (siga a convenção de c4a8b2d91e37_add_academic_structure.py); backfill
   determinístico (todas as linhas existentes -> source=TEXT,
   transcription_status=TRANSCRICAO_CONFIRMADA); criar o CheckConstraint.
   Downgrade: recusar (RuntimeError) se houver linhas com text IS NULL; caso
   contrário remover constraint/colunas e voltar text para NOT NULL. Downgrade
   idempotente/seguro para os enums nomeados.
4. create_answer (textual): cria source=TEXT, transcription_status=
   TRANSCRICAO_CONFIRMADA. Validar que AnswerInput.text não é vazio/só espaços
   (ACH-02) — 422 claro se vazio.
5. Novo endpoint TRANSACIONAL em main.py (NÃO em images.py — ACH-05): 
   `POST /v1/answers/image` com parâmetros DECLARATIVOS do FastAPI
   (file: UploadFile = File(...), question_id: str = Form(...),
   student_name_fake: str = Form(...)) — NÃO reusar request.form(max_fields=1)
   (ACH-03). Ordem fail-fast (ACH + §7): autorização (require_role +
   _get_owned_assessment + require_assessment_mutation a partir da question_id) +
   student_name_fake não-vazio ANTES de gravar qualquer byte. Depois: reutilizar
   as funções de validação/gravação de `routers/images.py` (Pillow, limite 10 MiB
   = 10_485_760 bytes, nome UUID, escrita atômica temp->os.replace), criar
   Answer(source=IMAGE, text=NULL, transcription_status=AGUARDANDO_TRANSCRICAO) +
   AnswerImage, commit por último; se o commit falhar: rollback + unlink do
   arquivo (sem órfãos). Retorno: schema composto AnswerWithImagesOut (AnswerOut +
   images: list[AnswerImageOut]).
6. Guard de correção (§6) em request_correction (main.py): logo após obter a
   answer, se `answer.transcription_status != TRANSCRICAO_CONFIRMADA` ou
   `not (answer.text or "").strip()` -> error_response(422,
   "ANSWER_NOT_TRANSCRIBED", "A resposta por imagem ainda não tem transcrição
   confirmada; não pode ser corrigida.", correlation_id). Use o helper
   error_response (padrão do projeto).
7. Defesa em profundidade (ACH-04) em run_correction_job (services/correction.py):
   se answer.text for nulo/vazio, marcar o job como FALHA com mensagem explícita
   ANTES de chamar o AI Engine (não deixar o AI Engine receber answer_text None).
8. schemas.py: AnswerOut.text -> Optional[str] = None; adicionar source e
   transcription_status; criar AnswerWithImagesOut. NÃO exponha storage_filename.
9. NÃO introduza idempotência/deduplicação no novo endpoint (política de reenvio
   não aprovada). NÃO adicione referência a OCR/correção em routers/images.py (há
   teste AST que proíbe — ACH-05).

## Frontend — interface de resposta por imagem (ACI-08)
- types.ts: Answer.text?: string | null; source?: 'TEXT'|'IMAGE';
  transcription_status?: 'AGUARDANDO_TRANSCRICAO'|'TRANSCRICAO_CONFIRMADA'.
- Tela/seção para o professor: seleção manual de avaliação->questão->aluno
  (nome fictício) e envio de foto JPEG/PNG até 10 MiB; usar o novo endpoint.
- Listar e visualizar imagens via download autenticado (nunca URL pública).
- Estados: carregando (enviando/baixando), sucesso, erro acionável (mapear
  401/403/413/422 para mensagens humanas).
- Aviso visível e inequívoco: "Imagem recebida e armazenada. A resposta aguarda
  transcrição — ainda NÃO foi transcrita nem corrigida." NUNCA mencionar nota/IA
  no upload. Desabilitar o botão durante o envio (mitigação de duplo clique, UX).
- Build de produção deve passar (`npm run build`). NÃO invente resposta vazia/
  fictícia em lugar nenhum do frontend para contornar contrato.

## Testes a escrever (core/app/tests/)
Cobrir ACI-01..ACI-09: criar resposta por imagem sem texto (201, source=IMAGE,
aguardando); pedir correção dela -> 422 ANSWER_NOT_TRANSCRIBED e nenhum
CorrectionJob; fluxo textual intacto (201 TEXT; correção 202); auth 401/403 no
novo endpoint; falha de commit sem órfão (monkeypatch); reenvio em
/answers/{id}/images preserva anteriores; create_answer com text vazio -> 422;
run_correction_job com text nulo falha explicitamente sem chamar rede (mock).
NÃO rode pytest/pip você mesmo se o ambiente bloquear — mas ESCREVA os testes.
Se conseguir rodar, rode e cole o resultado.

## Relatório final
Salve em `local-nao-versionado/claude_report_resposta_por_imagem.md`: arquivos
criados/alterados, resumo do diff, resultado dos testes (se rodou), mapeamento
ACI-01..09 -> evidência/limitação, decisões de design, confirmação de que
avalia_dev/apresentação não foram tocados, e `git status --short` final (sem
stage). NÃO faça git. Pare ao terminar.
