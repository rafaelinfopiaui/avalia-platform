# Revisão de arquitetura AC-07 / AC-09 — AV-S03

Data: 2026-09-28
Escopo: implementação reconstruída em `local/av-s03-recuperacao`, base `66c95201daf893fa7b2852e0d94b20314f8d8f34`
Revisor factual: Hermes (inspeção direta de código e contrato)

## 1. Pergunta avaliada

Confirmar que `Organization` foi implementada como entidade de domínio da estrutura acadêmica, não como fronteira implícita de isolamento multi-tenant; e que o contrato/documentação tornam essa distinção explícita.

## 2. Evidência do modelo

- `User` (`core/app/models.py:62-69`) não possui `organization_id` nem qualquer atributo de tenant.
- `Organization` é entidade pai de `Course`, `Discipline` e `Student` por FK de domínio.
- `ClassGroup` referencia `CourseDiscipline`, que referencia `Course` + `Discipline`.
- `ProfessorClassLink` referencia diretamente `User` + `ClassGroup` e contém papel/estado/vigência.
- Não existe tabela de membership de usuário→organização nem claim de organização no JWT.

Conclusão: o modelo não representa isolamento multi-tenant.

## 3. Evidência das queries de autorização

A busca estática e a leitura de `core/app/routers/academic.py` encontraram usos de `organization_id` nas queries apenas em:

1. `_organization_ids_for_user` (`academic.py:217-223`): deriva organizações a partir dos vínculos ativos reais do professor:
   `ProfessorClassLink` → `ClassGroup` → `CourseDiscipline` → `Course.organization_id`.
2. `_course_scope` (`academic.py:327-328`): restringe cursos às organizações derivadas por `_organization_ids_for_user`.
3. `_discipline_scope` (`academic.py:331-332`): restringe disciplinas às mesmas organizações derivadas.

Não existe query que faça `resource.organization_id == user.organization_id`, porque `User` não possui `organization_id`. Não existe middleware, dependency ou policy global que aplique filtro de organização a todas as queries. O escopo nasce do vínculo professor↔turma, conforme a matriz aprovada, e a organização é apenas o ancestral estrutural necessário para navegar Curso/Disciplina/Turma.

`Student` não usa organização como fronteira de autorização: `_student_scope` filtra por `Enrollment.class_group_id` dentro das turmas ativas do professor, conforme a decisão que separa identidade global do aluno de matrícula.

Administradores ignoram os filtros de escopo de professor e mantêm acesso global, como demonstrado pelos testes de `BL-AV-2-03` homologados.

## 4. Risco de ambiguidade documental identificado e corrigido

Antes desta revisão, `docs/contracts/openapi.yaml` listava os endpoints acadêmicos, mas não dizia explicitamente que `Organization` não é tenant. Isso deixava margem para interpretação indevida futura.

Correção documental aplicada em 2026-09-28: a descrição do contrato agora declara explicitamente:

- `Organization` é entidade de domínio acadêmico;
- não é fronteira de isolamento multi-tenant;
- não há requisito aprovado de multi-tenancy;
- escopo de professor é derivado de vínculo ativo de turma;
- admin mantém acesso global.

Nenhuma alteração de código foi necessária para AC-07/AC-09.

## 5. Veredito

- AC-07: ATENDIDO. A implementação não trata Organização como tenant, e nenhuma query é globalizada implicitamente por `organization_id` sem vínculo real de turma.
- AC-09: ATENDIDO após a correção documental em `docs/contracts/openapi.yaml`; contrato e este registro distinguem estrutura acadêmica de multi-tenancy.

## 6. Limite desta conclusão

Esta revisão prova o comportamento do código e contrato atuais da AV-S03. Não aprova uma arquitetura multi-tenant futura e não deve ser reinterpretada como autorização para introduzir isolamento por organização sem nova decisão/ADR.
