---
id: "EXEC-2026-10-15-01"
tipo: execucao
sprint: "BL-AV-4B-05 (retenção e exclusão de imagens) — planejamento técnico"
gerado_em: "2026-10-15T01:40:00-03:00"
executor: "Hermes (análise dirigida e desenho técnico)"
status: "planejamento concluído; implementação não autorizada nesta rodada"
base: "main e21332ae1335cab7e90eb9db8450e29865057b53"
branch: "docs/bl-av-4b-05-plano-retencao-exclusao-imagens"
---

# Snapshot EXEC-2026-10-15-01 — Planejamento técnico de BL-AV-4B-05 (retenção/exclusão de imagens)

> Rafael autorizou planejamento técnico e análise dirigida, sem
> implementação ou ações Git nesta rodada. Reconfirmado antes de
> iniciar: `main` local == remoto == `e21332ae1335cab7e90eb9db8450e29865057b53`,
> working tree limpo (confirmado por `git fetch` + `git rev-parse`
> independentes). Não repetida a auditoria das entregas já homologadas
> (AV-S06B, AV-S08B) — tratadas como dado conhecido.

## 1. Escopo desta rodada

Análise do ciclo de vida real de uma imagem de resposta (levantado no
código, não presumido) e proposta concreta de desenho técnico para
`BL-AV-4B-05`, cobrindo: autorização de exclusão, exclusão lógica vs.
física, tratamento de registros associados e auditoria, retenção
configurável, falhas parciais, idempotência/concorrência, arquivos
órfãos, e alcance real de backups.

Documento completo:
[`desenho_bl-av-4b-05_retencao_exclusao_imagens.md`](../evidence/BL-AV-4B-05/desenho_bl-av-4b-05_retencao_exclusao_imagens.md).

## 2. Método

- Leitura de `DEC-AV-013` e do critério canônico de `BL-AV-4B-05`
  (`backlog_tecnico_avalia.md`), sem reabrir nenhuma decisão já tomada.
- Leitura de código real (`core/app/models.py`, `core/app/main.py`,
  `core/app/routers/images.py`, migração `d5e3a7c19f42`) para confirmar
  vínculos reais entre `Answer`, `AnswerImage`, `CorrectionJob`,
  `AIExecution`, `HumanReview`, `AuditEvent` — nenhum vínculo presumido
  sem confirmação em código.
- Nenhum teste foi executado nesta rodada (não há implementação a
  testar ainda); nenhuma auditoria geral das entregas anteriores foi
  repetida.

## 3. Achados principais

- Confirmado por ausência de `cascade`/`ondelete` nas FKs: excluir uma
  `AnswerImage` **não** excluiu/exclui automaticamente a `Answer`, nem
  vice-versa — são entidades independentes no desenho atual.
- `CorrectionJob.answer_id` é FK obrigatória sem `ondelete` — o padrão
  do PostgreSQL bloqueia (`RESTRICT`) a exclusão da `Answer` enquanto
  um `CorrectionJob` existir, reforçando que a resposta/correção
  sobrevive estruturalmente à exclusão da imagem.
- O armazenamento de imagens é só em disco (metadados no banco, bytes
  no filesystem), confirmando a necessidade de tratar exclusão lógica
  (transação de banco, atômica) e remoção física (operação de
  filesystem, pode falhar independentemente) como duas fases distintas.
- `AuditEvent` já é genérico o suficiente (campo `resource_id` livre,
  sem FK real) para sobreviver à exclusão de qualquer recurso — mesmo
  padrão já usado em `delete_question` (`core/app/main.py:500-510`),
  reaproveitável sem mudança de desenho.
- Não existe hoje nenhum mecanismo de backup automatizado para o
  filesystem de imagens — só `pg_dump` manuais do banco em rodadas
  pontuais de migração, que não cobrem os bytes da imagem.

## 4. Decisões necessárias de Rafael (resumo; tabela completa no documento)

| # | Decisão | Recomendação |
|---|---|---|
| D1 | Exclusão lógica + janela de retenção antes da física, vs. física imediata | Exclusão lógica + janela |
| D2 | Bloquear exclusão quando `CorrectionJob`/`HumanReview` já existirem, ou permitir com confirmação extra | Bloquear em C/D (estágios com correção/revisão), livre em A/B |
| D3 | Valor da janela de retenção | Nenhum default proposto — configurável, sem remoção automática até Rafael decidir um valor |

## 5. Estado resultante

- Nenhum código alterado; nenhuma migração aplicada; nenhum serviço
  iniciado; nenhum dado excluído; nenhum stage/commit/push/merge nesta
  rodada (documentação criada, não versionada ainda — ver seção 7).
- Bancos protegidos não tocados: `avalia_dev` e
  `avalia_apresentacao_demo_20261002` continuam no mesmo estado
  reportado em todas as rodadas anteriores (`a9f4c2e71b06`).
- Numerador permanece **22/70**; `BL-AV-4B-10`/`11`/`13`/`15`
  permanecem PARCIAIS; `BL-AV-4B-05` permanece **pendente** (decisão de
  produto, não implementação) — este snapshot não reivindica avanço de
  numerador.

## 6. Próximo passo (dependente de decisão de Rafael)

Após D1/D2/D3 serem decididas: Claude Code prepara a implementação
detalhada (migração aditiva + endpoint + guard de estágio); Antigravity
faz revisão independente limitada a esta fatia; Codex só diante de
risco concreto. Sequência completa de implementação/testes já proposta
na seção 9 do documento de desenho.

## 7. Nota sobre versionamento

Este snapshot e o documento de desenho foram criados nesta rodada, na
branch `docs/bl-av-4b-05-plano-retencao-exclusao-imagens`, mas
**nenhuma ação Git foi executada** (sem stage/commit/push), por
instrução explícita de Rafael nesta rodada. Publicação fica para uma
rodada futura, mediante autorização separada.
