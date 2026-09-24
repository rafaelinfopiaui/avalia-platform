---
id: EXEC-2026-09-24-08
tipo: execucao
sprint: AV-S02-encerramento/planejamento-AV-S03
execution_scope: documental
status: planos_preparados_aguardando_aprovacao
gerado_em: "2026-09-24T10:00:00-03:00"
executor: "Hermes"
commit_referencia: 66c95201daf893fa7b2852e0d94b20314f8d8f34
---

# Snapshot EXEC-2026-09-24-08 — encerramento AV-S02 + planos de saneamento e AV-S03

> Execução documental. Nenhuma sprint funcional iniciada, nenhuma migração operacional aplicada,
> nenhum saneamento executado, nenhum baseline promovido.

## 1. Objetivo

Atender à instrução de Rafael de:
- registrar o encerramento da integração da AV-S02 distinguindo código/CI, banco operacional sem
  migração e baseline não promovido;
- registrar o commit direto em `main` (`66c9520`) como desvio, sem reverter/reescrever histórico,
  estabelecendo branch/PR como regra para toda mudança futura (inclusive documental);
- preparar para aprovação o procedimento detalhado de saneamento das 3 duplicatas fictícias e
  aplicação posterior da migração em `avalia_dev`, sem executar nada;
- preparar o plano detalhado da AV-S03, sem implementar, com premissas propostas para DEC-AV-006/007,
  distinção estrutura acadêmica vs multi-tenancy e posição do OCR na sequência.

## 2. Entregas

| Item | Estado | Entrega |
|---|---|---|
| Encerramento AV-S02 | registrado | `sprint_AV-S02...md` §19.8 — código integrado/CI verde vs banco sem migração vs baseline não promovido |
| Desvio de processo `66c9520` | registrado, não revertido | sprint §19.8, `DEC-AV-022`, `execution_policy.md` (regra branch/PR para toda mudança futura) |
| Plano de saneamento/migração | preparado para aprovação | `backlog/proposta_saneamento_human_reviews_duplicadas.md` — inventário exato, equivalência por todos os campos, vencedor proposto, preservação/auditoria, backup+restore isolado, prevenção de concorrência, comandos, pós-checks e recuperação |
| Plano AV-S03 | preparado para aprovação | `sprints/sprint_AV-S03_estrutura_academica.md` — escopo/DoR/ACs/risco/delegação, premissas DEC-AV-006/007, estrutura acadêmica ≠ multi-tenant, OCR antecipável/independente |
| Revisão independente dos planos | concluída por Codex (read-only) | parecer inicial condicional; todos os achados corrigidos: lock de tabela contra INSERT concorrente, equivalência semântica completa (`final_total`+JSON normalizado com `COALESCE`), DDL/INSERT explícitos e script SQL versionado pré-migração, recuperação compensatória/restore, pós-check nominal de AuditEvents; matriz de autorização e decisões estruturais da AV-S03; critérios críticos (incluindo AC-06) e mapa de impacto ampliados. **Gate final Codex: aprovado, nenhum bloqueante técnico restante.** Claude Code foi tentado primeiro, mas atingiu limite de sessão sem produzir revisão — autoria real registrada |
| Execução funcional | não iniciada | nenhuma linha de código/migração/UI implementada |

## 3. Evidências reais usadas no plano de saneamento

- `avalia_dev`: 8 linhas em `human_reviews`;
- exatamente 1 grupo duplicado: job `4f56a10b-3a44-4df5-9047-adef7546a3c0`, 3 linhas;
- 3 linhas idênticas em todos os campos relevantes (`reviewer_id`, `decision`, `final_total`,
  `final_scores_json`, `justification`), diferindo apenas em `id`/`created_at` — equivalentes, não
  conflitantes;
- 3 `AuditEvent` correspondentes, preservados no plano (nenhum será alterado/apagado);
- `\d human_reviews`: nenhuma `UniqueConstraint` no banco operacional;
- ferramentas disponíveis: `pg_dump`/`pg_restore` PostgreSQL 16.15.

## 4. Arquivos impactados

- `docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md`;
- `docs/governance/sprints/sprint_AV-S03_estrutura_academica.md` (novo);
- `docs/governance/sprints/sprint_AV-S02_ci_visual_isolamento_testes.md`;
- `docs/governance/execution_policy.md`;
- `docs/governance/registers/decisions.md`;
- `docs/governance/executive_technical_dashboard.md`;
- `docs/governance/snapshots/` (este snapshot + latest_execution).

## 5. Limites e estado final

- nenhuma migração/saneamento executados;
- nenhuma sprint funcional iniciada;
- AV-S03 permanece `planejada_aguardando_aprovacao`;
- DEC-AV-006/007 continuam pendentes — premissas rotuladas, não resolvidas por suposição;
- multi-tenancy explicitamente fora de escopo;
- OCR: levantamento técnico inicial continua antecipável e pode ser detalhado em paralelo, mas
  ainda não tem sprint detalhada aprovada/executada; entrada por imagem continua prioritária sobre
  CSV;
- nenhuma tag/deploy/baseline;
- mudanças em branch `docs/av-s02-encerramento-planos-operacionais`, PR em rascunho para revisão de
  Rafael (não merge automático).
