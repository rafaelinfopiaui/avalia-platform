# Tarefa: completar AV-S08B — ação de solicitar correção após confirmação (DELTA, escopo já autorizado)

Repo: /Users/rafaeloliveira/Projeto Estágio/avalia-plataform
Branch (já em checkout): feat/av-s08b-transcricao-manual

IMPORTANTE — antes de tocar em qualquer arquivo, rode `git status --short` e
`git diff --stat` e leia o que já existe nesta branch (migração, endpoints,
testes, frontend da transcrição manual). NÃO refaça nem reabra nada disso.
Esta tarefa é um DELTA pequeno e cirúrgico sobre o que já está pronto.

NÃO faça stage/commit/push. NÃO toque em avalia_dev nem apresentação. NÃO
implemente OCR, reabertura pós-confirmação, nem novos endpoints de backend —
o backend de correção já existe e já aceita resposta IMAGE confirmada (isso já
foi confirmado por teste manual: POST /v1/answers/{id}/corrections retorna 202
quando a resposta está com transcription_status=TRANSCRICAO_CONFIRMADA).
NÃO crie uma resposta textual (`AnswerPage`/`createAnswer`) para contornar o
fluxo — a correção tem que partir do MESMO answer_id da resposta por imagem
confirmada.

Grave seu relatório em local-nao-versionado/claude_report_av_s08b_delta_correcao.md
(git-ignored, nome diferente do relatório anterior para não sobrescrevê-lo).

## O que falta (confirmado por investigação prévia)

Backend: NADA a mudar. `POST /v1/answers/{answer_id}/corrections` (em
core/app/main.py, função `request_correction`) já bloqueia com 422
`ANSWER_NOT_TRANSCRIBED` antes da confirmação e já aceita (202) depois —
porque ele só olha `answer.transcription_status` e `answer.text`, sem se
importar se a origem foi TEXT ou IMAGE. A política de repetição de correção
(nova tentativa gera novo CorrectionJob com `attempt` incrementado, mesmo
answer_id) também já está pronta e não deve ser alterada.

Frontend: falta o botão/ação na tela de resposta por foto
(frontend/src/pages/ImageAnswerPage.tsx) que:
1. Só aparece quando `answer.transcription_status === 'TRANSCRICAO_CONFIRMADA'`
   (reaproveite a mesma condição já usada no componente `ManualTranscription`
   para mostrar o estado confirmado).
2. Antes de confirmar, a ação de correção não deve aparecer/estar disponível
   (já é o caso hoje, porque a área de confirmação some).
3. Ao clicar, chama `requestCorrection(answer.id)` — função que JÁ EXISTE em
   frontend/src/services/api.ts (é a mesma usada por AnswerPage.tsx para o
   fluxo textual). Reuse-a, não crie uma nova.
4. Estados de carregamento/sucesso/erro: siga o mesmo padrão visual já usado
   no resto do arquivo (veja `busy`, `Alert`, `Spinner` em
   ImageAnswerPage.tsx e em AnswerPage.tsx como referência de estilo).
5. Em caso de sucesso, navegue para `/correcoes/{job.id}` — rota que já
   existe (`CorrectionPage`), igual ao que `AnswerPage.tsx` já faz
   (`navigate(`/correcoes/${job.id}`)`). Para isso o componente que renderiza
   o botão precisa de acesso a `useNavigate` do react-router-dom (já importado
   em outras páginas do projeto).
6. Erros possíveis a tratar de forma legível (reaproveite ou adapte
   `humanError`/`transcriptionError` já existentes no arquivo, ou crie uma
   pequena função equivalente só para este caso): 422 `ANSWER_NOT_TRANSCRIBED`
   (não deveria acontecer já que o botão só aparece confirmado, mas trate por
   defesa em profundidade), 422 `RUBRIC_NOT_PUBLISHED` (rubrica da questão não
   publicada — mensagem clara pedindo para publicar a rubrica), 403/401/404
   nos mesmos moldes dos outros tratamentos do arquivo.
7. Depois de solicitar com sucesso, se o professor permanecer na tela (por
   exemplo, se a navegação falhar ou ele voltar), a resposta já confirmada
   deve deixar claro que uma correção já foi solicitada — não é obrigatório
   bloquear nova solicitação (a política vigente permite nova tentativa), mas
   o rótulo do botão deve refletir que já existe ao menos uma tentativa
   (ex.: "Solicitar nova análise da IA" após a primeira, análogo ao campo
   `attempt` que o backend já incrementa) SE isso for simples de obter sem
   endpoint novo — se não houver endpoint de leitura de jobs por answer_id
   disponível no momento, não invente um; deixe o rótulo fixo
   ("Solicitar análise da IA") e documente essa limitação no relatório.

## Onde colocar o botão

Sugestão (não obrigatória): dentro do bloco de `ManualTranscription` que já
mostra "Transcrição confirmada" (condição
`answer.transcription_status === 'TRANSCRICAO_CONFIRMADA'`), ou logo abaixo
dele no componente `SentAnswer`. Mantenha a tela coerente com o padrão visual
existente. Pode precisar levantar o `useNavigate` para o componente
`SentAnswer` ou `ImageAnswerPage` e passar um callback para dentro de
`ManualTranscription`, à sua escolha de organização — não precisa ser
exatamente a estrutura atual dos componentes, contanto que funcione e
mantenha a legibilidade.

## Testes

Adicione teste(s) automatizado(s) cobrindo o backend (mesmo que a lógica já
exista, não havia teste explícito cobrindo resposta IMAGE confirmada indo até
a correção) — pode ser em core/app/tests/test_manual_transcription.py (mesmo
arquivo da fatia) ou em um novo arquivo pequeno dedicado, à sua escolha:
- Resposta IMAGE com transcrição confirmada: `POST /v1/answers/{id}/corrections`
  retorna 202 e cria `CorrectionJob` com `answer_id` apontando para a MESMA
  resposta.
- O texto usado na correção (verificável via `AIExecution`/`AnswerOut.text`,
  ou inspecionando o que seria enviado ao AI Engine) é EXATAMENTE o texto
  confirmado pela transcrição manual (não um texto diferente, não vazio).
- Resposta IMAGE ainda não confirmada continua bloqueada (422
  `ANSWER_NOT_TRANSCRIBED`) — teste de regressão, não deveria já existir mas
  confirme que não quebrou.
- Não rode a suíte completa de novo do zero sem necessidade — mas rode pelo
  menos os testes deste arquivo + os já existentes de corrections/review para
  confirmar que nada quebrou (ex.: `pytest app/tests/test_manual_transcription.py
  app/tests -k "correction or review" -q`, ajuste ao padrão real de nomes de
  teste do repo).

## Frontend: build/lint

Rode `npx tsc -b`, `npm run build`, `npm run lint` no frontend/ e reporte o
resultado real.

## Ao terminar, no relatório (local-nao-versionado/claude_report_av_s08b_delta_correcao.md)

- arquivos alterados/criados (deve ser pequeno: ImageAnswerPage.tsx e talvez
  api.ts se precisar de ajuste mínimo; teste novo ou arquivo de teste
  ampliado);
- comandos reais executados e saída real (testes, lint, build) — não presuma;
- qualquer desvio desta instrução, com justificativa;
- confirmação explícita de que NÃO alterou nenhum endpoint de backend já
  existente da fatia anterior (draft/confirm) nem o endpoint de correção em
  si — só consumiu o que já existe.
