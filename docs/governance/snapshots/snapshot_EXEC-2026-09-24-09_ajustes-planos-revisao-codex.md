---
id: "EXEC-2026-09-24-09"
data: "2026-09-24"
fuso: "UTC-03:00"
tipo: "execucao_documental"
escopo: "ajustes dos planos de saneamento e AV-S03, revisão independente e reconciliação canônica"
status: "concluida_documental_aguardando_decisoes_de_Rafael"
executor: "Hermes"
revisor_independente: "Codex"
branch: "docs/av-s02-encerramento-planos-operacionais"
commit_referencia: "7f18ec30a4ee486af0d99b131728a32bc362941d"
baseline_promovido: false
---

# EXEC-2026-09-24-09 — ajustes dos planos e revisão independente

## 1. Objetivo e autoridade

Concluir a rodada documental autorizada por Rafael sobre:

- preservar e fortalecer o plano local de saneamento de `human_reviews` duplicadas;
- incorporar ao plano `AV-S03` os seis ajustes de domínio solicitados;
- apresentar alternativas e recomendações sem decidir por Rafael;
- obter revisão independente do Codex ancorada em diff exato;
- reconciliar dashboard e ponteiro de última execução sem reescrever o snapshot histórico anterior.

Esta execução **não autorizou** stage, commit, push, merge, criação ou execução do script de
saneamento, migração operacional, implementação da `AV-S03`, deploy, tag ou promoção de baseline.

## 2. Estado Git e remoto verificado

Verificação em `2026-09-24T17:01:36-03:00`:

- raiz Git: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform`;
- branch: `docs/av-s02-encerramento-planos-operacionais`;
- HEAD e upstream: `7f18ec30a4ee486af0d99b131728a32bc362941d`;
- divergência com upstream: `0` atrás / `0` à frente;
- mudança preexistente preservada no início: `docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md` modificada;
- arquivo não rastreado e fora do escopo preservado: `docs/roteiro-apresentacao-supervisor.md`;
- índice Git: vazio; nenhum stage realizado.

Estado remoto verificado por `gh pr view 2` nesta execução:

- PR [#2](https://github.com/rafaelinfopiaui/avalia-platform/pull/2): `OPEN`, rascunho, base `main`, `mergeStateStatus=CLEAN`;
- cabeça do PR: `7f18ec30a4ee486af0d99b131728a32bc362941d`;
- CI dessa cabeça: 3/3 checks concluídos com `SUCCESS` no run
  [36040963710](https://github.com/rafaelinfopiaui/avalia-platform/actions/runs/36040963710);
- as alterações locais desta execução são posteriores à cabeça do PR, não integram o PR e não são
  cobertas pela CI remota acima.

## 3. Entregas documentais

### 3.1 Plano de saneamento

O diff local preexistente foi preservado e complementado após os achados do Codex. A versão final
proposta documenta, sem executar:

- `INSERT` das duas revisões excedentes em `human_reviews_superseded`, comparação integral e
  `DELETE` na mesma transação;
- assertions executáveis com `RAISE EXCEPTION` e execução futura com `ON_ERROR_STOP=1`;
- duração real do lock até o `COMMIT` e proteção posterior dependente de writers parados;
- validação da tabela de arquivo preexistente quanto a colunas, tipos, nulabilidade,
  `NUMERIC(6,2)`, default, PK, índice `btree` válido/pronto e ausência de índice UNIQUE simples em
  `job_id`;
- rollback compensatório com contagens, comparação integral, quantidade removida e abort no
  primeiro desvio;
- proibição expressa de inferir autorização operacional deste plano.

Não foi criado `core/scripts/av_s02_saneamento_human_reviews.sql` e nenhuma consulta mutável foi
executada.

### 3.2 Plano AV-S03

Foram incorporados os seis pontos solicitados:

1. turma referencia a associação curricular curso–disciplina quando o domínio aprovado for N:N;
2. avaliações legadas sem turma preservam acesso do proprietário original e do admin;
3. propriedade da avaliação é distinta do vínculo à turma, sem edição implícita por colaborador;
4. vínculo inativo, futuro ou expirado não concede autorização derivada da turma;
5. `Student` global é separado de `Enrollment` e da gestão da matrícula;
6. downgrade com dados dependentes deve abortar antes de qualquer DDL destrutivo.

O plano atualiza escopo, modelo, matriz de autorização, DoR, mapa de impacto, backlog, critérios
`AC-01` a `AC-12`, validações, riscos, alternativas de domínio e closure gate. Todas as escolhas de
domínio continuam pendentes de decisão explícita de Rafael.

## 4. Revisão independente ancorada em diff exato

O Codex foi executado somente em modo read-only. Cada parecer foi ancorado em um arquivo de diff e
SHA-256; nenhum parecer anterior foi reutilizado como aprovação de versão posterior.

| Rodada | SHA-256 do diff integral | Parecer | Resultado e achados |
|---|---|---|---|
| v1 | `11cb3250d04f1bfdd924b26bd20a51141bed24b0dfa0494d41264c7427952b1e` | `AJUSTES_NECESSARIOS` | bloqueante no rollback compensatório; observações sobre validação de schema e terminologia transacional |
| v2 | `008b8cf45fd9b0c0a6ebb96410087a2bdbb434a5053dff9d5d4e7f357988046e` | `AJUSTES_NECESSARIOS` | rollback e terminologia corrigidos; validação de schema ainda incompleta |
| v3 | `fc1c2cbc9d9288a840e2d5429e4c5b0face09675a4c651db2723b62b1da295e0` | `AJUSTES_NECESSARIOS` | achado anterior corrigido; nova lacuna: índice esperado não exigia `btree`, `indisvalid` e `indisready` |
| v4 final | `fba6ec451aa7d0224fb603602ab8d7eb3ff72f1566257f09bf97a99aa7577789` | **`APROVADO`** | bloqueante v3 corrigido; achados anteriores permanecem corrigidos; nenhum bloqueante ou não bloqueante técnico restante; seis pontos da AV-S03 confirmados |

O delta final v3→v4 tem SHA-256
`9a36dbe3263c21c021e0435c43bcf1a2b0a4e6610962e25fb15cb04146cd6221`.

O parecer técnico aprova a coerência documental do hash v4; ele não homologa os planos, não decide
as alternativas de domínio e não autoriza execução operacional.

## 5. Agentes efetivamente utilizados

| Agente | Participação real nesta execução | Alterou arquivos? |
|---|---|---|
| Hermes | coordenação, edição documental, consolidação, verificações e registro canônico | sim |
| Codex CLI | revisão independente read-only dos dois planos, em quatro hashes sucessivos | não |
| Antigravity CLI | não acionado, porque o Codex não produziu alterações | não |
| Claude Code | não utilizado; nenhuma participação ou parecer atribuído | não |

## 6. Reconciliação entre histórico e estado atual

- `AV-S02` permanece homologada e integrada a `main`; PR #1 e CI remota verde são fatos históricos
  preservados.
- O snapshot `EXEC-2026-09-24-08` permanece histórico: registra a versão então existente e a revisão
  que a cobria; não foi reescrito.
- O PR #2 já existe em rascunho; a redação anterior “será aberto” ficou superada pelo estado remoto
  verificado nesta execução.
- A cabeça do PR #2 continua em `7f18ec3`; os planos locais revisados pelo Codex no hash v4 ainda não
  integram o PR.
- A aprovação Codex anterior cobre somente seu diff correspondente. A aprovação atual cobre apenas
  `fba6ec451aa7d0224fb603602ab8d7eb3ff72f1566257f09bf97a99aa7577789`.
- Nenhum baseline foi promovido.

## 7. Validações desta execução

Executadas após a criação do snapshot, atualização do dashboard e do ponteiro:

| Validação | Procedimento | Resultado real |
|---|---|---|
| links Markdown locais | script Python sobre os 5 documentos desta superfície | `45` links locais verificados; `0` ausentes |
| frontmatter | validação estrutural dos documentos alterados que possuem frontmatter | `2` arquivos; `0` erros |
| IDs de snapshots | inventário de `id` nos snapshots com frontmatter | `0` IDs duplicados |
| whitespace/diff | `git diff --check` | exit `0`, sem erro |
| hash dos dois planos | `git diff -- <plano_saneamento> <plano_AV-S03> | shasum -a 256` | `fba6ec451aa7d0224fb603602ab8d7eb3ff72f1566257f09bf97a99aa7577789`, igual ao hash aprovado pelo Codex |
| inventário | `git status --short --branch`, `git diff --name-status`, `git diff --cached --name-status`, `git ls-files --others --exclude-standard` | 4 arquivos tracked modificados, este snapshot novo e o arquivo preexistente fora do escopo; índice vazio |
| escopo funcional | classificação dos caminhos alterados | `0` alterações funcionais |
| estado remoto | `gh pr view 2 --json ...` | PR #2 aberto em rascunho, cabeça `7f18ec3`, `CLEAN`, 3/3 checks `SUCCESS`; mudanças locais posteriores fora do PR |

Testes de produto, migrações, banco, build, deploy e validação funcional não foram executados porque a
fatia é exclusivamente documental e essas ações não foram autorizadas.

## 8. Estado e decisões pendentes

Estado documental: concluído e revisado tecnicamente; aguardando decisões de Rafael. Não equivale a
homologação.

Dependem de Rafael:

- aprovar, ajustar ou rejeitar o plano de saneamento;
- decidir as alternativas de domínio listadas na seção 14 do plano `AV-S03`;
- aprovar, ajustar ou rejeitar o plano `AV-S03`;
- conceder separadamente qualquer futura autorização de stage/commit/push/merge;
- conceder separadamente qualquer futura autorização para criar/testar o script em ambiente
  isolado ou executar saneamento/migração em `avalia_dev`;
- decidir futuramente sobre promoção de baseline.

## 9. Working tree ao fechar a fatia

A fatia deve encerrar com mudanças somente documentais, não staged, incluindo os dois planos,
dashboard, ponteiro e este snapshot. O arquivo `docs/roteiro-apresentacao-supervisor.md` permanece
não rastreado e fora do escopo. Nenhum commit, push, merge ou ação operacional foi executado.
