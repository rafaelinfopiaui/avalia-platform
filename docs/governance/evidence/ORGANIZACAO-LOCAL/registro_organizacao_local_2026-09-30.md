# Registro da organização local — 2026-09-30

## Escopo

Este registro documenta a consolidação do checkout principal, a regularização de referências históricas, a preservação verificável de conteúdos locais e a retirada autorizada de worktrees.

Não houve merge, implementação de AV-S04, alteração em `avalia_dev`, saneamento operacional, deploy, promoção de baseline, reinstalação de dependências ou reexecução do benchmark OCR.

## Checkout principal

- caminho: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform`;
- branch documental: `docs/organizacao-local-20260930`;
- base da branch antes do commit documental: `ba6f4074f49f87461c515081964a2aff6202e6cb`;
- base equivalente à `main` integrada observada no início da regularização;
- nenhum novo worktree foi criado para esta tarefa.

## Mapa origem → destino

| Origem anterior | Destino atual | Classificação |
|---|---|---|
| `/Users/rafaeloliveira/Projeto Estágio/av-s05b-benchmark-experimento/` | `experiments/av-s05b/` | ambiente local ignorado; evidência canônica permanece em `docs/governance/evidence/AV-S05B/` |
| `docs/apresentacao-preceptor/` | `local-nao-versionado/materiais-apresentacao/apresentacao-preceptor/` | material local preservado, não publicável |
| `docs/roteiro-apresentacao-supervisor.md` | `local-nao-versionado/materiais-apresentacao/roteiro-apresentacao-supervisor.md` | material local preservado, não publicável |
| proposta de saneamento com 676 linhas | `local-nao-versionado/propostas-pendentes/proposta_saneamento_human_reviews_duplicadas.md` | não homologada e não executada |
| `/Users/rafaeloliveira/Projeto Estágio/revisao-diffs/` | `local-nao-versionado/revisao-diffs/` | material local preservado, não publicável |
| artefatos históricos AV-S03 recuperados | seleção mínima em `docs/governance/evidence/AV-S03-recuperacao/` | 6 de 39 artefatos originais publicados (4 textos probatórios + README + inventário); os 33 restantes, incluindo as 18 capturas pré-correção, preservados somente no pacote externo |

`experiments/` e `local-nao-versionado/` estão ancorados na raiz do `.gitignore`. Nenhum conteúdo dessas áreas é publicado por este branch.

## Regularização documental

Foram incorporados:

- `docs/governance/backlog/levantamento_ocr_visao_local.md`;
- `snapshot_EXEC-2026-09-24-09_ajustes-planos-revisao-codex.md`;
- `snapshot_EXEC-2026-09-24-10_execucao-local-av-s03-saneamento-ocr.md`;
- `snapshot_EXEC-2026-09-28-01_pacote_revisao_av-s03.md`.

As datas originais foram preservadas. Os arquivos receberam metadados/notas de regularização que os identificam como históricos. Em especial, a evidência de código perdido em 2026-09-24 não valida o código reconstruído em 2026-09-28 nem o código atualmente integrado.

Dos 39 arquivos encontrados em `AV-S03-recuperacao` — e não 40 como indicava o inventário anterior — a seleção final, aprovada por Rafael em 2026-09-30 após duas rodadas de revisão independente, publica somente **4 artefatos textuais**:

- `BL-AV-2-03-pacote/checksums_FINAL_20260928_162232.sha256` — manifesto final;
- `BL-AV-2-03-pacote/parecer_antigravity_rodada1_20260928_161715.txt`;
- `BL-AV-2-03-pacote/parecer_antigravity_rodada2_20260928_161715.txt`;
- `BL-AV-2-03-pacote/parecer_antigravity_rodada3_FINAL_20260928_161715.txt` — parecer final.

Mais `README.md` e `INVENTARIO_PUBLICADO_SHA256.txt` deste diretório.

**As 18 capturas visuais pré-correção (`BL-AV-2-04-visual/`) foram excluídas da seleção final** por decisão de Rafael: documentam o estado da interface antes de duas rodadas de correção de UI e poderiam ser lidas, fora de contexto, como validação do código final. Permanecem preservadas no pacote externo; a pasta correspondente no checkout principal **ainda existe no filesystem** (não removida por este processo — remoção manual ficou a cargo de Rafael) mas está deliberadamente fora de qualquer stage/commit.

Tarballs, cópias de código, dashboards antigos, estados intermediários e artefatos duplicados foram omitidos do Git. O conjunto integral permanece no pacote externo preservado. A seleção e os hashes individuais constam em `docs/governance/evidence/AV-S03-recuperacao/README.md`.

## Fronteira probatória AV-S03

- documentos de 2026-09-24 registram o estado histórico do código perdido;
- documentos e capturas de 2026-09-28 registram a reconstrução;
- nenhuma evidência do primeiro conjunto é usada como validação do segundo;
- a evidência canônica versionada da reconstrução está em `docs/governance/evidence/AV-S03/pacote-revisao-20260928/`;
- o PR #3 e seus checks verificam a integração histórica da reconstrução, não o estado operacional presente.
- `README.md` deste diretório também registra a colisão do identificador `EXEC-2026-09-28-01` entre dois arquivos distintos (um já rastreado, um histórico incorporado nesta regularização) e orienta o uso do nome completo do arquivo como identificador inequívoco.

## Correções aplicadas após revisão independente

Duas rodadas de revisão independente somente leitura (ver §Revisão abaixo) identificaram e motivaram as seguintes correções, todas aplicadas antes do stage:

- `docs/governance/registers/decisions.md` (`DEC-AV-026`): a redação original misturava o estado de 2026-09-28 (código local, não integrado; sprint aberta) com o presente. Foi adicionada qualificação explícita de que essas afirmações descrevem o estado **na data da decisão**, superado pela integração registrada em `DEC-AV-027`; o texto original da homologação técnica não foi reescrito, apenas anotado;
- `docs/governance/sprints/sprint_AV-S05B_investigacao_ocr.md`: três referências ativas (AC-05, AC-06, AC-08) apontavam para caminhos relativos inexistentes (`saida/...`, `proposta_coleta_manuscrito...`); corrigidas para os caminhos canônicos completos em `docs/governance/evidence/AV-S05B/`;
- `docs/adr/ADR-009-ocr-visao-local-rascunho.md`: duas referências (`saida/medicao_memoria_coexistencia.md`, `PREPARACAO_DOWNLOADS.md`) corrigidas para os caminhos canônicos completos;
- `docs/governance/sprints/sprint_AV-S02_ci_visual_isolamento_testes.md:49`: link quebrado para `docs/roteiro-apresentacao-supervisor.md` (removido da raiz nesta mesma organização) substituído por referência textual ao material local preservado em `local-nao-versionado/materiais-apresentacao/`, sem criar um link que parecesse apontar para um arquivo disponível no repositório remoto.

## Revisão independente

Duas rodadas de revisão independente somente leitura foram executadas via `delegate_task` antes do stage, cada uma em contexto isolado sem acesso ao histórico desta sessão:

1. Primeira rodada (2 subagentes em paralelo): revisão de conteúdo dos 39 arquivos de `AV-S03-recuperacao` (classificação completa, achados de segredo) e revisão das referências históricas/links quebrados. Resultado: recomendação de restringir a publicação a 4 textos e excluir as 18 imagens; identificação da colisão de ID e do link quebrado do roteiro.
2. Segunda rodada (1 subagente): revisão do diff/untracked já com a seleção de 4 textos aplicada. Veredito inicial **REPROVADO** por três achados (DEC-AV-026 incoerente com o presente; referências ativas quebradas na sprint AV-S05B e no ADR-009). Todos os três corrigidos nesta mesma rodada de trabalho, conforme listado acima.

Os subagentes foram executados pelo mesmo backend de modelo desta sessão (delegação interna via `delegate_task`, não um CLI externo como Antigravity/Codex); nenhuma chamada a Antigravity CLI, Codex CLI ou outro agente externo foi feita nesta etapa de revisão. Os pareceres "Antigravity" citados no conteúdo histórico publicado (rodadas 1–3 de `BL-AV-2-03-pacote/`) são evidência de 2026-09-28, pré-existente, não produzida por esta revisão.

## Recuperação verificável

Pacote preservado:

`/Users/rafaeloliveira/Projeto Estágio/RECUPERACAO-LOCAL-20260930_221041`

Estado final do inventário:

- 38 entradas;
- SHA-256 do arquivo `INVENTARIO_CHECKSUMS.sha256`: `979acb3032dcb42ea285f86a6ee96134565ce6cc26cc556f7cb57030452370e2`;
- verificação integral: `PASS`.

Stashes registrados por índice transitório e hash imutável:

- `stash@{0}` → `aa8031a374e2ae6f4ecf749a3f4a55c85dcdfaee`;
- `stash@{1}` → `d8907484674d6f82cbeceb1673c88c67e9765854`.

Refs independentes preservadas:

- `refs/recovery/stash-checkout-principal` → `aa8031a374e2ae6f4ecf749a3f4a55c85dcdfaee`;
- `refs/recovery/stash-av-s03-work` → `d8907484674d6f82cbeceb1673c88c67e9765854`.

O pacote contém `.git`, metadados dos worktrees capturados, bundle de todas as refs e bundle/cópia rastreada independente do planejamento AV-S04 no HEAD `35e7040e7222e583e29645d07238002f0ef24e6e`.

O teste em diretório isolado comprovou:

- extração do checkout e `git fsck`;
- leitura dos metadados de cinco worktrees históricos;
- importação e leitura dos dois stashes pelos hashes;
- recuperação de `decisions.md`, da proposta de 676 linhas, dos materiais de apresentação e do levantamento OCR;
- restauração do planejamento AV-S04 no SHA exato;
- extração do experimento sem venv/modelos;
- ausência de valores reais nos três `.env` sanitizados.

Resultado registrado em `TESTE_RECUPERACAO_ISOLADA_20260930.txt`: `recovery_test=PASS`.

## Worktrees retirados

Após status limpo e zero handles ativos, foram removidos por `git worktree remove`, sem `--force`:

| Worktree | Branch preservada | SHA preservado |
|---|---|---|
| `av-s03-work` | `local/av-s03-work-frozen-20260930` | `a5974b1ffecc18f59ed2df39bdf5ce4a210bf0e8` |
| `av-s05b-publish` | `docs/av-s05b-investigacao` | `44a09b0dc602a1e7a7e0626fb9ee703891bb444d` |
| `gov-006-publish` | `docs/gov-006-reconciliacao` | `1066e00fb7f5f4c521d9c1327d0382ac3718b193` |
| `av-s04-planning` | `docs/av-s04-planejamento` | `35e7040e7222e583e29645d07238002f0ef24e6e` |

O dry-run de `git worktree prune` listou somente a entrada órfã do caminho já ausente `/private/tmp/av-s03-work`. Essa única entrada foi podada; a branch `local/av-s03-execucao` permaneceu em `7f18ec30a4ee486af0d99b131728a32bc362941d`.

O diretório pai `avalia-plataform-worktrees` foi removido por `rmdir` somente após a listagem de seu conteúdo retornar `[]`.

## Experimento AV-S05B

Nenhum script contém o caminho antigo absoluto. Referências ativas no ADR e no sprint foram apontadas para a evidência canônica e para `experiments/av-s05b/`. Logs, pareceres e snapshots datados mantêm os caminhos históricos, acompanhados por nota de localização quando cabível.

Não houve reinstalação de dependências nem repetição do benchmark.

## Itens deliberadamente preservados fora da publicação

- proposta de saneamento de 676 linhas: não homologada e não executada;
- materiais de apresentação;
- árvore `local-nao-versionado/`;
- ambiente `experiments/av-s05b/`, incluindo dependências locais reconstruíveis;
- backup integral externo;
- branches, stashes e refs de recuperação.

`avalia-github-lab` permaneceu separado e intocado.

## AV-S04 e PR #7

O planejamento não foi recriado nem modificado. A branch `docs/av-s04-planejamento` permaneceu no HEAD `35e7040e7222e583e29645d07238002f0ef24e6e`. O PR #7 deve permanecer aberto, em rascunho e sem merge. A cópia local recuperável foi adicionada ao pacote antes da retirada do worktree.

## Nota de preservação dos originais restaurados

Os quatro documentos históricos (`levantamento_ocr_visao_local.md` e os três snapshots de 2026-09-24/28) foram restaurados ao **conteúdo original comprovado por hash**, idêntico ao extraído do pacote externo. A versão intermediária com banners de regularização escrita antes desta correção foi preservada, não descartada, em `RECUPERACAO-LOCAL-20260930_221041/PRE_RESTAURACAO_20260930/`.
