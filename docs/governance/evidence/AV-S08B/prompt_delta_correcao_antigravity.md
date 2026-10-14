# Revisão independente do DELTA — AV-S08B: solicitar correção após confirmação

Repo: /Users/rafaeloliveira/Projeto Estágio/avalia-plataform
Branch (checkout atual): feat/av-s08b-transcricao-manual

IMPORTANTE: esta é uma revisão de DELTA, não uma auditoria geral. Você já
revisou a implementação anterior da fatia AV-S08B (parecer em
`evidence/AV-S08B/revisao_implementacao_antigravity.md`, aprovado com
ressalvas documentais). NÃO reabra essa parte. Revise SOMENTE o que mudou
nesta rodada:

- `frontend/src/pages/ImageAnswerPage.tsx`: novo componente `CorrectionRequest`
  (linha ~322) e função `correctionError` (linha ~102), renderizado em
  `SentAnswer` só quando `transcription_status === 'TRANSCRICAO_CONFIRMADA'`
  (linha ~391).
- `core/app/tests/test_manual_transcription.py`: 3 testes novos sobre
  correção de resposta IMAGE confirmada (veja no final do arquivo, perto de
  `test_confirmed_image_answer_correction_uses_same_answer_and_confirmed_text`,
  `test_confirmed_image_answer_new_request_increments_attempt_on_same_answer`,
  `test_unconfirmed_image_answer_correction_stays_blocked`).
- Nenhum endpoint de backend foi criado ou alterado nesta rodada — confirme
  isso você mesmo (diff de `core/app/main.py`, `models.py`, `schemas.py`,
  `services/correction.py` deve ser idêntico ao que você já revisou antes).

NÃO faça stage/commit/push/merge. NÃO altere avalia_dev nem
avalia_apresentacao_demo_20261002. Pode criar/dropar bancos de teste
descartáveis próprios (nome contendo "test").

## O que verificar

1. O botão "Solicitar análise da IA" realmente só aparece após a confirmação
   (leia o JSX, não confie em screenshot/relato).
2. Ele chama `requestCorrection(answer.id)` — a MESMA função já existente em
   `api.ts`, usada pelo fluxo textual (`AnswerPage.tsx`) — e não cria nenhuma
   resposta nova nem endpoint novo.
3. Navegação para `/correcoes/{job.id}` no sucesso (rota já existente,
   `CorrectionPage`).
4. Estados de carregamento/sucesso/erro presentes e com mensagens legíveis
   (incluindo `RUBRIC_NOT_PUBLISHED` e `ANSWER_NOT_TRANSCRIBED` como defesa
   em profundidade, já que o botão só aparece confirmado).
5. Os 3 testes novos: confirme que o teste
   `test_confirmed_image_answer_correction_uses_same_answer_and_confirmed_text`
   realmente verifica que o `CorrectionJob.answer_id` é o MESMO id da
   resposta por imagem original, e que o texto enviado ao AI Engine
   (capturado via fake/mock do `run_correction_job`) é EXATAMENTE o texto
   confirmado — não o rascunho, não um texto diferente.
6. Re-rode você mesmo: `pytest app/tests/test_manual_transcription.py -q`
   (deve dar 33 passed, 5 skipped) e o teste de regressão
   `test_unconfirmed_image_answer_correction_stays_blocked` isoladamente.
7. Re-rode `npx tsc -b`, `npm run build`, `npm run lint` no frontend/ você
   mesmo.
8. Confirme que a política de repetição de correção (nova tentativa =
   `attempt` incrementado no MESMO `answer_id`, sem endpoint novo) não foi
   alterada — leia o código de `request_correction` em `main.py` e confirme
   que está idêntico ao da rodada anterior.

## Entregável

Escreva o parecer em
`docs/governance/evidence/AV-S08B/revisao_delta_correcao_antigravity.md`
com: veredito (aprovado / aprovado com ressalvas / reprovado), achados
numerados (ACH-NN) só sobre este delta, severidade e evidência real
(comando+saída ou código:linha) para cada achado.
