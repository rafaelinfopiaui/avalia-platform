# Desenho técnico curto — Extração OCR/visão experimental (DEC-AV-046)

> Menor delta para a primeira entrega assistida por imagem com OCR obrigatório.
> Reutiliza o fluxo já homologado/integrado; não reconstrói nada. Escopo: demonstração
> local com dados fictícios. Governança: `DEC-AV-046`; ADR: `ADR-009` (adendo 2026-10-22).

## Mapeamento aos IDs do backlog canônico
- `BL-AV-4B-07`/`BL-AV-4B-08` (preparação/extração local): 1ª fatia experimental — extração automática.
- `BL-AV-4B-21` (processamento recuperável da extração de uma imagem): estado persistido + retomada.
- `BL-AV-4B-13` (fallback manual após falha de extração): preservado (caminho manual homologado).
- Sprint de referência: `AV-S07B` (preparação/extração local), Fase 4 da trilha.
- Não encerra AV-S05B (PARCIAL) nem altera o numerador (22/70).

## Reuso (sem reconstruir)
- Upload/captura móvel (`POST /v1/answers/image`, PR #23/#16), download autenticado, `AnswerImage` (deleted_at).
- `manual-transcription/draft` + `/confirm` (DEC-AV-040/041), lock por `transcription_version`, `AuditEvent`.
- `POST /v1/answers/{id}/corrections` (análise textual, DEC-AV-041) e `HumanReview` (revisão).

## Delta (3 camadas)

### AI Engine — motor de visão SEPARADO do textual
- Novo `vision_client.py`: chama `POST {OLLAMA_URL}/api/generate` com `model=AI_VISION_MODEL_NAME`
  (`qwen2.5vl:3b`), `images=[<base64>]`, `options={num_ctx:8192, seed:42, temperature:0}`,
  `stream:false`, SEM `format:json`. Lê e sanitiza o corpo do erro HTTP (corrige lacuna AV-S05B).
- Novo `POST /v1/extract` (schema próprio): entrada = imagem base64 + metadados; saída = texto bruto +
  {modelo, duração, estado: ok|vazio|falha, detalhe_falha}. Prompt de transcrição LITERAL
  (preserva erros do aluno; não corrige/completa/reescreve). Nunca fabrica texto; vazio é "vazio".
- Config nova: `AI_VISION_MODEL_NAME=qwen2.5vl:3b`, `AI_VISION_NUM_CTX=8192`, `AI_VISION_SEED=42`.
  Modelo de visão e modelo textual de correção permanecem distintos.
- Segurança: conteúdo da imagem/texto é DADO não confiável, nunca instrução; o motor não recebe
  ferramentas/segredos; saída tratada como texto puro. Não registrar foto/texto integral/segredos em log
  (apenas comprimento/hash, padrão já usado).

### Core — orquestração da extração
- Novo modelo `TranscriptionExtraction` (migração aditiva): `id, answer_id, answer_image_id,
  engine, model, config_json, status, raw_output(text), duration_ms, error_detail, created_at`.
  Preserva saída bruta e vínculo à imagem; distinto de draft/confirmado.
- Novo `POST /v1/answers/{id}/transcription/extract` (professor/admin):
  autoriza por propriedade/vínculo (reusa `_get_owned_assessment`); seleciona a imagem ATIVA
  (`deleted_at IS NULL`); se houver múltiplas, escolhe de forma EXPLÍCITA e registra a proveniência
  (não escolher silenciosamente). Chama o AI Engine `/v1/extract` com a imagem real do storage.
  Grava `TranscriptionExtraction`. Preenche `manual_transcription_draft` com o texto extraído
  SOMENTE se o draft estiver vazio (NUNCA sobrescreve rascunho manual já preenchido); marca origem OCR.
  NÃO confirma a transcrição; NÃO dispara correção. Idempotência: bloqueia extração concorrente/clique
  repetido por estado/lock; sem retry oculto nem reextração automática. Timeout explícito.
- Nunca usa texto do cartão/referência/transcrição esperada como entrada do motor — só a imagem.
- Concorrência de recursos: serializa extração (visão) × análise (texto) para não disputar memória.

### Frontend — conferência humana
- Botão "Extrair texto da imagem (experimental)" na tela de resposta por imagem. Rótulo de que é
  experimental e exige conferência. Estados: processando / sucesso / falha / sem texto.
- Mostra imagem + texto extraído lado a lado; edição antes de confirmar; rótulo de origem (OCR|manual).
- Confirmação explícita e definitiva (reusa `/confirm`). "Solicitar análise" só após confirmação válida.
- Fallback manual preservado (digitar/editar quando extração falha/vazia). Saída renderizada como
  TEXTO (nunca HTML executável). Retomada após reload reusa o fluxo existente.

## Fora de escopo nesta fatia
Recorte humano de região (só se necessário, com desenho mínimo antes); preparação determinística de
imagem (só com necessidade concreta, preservando original + registrando derivado); múltiplas páginas;
fórmulas/tabelas/desenhos. Nenhuma reconstrução generativa de letras. Sem refatoração ampla/deps novas.

## Evidência dos testes (resumo sanitizado — 2026-10-22)

### Confirmação humana (relato do professor)
O professor executou o fluxo em dois aparelhos (um iPhone e um Android) no ambiente local de demonstração,
com dados fictícios, e confirmou SATISFATÓRIOS exclusivamente três passos: (1) captura/envio da foto;
(2) reconhecimento de texto (extração OCR local por IA de visão); (3) análise pedagógica pela IA.
Este relato NÃO abrange recuperação após reload, remoção/reseleção de imagem, confirmação da transcrição
nem registro de revisão humana final — não validados especificamente nesta rodada.

### Comprovações de backend (observação por leitura, separada do relato humano)
Durante a sessão de testes, ações humanas na interface geraram 6 respostas por imagem novas, cada uma com
1 extração OCR (status ok, modelo de visão) e análise textual (modelo textual distinto). A reconciliação
por resposta mostra 6 extrações e 8 análises: quatro respostas com uma análise e duas respostas com duas
análises (ambas as tentativas registradas como "sugerida", sem erro — tentativas adicionais legítimas,
não falhas). Cada chamada foi correlacionada ao log do servidor de inferência local por janela temporal,
duração e modelo. Os dois motores são distintos: visão para a extração e texto para a análise (duas
chamadas reais por resposta analisada).

Autoria das gravações: os registros novos foram criados pelas AÇÕES HUMANAS de teste na interface; a coleta
posterior foi feita SOMENTE por leitura (consultas e leitura de log), sem criar, editar, apagar dados nem
repetir inferência.

### Limitação da correlação
O log de inferência é um access-log (método, status, duração, rota), sem identificador da resposta nem
corpo da requisição. A associação extração/análise ↔ chamada real é temporal (janela + duração + modelo),
robusta porém indireta; não há vínculo explícito por chave no log.

### Revisão independente e validações
Revisão de código independente por agente de família distinta do executor, em fluxo legítimo (sem bypass de
permissões), com parecer final "aprovado com ressalvas"; as ressalvas materiais foram corrigidas e cobertas
por teste. Validações automatizadas executadas localmente (lint, testes de unidade/integração em SQLite,
testes de concorrência em PostgreSQL descartável, testes específicos da extração, migração aditiva
reversível, build/lint do frontend). Números exatos e separação por suíte constam do PR.

### Limitações remanescentes e caráter experimental
A extração é EXPERIMENTAL. O motor de visão pode produzir texto incorreto ou sem suporte (falhou no
controle ilegível recortado da investigação anterior, AC-05, n=1). A conferência humana é obrigatória e não
garante a identificação de todo erro. O sucesso funcional observado nos aparelhos testados NÃO apaga essas
limitações nem garante qualquer manuscrito. Serialização visão×texto é por processo (ambiente single-worker);
não há seletor de múltiplas imagens no frontend (o backend recusa com segurança quando há mais de uma ativa);
o lock não é mantido durante a inferência (o resultado só é aceito se a imagem seguir ativa na revalidação).
Esta evidência NÃO constitui homologação do projeto nem autorização de uso operacional com dados reais;
numerador e baseline permanecem inalterados.
