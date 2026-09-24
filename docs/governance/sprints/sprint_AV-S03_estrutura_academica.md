---
id: "AV-S03"
status: planejada_aguardando_aprovacao
objetivo_aprovado_por: pendente_Rafael
consolidador: "Hermes"
baseline_entrada: "../snapshots/latest_validated_baseline.md (nenhum promovido; código AV-S01/AV-S02 integrado a main em 2026-09-24, SHA 66c95201daf893fa7b2852e0d94b20314f8d8f34, mas isso NÃO é baseline operacional promovido)"
---

# AV-S03 — Estrutura acadêmica mínima: Organização, Curso, Disciplina, Turma e Aluno

> **PLANO PARA APROVAÇÃO. NÃO AUTORIZA EXECUÇÃO.** Nenhum código, migração, dado ou interface de
> AV-S03 foi implementado nesta sessão. O objetivo deste documento é tornar as decisões e o escopo
> verificáveis antes de Rafael aprovar (ou ajustar/rejeitar) a sprint.

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
- modelos/tabelas mínimos: `Organization`, `Course`, `Discipline`, `ClassGroup` (Turma), `Student`;
- tabela de vínculo professor↔turma (muitos-para-muitos ou entidade explícita, a definir no desenho
  técnico da sprint, mas com unicidade e índices claros);
- vínculo avaliação↔turma;
- migração Alembic aditiva e reversível, testada primeiro em PostgreSQL isolado;
- endpoints Core mínimos para listar/criar/editar (sem exclusão destrutiva nesta primeira entrega):
  organizações, cursos, disciplinas, turmas, alunos e vínculos professor↔turma;
- checagem de autorização por vínculo em cada endpoint novo e no acesso a avaliações por turma;
- telas frontend mínimas de turma/aluno/vínculo da avaliação;
- testes de autorização cruzada, constraint, migração e fluxo visual com dados fictícios;
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
- cardinalidades corretas (não hardcode dos números acima); `Organization` 1:N `Course`, `Course`
  1:N `Discipline`, `Discipline` 1:N `ClassGroup`, `ClassGroup` N:N `Student` se o domínio exigir
  aluno em mais de uma turma/disciplina — confirmar no desenho; a premissa de teste não congela a
  cardinalidade de produção;
- índices mínimos nas FKs e unicidade por identificadores internos; nenhum particionamento/sharding.

Efeito nas permissões:
- a matriz de acesso exige pelo menos 2 professores/2 turmas para provar isolamento por vínculo;
- admin acessa ambas; professor A não acessa turma/avaliação do professor B;
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

A autorização por vínculo professor↔turma não resolve sozinha operações sobre entidades pai ou
administração de vínculos. Para evitar implementação divergente por endpoint, propõe-se a matriz
abaixo — sujeita à aprovação de Rafael:

| Recurso/ação | Admin | Professor vinculado | Professor não vinculado | Não autenticado |
|---|---|---|---|---|
| Organização — criar/editar | permitido | proibido (403) | proibido (403) | 401 |
| Organização — listar/ler | global | somente organizações derivadas de suas turmas (sem listar outras) | vazio/403 conforme rota | 401 |
| Curso/Disciplina — criar/editar | permitido | proibido (403) | proibido (403) | 401 |
| Curso/Disciplina — listar/ler | global | somente pais necessários às suas turmas | vazio/403 conforme rota | 401 |
| Turma — criar/editar | permitido | leitura/operação somente se vinculado; criação/edição administrativa proibida | 403 | 401 |
| Gerir vínculo professor↔turma | permitido | proibido (não pode autoatribuir-se nem remover outros) | proibido | 401 |
| Aluno — criar/editar | permitido | permitido somente no contexto de turma vinculada e segundo matrícula aprovada | 403 | 401 |
| Aluno — listar/ler | global | somente alunos matriculados em turmas vinculadas; se aluno estiver em várias turmas, exposição limitada aos dados necessários à turma acessada | 403 | 401 |
| Avaliação vinculada à turma | global | permitido somente em turma vinculada | 403 sem vazamento | 401/retorno pós-login |
| Recursos ainda sem turma | global | não visíveis/não operáveis por professor até vínculo explícito | 403 | 401 |

Cada rota nova precisa de testes positivos e negativos correspondentes. Listagens devem filtrar no
banco, não buscar globalmente e filtrar em memória. Erros 403/404 devem seguir a política já usada
pelo produto sem revelar a existência de recurso não autorizado.

**Decisão objetiva solicitada:** Rafael aprova esta matriz, ou ajusta quais operações professor
pode executar. Sem essa decisão, `BL-AV-2-03` permanece refinado, não `ready`.

## 6. Backlog e DoR

| ID | Entrega | DoR | Estado |
|---|---|---|---|
| BL-AV-2-01 | modelo acadêmico mínimo | refinado; falta decisão sobre cardinalidade aluno↔turma e premissas DEC-AV-006/007 | planejado |
| BL-AV-2-02 | migração Alembic aditiva | refinado; depende do modelo aprovado em BL-AV-2-01; teste Postgres isolado obrigatório | planejado |
| BL-AV-2-03 | autorização professor↔turma | refinado; padrão AV-S01 é dependência satisfeita; matriz de perfis definida | planejado |
| BL-AV-2-04 | telas mínimas de turma/aluno/vínculo | refinado; depende do contrato dos endpoints e do ambiente-alvo aceito | planejado |
| BL-AV-2-05 | validação do marco | refinado; depende das premissas de dados fictícios/denominador aprovadas | planejado |

Nenhum item está `ready` para execução até Rafael decidir as perguntas da seção 14. A existência
deste plano não inicia AV-S03.

## 7. Mapa de impacto inicial

| Item | Criar | Alterar | Não tocar |
|---|---|---|---|
| BL-AV-2-01/02 | `core/alembic/versions/<nova_revision>_estrutura_academica.py`; testes `core/app/tests/test_academic_structure.py` | `core/app/models.py`, `core/app/schemas.py`; fixtures isoladas em `core/app/tests/conftest.py` somente se necessário | migração AV-S02 `7b1d6d853f20`, dados existentes em `avalia_dev`, seed de demonstração sem decisão explícita |
| BL-AV-2-03 | testes `core/app/tests/test_academic_authorization.py` | `core/app/main.py` ou novo `core/app/routers/academic.py` (escolher um padrão após inspeção); `deps.py` apenas se necessário | sem transformar autorização em multi-tenant implícito; sem refatorar auth fora das rotas acadêmicas |
| BL-AV-2-04 | páginas/componentes acadêmicos sob `frontend/src/pages/` e testes aplicáveis | `frontend/src/App.tsx`, `services/api.ts`, `types.ts` | fluxo de revisão humana já homologado; nada de OCR/upload |
| BL-AV-2-05 | `docs/governance/evidence/AV-S03/`, snapshot e fechamento | sprint, dashboard, backlog/débitos/decisões; READMEs/contrato conforme resultado | baseline validado sem autorização de promoção |
| Contrato | — | `docs/contracts/openapi.yaml`, `core/README.md`, `frontend/README.md` se existir/aplicável | PRD/ADR sem decisão explícita |

Mudança fora deste mapa exige registro prévio em Ajustes de Percurso; ampliação relevante depende
de Rafael.

## 8. Delegação proposta (apenas após aprovação da sprint)

| Item | Executor proposto | Revisor distinto | Limites |
|---|---|---|---|
| BL-AV-2-01/02 | Codex | Claude Code ou Antigravity CLI | modelo+migração; banco isolado; não aplicar em `avalia_dev` sem autorização específica |
| BL-AV-2-03 | Antigravity CLI ou Codex (distinto do autor do modelo) | Claude Code | autorização/matriz; não refatorar auth fora do necessário |
| BL-AV-2-04 | Antigravity CLI | Codex | UI mínima; dados fictícios; sem design system/refatoração ampla |
| BL-AV-2-05 | Hermes (evidência) | agente que não implementou o fluxo visual | navegador real, sem segredos/dados reais |
| Consolidação | Hermes | — | sprint/snapshot/dashboard, distinção planejado/implementado/validado/homologado |

Disponibilidade dos agentes deve ser reconfirmada no início da execução; fallback/autoria real
devem ser registrados sem inferência.

## 9. Critérios de aceite propostos

| ID | Critério | Método | Estado |
|---|---|---|---|
| AC-01 | migração cria estrutura acadêmica em PostgreSQL isolado sem perda de dados preexistentes e faz downgrade limpo | migração + inspeção SQL | não executado |
| AC-02 | professor vinculado à turma consegue listar/operar turma, alunos e avaliações vinculadas | integração HTTP real | não executado |
| AC-03 | professor não vinculado recebe 403 nas rotas da turma/aluno/avaliação; nenhum dado é vazado no corpo | matriz de autorização, 2 professores/2 turmas | não executado |
| AC-04 | admin mantém acesso global conforme padrão existente | integração HTTP real | não executado |
| AC-05 | usuário não autenticado recebe 401 e retorna ao destino após login quando aplicável | integração + visual | não executado |
| AC-06 | UI cria/visualiza turma e aluno fictício e vincula avaliação à turma sem expor dados reais | navegador real | não executado |
| AC-07 | Organização é tratada como entidade de domínio, sem alegação de isolamento multi-tenant; nenhuma query é implicitamente globalizada por `organization_id` sem requisito aprovado | revisão de segurança/arquitetura | não executado |
| AC-08 | suíte Core, Ruff, ESLint, frontend build e CI remota permanecem verdes | automatizada/local+remota | não executado |
| AC-09 | contratos OpenAPI e documentação distinguem estrutura acadêmica de multi-tenancy | inspeção documental | não executado |
| AC-10 | denominador da validação (professores/turmas/alunos/avaliações) é o aprovado por Rafael; nenhum resultado é generalizado além dele | inspeção + integração | não executado |

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
| AC-01 | `alembic upgrade head`/`downgrade` em dump restaurado isolado | PostgreSQL 16 isolado | migração/integração |
| AC-02–05 | pytest + HTTP real contra Postgres isolado | Core local | automatizada/integração |
| AC-06 | Playwright/Chrome real via CDP | frontend/Core/Postgres isolados, dados fictícios | visual |
| AC-07/09 | revisão independente de código/contrato | repositório | inspeção/security review |
| AC-08 | Ruff Core/AI, pytest Core/AI, ESLint/build, GitHub Actions | local + CI | automatizada |
| AC-10 | relatório com denominador explícito | snapshot | documental |

## 12. Riscos e mitigação

| Risco | Prob./impacto | Mitigação | Dono |
|---|---|---|---|
| tratar Organização como tenant implicitamente | média/alta | seção 5 como limite contratual; revisão arquitetural independente | Hermes/revisor |
| lacuna de autorização reaparecer nas rotas novas | média/alta | matriz 4 perfis + vínculo explícito + testes negativos antes da UI | autor backend/revisor |
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
3. **Cardinalidade aluno↔turma:** aceitar N:N com entidade de matrícula (`Enrollment`), permitindo
   histórico/status/datas de matrícula (recomendação), ou restringir 1:N nesta versão.
4. **Curso↔Disciplina:** aceitar N:N (uma disciplina curricular pode existir em vários cursos,
   com uma entidade associativa e atributos por curso — recomendação) ou Course 1:N Discipline.
5. **Identidade de turma/oferta:** incluir obrigatoriamente `period`/ano-semestre e um código
   interno, com unicidade proposta `(discipline_id, period, code)`, ou adiar período letivo. A
   recomendação é incluir desde AV-S03 para não confundir turmas históricas.
6. **Vínculo professor↔turma:** entidade associativa N:N com `role` (responsável/colaborador),
   `starts_at`/`ends_at` opcionais e unicidade `(professor_id, class_group_id, role)`; ou vínculo
   simples sem atributos. Recomendação: entidade explícita com papel, para autorização auditável.
7. **Unicidades naturais:** aprovar códigos internos únicos no escopo pai (`Course.code` por
   organização, `Discipline.code` por organização ou curso conforme decisão 4, `Student.external_id`
   por organização), sem assumir CPF/e-mail real. Ajustar se outro identificador for preferido.
8. **Avaliações legadas sem turma:** manter `assessment.class_group_id` nullable nesta sprint,
   preservando todas as avaliações existentes; avaliações novas devem exigir turma após data de
   corte explicitamente definida. Migração/backfill das avaliações legadas é item separado,
   não dedução automática. Downgrade só é seguro enquanto não houver dados dependentes, ou precisa
   preservar/exportar dados antes de remover tabelas — decidir a política.
9. **Entidade Organização:** confirmar que em AV-S03 ela é apenas estrutura acadêmica, sem
   multi-tenancy. Se isolamento cross-organização for requisito agora, abrir decisão/backlog
   próprios antes da implementação (mudança relevante de escopo).
10. **Matriz de autorização:** aprovar ou ajustar a matriz da seção 5.1 (administração de
    organizações/cursos/disciplinas/vínculos; professor restrito às turmas vinculadas).
11. **Itens da sprint:** aprovar `BL-AV-2-01` a `BL-AV-2-05` no escopo acima, ou ajustar/remover algum.
12. **OCR paralelo:** autorizar apenas o detalhamento documental do levantamento técnico
    `BL-AV-4B-01`/`AV-S05B` em paralelo (sem execução), ou manter tudo após AV-S03. Independentemente
    disso, entrada por imagem permanece prioritária sobre CSV.

## 15. Definition of Done proposta

- [ ] decisões da seção 14 registradas sem inferência;
- [ ] critérios AC-01 a AC-10 avaliados com denominador explícito;
- [ ] migração testada em PostgreSQL isolado, não aplicada a ambiente operacional sem autorização;
- [ ] matriz de autorização (professor vinculado/não vinculado/admin/não autenticado) verde;
- [ ] nenhuma alegação de multi-tenancy sem requisito aprovado;
- [ ] dados fictícios apenas;
- [ ] implementação/revisão por agentes distintos;
- [ ] CI remota verde no HEAD exato;
- [ ] snapshot/dashboard/débitos/decisões atualizados;
- [ ] homologação de Rafael registrada somente se ocorrer.

## 16. Critérios de encerramento

AV-S03 só pode ser concluída se a estrutura acadêmica mínima estiver implementada, autorização por
vínculo comprovada negativa e positivamente, migração validada em Postgres isolado, UI mínima
validada em navegador real, CI remota verde e nenhuma ampliação implícita para multi-tenant/OCR/CSV.

**Critérios críticos:** AC-01 (migração), AC-02 (caminho positivo do professor vinculado), AC-03
(bloqueio do não vinculado), AC-04 (admin), AC-05 (não autenticado/retorno), AC-06 (UI mínima
integrada ao objetivo funcional), AC-07 (sem alegação multi-tenant) e AC-08 (CI). Falha de
qualquer um impede conclusão automática; não pode ser aceita apenas como débito sem exceção
explícita de Rafael. AC-09/10 também precisam ser avaliados, mas uma lacuna documental não crítica
só pode levar a `concluída com débitos` se registrada e aceita explicitamente.

Integração, migração operacional e promoção de baseline exigem autorizações específicas
independentes.

## 17. Execução e review

**Não iniciado.** Preencher somente após aprovação explícita de Rafael e abertura formal da sprint.

## 18. Closure gate

Não aplicável enquanto a sprint estiver apenas planejada. Ao final de execução futura, aplicar
[`sprint_closure_gate.md`](../sprint_closure_gate.md).
