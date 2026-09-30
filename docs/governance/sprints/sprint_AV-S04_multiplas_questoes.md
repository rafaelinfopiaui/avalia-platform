---
id: "AV-S04"
status: planejamento_publicado_aguardando_decisoes_e_aprovacao
objetivo_aprovado_por: "pendente (planejamento autorizado por Rafael em 2026-09-30; sprint em si ainda não aprovada para execução)"
consolidador: "Hermes"
baseline_entrada: "main@ba6f4074f49f87461c515081964a2aff6202e6cb (PR #5 + PR #6 integrados nesta mesma data)"
depende_de: "AV-S03 (homologada e integrada); independente da coleta manuscrita de AV-S05B"
---

# AV-S04 — Múltiplas questões por avaliação (planejamento)

> **ESTE DOCUMENTO É PLANEJAMENTO, NÃO EXECUÇÃO.** Nenhum código de AV-S04
> foi escrito, testado ou integrado. Nenhuma implementação está autorizada
> a partir deste documento; a autorização cobriu explicitamente apenas a
> preparação e publicação canônica deste planejamento, sem depender da
> coleta manuscrita de AV-S05B e sem iniciar a sprint.

## 1. Objetivo e posição na trilha

Permitir que uma avaliação contenha, ordene, edite e publique **múltiplas
questões**, preservando:

- os limites de autorização por vínculo professor↔turma já corrigidos em
  AV-S01/AV-S03;
- o significado histórico de respostas, rubricas, correções e revisões
  humanas já registradas — nenhuma operação permitida pode reescrever o
  contexto de uma correção existente.

Backlog coberto: `BL-AV-3-01` a `BL-AV-3-04` (ver
[`backlog_tecnico_avalia.md`](../backlog/backlog_tecnico_avalia.md) linhas
86–89 e 307–310).

Dependência real: AV-S04 depende tecnicamente da estrutura acadêmica e do
padrão de autorização homologados e integrados em AV-S03
(`DEC-AV-026`/`DEC-AV-027`, PR #3). **Não depende** da coleta manuscrita ou
da investigação de OCR de AV-S05B — são eixos tecnicamente independentes.

## 2. Evidência de código inspecionada nesta preparação

- `core/app/models.py`: `Assessment` já modela relação 1:N com `Question`
  (`Assessment.questions`); não há campo de ordenação (`position`) em
  `Question`.
- `core/app/schemas.py`: `AssessmentCreate.question` permanece **singular**;
  `AssessmentOut.questions` já é plural. Ou seja, o modelo de dados já
  comporta múltiplas questões, mas o contrato de criação e os endpoints
  atuais ainda operam sobre uma questão por vez.
- `core/app/main.py`: `POST /v1/assessments` cria com base no payload
  singular; `PATCH /v1/assessments/{id}` só atualiza `title`.
- `frontend/src/types.ts`: `Assessment` já aceita opcionalmente tanto
  `question?` quanto `questions?: Question[]`, mas o fluxo de criação do
  editor ainda envia o payload singular.
- `frontend/src/services/api.ts`: `updateAssessment` usa `PUT`, enquanto o
  Core expõe `PATCH` — inconsistência preexistente, não introduzida por
  este planejamento, que precisa de correção dentro do escopo de
  `BL-AV-3-04`.
- Nenhuma implementação de múltiplas questões foi iniciada; a lacuna é
  exatamente a diferença entre o modelo de dados (já plural) e o contrato
  de API/frontend (ainda singular).

## 3. Decisões que Rafael precisa tomar antes de `status: ready`

1. **Estratégia de conteúdo publicado (recomendado: publicação imutável).**
   Após publicar, título, ordem/conteúdo das questões e rubricas tornam-se
   imutáveis; uma mudança posterior exige clonar a avaliação em um novo
   rascunho, preservando IDs e correções antigas. Alternativa mais flexível
   (versionamento lógico de questão) expande consideravelmente schema,
   API e risco de migração.
2. **Contrato de criação e compatibilidade.** Recomendado: `questions:
   list[QuestionInput]` com pelo menos um item como contrato canônico;
   decidir se o payload singular `question` permanece aceito
   temporariamente como alias depreciado ou é rejeitado imediatamente.
3. **API de edição de rascunho.** Recomendado: endpoints explícitos de
   coleção (`POST`, `PATCH`, `DELETE`, reordenação) em vez de substituir a
   lista inteira, para preservar IDs e evitar perda destrutiva acidental.
4. **Regra de ordenação.** Recomendado: campo inteiro persistido
   `position`, único por avaliação, retornado sempre ordenado.
5. **Fluxo de resposta.** Recomendado: uma resposta continua vinculada a
   uma questão; a interface exige seleção explícita da questão, sem
   submissão de toda a avaliação em uma única chamada.
6. **Pontuação.** Decidir se o total da avaliação é apenas a soma das
   `max_score` das questões (recomendado, sem estado redundante) ou se
   passa a existir um total persistido separado.
7. **Limites mínimo/máximo de questões e de tamanho de texto.** Mínimo
   recomendado: uma questão para publicar. Máximo e limites de tamanho
   exigem decisão explícita de produto/segurança, não valor arbitrário.

## 4. Critérios de aceite propostos para revisão da sprint

- **AC-01 / BL-AV-3-01:** professor com vínculo ativo à turma cria um
  rascunho com pelo menos duas questões ordenadas, cada uma com sua
  própria pontuação máxima e rubrica.
- **AC-02 / BL-AV-3-01:** `GET /v1/assessments/{id}` retorna cada questão
  exatamente uma vez, em ordem determinística.
- **AC-03 / BL-AV-3-02:** questões de rascunho podem ser adicionadas,
  editadas, removidas e reordenadas apenas pelo dono autorizado; a mesma
  operação por outro professor retorna `403` sem alterar estado.
- **AC-04 / BL-AV-3-02:** a publicação falha atomicamente se qualquer
  questão não tiver rubrica válida ou se o total da rubrica divergir da
  pontuação máxima da questão.
- **AC-05 / BL-AV-3-02:** após publicada, título, conteúdo/ordem das
  questões e rubricas não podem ser alterados pelos endpoints públicos.
- **AC-06 / BL-AV-3-03:** uma resposta e correção criadas para uma questão
  publicada continuam expondo o mesmo enunciado, contexto de referência e
  versão de rubrica após qualquer operação permitida posteriormente.
- **AC-07 / BL-AV-3-03:** o endpoint de contexto de revisão resolve a
  questão e rubrica exatas associadas à correção, não "a primeira questão"
  da avaliação.
- **AC-08 / BL-AV-3-04:** o OpenAPI expõe entrada/saída plural de questões
  e todas as respostas de mutação/erro; os tipos do frontend correspondem
  ao contrato gerado/verificado.
- **AC-09:** o frontend permite criar e editar pelo menos dois blocos de
  questão/rubrica, reordená-los visivelmente, publicar apenas quando
  válido e selecionar uma questão específica para responder.
- **AC-10:** todos os testes existentes de Core, AI Engine e frontend
  permanecem verdes; registros legados de questão única continuam
  legíveis.

## 5. Plano de execução detalhado (arquivo completo)

O plano de execução tarefa-a-tarefa completo — com testes, arquivos, riscos
e comandos — foi elaborado com a skill `plan` e está preservado em:

`/Users/rafaeloliveira/Projeto Estágio/.hermes/plans/2026-09-30_170000-av-s04-multiplas-questoes.md`

Esse arquivo local não é o documento canônico de governança; é o rascunho
de trabalho que originou este sprint document. Cobre 9 tarefas: contrato
com testes falhando, ordenação determinística, contrato plural de criação,
mutações de rascunho autorizadas, preservação de correções históricas,
alinhamento OpenAPI/frontend, editor de múltiplas questões no frontend,
fluxo de resposta/revisão ciente da questão exata, e validação ponta a
ponta com encerramento de governança.

## 6. Recomendações concretas do consolidador para cada decisão pendente

Recomendações objetivas, para acelerar a decisão de Rafael — nenhuma foi
adotada como aprovada:

1. Publicação imutável com clonagem explícita para nova versão. Menor
   risco de reescrever contexto de correções já existentes; versionamento
   lógico completo pode ser reavaliado depois se a imutabilidade se
   mostrar operacionalmente limitante.
2. Contrato `questions` plural como único contrato aceito desde o início
   (sem alias `question` singular). O produto ainda não está em produção
   com dados singulares reais fora do que já foi homologado; manter dois
   contratos aumenta superfície de erro sem benefício comprovado.
3. Endpoints explícitos de coleção (`POST`/`PATCH`/`DELETE`/reordenação)
   em vez de substituição da lista inteira. Reduz risco de perda
   destrutiva acidental e preserva IDs para rastreabilidade de correções.
4. Campo `position` inteiro, persistido, único por `(assessment_id,
   position)`, populado via migração Alembic com backfill determinístico.
5. Uma resposta por questão, seleção explícita pelo aluno/professor na
   interface. Consistente com o modelo atual de `Answer.question_id`, sem
   exigir reformulação do fluxo de correção.
6. Total da avaliação derivado por soma das `max_score`, sem estado
   redundante persistido — reduz risco de inconsistência entre total
   armazenado e soma real.
7. Mínimo de 1 questão para publicar; máximo e limites de tamanho ficam
   como decisão explícita de Rafael, já que envolvem trade-off de produto
   sem precedente técnico interno para inferir automaticamente.

## 7. O que este planejamento não autoriza

- Não autoriza abrir branch de implementação de código de AV-S04.
- Não autoriza migração Alembic real, nem contra ambiente isolado nem
  contra `avalia_dev`.
- Não autoriza alteração de `core/app/models.py`, `schemas.py`,
  `main.py`, ou qualquer arquivo de frontend listado na seção 5 do plano
  detalhado.
- Não promove baseline, não faz deploy, não executa saneamento
  operacional.
- Não torna a coleta manuscrita de AV-S05B pré-requisito de AV-S04, nem o
  inverso.

## 8. Checklist de Definition of Ready (ainda em aberto)

- [ ] decisões da seção 3 explicitamente resolvidas por Rafael;
- [ ] `status` deste documento alterado de
      `planejamento_publicado_aguardando_decisoes_e_aprovacao` para
      `ready` ou equivalente, por decisão explícita de Rafael;
- [ ] base Git exata e trabalho local pendente registrados no momento da
      abertura da execução (rito de `execution_policy.md` §3);
- [ ] política de compatibilidade de API aprovada;
- [ ] estratégia de migração/backfill revisada contra o schema real, sem
      tocar `avalia_dev`;
- [ ] ambientes de teste e procedimento de validação em navegador
      definidos;
- [ ] arquivos/responsáveis e revisores independentes nomeados;
- [ ] autorizações de implementação, Git e ações remotas registradas
      separadamente desta autorização de planejamento.
