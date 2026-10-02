# EXEC-2026-10-01-03 — Retomada da preparação de `avalia_dev` após interrupção de cota

---
id: "EXEC-2026-10-01-03"
tipo: "retomada_execucao_local_sem_git"
consolidador: "Hermes"
data: "2026-10-01"
autorizado_por: "Rafael (2026-10-01; mesma autorização da rodada preparatória completa sem escrita em avalia_dev — esta é uma retomada de trabalho, não uma nova autorização de escopo)"
carater: "retomada_apos_interrupcao_tecnica"
---

## Motivo do registro

A execução foi interrompida por `HTTP 429: The usage limit has been reached`
durante uma chamada de API (não por decisão do usuário nem por bloqueio de
governança). Rafael solicitou retomada explícita do trabalho pendente, sem
reinterpretar o esgotamento de cota como perda de autorização nem como
licença para ampliar escopo.

## Última demanda efetivamente autorizada antes da interrupção

Rodada preparatória completa de atualização de `avalia_dev`, **sem escrita
real em `avalia_dev`**, cobrindo:
1. consolidação do saneamento (base: proposta local de 676 linhas,
   commit `aa8031a`, incorporando as 9 melhorias GOV-006), com revisão
   independente quanto a equivalência de duplicatas, arquivamento integral,
   preservação de auditoria, assertions/locks, e recuperação após falha;
2. scripts reproduzíveis de diagnóstico, saneamento, validação e
   recuperação, mantidos locais (não é autorização de commit);
3. backup somente leitura de `avalia_dev` e restauração em PostgreSQL 16
   isolado, com ensaio da cadeia `e1b02279b1a5 → saneamento → 7b1d6d853f20
   → c4a8b2d91e37 → a9f4c2e71b06`, cobrindo falhas e retomada;
4. demonstração (flags acadêmicas + seed fictício) somente no ambiente
   isolado;
5. pacote de entrega para decisão de Rafael (scripts, diff, parecer
   independente, evidências, sequência operacional, condições de abortar/
   recuperar).

P4 (execução real em `avalia_dev`) e P5 (ativação de flags no ambiente)
permaneciam explicitamente **não autorizados**, assim como commit/push/
merge, deploy ou promoção de baseline.

## Ponto de interrupção

A interrupção ocorreu **depois** da 2ª rodada de revisão independente ter
devolvido REPROVADO (6 achados: guard do seed por substring, estado
pós-saneamento/recovery sem prova integral, idempotência fraca do seed,
`search_path` ausente no diagnóstico, cenário de falha pré-commit sintético
em vez do script real) e **antes** de uma 3ª rodada de revisão confirmar as
correções.

## Estado real inspecionado nesta retomada

- Branch: `chore/preparacao-avalia-dev-av-s04` (confirmado via
  `git branch --show-current`).
- HEAD do checkout principal: `9ab6e43` (merge do PR #9, inalterado).
- `git status --short`: apenas arquivos não rastreados esperados —
  `core/scripts/` (6 arquivos) e os dois documentos de backlog
  (`plano_atualizacao_avalia_dev_av-s04_2026-10-01.md`,
  `proposta_saneamento_human_reviews_duplicadas_v2_consolidada.md`).
  Nenhum arquivo rastreado modificado. Nenhum commit/push/merge feito.
- Backup somente leitura de `avalia_dev`, criado na rodada anterior, íntegro
  e fora do Git: `~/avalia-backups/avalia_dev_preparacao_av-s04_20261001_101850.dump`
  (modo `0600`), com checksum SHA-256 reverificado nesta retomada
  (`shasum -a 256 -c` → `OK` para dump e CSV de `human_reviews`).
- Nenhum processo em segundo plano da rodada anterior continuava ativo;
  nenhum cluster PostgreSQL temporário residual (o runner usa `trap cleanup
  EXIT` e remove `CLUSTER_DIR` ao final).

## Trabalho retomado nesta sessão

As 6 correções identificadas pela 2ª revisão independente foram aplicadas
aos arquivos locais (não versionados), reaproveitando o backup e os scripts
já existentes, sem duplicar backup nem recriar scripts do zero:

1. `seed_academic_multi_question_demo.py:require_isolated_database` —
   substituído substring-match por `urlsplit()` + `re.fullmatch` ancorado no
   nome real do banco extraído da URL.
2. `av_s02_saneamento_human_reviews.sql` (estado `is_post`) — adicionada
   exigência de `COUNT(*) FROM human_reviews_superseded WHERE job_id=<job> = 2`
   exato (nenhuma linha arquivada além das 2 nominalmente validadas).
3. `av_s02_recuperacao_saneamento.sql` (estado `recovered`) — adicionada
   exigência de `COUNT(*) FROM human_reviews WHERE job_id=<job> = 3` e
   `COUNT(*) FROM human_reviews_superseded WHERE job_id=<job> = 0`.
4. `seed_academic_multi_question_demo.py:validate_existing` — ampliada para
   comparar todos os campos determinísticos das 14 entidades (não apenas
   FKs/IDs), tornando a idempotência verdadeiramente fail-closed a drift de
   conteúdo.
5. `av_s02_diagnostico_human_reviews.sql` — adicionado `SET search_path =
   public, pg_catalog;` e qualificação explícita `public.human_reviews` /
   `public.audit_events`.
6. `run_avalia_dev_update_dry_run.sh` (cenário D) — substituída a transação
   sintética por um trigger `BEFORE DELETE` real em `human_reviews` que
   força a exceção durante a execução do próprio
   `av_s02_saneamento_human_reviews.sql` via `psql -f`, provando a
   atomicidade do script real (o trigger é removido logo após o teste).

Após as correções: `bash -n`, `py_compile` e `ruff check` green; ensaio
completo reexecutado com o backup já existente —
`ALL_DRY_RUN_SCENARIOS_GREEN` (todas as durações e asserções em
`/private/tmp/av_s02_dry_run_round3.log`, não copiado para o pacote público
pois contém apenas texto efêmero de console, não dados reais).

Uma 3ª rodada de revisão independente (subagente dedicado, mesmo padrão das
rodadas anteriores) foi disparada para confirmar objetivamente as 6
correções antes de fechar o pacote.

## Resultado da 3ª rodada de revisão independente

**APROVADO, sem ressalvas.** O subagente revisor leu os 6 arquivos linha a
linha, cruzou `seed_academic_multi_question_demo.py` contra
`core/app/models.py` campo a campo, e confirmou que as 6 correções fecham
exatamente os achados da rodada 2, sem enfraquecer nenhum guard existente e
sem introduzir novo bloqueador. Parecer completo arquivado em
`docs/governance/evidence/AV-OPER-001-avalia-dev-preparacao/parecer_independente_rodada3_2026-10-01.md`.

Com isso, a preparação (P1–P3) está tecnicamente concluída e pronta para a
decisão de Rafael sobre P4 (execução real) e P5 (ativação de flags).

> **Proveniência desta seção e da seguinte (2026-10-02):** o texto abaixo
> ("Publicação do PR #10" e "Intervenção do Codex antes da integração")
> foi originalmente escrito por Hermes em 2026-10-01/02, mas Rafael
> instruiu explicitamente a não commitá-lo diretamente em `main` nem abrir
> um PR só para isso. Ficou preservado como pacote local recuperável em
> `~/avalia-local-packages/snapshot-update-pos-pr10-2026-10-02/`
> (diff, conteúdo completo antes/depois, checksums SHA-256 verificados) até
> esta incorporação, autorizada por Rafael junto com a publicação da
> documentação de P4 (2026-10-02). Reaplicado via `git apply` do patch
> preservado nesse pacote, contra a base `main@9310b54`, sem alteração de
> conteúdo.

## Publicação do PR #10 (2026-10-01)

Commit `6c20bb83ee1c9bee136dc1b74ff6c5bfe29a9dec` publicado na branch
`chore/preparacao-avalia-dev-av-s04`, PR #10 aberto em rascunho contra
`main`. CI verde nos 3 jobs (Frontend, AI Engine, Core API).

## Intervenção do Codex antes da integração (2026-10-02)

Enquanto o PR #10 aguardava decisão de Rafael sobre P4/P5, Rafael
interrompeu uma sessão do Codex CLI para preservar a centralização da
execução no Hermes, mas uma intervenção já havia sido publicada
diretamente por ele (Rafael, via commit do Codex) na branch:

- commit `e8a994e89e0450986f0bdbcc9e696945caa44bbc`, autor Rafael Oliveira,
  2026-10-02 09:00:16 -03:00;
- único arquivo alterado:
  `docs/governance/backlog/plano_atualizacao_avalia_dev_av-s04_2026-10-01.md`
  (10 inserções, 4 remoções);
- conteúdo verificado via `git show e8a994e` nesta sessão (não presumido):
  (1) corrige a seção 3.2 — contadores agregados de `pg_stat_user_tables`
  são sinais auxiliares com possível atraso, não identificam o autor da
  escrita nem provam ausência dela; operações autorizadas de saneamento e
  migração também alteram esses contadores, então variações devem ser
  conciliadas com as etapas/sessões autorizadas, não tratadas como prova
  automática de incidente; (2) o mesmo ajuste é propagado ao Estado 0 da
  matriz de recuperação (seção 3.8); (3) nova seção 9 registra uma
  conferência limitada das ressalvas das rodadas 4 e 5 de revisão
  independente contra o HEAD `6c20bb83e`, confirmando que todas as
  correções textuais anteriores (sequência completa no restore final,
  alternativa de recuperação do índice, referências renumeradas, REVOKE
  opcional, nota histórica, `LEFT JOIN LATERAL`, exemplo de restauração)
  estavam de fato presentes, e acrescenta a ressalva de que qualquer uso
  futuro da camada opcional de ACL precisa preservar também `grantor` e
  grant options, não apenas grantee/privilege_type — o exemplo de `GRANT`
  de restauração do documento é resumido, não um restaurador universal.
- nenhum script SQL/Python em `core/scripts/` foi tocado por este commit;
- nenhuma ação Git além deste commit documental (sem merge, sem push para
  `main`, sem alteração de PR);
- CI da rodada 37004155698 confirmada concluída nesta sessão (não
  presumida): `gh run view 37004155698` e `gh pr checks 10` retornaram os
  3 jobs (`AI Engine`, `Core API`, `Frontend`) com status `pass` sobre o
  HEAD `e8a994e`.

Avaliação desta sessão: a correção é tecnicamente válida e consistente com
o restante do documento — não introduz enfraquecimento de guard nem
contradição com as seções já revisadas independentemente. Não foi
necessário reverter nem repetir o ensaio técnico (`ALL_DRY_RUN_SCENARIOS_GREEN`
permanece válido — nenhum script executável foi alterado). A partir desta
intervenção, toda execução (Git, CI, integração) voltou a ocorrer
exclusivamente via Hermes, conforme instrução de Rafael.

## Disponibilidade de ferramentas de agente externas verificada nesta retomada

- `claude` (Claude Code CLI): binário presente e funcional
  (`claude --version` → `2.1.260`); processo anterior (`proc_e67465b1a8dc`)
  havia terminado com `Failed to authenticate: OAuth session expired` —
  sessão expirada, não cota — não foi usado nesta retomada.
- `codex` (Codex CLI): binário presente e funcional
  (`codex --version` → `codex-cli 0.150.1`).
- `agy` (Antigravity CLI): binário presente.
- Nenhuma configuração de modelo/provedor/fallback foi alterada. A revisão
  independente da 3ª rodada foi delegada via `delegate_task` (mesmo
  mecanismo das rodadas 1 e 2), não trocando provedor pago nem alterando
  configuração global.

## Pendências explícitas (sem mudança de escopo)

Idênticas às já registradas no plano consolidado (§6) e no dashboard: P1
(qual versão do saneamento adotar/ajustar — já endereçado ao adotar a base
de 676 linhas com as 9 melhorias), P3 agora **concluído** nesta rodada
(ensaio isolado completo, green), P4 e P5 seguem pendentes de decisão de
Rafael, P6 (estender seed) permanece opcional e não decidido.

Nenhuma escrita, saneamento, migração ou ativação foi feita em `avalia_dev`
nesta retomada. Nenhum commit/push/merge, deploy ou promoção de baseline.
Nenhum novo worktree ou diretório externo de trabalho foi criado.
