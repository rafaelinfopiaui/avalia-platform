---
id: "AV-S01"
status: homologada_com_debito_residual
objetivo_aprovado_por: "Rafael (2026-09-23, homologação de GOV-001 a GOV-004 e aprovação desta sprint na mesma conversa)"
consolidador: "Hermes"
baseline_entrada: "../snapshots/latest_validated_baseline.md (nenhum promovido — BASELINE-001 permanece candidato)"
---

# AV-S01 — Autorização por vínculo, retomada de fluxo e revalidação

> Primeira sprint funcional aprovada sob esta governança. Aprovação registrada por Rafael em 2026-09-23, com 7 refinamentos obrigatórios (ver §3, §6, §8, §11, §14). Esta aprovação cobre exclusivamente os itens listados em §5 — não autoriza AV-S02 em diante nem qualquer outra sprint da trilha.

## 1. Objetivo e valor esperado

Eliminar a lacuna de autorização por vínculo encontrada por inspeção estática nas rotas de resposta, correção e revisão, e resolver a retomada de fluxo que hoje depende de `sessionStorage` do navegador — ambos condição para o resultado esperado da Etapa 1 ("um professor completa e retoma o fluxo; outro professor não acessa seus dados"). Produzir, junto, uma revalidação datada da suíte existente.

Resultado observável ao final: as quatro rotas identificadas (e qualquer rota nova criada nesta sprint) aplicam o mesmo padrão de autorização por vínculo já usado em `get_assessment`/`publish_assessment`; a tela de revisão carrega corretamente ao abrir a URL diretamente, sem depender de navegação prévia; a suíte Core/AI Engine e o build do frontend têm um resultado real e datado, não herdado de 09–11/09/2026.

## 2. Origem

| Fonte/requisito | Trecho ou decisão aplicável | Link |
|---|---|---|
| BL-AV-1-01/02/03/04/07/08 | Itens de backlog detalhados na Etapa 1 | [`backlog_tecnico_avalia.md`](../backlog/backlog_tecnico_avalia.md) §3 |
| RF-01 (RBAC no servidor), RNF-01 | Requisitos de origem dos itens 01/02/04 | citado no backlog, item BL-AV-1-01 |
| Achado de código desta trilha (GOV-002) | `create_answer`, `request_correction`, `get_correction_job`, `review_correction` em `core/app/main.py` não chamam `_get_owned_assessment` nem equivalente — confirmado nesta sessão por leitura direta do arquivo (linhas 190-329) | `core/app/main.py` |
| Escopo explícito do usuário | "verificar retomada do trabalho após sair da sessão ou abrir uma URL diretamente" | conversa de instituição da governança |
| RN-017 | comportamento já validado de que falha da IA não fabrica resultado; teste existente `test_ai_engine_unavailable_does_not_fabricate_result` | `core/app/tests/test_core_flow.py` linha 74 |
| Instrução de Rafael (2026-09-23, aprovação desta sprint) | 7 refinamentos de escopo, autorização e critérios de aceite | esta conversa; refletidos em §3, §6, §8, §11, §14 |

Lacunas de fonte: nenhuma — todos os itens têm origem rastreável, sem requisito inventado.

## 3. Escopo

Incluído:
- reprodução em runtime da lacuna de autorização nas rotas `create_answer`, `request_correction`, `get_correction_job`, `review_correction` (BL-AV-1-01);
- correção dessas rotas para exigir vínculo de propriedade (mesmo padrão de `_get_owned_assessment`), preservando acesso do papel `admin` (BL-AV-1-02);
- alteração do frontend para que a tela de revisão recupere dados via API a partir do `id` da URL, em vez de depender exclusivamente de `sessionStorage` (BL-AV-1-03);
- **refinamento nº 3 de Rafael:** design e registro do contrato de um endpoint de leitura agregado necessário à retomada (ver §6) — a *implementação* deste endpoint específico só começa depois que o contrato, a verificação de autorização por vínculo e a revisão arquitetural estiverem registrados (ver gate em §6.3);
- suíte de regressão cobrindo os quatro endpoints (e o endpoint novo, se implementado nesta sprint) com quatro perfis de acesso: professor dono, outro professor, admin, sem autenticação (BL-AV-1-04, refinamento nº 5 de Rafael);
- revalidação da suíte pytest do Core e AI Engine e do build do frontend, com resultado datado (BL-AV-1-07);
- confirmação de que `test_ai_engine_unavailable_does_not_fabricate_result` continua passando após as correções (BL-AV-1-08);
- **refinamento nº 4 de Rafael:** validação visual **dirigida** aos quatro casos de retomada de AC-03 (não a validação visual completa do roteiro de demonstração, que permanece em AV-S02).

Fora de escopo:
- estrutura acadêmica (etapa 2, AV-S03);
- CI versionada (AV-S02);
- validação visual **completa** do roteiro de demonstração (AV-S02) — apenas os casos de AC-03 são validados visualmente nesta sprint;
- qualquer mudança de schema de banco além da estritamente necessária para a correção de autorização (nenhuma prevista);
- qualquer item de outra etapa da trilha (2 a 8, incluindo 4B);
- qualquer decisão sobre as próximas sprints — esta aprovação não estende autorização de execução a AV-S02 em diante.

## 4. Baseline e estado de abertura

- último baseline validado: nenhum (`BASELINE-001` permanece candidato — a homologação de GOV-001 a GOV-004 registrada por Rafael em 2026-09-23 é documental e **não promove** `BASELINE-001` a baseline funcional, conforme ressalva nº 2 da Decisão A);
- última execução registrada no início desta sprint: [GOV-004](../snapshots/snapshot_EXEC-2026-09-23-01_GOV-004.md);
- commit/branch de referência: `main` / `0be691e12e9d5d6f3ffc989237739f6559d8dacd` (working tree com as mesmas alterações locais de GOV-001–004, nenhum código tocado até a abertura desta sprint);
- alterações preexistentes a proteger: `docs/roteiro-apresentacao-supervisor.md` e toda a árvore `docs/governance/`;
- dependências/bloqueantes: nenhuma dependência técnica de outra sprint (primeira sprint candidata). `BKL-AV-004` (achado de autorização não reproduzido em runtime) é justamente o que `BL-AV-1-01` resolve — não é um bloqueante externo, é o próprio objeto desta sprint.

## 5. Backlog e DoR

| ID | Descrição | Responsável | DoR | Estado |
|---|---|---|---|---|
| BL-AV-1-01 | Reproduzir em runtime a lacuna de autorização nas 4 rotas | Codex | ready — fixture `second_professor_token` definida em §6.1; nenhuma decisão de produto pendente | proposto → pronto para iniciar |
| BL-AV-1-02 | Corrigir as quatro rotas para exigir vínculo de propriedade | Codex | ready após 01 confirmar o achado | proposto |
| BL-AV-1-03 | Retomada via API na tela de revisão (consumir o novo endpoint de contexto, ver §6) | Antigravity CLI | ready — contrato do endpoint definido em §6.2; implementação do endpoint em si depende do gate de §6.3 | proposto |
| BL-AV-1-04 | Suíte de regressão de autorização cruzada, com matriz de 4 perfis (refinamento nº 5) | Codex | ready após 01/02 | proposto |
| BL-AV-1-07 | Revalidação datada da suíte pytest (Core, AI Engine) e build do frontend | Codex (backend) + Antigravity CLI (build frontend) | ready — não depende de decisão de produto | proposto |
| BL-AV-1-08 | Confirmar RN-017 após as correções de autorização | Codex | ready após 02 | proposto |

Nenhum item depende de decisão de produto ainda pendente (`DEC-AV-006` em diante) — todas as lacunas de DoR eram técnicas de refinamento, resolvidas pelos 7 pontos de Rafael e registradas abaixo.

## 6. Mapa de impacto

| Item | Criar | Alterar | Não tocar |
|---|---|---|---|
| BL-AV-1-01/04 | `core/app/tests/test_authorization_boundaries.py` (novo); fixture `second_professor_token` em `core/app/tests/conftest.py` | — | modelos e schemas existentes |
| BL-AV-1-02 | — | `core/app/main.py` (rotas `create_answer`, `request_correction`, `get_correction_job`, `review_correction`) | `core/app/deps.py` (reutilizar `require_role`/`get_current_user` existentes, não recriar) |
| BL-AV-1-03 | endpoint novo `GET /v1/correction-jobs/{job_id}/context` (contrato em §6.2); `frontend/src/services/api.ts` (nova função `getCorrectionContext`) | `frontend/src/pages/ReviewPage.tsx` (buscar via API quando `readWorkflow()` estiver vazio, mantendo `sessionStorage` como cache local, não como única fonte) | `frontend/src/pages/CorrectionPage.tsx` (já busca via API; validar se precisa reaproveitar o novo endpoint em vez de duplicar lógica) |
| BL-AV-1-07 | — | nenhum arquivo de produto; apenas execução de comando e registro de resultado | — |
| BL-AV-1-08 | — | nenhuma alteração de código prevista; apenas execução do teste existente | `core/app/tests/test_core_flow.py` (não modificar o teste, só executá-lo) |

### 6.1 Refinamento nº 2 de Rafael — fixtures isoladas

Decisão técnica registrada (rotineira, dentro da autorização geral de Rafael para Hermes resolver detalhes de execução): a suíte já usa um padrão isolado por teste — `test_engine` (fixture em `core/app/tests/conftest.py`, linha 19) cria um SQLite próprio em `tmp_path`, descartado ao final do teste; não existe seed nem dado de ambiente operacional tocado pelos testes atuais. Para `BL-AV-1-01/04`, será adicionada uma fixture `second_professor_token`, análoga à `professor_token` existente (mesmo arquivo, linha 56), criando um segundo usuário professor isolado no mesmo `test_engine` de cada teste. Nenhum seed real ou dado de ambiente será criado, alterado ou lido — apenas dados fictícios dentro do banco de teste temporário, descartado ao final.

### 6.2 Refinamento nº 3 de Rafael — contrato proposto do endpoint de leitura para retomada

**Problema real, confirmado por leitura de código nesta sessão:** `ReviewPage.tsx` (linha 10) só lê `readWorkflow()` (`sessionStorage`); se vazio, mostra aviso de dados indisponíveis (linha 18) em vez de buscar via API. `CorrectionPage.tsx` já busca o `job` via API a cada poll (linha 22), mas não tem acesso a `assessment`/`question`/`rubric`/`answer` — apenas ao `job`, que não inclui esses dados aninhados (`CorrectionJobOut`, `core/app/schemas.py` linha 140, só tem `id`, `answer_id`, `status`, `attempt`, `error_message`, `latest_execution`).

**Contrato proposto (design, não implementado nesta mensagem):**

```
GET /v1/correction-jobs/{job_id}/context
Autenticação: obrigatória (Bearer token)
Autorização: mesmo padrão de _get_owned_assessment — o professor autenticado
             só acessa se for owner_id da Assessment correspondente à cadeia
             job -> answer -> question -> assessment; papel admin sempre acessa.
Resposta 200:
  {
    "job": CorrectionJobOut,        # já existe, reaproveitado
    "answer": AnswerOut,            # já existe, reaproveitado
    "question": QuestionOut,        # já existe (inclui rubrics[]), reaproveitado
    "assessment": { "id": str, "title": str }   # subconjunto mínimo, não o AssessmentOut completo
  }
Erros:
  404 se job/answer/question/assessment não existir (mesma semântica de get_correction_job hoje);
  403 se o professor autenticado não for owner_id da assessment (papel admin sempre passa) —
      esta é a checagem que get_correction_job NÃO tem hoje, e que este novo endpoint já nasce com.
```

Justificativa de agregação (em vez de 3 chamadas separadas): evita expor `GET /v1/answers/{id}` e `GET /v1/questions/{id}` como rotas novas isoladas — cada uma exigiria sua própria checagem de autorização por vínculo, ampliando a superfície de auditoria. Um único endpoint de contexto, já nascendo com a checagem correta, é mais fácil de revisar e teve precedente já usado (`get_assessment`, que devolve `AssessmentOut` aninhado com `questions[].rubrics[]`).

### 6.3 Gate de implementação do endpoint (refinamento nº 3, parte final)

Conforme instrução de Rafael ("registrar contrato, autorização por vínculo e revisão arquitetural antes da implementação"), a implementação de `GET /v1/correction-jobs/{job_id}/context` só começa depois que:
1. este contrato (§6.2) tiver sido revisado por um agente que não seja quem vai implementá-lo (ver §7 — Antigravity CLI ou Hermes, já que Claude Code está indisponível nesta reconfirmação, ver §11);
2. a revisão confirmar que a checagem de autorização por vínculo está correta e que o contrato não duplica dado sensível desnecessário na resposta;
3. qualquer ajuste do contrato resultante da revisão for registrado em §14 (Ajustes de percurso) antes do código ser escrito.

**Revisão executada em 2026-09-23T15:5x-03:00 por Antigravity CLI** (`agy -p`, modelo Gemini 3.1 Pro High), papel de revisor arquitetural independente, redistribuído de Claude Code conforme §11. Parecer:

- checagem de autorização por vínculo (cadeia `job → answer → question → assessment`, comparação com `owner_id`, exceção para `admin`): **correta e consistente** com `_get_owned_assessment`;
- exposição de dado sensível: **nenhuma além do já exposto** hoje por `CorrectionJobOut`/`AnswerOut`/`QuestionOut`; o subconjunto mínimo de `assessment` (`id`+`title`) foi elogiado como desenho correto (evita expor todas as questões da prova);
- semântica de erro (404/403): consistente com o padrão de `_get_owned_assessment`;
- **ressalva de design:** o contrato originalmente descrito em §6.2 usava um dicionário ad-hoc `{"id": str, "title": str}` para o resumo de `assessment`, divergindo do padrão do projeto de usar exclusivamente modelos Pydantic (`BaseModel`) para toda resposta tipada;
- **aprovação: condicional.** Condição exigida antes da implementação: formalizar os schemas de resposta em `core/app/schemas.py` como modelos Pydantic explícitos — `AssessmentSummaryOut` (apenas `id`, `title`) e `CorrectionJobContextOut` (agregando `job`, `answer`, `question`, `assessment`), em vez de montar o JSON diretamente na rota.

**Ajuste aplicado ao contrato de §6.2**, registrado também em §14: a resposta 200 passa a ser tipada como `CorrectionJobContextOut` (Pydantic), com `assessment: AssessmentSummaryOut` no lugar do dicionário ad-hoc. Nenhuma mudança de campo, nome ou semântica de erro — apenas formalização de tipo, conforme exigido pela revisão.

Gate atendido. Implementação autorizada a prosseguir, com a condição acima incorporada.

## 7. Delegação

| Item | Executor | Objetivo | Arquivos/escopo | Critérios | Limites | Evidência esperada |
|---|---|---|---|---|---|---|
| BL-AV-1-01 | Codex | Reproduzir em runtime a lacuna de autorização | `core/app/tests/test_authorization_boundaries.py` (novo), `conftest.py` (fixture nova) | AC-01 (matriz de 4 perfis) confirmando o achado nas 4 rotas | não alterar `core/app/main.py` nesta etapa — só reproduzir, não corrigir | saída real de `pytest -v` anexada ao fechamento |
| BL-AV-1-02 | Codex | Corrigir as 4 rotas | `core/app/main.py` (rotas citadas) | AC-01/AC-02 passando; nenhuma rota `admin` quebrada | reutilizar `_get_owned_assessment` ou padrão equivalente; não criar novo mecanismo de autorização | diff da alteração + saída de `pytest` |
| BL-AV-1-03 (frontend) | Antigravity CLI | Retomada via API na tela de revisão | `frontend/src/pages/ReviewPage.tsx`, `frontend/src/services/api.ts` | AC-03 (4 sub-casos) | não implementar o endpoint novo (é Codex, após gate §6.3); usar `sessionStorage` só como cache, nunca única fonte | evidência visual dos 4 casos + teste de frontend, se viável |
| BL-AV-1-03 (endpoint, contrato) | revisão: Antigravity CLI; implementação: Codex, após gate §6.3 | Revisar e, após aprovação, implementar `GET /v1/correction-jobs/{job_id}/context` | `core/app/main.py`, `core/app/schemas.py` (schema agregado novo, se necessário) | autorização por vínculo correta (mesmo padrão de BL-AV-1-02); nenhum dado sensível além do já exposto em endpoints existentes | implementação só após revisão registrada (§6.3) | registro da revisão em §14 antes do código; depois, diff + teste |
| BL-AV-1-04 | Codex | Suíte de regressão com matriz de 4 perfis | `core/app/tests/test_authorization_boundaries.py` | AC-01 cobrindo as 4 rotas × 4 perfis (16 casos, ou menos se algum perfil não se aplicar a uma rota) | cobre também o endpoint novo, se implementado a tempo | saída real de `pytest` |
| BL-AV-1-07 | Codex (Core/AI Engine) + Antigravity CLI (build frontend) | Revalidação datada da suíte e build | nenhum arquivo de produto | AC-06 | apenas execução e registro, sem alterar comportamento | saída de `pytest`/`npm run build` com contagem e data |
| BL-AV-1-08 | Codex | Confirmar RN-017 após as correções | nenhuma alteração de código | AC-05 | não modificar o teste existente | saída de `pytest` do teste específico |
| Revisão cruzada geral | Antigravity CLI (backend de Codex) e Codex (frontend de Antigravity), consolidação final por Hermes | Revisão independente de cada mudança antes de considerar a sprint fechável | toda a sprint | nenhuma alegação de "corrigido" sem reprodução real prévia | Claude Code está indisponível nesta reconfirmação (ver §11) — seu papel de revisão arquitetural não é preenchido por autorrevisão do próprio implementador | registro de quem revisou o quê, no fechamento |

Consolidação canônica: Hermes.

## 8. Critérios de aceite

**Refinamento nº 5 de Rafael aplicado:** AC-01 passa a ser uma matriz de 4 perfis (proprietário, outro professor, admin, sem autenticação), não apenas 2 casos.

| ID | Critério | Método previsto | Estado |
|---|---|---|---|
| AC-01 | Matriz de autorização nas rotas `create_answer`, `request_correction`, `get_correction_job`, `review_correction` e no endpoint novo (se implementado): (a) professor proprietário — permitido; (b) outro professor — bloqueado, sem criar resposta/job/revisão; (c) admin — permitido; (d) sem autenticação — 401, sem side-effect. Nenhuma requisição negada cria efeito colateral (resposta, job ou revisão registrados). | automatizada (integração real de componentes internos — pytest + TestClient + SQLite real, sem rede externa, sem navegador) + integração real via HTTP contra serviços rodando | **atendido** — 35/35 testes (incluindo 24 de matriz), reexecução independente por Hermes; matriz completa reconfirmada via `curl`/requests reais contra Core+Postgres reais, com 2 professores reais |
| AC-02 | *(absorvido pela matriz de AC-01, mantido como referência histórica ao critério original)* | — | substituído por AC-01 |
| AC-03 | Refinado (refinamento nº 4 de Rafael) — 4 sub-casos de retomada via URL de revisão: (a) usuário autenticado, sem contexto local de revisão (`sessionStorage` vazio) abre a URL diretamente e os dados corretos são carregados via API; (b) contexto antigo de outra resposta em `sessionStorage` não contamina a revisão atual (a página usa o `id` da URL como fonte de verdade, não o cache antigo); (c) usuário sem autenticação é redirecionado ao login e retorna ao destino original após autenticar; (d) usuário autenticado mas sem permissão sobre aquela avaliação recebe bloqueio (mesmo padrão de AC-01/403), não uma tela quebrada. | visual/integração real via navegador (captura ou gravação) + inspeção de código para (b); AC-03(c) já é comportamento existente de `SessionGuard`/`LoginPage` (a confirmar, não presumir) | **atendido — sem lacuna de evidência (saneamento de 2026-09-23, snapshot [`EXEC-2026-09-23-05`](../snapshots/snapshot_EXEC-2026-09-23-05_AV-S01-saneamento.md) §3).** Os 4 sub-casos foram confirmados por evidência visual real em navegador (Chrome real via CDP + Playwright, screenshots inspecionados): (a) dados corretos carregados via API sem cache local; (b) 10 capturas de estado durante navegação client-side entre 2 revisões, nenhum frame com dados vazados da revisão anterior; (c) redirect para login com retorno ao destino original e query string preservada; (d) bloqueio 403 explícito, sem tela quebrada, sem vazamento de dado. A lacuna de evidência anteriormente registrada (validação só por integração HTTP + inspeção de código) está sanada. |
| AC-04 | Suíte de regressão automatizada cobre a matriz de AC-01 nas 4 rotas (e no endpoint novo, se aplicável) e passa | automatizada | **atendido** — 24 casos (20 de matriz + 4 de cadeia quebrada), reexecutados por Hermes |
| AC-05 | `test_ai_engine_unavailable_does_not_fabricate_result` continua passando após as mudanças | automatizada | **atendido** — reexecutado 2x por Hermes (1 passed em ambos, após correção de poluição de ambiente registrada em §14) |
| AC-06 | Suíte completa do Core e do AI Engine (modo simulado) e build do frontend executados nesta sprint, com contagem real e data | automatizada | **atendido com débito** — Core 35/35; AI Engine 21/21 (modo padrão), 19/21 (`AI_ENGINE_MODE=simulated` global, `DEBT-AV-009`, causa identificada e não relacionada a esta sprint); frontend `npm run build` 0 erros (4 execuções) |

**Refinamento nº 1 de Rafael aplicado a todos os AC acima:** um AC só é marcado "atendido" com evidência real de execução (comando + saída + data). Se um documento de política ou este próprio plano disser algo diferente do que a execução real mostrar, a divergência é registrada explicitamente — nunca resolvida declarando conformidade só porque o documento tem precedência normativa. Precedência normativa (política > sprint > evidência mais antiga) rege o que é *esperado*; evidência datada rege o que é *observado*. As duas coisas não se confundem no fechamento desta sprint.

## 9. Definition of Done

- [x] AC-01, AC-03 (4 sub-casos), AC-04, AC-05, AC-06 avaliados com evidência real e classificação de tipo (§10) — AC-03 sem lacuna de evidência, comprovado por validação visual real no saneamento de 2026-09-23 (snapshot `EXEC-2026-09-23-05`);
- [x] nenhuma rota `admin` quebrada — confirmado via matriz de testes e integração HTTP real;
- [x] mudanças vinculadas aos itens BL-AV-1-01 a 04, 07, 08;
- [x] contrato do endpoint novo (§6.2) revisado por agente diferente do implementador, com registro em §14, antes do código ser escrito;
- [x] débitos/decisões residuais registrados nos registros canônicos com ID (`DEBT-AV-009`);
- [x] revisão cruzada real registrada (quem revisou o quê), sem autorrevisão apresentada como independente — backend por Antigravity CLI, frontend por Codex (3 rodadas);
- [x] disponibilidade dos agentes reconfirmada no dia real de execução (não presumida a partir do registro de §11) — Claude Code reconfirmado indisponível (`claude auth status`);
- [x] snapshot de execução gerado;
- [x] dashboard atualizado;
- [x] closure gate desta sprint preenchido (§16);
- [x] README/contrato OpenAPI atualizado (`core/README.md`, `docs/contracts/openapi.yaml`);
- [x] homologação de Rafael sobre o fechamento registrada em 2026-09-23 — inclui execução original e saneamento `EXEC-2026-09-23-05`, com `DEBT-AV-009` aceito como débito residual aberto; não autoriza commit/push/tag/deploy, promoção de baseline nem próxima sprint.

## 10. Validações previstas

**Refinamento nº 6 de Rafael aplicado — classificação explícita de tipos de evidência, sem misturá-los:**

| Item/AC | Comando ou procedimento | Ambiente | Tipo (classificação explícita) |
|---|---|---|---|
| AC-01 | `pytest core/app/tests/test_authorization_boundaries.py -v` (novo arquivo) | SQLite de teste local (`tmp_path`, descartado ao final) | **automatizada — integração real de componentes internos** (FastAPI + SQLAlchemy + SQLite real; não é mock, mas também não envolve navegador nem rede externa) |
| AC-03(a)(b)(d) | teste de frontend (framework a definir) ou roteiro manual documentado com captura de tela | navegador local | **visual/integração real** (via navegador de verdade, distinto do item acima) |
| AC-03(c) | inspeção de código de `SessionGuard`/`LoginPage` + confirmação manual no navegador | navegador local | **inspeção de código + visual**, classificados separadamente no registro de fechamento |
| AC-04 | `pytest core/app/tests -q` | ambiente de teste do Core | automatizada |
| AC-05 | `pytest core/app/tests/test_core_flow.py::test_ai_engine_unavailable_does_not_fabricate_result -v` | ambiente de teste do Core | automatizada |
| AC-06 | `pytest` (Core), `pytest` (AI Engine, **modo simulado** — Ollama real não fica implicitamente incluído nesta sprint), `npm run build` (frontend) | ambiente local do executor | automatizada; a parte do AI Engine é explicitamente **modo simulado**, não integração real com Ollama — se algum resultado depender de Ollama real, isso deve ser rotulado como **integração real com serviço externo**, não confundido com o resultado em modo simulado |

Nenhum resultado histórico (09–11/09/2026) é reaproveitado como evidência desta sprint — apenas como contexto, conforme já registrado em BASELINE-001.

## 11. Riscos e mitigação

| Risco | Probabilidade/impacto qualitativo | Mitigação | Dono |
|---|---|---|---|
| BL-AV-1-01 pode não confirmar a lacuna (falso positivo da inspeção estática) | baixa probabilidade / impacto baixo | registrar o resultado real e ajustar o item antes de prosseguir para 02 | Codex |
| Correção de autorização quebra fluxo legítimo do próprio professor | média / média | AC-01(a) cobre professor dono explicitamente na matriz | Codex |
| Endpoint novo (§6.2) amplia superfície de autorização sem revisão suficiente | média / alta — é exatamente o tipo de falha que esta sprint existe para corrigir, não para repetir | gate obrigatório de §6.3: revisão por agente diferente do implementador antes do código | Antigravity CLI (revisor) + Hermes (consolidação) |
| **Refinamento nº 7 de Rafael — Claude Code indisponível** | certa (confirmada nesta sessão, ver §11 abaixo — nomenclatura de seção duplicada intencionalmente evitada; ver "Disponibilidade dos agentes" logo abaixo) | revisão arquitetural planejada para Claude Code é redistribuída entre Antigravity CLI e Hermes, registrada como tal — nunca apresentada como se Claude Code tivesse revisado | Hermes |
| Ambiente local desatualizado desde a última revalidação dificulta AC-06 | média | registrar exatamente o que falhou por ambiente vs. por código, sem misturar as duas causas | executor da sprint |
| AC-03(c) pode já funcionar sem mudança (comportamento existente de `SessionGuard`) ou pode precisar de ajuste | a confirmar | não presumir; tratar como item de verificação, registrando se precisou de código novo ou não | Antigravity CLI |

### Disponibilidade dos agentes (refinamento nº 7 de Rafael, reconfirmada nesta sessão)

Reconfirmação real, executada em 2026-09-23, nesta sessão (não reaproveitada de registro de 22/09):

- **Codex** — `codex exec "responda apenas: ok"` → respondeu `ok` (sessão real, modelo `gpt-5.6-sol`, workdir confirmado no repositório correto). Disponível.
- **Antigravity CLI** — `agy -p "responda apenas: ok"` → respondeu `ok`. Disponível.
- **Claude Code (subprocess)** — `claude -p "responda apenas: ok"` → `Failed to authenticate: OAuth session expired and could not be refreshed`. **Indisponível**, mesma causa raiz já registrada em execuções anteriores (sessão OAuth expirada).

Consequência registrada, conforme instrução de Rafael: o papel de revisão arquitetural originalmente previsto para Claude Code nesta sprint (revisão cruzada de BL-AV-1-02 e do contrato do endpoint em §6.2/§6.3) é reatribuído a **Antigravity CLI**, com consolidação final por **Hermes**. Nenhuma revisão de Claude Code será declarada nesta sprint. Se Codex implementar BL-AV-1-02 e o endpoint novo, a revisão desses itens não pode ser feita pelo próprio Codex apresentando-se como revisor independente — cabe a Antigravity CLI e/ou Hermes.

## 12. Estimativas

Método: contagem de itens e complexidade qualitativa, sem histórico de velocity sob esta governança (mesma base metodológica já usada em `proposta_sprints_operacao_de_turma.md`). Tamanho qualitativo: **M** (média) — 6 itens de backlog originais + 1 refinamento técnico (endpoint de contexto) com gate de revisão próprio. Valores desta seção são estimativas, não compromissos.

## 13. Critérios de encerramento

Além do [closure gate geral](../sprint_closure_gate.md):
- a matriz de autorização de AC-01 precisa cobrir as 4 rotas originais **e** o endpoint novo, se ele tiver sido implementado dentro desta sprint; se o endpoint não for implementado a tempo, isso é registrado como não entrega parcial, não como falha silenciosa;
- nenhum AC pode ser marcado "atendido" citando apenas a existência de código — exige saída de comando real, com data;
- a reatribuição do papel de Claude Code (§11) precisa estar registrada no fechamento, não apenas nesta abertura;
- a Decisão A (ajuste 1 de Rafael) aplica-se ao fechamento: qualquer divergência entre o que este documento previu e o que a execução real mostrou é registrada como divergência, não reconciliada silenciosamente citando a precedência do documento.

## 14. Ajustes de percurso

| Data/fuso | Mudança | Motivo | Impacto | Decisão/autorização |
|---|---|---|---|---|
| 2026-09-23T14:35-03:00 | Escolha do nome do endpoint (`GET /v1/correction-jobs/{job_id}/context`) e da fixture (`second_professor_token`) | detalhe técnico de nomenclatura, sem ambiguidade de produto | nenhum | escolha técnica rotineira de Hermes, dentro da autorização geral de Rafael ("Hermes pode resolver escolhas técnicas rotineiras... registrando-as") |
| 2026-09-23T15:5x-03:00 | Resposta do endpoint novo tipada como Pydantic (`CorrectionJobContextOut`/`AssessmentSummaryOut`) em vez de dicionário ad-hoc | exigência da revisão arquitetural (Antigravity CLI, §6.3) para manter consistência de tipagem forte já usada em todo `main.py`/`schemas.py` | nenhuma mudança de campo/semântica de erro; apenas formalização de tipo | condição da revisão arquitetural (§6.3), aplicada por Hermes como escolha técnica rotineira dentro da autorização geral de Rafael |
| 2026-09-23T16:4x-03:00 | Guard `data.job?.id !== id` adicionado diretamente por Hermes em `ReviewPage.tsx`, entre o guard de erro e a renderização de `ReviewForm` | fechar a última janela de exposição de dados de revisão anterior ao navegar client-side entre duas revisões sem remontar o componente — achado de revisão cruzada por Codex (2ª rodada de achado sobre o mesmo componente) | impede renderizar `ReviewForm` com `job` de um `id` diferente do da URL atual; nenhuma mudança de contrato ou comportamento de rotas do backend | escolha técnica rotineira de Hermes, dentro da autorização geral de Rafael; confirmada como correção suficiente por revisão de confirmação do Codex ("corrigido, aprovado") |
| 2026-09-23T16:5x-03:00 | Variáveis de ambiente (`AI_ENGINE_URL`, `DATABASE_URL`, `JWT_SECRET` etc.) exportadas por Hermes no terminal para subir os serviços locais (Core/AI Engine/frontend) causaram falha transitória do teste `test_ai_engine_unavailable_does_not_fabricate_result` ao rodar a suíte na mesma sessão de shell | poluição de ambiente da própria verificação de Hermes, não uma regressão de código — o teste depende de `AI_ENGINE_URL` apontar para porta inexistente (via `conftest.py`, que só usa `setdefault`) | nenhum no código; a suíte voltou a 35/35 após `unset` das variáveis | registrado para transparência (ressalva 1 da Decisão A de Rafael — divergência sempre registrada); nenhuma correção de código foi necessária |

Novos ajustes serão adicionados a esta tabela conforme ocorrerem durante a execução real.

## 15. Execução e review

Execução backend de 2026-09-23 (Codex), vinculada a BL-AV-1-01/02/04/07/08:

- BL-AV-1-01: matriz escrita antes da correção; `pytest` observou sucesso indevido do segundo professor nas quatro rotas (`201`, `202`, `200`, `200`), com 8 failed/12 passed no conjunto que já incluía o endpoint ainda inexistente;
- BL-AV-1-02: implementada autorização pela cadeia relacional real antes de qualquer mutação; admin preservado;
- endpoint de contexto: implementado conforme contrato aprovado, com schemas Pydantic e `404` por elo ausente;
- BL-AV-1-04: 24 passed (20 casos de matriz + 4 casos de cadeia quebrada);
- BL-AV-1-07: Core 35 passed; AI Engine no modo explicitamente simulado 19 passed/2 failed; a mesma suíte no modo padrão passou 21/21. Divergência registrada como `DEBT-AV-009`;
- BL-AV-1-08: RN-017 isolado passou 1/1 sem alteração no teste.

**Verificação independente por Hermes (consolidador), 2026-09-23T16:0x-16:3x-03:00** — não reaproveitando a alegação do executor sem reprodução própria:

- ambiente Python 3.11 isolado criado (`/tmp/av_core_venv`, `/tmp/av_ai_venv`); Python 3.9 do sistema é incompatível com a sintaxe do projeto (`str | None`) e foi descartado;
- `pytest core/app/tests -v` reexecutado por Hermes: **35 passed**, confirma exatamente a alegação de Codex;
- `pytest core/app/tests/test_core_flow.py::test_ai_engine_unavailable_does_not_fabricate_result -v` reexecutado: **1 passed** — AC-05 confirmado;
- AI Engine reexecutado por Hermes: modo padrão **21 passed**; `AI_ENGINE_MODE=simulated` global **19 passed, 2 failed** (`test_invalid_llm_json_triggers_repair_and_succeeds`, `test_invalid_llm_json_fails_after_repair_returns_502`) — confirma que a divergência é causada pela variável de ambiente global, não pelas mudanças desta sprint (nenhum arquivo do AI Engine foi tocado); `DEBT-AV-009` confirmado como registrado corretamente;
- **integração real contra os serviços rodando** (Postgres real, Core em `uvicorn`, AI Engine em modo simulado, banco `avalia_dev` reaproveitado — dados fictícios de demonstração já existentes, nenhum dado real): matriz completa de AC-01 executada via chamadas HTTP reais com dois professores reais (seed + criado nesta sessão) e um endpoint novo — `create_answer`, `request_correction`, `get_correction_job`, `review_correction` e `GET .../context` retornaram `403` para o professor não-dono e `401` para requisição sem token em todos os casos; o professor dono conseguiu completar o fluxo completo (criar resposta → solicitar correção → consultar job → registrar revisão humana) com sucesso; o endpoint novo retornou o payload exato do contrato (`job`/`answer`/`question`/`assessment`) tipado corretamente;
- **revisão cruzada real por Antigravity CLI** (`agy -p`, modelo Gemini 3.1 Pro High), sobre o diff completo do backend + suíte de teste: confirmou (1) checagem de vínculo antes de qualquer efeito colateral, (2) semântica 404 preservada em `_get_job_context`, (3) suíte cobre os 4 perfis nas 4 rotas + endpoint novo, verificando ausência de efeito colateral em perfis negados, (4) nenhuma brecha de autorização encontrada — observação de design (N+1 queries em `_get_job_context`) classificada explicitamente como não-bug. **Veredito: aprovação incondicional.**

Frontend e AC-03: ver §15.1 abaixo (revisão cruzada encontrou 2 rodadas de problemas reais, ambas corrigidas e reconfirmadas).

### 15.1 — Frontend (BL-AV-1-03): 3 rodadas de implementação/revisão até convergir

**Rodada 1 (Antigravity CLI, implementação inicial):** endpoint consumido via `getCorrectionContext`; 4 sub-casos de AC-03 implementados; `npm run build` real: 0 erros. Revisão cruzada por Codex encontrou 5 problemas: uso de `any` em vez dos tipos do projeto; **achado mais sério — lógica de cache (`current.job?.id === id`) não garante coerência entre `job`/`answer`/`assessment` e permite que dados de outro professor fiquem em `sessionStorage` sem revalidação** (não limpo no logout; `CorrectionPage` só atualiza `job`); `writeWorkflow(newData as any)` grava objeto incompatível com o tipo `Assessment`; redirecionamento pós-login perdia `location.search` (`?manual=1`); sem guarda contra corrida entre requisições. Veredito: **aprovação condicional**.

**Rodada 2 (Antigravity CLI, correção dos 5 pontos):** `any` removidos (tipo `ReviewData` + tipos existentes de `types.ts`); `writeWorkflow` removido; `location.search` preservado em `App.tsx`; guarda de corrida com flag `active`; `npm run build` real: 0 erros. **Mas a correção do item de contaminação de cache ficou incompleta**: o componente ainda fazia `setData(current); setLoading(false)` de forma síncrona a partir do `sessionStorage` antes da resposta da API — ou seja, `ReviewForm` era renderizado imediatamente com dados potencialmente de outro professor, só trocando de tela quando o `403` chegasse. Revisão por Codex, com pergunta direcionada de Hermes sobre esse ponto específico: **veredito explícito "falha residual real, deve bloquear"** — não um débito aceitável, por violar diretamente o objetivo de isolamento entre professores desta sprint (AC-03(d)).

**Rodada 3 (Antigravity CLI, correção da janela de exposição):** removido o `setData(current)` síncrono; `loading` permanece `true` até a primeira resposta bem-sucedida da API. `npm run build` real: 0 erros. Nova revisão por Codex encontrou um problema residual mais estreito: ao navegar client-side entre duas revisões (mudança de `:id` sem remontar o componente), dados do `id` anterior (já autorizados) podiam aparecer por um render antes do `useEffect` reagir ao novo `id`.

**Correção final (aplicada diretamente por Hermes, consolidador, escolha técnica rotineira registrada em §14):** adicionado guard `if (data.job?.id !== id) { return <loading/> }` entre o guard de `errorObj` e a renderização de `ReviewForm`, garantindo que dados de uma revisão anterior nunca aparecem quando a URL já aponta para um `id` diferente, mesmo antes do fetch resolver. `npm run build` real (executado por Hermes): 0 erros. Confirmação final por Codex, com o diff completo: **"corrigido, aprovado"**.

**Verificação independente por Hermes:** `npm run build` reexecutado a cada rodada (4 execuções reais, todas com 0 erros TypeScript); `grep -n "\bany\b"` confirmando ausência de `any` no diff final; requisição HTTP real contra o backend rodando confirmando que `GET /correction-jobs/{job_id}/context` para um professor não-dono retorna `403` com corpo `{"detail": "..."}` sem vazar nenhum campo de `job`/`answer`/`question`/`assessment`.

### 15.2 — Limitação de ambiente: validação visual via navegador real não disponível nesta sessão

O refinamento nº 4 de Rafael pede validação visual dirigida dos 4 sub-casos de AC-03. Tentativas reais desta sessão:

- `browser_exec`/`new_tab` (sessões `default`, `avalia_demo`, `av01`, `av02`): falharam com `daemon didn't come up` — o Chrome já em uso pelo usuário não expõe porta de depuração remota, e não é seguro fechá-lo (risco de perder trabalho aberto do usuário);
- tentativa de subir um Chrome isolado com `--remote-debugging-port` próprio e apontar via `BROWSER_CDP_URL`/`BU_CDP_WS`: o processo Chrome isolado subiu corretamente (confirmado via `curl http://localhost:9333/json/version`), mas o daemon do `browser_exec` não honrou a variável de ambiente de processo nesta sessão; a alternativa de configurar `browser.cdp_url` em `~/.hermes/config.yaml` foi bloqueada pela própria ferramenta (`write_file` recusa por ser arquivo de configuração sensível do Hermes) — decisão correta de segurança, não contornada.

**Decisão registrada (escolha técnica rotineira de Hermes, dentro da autorização geral):** diante da indisponibilidade do navegador real, os 4 sub-casos de AC-03 foram verificados por **integração real via HTTP** contra os serviços rodando (Postgres real, Core via `uvicorn`, AI Engine via `uvicorn` em modo simulado, frontend buildado via Vite), não por captura visual em navegador:

- **(a)** confirmado por análise de código + build: sem cache local, `ReviewPage` monta com `loading=true`, chama `getCorrectionContext(id)`, e só renderiza `ReviewForm` após resposta 200;
- **(b)** confirmado por análise de código (guard `data.job?.id !== id`, rodada 3) + `npm run build`: dados de uma revisão anterior não aparecem quando o `id` da URL muda;
- **(c)** confirmado por leitura de `App.tsx`/`LoginPage.tsx`: `SessionGuard` redireciona para `/login` com `state.from = pathname + search`; `LoginPage` usa esse `from` após autenticar — mecanismo do React Router já existente, apenas corrigido para preservar `search` (rodada 2);
- **(d)** confirmado por chamada HTTP real: professor sem vínculo recebe `403` com corpo sem vazamento de dado, e o código do frontend trata explicitamente `ApiError.status === 403` com um `<Alert>` dedicado (não uma tela quebrada) — porém **não foi observado visualmente em navegador real**, apenas verificado por leitura de código e pela resposta HTTP real que o alimenta.

Este é um nível de evidência mais fraco que validação visual real (confirma o comportamento do lado do servidor e a lógica declarada do componente, mas não a renderização de fato em um DOM real). Registrado explicitamente como lacuna, não disfarçado como validação visual completa — conforme a ressalva 1 da Decisão A de Rafael (divergência entre o previsto e o observado sempre registrada).

## 16. Closure gate

Aplicado [`sprint_closure_gate.md`](../sprint_closure_gate.md):

### A. Escopo e produto
- A1 (objetivo/critérios avaliados item a item): atendido — ver §15.1/§15.2 e evidências de §10 real abaixo;
- A2 (mudanças vinculadas ao backlog): atendido — cada arquivo alterado corresponde a BL-AV-1-01/02/03/04/07/08;
- A3 (planejado/implementado/validado/homologado não confundidos): atendido — esta seção distingue verificação de Hermes de alegação dos executores, e nada é apresentado como homologado por Rafael;
- A4 (não entregas/riscos/débitos com IDs): atendido — `DEBT-AV-009` (AI Engine + modo simulado global) e a limitação de validação visual (§15.2) registrados;
- A5 (README/PRD/roadmap): `core/README.md` e `docs/contracts/openapi.yaml` atualizados pelo próprio Codex como parte do DoD do endpoint novo — confirmado por diff.

### B. Qualidade e evidência
- B1 (validações executadas ou marcadas honestamente): atendido — AC-01/04/05/06 com evidência real (testes + integração HTTP real); AC-03 com evidência parcial explícita (§15.2);
- B2 (comando/data/ambiente/resultado real): atendido — ver §10 desta seção;
- B3 (simulação/mock/inspeção/automação/integração real/visual diferenciados): atendido — §15.2 classifica explicitamente cada tipo de evidência usado;
- B4 (nenhuma limitação promovida a sucesso): atendido — a ausência de validação visual real é registrada como lacuna, não maquiada;
- B5 (testes/lint/build aplicáveis): **parcialmente atendido** — Core 35/35 passed; AI Engine 21/21 no modo padrão, 19/21 no modo simulado global (`DEBT-AV-009`, causa identificada, não relacionada às mudanças desta sprint); frontend `npm run build` 0 erros (4 execuções reais);
- B6 (segurança/privacidade verificadas): atendido — é o próprio foco da sprint; verificado por integração real (curl) e revisão cruzada de 2 agentes independentes, com 2 achados de segurança reais corrigidos antes do fechamento (contaminação de cache backend-side prevenida por design original; contaminação de cache frontend-side corrigida em 3 rodadas).

### C. Documentação e estado do repositório
- C1 (snapshot desta execução existe): atendido — ver snapshot GOV-005 (adendo de fechamento);
- C2 (sprint/dashboard/registros refletem mesmo estado): atendido — dashboard e `latest_execution.md` atualizados nesta mesma execução;
- C3 (working tree registrado): atendido — ver §10 real;
- C4/C5 (README/links revisados): atendido — `core/README.md`, `openapi.yaml` atualizados; validação de links da governança executada no fechamento;
- C6 (última execução ≠ baseline validado): atendido — nenhuma promoção de baseline ocorreu nem foi sugerida.

### D. Autoridade
- D1 (delegação/revisão só se ocorreram): atendido — cada revisão cruzada tem agente, comando e resultado registrados; nenhuma autorrevisão apresentada como independente;
- D2 (nenhuma decisão atribuída a Rafael sem manifestação): atendido — o fechamento é apresentado para homologação, não presumido;
- D3 (exceções críticas): a limitação de validação visual, originalmente registrada em §15.2, foi **sanada no saneamento de 2026-09-23** (snapshot [`EXEC-2026-09-23-05`](../snapshots/snapshot_EXEC-2026-09-23-05_AV-S01-saneamento.md) §3) — os 4 sub-casos de AC-03 foram confirmados por evidência visual real em navegador. Não há mais exceção pendente sobre este item;
- D4 (commit/push/deploy): não aplicável — nenhum ocorreu.

**Resultado desta sprint (atualizado após o saneamento de 2026-09-23, snapshot `EXEC-2026-09-23-05`): concluída com um débito residual, sem lacuna de evidência**, não "concluída" sem ressalva:
- **débito:** `DEBT-AV-009` (suíte do AI Engine incompatível com `AI_ENGINE_MODE=simulated` global — pré-existente, não causado por esta sprint; causa raiz agora documentada: falha de isolamento de 2 testes que não fixam `settings.ai_engine_mode="real"` explicitamente, não defeito do produto);
- **lacuna de evidência anteriormente registrada (AC-03, validação visual):** **sanada** — ver snapshot `EXEC-2026-09-23-05` §3; os 4 sub-casos foram confirmados com evidência visual real em navegador (Chrome real via CDP + Playwright), sem nenhuma falha encontrada;
- **2 achados de segurança reais foram encontrados e corrigidos** durante a própria execução original (não após), confirmando o valor da revisão cruzada exigida por Rafael;
- justificativa completa em §15.1/§15.2 (execução original) e no snapshot `EXEC-2026-09-23-05` §3 (saneamento); não classificar como "reprovada" — os 6 itens do backlog foram implementados, testados e revisados, e a única lacuna de evidência identificada no fechamento original foi resolvida no saneamento subsequente, dentro do mesmo escopo já autorizado;
- **homologação do fechamento (incluindo o saneamento) registrada por Rafael em 2026-09-23** — `DEBT-AV-009` explicitamente aceito como débito residual aberto; nenhuma autorização de commit/push/tag/deploy, promoção de baseline ou próxima sprint foi concedida.

## 17. Homologação de Rafael (2026-09-23)

Rafael homologou explicitamente o fechamento completo da `AV-S01`, incluindo a execução original e o saneamento [`EXEC-2026-09-23-05`](../snapshots/snapshot_EXEC-2026-09-23-05_AV-S01-saneamento.md). A homologação registra, sem ampliar o escopo:

- AC-03 atendido pela validação em navegador real, nos 4 subcasos; evidências versionadas em [`../evidence/AV-S01/`](../evidence/AV-S01/):
  - [`ac03_a_sem_contexto_local.png`](../evidence/AV-S01/ac03_a_sem_contexto_local.png);
  - [`ac03_b_sem_contaminacao_cache.png`](../evidence/AV-S01/ac03_b_sem_contaminacao_cache.png);
  - [`ac03_c_redirect_login.png`](../evidence/AV-S01/ac03_c_redirect_login.png) e [`ac03_c_retorno_pos_login.png`](../evidence/AV-S01/ac03_c_retorno_pos_login.png);
  - [`ac03_d_bloqueio_sem_permissao.png`](../evidence/AV-S01/ac03_d_bloqueio_sem_permissao.png);
- `DEBT-AV-010` resolvido;
- `DEBT-AV-009` aberto e aceito como débito residual, com correção de isolamento dos testes a priorizar na próxima sprint elegível;
- validação da IA realizada em modo simulado nesta execução; nenhuma revalidação da inferência real/Ollama foi alegada;
- Claude Code indisponível por OAuth expirado; autoria/revisão efetiva preservada: Codex implementou backend e revisou frontend em 3 rodadas; Antigravity CLI implementou frontend e revisou backend/contrato; Hermes consolidou, reproduziu as validações, aplicou o guard final do frontend e conduziu o saneamento visual/investigação de `DEBT-AV-009`;
- serviços/processos iniciados no saneamento (Core porta 8000, AI Engine porta 8001, Vite porta 5173 e Chrome CDP porta 9333) foram encerrados; verificação final por `lsof`/`ps` não encontrou listeners/processos relacionados ativos;
- dados fictícios adicionados ao Postgres local `avalia_dev` permanecem: professor `professor.b.demo@avalia-platform.example`; respostas fictícias `dceacb38-0293-4548-9c44-ae7464aaa1e0` e `cdbadae4-d995-4699-a73a-e387d90a5927`; jobs simulados `1683329d-3bcb-4789-8ef2-3797de63fdb5` e `1a75827e-4938-44dc-9ada-8062de0e4720`, ambos `SUGERIDA`. Nenhum token/senha foi versionado; temporários sensíveis foram removidos de `/tmp`.

Esta homologação **não autoriza** commit, push, tag, deploy, promoção automática de baseline nem início de outra sprint. O planejamento da próxima sprint é apresentado separadamente para aprovação.
