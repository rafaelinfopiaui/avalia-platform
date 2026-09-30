---
id: GOV-006
tipo: auditoria-governanca
status: concluida_homologada_em_publicacao
abertura: "2026-09-30"
responsavel_consolidacao: Hermes
homologacao: aceita_por_Rafael_em_2026-09-30
depende_de: GOV-005
---

# GOV-006 — Auditoria de governança: reconstrução do estado real, matriz de rastreabilidade (AV-S03 a AV-S05B) e reconciliação do numerador

> Execução exclusivamente de inspeção e regularização documental local. Não
> inicia nenhuma sprint funcional, não altera código, não executa
> stage/commit/push/merge, não altera `avalia_dev`, não exclui branch/worktree,
> não promove baseline. Suspendeu, durante a execução, qualquer nova
> atividade funcional a pedido explícito de Rafael.

**Nota de versão:** este documento substitui a primeira rodada desta
auditoria (mesma sessão, 2026-09-30), que continha um erro aritmético no
numerador (15/70, correto é 14/70) e linguagem imprecisa sobre AV-S04/AV-S05
("nenhuma execução encontrada" em vez de "nenhuma evidência localizada nas
fontes inspecionadas") e sobre a coleta manuscrita de AV-S05B ("em
andamento" sem evidência de fotografia real). Corrigido nesta segunda
rodada, a pedido de Rafael, sem reabrir uma nova auditoria geral.

## 1. Motivação e gatilho

Rafael identificou que a última sprint documentada parecia ser `AV-S03`,
embora já houvesse referências a `AV-S04` e `AV-S05` no planejamento, e
solicitou uma auditoria completa antes de qualquer nova decisão — sem
presumir que `AV-S05` (CSV, Etapa 4, Fase 5) e `AV-S05B` (investigação de
OCR/visão local, Etapa 4B, Fase 2) fossem a mesma coisa.

## 2. Checkouts e bases usados nesta auditoria (explícito, para não gerar nova divergência)

Duas cópias de trabalho do mesmo repositório remoto
(`github.com/rafaelinfopiaui/avalia-platform`) foram inspecionadas:

| Checkout | Caminho | Branch | HEAD | Situação |
|---|---|---|---|---|
| Principal | `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform` | `docs/av-s02-encerramento-planos-operacionais` | `7f18ec3` (2026-09-24) | 13 commits atrás de `main`; contém alterações locais não commitadas desde 2026-09-24/28, nunca propagadas |
| Worktree de trabalho | `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform-worktrees/av-s03-work` | `main` | `a5974b1` (2026-09-29) | sincronizado com `origin/main`; usado nas últimas 3 rodadas de execução (AV-S05B, esta auditoria) |

**Todas as edições documentais desta auditoria (rodadas 1 e 2) foram
aplicadas exclusivamente no worktree de trabalho, base `main` HEAD
`a5974b1`.** O checkout principal não foi editado nesta auditoria — apenas
lido, para comparação de conteúdo. Isso é registrado aqui explicitamente
para que qualquer leitor futuro saiba qual cópia é a fonte das correções
abaixo, evitando que uma terceira pessoa edite o checkout principal
pensando que ele já reflete estas correções.

## 3. Escopo autorizado

- reconstruir o estado real do repositório principal e de todos os
  worktrees vinculados (branches, commits, PRs, arquivos não commitados);
- inspecionar documentos de sprint, backlog, decisões, snapshots e
  dashboard já existentes, **por conteúdo, não apenas por lista de paths**;
- montar matriz de rastreabilidade para `AV-S03`, `AV-S04`, `AV-S05` e
  `AV-S05B`, separando estados (planejado, autorizado, executado
  localmente, revisado, homologado, integrado) sem inferir uns dos outros;
- identificar desvios (execução sem registro, documento em checkout
  secundário, dashboard/backlog desatualizados, evidência de versão
  diferente do código atual, atividade fora de escopo, artefato só em
  diretório temporário) e sua **causa comprovada**, não apenas o sintoma;
- regularizar documentalmente apenas o que for comprovável por evidência já
  existente — sem retrodatar registros, inventar autorização, marcar
  critério sem evidência ou homologar retroativamente;
- registrar esta própria auditoria seguindo a convenção de numeração já
  vigente (`GOV-NNN`), sem inventar numeração conflitante.

## 4. Método

1. Inspeção Git em `avalia-plataform` (checkout principal) e nos worktrees
   ativos e prunáveis (`git worktree list`, `git branch -vv`, `git log
   --all`, `gh pr list --state all`, `gh pr checks`, `gh run list`).
2. Leitura de todos os documentos de governança existentes nos dois
   checkouts, com **comparação por conteúdo** (`diff` linha a linha, não
   apenas contagem de paths modificados) para `dashboard`, `backlog`,
   `decisions.md` e `proposta_saneamento_human_reviews_duplicadas.md`.
3. Busca textual por `AV-S04` e `AV-S05` (case-insensitive, com e sem `B`)
   em todo o histórico Git e em todos os documentos, para não presumir
   equivalência entre `AV-S05` e `AV-S05B`.
4. Inspeção de código real (`core/app/schemas.py`, `core/app/main.py`) para
   verificar suporte a múltiplas questões por avaliação e caminhos de
   importação CSV no Core/AI Engine/frontend.
5. Busca no filesystem por evidência física da coleta manuscrita de
   `AV-S05B` (arquivos `MAN-*`) antes de descrever seu estado.
6. Comparação de datas de modificação de arquivo, timestamps de commit e
   data corrente (`2026-09-30`) para reconstruir a ordem real dos eventos
   e a causa das divergências entre checkouts.

## 5. Resultado — matriz de rastreabilidade (resumo; detalhe apresentado a Rafael na resposta desta execução)

- **`AV-S03`**: homologada por Rafael (`DEC-AV-026` técnica de
  `BL-AV-2-03`; `DEC-AV-027` da entrega completa) e **integrada a `main`**
  via PR #3 (merge commit `c391865`) e PR #4 de encerramento documental
  (merge commit `a5974b1`), ambos com CI 3/3 verde. Trabalho realizado e
  registrado inteiramente no worktree de trabalho, não no checkout
  principal.
- **`AV-S04`** (múltiplas questões por avaliação, Etapa 3): **nenhuma
  evidência de execução localizada nas fontes inspecionadas** (nenhum
  branch, commit, worktree ou documento além da linha de backlog original,
  `BL-AV-3-01` a `04`, estado `proposto`). Confirmado por leitura de
  código: `AssessmentCreate.question` em `core/app/schemas.py` continua
  singular (`Optional[QuestionInput]`), sem suporte a lista de questões.
- **`AV-S05`** (contrato/prévia de importação CSV, Etapa 4): **nenhuma
  evidência de execução localizada nas fontes inspecionadas**; nenhum
  caminho de código relacionado a CSV em `core/`, `ai-engine/` ou
  `frontend/src/`. Backlog (`BL-AV-4-01`/`02`) permanece `proposto`,
  coerente com a ausência de evidência.
- **`AV-S05B`** (investigação de OCR/visão local, Etapa 4B — **distinta de
  `AV-S05`**, confirmado por leitura da trilha §11 e do backlog): entrega
  experimental e documental local, ainda não publicada no repositório
  **no instante desta inspeção** (sem stage/commit) — protocolo congelado, benchmark de texto impresso
  medido, revisão cruzada Codex+Antigravity, ADR em rascunho com revisão
  independente concluída. A publicação desses artefatos como parte do
  repositório é aplicável e ainda pendente, mesmo não havendo código de
  produção envolvido — trata-se de documentação/evidência versionável,
  então presente apenas no worktree local e no diretório experimental
  externo ao repositório. Adendo: em 2026-09-30, após homologação de GOV-006,
  Rafael autorizou e o Pacote B foi publicado no PR rascunho #5; continua
  parcial e não integrado a `main`.

## 6. Origem comprovada das divergências entre os dois checkouts

Ao comparar por conteúdo (não apenas por lista de paths modificados), a
mesma lista de arquivos alterados nos dois checkouts continha versões
**diferentes** em pontos relevantes. Reconstrução factual, por arquivo:

### 6.1 `executive_technical_dashboard.md` — numerador "7 → 9" no checkout principal

- O checkout principal tem, em seu banner de topo (linha 3, working tree
  não commitado), a frase: *"numerador de progresso corrigido de 7 para 9
  itens (achado de reconciliação, 2026-09-28)"*, e na seção de progresso
  funcional (linha 47), a tabela completa dessa correção: os 6 itens da
  `AV-S01` + `BL-AV-1-05` + `BL-AV-1-06` (achado: estavam homologados no
  backlog mas ausentes do numerador) + `BL-AV-1-09` = **9**, com
  `BL-AV-1-10` explicitamente excluído por seu débito `DEBT-AV-011` aberto.
- Essa correção está registrada em detalhe no arquivo
  `docs/governance/snapshots/snapshot_EXEC-2026-09-28-01_pacote_revisao_av-s03.md`
  (existe **apenas no checkout principal**, untracked, nunca commitado em
  nenhum branch — confirmado por `git log --all -- <path>` vazio).
- **Nenhuma dessas duas edições (dashboard "7→9" e o snapshot
  EXEC-2026-09-28-01) foi commitada em nenhum branch.** Elas existem
  exclusivamente como alterações não commitadas no working tree do
  checkout principal, datadas de 2026-09-28 13:43 (mtime do dashboard).
- O worktree de trabalho foi criado a partir de `main` HEAD `a5974b1` em
  2026-09-29, **depois** dessa correção de 2026-09-28 ter sido feita — mas
  como a correção nunca foi commitada nem mesclada a `main`, o worktree
  nasceu sem ela: herdou a versão committed mais antiga do dashboard, que
  ainda dizia "7 de 70" (confirmado: `git show main:.../dashboard.md`
  mostra "7 de 70", idêntico ao commit anterior `8e4b1fa` e ao merge de
  PR#3 `c391865` — a correção de 7→9 nunca chegou a nenhum commit real).
- **Causa comprovada:** a correção "7→9" foi feita e ficou presa como
  edição local não commitada no checkout principal (branch antiga,
  `docs/av-s02-encerramento-planos-operacionais`, HEAD `7f18ec3`). Quando
  o trabalho subsequente de homologação/integração da `AV-S03`
  (`DEC-AV-026`, `DEC-AV-027`, PR #3, PR #4) foi feito depois, em rodadas
  posteriores, ele foi feito **inteiramente no worktree de trabalho**
  (criado a partir de `main`), sem nunca reler ou incorporar a correção
  pendente do checkout principal — os dois fios de trabalho nunca se
  encontraram. Minha primeira rodada desta auditoria (2026-09-30) herdou
  apenas o dashboard do worktree (numerador committed "7 de 70", ainda sem
  a correção de 2026-09-28) e, ao recontar, incluí por engano `BL-AV-1-10`
  no lote-base de 10 itens de `AV-S01`/`AV-S02` (em vez dos 9 corretos,
  que excluem `BL-AV-1-10` por seu débito `DEBT-AV-011` aberto), chegando
  a 10 + 5 = 15 em vez do valor correto. O valor correto, partindo da base
  real (9, sem `BL-AV-1-10`) mais os 5 itens da `AV-S03`, é **14**.
- **Versão com os registros mais recentes:** nenhum dos dois checkouts,
  isoladamente, tinha o estado mais atual — o checkout principal tinha o
  numerador mais correto (9) mas desatualizado quanto à integração da
  `AV-S03` (ainda achava que o código "não está mais disponível"); o
  worktree tinha a `AV-S03` corretamente homologada/integrada mas herdou
  um numerador desatualizado (7, não 9). A versão correta é a combinação
  das duas: numerador base 9 (do checkout principal) + 5 itens da `AV-S03`
  (do worktree) = **14**.

### 6.2 `sprint_AV-S03_estrutura_academica.md`, `decisions.md`, `backlog_tecnico_avalia.md`

- Divergências menores de formatação/ordenação entre os dois checkouts
  (ex.: uma frase de desvio de processo em `DEC-AV-022` presente no
  checkout principal e ausente no worktree) foram inspecionadas e não
  alteram nenhum fato desta auditoria — são edições de commits diferentes
  no histórico linear de `main` (`DEC-AV-022` foi reescrita entre commits
  `9e4b1d0`/`7f18ec3` e o commit posterior `a5d0a2c`, que está em `main`
  mas não é ancestral de `7f18ec3`). Nenhuma delas foi apagada; ambas as
  formulações continuam recuperáveis via `git log --all` nos respectivos
  commits.

### 6.3 `proposta_saneamento_human_reviews_duplicadas.md` — conteúdo único preservado, não perdido

- O checkout principal tem uma versão **não commitada, de 676 linhas**
  deste documento; a versão committed em `main` (idêntica à do worktree)
  tem 359 linhas. A diferença não é uma seção inteira faltante — os
  mesmos títulos de seção existem nos dois — mas as seções 7.3 e 7.4 do
  checkout principal contêm texto mais detalhado (assertions executáveis
  explícitas dentro da transação) do que a versão condensada que acabou
  committed.
- **Este conteúdo mais detalhado nunca foi commitado e existe apenas no
  checkout principal.** Não foi apagado por esta auditoria — não editei
  este arquivo em nenhum dos dois checkouts. Fica registrado aqui como
  achado, para que Rafael decida se quer que a versão de 676 linhas
  substitua a de 359 linhas committed, ou se a condensação foi
  intencional.

### 6.4 Causa geral, documentada sem inventar certeza além do que os dados comprovam

Comprovado por Git/mtimes: o checkout principal acumulou edições locais
entre 2026-09-24 e 2026-09-28 que nunca foram commitadas nem mescladas a
`main`. Trabalho posterior (a reconstrução e homologação da `AV-S03`,
2026-09-28/29) foi conduzido em um worktree separado, criado a partir de
`main`, sem nunca reincorporar as edições pendentes do checkout principal.
Isso não é uma corrupção de dados nem uma cópia divergente por acidente de
sincronização — é o efeito direto de duas cópias de trabalho terem
recebido edições locais em momentos diferentes, sem processo de
sincronização entre elas (nenhum commit, nenhum `git pull`/`push` entre os
dois). **Não há incerteza residual sobre esta causa** — cada passo foi
confirmado por comando Git (`git log --all`, `git show`, `diff` de
conteúdo, `stat` de mtime).

## 7. Correções aplicadas nesta rodada (todas no worktree de trabalho, base `main` `a5974b1`)

1. **Numerador nominal corrigido de 15/70 para 14/70**, com lista nominal
   de cada um dos 14 IDs, sua homologação (decisão + data) e observação —
   ver `executive_technical_dashboard.md`, seção "Trilha proposta". `BL-AV-1-10`
   foi explicitamente excluído do numerador (código integrado, mas
   `DEBT-AV-011`/migração operacional em `avalia_dev` permanece aberta) e
   movido para um indicador separado de itens parciais, sem ponderação
   percentual, junto com `BL-AV-4B-01`/`BL-AV-4B-20`.
2. **Linguagem sobre AV-S04/AV-S05 corrigida** em todo o dashboard (banner
   de topo e seção de progresso) para "nenhuma evidência de execução
   localizada nas fontes inspecionadas", em vez de "nenhuma execução
   encontrada"/"não iniciado" — formulação mais precisa sobre os limites
   do que uma auditoria documental pode afirmar.
3. **Linguagem sobre AV-S05B corrigida**: descrita como "entrega
   experimental e documental local, ainda não publicada no repositório"
   (aplicável mesmo sem código de produção), e a coleta manuscrita como
   "autorizada e com protocolo pré-registrado, sem evidência de fotografia
   ou coleta iniciada localizada no filesystem nesta auditoria" — busca
   por arquivos `MAN-*` no filesystem não encontrou nenhum resultado;
   autorização e protocolo preparado não comprovam coleta iniciada.
4. **Causa da divergência entre checkouts documentada** (seção 6 acima),
   sem apagar nenhum registro único de nenhum dos dois checkouts — a
   versão de 676 linhas de `proposta_saneamento_human_reviews_duplicadas.md`
   no checkout principal permanece intacta, não sobrescrita.

## 8. Desvios documentais da primeira rodada, mantidos (ainda válidos)

1. Sprint AV-S03 §17/18 (worktree) diziam "não iniciado" apesar de
   homologada e integrada — corrigido (mantido da rodada 1).
2. Duas linhas internas do dashboard (tabela de componentes, linha
   BL-AV-2-03) diziam "local, não integrado" apesar do banner de topo já
   estar correto — corrigido (mantido da rodada 1).
3. Backlog: `BL-AV-2-01` a `05` permaneciam `proposto` apesar de
   homologados/integrados — corrigido (mantido da rodada 1).
4. Checkout principal permanece na branch antiga, 13 commits atrás de
   `main` — constatado, não alterado (decisão de Rafael).
5. Worktree do Codex em `/private/tmp/av-s03-work` prunable — constatado,
   não podado (decisão de Rafael).

## 9. Desvios verificados e NÃO regularizados (dependem de decisão de Rafael)

- Checkout principal: manter na branch antiga ou trocar para `main`? Não
  trocado nesta auditoria — não é pré-requisito para concluí-la.
- Worktree prunable do Codex: podar ou preservar o metadado? Não podado —
  não é pré-requisito para concluir a auditoria.
- Conteúdo mais detalhado (676 linhas) de `proposta_saneamento_human_reviews_duplicadas.md`
  no checkout principal: promover para substituir a versão condensada
  committed, ou manter a condensação como está? Não decidido nesta
  auditoria.
- Publicação dos artefatos de `AV-S05B`: não estava autorizada durante a
  auditoria e constava como pendência separada. Adendo de 2026-09-30: Rafael
  autorizou a publicação documental, realizada na branch
  `docs/av-s05b-investigacao`, PR rascunho #5, sem merge e sem homologação de
  solução OCR para o produto.

## 10. Retomada — coleta manuscrita removida como dependência geral

A coleta manuscrita de `AV-S05B` **não é dependência para avançar em
nenhuma outra frente do projeto**. Ela é relevante apenas para fechar
`AC-02`/`AC-05` da própria `AV-S05B`, que permanece classificada como
**parcial** independentemente de quando essa coleta ocorrer. Em
específico:

- `AV-S05B` permanece parcial — nem bloqueia nem é bloqueada por nenhuma
  outra sprint.
- `AV-S04` (múltiplas questões) pode ser **planejada separadamente** a
  partir de agora, já que esta reconciliação confirma que ela depende
  tecnicamente apenas da consolidação da Fase 1 (já homologada) e da
  estrutura acadêmica da `AV-S03` (já homologada e integrada) — não da
  coleta manuscrita de `AV-S05B`, que pertence a uma frente paralela
  (Fase 2, Etapa 4B) sem dependência técnica declarada sobre `AV-S04`
  (Etapa 3, Fase 3). Planejamento formal de `AV-S04` não foi iniciado
  nesta auditoria — fica como opção disponível para decisão de Rafael.

## 11. Backlog desta execução

| ID | Entrega | Estado |
|---|---|---|
| GOV-006-01 | Reconstrução do estado real (Git, worktrees, branches, PRs, CI) | implementado; validação documental concluída |
| GOV-006-02 | Matriz de rastreabilidade AV-S03/AV-S04/AV-S05/AV-S05B | implementado; apresentada na resposta desta execução |
| GOV-006-03 | Identificação de desvios documentais e sua causa comprovada | implementado; ver seções 6, 8 |
| GOV-006-04 | Regularização documental comprovável (sprint AV-S03 §17/18, dashboard, backlog, numerador nominal) | implementado; validação documental concluída |
| GOV-006-05 | Registro desta auditoria conforme convenção `GOV-NNN` vigente | implementado; este documento (2ª rodada) |
| GOV-006-06 | Pacote durável revisável com inventário, separando auditoria de investigação OCR | implementado; ver seção 12 |
| GOV-006-07 | Homologação desta auditoria | **homologado em 2026-09-30 por Rafael**: aceita a reconciliação, o numerador 14/70 e os itens parciais separados |

## 12. Pacote durável e proposta de publicação

Ver documento separado
`docs/governance/evidence/GOV-006/pacote_revisao_gov-006.md`, criado nesta
rodada, com:

- inventário SHA-256 dos documentos e evidências do Pacote A;
- delta integral da proposta local de saneamento de 676 linhas contra a
  versão integrada, sem publicá-la como plano aprovado;
- publicação em dois pacotes distintos, porém **empilhados por dependência
  real**: (a) Pacote B/AV-S05B sobre `main`; (b) Pacote A/GOV-006 sobre o
  HEAD de B, pois A consolida `dashboard`, `backlog` e `latest_execution`.
  `decisions.md` pertence a B. A separação de inventário não implica
  independência de integração.

## 13. Encerramento

**Estado da execução:** concluída documentalmente e homologada por Rafael em
2026-09-30; publicação autorizada por branches dedicadas e PRs em rascunho,
sem merge. Nenhuma nova sprint funcional foi iniciada; toda atividade
funcional permaneceu suspensa durante esta auditoria.

**Closure gate aplicado:**

- desvios identificados com evidência de antes/depois, incluindo causa
  comprovada por Git/mtime, não apenas sintoma: atendido;
- nenhuma correção retrodatada, nenhuma autorização inventada, nenhum
  critério marcado sem evidência, nenhuma homologação retroativa presumida
  pelo executor: atendido;
- histórico anterior preservado — nenhuma seção de sprint/dashboard/backlog
  apagada, apenas complementada com nota datada; conteúdo único do checkout
  principal (`proposta_saneamento`, 676 linhas) preservado sem sobrescrita:
  atendido;
- trabalhos existentes, arquivos locais, branches e worktrees preservados
  sem remoção: atendido — nenhum `git worktree prune`, nenhuma exclusão de
  branch, nenhum checkout alterado;
- checkout e base usados em cada alteração documentados explicitamente
  (seção 2): atendido;
- mudanças limitadas a Markdown de sprint/backlog/dashboard, todas no
  worktree de trabalho: atendido por inspeção de paths;
- código, dependências, banco, infraestrutura e serviços: sem alteração;
- na execução original da auditoria, stage, commit, push, merge, deploy e
  alteração remota não foram realizados; a publicação posterior recebeu
  autorização específica e é registrada em
  `evidence/GOV-006/registro_publicacao_pacote_a_2026-09-30.md`;
- homologação por Rafael: **recebida em 2026-09-30** para a reconciliação e
  numerador 14/70; não promove baseline nem autoriza merge.

## 14. Próxima ação autorizável

Publicar os pacotes autorizados em PRs rascunho, acompanhar os checks dos
respectivos HEADs e preservar a pilha B→A sem merge. Depois, preparar o
planejamento da `AV-S04`, sem iniciar implementação e sem vinculá-la à coleta
manuscrita. A proposta de saneamento de 676 linhas permanece local, não
aprovada e sujeita às revisões listadas em
`evidence/GOV-006/comparacao_proposta_saneamento_676.md`.
