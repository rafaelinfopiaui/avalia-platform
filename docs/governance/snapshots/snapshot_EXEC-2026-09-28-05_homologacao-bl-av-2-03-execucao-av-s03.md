---
id: "EXEC-2026-09-28-05"
tipo: execucao
sprint: "AV-S03"
gerado_em: "2026-09-28T16:45:00-03:00"
executor: "Hermes (com Antigravity para BL-AV-2-04)"
status: parcial
commit_referencia: "66c95201daf893fa7b2852e0d94b20314f8d8f34"
---

# Snapshot EXEC-2026-09-28-05 — homologação de BL-AV-2-03, execução local dos demais itens da AV-S03

> Registro histórico. Não promover automaticamente a baseline.

## 1. Abertura

- objetivo: (1) registrar a homologação formal de `BL-AV-2-03` por Rafael; (2) continuar a execução
  local já autorizada da AV-S03, conferindo `BL-AV-2-01/02/04/05` contra os artefatos atuais,
  completando pendências no escopo já autorizado, reexecutando verificações onde havia lacuna ou
  alteração relevante;
- escopo autorizado: implementação mínima de `BL-AV-2-04` (frontend); revalidação de migração em
  PostgreSQL isolado; validação visual em navegador real; consolidação documental; construção de
  pacote recuperável consolidado da AV-S03;
- fora de escopo, mantido: `avalia_dev`, stage, commit, push, tag, deploy, promoção de baseline,
  início de nova sprint;
- branch/upstream/commit: `local/av-s03-recuperacao`, `origin/main`, `66c95201daf893fa7b2852e0d94b20314f8d8f34`;
- worktree: `avalia-plataform-worktrees/av-s03-work` (reconstrução; o worktree original de
  2026-09-24 foi perdido, ver `snapshot_EXEC-2026-09-28-01_pacote_revisao_av-s03.md` §3).

## 2. Homologação de BL-AV-2-03

Rafael homologou `BL-AV-2-03` na versão reconstruída identificada pelo pacote canônico em
`docs/governance/evidence/AV-S03/pacote-revisao-20260928/` e pelo manifesto histórico
`docs/governance/evidence/AV-S03-recuperacao/BL-AV-2-03-pacote/checksums_FINAL_20260928_162232.sha256`,
com base no parecer independente e adversarial da terceira rodada de revisão cruzada (Antigravity,
somente leitura): **APROVADO SEM RESSALVAS**. Registrado formalmente em `DEC-AV-026`
(`docs/governance/registers/decisions.md`).

**Distinções explícitas da homologação, preservadas nesta execução:**
1. item tecnicamente aprovado e homologado — `BL-AV-2-03` apenas;
2. código permanece local, sem stage/commit/push/merge — homologação técnica não é integração;
3. `AV-S03` como sprint permanece aberta, sujeita ao fechamento dos demais critérios de aceite.

`BL-AV-2-03` não foi reaberto nesta execução — nenhuma alteração de código relevante ou nova
evidência de defeito o justificaria.

## 3. Itens revalidados/concluídos nesta execução

| Item | Ação nesta execução | Evidência |
|---|---|---|
| `BL-AV-2-01` (modelo) | conferido contra `core/app/models.py` atual; sem alteração necessária | inspeção direta |
| `BL-AV-2-02` (migração) | revalidado em PostgreSQL 16 isolado (porta 55435, banco `avalia_bl_av_2_03_revalidacao`, descartado ao final): `alembic upgrade head` limpo; downgrade limpo em banco vazio; downgrade com dados dependentes reais (organização/curso/disciplina/associação/turma inseridos) **abortou com `RuntimeError` antes de qualquer DROP**, dados confirmados intactos por `SELECT` direto | comandos executados ao vivo por Hermes, não apenas relatados |
| `BL-AV-2-04` (UI mínima) | implementado por Antigravity (delegação conforme tabela de delegação da sprint, §8); revisado e confirmado ao vivo por Hermes: `npm run lint` limpo, `npm run build` 0 erros, suíte Core 68/68 sem regressão | `frontend/src/pages/AcademicPage.tsx` (novo), `AssessmentEditorPage.tsx`, `services/api.ts`, `types.ts`, `App.tsx`, `Layout.tsx`, `styles/theme.css` (alterados) |
| `BL-AV-2-05` (validação do marco) | AC-01 a AC-12 revisados um a um contra evidência real desta rodada (ver `sprint_AV-S03_estrutura_academica.md` §9 atualizada); 8 de 12 critérios com evidência completa, 2 pendentes de revisão documental (AC-07/09), 1 sem CI remota por estar fora de escopo (AC-08 parcial), 1 não fechado formalmente (AC-10) | seção 9 da sprint, atualizada nesta execução |

## 4. Validação visual em navegador real (AC-06)

Ambiente: backend `uvicorn` real (porta 8010) + PostgreSQL 16 isolado (porta 55435, banco
`avalia_visual_av_s03`, populado por seed fictício) + frontend `vite` real (porta 5183) + Chrome
real via CDP (fallback documentado por bloqueio do browser tool padrão em `localhost`/IPs privados,
mesmo padrão já usado em 2026-09-24).

Fluxo validado ponta a ponta, com evidência de rede capturada (não presumida):
1. login real (professor e admin, JWT real emitido pelo backend);
2. criação de Organização → Curso → Disciplina → associação curricular → Turma → Aluno via API real
   (admin) e confirmação visual na UI;
3. vínculo professor↔turma (`RESPONSIBLE`) via API real;
4. professor visualiza exatamente sua turma vinculada na UI (escopo de autorização refletido
   corretamente na interface);
5. matrícula do aluno na turma (via admin — ver achado operacional abaixo);
6. criação de avaliação nova pelo professor com seletor de turma na UI: payload de rede capturado via
   CDP confirma `class_group_id` correto enviado em `POST /v1/assessments` (`201 Created`); rubrica
   publicada (`POST /v1/questions/{id}/rubric`, `201 Created`); persistência confirmada por consulta
   direta ao banco (`GET /v1/assessments` retorna o `class_group_id` salvo).

**Confirmação de regressão:** o bug de 2026-09-24 (turma selecionada no formulário não era enviada
no `POST /assessments` inicial, conforme `executive_technical_dashboard.md` linha 56 histórica) **não
está presente na implementação reconstruída** — confirmado por captura de rede real, não por leitura
de código.

Evidência (18 capturas de tela): `docs/governance/evidence/AV-S03-recuperacao/BL-AV-2-04-visual/`.

## 5. Achado operacional registrado (não bloqueante, não reabre BL-AV-2-03)

Ao tentar matricular um aluno via UI como professor `RESPONSIBLE`, o dropdown de "Aluno" no
formulário de Matrícula está vazio para um aluno que nunca esteve em nenhuma turma do professor.
Causa raiz confirmada por chamada direta à API: `GET /v1/students` retorna `[]` para o professor
nesse cenário (a função `_student_scope` em `academic.py` só retorna alunos já matriculados em
turmas ativas do professor) e `[aluno]` para o admin com o mesmo dado. **Isso é o comportamento
correto conforme a matriz de autorização aprovada** (seção 5 da sprint, linha "Dados globais do
aluno — leitura mínima"), não um defeito de autorização. Na prática, gera uma dependência
operacional: a primeira matrícula de um aluno novo em qualquer turma precisa ser feita por um admin
(ou o backend precisa de uma rota de busca por identificador exato, fora do escopo desta execução).
Registrado na sprint (§9) para decisão de Rafael; nenhuma alteração de autorização foi feita.

## 6. Pacote consolidado e verificação de completude

Dois pacotes recuperáveis foram produzidos, ambos com checksums SHA-256 verificados.
Na regularização documental de 2026-09-30, o conteúdo integral redundante ficou no pacote externo
`RECUPERACAO-LOCAL-20260930_221041`; no Git permanecem apenas o necessário à rastreabilidade e o
pacote canônico revisável:

1. `docs/governance/evidence/AV-S03-recuperacao/` — índice dos 39 artefatos originais, parecer final,
   manifesto final e 18 capturas da reconstrução; tarballs e rodadas intermediárias não foram
   duplicados no Git.
2. `docs/governance/evidence/AV-S03/pacote-revisao-20260928/` — pacote canônico revisável da
   reconstrução, com diffs, inventário e arquivos novos.

**Verificação de completude real** (não apenas checksum agregado): o tarball consolidado foi extraído
em diretório temporário e cada um dos 22 arquivos foi comparado byte-a-byte (`diff`) contra o arquivo
correspondente no worktree real. Resultado: **22/22 arquivos idênticos** — nenhuma divergência, nenhum
arquivo ausente. Checksums SHA-256 de todos os artefatos do pacote confirmados com `shasum -c`.

## 7. Validações executadas (resumo)

| Item | Comando | Resultado real |
|---|---|---|
| Core (regressão completa) | `cd core && ruff check app/ && pytest app/tests -q` | Ruff limpo; **68 passed, 0 failed**, 12 warnings |
| Frontend | `cd frontend && npm run lint && npm run build` | 0 erros, 0 avisos; build 0 erros |
| Migração PostgreSQL isolado | `alembic upgrade head` / `downgrade -1` (limpo e com dados dependentes) | upgrade OK; downgrade limpo OK; downgrade com dados dependentes abortou corretamente sem DROP |
| Validação visual | Chrome real via CDP, fluxo completo | login, CRUD acadêmico, vínculo, matrícula, avaliação vinculada — todos confirmados; payload de rede capturado |
| Completude do pacote consolidado | `diff` byte-a-byte de 22/22 arquivos extraídos vs worktree | 22/22 idênticos |

## 8. Estado final e limites

- `BL-AV-2-03`: homologado por Rafael (`DEC-AV-026`), local, não integrado;
- `BL-AV-2-01/02/04`: implementados e revalidados tecnicamente nesta execução, sem homologação
  formal própria — aguardam decisão de Rafael sobre o fechamento do marco `BL-AV-2-05`;
- `BL-AV-2-05` (marco da sprint): parcialmente executado; AC-07/09/10 pendentes; AC-08 parcial (sem
  CI remota, sprint segue local);
- `AV-S03` como sprint: **permanece aberta**; esta execução não declara a sprint concluída ou
  homologada;
- `avalia_dev`: não acessado nem alterado; todos os testes/validações usaram bancos SQLite
  temporários ou PostgreSQL isolado (portas 55434/55435, descartáveis, fora de qualquer ambiente do
  projeto);
- Git/remoto: nenhuma ação de stage, commit, push, tag, deploy ou outra ação remota foi realizada;
- baseline: não promovido; nova sprint: não iniciada.

## 9. Próxima decisão

Rafael revisar a proposta de commits/PRs (ver `executive_technical_dashboard.md` e comunicação
direta desta execução) e decidir: (1) se autoriza consolidar `BL-AV-2-01/02/04` num commit/PR
próprio agora ou aguarda o fechamento completo de `BL-AV-2-05`; (2) tratamento de AC-07/09/10
pendentes; (3) relação com o PR #2 já aberto (branch `docs/av-s02-encerramento-planos-operacionais`,
puramente documental, sem código da AV-S03).
