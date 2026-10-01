---
id: "EXEC-2026-09-24-10"
tipo: "execucao_local_autorizada"
consolidador: "Hermes"
data: "2026-09-24"
autorizado_por: "Rafael (2026-09-24; DEC-AV-023, DEC-AV-024, DEC-AV-025)"
---

# Snapshot EXEC-2026-09-24-10 — Execução local BL-AV-2-01..05 + ensaio de saneamento + OCR documental

> **Execução exclusivamente LOCAL, em worktree isolado (`/tmp/av-s03-work`, branch
> `local/av-s03-execucao`, base `7f18ec30a4ee486af0d99b131728a32bc362941d`) e PostgreSQL isolado
> (porta 55434, fora de qualquer ambiente do projeto). NENHUM stage, commit, push, merge, migração
> operacional, deploy ou promoção de baseline foi realizado no repositório principal. `avalia_dev`
> não foi tocado em nenhum momento — nem para leitura, nem para escrita.**

## 1. Escopo autorizado e cumprido

Autorização de Rafael (2026-09-24), restrita a:
- `DEC-AV-023`: execução local de `BL-AV-2-01` a `BL-AV-2-05`, PostgreSQL somente isolado,
  revisão cruzada, validação visual;
- `DEC-AV-024`: criação/ensaio do script de saneamento em ambiente isolado, sem escrita em
  `avalia_dev`;
- `DEC-AV-025`: detalhamento documental do levantamento de OCR, sem benchmark/implementação.

## 2. BL-AV-2-01/02 — Modelo e migração da estrutura acadêmica

**Autoria efetiva: Codex CLI** (`codex exec --sandbox workspace-write`), verificação independente
por Hermes.

- Novos modelos em `core/app/models.py`: `Organization`, `Course`, `Discipline`,
  `CourseDiscipline`, `ClassGroup`, `Student`, `Enrollment`, `ProfessorClassLink`; FK
  `Assessment.class_group_id` (nullable, preserva avaliações legadas).
- Migração `core/alembic/versions/c4a8b2d91e37_add_academic_structure.py`, encadeada após
  `7b1d6d853f20`.
- Nova flag `ACADEMIC_MODULE_ENABLED` em `core/app/config.py` (default `false`) — implementa a
  decisão de Rafael: "para novas avaliações, a exigência de turma começa com a ativação do módulo
  acadêmico. Avaliações legadas preservam acesso e histórico."
- Guard de downgrade destrutivo: bloqueia com `RuntimeError` explícito antes de qualquer `DROP`
  quando existem dados dependentes/cadastrais em `enrollments`, `professor_class_links`,
  `assessments.class_group_id`, `students`, `class_groups`, `course_disciplines`, `disciplines`,
  `courses` ou `organizations` (ampliado após achado de revisão cruzada — ver §5).
- Testes: `core/app/tests/test_academic_structure.py` (16 testes, modelo/migração).

**Verificação independente (Hermes, fora do sandbox do Codex):**
- `pytest app/tests -q` → 48 passed (SQLite, ambiente de testes do projeto).
- `ruff check` nos arquivos novos → All checks passed (4 erros de ruff pré-existentes em
  migrações antigas, não tocados por esta sprint, confirmados fora de escopo).
- PostgreSQL isolado real (porta 55434): `alembic upgrade head` cria as 8 tabelas com sucesso;
  `alembic downgrade 7b1d6d853f20` limpo quando não há dados; guard bloqueia downgrade real com
  dados dependentes reais inseridos (não simulado) — `RuntimeError` confirmado antes de qualquer
  `DROP`, dados permaneceram intactos após a tentativa.

## 3. BL-AV-2-03 — Endpoints e autorização

**Autoria efetiva: Antigravity CLI**, revisão cruzada independente por **Codex CLI**
(`codex exec --sandbox read-only`), correções aplicadas por Hermes.

Endpoints novos em `core/app/main.py`: CRUD de `Organization`, `Course`, `Discipline`,
`CourseDiscipline`, `ClassGroup`, `ProfessorClassLink`, `Student`, `Enrollment`, e
`POST /assessments/{id}/class-group`. Contrato em `docs/contracts/openapi.yaml` (paths e schemas
do módulo acadêmico, finalizados antes da implementação).

**Revisão cruzada Codex — achados e correções (hash do diff revisado documentado na sessão):**

| # | Achado (Codex) | Classificação | Correção aplicada | Verificação |
|---|---|---|---|---|
| 1 | Avaliação já vinculada a turma continuava editável (publicar/revincular) mesmo após o vínculo do professor expirar — violava a decisão 6.ii (leitura histórica sem edição) | BLOQUEANTE | Nova função `_assert_assessment_writable`, chamada em `publish_assessment` e `link_assessment_class_group`; leitura (`GET`) permanece liberada | Teste novo `test_expired_link_blocks_publish_and_relink_of_already_linked_assessment`; passou |
| 2 | Admin não conseguia vincular avaliação de qualquer professor a qualquer turma (a matriz de autorização prevê acesso global do admin) | BLOQUEANTE | `link_assessment_class_group` agora só exige propriedade+vínculo ativo quando `user.role == PROFESSOR`; admin passa sem essas checagens | Teste novo `test_admin_can_link_assessment_to_class_group_without_own_link`; passou |
| 3 | Guard de downgrade verificava apenas `enrollments`/`professor_class_links`/`assessments.class_group_id`, permitindo perda silenciosa de organizações/cursos/disciplinas/turmas/alunos órfãos (sem matrícula/vínculo) | BLOQUEANTE | Guard ampliado para checar as 9 tabelas do módulo antes de qualquer `DROP` (ver §2) | Testado no PostgreSQL isolado real: organização órfã sem matrícula bloqueou o downgrade corretamente |
| 4 | 403 antes de 404 permite inferir existência de recursos (turma/matrícula/avaliação) | NÃO BLOQUEANTE | Não corrigido nesta rodada — confirmado como padrão pré-existente desde AV-S01 (`_get_owned_assessment` original, commit `59f9f01`), não uma regressão desta sprint. Registrado como decisão pendente para Rafael (ver §8) | — |
| 5 | `EnrollmentStatus` não usa `values_callable` como `ProfessorRole` | NÃO BLOQUEANTE | Inconsistência de estilo sem impacto funcional; não corrigido | — |

Veredito final da revisão cruzada Codex: `AJUSTES_NECESSARIOS` → todos os 3 achados bloqueantes
corrigidos e reverificados por Hermes de forma independente (não apenas repetição do relato do
Codex).

**Verificação independente de integração (Hermes):** servidor `uvicorn` real contra PostgreSQL
isolado (porta 55434) + chamadas HTTP reais via `urllib`/Playwright — não simulação:
- vínculo `responsible` × `collaborator` (apenas responsible matricula);
- filtragem de turmas por vínculo ativo no banco (JOIN), confirmada com professor sem vínculo
  não enxergando a turma;
- vínculo expirado: professor não vê a turma, matrícula bloqueada (403);
- matrícula duplicada `ACTIVE` → 409 `ACTIVE_ENROLLMENT_ALREADY_EXISTS`;
- `AuditEvent` real persistido para `ProfessorClassLink` e vínculo avaliação↔turma.

## 4. BL-AV-2-04 — UI mínima

**Autoria efetiva: Antigravity CLI**, verificação independente por Hermes (browser real via CDP).

Novos arquivos: `frontend/src/pages/ClassGroupsPage.tsx` (rota `/turmas`),
`frontend/src/pages/ClassGroupDetailPage.tsx` (rota `/turmas/:id`, matrícula de alunos);
alterações em `AssessmentEditorPage.tsx` (seletor de turma), `services/api.ts`, `types.ts`,
`App.tsx`, `Layout.tsx`.

- `npm run lint` → sem erros.
- `npm run build` (`tsc -b && vite build`) → sem erros.

## 5. BL-AV-2-05 — Integração e validação visual real

Backend (`uvicorn`) e frontend (`vite dev`) reais, rodando contra PostgreSQL isolado (porta
55434), navegador Chrome real conectado via CDP (fallback documentado, pois o browser tool do
Hermes não conseguiu abrir `localhost` neste ambiente) + Playwright. Screenshots capturadas e
inspecionadas via `vision_analyze` a cada etapa (evidência em `/tmp/av-s03-work/evidence_*.png`,
fora do Git).

Fluxo real executado e confirmado visualmente:
1. Login do professor;
2. Listagem de turmas (`/turmas`) — turma T01 (2026-2) exibida corretamente;
3. Detalhe da turma (`/turmas/cg-visual-1`) — matrícula de aluno via "Informar ID"; matrícula
   duplicada corretamente rejeitada com mensagem amigável (409 traduzido);
4. Criação de nova avaliação com seleção de turma no editor;
5. **Achado real de integração (bug):** o `POST /assessments` inicial não enviava
   `class_group_id`, então com `ACADEMIC_MODULE_ENABLED=true` a criação falhava com
   `422 MISSING_CLASS_GROUP` mesmo com turma selecionada no formulário. **Corrigido**:
   `payload` do `AssessmentEditorPage.tsx` agora inclui `class_group_id`; tipo de
   `createAssessment` em `api.ts` atualizado. Corrigido e reverificado: rascunho salvo com
   sucesso e badge "Turma vinculada: Turma T01 (2026-2)" confirmado visualmente.
6. Publicação da avaliação — confirmada no banco (`status=PUBLICADA`,
   `class_group_id=cg-visual-1`) via consulta SQL direta. **Achado não corrigido (fora de
   escopo):** a navegação pós-publicação usa `saved.id`, mas o backend de `publish` só retorna
   `{"status": "PUBLICADA"}` sem `id` — bug pré-existente confirmado via
   `git show 7f18ec3:frontend/src/pages/AssessmentEditorPage.tsx` (já presente no commit-base
   `59f9f01`, anterior a esta sprint); não é regressão de BL-AV-2-04, registrado como achado para
   decisão de prioridade de Rafael, não corrigido nesta rodada por estar fora do escopo
   autorizado desta sprint.

## 6. Ensaio isolado do saneamento de `human_reviews` (DEC-AV-024)

Script `core/scripts/av_s02_saneamento_human_reviews.sql` (v4, aprovado por Codex — ver snapshot
`EXEC-2026-09-24-09`) ensaiado em PostgreSQL isolado (porta 55434), NUNCA em `avalia_dev`:

- **Preservação integral**: cenário fictício idêntico ao de `avalia_dev` (job_id
  `4f56a10b-3a44-4df5-9047-adef7546a3c0`, 3 linhas duplicadas) semeado via
  `core/scripts/seed_saneamento_ensaio.sql`; script executado com sucesso — vencedora íntegra,
  2 arquivadas, `AuditEvent`s intocados, 0 grupos duplicados remanescentes.
- **Abortos previstos**: cenário conflitante (divergência de campo entre linhas do mesmo job_id)
  via `seed_saneamento_ensaio_conflitante.sql` — script abortou com `ON_ERROR_STOP` (exit code 3)
  sem alterar nenhuma linha (rollback total confirmado).
- **Recuperação (Cenário B, pré-migração)**: `core/scripts/recuperacao_cenario_b.sql` executado
  após saneamento bem-sucedido em banco sem a constraint ainda aplicada — 3 linhas restauradas,
  arquivo limpo, confirmado por consulta direta.
- **Recuperação (Cenário C, pós-constraint)**: downgrade da migração de unicidade
  (`7b1d6d853f20`) executado para remover a constraint, seguido da mesma recuperação
  compensatória — 3 linhas restauradas com sucesso.
- **Aplicação posterior da constraint**: `alembic upgrade head` reaplicado com sucesso após
  saneamento — `uq_human_reviews_job_id` confirmada via `\d human_reviews`.

Todos os bancos de ensaio foram criados/descartados exclusivamente no PostgreSQL isolado (porta
55434); nenhum arquivo de backup do banco original foi criado ou lido nesta rodada (não houve
necessidade de acesso a `avalia_dev`).

## 7. Detalhamento documental de OCR (DEC-AV-025)

Novo documento `docs/governance/backlog/levantamento_ocr_visao_local.md` (BL-AV-4B-01),
consolidando critérios de avaliação, candidatos técnicos, plano de ensaio futuro (não executado)
e limites explícitos: nenhum benchmark rodado, nenhuma dependência de OCR instalada, nenhuma
implementação de ingestão de imagem.

## 8. Correções aplicadas fora do código (registros)

- `docs/governance/registers/decisions.md`: `DEC-AV-023`, `DEC-AV-024`, `DEC-AV-025`
  registradas como aprovadas restritas ao escopo declarado; `DEC-AV-006`/`DEC-AV-007`
  permanecem pendentes em caráter geral.
- `docs/governance/sprints/sprint_AV-S03_estrutura_academica.md`: frontmatter e banner
  atualizados para `aprovada_execucao_local_autorizada`.
- `docs/contracts/openapi.yaml`: paths e schemas do módulo acadêmico adicionados antes da
  implementação (validado com `yaml.safe_load`).

## 9. Não realizado nesta rodada (decisões pendentes de Rafael)

1. Padrão 403/404 (achado não bloqueante do Codex, §3 item 4): manter o padrão pré-existente
   (403 antes de 404, já usado desde AV-S01) ou alterar para 404 uniforme nos novos recursos
   acadêmicos — mudança afetaria também endpoints legados, fora do escopo local autorizado.
2. Bug pré-existente de navegação pós-publicação (`saved.id` undefined) — priorizar correção
   (fora do escopo desta sprint, mas afeta a UX de todo fluxo de publicação, não só o acadêmico).
3. Integração ao PR #2 / remoto: nenhuma alteração desta rodada foi commitada, staged ou
   enviada. Aguarda autorização específica de Rafael para o próximo passo Git/remoto.
4. Execução em `avalia_dev` (script de saneamento e migração de unicidade `7b1d6d853f20`):
   continua não autorizada; o ensaio comprovou viabilidade técnica, não substitui autorização
   operacional.
5. Homologação da AV-S03: não declarada. Esta execução é técnica/local; validação remota (CI,
   revisão de Rafael sobre o diff exato) permanece pendente.

## 10. Estado do repositório principal

Nenhuma alteração de código (`core/`, `frontend/`) foi aplicada ao repositório principal
(`/Users/rafaeloliveira/Projeto Estágio/avalia-plataform`) nesta rodada — toda a implementação
ocorreu em worktree isolado (`/tmp/av-s03-work`, branch `local/av-s03-execucao`), preservando o
working tree documental pré-existente do repositório principal intacto. O diff completo do código
(3.871 linhas, SHA-256 `86dc39f5cc6ba9b70b2cc70d88659eb1fbf222596b42c3a266ee48ddf0bceab4`) está
disponível fora do Git em `/tmp/av-s03-work/deliverable/av-s03-execucao-local-completa.diff` para
a próxima autorização Git/remota.
