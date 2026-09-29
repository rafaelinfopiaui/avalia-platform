---
id: "RECONCILIACAO-2026-09-29-02"
tipo: reconciliacao_documental
sprint: "AV-S03 (encerramento) / governanca geral"
gerado_em: "2026-09-29T00:00:00-03:00"
autor_execucao: "Hermes"
decisao_de: "Rafael"
---

# Reconciliação do conteúdo do PR #2 contra `main` — 2026-09-29

## Contexto

O PR #2 (`docs/av-s02-encerramento-planos-operacionais` → `main`) foi aberto
em 2026-09-24, antes da implementação e integração completa da `AV-S03`
(PR #3, merge commit `c391865`, 2026-09-29). Rafael solicitou explicitamente
que, antes de propor o fechamento do PR #2, seu conteúdo fosse comparado
contra `main` e classificado, e que o conteúdo ainda necessário fosse
preservado em versão atualizada por branch/PR.

## Classificação item a item

| Arquivo do PR #2 | Classificação | Evidência |
|---|---|---|
| `docs/governance/registers/decisions.md` (adição de `DEC-AV-022` com detalhe do desvio de processo) | **já incorporado** | `git diff origin/main...7f18ec3 -- decisions.md` mostra apenas a linha `DEC-AV-022`, idêntica à já presente em `main` (confirmado por `git show origin/main:decisions.md \| grep DEC-AV-022`) |
| `docs/governance/execution_policy.md` (regra: toda mudança versionada segue branch+PR) | **ainda necessário e ausente** | Não presente em `main`. Reincorporado nesta branch (ver seção seguinte) |
| `docs/governance/sprints/sprint_AV-S02...md` §19.8 (3 estados distintos: código/CI, `avalia_dev`, baseline; evidência SQL completa do desvio) | **parcialmente incorporado** — o resumo está em `DEC-AV-022` (main); o detalhamento com evidência SQL completa não está em nenhum lugar de `main` | Reincorporado nesta branch em versão consolidada (este documento, seção "Detalhamento preservado") |
| `docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md` (plano completo de saneamento + aplicação da migração `7b1d6d853f20` em `avalia_dev`, 352 linhas) | **ainda necessário e ausente** | Não presente em `main`. Reincorporado nesta branch em versão atualizada (ver seção "Plano de saneamento"), com estado de `avalia_dev` reconfirmado nesta data por leitura read-only |
| `docs/governance/sprints/sprint_AV-S03_estrutura_academica.md` (versão do PR #2) | **superado** | É a versão de planejamento de 2026-09-24 (`status: planejada_aguardando_aprovacao`), anterior a qualquer implementação. A versão real, executada, homologada (`DEC-AV-027`) e integrada está em `main` desde o merge do PR #3 |
| `docs/governance/executive_technical_dashboard.md` | **superado** | Captura o estado de 2026-09-24 (AV-S03 "não iniciada"); `main` já reflete a AV-S03 completa e integrada, informação mais recente e mais precisa |
| `docs/governance/snapshots/latest_execution.md` | **superado** | Mesmo motivo — aponta para uma execução intermediária de 24/09, superada por execuções posteriores já refletidas em `main` |
| `docs/governance/snapshots/snapshot_EXEC-2026-09-24-08_planos-saneamento-av-s03.md` (novo) | **superado como registro-ponteiro** | O conteúdo relevante (os dois planos) é preservado separadamente nesta reconciliação; o snapshot em si, como registro de uma execução intermediária já superada, não precisa ser trazido à parte |

## Detalhamento preservado (do §19.8 do PR #2, consolidado e reconfirmado)

Rafael determinou, em 2026-09-24, o registro do encerramento da integração
da `AV-S02`, distinguindo três estados que não devem ser confundidos:

1. **Código integrado e CI verde:** confirmado então e ainda válido. `main`
   passou por `7f2e0032ac7971ae43db5cc2386da0de321b778f` (merge do PR #1),
   `66c95201daf893fa7b2852e0d94b20314f8d8f34` (commit documental
   subsequente, feito diretamente em `main` — ver desvio abaixo), e agora
   `c39186596ca21dc1e8bf7bd2d52f09f4a9a00598` (merge do PR #3, `AV-S03`). CI
   real verde em todos os pontos relevantes do histórico.
2. **Banco `avalia_dev` ainda sem a migração de unicidade:** reconfirmado
   nesta data (2026-09-29, leitura read-only, nenhuma escrita): `SELECT
   job_id, COUNT(*) FROM human_reviews GROUP BY job_id HAVING COUNT(*) > 1`
   retorna o mesmo grupo duplicado do job `4f56a10b-3a44-4df5-9047-
   adef7546a3c0` (3 linhas), inalterado desde 24/09. A migração
   `7b1d6d853f20`, presente no código de `main`, **não foi aplicada** a
   nenhum ambiente operacional.
3. **Baseline operacional ainda não promovido:** ainda válido.
   `docs/governance/snapshots/latest_validated_baseline.md` continua sem
   nenhum baseline promovido sob esta governança.

**Desvio de processo identificado em 2026-09-24 e registrado (não
revertido, não reescrito):** o commit `66c95201daf893fa7b2852e0d94b20314f8d8f34`
("docs(governance): registra resultado da integração do PR #1 a main") foi
feito diretamente em `main`, sem branch/PR — contrariando o fluxo de
branch dedicada + PR + CI. Rafael determinou que não seria revertido, mas
que mudanças futuras (inclusive documentais) sigam branch/PR salvo
autorização explícita em contrário. Esse resumo já está registrado em
`DEC-AV-022` (`docs/governance/registers/decisions.md`, em `main`); este
documento preserva o detalhamento completo (os 3 estados distintos com
evidência), que não estava em `main` antes desta reconciliação.

## Plano de saneamento (do PR #2, reincorporado sem alteração de conteúdo técnico)

O plano completo — inventário exato dos registros afetados, confirmação de
equivalência campo a campo, regra de seleção da revisão ativa, preservação
das demais revisões e referências de auditoria, backup e validação de
restauração em ambiente isolado, prevenção de escritas concorrentes,
comandos/verificações/plano de recuperação, e aplicação da migração
`7b1d6d853f20` após o saneamento — permanece **PROPOSTA, NÃO EXECUTADA**,
exatamente como estava classificado no PR #2. Nenhum comando deste plano foi
executado contra `avalia_dev` nesta reconciliação nem em nenhuma execução
anterior.

O conteúdo técnico integral do plano é preservado, sem alteração, em
`docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md`
(reincorporado nesta branch). Reconfirmação desta data: o inventário de
2026-09-24 (1 grupo duplicado, job `4f56a10b-...`, 3 linhas) permanece
exato — verificado por leitura read-only em 2026-09-29, sem nenhuma escrita
em `avalia_dev`.

**Este plano continua dependendo de aprovação explícita de Rafael, item por
item, antes de qualquer execução. Nenhuma execução está autorizada por este
documento.**

## Decisão sobre o PR #2

Com o conteúdo necessário preservado em versão atualizada nesta branch
(`docs/av-s03-encerramento-integracao`, PR #4), a recomendação é: **fechar o
PR #2 sem merge**, pois:
- o conteúdo já incorporado (`decisions.md`) não precisa ser reaplicado;
- o conteúdo ainda necessário (`execution_policy.md`, detalhamento do
  desvio, plano de saneamento) foi reincorporado aqui, em versão
  reconfirmada contra o estado atual;
- o conteúdo superado (dashboard, latest_execution, documento de sprint
  AV-S03 de planejamento, snapshot intermediário) aplicado sobre o `main`
  atual reverteria informação mais recente e mais precisa (a integração
  real da AV-S03).

Decisão final de fechar o PR #2 cabe a Rafael — este documento apenas
prepara a base para essa decisão, conforme solicitado; nenhuma ação sobre o
PR #2 foi tomada nesta reconciliação.
