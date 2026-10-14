# Desenho técnico — Resposta por imagem (AV-S06B, complemento) — v2 (ajustes da revisão incorporados)

> Desenho ANTES do código. Direção de produto aprovada por Rafael (2026-10-14):
> a foto pode ser a entrada inicial da resposta, sem texto digitado/vazio/fictício;
> correção bloqueada até transcrição confirmada pelo professor. Rodada local,
> sem publicação. Reutiliza o backend de imagens homologado (não amplia sua
> homologação).
>
> **v2 — ajustes incorporados após revisão independente do Antigravity
> (APROVADO COM AJUSTES, parecer em `revisao_desenho_antigravity.md`):** ver
> seção 12. Todos os achados são técnicos/detalhamento, sem nova decisão de
> produto.

## 1. Princípio de desenho

Menor mudança coerente: NÃO são alternativas excludentes. Combinamos:
- `Answer.text` passa a ser **opcional no nível de armazenamento** (nullable),
  governado por um **invariante de origem** (a resposta nasce de texto OU de
  imagem), em vez de texto sempre obrigatório;
- um **fluxo transacional "resposta por imagem"** que cria a `Answer` e anexa a
  primeira imagem numa única operação, deixando a resposta em estado
  `aguardando_transcricao`.

Assim o fluxo textual existente não muda de contrato, e o fluxo por imagem ganha
um caminho próprio e explícito.

## 2. Representação: resposta textual vs. resposta por imagem

Introduzir em `Answer` dois campos:

- `source` (enum `AnswerSource`): `TEXT` | `IMAGE`.
  - `TEXT`: resposta digitada (fluxo atual). `text` obrigatório e não-vazio.
  - `IMAGE`: resposta cuja entrada inicial é a foto. `text` começa NULL.
- `transcription_status` (enum `TranscriptionStatus`, só relevante p/ `source=IMAGE`):
  `AGUARDANDO_TRANSCRICAO` | `TRANSCRICAO_CONFIRMADA`.
  - `TEXT` nasce já com `transcription_status = TRANSCRICAO_CONFIRMADA` (o próprio
    texto digitado é a "transcrição confirmada" pela origem humana), para manter
    um único invariante de "pronta para correção".
  - `IMAGE` nasce `AGUARDANDO_TRANSCRICAO`.

`Answer.text` muda para `nullable=True` no modelo e na migração.

Nota: nesta fatia NÃO há OCR nem endpoint de confirmar transcrição funcional de
ponta a ponta (confirmar transcrição é AV-S08B, depende de OCR). O estado
`TRANSCRICAO_CONFIRMADA` para `source=IMAGE` existe no desenho, mas o único jeito
de alcançá-lo nesta fatia é inexistente de propósito — a resposta por imagem
termina legitimamente em `AGUARDANDO_TRANSCRICAO`. (Isso evita confirmação
fictícia.)

## 3. Invariantes (validados no modelo/serviço e por teste)

1. `source=TEXT`  => `text` NOT NULL e não-vazio; `transcription_status=TRANSCRICAO_CONFIRMADA`.
2. `source=IMAGE` => `text` pode ser NULL; ao nascer, `transcription_status=AGUARDANDO_TRANSCRICAO`;
   deve existir >= 1 `AnswerImage` vinculada (garantido pela transação do §5).
3. Correção só é permitida quando `transcription_status=TRANSCRICAO_CONFIRMADA`
   E `text` não-vazio (ver §6). Como não há como confirmar transcrição nesta
   fatia, toda resposta por imagem fica bloqueada para correção — por desenho.
4. Nunca gravar `text=""` nem placeholder para uma resposta por imagem. Ausência
   de texto é representada por NULL + `source=IMAGE`.

## 4. Compatibilidade com registros e consumidores existentes

- Migração: `answers.text` -> nullable. Backfill: todas as linhas existentes
  recebem `source=TEXT` e `transcription_status=TRANSCRICAO_CONFIRMADA`
  (preservam comportamento atual). Nenhuma linha existente fica com text NULL.
- `POST /v1/answers` (contrato textual vigente): inalterado — continua exigindo
  `text`; cria `source=TEXT`. Consumidores atuais não percebem diferença.
- `AnswerOut`: ganha `source` e `transcription_status` como campos adicionais
  (aditivo, não quebra clientes que ignoram campos extras); `text` passa a poder
  ser `null` no schema de saída para respostas por imagem.
- `run_correction_job` já lê `answer.text`; fica protegido pelo bloqueio do §6,
  então nunca recebe `text=None` (não precisa mudar sua lógica interna, mas o
  caminho que o dispara passa a barrar antes).

## 5. Fluxo transacional "resposta por imagem" (novo endpoint)

Novo: `POST /v1/answers/image` (multipart) — cria a Answer por imagem e anexa a
primeira foto atomicamente. Campos: `question_id`, `student_name_fake`, `file`.

Passos (uma transação lógica):
1. autorização idêntica a `create_answer` (`_get_owned_assessment` +
   `require_assessment_mutation`), a partir da `question_id`;
2. validação da imagem **reutilizando as funções já homologadas** de
   `routers/images.py` (validação Pillow, limite, nome UUID, escrita atômica);
3. gravar o arquivo em disco (padrão homologado: temp -> fsync -> os.replace);
4. criar `Answer(source=IMAGE, text=NULL, transcription_status=AGUARDANDO_TRANSCRICAO)`
   e `AnswerImage` apontando para o arquivo, e commitar **juntos**;
5. em falha de qualquer etapa após gravar o arquivo: remover o arquivo e não
   deixar Answer nem AnswerImage órfãos (ver §7).

O endpoint homologado `POST /v1/answers/{answer_id}/images` continua válido para
anexar imagem a uma Answer já existente (inclusive reenvio). Não alteramos seu
contrato nem sua homologação — só o reutilizamos internamente onde couber.

## 6. Bloqueio de correção sem transcrição confirmada (todos os caminhos)

Caminho único de disparo hoje: `POST /v1/answers/{answer_id}/corrections`
(`request_correction`). Adicionar, logo após obter a `answer` e antes de criar o
`CorrectionJob`:

    if answer.transcription_status != TRANSCRICAO_CONFIRMADA or not (answer.text or "").strip():
        -> 422 code "ANSWER_NOT_TRANSCRIBED"
           "A resposta por imagem ainda não tem transcrição confirmada; não pode ser corrigida."

- Isso cobre o único caminho de correção. `run_correction_job` nunca é agendado
  sem passar por aqui.
- Teste explícito: resposta `source=IMAGE` em `AGUARDANDO_TRANSCRICAO` -> 422 e
  nenhum `CorrectionJob` criado; resposta textual existente -> continua 202.

## 7. Falha entre banco e armazenamento de arquivo

Reutiliza o padrão homologado (escrita atômica + rollback):
- grava em arquivo temporário no diretório de storage; valida; `os.replace` para
  nome final só após validação;
- cria Answer + AnswerImage e `db.commit()` por último;
- se o commit falhar: `db.rollback()` e remover o arquivo final
  (`unlink(missing_ok=True)`) — sem Answer órfã, sem AnswerImage órfã, sem
  arquivo solto;
- se a gravação do arquivo falhar: nenhuma linha é criada (ordem: validar/gravar
  arquivo antes de commitar banco; mas a Answer só é persistida no commit final).
- Decisão de ordem: no fluxo transacional, criar o arquivo primeiro e o registro
  depois, igual ao endpoint homologado — assim "arquivo sem registro" é limpo no
  except, e "registro sem arquivo" não ocorre.

## 8. Repetição de requisição (sem inventar política de reenvio)

- `POST /v1/answers/{answer_id}/images` (homologado): reenvio continua permitido
  como já é — cada chamada cria nova `AnswerImage`, preserva as anteriores
  (DEC-AV-018 "uma resposta de uma questão por foto" preservada; sem unicidade de
  foto nem proibição de reenvio).
- `POST /v1/answers/image` (novo, transacional): cada chamada cria uma NOVA
  resposta por imagem. NÃO introduzir idempotência artificial nem deduplicação
  por hash nesta fatia (seria política de reenvio não aprovada). Repetir a
  requisição cria outra resposta — comportamento explícito e documentado, sem
  inventar regra. Se, no futuro, Rafael quiser evitar duplicatas de resposta,
  isso é decisão de produto própria.
- Observação honesta: sem idempotência, um duplo clique no frontend pode criar
  duas respostas por imagem. Mitigação no frontend (desabilitar botão durante o
  envio) é UX, não política de contrato — aplicá-la como conveniência, sem alterar
  a semântica do backend.

## 9. Delimitação (o que NÃO entra)

- Sem OCR, sem transcrição simulada, sem endpoint de confirmar transcrição
  funcional (a resposta por imagem termina legitimamente em
  `AGUARDANDO_TRANSCRICAO`).
- Sem exclusão de imagem/resposta (BL-AV-4B-05 permanece pendente).
- Sem retenção operacional.
- Sem alterar a homologação do backend de imagens; só reuso.

## 10. Itens de contrato/migração resumidos (menor mudança)

- Migração nova: `answers.text` -> nullable; adicionar `answers.source`
  (default TEXT para linhas existentes) e `answers.transcription_status`
  (default TRANSCRICAO_CONFIRMADA para linhas existentes); backfill determinístico.
  Downgrade: recusar se houver linhas com `text IS NULL` (não dá para voltar a
  NOT NULL sem perder dado) — padrão de recusa já usado na migração de imagens.
- Modelo: 2 enums novos + 2 colunas em `Answer` + `text` nullable.
- Schemas: `AnswerOut` ganha `source`/`transcription_status`; `text` opcional na
  saída.
- Endpoints: +1 (`POST /v1/answers/image`); `request_correction` ganha o guard.
- Frontend: tela/seção de "enviar resposta por foto" + lista/visualização +
  estados + aviso "aguardando transcrição, não corrigida".

## 11. Critérios de aceite propostos (a confirmar na sprint)

- ACI-01: criar resposta por imagem (JPEG/PNG <=10 MiB) sem texto -> 201, Answer
  `source=IMAGE`, `transcription_status=AGUARDANDO_TRANSCRICAO`, 1 AnswerImage.
- ACI-02: pedir correção de resposta por imagem não transcrita -> 422
  `ANSWER_NOT_TRANSCRIBED`, nenhum CorrectionJob.
- ACI-03: fluxo textual existente inalterado (criar resposta textual -> 201
  `source=TEXT`; pedir correção -> 202).
- ACI-04: autorização (professor sem vínculo -> 403; sem token -> 401) no novo
  endpoint.
- ACI-05: falha de commit após gravar arquivo -> nenhuma Answer/AnswerImage
  órfã, nenhum arquivo solto.
- ACI-06: reenvio em `/answers/{id}/images` continua criando nova imagem,
  preservando anteriores.
- ACI-07: migração aplica e faz backfill determinístico em banco isolado; linhas
  existentes viram `source=TEXT`/`TRANSCRICAO_CONFIRMADA`, nenhuma com text NULL.
- ACI-08 (frontend): estados de carregando/sucesso/erro; aviso explícito de
  "aguarda transcrição, não corrigida"; nenhuma menção a nota/IA no upload.

## 12. Ajustes incorporados da revisão do Antigravity (v2)

Veredito: APROVADO COM AJUSTES. Arquitetura central (text nullable + source +
transcription_status + endpoint transacional + guard de correção) confirmada como
a menor mudança coerente. Ajustes técnicos a aplicar na implementação:

- **ACH-01 (AnswerOut):** `text` passa a `Optional[str] = None`; adicionar `source`
  e `transcription_status`. Aditivo; `correction-jobs/{id}/context` não quebra
  (só dispara com texto válido).
- **ACH-02 (Invariante 1 estrito):** validar no backend que `AnswerInput.text`
  não é vazio/só espaços (`.strip()`), ao criar resposta textual — hoje o schema
  aceita `str` sem `min_length`.
- **ACH-03 (multipart no novo endpoint):** NÃO reutilizar o `request.form(max_files=1,
  max_fields=1)` do endpoint homologado (ele é para 1 campo). O novo
  `POST /v1/answers/image` tem 3 campos (`file`, `question_id`, `student_name_fake`)
  — usar parâmetros declarativos do FastAPI (`UploadFile = File(...)`,
  `str = Form(...)`), evitando HTTP 400. O endpoint homologado permanece intacto.
- **ACH-04 (defesa em profundidade):** adicionar fail-fast em `run_correction_job`
  (`core/app/services/correction.py`): se `answer.text` for nulo/vazio, marcar o
  job como falha explícita ANTES de chamar o AI Engine (que exige `answer_text:
  str`). O guard primário continua em `request_correction`; isto é redundância
  defensiva, não o controle principal.
- **ACH-05 (isolamento do teste AST):** o teste pré-existente
  `test_images_module_has_no_ocr_or_correction_references` proíbe referências a
  correção em `routers/images.py`. Portanto o novo endpoint transacional e o guard
  de correção ficam em **`main.py`** (não em `images.py`). As funções de validação/
  gravação de imagem são reutilizadas de `images.py` por import, sem trazer termos
  de correção para lá.
- **ACH-06 (frontend types):** atualizar `frontend/src/types.ts` para
  `text?: string | null`, `source?: 'TEXT'|'IMAGE'`, `transcription_status?: ...`;
  `ReviewPage.tsx` já tolera `text` ausente.
- **Integridade no SGBD (CheckConstraint):** adicionar na tabela `answers` o
  constraint `(source='TEXT' AND text IS NOT NULL) OR (source='IMAGE')`, garantindo
  o invariante mesmo contra escrita fora da API.
- **Schema de retorno do novo endpoint (decisão técnica):** `POST /v1/answers/image`
  responde com `AnswerOut` acrescido de `images: list[AnswerImageOut]` (um schema
  composto `AnswerWithImagesOut`), para o cliente já receber o `image_id` da foto
  anexada sem segunda chamada. Dentro da direção aprovada; não é decisão de produto.
- **Fail-fast antes de I/O:** no novo endpoint, validar auth + existência da
  Question + `require_assessment_mutation` + `student_name_fake` não-vazio ANTES de
  gravar qualquer byte em disco.
- **Convenção de enums no Alembic:** `AnswerSource` e `TranscriptionStatus` seguem
  a convenção de tipos nomeados do PostgreSQL já usada em
  `c4a8b2d91e37_add_academic_structure.py`, com downgrade seguro/idempotente.

Nenhum desses ajustes introduz decisão de produto nova — todos ficam dentro da
direção aprovada por Rafael.
