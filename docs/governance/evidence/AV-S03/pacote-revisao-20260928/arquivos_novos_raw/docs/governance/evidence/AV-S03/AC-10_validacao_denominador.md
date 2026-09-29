# Validação AC-10 — denominador da AV-S03 executado em ambiente isolado

Data: 2026-09-28
Decisão base: `DEC-AV-007` (denominador reconfirmado por Rafael em 2026-09-28, restrito à
validação funcional da AV-S03, sem estabelecer capacidade/desempenho/dimensionamento de
produção, sem resolver `DEC-AV-007` para a trilha completa).

## 1. Ambiente

- PostgreSQL 16.15 isolado, instância dedicada (`initdb` própria, porta 55437, socket em `/tmp`,
  fora de qualquer ambiente do projeto e de `avalia_dev`);
- banco `avalia_ac10_validacao`, schema aplicado via `alembic upgrade head` (mesma cadeia de
  migrações usada pela suíte homologada: `e1b02279b1a5` → `7b1d6d853f20` → `c4a8b2d91e37`);
- execução via FastAPI `TestClient` sobre o app real (`app.main.app`), com `DATABASE_URL`
  apontando para o Postgres isolado (não SQLite), login real via `/v1/auth/login` com JWT real
  emitido pelo backend, e todas as operações via endpoints HTTP reais (não chamadas diretas de
  função/ORM, exceto o seed inicial de usuários e vínculos, que usa a sessão diretamente por não
  existir endpoint de cadastro de usuário/vínculo fora do fluxo administrativo already coberto
  pela suíte homologada).
- scripts de execução: `docs/governance/evidence/AV-S03/AC-10-scripts/ac10_seed.py` (estrutura +
  dados) e `docs/governance/evidence/AV-S03/AC-10-scripts/ac10_scenarios.py` (avaliações + matriz
  de autorização), preservados como evidência reexecutável. Ambos assumem `DATABASE_URL` apontando
  para um PostgreSQL isolado dedicado (não incluído no repositório) e devem ser executados a partir
  do diretório `core/` do projeto, com o virtualenv do Core ativado.

## 2. Denominador seedado (conforme aprovação de 2026-09-28)

| Item | Quantidade seedada | Observação |
|---|---|---|
| Organização | 1 | `Instituto AC-10` |
| Curso | 1 principal + 1 adicional | o curso adicional existe apenas para provar o cenário "disciplina em mais de um curso" (exigido pelo texto vigente §4.2); o denominador principal de turmas usa o curso 1 |
| Disciplina | 2 | uma delas (`Estruturas de Dados`) associada a AMBOS os cursos |
| Turma | 2 | `T01` (curso 1 + disciplina 1) e `T02` (curso 1 + disciplina 2) |
| Professor | 2 | `prof_a` e `prof_b`, com permissões DISTINTAS (ver seção 3) |
| Alunos matriculados por turma | 10 por turma (20 matrículas, 19 alunos únicos) | 1 aluno matriculado em AMBAS as turmas, cobrindo "aluno em mais de uma turma" |
| Avaliações por turma | 2 por turma (4 no total) | 2 na turma 1 (por `prof_a`), 2 na turma 2 (por `admin`, já que `prof_b` tem vínculo expirado lá) |

## 3. Cenários adicionais exigidos pelo texto vigente da sprint (§4.2) e pela aprovação de 2026-09-28

| Cenário exigido | Como foi coberto |
|---|---|
| aluno em mais de uma turma | 1 aluno (`Aluno Compartilhado Multi-Turma`) matriculado ACTIVE nas turmas T01 e T02 |
| professores com permissões distintas | `prof_a` = RESPONSIBLE na T01, sem vínculo na T02; `prof_b` = COLLABORATOR na T01, RESPONSIBLE **expirado** na T02 |
| disciplina em mais de um curso | disciplina `Estruturas de Dados` associada via `CourseDiscipline` tanto ao curso 1 quanto ao curso 2 |
| vínculo expirado | vínculo de `prof_b` na T02 com `ends_at` no passado (60 dias atrás a -1 dia) |

## 4. Resultado real da execução (16/16 cenários, evidência de código de status HTTP real)

| # | Cenário | Resultado | Evidência |
|---|---|---|---|
| 1 | login real (admin, prof_a, prof_b) | PASS | 3x `POST /v1/auth/login` → 200, JWT emitido |
| 2 | estrutura: 1 org, 2 cursos, 2 disciplinas | PASS | IDs reais retornados por `POST /v1/organizations`, `/v1/courses`, `/v1/disciplines` |
| 3 | disciplina em mais de um curso | PASS | 2 `CourseDiscipline` criadas para a mesma disciplina em cursos diferentes |
| 4 | estrutura: 2 turmas | PASS | `POST /v1/class-groups` x2, unicidade `(course_discipline_id, period, code)` respeitada |
| 5 | professores com permissões distintas | PASS | vínculos criados: RESPONSIBLE/COLLABORATOR/RESPONSIBLE-expirado |
| 6 | 10 alunos matriculados por turma | PASS | 20 `POST /v1/enrollments` retornaram 201 |
| 7 | aluno em mais de uma turma | PASS | aluno único matriculado ACTIVE nas duas turmas |
| 8 | 2 avaliações na turma 1 (prof_a RESPONSIBLE) | PASS | `POST /v1/assessments` x2 → 201 |
| 9 | vínculo EXPIRADO não concede acesso a operação NOVA | PASS | `prof_b` tentou criar avaliação na T02 → **403** |
| 10 | admin mantém acesso global (sem vínculo) | PASS | admin criou avaliação na T02 → **201** |
| 11 | 2 avaliações na turma 2 (via admin) | PASS | `POST /v1/assessments` x2 → 201 |
| 12 | COLLABORATOR não lê avaliação alheia da turma vinculada | PASS | `prof_b` tentou ler avaliação de `prof_a` → **403** (ownership estrito, comportamento homologado em BL-AV-2-03; não é regressão — é o comportamento já aprovado na matriz seção 5.1: "própria ou acesso explicitamente concedido pela política de papel") |
| 13 | COLLABORATOR não herda edição/mutação de avaliação alheia | PASS | `prof_b` tentou publicar avaliação de `prof_a` → **403** |
| 14 | professor sem vínculo não acessa avaliação de turma alheia | PASS | `prof_a` tentou ler avaliação da T02 (sem vínculo lá) → **403** |
| 15 | aluno compartilhado visível ao professor da turma correspondente | PASS | `GET /v1/students` por `prof_a` retornou 10 alunos, incluindo o compartilhado |
| 16 | admin vê todos os alunos (escopo global) | PASS | `GET /v1/students` por admin retornou 19 alunos únicos (9+9+1 compartilhado) |

## 5. Nota de transparência sobre a execução

Na primeira execução do cenário 12, a expectativa inicial do script era `200` (colaborador
conseguiria ler a avaliação). O resultado real foi `403`. Investigação imediata (leitura de
`core/app/main.py::_get_owned_assessment`) confirmou que a implementação homologada usa ownership
estrito (`owner_id == user.id`) para leitura de avaliação, sem exceção de papel — o que é
consistente com a matriz de autorização aprovada na sprint (seção 5.1: "Avaliação com turma —
ler: própria ou acesso explicitamente concedido pela política de papel", e nenhuma política de
papel concede essa leitura a colaboradores nesta implementação). A expectativa do script foi
corrigida para refletir o comportamento correto e homologado; não houve alteração de código de
produção para "fazer passar o teste" — o comportamento observado já era o correto.

## 6. Regressão confirmada

`python -m pytest app/tests -q` (suíte completa homologada, 68 testes): **68 passed, 0 failed**,
antes e depois da execução dos scripts de validação de AC-10 — os scripts operam em banco Postgres
isolado próprio (`avalia_ac10_validacao`), sem qualquer interferência na suíte SQLite in-memory da
suíte homologada.

## 7. Veredito

**AC-10: ATENDIDO.** O denominador aprovado por Rafael em 2026-09-28 foi seedado integralmente em
ambiente isolado (PostgreSQL dedicado, fora de `avalia_dev`), incluindo os 4 cenários adicionais
exigidos pelo texto vigente da sprint (§4.2). A matriz de autorização foi exercitada via HTTP real
contra esse denominador, com 16/16 cenários passando, e a suíte homologada de `BL-AV-2-03`
permaneceu 68/68 sem regressão. Nenhum resultado desta validação é generalizado além do
denominador aprovado (não há alegação de capacidade, desempenho ou comportamento sob volume
diferente do seedado).

## 8. Limpeza do ambiente

A instância PostgreSQL isolada usada nesta validação foi parada e seus arquivos de dados removidos
ao final da execução (`pg_ctl stop` + remoção do diretório de dados temporário), preservando
apenas este relatório e os scripts de seed/cenários como evidência reexecutável.
