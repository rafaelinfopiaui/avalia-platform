---
id: "EXEC-2026-09-29-01"
tipo: execucao
sprint: "AV-S03"
gerado_em: "2026-09-29T02:15:00-03:00"
executor: "Hermes (consolidação), Codex (revisões independentes), Antigravity (correções delegadas)"
status: parcial
commit_referencia: "a5d0a2c6512d60837cb8ca7acab3555d2259bd80"
---

# Snapshot EXEC-2026-09-29-01 — validação de AC-10, pacote de revisão, publicação e CI remota da AV-S03

> Registro histórico. Não promover automaticamente a baseline.

## 1. Abertura

- objetivo: (1) executar validação real de AC-10 com o denominador reconfirmado por Rafael
  (`DEC-AV-007`, 2026-09-28); (2) submeter o ajuste do default de `isAcademicModuleEnabled()` à
  revisão independente do Codex; (3) montar pacote de revisão completo (diff, inventário,
  checksums); (4) prosseguir com stage, commits, push e PR em rascunho, sob a autorização já
  concedida por Rafael; (5) acompanhar CI remota do HEAD publicado;
- escopo autorizado: exatamente os 4 itens acima, explicitamente definidos por Rafael nesta rodada;
- fora de escopo, mantido: merge, alteração de `avalia_dev`, saneamento operacional, deploy,
  promoção de baseline, nova sprint;
- branch/commit inicial: `local/av-s03-recuperacao` @ `66c95201daf893fa7b2852e0d94b20314f8d8f34`
  (== `origin/main`, 0 divergência);
- branch/commit final: `feat/av-s03-estrutura-academica` @ `a5d0a2c6512d60837cb8ca7acab3555d2259bd80`,
  publicada em `origin`, PR #3 aberto em rascunho.

## 2. AC-10 — validação real do denominador

Denominador reconfirmado por Rafael em 2026-09-28 (`DEC-AV-007`, restrito à validação funcional da
AV-S03): 1 organização, 1 curso, 2 disciplinas, 2 turmas, 2 professores, 10 alunos matriculados por
turma, 2 avaliações por turma — incluindo explicitamente aluno em múltiplas turmas e professores
com permissões distintas. O texto vigente da sprint (§4.2) também exige disciplina em mais de um
curso e vínculo expirado; ambos mantidos como cenários obrigatórios por não terem sido removidos
explicitamente.

Executado em PostgreSQL 16 isolado dedicado (fora de `avalia_dev`, removido ao final), via FastAPI
`TestClient` sobre o app real com login JWT real e endpoints HTTP reais. **16/16 cenários PASS**,
incluindo o achado de transparência registrado: a primeira execução do cenário de leitura por
colaborador revelou que a expectativa inicial do script (200) estava desalinhada com o comportamento
homologado (403, ownership estrito) — corrigido no script, não no código de produção, pois o
comportamento observado já era o correto e homologado em `BL-AV-2-03`.

Suíte homologada do Core confirmada sem regressão (68/68) antes e depois da execução dos scripts.

Evidência completa: `docs/governance/evidence/AV-S03/AC-10_validacao_denominador.md`; scripts
reexecutáveis em `docs/governance/evidence/AV-S03/AC-10-scripts/`.

**AC-10: marcado ATENDIDO** no documento da sprint.

## 3. Revisão independente do ajuste de default (isAcademicModuleEnabled)

O ajuste pontual do default de `false` (aplicado por Hermes após achado do Codex na revalidação de
`BL-AV-2-04`) foi submetido a uma revisão independente adicional, limitada exclusivamente a esse
ajuste. Veredito do Codex: **APROVADO COM RESSALVAS** — correção correta, sem regressão funcional
identificada, `npm run lint`/`build` confirmados pelo próprio revisor. Ressalva reafirmada: as duas
configurações (frontend/backend) continuam independentes e podem divergir se alteradas
separadamente no futuro — registrada como `DEBT-AV-012` no registro canônico de débitos técnicos
(o Codex notou que o débito não tinha ID próprio; corrigido nesta rodada).

## 4. Pacote de revisão

Pacote completo montado em `docs/governance/evidence/AV-S03/pacote-revisao-20260928.tar.gz`
(committed), contendo: base Git (branch/HEAD/upstream/divergência), diff completo dos 14 arquivos
rastreados modificados, diff dos 17 arquivos novos contra `/dev/null`, cópia byte-a-byte de cada
arquivo novo (verificada idêntica ao worktree via `cmp`), inventário com SHA-256 individual de
todos os 31 arquivos, checksum SHA-256 do próprio pacote, e verificação de extração do tarball
idêntica ao diretório original (`diff -r`, 0 diferenças).

## 5. Reconciliação documental

Ao preparar os commits, identificou-se que os registros canônicos (`decisions.md`,
`technical_debts.md`) e o documento da sprint (`sprint_AV-S03_estrutura_academica.md`) tinham sido
editados em duas cópias de trabalho diferentes: este worktree (`av-s03-work`) e o checkout principal
do repositório (branch documental de encerramento da AV-S02, base do PR #2). As duas cópias foram
reconciliadas trazendo as decisões já autorizadas (`DEC-AV-023/024/025/026`) para esta branch, junto
das atualizações desta rodada.

**Divergência identificada nesta rodada e RESOLVIDA em 2026-09-29 (reconciliação
pré-merge do PR #3, ver `snapshot_RECONCILIACAO-2026-09-29-01_contrato-openapi-av-s03.md`):**
`docs/contracts/openapi.yaml` tinha duas versões incompatíveis — a desta branch,
conferida rota-a-rota contra o schema OpenAPI real gerado pela aplicação
(`app.openapi()`) sobre o código de `BL-AV-2-03`; e a do checkout principal,
uma proposta de design mais antiga, nunca implementada. Nota de correção
terminológica: a formulação "contrato REAL, testado e homologado" usada
abaixo confundia estados distintos (revisão técnica, testes automatizados e
homologação formal de Rafael); a formulação correta e a decisão de
reconciliação estão registradas no documento de reconciliação linkado acima.

## 6. Organização dos commits (branch `feat/av-s03-estrutura-academica`, a partir de `main`)

| Commit | Conteúdo |
|---|---|
| `cb8a96b` | backend: modelo, migração e autorização (BL-AV-2-01/02/03) |
| `0bf25e9` | frontend: telas mínimas de gestão acadêmica (BL-AV-2-04) |
| `bcef65f` | governança: evidências, snapshots desta sprint, pacote de revisão |
| `a5d0a2c` | reconciliação de registros canônicos e documento da sprint |

Working tree limpo após os 4 commits; validações locais (Ruff, pytest, ESLint, build) reexecutadas
e confirmadas verdes após cada commit relevante.

## 7. Publicação e CI remota

- push: `feat/av-s03-estrutura-academica` → `origin` (novo branch);
- PR: [#3](https://github.com/rafaelinfopiaui/avalia-platform/pull/3), **rascunho** (draft), base
  `main`, HEAD `a5d0a2c6512d60837cb8ca7acab3555d2259bd80`;
- CI remota real (run `36511468808`): **3/3 jobs verdes** — `AI Engine (FastAPI)` (18s),
  `Core API (FastAPI + Postgres)` (1m47s), `Frontend (Vite + React + TS)` (16s);
- `AC-08` atualizado no documento da sprint para **executado e confirmado**, incluindo a evidência
  real de CI remota (antes: parcial, por não haver PR aberto).

## 8. Estado final e limites

- `BL-AV-2-03`: **homologado** por Rafael (`DEC-AV-026`), agora também publicado em PR com CI verde;
- `BL-AV-2-04`: correções verificadas e revalidadas de forma independente (2 rodadas Codex);
  **homologação formal por Rafael continua pendente**;
- `AV-S03` (marco `BL-AV-2-05`): 11 de 12 critérios de aceite com evidência completa (AC-05 mantém
  a ressalva já registrada: retorno pós-login não reverificado visualmente nesta rodada); sprint
  como um todo **permanece aberta**, sujeita a homologação formal por Rafael;
- `avalia_dev`: não acessado nem alterado; toda validação usou PostgreSQL isolado dedicado,
  removido ao final;
- Git/remoto: branch publicada, PR aberto em **rascunho** (draft), CI remota real executada e
  verde; **nenhum merge realizado** — fora do escopo desta execução;
- `DEC-AV-007`: reconfirmado e restrito para `AV-S03` nesta rodada; permanece pendente em caráter
  geral para a trilha completa;
- baseline: não promovido; nova sprint: não iniciada; saneamento operacional: não executado.

## 9. Próxima decisão

Rafael revisar o PR #3 (diff completo disponível também no pacote local
`docs/governance/evidence/AV-S03/pacote-revisao-20260928.tar.gz`) e decidir: (1) homologação de
`BL-AV-2-04` e do marco completo `BL-AV-2-05`; (2) reconciliação de `docs/contracts/openapi.yaml`
entre esta branch e o PR #2 documental já existente; (3) autorização de merge do PR #3, quando
aplicável; (4) tratamento de `DEBT-AV-012` (não bloqueante) em sprint futura.
