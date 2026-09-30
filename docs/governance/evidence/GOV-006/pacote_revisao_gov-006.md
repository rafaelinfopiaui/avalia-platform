# Pacote de revisão e publicação GOV-006

## Situação

Rafael aceitou em 2026-09-30 a reconciliação GOV-006, o numerador nominal
`14/70` e a apresentação separada de itens parciais. Também autorizou a
publicação dos pacotes A e B por branches dedicadas e PRs em rascunho, sem
merge.

Este documento registra a composição real da pilha. Os pacotes não são
independentes em Git: o Pacote A consolida arquivos canônicos compartilhados
depois que o Pacote B introduz a investigação OCR.

## Base e dependência real

### Pacote B — investigação OCR

- branch: `docs/av-s05b-investigacao`;
- base: `main@a5974b1ffecc18f59ed2df39bdf5ce4a210bf0e8`;
- HEAD publicado: `44a09b0dc602a1e7a7e0626fb9ee703891bb444d`;
- PR em rascunho: `https://github.com/rafaelinfopiaui/avalia-platform/pull/5`;
- arquivos canônicos compartilhados deliberadamente não alterados nessa branch:
  `backlog_tecnico_avalia.md`, `executive_technical_dashboard.md` e
  `latest_execution.md`.

### Pacote A — governança

- branch: `docs/gov-006-reconciliacao`;
- base: HEAD publicado do Pacote B (`44a09b0`);
- PR deve ter como base `docs/av-s05b-investigacao`, não `main`;
- consequência: revisão/merge de A depende de B. Sem merge autorizado. Se B for
  eventualmente integrado, A deverá ser retargetado para `main` e seu diff
  revalidado antes de qualquer decisão de merge.

Essa pilha impede duas versões concorrentes dos arquivos compartilhados. O
Pacote A é o único que atualiza `backlog`, `dashboard` e `latest_execution`.
`decisions.md` pertence ao Pacote B e não é reeditado por A.

## Pacote A — conteúdo

- `docs/governance/sprints/sprint_GOV-006_auditoria_governanca.md`;
- `docs/governance/snapshots/snapshot_EXEC-2026-09-30-01_gov-006-auditoria.md`;
- `docs/governance/snapshots/snapshot_EXEC-2026-09-30-02_gov-006-reconciliacao.md`;
- `docs/governance/executive_technical_dashboard.md`;
- `docs/governance/backlog/backlog_tecnico_avalia.md`;
- `docs/governance/sprints/sprint_AV-S03_estrutura_academica.md`;
- `docs/governance/snapshots/latest_execution.md`;
- `docs/governance/evidence/GOV-006/`.

Inclui a lista nominal dos 14 itens, suas decisões de homologação e os critérios
de conclusão comprovados. `BL-AV-1-10` permanece fora do numerador por
`DEBT-AV-011`; itens parciais não recebem percentual ponderado.

## Pacote B — conteúdo já publicado na branch

- `docs/adr/ADR-009-ocr-visao-local-rascunho.md`;
- `docs/governance/sprints/sprint_AV-S05B_investigacao_ocr.md`;
- `docs/governance/snapshots/snapshot_EXEC-2026-09-29-04_av-s05b-benchmark-ocr.md`;
- `docs/governance/registers/decisions.md` (`DEC-AV-017`);
- `docs/governance/evidence/AV-S05B/`.

A investigação permanece parcial; manuscrito e revisão humana permanecem
pendentes; nenhuma solução OCR está homologada para o produto.

## Proposta local de saneamento (676 linhas)

A cópia local longa foi preservada no checkout principal e não foi publicada
como plano aprovado nem usada para substituir a versão integrada. Este pacote
publica somente:

- `comparacao_proposta_saneamento_676.md`: síntese das diferenças que exigem
  revisão;
- `diff_proposta_saneamento_676_vs_integrada.txt`: delta integral e reversível
  entre a versão integrada de 359 linhas e a cópia local de 676 linhas.

Permanecem pendentes revisão SQL independente, validação em banco restaurado
isolado, confirmação das evidências operacionais, decisão sobre retenção e
janela de manutenção. Nenhuma ação em `avalia_dev` foi executada ou autorizada.

## Rito contra recorrência

Antes de cada execução, o registro correspondente deve conter, conforme
`execution_policy.md` §3:

1. checkout e raiz Git reais;
2. branch e commit/base upstream;
3. working tree e alterações locais relevantes ainda não incorporadas;
4. dependências entre branches/PRs e arquivos compartilhados;
5. escopo autorizado, fora de escopo e validações previstas.

No encerramento, registrar onde estão código, documentos e evidências, quais
foram publicados e quais continuam somente locais. Publicação não é exigida
para toda atividade; contudo, pendências locais conhecidas devem aparecer no
registro de abertura da execução seguinte para que não sejam ignoradas.

## Limites

Não autorizados nem executados nesta publicação: merge, exclusão de branch ou
worktree, alteração em `avalia_dev`, saneamento operacional, deploy ou promoção
de baseline.
