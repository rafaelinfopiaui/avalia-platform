# Plano — Complemento frontend da AV-S06B (interface de upload de imagem)

> PLANEJAMENTO apenas. Nenhuma implementação frontend nesta rodada.
> Sem nova numeração: é complemento da AV-S06B (camada de apresentação dos
> endpoints de imagem já homologados/integrados em `main` via PR #15 / b818961).

## 1. Objetivo

Tornar utilizável de ponta a ponta, na interface do professor, o recebimento de
imagem de resposta já existente no backend: selecionar os vínculos exigidos pelo
contrato, enviar uma imagem JPEG/PNG (até 10 MiB), listar e visualizar as imagens
por download autenticado, com mensagens claras de carregamento/sucesso/erro e a
indicação inequívoca de que armazenar a imagem NÃO significa transcrever nem
corrigir.

Esta fatia NÃO inclui OCR, extração, conferência de transcrição nem correção.

## 2. Contrato atual imagem <-> resposta (conferido no código integrado)

Endpoints (de `core/app/routers/images.py`, já em `main`):
- `POST /v1/answers/{answer_id}/images` (multipart, campo `file`) — anexa imagem
  a uma `Answer` **já existente**; autorização por propriedade/vínculo.
- `GET /v1/answers/{answer_id}/images` — lista imagens de uma resposta.
- `GET /v1/answer-images/{image_id}/download` — download autenticado do binário.

Criação de resposta hoje (`POST /v1/answers`, schema `AnswerInput`):
exige `question_id`, `student_name_fake` e `text` (todos obrigatórios); o modelo
`Answer.text` é `nullable=False`.

### 2.1 LACUNA CONTRATUAL (apresentada, não contornada)

O upload de imagem exige uma `Answer` pré-existente, mas **toda `Answer` exige
`text` não-vazio** para ser criada. Hoje **não há** caminho contratual para uma
"resposta cuja resposta é a imagem" sem antes inserir um texto.

- Isto importa porque, no fluxo por imagem, a foto É a resposta; o texto só
  deveria existir **depois** da transcrição confirmada (etapa AV-S08B, que depende
  de OCR — ainda não decidido). Exigir `text` agora força o professor a digitar
  algo antes de ter a transcrição.
- **NÃO proponho contorno** com texto fictício, placeholder ou `text=""` — isso
  violaria a regra de não inventar resposta para driblar a dependência, e poluiria
  o dado com conteúdo não confiável que depois entraria na fila de correção.
- Encaminhamento objetivo: esta lacuna precisa de **decisão de contrato** antes de
  a interface de upload ser plenamente útil. Opções a decidir por Rafael (não
  decididas aqui):
  1. permitir `Answer` com `text` opcional/nulo quando há imagem anexada
     (exige migração de `answers.text` para nullable + regra de que uma resposta
     precisa ter texto OU imagem) — tem impacto em `create_answer`, schema,
     correção e nos invariantes existentes; **não trivial**, merece item próprio;
  2. um endpoint/fluxo de criação "resposta por imagem" que crie a `Answer` e
     anexe a imagem numa transação, com `text` marcado como pendente de
     transcrição;
  3. manter o contrato atual e aceitar que, nesta primeira interface, a imagem só
     pode ser anexada a respostas que já tenham texto (uso limitado, pouco
     aderente ao propósito do fluxo por imagem).
- Recomendação: tratar a lacuna como **decisão de contrato + possível item de
  backlog** antes de implementar a interface; não resolver por conveniência no
  frontend.

## 3. Escopo do complemento frontend (quando autorizado)

- Seleção manual dos vínculos exigidos pelo contrato (professor escolhe
  avaliação -> questão -> aluno/resposta), preservando `DEC-AV-021` (seleção
  manual) e `DEC-AV-018` ("uma resposta de uma questão por foto"; reenvio
  permitido — não transformar em unicidade/proibição de reenvio).
- Upload de arquivo JPEG/PNG até 10 MiB (10 485 760 bytes), com validação de
  tipo/tamanho no cliente **como conveniência** — a validação autoritativa é a do
  backend (Pillow + limite). Mostrar erro claro quando o backend recusar (422/413/
  403/401).
- Listagem das imagens da resposta e visualização via download autenticado
  (nunca URL pública; usar o endpoint autenticado).
- Mensagens de estado: carregando (enviando/baixando), sucesso (imagem anexada),
  erro acionável (arquivo inválido, grande demais, sem permissão, sessão expirada).
- Indicação visível e inequívoca de que **armazenar a imagem não transcreve nem
  corrige** — texto do tipo "Imagem recebida e armazenada. Ela ainda não foi
  transcrita nem corrigida." (sem linguagem que sugira IA/nota).

## 4. Dependências por atividade (separadas, não bloqueio geral)

| Atividade | Depende de | Status |
|---|---|---|
| Interface de upload/listagem/visualização | endpoints de imagem (já em `main`) + **resolução da lacuna §2.1** | desbloqueada tecnicamente nos endpoints; **bloqueada pela decisão de contrato** para ser plenamente útil |
| Extração/OCR real (AV-S07B, BL-AV-4B-06/07/08/09) | decisão arquitetural de OCR (`BL-AV-4B-02`), que depende do benchmark (`BL-AV-4B-20`/AV-S05B, parcial) e de `DEC-AV-017` | **bloqueada** — não iniciar |
| Conferência/confirmação da transcrição (AV-S08B, BL-AV-4B-10..13) | existência de transcrição (AV-S07B) | **bloqueada por AV-S07B** — mas o *planejamento* da conferência pode ser feito; não está globalmente bloqueado |
| Retenção/exclusão operacional (`BL-AV-4B-05`) | decisão de produto (retenção + exclusão) | **pendente de decisão** |

Observação: a extração real é o único ponto que depende da decisão de OCR. O
planejamento da conferência (AV-S08B) não está bloqueado em si — só a sua
implementação depende de haver transcrição. Não declarar toda a atividade de
planejamento da conferência como bloqueada.

## 5. Critérios de aceite propostos (para a futura sprint de interface)

- a UI nunca dispara correção nem menciona nota/IA ao anexar imagem;
- upload só via endpoint autenticado; imagem exibida só via download autenticado;
- erros do backend (401/403/413/422) refletidos em mensagens humanas e acionáveis;
- seleção manual de vínculos conforme contrato; reenvio permitido (DEC-AV-018);
- nenhuma criação de resposta com texto fictício/vazio para contornar a lacuna §2.1
  (bloqueado até decisão de contrato).

## 6. O que NÃO fazer nesta e na próxima rodada de implementação

Sem OCR, sem correção automática, sem criação de resposta fictícia, sem exclusão
(não decidida), sem migração operacional em bancos protegidos, sem P5/seed/deploy/
baseline. Interface só após autorização específica e, idealmente, após a decisão
de contrato da §2.1.
