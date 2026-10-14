---
id: "AV-S08B"
status: "publicada em PR rascunho #18, sem merge — aguardando homologação de Rafael"
objetivo_aprovado_por: Rafael (2026-10-14, nesta conversa)
consolidador: "Hermes"
baseline_entrada: "main HEAD e8b08646cfee5e9fea70d8e9bbcb4cf39f5a3d2d (merge PR #17, DEBT-AV-014 integrada)"
---

# AV-S08B — Transcrição manual e confirmação humana (Etapa 4B, subseção D, parte manual)

> Identificador novo na numeração de sprints desta trilha (as sprints AV-S07B
> ficam reservadas para a parte de OCR/extração automática, ainda não
> autorizada; esta é a parte manual, que não depende de OCR). Itens do
> backlog canônico já existentes (`BL-AV-4B-10/11/13/14/15`), parcialmente
> cobertos nesta sprint — ver `plano_transcricao_manual_confirmacao_humana.md`
> §1 para a distinção exata parcial/integral por item.

## 1. Objetivo e valor esperado

Permitir que o professor digite manualmente a transcrição de uma resposta
por imagem já persistida (`DEBT-AV-014`/`DEC-AV-037`), salvando rascunhos
recuperáveis, confirmando explicitamente o texto final, e assim liberando a
mesma ação de solicitação de correção já existente para o fluxo textual —
sem OCR, sem disparo automático de correção, com controle de concorrência
real contra edição simultânea entre abas/sessões.

## 2. Origem

| Fonte/requisito | Trecho ou decisão aplicável | Link |
|---|---|---|
| `BL-AV-4B-10` (parcial) | Tela de conferência imagem+texto lado a lado | `backlog_tecnico_avalia.md` linha 371 |
| `BL-AV-4B-11` (parcial) | Edição/confirmação da transcrição; preservação de histórico | linha 372 |
| `BL-AV-4B-13` (coberto integralmente) | Transcrição manual quando a extração falhar — aqui, único caminho disponível (sem OCR) | linha 374 |
| `BL-AV-4B-14` (coberto) | Vincular resposta confirmada; impedir correção antes da confirmação | linha 378 |
| `BL-AV-4B-15` (parcial) | Cadeia imagem→(OCR ausente)→transcrição confirmada→correção→revisão | linha 379 |
| `DEC-AV-037` | resposta por imagem nasce "aguardando transcrição"; correção bloqueada até confirmação | `decisions.md` |
| `DEC-AV-039` | homologação/integração de DEBT-AV-014 (retomada de respostas por imagem), pré-requisito desta sprint | `decisions.md` |
| `DEC-AV-040` | DP-1/DP-2/DP-3 aprovadas + controle de concorrência exigido | `decisions.md`, aprovada 2026-10-14 |
| Pedido desta conversa (2026-10-14) | autorização explícita de planejamento e execução LOCAL da fatia manual | corpo da conversa |

Lacunas de fonte: nenhuma — os itens já constavam no backlog canônico desde
a formalização da Etapa 4B (GOV-003).

## 3. Escopo

### 3.1 Entra nesta sprint
- Backend: 2 endpoints de mutação (`PATCH .../manual-transcription/draft`,
  `POST .../manual-transcription/confirm`), modelo de dados ampliado em
  `Answer` (3 colunas nullable + 1 inteiro de versão), reuso de `AuditEvent`
  para histórico, controle de concorrência por versão.
- Frontend: tela de conferência (imagem + campo de texto), ações distintas
  de salvar rascunho e confirmar, aviso de confirmação definitiva, mensagens
  de conflito compreensíveis.
- Testes automatizados cobrindo ACD-01 a ACD-17 do plano técnico.
- Validação em ambiente isolado (HTTP real + navegador real + concorrência
  real).

### 3.2 Não entra nesta sprint
- OCR, extração automática, preparação de imagem (`BL-AV-4B-06/07/08/09`).
- Sinalização de incerteza de leitura (`BL-AV-4B-12`, inaplicável sem OCR).
- Reabertura/retificação pós-confirmação (DP-2 fechou: fatia futura).
- Múltiplos rascunhos concorrentes selecionáveis (DP-1 fechou: um atual).
- Qualquer migração operacional, P5, seed operacional, deploy, baseline.

## 4. Baseline e estado de abertura

Baseline: `main` HEAD `e8b08646cfee5e9fea70d8e9bbcb4cf39f5a3d2d` (merge commit
do PR #17, DEBT-AV-014 integrada — confirmado por `git log --oneline main -1`
nesta mesma sessão). Branch de planejamento documental:
`docs/av-s08b-plano-transcricao-manual` (local, não publicada). Branch de
implementação a criar a partir desta mesma base: `feat/av-s08b-transcricao-manual`.

## 5. Backlog e DoR (Definition of Ready)

- [x] Plano técnico escrito e revisado (Antigravity, 2 rodadas: completa +
  limitada pós-decisão).
- [x] Decisões de produto aprovadas (`DEC-AV-040`).
- [x] Nomenclatura real do código conferida (`AnswerSource`,
  `TranscriptionStatus`, `Rubric.version` como precedente de versionamento).
- [x] Critérios de aceite definidos antes do código (ACD-01 a ACD-17).
- [x] Mapa de impacto definido (§6 abaixo).

## 6. Mapa de impacto

| Item | Criar | Alterar | Não tocar |
|---|---|---|---|
| Modelo de dados | — | `core/app/models.py` (`Answer`: +4 colunas nullable/default — `manual_transcription_draft`, `transcription_confirmed_by_id`, `transcription_confirmed_at`, `transcription_version`); `core/alembic/versions/` (nova migração aditiva) | `AnswerImage`, `CorrectionJob`, `HumanReview`, `AuditEvent` (reusados sem alteração de schema) |
| Backend — endpoints | `core/app/main.py` (2 novos endpoints: `PATCH .../manual-transcription/draft`, `POST .../manual-transcription/confirm`) | `core/app/schemas.py` (`AnswerOut`: +2 campos opcionais — `manual_transcription_draft`, `transcription_version`) | `request_correction`, `review_correction`, `list_image_answers` (DEBT-AV-014, não tocado além de herdar os novos campos via `AnswerOut`) |
| Frontend | — | `frontend/src/pages/ImageAnswerPage.tsx` (tela de conferência: campo de texto, ações draft/confirm, aviso de confirmação definitiva); `frontend/src/services/api.ts` (2 novas chamadas); `frontend/src/types.ts` (campos novos em `AnswerWithImages`) | `AnswerPage.tsx` (fluxo textual, não tocado) |
| Testes | `core/app/tests/test_manual_transcription.py` (novo, ACD-01..17) | — | suíte existente (171 testes, deve permanecer 171 passed + novos) |

Mudança fora do mapa exige registro prévio em Ajustes de Percurso (§14 do
padrão de sprint, a preencher durante a execução se necessário).

## 7. Decisões necessárias (já resolvidas antes do código)

Diferente da sprint AV-S06B original (que tinha decisões de implementação
propostas mas não aprovadas), esta sprint só inicia código com as decisões
de produto já fechadas:

| Decisão | Resolução | Registro |
|---|---|---|
| DP-1 — múltiplos rascunhos vs. único | Um rascunho atual, histórico via AuditEvent | `DEC-AV-040` §2.1 |
| DP-2 — reabertura pós-confirmação | Sem reabertura nesta fatia; confirmação definitiva | `DEC-AV-040` §2.2 |
| DP-3 — reconfirmação com correção existente | Sempre conflito 409, nunca dispara correção automaticamente | `DEC-AV-040` §2.3 |
| Controle de concorrência | Versão incremental (`transcription_version`), mesmo padrão de `Rubric.version` | `DEC-AV-040` §2.4 |

## 8. Critérios de aceite

Ver `evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md` §11
para a tabela completa ACD-01 a ACD-17 (fonte canônica dos critérios,
mantida em um único lugar para não divergir entre documentos). Resumo por
categoria:
- **Rascunho**: ACD-01, ACD-01B, ACD-04 (parte vazia), ACD-15.
- **Confirmação**: ACD-02, ACD-03, ACD-04, ACD-06, ACD-07.
- **Autorização**: ACD-05, ACD-14.
- **Não-disparo automático / liberação de correção**: ACD-08, ACD-09, ACD-11.
- **Histórico/auditoria**: ACD-10.
- **Regressão textual**: ACD-12.
- **Interface**: ACD-13.
- **Concorrência**: ACD-15, ACD-16, ACD-17.

## 9. Definition of Done

- [x] Todos os ACD-01..17 com evidência real (HTTP real em PostgreSQL
  isolado; concorrência real via threads/conexões simultâneas, não apenas
  sequencial; navegador real para ACD-13).
- [x] Suíte completa sem regressão (171 pré-existentes + novos).
- [x] `ruff check` e build/tsc do frontend limpos.
- [x] Revisão independente do Antigravity da implementação (completa, não
  limitada — diferente da revisão de plano desta rodada).
- [x] AI Engine do teste identificado explicitamente como real ou simulado
  (requisito direto de Rafael nesta autorização).
- [x] Bancos protegidos (`avalia_dev`, apresentação) auditados intactos
  antes e depois.
- [x] Governança atualizada (snapshot de encerramento, dashboard,
  `technical_debts.md`/backlog — sem encerrar itens mais amplos que a parte
  manual entregue).
- [x] Diff local revisado, pacote recuperável, parecer e limitações
  apresentados — sem stage/commit/push/merge nesta rodada.

## 10. Validações previstas

Ambiente isolado e descartável (PostgreSQL próprio, Core próprio,
`ACADEMIC_MODULE_ENABLED=false`), navegador real (Chrome via CDP), dados
fictícios. Cenários obrigatórios (pedido direto de Rafael):
1. Recuperação do rascunho após reload e nova sessão.
2. Autorização e regras vigentes de mutação por vínculo (`require_assessment_mutation`).
3. Texto vazio/inválido rejeitado na confirmação.
4. Edição concorrente de rascunho e confirmação com versão desatualizada
   (conflito real, não apenas sequencial).
5. Confirmação repetida (idempotente) e tentativa de alteração posterior
   (conflito).
6. Nenhuma correção iniciada automaticamente pela confirmação.
7. Solicitação de correção bloqueada antes da confirmação, permitida depois.
8. Preservação do texto efetivamente usado pela correção e pela revisão
   humana final (rastreabilidade).

AI Engine do teste: identificado explicitamente como real ou simulado no
relatório de execução — nenhuma evidência de um modo é atribuída ao outro.

## 11. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Condição de corrida real não reproduzida em teste sequencial | ACD-15/16 exigem concorrência real (threads/conexões simultâneas contra PostgreSQL), não apenas chamadas sequenciais simulando concorrência |
| Confusão entre "confirmação" desta fatia (manual) e um futuro "confirmação" de OCR revisado | nomenclatura das colunas sem prefixo `manual_` nas de confirmação (`transcription_confirmed_by_id/_at`), decidido na revisão do Antigravity, reduz retrabalho futuro |
| Encerrar prematuramente itens de backlog mais amplos (`BL-AV-4B-10/11`) | marcados explicitamente como "parcial" em todo documento; backlog não será editado para "concluído" nesta sprint |

## 12. Estimativas

Não aplicável formalmente (trilha não usa estimativa de prazo); escopo
definido é implementável em uma rodada de execução local, análoga em
tamanho à fatia DEBT-AV-014 recém-concluída (2 endpoints, 1 tela, suíte
de testes, validação isolada).

## 13. Critérios de encerramento

Sprint encerra (localmente, sem publicação nesta rodada) quando: todos os
ACD-01..17 tiverem evidência real reportada por tipo; suíte completa sem
regressão; revisão independente do Antigravity concluída (aprovado ou
aprovado com ressalvas registradas); governança atualizada; diff local e
pacote recuperável apresentados a Rafael para decisão de publicação em
rodada futura (não incluída aqui).

**Atualização (2026-10-14, publicação autorizada por Rafael):** os
critérios acima foram cumpridos; Rafael autorizou publicar em PR rascunho,
sem merge. Publicação concluída — PR
[#18](https://github.com/rafaelinfopiaui/avalia-platform/pull/18), SHA
`92edce4013ba5688be4e4ff99fdf249a677636f3`, CI 3/3 checks pass, sem merge.
Ver `snapshot_EXEC-2026-10-14-10_publicacao_av-s08b.md` para o detalhamento
completo da publicação. Homologação permanece decisão de Rafael.

## 14. Ajustes de percurso

- **D-1 (2026-10-14, Claude Code, avaliado por Antigravity ACH-01 e aceito):**
  `AnswerOut` ganhou 2 campos além dos previstos no mapa de impacto §6
  (`manual_transcription_draft`, `transcription_version`): também
  `transcription_confirmed_by_id` e `transcription_confirmed_at`. Motivo:
  requisito de UX do §3.3 do plano técnico ("quem confirmou e quando") não é
  atendível sem expor esses campos no DTO. Mudança aditiva, retrocompatível,
  restrita a quem já pode ler a resposta. Não altera contrato de nenhum
  endpoint existente.
- **D-2 (2026-10-14, Claude Code, avaliado por Antigravity ACH-02 e aceito):**
  `frontend/src/services/api.ts`, função `send()`: passou a repassar `details`
  do corpo de erro HTTP ao `ApiError` (antes descartado). Motivo: o contrato
  de 409 do plano (§3.3/§6) devolve `details.current_answer` para o cliente
  decidir em conflito de versão; sem isso o frontend não tem acesso ao dado.
  Aditivo — nenhum consumidor pré-existente lia `details`.
- **ACD-13 e parte "navegador real" de ACD-01B**: não cobertos pelo executor
  nem pelo revisor (ambos restritos a `tsc`/build/lint); **validados
  posteriormente pelo Hermes em navegador real** (rascunho, reload, bloqueio
  de outro professor, revisão em 2 passos, confirmação, liberação de
  correção) — ver `snapshot_EXEC-2026-10-14-08_encerramento_av-s08b.md` §4.
- **D-3 (2026-10-14, delta pós-conclusão, dentro do escopo já autorizado —
  sem nova decisão de produto):** adicionado o caminho de interface para
  solicitar correção da resposta IMAGE confirmada (botão "Solicitar análise
  da IA" em `ImageAnswerPage.tsx`, visível só após confirmação, reutilizando
  `requestCorrection` já existente — zero endpoints novos). Revisão
  independente do Antigravity (só o delta): APROVADO, sem ressalva
  bloqueante. Ver `snapshot_EXEC-2026-10-14-09_conclusao_escopo_av-s08b.md`
  §2.
- **Validação de integração completa** (foto→rascunho→confirmação→correção→
  revisão humana final) executada com AI Engine real em modo simulado
  explícito, fechando a lacuna que a validação visual anterior (engine morto
  de propósito) não cobria. Confirmado por banco de dados que o texto
  enviado à IA é exatamente o texto confirmado e que o `CorrectionJob` usa o
  mesmo `answer_id` da resposta original. Ver
  `snapshot_EXEC-2026-10-14-09_conclusao_escopo_av-s08b.md` §3.
- **Reconciliação de `DEBT-AV-014`**: o registro em `technical_debts.md`
  dizia incorretamente "integração aguarda o merge efetivo do PR #17"; o
  merge já havia ocorrido (`e8b0864`, baseline desta própria sprint).
  Corrigido com nota de reconciliação datada, sem apagar o texto histórico.

## 15. Papéis de execução

Claude Code executor principal. Antigravity revisão independente completa
da implementação (a revisão do plano já foi feita em 2 rodadas — completa e
limitada). Codex só diante de risco concreto identificado durante a
execução, não revisão geral.
