# Evidência de validação visual — Resposta por imagem (AV-S06B, DEC-AV-037)

> Rodada LOCAL de validação visual (ACI-08), autorizada como parte da execução já
> aprovada. Sem publicação. Sem stage/commit/push/merge. Navegador real (Chromium
> via CDP) contra ambiente isolado descartável. Evidências sanitizadas (sem tokens,
> sem bytes de imagem, sem dados reais).

## 1. Ambiente (isolado, descartável)

- Banco PostgreSQL descartável próprio: `av_s06b_rpi_visual_hermes` (migrado a head
  `e7c3f1a8b2d4`); **não** usou `avalia_dev` nem `avalia_apresentacao_demo_20261002`.
- Storage temporário: `/tmp/av_s06b_rpi_visual_storage`.
- Core (FastAPI) em `127.0.0.1:8196`, `ACADEMIC_MODULE_ENABLED=false`,
  `AI_ENGINE_URL` apontando para porta morta (`health.ai_engine=false`). **Nenhum
  Ollama/OCR iniciado** — não é necessário para recebimento e bloqueio de correção.
- Frontend (Vite) em `127.0.0.1:5273`, `VITE_API_URL` para o Core isolado.
- Seed mínimo: 2 professores fictícios; 2 avaliações publicadas do prof1
  (Biologia com 2 questões, História com 1 questão).
- Login usado: `prof1@verif.example.com` (fictício, ambiente isolado).

## 2. Cenários executados (navegador real)

| # | Cenário (requisito) | Resultado | Evidência observada |
|---|---|---|---|
| 1 | Seleção manual de avaliação/questão/aluno conforme o contrato | **PASS** | Selects "Avaliação" e "Questão" em cascata; escolher Biologia populou Questão 1 e 2; enunciado da questão exibido; campo "Identificação fictícia do aluno" manual (DEC-AV-021) |
| 2 | Envio de JPEG válido; carregando e sucesso | **PASS** | `resposta_bio.jpg` (5 KiB) → 201; botão vira "Enviando imagem…"; aviso de sucesso e card "Aguardando transcrição" |
| 3 | Envio de PNG válido | **PASS** | `resposta_hist.png` (1 KiB) → 201 na Questão 2 (Aluno B) |
| 4 | Listagem e visualização por download autenticado | **PASS** | Card lista a imagem (nome, tipo, tamanho, data); botão "Visualizar" baixa via **blob autenticado** (`src` começa com `blob:`), imagem renderiza com `naturalWidth=640` (dimensão real) |
| 5 | Estado "aguardando transcrição" preservado após recarregar | **RESSALVA** (ver §3) | O **estado está preservado no backend** (consulta ao banco após reload: `source=IMAGE`, `transcription_status=AGUARDANDO_TRANSCRICAO`, `text` NULL; 2 imagens no storage). Porém a tela de Resposta por Foto **não reexibe** as respostas após F5 — a lista é rotulada "enviadas nesta sessão" (estado React volátil) |
| 6 | Ausência de ação de correção para a resposta por imagem | **PASS** | A tela "Resposta por foto" não possui botão de correção/análise algum; o único botão é "Enviar foto da resposta". Contraste: a tela textual "Inserir resposta" tem "Solicitar análise da IA". O bloqueio de backend (422 `ANSWER_NOT_TRANSCRIBED`) já estava validado por HTTP em rodadas anteriores (reaproveitado, não repetido) |
| 7 | Rejeição compreensível de arquivo inválido | **PASS** | `falso.png` (extensão png, conteúdo não-imagem) → backend 422 → mensagem "O arquivo enviado não é uma imagem JPEG ou PNG válida. Envie uma foto JPEG ou PNG legível e confira os campos." Nenhuma resposta criada |
| 8 | Rejeição de arquivo acima de 10 MiB | **PASS** | `grande.png` (13,9 MiB) → barrado no cliente antes do envio: "A imagem excede o limite de 10 MiB. Reduza a resolução ou comprima a foto." |
| 9 | Troca de avaliação/questão sem exibir imagem ou estado da seleção anterior | **PASS** | Trocar Biologia→História resetou a questão para vazio, recarregou as questões da História, limpou campo arquivo e aluno; nenhum enunciado/imagem da seleção anterior persistiu no formulário. Trocar de questão também limpou o input de arquivo |
| 10 | Fluxo textual ainda utilizável | **PASS** | Tela "Inserir resposta" com textarea e "Solicitar análise da IA" funcional; link cruzado "Enviar resposta por foto" presente |

Resumo: **9 cenários PASS, 1 com ressalva** (cenário 5).

## 3. Achado concreto (cenário 5) e decisão

**Fato:** a preservação do estado "aguardando transcrição" está garantida no
**backend** — após recarregar, `GET` do estado continua retornando
`IMAGE/AGUARDANDO_TRANSCRICAO` e as imagens persistem no storage. A **limitação é de
interface**: a tela de Resposta por Foto não re-busca do backend as respostas já
enviadas ao carregar; a lista ("enviadas nesta sessão") é intencionalmente volátil
e some após F5.

**Causa de escopo:** não existe hoje endpoint `GET` para listar respostas por imagem
persistidas de uma avaliação/questão (só há `POST` de criação e
`GET /v1/answers/{answer_id}/images`, que exige conhecer o `answer_id`). Reexibir o
estado após reload exigiria **criar um endpoint novo no backend** — ampliação do
backend homologado.

**Decisão (Rafael, nesta rodada):** registrar como **limitação de UX conhecida
(débito)**, **sem alterar backend/código** nesta rodada. A preservação de estado
está garantida no backend; a reexibição após reload fica como **pendência para
fatia futura**. Portanto **nenhuma correção de código** foi feita — Claude Code e
Antigravity **não** foram acionados (não há delta a revisar).

## 4. Integridade de ambiente

- Bancos protegidos verificados **intactos** antes e depois: `avalia_dev`
  (`a9f4c2e71b06`, 16 human_reviews) e `avalia_apresentacao_demo_20261002`
  (`a9f4c2e71b06`). Nenhuma migração/escrita neles.
- Storage: apenas os **2 arquivos válidos** foram gravados; o inválido e o
  >10 MiB **não** geraram arquivo nem registro.
- Encerramento: Core, Vite e Chromium de automação desta rodada **desligados**;
  banco descartável **dropado**; storage temporário e assets de teste **removidos**.

## 5. Débito registrado

- **DEBT-AV-014 (UX):** a tela de Resposta por Foto não reexibe, após recarregar, as
  respostas por imagem já persistidas (em estado "aguardando transcrição") de uma
  avaliação/questão. Correção futura envolve um endpoint `GET` de listagem + consumo
  na tela. Não afeta recebimento, armazenamento, autorização nem o bloqueio de
  correção, todos validados.
