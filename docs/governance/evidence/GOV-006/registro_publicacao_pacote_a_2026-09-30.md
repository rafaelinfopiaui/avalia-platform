# Registro de publicação — Pacote A / GOV-006

## Abertura (2026-09-30, -03:00)

- objetivo: publicar a reconciliação GOV-006 homologada, sua rastreabilidade e
  correções documentais em branch dedicada e PR em rascunho;
- checkout: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform-worktrees/gov-006-publish`;
- raiz Git: o mesmo caminho;
- branch: `docs/gov-006-reconciliacao`;
- base Git: `docs/av-s05b-investigacao@44a09b0dc602a1e7a7e0626fb9ee703891bb444d`;
- upstream planejado do PR: `docs/av-s05b-investigacao`;
- estado inicial: worktree limpo criado diretamente sobre o HEAD publicado do
  Pacote B;
- fonte local das correções: worktree `av-s03-work`, branch `main`, base original
  `a5974b1`, com alterações documentais ainda não incorporadas;
- alterações locais conhecidas fora deste pacote:
  - proposta de saneamento de 676 linhas no checkout principal, preservada mas
    não publicada como plano; somente comparação/delta entram neste pacote;
  - diretório experimental original `av-s05b-benchmark-experimento`, sem Git;
  - worktree órfão `/private/tmp/av-s03-work` continua apenas como metadado
    `prunable`, sem limpeza autorizada;
- consolidador: Hermes;
- autorização: stage/commit/push e PR em rascunho, sem merge.

## Arquivos compartilhados

- `decisions.md`: pertence ao Pacote B; A herda sem novo diff;
- `backlog_tecnico_avalia.md`, `executive_technical_dashboard.md` e
  `latest_execution.md`: pertencem à consolidação do Pacote A;
- a base B→A é obrigatória enquanto ambos permanecerem abertos.

## Fora de escopo

- merge, exclusão de branches/worktrees, deploy, promoção de baseline;
- alteração em `avalia_dev` e saneamento operacional;
- implementação funcional da AV-S04;
- homologação de OCR para produto.

## Reconciliação posterior — organização local (2026-09-30)

As linhas 16–21 acima registram o estado no momento de abertura deste pacote.
Após autorização específica e teste de recuperação isolado:

- o ambiente experimental foi movido para `experiments/av-s05b/` e permanece
  ignorado pelo Git;
- a única entrada órfã de `/private/tmp/av-s03-work` foi confirmada por
  `git worktree prune --dry-run --verbose --expire now` e então podada;
- a branch `local/av-s03-execucao` permaneceu preservada em
  `7f18ec30a4ee486af0d99b131728a32bc362941d`.

O registro original não foi reescrito retroativamente. O estado final e as
provas de recuperação estão em
`docs/governance/evidence/ORGANIZACAO-LOCAL/registro_organizacao_local_2026-09-30.md`.
