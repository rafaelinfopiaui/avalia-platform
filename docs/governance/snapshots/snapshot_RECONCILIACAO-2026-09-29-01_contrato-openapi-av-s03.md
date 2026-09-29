---
id: "RECONCILIACAO-2026-09-29-01"
tipo: reconciliacao_documental
sprint: "AV-S03"
gerado_em: "2026-09-29T00:00:00-03:00"
autor_execucao: "Hermes"
decisao_de: "Rafael"
---

# Reconciliação do contrato OpenAPI — AV-S03

## Contexto

Durante a execução da AV-S03, foi identificado que `docs/contracts/openapi.yaml`
existia em dois estados divergentes e incompatíveis:

1. **No checkout principal do repositório** (`/avalia-plataform`, working tree,
   nunca commitado em nenhuma branch): uma **proposta de design** elaborada
   durante o planejamento da sprint (~2026-09-24), antes de qualquer código de
   BL-AV-2-01/02/03 existir. Paths, nomes de recursos e schemas divergem da
   implementação real (ex.: propunha `/class-groups/{id}/professors` e
   `/class-groups/{id}/enrollments` como sub-rotas; a implementação real criou
   `/professor-class-links` e `/enrollments` como recursos de primeira classe
   com seus próprios CRUDs).

2. **Na branch `feat/av-s03-estrutura-academica`** (commitado desde `cb8a96b`,
   PR #3): uma versão do contrato conferida rota-a-rota e schema-a-schema
   contra o código efetivamente implementado em
   `core/app/routers/academic.py`.

## Verificação realizada nesta reconciliação (2026-09-29)

Foi extraído o schema OpenAPI real gerado pela própria aplicação FastAPI
(`app.openapi()`, executado em ambiente isolado) e comparado rota a rota
contra `docs/contracts/openapi.yaml` da branch `feat/av-s03-estrutura-academica`:

| Recurso | Rotas reais (FastAPI) | Presente no contrato da branch |
|---|---|---|
| organizations | GET/POST /v1/organizations, GET/PATCH/DELETE /v1/organizations/{id} | sim |
| courses | GET/POST /v1/courses, GET/PATCH/DELETE /v1/courses/{id} | sim |
| disciplines | GET/POST /v1/disciplines, GET/PATCH/DELETE /v1/disciplines/{id} | sim |
| course-disciplines | GET/POST /v1/course-disciplines, GET/PATCH/DELETE /v1/course-disciplines/{id} | sim |
| class-groups | GET/POST /v1/class-groups, GET/PATCH/DELETE /v1/class-groups/{id} | sim |
| students | GET/POST /v1/students, GET/PATCH/DELETE /v1/students/{id} | sim |
| enrollments | GET/POST /v1/enrollments, GET/PATCH/DELETE /v1/enrollments/{id} | sim |
| professor-class-links | GET/POST /v1/professor-class-links, GET/PATCH/DELETE /v1/professor-class-links/{id} | sim |
| assessments/{id}/class-group | POST | sim |

Nenhuma divergência funcional encontrada entre a implementação e o contrato
já commitado na branch. As 9 entradas de recurso acadêmicas (8 recursos com
CRUD completo + o endpoint de vínculo avaliação↔turma) batem 1:1 com o
contrato, cada uma com todos os métodos HTTP correspondentes.

A proposta de design antiga do checkout principal **não corresponde** a
nenhuma dessas 9 rotas na sua forma de sub-recurso (`/class-groups/{id}/
professors`, `/class-groups/{id}/enrollments`) — o design evoluiu durante a
implementação para recursos de primeira classe, decisão já registrada em
`DEC-AV-023`/`DEC-AV-024`/`DEC-AV-025` do canônico de decisões.

## Precisão terminológica (correção desta reconciliação)

Em registros anteriores desta sprint (commit `a5d0a2c` da branch, e no corpo
do PR #3 antes desta reconciliação), o contrato commitado foi descrito como
"versão REAL, testada e homologada". Essa formulação confundia três estados
distintos que devem ser mantidos separados:

- **Revisão técnica**: conferência rota-a-rota e schema-a-schema contra o
  código, como a realizada nesta reconciliação — não é teste nem homologação.
- **Testes**: execução automatizada da suíte (Core 68/68 testes, Ruff,
  ESLint, build) — valida comportamento do código, não valida o arquivo de
  documentação do contrato em si.
- **Homologação**: decisão formal de Rafael sobre a funcionalidade
  (`DEC-AV-026`, homologação de `BL-AV-2-03`). Essa homologação recaiu sobre
  o comportamento da aplicação, não especificamente sobre o texto do arquivo
  `docs/contracts/openapi.yaml`.

Correção: `docs/contracts/openapi.yaml` da branch é o contrato **verificado
por conferência técnica direta contra o código implementado e testado**;
não é, em si, um artefato que tenha sido objeto de homologação nominal
separada. Este documento corrige a formulação onde ela apareceu.

## Decisão adotada (autorizada por Rafael em 2026-09-29)

1. `docs/contracts/openapi.yaml` da branch `feat/av-s03-estrutura-academica`
   é adotado como **contrato vigente** e seguirá para `main` via merge do
   PR #3.
2. A proposta de design antiga foi preservada como histórico identificado em
   `docs/contracts/historico/openapi_proposta_design_av-s03_superada.yaml`
   (commitada nesta branch), com cabeçalho explícito marcando-a como
   superada e não-editável.
3. A cópia de trabalho não commitada da proposta antiga no checkout
   principal (`/avalia-plataform`, working tree) foi descartada
   (`git checkout -- docs/contracts/openapi.yaml`) após a preservação acima,
   eliminando o risco de commit acidental futuro daquela versão.
4. **Salvaguarda contra reintrodução**: o PR #2 (`docs/av-s02-encerramento-
   planos-operacionais`) foi auditado e **não modifica**
   `docs/contracts/openapi.yaml` — confirmado via
   `gh pr view 2 --json files`. Não há, portanto, vetor de reintrodução do
   contrato antigo por aquele PR. Qualquer PR futuro que toque
   `docs/contracts/openapi.yaml` deve ser conferido contra o schema real da
   aplicação (`app.openapi()`) antes do merge, não contra versões de design
   anteriores à implementação.

## Referências

- `docs/contracts/openapi.yaml` (contrato vigente, esta branch/PR #3)
- `docs/contracts/historico/openapi_proposta_design_av-s03_superada.yaml`
  (histórico superado)
- `docs/governance/registers/decisions.md`: DEC-AV-023, DEC-AV-024,
  DEC-AV-025, DEC-AV-026
- PR #3: https://github.com/rafaelinfopiaui/avalia-platform/pull/3

## Revisão independente desta reconciliação (Codex, 2026-09-29)

Revisão técnica independente (Codex, execução isolada, sem acesso ao histórico
desta conversa) auditou: (1) as rotas do contrato vigente contra o schema real
gerado pela aplicação; (2) a preservação e o cabeçalho do histórico superado;
(3) a coerência interna deste documento de reconciliação; (4) a clareza da
separação denominador (A) vs. dado adicional (B) na evidência de AC-10.

Veredito: **APROVADO**. Confirmou as 8 rotas de recurso com CRUD completo mais
o endpoint de vínculo avaliação↔turma; confirmou o cabeçalho do histórico como
claro; considerou a reconciliação consistente na adoção do contrato vigente,
preservação do histórico e distinção revisão técnica/testes/homologação; e
considerou a separação A/B da evidência AC-10 clara e sem contradição no
veredito final. Observação menor incorporada: a formulação "9 rotas
acadêmicas" foi ajustada para "9 entradas de recurso" para não sugerir 9
operações HTTP distintas onde há, na verdade, múltiplos métodos por entrada.
