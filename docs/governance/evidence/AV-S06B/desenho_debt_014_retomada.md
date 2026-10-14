# Fatia DEBT-AV-014 — Recuperação de envios persistidos (resposta por imagem)

> Branch dedicada `feat/av-s06b-debt-014-retomada-respostas-imagem` (a partir de
> `main` cf81109). Autorização: Rafael (2026-10-14), após homologação/integração do
> PR #16 (DEC-AV-038). Resolve `DEBT-AV-014`. Rodada LOCAL: sem stage/commit/push
> nesta fatia. Claude Code implementa; Antigravity revisa; Codex só diante de risco
> concreto. Sem transcrição manual nem OCR nesta fatia.

## 1. Problema (DEBT-AV-014)

A tela de "Resposta por foto" (`ImageAnswerPage.tsx`) exibe apenas os envios feitos
na sessão atual (estado React volátil). Após recarregar (F5) ou abrir nova sessão,
a UI não retoma/lista as respostas por imagem já persistidas — não existe endpoint
`GET` de listagem por avaliação/questão. Os dados persistem no backend; o impacto é
de rastreabilidade visual.

## 2. Escopo desta fatia (o que entra)

- **Backend:** endpoint `GET` de listagem autenticada de respostas por imagem de uma
  avaliação (e filtrável por questão), retornando cada resposta com seu estado
  (`source=IMAGE`, `transcription_status`) e suas imagens (metadados), SEM expor
  `storage_filename`. A imagem em si continua só por download autenticado
  (`GET /v1/answer-images/{id}/download`, já existente).
- **Frontend:** a tela `/respostas/foto` passa a **buscar do backend** as respostas
  por imagem persistidas da avaliação/questão selecionada ao carregar e após troca,
  exibindo-as (com estado "aguardando transcrição") além dos envios da sessão.
  Retomada funciona após **reload** e em **nova sessão**.

## 3. Fora de escopo (NÃO entra)

- Transcrição manual, confirmação humana, OCR, extração — nada disso.
- Exclusão/retenção de imagens (BL-AV-4B-05 segue pendente).
- Qualquer correção/disparo de IA sobre resposta por imagem (bloqueio permanece).
- Alteração do fluxo textual.

## 4. Regra de autorização (crítica — leitura histórica)

O contrato homologado autoriza **leitura por propriedade**, sem exigir vínculo
ativo de turma (padrão de `list_assessments`/`get_assessment`/`_get_owned_assessment`:
`owner_id == user.id` para professor; admin vê tudo). A listagem desta fatia é
**leitura histórica** e DEVE seguir esse padrão:
- **NÃO** usar `require_assessment_mutation` nem `require_active_class_link` na
  leitura (isso é regra de mutação/upload, não de consulta).
- Professor dono da avaliação lê suas respostas por imagem mesmo que o vínculo
  ativo com a turma não exista mais (consulta histórica preservada).
- Professor não-dono: 403. Sem autenticação: 401.

## 5. Contrato proposto (menor mudança coerente)

- `GET /v1/assessments/{assessment_id}/image-answers?question_id=<opcional>`
  - Autorização: `_get_owned_assessment` (propriedade; admin vê tudo). Sem vínculo ativo.
  - Resposta: `list[AnswerWithImagesOut]` (reusa o schema já homologado), filtrada
    a `source == IMAGE`, ordenada por `created_at`. Se `question_id` informado,
    restringe à questão (validando que pertence à avaliação).
  - Não cria, não altera, não dispara nada. Somente leitura.
- Reuso: `AnswerWithImagesOut`/`AnswerImageOut` já existem; nenhuma migração nova.

## 6. Critérios de aceite (ACD — DEBT-AV-014)

| ID | Critério | Método |
|---|---|---|
| ACD-01 | `GET` lista as respostas por imagem persistidas da avaliação (source=IMAGE), com estado e imagens; não inclui respostas textuais | integração real |
| ACD-02 | Filtro por `question_id` restringe corretamente; question de outra avaliação -> 404/validação | integração real |
| ACD-03 | Autorização de leitura por propriedade: dono 200; não-dono 403; sem token 401 | integração real |
| ACD-04 | **Leitura histórica**: dono SEM vínculo ativo com a turma ainda lê (200) — leitura não exige vínculo ativo | integração real (avaliação com class_group_id, sem ProfessorClassLink) |
| ACD-05 | `storage_filename` nunca exposto; imagem só por download autenticado | integração real + inspeção |
| ACD-06 | Frontend: ao abrir/recarregar a tela e em nova sessão, as respostas por imagem persistidas aparecem (retomada), com estado "aguardando transcrição" | validação visual (navegador) |
| ACD-07 | Frontend: estados de carregamento, vazio ("nenhuma resposta por foto nesta seleção") e erro (com repetir) | validação visual |
| ACD-08 | Frontend: trocar avaliação/questão não exibe dados/imagens da seleção anterior | validação visual |
| ACD-09 | Bloqueio de correção permanece: resposta por imagem sem transcrição confirmada não pode ser corrigida (regressão) | teste + integração |
| ACD-10 | Fluxo textual preservado (regressão) | suíte |

## 7. Validação prevista

- Automatizada: testes do novo endpoint (ACD-01..05, 09) + suíte completa sem
  regressão (ACD-10).
- PostgreSQL isolado descartável; navegador real para ACD-06/07/08 (reload e nova
  sessão). Exclusivamente dados fictícios. Bancos protegidos não tocados.

## 8. Papéis

Claude Code implementa; Antigravity revisa de forma independente; Codex só diante
de risco concreto. Hermes faz verificação independente própria.

## 9. Limites

Sem stage/commit/push nesta fatia. Sem bancos protegidos, migração operacional, P5,
seed operacional, deploy, baseline, OCR ou transcrição manual. 19/70 preservado;
AV-S05B parcial; BL-AV-4B-05 pendente.
