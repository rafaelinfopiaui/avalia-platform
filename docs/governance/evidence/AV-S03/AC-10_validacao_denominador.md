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

## 2. Dados seedados — denominador principal (DEC-AV-007) vs. cenário adicional (§4.2)

Esta seção distingue explicitamente duas origens de dados, que não devem ser confundidas:

**(A) Denominador principal**, exatamente como reconfirmado por Rafael em `DEC-AV-007`
(2026-09-28): "1 organização, 1 curso, 2 disciplinas, 2 turmas, 2 professores, 10 alunos
matriculados por turma, 2 avaliações por turma — incluindo explicitamente os cenários de aluno em
múltiplas turmas e professores com permissões distintas". Nenhum item desta lista (A) foi
acrescentado por iniciativa própria desta execução; todos foram explicitamente aprovados.

**(B) Dado adicional, fora do denominador aprovado**, acrescentado por decisão de execução para
cobrir uma exigência textual do documento da sprint (§4.2, "disciplina em mais de um curso") que
`DEC-AV-007` não cobre literalmente (o denominador fala em "1 curso", singular). Este item (B) é
preservado como cenário à parte, isolado do restante da validação, para que a leitura da tabela
abaixo não confunda os dois conjuntos.

| Item | Origem | Quantidade seedada | Observação |
|---|---|---|---|
| Organização | (A) denominador aprovado | 1 | `Instituto AC-10` |
| Curso — principal | (A) denominador aprovado | 1 | usado por todas as 2 turmas do denominador |
| Curso — adicional | **(B) fora do denominador**, acrescentado só para o cenário de §4.2 | 1 | não participa de nenhuma turma, matrícula ou avaliação; existe apenas como segundo ponto de associação da disciplina compartilhada (ver linha seguinte) |
| Disciplina | (A) denominador aprovado | 2 | uma delas (`Estruturas de Dados`) recebe uma associação adicional (B) ao curso adicional, apenas para o teste de §4.2 — sua associação ao curso principal (A) é a que participa do restante da validação |
| Turma | (A) denominador aprovado | 2 | `T01` e `T02`, ambas vinculadas ao curso **principal** (A); o curso adicional (B) não tem turmas |
| Professor | (A) denominador aprovado | 2 | `prof_a` e `prof_b`, com permissões DISTINTAS (ver seção 3) |
| Alunos matriculados por turma | (A) denominador aprovado | 10 por turma (20 matrículas, 19 alunos únicos) | 1 aluno matriculado em AMBAS as turmas, cobrindo "aluno em mais de uma turma" |
| Avaliações por turma | (A) denominador aprovado | 2 por turma (4 no total) | 2 na turma 1 (por `prof_a`), 2 na turma 2 (por `admin`, já que `prof_b` tem vínculo expirado lá) |

Consequência prática: os cenários 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 da seção 4
abaixo exercitam exclusivamente o denominador principal (A) — 1 organização, 1 curso, 2 turmas
sobre esse curso, 2 professores, 20 matrículas, 4 avaliações. Apenas o cenário 3 ("disciplina em
mais de um curso") exercita o dado adicional (B); é o único ponto da validação que depende do
curso extra, e seu resultado é reportado separadamente na seção 3 abaixo para não ser confundido
com o restante da cobertura do denominador aprovado.

## 3. Cenários adicionais exigidos pelo texto vigente da sprint (§4.2) e pela aprovação de 2026-09-28

| Cenário exigido | Origem | Como foi coberto |
|---|---|---|
| aluno em mais de uma turma | (A) denominador aprovado (`DEC-AV-007`) | 1 aluno (`Aluno Compartilhado Multi-Turma`) matriculado ACTIVE nas turmas T01 e T02 |
| professores com permissões distintas | (A) denominador aprovado (`DEC-AV-007`) | `prof_a` = RESPONSIBLE na T01, sem vínculo na T02; `prof_b` = COLLABORATOR na T01, RESPONSIBLE **expirado** na T02 |
| disciplina em mais de um curso | **(B) fora do denominador aprovado**, exigência textual de §4.2 não coberta literalmente por `DEC-AV-007` | disciplina `Estruturas de Dados` associada via `CourseDiscipline` tanto ao curso principal (A) quanto ao curso adicional (B); nenhuma turma, matrícula ou avaliação usa o curso adicional |
| vínculo expirado | (A) denominador aprovado (`DEC-AV-007`) | vínculo de `prof_b` na T02 com `ends_at` no passado (60 dias atrás a -1 dia) |

## 4. Resultado real da execução (16/16 cenários, evidência de código de status HTTP real)

| # | Cenário | Resultado | Evidência |
|---|---|---|---|
| 1 | login real (admin, prof_a, prof_b) | PASS | 3x `POST /v1/auth/login` → 200, JWT emitido |
| 2 | estrutura: 1 org, 2 cursos, 2 disciplinas | PASS | IDs reais retornados por `POST /v1/organizations`, `/v1/courses`, `/v1/disciplines` |
| 3 | disciplina em mais de um curso **(B, fora do denominador aprovado)** | PASS | 2 `CourseDiscipline` criadas para a mesma disciplina em cursos diferentes |
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

**AC-10: ATENDIDO.** O denominador principal aprovado por Rafael em `DEC-AV-007` (2026-09-28) foi
seedado integralmente em ambiente isolado (PostgreSQL dedicado, fora de `avalia_dev`) — 1
organização, 1 curso, 2 disciplinas, 2 turmas, 2 professores, 10 alunos/turma, 2 avaliações/turma
— incluindo os cenários de aluno multi-turma, professores com permissões distintas e vínculo
expirado, todos explicitamente parte desse denominador. Adicionalmente, um curso extra (fora do
denominador aprovado) foi seedado apenas para cobrir a exigência textual de §4.2 ("disciplina em
mais de um curso"), que `DEC-AV-007` não cobre literalmente por falar em "1 curso" — esse dado
adicional está isolado e identificado na seção 2 e não contamina a leitura do denominador principal.
A matriz de autorização foi exercitada via HTTP real, com 16/16 cenários passando (15 sobre o
denominador principal, 1 sobre o dado adicional de §4.2), e a suíte homologada de `BL-AV-2-03`
permaneceu 68/68 sem regressão. Nenhum resultado desta validação é generalizado além do
denominador aprovado nem do dado adicional isolado (não há alegação de capacidade, desempenho ou
comportamento sob volume diferente do seedado).

## 8. Limpeza do ambiente

A instância PostgreSQL isolada usada nesta validação foi parada e seus arquivos de dados removidos
ao final da execução (`pg_ctl stop` + remoção do diretório de dados temporário), preservando
apenas este relatório e os scripts de seed/cenários como evidência reexecutável.
