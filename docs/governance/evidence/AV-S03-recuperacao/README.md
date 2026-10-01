# Reconciliação histórica — AV-S03-recuperação

Regularização documental: 2026-09-30. Inventário de origem: 2026-09-28.

> **ARQUIVO HISTÓRICO — NÃO É EVIDÊNCIA DO CÓDIGO ATUAL.** Os registros de 2026-09-24
> descrevem uma implementação cujo worktree e diff foram perdidos. Os artefatos sob
> `AV-S03-recuperacao/` abaixo pertencem a uma reconstrução independente realizada em
> 2026-09-28, baseada em `66c95201daf893fa7b2852e0d94b20314f8d8f34`. Evidência de uma
> geração não deve ser transferida para outra sem comparação de conteúdo e nova execução.

> **Fronteira obrigatória de interpretação.** A implementação original executada em
> 2026-09-24 no worktree `/tmp/av-s03-work` foi perdida antes de ser preservada como
> código revisável. Relatos daquela execução são registros históricos e **não validam**
> o código reconstruído. Os dois artefatos textuais publicados abaixo como evidência
> técnica pertencem exclusivamente à reconstrução realizada em 2026-09-28 no worktree
> `avalia-plataform-worktrees/av-s03-work`, posteriormente consolidada no PR #3.

## Resultado da revisão

A solicitação mencionava 40 arquivos; a recontagem real encontrou **39 arquivos**.
Todos foram lidos/inventariados por duas revisões independentes (ver §5). A seleção
aprovada por Rafael em 2026-09-30 publica **4 artefatos textuais**:

1. `BL-AV-2-03-pacote/checksums_FINAL_20260928_162232.sha256` — manifesto final que
   identifica por hash o pacote homologado; âncora de integridade citada por
   `DEC-AV-026` e pelo snapshot EXEC-2026-09-28-05.
2. `BL-AV-2-03-pacote/parecer_antigravity_rodada1_20260928_161715.txt` — primeira
   rodada de revisão independente da reconstrução, com achados bloqueantes reais.
3. `BL-AV-2-03-pacote/parecer_antigravity_rodada2_20260928_161715.txt` — segunda
   rodada, confirma correções e registra novos ajustes necessários.
4. `BL-AV-2-03-pacote/parecer_antigravity_rodada3_FINAL_20260928_161715.txt` —
   parecer final que fecha a sequência achado → correção → aprovação.

Mais os dois arquivos de índice deste diretório: este `README.md` e
`INVENTARIO_PUBLICADO_SHA256.txt` (hashes dos 6 arquivos efetivamente publicados).

## Publicados (6 arquivos neste diretório, rastreados no Git)

| Caminho | Escopo coberto |
|---|---|
| `README.md` | este índice |
| `INVENTARIO_PUBLICADO_SHA256.txt` | hashes dos 5 arquivos abaixo |
| `BL-AV-2-03-pacote/checksums_FINAL_20260928_162232.sha256` | manifesto de 10 itens do pacote homologado de `BL-AV-2-03` (2026-09-28 16:22) |
| `BL-AV-2-03-pacote/parecer_antigravity_rodada1_20260928_161715.txt` | parecer independente, rodada 1 |
| `BL-AV-2-03-pacote/parecer_antigravity_rodada2_20260928_161715.txt` | parecer independente, rodada 2 |
| `BL-AV-2-03-pacote/parecer_antigravity_rodada3_FINAL_20260928_161715.txt` | parecer independente, rodada 3 (final) |

O manifesto `checksums_FINAL_20260928_162232.sha256` identifica por hash os 10 itens do
pacote final de `BL-AV-2-03` tal como homologado em 2026-09-28; os tarballs e arquivos
binários por ele descritos **não são republicados aqui** — permanecem apenas no pacote
externo (ver §3).

## Preservados somente no pacote recuperável externo (não publicados no Git)

Os demais **33 dos 39 arquivos** originais — incluindo os três tarballs, os pacotes
intermediários/superados, os diffs/código recuperado do worktree perdido e as **18
capturas visuais pré-correção** de `BL-AV-2-04-visual/` — permanecem exclusivamente em:

`/Users/rafaeloliveira/Projeto Estágio/RECUPERACAO-LOCAL-20260930_221041`

com inventário, checksums SHA-256 e teste real de restauração em diretório isolado
(`recovery_test=PASS`). As 18 imagens não são publicadas porque documentam o estado
da interface **antes** de duas rodadas de correção (revisão de UI e ajustes
posteriores) e poderiam ser lidas, fora de contexto, como validação do código final —
o que elas não são. A evidência funcional atual da `AV-S03` está em
`docs/governance/evidence/AV-S03/pacote-revisao-20260928/`.

Não são publicados novamente tarballs, cópias de código, dashboards antigos, estados
Git intermediários ou pareceres superados. O pacote versionado canônico da
reconstrução permanece em `docs/governance/evidence/AV-S03/pacote-revisao-20260928/`.

## Colisão de identificador — `EXEC-2026-09-28-01`

Existem dois arquivos distintos com o mesmo `id: "EXEC-2026-09-28-01"` no front-matter:

- `docs/governance/snapshots/snapshot_EXEC-2026-09-28-01_BL-AV-2-03-testes.md` — já
  rastreado em `main`, registra os testes automatizados de `BL-AV-2-03`.
- `docs/governance/snapshots/snapshot_EXEC-2026-09-28-01_pacote_revisao_av-s03.md` —
  histórico, incorporado nesta regularização (2026-09-30), registra a perda do código
  original e a preparação do pacote de revisão.

Não foi renumerado nem reescrito nenhum dos dois originais. Qualquer referência deve
usar o **nome completo do arquivo** como identificador inequívoco — nunca apenas
`EXEC-2026-09-28-01`.

## Rotulagem histórica dos quatro documentos incorporados

Os quatro documentos abaixo foram restaurados ao conteúdo original comprovado por
hash (ver §6) e permanecem em seus caminhos canônicos, fora deste diretório:

| Documento | Rótulo |
|---|---|
| `docs/governance/backlog/levantamento_ocr_visao_local.md` | registro histórico documental (2026-09-24); não valida código; não autoriza benchmark |
| `docs/governance/snapshots/snapshot_EXEC-2026-09-24-09_ajustes-planos-revisao-codex.md` | registro histórico documental; não valida código |
| `docs/governance/snapshots/snapshot_EXEC-2026-09-24-10_execucao-local-av-s03-saneamento-ocr.md` | relato histórico de execução cujo código-fonte/diff foi perdido |
| `docs/governance/snapshots/snapshot_EXEC-2026-09-28-01_pacote_revisao_av-s03.md` | inspeção forense da perda; não é validação funcional |

Nenhum desses quatro arquivos foi editado para parecer atual. O conteúdo é idêntico,
byte a byte, ao recuperado em 2026-09-28/29; a cópia intermediária com banners de
regularização que havia sido escrita antes desta rodada foi preservada, não
descartada, em `RECUPERACAO-LOCAL-20260930_221041/PRE_RESTAURACAO_20260930/`.

## Referências vigentes

- código/diff reconstruído e evidência funcional atual: `docs/governance/evidence/AV-S03/pacote-revisao-20260928/`;
- parecer final homologado: `BL-AV-2-03-pacote/parecer_antigravity_rodada3_FINAL_20260928_161715.txt`;
- manifesto final histórico: `BL-AV-2-03-pacote/checksums_FINAL_20260928_162232.sha256`;
- perda do código original: `docs/governance/snapshots/snapshot_EXEC-2026-09-28-01_pacote_revisao_av-s03.md` §3;
- evidência visual pré-correção (não publicada): pacote externo, `av_s03_01..18_*.png`.

Nenhum desses registros autoriza alteração em `avalia_dev`, saneamento operacional,
deploy, promoção de baseline ou implementação da AV-S04.

## Revisão e verificação (§5/§6)

Duas revisões independentes somente leitura avaliaram esta seleção em 2026-09-30:

- revisão de conteúdo dos 39 arquivos (classificação completa, achados de segredo:
  nenhum confirmado);
- revisão de referências históricas e verificação de hash dos quatro documentos
  restaurados (hashes idênticos aos listados abaixo).

Hashes dos quatro documentos históricos restaurados (idênticos ao conteúdo original
de 2026-09-28/29, conforme ambas as revisões independentes confirmaram):

```text
99de191600997392e157f93eed35e65267c8b3c9d29eaebc95af4fc9a339bc43  levantamento_ocr_visao_local.md
7cabe55917019aa65e9d7fc1b7cf0987e3935af6e8791440a52136b1904784b0  snapshot_EXEC-2026-09-24-09_ajustes-planos-revisao-codex.md
5e8cf6465a5c0fbc9a453f5a849c36e6ff8008a24cb1dcc8bc60037d6a92040e  snapshot_EXEC-2026-09-24-10_execucao-local-av-s03-saneamento-ocr.md
c7eb819d742ed60bf5a69ae870b8297f960bc450d2369abd933c7f0a6f926bfa  snapshot_EXEC-2026-09-28-01_pacote_revisao_av-s03.md
```
