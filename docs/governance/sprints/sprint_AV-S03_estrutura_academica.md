---
id: "AV-S03"
status: homologada_integracao_autorizada_2026-09-29_DEC-AV-027
objetivo_aprovado_por: "Rafael (2026-09-24; DEC-AV-023; escopo restrito à AV-S03)"
consolidador: "Hermes"
baseline_entrada: "../snapshots/latest_validated_baseline.md (nenhum promovido; código AV-S01/AV-S02 integrado a main em 2026-09-24, SHA 66c95201daf893fa7b2852e0d94b20314f8d8f34, mas isso NÃO é baseline operacional promovido)"
---

# AV-S03 — Estrutura acadêmica mínima: Organização, Curso, Disciplina, Turma e Aluno

> **PLANO APROVADO PARA EXECUÇÃO LOCAL EM 2026-09-24 (DEC-AV-023).** A autorização cobre
> `BL-AV-2-01` a `BL-AV-2-05`, PostgreSQL somente isolado, dados fictícios, revisão cruzada e
> validação visual. Não autoriza stage, commit, push, merge, CI remota, migração operacional,
> deploy ou promoção de baseline; por isso o fechamento integral continua bloqueado até autorização
> Git/remota e sua evidência.

## 1. Objetivo e valor esperado

Introduzir uma estrutura acadêmica mínima e coerente para substituir o uso isolado de avaliações
sem contexto de turma/aluno, permitindo:

- modelar Organização → Curso → Disciplina → Turma → Aluno;
- vincular professor à turma e avaliação à turma;
- reaplicar o padrão de autorização por vínculo corrigido em AV-S01 (professor só opera turmas às
  quais está vinculado; admin mantém acesso global);
- oferecer telas mínimas para criar turma/aluno e vincular avaliação à turma;
- validar o marco com dados fictícios: um professor vinculado à turma consegue operar seus dados;
  outro professor não vinculado recebe 403, sem vazamento.

Valor: cria a base necessária para AV-S04 (avaliações completas/múltiplas questões), entrada por
imagem e importação futura, sem introduzir multi-tenancy implícito nem antecipar identificação
automática de aluno/questão.

## 2. Origem e posição na trilha

| Fonte/requisito | Aplicação | Link |
|---|---|---|
| Etapa 2 / Fase 3 da trilha "Operação de uma turma" | estrutura acadêmica e vínculos necessários às etapas posteriores | [`trilha_operacao_de_turma.md`](../backlog/trilha_operacao_de_turma.md) §2/§11 |
| `BL-AV-2-01` | modelo Organização/Curso/Disciplina/Turma/Aluno | [`backlog_tecnico_avalia.md`](../backlog/backlog_tecnico_avalia.md) |
| `BL-AV-2-02` | migração Alembic da estrutura acadêmica | idem |
| `BL-AV-2-03` | permissões por vínculo professor↔turma | idem |
| `BL-AV-2-04` | telas mínimas de turma/aluno e vínculo à avaliação | idem |
| `BL-AV-2-05` | critério de aceite do marco (turma fictícia + alunos + vínculo/autorização) | idem |
| padrão integrado em AV-S01 | autorização por vínculo e teste de acesso cruzado | [`sprint_AV-S01...md`](sprint_AV-S01_autorizacao_retomada_revalidacao.md) |

Dependência real satisfeita: a Etapa 2 depende do padrão de autorização por vínculo da Etapa 1
estar corrigido, para não replicar a lacuna anterior na estrutura nova. AV-S01 está homologada e o
código foi integrado a `main` com CI verde em 2026-09-24.

## 3. Escopo

Incluído:
- modelos/tabelas mínimos: `Organization`, `Course`, `Discipline`, associação curricular
  curso↔disciplina, `ClassGroup` (Turma/oferta), `Student` e `Enrollment` (matrícula);
- turma vinculada à **associação curricular curso–disciplina**, e não diretamente a uma disciplina
  ambígua quando `Course↔Discipline` for N:N; se Rafael optar por `Course 1:N Discipline`, a FK
  direta equivalente e suas unicidades serão usadas conforme a decisão da seção 14;
- entidade explícita de vínculo professor↔turma com estado e vigência suficientes para autorização,
  sem transformar colaboração em propriedade automática dos recursos da turma;
- vínculo avaliação↔turma preservando separadamente o proprietário da avaliação; avaliações legadas
  sem turma continuam acessíveis ao proprietário já autorizado e ao admin;
- migração Alembic aditiva e reversível enquanto não houver dados dependentes; downgrade destrutivo
  deve detectar dependências e abortar com diagnóstico, nunca apagá-las para produzir sucesso;
- endpoints Core mínimos para listar/criar/editar (sem exclusão destrutiva nesta primeira entrega):
  organizações, cursos, disciplinas, associações curriculares, turmas, alunos, matrículas e vínculos
  professor↔turma;
- checagem de autorização por vínculo ativo em cada endpoint novo, combinada com propriedade da
  avaliação quando aplicável;
- telas frontend mínimas de turma/aluno/matrícula/vínculo da avaliação;
- testes de autorização cruzada, vínculos expirados/inativos, propriedade, constraint, migração e
  fluxo visual com dados fictícios;
- contrato OpenAPI atualizado.

Fora de escopo:
- arquitetura multi-tenant completa (isolamento forte por tenant, schemas/bancos por organização,
  tenant context obrigatório em todas as queries, subdomínio por organização, billing por tenant,
  políticas cross-tenant); ver seção 5;
- múltiplas questões por avaliação (AV-S04);
- importação CSV (Etapa 4, continua posterior à imagem por `DEC-AV-016`);
- upload/OCR/transcrição de imagem (Fase 2/Etapas 4B; investigação pode avançar em paralelo, mas
  implementação de entrada por imagem não pertence a AV-S03);
- dados reais de alunos, LGPD/consentimento/retention final; somente dados fictícios;
- autenticação de aluno, portal do aluno, liberação de resultado ao aluno;
- migração operacional de `7b1d6d853f20`/saneamento de duplicatas de AV-S02 (procedimento separado,
  fora desta sprint);
- tag/deploy/promoção de baseline.

## 4. Premissas propostas para DEC-AV-006 e DEC-AV-007 (não são decisões resolvidas)

As decisões continuam **pendentes** no registro canônico. A aprovação deste plano deve indicar se
Rafael aceita estas premissas APENAS para AV-S03 ou se quer decidir as `DEC-AV-006/007` de forma
geral. Até decisão explícita, tratá-las como hipóteses de planejamento, não fatos.

### 4.1 DEC-AV-006 — ambiente-alvo

**Premissa proposta para AV-S03:** execução e validação em ambiente local isolado do executor,
PostgreSQL 16 isolado para migração/testes de integração, dados 100% fictícios, sem deploy e sem
qualquer dado real. CI remota deve reproduzir Core/AI/frontend, mas não equivale a homologação em
ambiente compartilhado/piloto.

Efeito no modelo de dados:
- podemos criar modelos/migrações aditivos sem mecanismo de provisionamento multiambiente;
- não definimos SLA, backup/restore operacional ou estratégia de migração de dados reais dentro de
  AV-S03;
- migração operacional de `avalia_dev` (inclusive pendência de AV-S02) permanece processo separado.

Efeito nas permissões:
- autorização testada por dados fictícios em banco isolado/local; sem alegação de validação em
  piloto multiusuário real;
- matriz mínima: professor vinculado, professor não vinculado, admin, usuário sem autenticação.

Efeito nos critérios de aceite:
- aceitação local + CI remota + validação visual real no navegador com dados fictícios;
- não inclui desempenho, disponibilidade, segurança de rede ou uso com dados reais.

**Decisão objetiva solicitada a Rafael:** aceitar esta premissa restrita a AV-S03, ou escolher outro
ambiente-alvo (homologação compartilhada/piloto supervisionado). A decisão geral de DEC-AV-006 só
muda de `pendente` para `aprovada` se Rafael disser explicitamente que a escolha vale para a trilha,
não apenas para esta sprint.

### 4.2 DEC-AV-007 — dimensionamento

**Premissa proposta para AV-S03 (apenas para desenho e testes):**
- 1 organização;
- 1 curso;
- 2 disciplinas;
- 2 turmas;
- 2 professores;
- 10 alunos fictícios por turma;
- 2 avaliações (uma por turma), 1 questão por avaliação (limite atual do produto, AV-S04 amplia);
- volume de respostas baixo (até 20), sem meta de carga/desempenho nesta sprint.

Efeito no modelo de dados:
- cardinalidades corretas (sem hardcode dos números acima): `Organization` 1:N `Course`;
- se `Course↔Discipline` for N:N, uma associação curricular explícita (por exemplo
  `CourseDiscipline`) representa a disciplina no currículo do curso, e `ClassGroup` referencia essa
  associação; a unicidade proposta da oferta passa a ser
  `(course_discipline_id, period, code)`, evitando uma turma de disciplina sem curso definido;
- se Rafael optar por `Course 1:N Discipline`, `ClassGroup` referencia `discipline_id`, e a
  unicidade equivalente é `(discipline_id, period, code)`; as duas alternativas continuam
  pendentes e não devem coexistir por conveniência na implementação;
- `ClassGroup` N:N `Student` usa `Enrollment`, separando identidade global do aluno de status,
  datas e demais atributos da matrícula na turma;
- vínculo professor↔turma é entidade explícita com papel, estado e vigência; vínculos inativos,
  ainda não iniciados ou expirados não satisfazem autorização;
- índices mínimos nas FKs e unicidades no escopo pai aprovado; nenhum particionamento/sharding.

Efeito nas permissões:
- a matriz de acesso exige pelo menos 2 professores/2 turmas para provar isolamento por vínculo;
- admin acessa ambas; professor A não acessa turma/avaliação do professor B apenas por compartilhar
  vínculo com a mesma turma;
- propriedade da avaliação e vínculo ativo com a turma são verificações distintas: o responsável
  pela avaliação mantém edição; um colaborador da turma recebe somente as ações explicitamente
  aprovadas na matriz, sem herdar edição de avaliações de outro professor;
- avaliações legadas com `class_group_id = NULL` continuam acessíveis ao proprietário segundo as
  regras homologadas em AV-S01 e ao admin; não se tornam globais nem inacessíveis por falta de turma;
- professor pode gerir a matrícula na turma autorizada conforme matriz aprovada, mas não alterar os
  dados globais compartilhados do aluno;
- uma única organização no teste NÃO prova isolamento entre organizações (ver seção 5).

Efeito nos critérios de aceite:
- suíte precisa exercitar o denominador (2 professores, 2 turmas, 10 alunos por turma) sem alegar
  escalabilidade além dele;
- nenhuma meta de latência/performance é estabelecida nesta sprint; isso depende de DEC-AV-007
  geral/hardware (`DEC-AV-009`).

**Decisão objetiva solicitada a Rafael:** aceitar esta premissa de teste restrita a AV-S03, ajustar
os números, ou resolver DEC-AV-007 para toda a trilha. Até manifestação explícita, DEC-AV-007
permanece `pendente`.

## 5. Estrutura acadêmica ≠ multi-tenancy

A entidade `Organization` nesta sprint representa **estrutura de domínio acadêmico**, não uma
fronteira automática de tenant. Em AV-S03, ela permite associar cursos e organizar dados — mas não
introduz implicitamente:

- tenant context obrigatório na sessão/token;
- filtro automático por `organization_id` em todas as queries;
- isolamento criptográfico/físico por banco ou schema;
- proteção cross-organization global;
- administração/billing/configuração por tenant;
- invariantes de unicidade globais vs. por tenant em todo o produto.

Regra de autorização desta sprint: isolamento por **vínculo explícito professor↔turma** e
propriedade dos recursos derivados, usando o padrão já comprovado em AV-S01. A presença de
`organization_id` nas entidades não deve ser apresentada como garantia de isolamento
multi-organização. Se Rafael quiser isolamento entre organizações como requisito de segurança, ele
deve virar decisão/backlog próprios antes da implementação (por exemplo `DEC-AV-023`/item futuro),
com matriz cross-org e revisão de todas as queries — não será inferido nesta sprint.

### 5.1 Matriz proposta de autorização por recurso/ação (decisão necessária antes do DoR)

A autorização por vínculo professor↔turma não resolve sozinha operações sobre entidades pai,
administração de vínculos, propriedade de avaliações ou identidade global de alunos. Regras
transversais propostas, ainda sujeitas à aprovação de Rafael:

1. vínculo só autoriza quando `active = true`, `starts_at <= agora` (se preenchido) e
   `ends_at > agora` (se preenchido); vínculo inativo, futuro ou expirado não concede acesso novo;
2. vínculo com a turma concede contexto, não transfere propriedade: uma avaliação mantém
   `owner_professor_id`; colaboração não concede implicitamente edição da avaliação de outro dono;
3. identidade global de `Student` e matrícula `Enrollment` são recursos diferentes; professor pode
   operar matrícula dentro da turma autorizada conforme a política aprovada, mas não reescrever
   dados globais compartilhados do aluno;
4. avaliação legada com `class_group_id = NULL` preserva acesso do proprietário já autorizado e do
   admin; não é publicada para outros professores e não depende de vínculo de turma inexistente;
5. para avaliações com turma após expiração do vínculo, nenhuma permissão derivada da turma
   sobrevive. A manutenção de leitura histórica do próprio autor versus bloqueio total é uma escolha
   explícita da seção 14; até decisão, a implementação não pode inferi-la.

| Recurso/ação | Admin | Professor com vínculo ativo | Professor sem vínculo ativo | Não autenticado |
|---|---|---|---|---|
| Organização — criar/editar | permitido | proibido (403) | proibido (403) | 401 |
| Organização — listar/ler | global | somente organizações derivadas de suas turmas ativas, sem listar outras | vazio/403 conforme rota | 401 |
| Curso/Disciplina/associação curricular — criar/editar | permitido | proibido (403) | proibido (403) | 401 |
| Curso/Disciplina/associação curricular — listar/ler | global | somente pais necessários às suas turmas ativas | vazio/403 conforme rota | 401 |
| Turma — criar/editar | permitido | leitura/operação somente durante vínculo ativo; criação/edição administrativa proibida | 403 | 401 |
| Gerir vínculo professor↔turma | permitido | proibido: não pode autoatribuir-se, reativar-se nem alterar/remover outros | proibido | 401 |
| Dados globais do aluno — criar/editar identidade | permitido | proibido; alteração compartilhada exige operação administrativa | proibido | 401 |
| Dados globais do aluno — leitura mínima | global | somente campos necessários aos alunos matriculados em turmas ativas vinculadas | 403 | 401 |
| Matrícula — criar/alterar status/datas/encerrar | permitido | somente em turma ativa vinculada e conforme papel aprovado na decisão 6 da seção 14 | 403 | 401 |
| Avaliação com turma — criar | permitido | pode criar avaliação própria em turma ativa vinculada, conforme papel aprovado | 403 | 401 |
| Avaliação com turma — ler | global | própria ou acesso explicitamente concedido pela política de papel; vínculo sozinho não implica edição | 403 sem vazamento | 401/retorno pós-login |
| Avaliação com turma — editar/excluir | global | somente proprietário, salvo poder adicional de responsável explicitamente aprovado; colaborador não herda edição | 403 sem vazamento | 401 |
| Avaliação legada sem turma — ler/editar | global | somente o proprietário conforme regras homologadas; demais professores sem acesso | somente proprietário direto; vínculo de turma é inaplicável | 401/retorno pós-login |
| Vínculo inativo/futuro/expirado | global | não conta como ativo; perde permissões derivadas da turma | 403; eventual leitura histórica própria depende da decisão 6 | 401 |

Cada rota nova precisa de testes positivos e negativos correspondentes. Listagens devem filtrar no
banco, não buscar globalmente e filtrar em memória. Erros 403/404 devem seguir a política já usada
pelo produto sem revelar a existência de recurso não autorizado. Testes devem cobrir transições de
vínculo ativo→inativo/expirado e provar que a expiração revoga o acesso derivado sem apagar dados.

**Decisão objetiva solicitada:** Rafael aprova esta matriz e escolhe as alternativas de papel e
pós-expiração da seção 14, ou ajusta quais operações professor pode executar. Sem essas decisões,
`BL-AV-2-03` permanece refinado, não `ready`.

## 6. Backlog e DoR

| ID | Entrega | DoR | Estado |
|---|---|---|---|
| BL-AV-2-01 | modelo acadêmico mínimo | **implementado e revalidado (2026-09-28)** — modelo completo em `core/app/models.py` (Organization/Course/Discipline/CourseDiscipline/ClassGroup/Student/Enrollment/ProfessorClassLink), unicidades conforme seção 5 | implementado, local, não homologado formalmente à parte (ver BL-AV-2-05) |
| BL-AV-2-02 | migração Alembic aditiva | **implementado e revalidado (2026-09-28)** — `c4a8b2d91e37_add_academic_structure.py`; `alembic upgrade head`/`downgrade` executados em PostgreSQL 16 isolado (porta 55435, fora de qualquer ambiente do projeto); guard de downgrade testado com dados dependentes reais: abortou com `RuntimeError` **antes de qualquer DROP**, dados preservados (evidência reconstruída e pacote revisável: `docs/governance/evidence/AV-S03/pacote-revisao-20260928/`; classificação do pacote intermediário omitido do Git: `docs/governance/evidence/AV-S03-recuperacao/README.md`) | implementado, local, não homologado formalmente à parte (ver BL-AV-2-05) |
| BL-AV-2-03 | autorização professor↔turma | **HOMOLOGADO por Rafael (DEC-AV-026, 2026-09-28)** — 3 rodadas de correção após revisão cruzada adversarial independente (Antigravity), veredito final APROVADO SEM RESSALVAS, reverificado sem regressão; suíte focal 20/20, suíte Core 68/68 determinística | **homologado, local, não integrado ao repositório principal** |
| BL-AV-2-04 | telas mínimas de turma/aluno/vínculo | **implementado e validado visualmente (2026-09-28)** — `frontend/src/pages/AcademicPage.tsx` (abas Organização/Curso/Disciplina/Turma/Aluno/Matrícula, separação estrita Student↔Enrollment), seletor de turma em `AssessmentEditorPage.tsx`; validado em Chrome real via CDP contra backend real + PostgreSQL isolado: login, criação de organização→curso→disciplina→turma, vínculo professor↔turma, matrícula (via admin), criação de avaliação com `class_group_id` enviado e persistido corretamente (payload de rede capturado, não presumido) | implementado, local, não homologado formalmente à parte (ver BL-AV-2-05) |
| BL-AV-2-05 | validação do marco | **concluído (2026-09-29)** — AC-01 a AC-12 têm evidência real completa nesta sprint (ver seção 9); todos os 12 critérios de aceite executados e confirmados | **concluído; marco da sprint homologado por Rafael (DEC-AV-027)** |

**Nota (2026-09-28):** a implementação original de 2026-09-24 (worktree `/tmp/av-s03-work`) foi
perdida (ver `snapshot_EXEC-2026-09-28-01_pacote_revisao_av-s03.md` §3). Toda a evidência acima é da
**reconstrução em novo worktree** (`avalia-plataform-worktrees/av-s03-work`, branch
`local/av-s03-recuperacao`), obtida por reexecução real, não por reaproveitamento do relato antigo.
`BL-AV-2-03` foi o único item com processo formal de homologação distinto nesta rodada; os demais
permanecem tecnicamente implementados/validados mas aguardam decisão de Rafael sobre fechamento do
marco `BL-AV-2-05` e da sprint como um todo antes de qualquer integração.

## 7. Mapa de impacto inicial

| Item | Criar | Alterar | Não tocar |
|---|---|---|---|
| BL-AV-2-01/02 | `core/alembic/versions/<nova_revision>_estrutura_academica.py`; testes `core/app/tests/test_academic_structure.py` | `core/app/models.py`, `core/app/schemas.py`; fixtures isoladas em `core/app/tests/conftest.py` somente se necessário; associação curricular, `Enrollment`, vínculo professor↔turma e guard de downgrade conforme decisões aprovadas | migração AV-S02 `7b1d6d853f20`, dados existentes em `avalia_dev`, seed de demonstração sem decisão explícita |
| BL-AV-2-03 | testes `core/app/tests/test_academic_authorization.py` | `core/app/main.py` ou novo `core/app/routers/academic.py` (escolher um padrão após inspeção); `deps.py` apenas se necessário; checagens de propriedade, vínculo ativo e legado sem turma | sem transformar autorização em multi-tenant implícito; sem refatorar auth fora das rotas acadêmicas |
| BL-AV-2-04 | páginas/componentes acadêmicos sob `frontend/src/pages/` e testes aplicáveis | `frontend/src/App.tsx`, `services/api.ts`, `types.ts`; UI separa dados globais do aluno da matrícula | fluxo de revisão humana já homologado; nada de OCR/upload |
| BL-AV-2-05 | `docs/governance/evidence/AV-S03/`, snapshot e fechamento | sprint, dashboard, backlog/débitos/decisões; READMEs/contrato conforme resultado | baseline validado sem autorização de promoção |
| Contrato | — | `docs/contracts/openapi.yaml`, `core/README.md`, `frontend/README.md` se existir/aplicável | PRD/ADR sem decisão explícita |

Mudança fora deste mapa exige registro prévio em Ajustes de Percurso; ampliação relevante depende
de Rafael.

## 8. Delegação proposta (apenas após aprovação da sprint)

| Item | Executor proposto | Revisor distinto | Limites |
|---|---|---|---|
| BL-AV-2-01/02 | Codex | Antigravity CLI | modelo+migração; banco isolado; não aplicar em `avalia_dev` sem autorização específica |
| BL-AV-2-03 | Antigravity CLI ou Codex (distinto do autor do modelo) | o outro agente, distinto do implementador | autorização/matriz; não refatorar auth fora do necessário |
| BL-AV-2-04 | Antigravity CLI | Codex | UI mínima; dados fictícios; sem design system/refatoração ampla |
| BL-AV-2-05 | Hermes (evidência) | agente que não implementou o fluxo visual | navegador real, sem segredos/dados reais |
| Consolidação | Hermes | — | sprint/snapshot/dashboard, distinção planejado/implementado/validado/homologado |

Disponibilidade dos agentes deve ser reconfirmada no início da execução; fallback/autoria real
devem ser registrados sem inferência.

## 9. Critérios de aceite propostos

| ID | Critério | Método | Estado |
|---|---|---|---|
| AC-01 | upgrade cria a estrutura acadêmica em PostgreSQL isolado sem perda; downgrade funciona quando não há dados dependentes e, quando há, aborta com diagnóstico antes de remover qualquer dado ou tabela | migração + cenários SQL de upgrade/downgrade | **executado e confirmado (2026-09-28)** — upgrade/downgrade limpo OK; downgrade com dados dependentes abortou com `RuntimeError` antes de qualquer DROP, dados preservados (evidência: `AV-S03-pacote-consolidado`) |
| AC-02 | professor com vínculo ativo consegue listar/operar turma, matrículas e avaliações dentro dos poderes do papel aprovado | integração HTTP real | **executado e confirmado (2026-09-28)** — validado via HTTP real (backend + Postgres isolado) e via UI real (Chrome/CDP): professor RESPONSIBLE viu sua turma, avaliação criada com `class_group_id` persistido |
| AC-03 | professor não vinculado, inativo, ainda não iniciado ou expirado recebe 403 nas rotas da turma/matrícula/avaliação; nenhum dado é vazado | matriz de autorização, 2 professores/2 turmas + transições de vigência | **executado e confirmado (2026-09-28)** — coberto pela suíte de 20 testes focais de `BL-AV-2-03` (homologada), incluindo anti-oráculo 404/403 |
| AC-04 | admin mantém acesso global conforme padrão existente | integração HTTP real | **executado e confirmado (2026-09-28)** — validado via HTTP real e via UI (admin viu todas as organizações/alunos/matrículas) |
| AC-05 | usuário não autenticado recebe 401 e retorna ao destino após login quando aplicável | integração + visual | **executado e confirmado (2026-09-29)** — 401 automatizado reconfirmado (`test_academic_routes_require_authentication`); retorno ao destino pós-login validado visualmente em ambiente isolado contra o código integrado a `main`: acesso não autenticado a `/academico` redireciona a `/login` preservando o destino (`history.state.from`), e após login retorna automaticamente a `/academico` (`page.wait_for_url` confirmado + evidência visual); evidência completa em `docs/governance/evidence/AV-S03/AC-05_validacao_retorno_pos_login.md` |
| AC-06 | UI cria/visualiza turma e aluno fictício, gere matrícula separadamente e vincula avaliação à turma sem expor dados reais | navegador real | **executado e confirmado (2026-09-28)** — Chrome real via CDP, dados fictícios, fluxo completo (login→organização→curso→disciplina→turma→aluno→matrícula→avaliação vinculada) validado ponta a ponta; evidência em `docs/governance/evidence/AV-S03-recuperacao/BL-AV-2-04-visual/` (18 capturas) |
| AC-07 | Organização é entidade de domínio, sem alegação de isolamento multi-tenant; nenhuma query é implicitamente globalizada por `organization_id` sem requisito aprovado | revisão de segurança/arquitetura | **executado e confirmado (2026-09-28)** — revisão de arquitetura dedicada (não apenas inspeção pontual): nenhuma query filtra por `organization_id` fora de `_organization_ids_for_user`/`_course_scope`/`_discipline_scope`, todas derivadas do vínculo real de turma; `User` não possui `organization_id`; evidência completa em `docs/governance/evidence/AV-S03/AC-07-AC-09_revisao_arquitetura.md` |
| AC-08 | suíte Core, Ruff, ESLint, frontend build e CI remota permanecem verdes | automatizada/local+remota | **executado e confirmado (2026-09-29)** — Core 68/68, Ruff limpo, ESLint limpo, `npm run build` 0 erros, confirmados localmente; **CI remota real executada e verde**: PR #3 (`feat/av-s03-estrutura-academica` → `main`), run 36511468808, 3/3 jobs (`AI Engine`, `Core API + Postgres`, `Frontend`) |
| AC-09 | contratos OpenAPI e documentação distinguem estrutura acadêmica de multi-tenancy | inspeção documental | **executado e confirmado (2026-09-28)** — `docs/contracts/openapi.yaml` (bloco `info.description`) agora declara explicitamente que `Organization` não é fronteira de isolamento multi-tenant e referencia a revisão de arquitetura completa |
| AC-10 | denominador da validação é o aprovado por Rafael; nenhum resultado é generalizado além dele | inspeção + integração | **executado e confirmado (2026-09-28)** — denominador reconfirmado por Rafael em `DEC-AV-007` (1 organização, 1 curso, 2 disciplinas, 2 turmas, 2 professores, 10 alunos/turma, 2 avaliações/turma) seedado integralmente em PostgreSQL 16 isolado dedicado, incluindo os 4 cenários exigidos pelo §4.2 (aluno em múltiplas turmas, professores com permissões distintas, disciplina em mais de um curso, vínculo expirado); matriz de autorização exercitada via HTTP real (`TestClient` + login JWT real): **16/16 cenários PASS**; suíte homologada de `BL-AV-2-03` confirmada sem regressão (68/68); nenhum resultado generalizado além do denominador seedado; evidência completa em `docs/governance/evidence/AV-S03/AC-10_validacao_denominador.md` |
| AC-11 | turma referencia inequivocamente curso+disciplina pela alternativa aprovada e as unicidades impedem oferta ambígua | constraint + integração SQL | **executado e confirmado (2026-09-28)** — `UniqueConstraint` em `ClassGroup(course_discipline_id, period, code)` presente no modelo e na migração; testado via `test_duplicate_class_group_identity_is_rejected` |
| AC-12 | proprietário/admin preservam acesso às avaliações legadas sem turma; vínculo de colaborador não concede edição de avaliação alheia; dados globais do aluno não são alteráveis por operação de matrícula | matriz de autorização e regressão das regras homologadas | **executado e confirmado (2026-09-28)** — coberto pela suíte homologada de `BL-AV-2-03` (`test_legacy_assessment_remains_accessible_to_owner_and_admin`, `test_collaborator_cannot_create_enrollment`, achado A corrigido) |

**Observação operacional registrada nesta rodada (não bloqueante, não reabre `BL-AV-2-03`):** a
matriz de autorização aprovada (seção 5, linha "Dados globais do aluno — leitura mínima") restringe
a visão do professor a alunos **já matriculados** em suas turmas ativas. Isso é o comportamento
correto e homologado, mas gera uma lacuna de fluxo na UI: um professor `RESPONSIBLE` não consegue
ver/buscar um aluno que nunca esteve em nenhuma de suas turmas para realizar a primeira matrícula
dele — validado ao vivo (`GET /v1/students` retorna `[]` para o professor nesse cenário, `[aluno]`
para o admin). Na prática, a matrícula inicial de um aluno novo depende de ação do admin. Isso é
consequência de decisão já aprovada (`DEC-AV-023`), não um defeito de `BL-AV-2-03` — registrado para
decisão de Rafael sobre o fluxo operacional (ex.: busca por identificador exato sem listagem
completa, ou matrícula inicial sempre administrativa), sem qualquer alteração de autorização nesta
rodada.

## 10. Posição da investigação de OCR e prioridade imagem > CSV

Decisões já aprovadas e que este plano não altera:
- `DEC-AV-016`: entrada por imagem permanece prioritária sobre importação CSV;
- `DEC-AV-018`: primeira versão é uma resposta de uma questão por foto (não prova inteira);
- `DEC-AV-021`: professor seleciona manualmente avaliação, questão e aluno (sem identificação automática na primeira versão).

A investigação de OCR foi definida como **antecipável** em GOV-004/Fase 2 e independe da AV-S03 em
sua etapa inicial:

**Atividades que podem ser planejadas/executadas independentemente de AV-S03 (mas não estão
autorizadas por este plano):**
1. `BL-AV-4B-01` — levantamento técnico inicial de alternativas de OCR/visão local, licenças,
   requisitos de hardware e limitações;
2. proposta de métricas, amostras e limites de aceite para Rafael decidir `DEC-AV-017`;
3. levantamento de requisitos de isolamento de recursos entre OCR e correção local (`BL-AV-4B-17`),
   sem implementar arquitetura;
4. inventário de formatos de imagem e riscos técnicos, sem upload/armazenamento real.

**Atividades OCR que NÃO podem avançar antes de decisões/dependências:**
- benchmark comparativo `BL-AV-4B-20` depende de Rafael aprovar previamente métricas/amostras/
  critérios (`DEC-AV-017`) — critérios não podem ser ajustados depois para favorecer resultado;
- decisão arquitetural `BL-AV-4B-02` depende do benchmark medido;
- implementação da entrada por imagem (AV-S06B em diante) depende da decisão de OCR (Fase 2) e da
  estrutura acadêmica/vínculos de AV-S03/AV-S04 (Fase 3).

**Posição atual:** o levantamento técnico inicial está no backlog e sequenciado em `AV-S05B`, mas
**ainda não existe documento detalhado de sprint aprovado/executado para ele**. Portanto está
planejado apenas em nível de trilha/backlog, não iniciado. Rafael pode decidir detalhá-lo em
paralelo à AV-S03 sem iniciar sua execução — isso não altera a prioridade imagem > CSV.

## 11. Validações previstas

| Item/AC | Comando/procedimento | Ambiente | Tipo |
|---|---|---|---|
| AC-01/11 | `alembic upgrade head` e downgrade em banco vazio; tentativa de downgrade com dados dependentes deve falhar antes de DDL destrutivo | PostgreSQL 16 isolado | migração/integração |
| AC-02–05/12 | pytest + HTTP real contra Postgres isolado, incluindo vínculo expirado/inativo, propriedade, legado sem turma e matrícula | Core local | automatizada/integração |
| AC-06 | Playwright/Chrome real via CDP | frontend/Core/Postgres isolados, dados fictícios | visual |
| AC-07/09 | revisão independente de código/contrato | repositório | inspeção/security review |
| AC-08 | Ruff Core/AI, pytest Core/AI, ESLint/build, GitHub Actions | local + CI | automatizada |
| AC-10 | relatório com denominador explícito | snapshot | documental |

## 12. Riscos e mitigação

| Risco | Prob./impacto | Mitigação | Dono |
|---|---|---|---|
| tratar Organização como tenant implicitamente | média/alta | seção 5 como limite contratual; revisão arquitetural independente | Hermes/revisor |
| lacuna de autorização reaparecer nas rotas novas | média/alta | matriz 4 perfis + propriedade da avaliação + vínculo ativo/vigente + testes negativos antes da UI | autor backend/revisor |
| turma ficar ligada a disciplina sem curso inequívoco | média/alta | turma referencia associação curricular quando N:N; constraint da alternativa aprovada | autor modelo/revisor |
| colaborador editar avaliação alheia ou vínculo expirado continuar válido | média/alta | propriedade separada do vínculo; verificação de estado/vigência em toda autorização | autor backend/revisor |
| professor alterar dados globais compartilhados do aluno por rota de matrícula | média/alta | separar `Student` de `Enrollment`; edição global administrativa | autor backend/revisor |
| downgrade remover dados acadêmicos dependentes | baixa/alta | guard pré-DDL aborta com diagnóstico; reversão destrutiva exige plano/autorização separados | autor migração/revisor |
| migração alterar dados existentes | baixa/alta | aditiva, testada em Postgres restaurado isolado, sem aplicação operacional nesta sprint sem autorização específica | autor migração |
| DEC-AV-006/007 serem tratadas como resolvidas por suposição | média/média | seção 4: premissas rotuladas, decisão objetiva de Rafael antes do DoR | Hermes |
| escopo crescer para AV-S04/OCR/CSV | média/média | fora de escopo explícito; ajuste relevante volta a Rafael | consolidador |
| dados reais de alunos entrarem na validação | baixa/alta | apenas fixtures/dados fictícios; inspeção de evidências antes de versionar | todos |

## 13. Estimativa

Método: complexidade qualitativa por item e integrações, sem velocidade histórica confiável sob
esta governança. Tamanho proposto: **M/G** — modelo/migração moderados, mas autorização cross-resource
e UI+evidência elevam o risco. A estimativa não é compromisso de prazo.

## 14. Decisões objetivas solicitadas a Rafael

Para aprovar AV-S03, Rafael decide:

1. **Ambiente (premissa DEC-AV-006):** aceitar, apenas para AV-S03, ambiente local + PostgreSQL
   isolado + dados fictícios + CI remota como alvo de validação; ou escolher ambiente compartilhado/
   piloto. Esta decisão restrita NÃO resolve DEC-AV-006 geral salvo declaração explícita.
2. **Dimensionamento (premissa DEC-AV-007):** aceitar o denominador proposto (1 organização,
   1 curso, 2 disciplinas, 2 turmas, 2 professores, 10 alunos/turma, 2 avaliações) apenas para
   testes de AV-S03; ajustar os números; ou resolver DEC-AV-007 geral. A premissa restrita não
   vira decisão canônica automaticamente.
3. **Cardinalidade aluno↔turma:**
   - alternativa A: N:N com `Enrollment`, permitindo histórico, status e datas;
   - alternativa B: 1:N nesta versão, mais simples, mas impede representar o mesmo aluno em turmas/
     disciplinas diferentes sem duplicar identidade.
   - **Recomendação técnica:** A, porque também permite separar identidade global de matrícula sem
     duplicar o aluno.
4. **Curso↔Disciplina e ligação da turma:**
   - alternativa A: N:N com associação curricular (`CourseDiscipline`); `ClassGroup` referencia
     `course_discipline_id`;
   - alternativa B: `Course 1:N Discipline`; `ClassGroup` referencia `discipline_id`.
   - **Recomendação técnica:** A, porque uma disciplina curricular pode compor mais de um curso sem
     duplicar sua identidade; a turma fica inequivocamente ligada ao par curso–disciplina.
5. **Identidade de turma/oferta:**
   - com a alternativa 4A: incluir `period`/ano-semestre e código interno, únicos por
     `(course_discipline_id, period, code)`;
   - com a alternativa 4B: usar `(discipline_id, period, code)`;
   - alternativa de adiamento: omitir período nesta sprint, aceitando risco de colisão histórica.
   - **Recomendação técnica:** incluir período desde AV-S03 e usar a unicidade correspondente à
     alternativa escolhida em 4.
6. **Vínculo professor↔turma, papel e vigência:**
   - alternativa A: vínculo simples ativo/inativo, sem papel nem vigência;
   - alternativa B: entidade explícita com `role` (`responsible`/`collaborator`), `active`,
     `starts_at`, `ends_at`; responsável administra matrículas/vínculos permitidos, mas nenhum papel
     edita avaliação de outro proprietário por implicação;
   - alternativa C: como B, mas responsável também pode editar avaliações de colaboradores.
   - **Recomendação técnica:** B. É auditável e preserva propriedade; C amplia poder e só deve ser
     escolhida por decisão explícita.
   - em qualquer alternativa com vigência, vínculo inativo, futuro ou expirado não autoriza novas
     operações. Para avaliação com turma após expiração, escolher: (i) bloqueio total ao professor,
     mantendo admin; ou (ii) leitura histórica somente das avaliações próprias, sem edição.
     **Recomendação técnica:** (ii), por continuidade/auditoria, sem preservar poder de alteração.
7. **Dados globais do aluno versus matrícula:**
   - alternativa A: apenas admin cria/edita identidade global de `Student`; professor com poder na
     turma gere apenas `Enrollment` (matricular, alterar status/datas, encerrar);
   - alternativa B: professor propõe alteração global, sujeita a aprovação administrativa/auditoria;
   - alternativa C: professor edita diretamente dados globais de alunos matriculados em sua turma.
   - **Recomendação técnica:** A na primeira versão. C é desaconselhada porque o aluno pode estar em
     várias turmas e a alteração afetaria contextos compartilhados.
8. **Unicidades naturais:** aprovar códigos internos únicos no escopo pai (`Course.code` por
   organização; associação curricular única por `(course_id, discipline_id)`; `Student.external_id`
   por organização; turma conforme decisão 5), sem assumir CPF/e-mail real. Ajustar se outro
   identificador for preferido.
9. **Avaliações legadas sem turma:** manter `assessment.class_group_id` nullable nesta sprint e
   preservar acesso do proprietário já autorizado e do admin. Avaliações novas podem: (A) exigir
   turma imediatamente após a migração; ou (B) exigir turma após data de corte/configuração explícita.
   Backfill das legadas é item separado, nunca dedução automática. **Recomendação técnica:** B se o
   rollout precisar compatibilidade; A somente se todos os criadores atuais puderem migrar de uma vez.
10. **Política de downgrade:**
    - alternativa A: downgrade permitido apenas quando as tabelas/colunas novas não têm dados
      dependentes; caso contrário, guard pré-DDL aborta com diagnóstico e mantém schema/dados;
    - alternativa B: antes do downgrade, exportar/arquivar dependências por procedimento separado,
      revisado e autorizado, e só então repetir o downgrade;
    - alternativa C: `downgrade` destrutivo automático com cascade.
    - **Recomendação técnica:** A como comportamento padrão; B como operação excepcional separada;
      C é rejeitada tecnicamente por risco de perda silenciosa, mas a decisão final é de Rafael.
11. **Entidade Organização:** confirmar que em AV-S03 ela é apenas estrutura acadêmica, sem
    multi-tenancy. Se isolamento cross-organização for requisito agora, abrir decisão/backlog
    próprios antes da implementação (mudança relevante de escopo).
12. **Matriz de autorização:** aprovar ou ajustar a seção 5.1, incluindo propriedade de avaliação,
    poderes de responsável/colaborador, vigência, acesso legado e separação `Student`/`Enrollment`.
13. **Itens da sprint:** aprovar `BL-AV-2-01` a `BL-AV-2-05` no escopo acima, ou ajustar/remover algum.
14. **OCR paralelo:** autorizar apenas o detalhamento documental do levantamento técnico
    `BL-AV-4B-01`/`AV-S05B` em paralelo (sem execução), ou manter tudo após AV-S03. Independentemente
    disso, entrada por imagem permanece prioritária sobre CSV.

### 14.1 Decisões aprovadas para esta sprint — DEC-AV-023

Em 2026-09-24, Rafael aprovou as recomendações acima **somente para AV-S03**:

- ambiente local, PostgreSQL isolado, dados fictícios, revisão cruzada e validação visual;
- cenário mínimo proposto, ampliado obrigatoriamente com aluno em mais de uma turma, disciplina em
  mais de um curso e vínculo de professor expirado;
- aluno↔turma N:N por `Enrollment`;
- curso↔disciplina N:N por `CourseDiscipline`; `ClassGroup` referencia essa associação;
- identidade da turma por `(course_discipline_id, period, code)`;
- vínculo professor↔turma como entidade com `role` (`responsible`/`collaborator`), `active`,
  `starts_at` e `ends_at`; responsável pode gerir matrículas/vínculos permitidos, mas ninguém edita
  avaliação de outro proprietário por implicação;
- vínculo inativo, futuro ou expirado não concede novas operações; após expiração, professor mantém
  somente leitura histórica das próprias avaliações, sem edição;
- apenas admin cria/edita a identidade global de `Student`; professor responsável gere
  `Enrollment` sem alterar os dados globais do aluno;
- unicidades naturais no escopo pai conforme a recomendação da decisão 8;
- avaliações legadas mantêm `class_group_id` nulo e preservam acesso/histórico do proprietário e do
  admin; novas avaliações passam a exigir turma **quando o módulo acadêmico for ativado**;
- downgrade só ocorre sem dados dependentes; caso contrário, guard pré-DDL aborta sem alterar
  schema/dados. Exportação/arquivamento é operação excepcional separada;
- `Organization` é estrutura acadêmica, não fronteira de tenant;
- matriz de autorização da seção 5.1 aprovada com essas regras;
- `BL-AV-2-01` a `BL-AV-2-05` autorizados para execução local;
- `BL-AV-4B-01` autorizado apenas para detalhamento documental, sem benchmark ou OCR.

`DEC-AV-006` e `DEC-AV-007` permanecem pendentes para a trilha geral. A aprovação desta seção não
autoriza CI remota, stage, commit, push, merge, migração em `avalia_dev`, deploy ou baseline.

Antes de qualquer implementação, o contrato OpenAPI e a matriz acima devem estar finalizados e
revisados. A execução registra autoria real de Codex/Antigravity/Hermes; Claude Code não será
contabilizado sem participação efetiva e, nesta execução, não será tentado por indisponibilidade já
informada.

## 15. Definition of Done proposta

- [ ] decisões da seção 14 registradas sem inferência;
- [ ] critérios AC-01 a AC-12 avaliados com denominador explícito;
- [ ] migração testada em PostgreSQL isolado, incluindo bloqueio seguro de downgrade com dados dependentes, e não aplicada a ambiente operacional sem autorização;
- [ ] matriz de autorização (vínculo ativo/inativo/expirado, propriedade, legado sem turma, admin e não autenticado) verde;
- [ ] identidade global de aluno e matrícula comprovadamente separadas;
- [ ] nenhuma alegação de multi-tenancy sem requisito aprovado;
- [ ] dados fictícios apenas;
- [ ] implementação/revisão por agentes distintos;
- [ ] CI remota verde no HEAD exato;
- [ ] snapshot/dashboard/débitos/decisões atualizados;
- [ ] homologação de Rafael registrada somente se ocorrer.

## 16. Critérios de encerramento

AV-S03 só pode ser concluída se a estrutura acadêmica mínima estiver implementada, a turma estiver
ligada inequivocamente ao curso+disciplina segundo a alternativa aprovada, autorização por vínculo
ativo e propriedade estiver comprovada negativa e positivamente, acesso legado estiver preservado,
migração e bloqueio de downgrade destrutivo estiverem validados em Postgres isolado, UI mínima
validada em navegador real, CI remota verde e nenhuma ampliação implícita para multi-tenant/OCR/CSV.

**Critérios críticos:** AC-01 (migração/downgrade seguro), AC-02 (caminho positivo do professor com
vínculo ativo), AC-03 (bloqueio sem vínculo ativo), AC-04 (admin), AC-05 (não autenticado/retorno),
AC-06 (UI mínima integrada ao objetivo funcional), AC-07 (sem alegação multi-tenant), AC-08 (CI),
AC-11 (ligação curso–disciplina inequívoca) e AC-12 (propriedade, legado e separação aluno/matrícula).
Falha de qualquer um impede conclusão automática; não pode ser aceita apenas como débito sem exceção
explícita de Rafael. AC-09/10 também precisam ser avaliados, mas uma lacuna documental não crítica
só pode levar a `concluída com débitos` se registrada e aceita explicitamente.

Integração, migração operacional e promoção de baseline exigem autorizações específicas
independentes.

## 17. Execução e review

Executada localmente em 2026-09-24 (worktree isolado, depois reconstruído após
perda do worktree original — ver `snapshot_EXEC-2026-09-28-01_pacote_revisao_av-s03.md`
§3) e revalidada em rodadas subsequentes. Revisão cruzada independente:
Antigravity CLI (3 rodadas sobre `BL-AV-2-03`, terceira **APROVADO SEM
RESSALVAS**) e Codex (confirmação de Ruff/testes). `BL-AV-2-04` corrigido após
2ª rodada de revisão do Codex. Homologação técnica de `BL-AV-2-03` em
`DEC-AV-026` (2026-09-28); homologação de `BL-AV-2-04` e da entrega funcional
completa da AV-S03 em `DEC-AV-027` (2026-09-29). AC-05 fechado com evidência
visual real em rodada adicional (`snapshot_EXEC-2026-09-29-03_ac05-reconciliacao-pr2.md`).
Integração ao `main` autorizada e executada via PR #3 (merge commit `c391865`,
CI 3/3 verde) e PR #4 (encerramento documental, merge commit `a5974b1`, CI 3/3
verde). Estado final: **12 de 12 critérios de aceite executados e confirmados**
(conforme banner do dashboard, seção 1), `DEBT-AV-012` aceito como débito
residual. Migração operacional em `avalia_dev` permanece não aplicada
(fora do escopo desta sprint).

*(Nota de reconciliação, 2026-09-30, auditoria GOV-006: esta seção e a
seção 18 abaixo estavam desatualizadas — ainda descreviam a sprint como
"não iniciada"/"apenas planejada" apesar de o frontmatter já registrar
`status: homologada_integracao_autorizada_2026-09-29_DEC-AV-027` e de a
integração já estar concluída em `main`. Corrigido nesta auditoria com base
em evidência já existente nos registros canônicos citados acima — nenhum
critério foi reavaliado nem recalculado, apenas a seção de fechamento do
próprio documento de sprint foi preenchida para refletir o que os registros
canônicos já diziam.)*

## 18. Closure gate

Fechamento formal aplicado — ver `sprint_closure_gate.md`. Critérios críticos
(AC-01 a AC-08, AC-11, AC-12) atendidos com evidência; nenhuma falha crítica
sem exceção registrada. `DEC-AV-026`/`DEC-AV-027` constituem a homologação de
Rafael para os itens funcionais (`BL-AV-2-03`, `BL-AV-2-04`) e para a entrega
completa da sprint, respectivamente. Integração a `main` autorizada e
concretizada (PR #3, PR #4). Nenhuma migração operacional, deploy ou
promoção de baseline foi incluída nesta homologação.
