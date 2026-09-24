---
id: "AV-S02"
status: implementada_local_aguardando_ci_remota
objetivo_aprovado_por: "Rafael (2026-09-23, aprovação do plano com 4 condições e 5 refinamentos de execução)"
consolidador: "Hermes"
baseline_entrada: "../snapshots/latest_validated_baseline.md (nenhum promovido — AV-S01 homologada não promoveu baseline)"
---

# AV-S02 — CI mínima, validação visual do fluxo central e isolamento dos testes do AI Engine

> Plano proposto após a homologação de `AV-S01`. **Nenhuma execução está autorizada por este documento.** A aprovação solicitada ao final cobre o plano e o escopo; commit, push, tag, deploy e promoção de baseline permanecem sujeitos a autorização específica separada. A CI remota não pode ser observada sem uma ação Git/remota posterior — ver gate em §13.

## 1. Objetivo e valor esperado

Concluir a Etapa 1 (consolidação do fluxo existente) com três resultados observáveis e independentes:

1. uma CI mínima versionada que execute automaticamente as verificações existentes do Core, AI Engine e frontend;
2. evidência visual atual e documentada do fluxo central completo da interface, com IA em modo **simulado** e dados fictícios, sem alegar inferência real;
3. saneamento de `DEBT-AV-009`, isolando os dois testes do caminho real de reparo de JSON da variável global `AI_ENGINE_MODE`, sem alterar RN-017 nem enfraquecer expectativas.

Valor esperado: a saúde técnica deixa de depender exclusivamente de comandos manuais; o fluxo central ganha evidência visual completa; e a suíte do AI Engine passa a ser reprodutível tanto no ambiente padrão quanto com `AI_ENGINE_MODE=simulated` global.

## 2. Elegibilidade e dependências reais

A próxima sprint elegível é `AV-S02`, não `AV-S03`, porque:

- a proposta vigente coloca `AV-S02` ainda na Fase 1, imediatamente após `AV-S01`;
- sua única dependência de código, `AV-S01` (base estabilizada), foi executada, saneada e homologada por Rafael em 2026-09-23;
- `AV-S03` inicia estrutura acadêmica e amplia produto/modelo de dados, enquanto `AV-S02` fecha débitos de consolidação e automação ainda abertos (`DEBT-AV-004`, `005`, `009`);
- nenhuma decisão sobre OCR, CSV, hardware, retenção de dados reais ou estrutura acadêmica é necessária para os três itens desta sprint;
- decisões abertas não são tratadas como bloqueantes universais: `DEC-AV-007`, `009`, `012`, `013`, `017`, `019`, `020` não bloqueiam esta sprint.

Dependências reais por item:

| Item | Dependência real | Estado |
|---|---|---|
| BL-AV-1-05 | serviços locais funcionais + definição do ambiente-alvo da evidência (`DEC-AV-006`) | proposta deste plano: **ambiente local do executor, com dados fictícios e IA simulada**; a aprovação deste plano registra essa decisão apenas para AV-S02, sem decidir piloto/homologação compartilhada |
| BL-AV-1-06 | comandos de teste/build estáveis; GitHub Actions disponível; execução remota exige workflow alcançar o remoto | comandos conhecidos; criação/validação local pode começar após aprovação; **commit/push posterior exige autorização específica de Rafael** |
| BL-AV-1-09 | causa raiz de `DEBT-AV-009` conhecida | atendida por `EXEC-2026-09-23-05`; sem decisão de produto pendente; não depende de Ollama real |

## 3. Origem

| Fonte/requisito | Trecho ou decisão aplicável | Link |
|---|---|---|
| BL-AV-1-05 / DEBT-AV-004 | validação visual documentada do fluxo central | [`backlog_tecnico_avalia.md`](../backlog/backlog_tecnico_avalia.md) §3 |
| BL-AV-1-06 / DEBT-AV-005 | CI mínima versionada | [`backlog_tecnico_avalia.md`](../backlog/backlog_tecnico_avalia.md) §3 |
| BL-AV-1-09 / DEBT-AV-009 | isolamento dos 2 testes do caminho real contra `AI_ENGINE_MODE=simulated` global | [`technical_debts.md`](../registers/technical_debts.md), `EXEC-2026-09-23-05` §4 |
| Homologação de AV-S01 | incluir a correção de `DEBT-AV-009` na próxima sprint elegível; não iniciar antes de aprovação | [`decisions.md`](../registers/decisions.md), `DEC-AV-003` |
| Roteiro visual | fluxo login → avaliação → rubrica → publicação → resposta → correção → revisão | [`docs/roteiro-apresentacao-supervisor.md`](../../roteiro-apresentacao-supervisor.md) §3 |

Lacunas de fonte: nenhuma. O modo de inferência da evidência visual desta sprint é explicitamente simulado; inferência real/Ollama permanece fora do escopo e não será alegada.

## 4. Escopo

Incluído:

- BL-AV-1-05: executar o fluxo visual central completo, com navegador real e dados fictícios:
  - login;
  - criação de avaliação/questão;
  - criação e validação de rubrica;
  - publicação;
  - envio de resposta fictícia;
  - acompanhamento do job;
  - revisão humana e persistência da decisão;
  - evidência visual por etapa, sem tokens/senhas;
- BL-AV-1-06: criar CI mínima em GitHub Actions para:
  - Core: suíte `pytest` existente;
  - AI Engine: suíte padrão + suíte com `AI_ENGINE_MODE=simulated` global após o isolamento de BL-AV-1-09;
  - frontend: `npm ci` + `npm run build`;
  - validação estática do workflow (YAML/actionlint, se disponível) antes de qualquer ação remota;
- BL-AV-1-09: fixar explicitamente o modo real apenas nos 2 testes que validam o caminho LLM/reparo e confirmar a cobertura do ramo simulado;
- documentação dos comandos oficiais e classificação de evidência;
- revisão cruzada por autor distinto;
- atualização de snapshot/dashboard/registros/closure gate.

Fora de escopo:

- inferência real/Ollama e alegações de qualidade pedagógica da IA;
- dados reais de alunos;
- infraestrutura/backup/recuperação (`DEBT-AV-008`);
- deploy, release, tag ou promoção de baseline;
- correção de warnings de Pydantic/React Router ou refatorações não relacionadas;
- estrutura acadêmica (`AV-S03`), OCR, CSV e qualquer sprint posterior;
- commit/push automático: mesmo se a sprint for aprovada, o diff e o staged diff serão apresentados a Rafael antes de qualquer commit/push, conforme a governança.

## 5. Baseline e estado de abertura

- último baseline validado: nenhum (`BASELINE-001` permanece candidato);
- última execução: [`EXEC-2026-09-23-05`](../snapshots/snapshot_EXEC-2026-09-23-05_AV-S01-saneamento.md), homologada junto com `AV-S01`;
- branch/upstream/commit de referência: `main` / `origin/main` / `0be691e12e9d5d6f3ffc989237739f6559d8dacd` (confirmar novamente na abertura real);
- working tree: alterações não staged e não commitadas de AV-S01/governança; preservar integralmente e não misturar ações Git;
- serviços ativos ao preparar este plano: nenhum listener/processo do saneamento nas portas 8000, 8001, 5173/5174, 9333;
- dados fictícios adicionais no `avalia_dev`: professor B, 2 respostas e 2 jobs simulados de AV-S01; podem ser reutilizados somente se isso não contaminar o roteiro — preferir fixtures/nova identificação datada para AV-S02;
- bloqueante de início: aprovação explícita deste plano por Rafael.

## 6. Backlog e DoR

| ID | Descrição | Responsável proposto | DoR | Estado |
|---|---|---|---|---|
| BL-AV-1-09 | Isolar 2 testes do caminho real do modo global do AI Engine | Codex (implementação) + Antigravity CLI (revisão) | ready — causa raiz, arquivo, expectativa e comandos definidos; nenhuma decisão pendente | planejado |
| BL-AV-1-06 | CI mínima versionada | Codex (workflow) + Antigravity CLI (revisão) | ready para implementação local; execução remota bloqueada até autorização Git específica | planejado |
| BL-AV-1-05 | Validação visual completa do fluxo central | Antigravity CLI (roteiro/execução) + Hermes (verificação independente) | ready **se Rafael aprovar neste plano o ambiente local + IA simulada como alvo de AV-S02** | planejado |

DoR da sprint: parcialmente condicionado à decisão de ambiente acima. A aprovação do plano com essa premissa torna os 3 itens `ready`; rejeição/alteração da premissa devolve BL-AV-1-05 a refinamento sem iniciar execução.

## 7. Mapa de impacto

| Item | Criar | Alterar | Não tocar |
|---|---|---|---|
| BL-AV-1-09 | opcional: fixture localizada em `ai-engine/tests/conftest.py`, somente se reduzir duplicação sem ampliar escopo | `ai-engine/tests/test_schema_repair_and_fallback.py` | `ai-engine/app/cascade.py`, RN-017, schemas/contratos de produto |
| BL-AV-1-06 | `.github/workflows/ci.yml` (nome final sujeito à convenção encontrada na abertura); opcional config mínima de actionlint somente se necessária | README aplicável para documentar comandos oficiais | workflows de deploy/release; infra de produção |
| BL-AV-1-05 | `docs/governance/evidence/AV-S02/` (capturas); roteiro de execução/evidência no snapshot | `docs/roteiro-apresentacao-supervisor.md` apenas se a execução real divergir do roteiro atual; caso contrário registrar “sem alteração” | dados reais, segredos, histórico visual de AV-S01 |
| Governança | snapshot de execução/fechamento de AV-S02 | sprint, dashboard, débitos, decisões se aplicável | baseline validado sem decisão de Rafael |

Mudança fora deste mapa exige registro antes da edição; ampliação relevante volta a Rafael.

## 8. Delegação e revisão independente

| Item | Executor | Revisor distinto | Evidência esperada |
|---|---|---|---|
| BL-AV-1-09 | Codex | Antigravity CLI | diff mínimo; testes direcionados; 2 suítes completas (default/simulado global); parecer sobre preservação das expectativas |
| BL-AV-1-06 | Codex | Antigravity CLI | workflow + validação local; parecer sobre segurança, cache/dependências e ausência de deploy/secrets desnecessários |
| BL-AV-1-05 | Antigravity CLI | Hermes | capturas reais por etapa; logs sem token; reprodução independente de amostra crítica por Hermes |
| Consolidação | Hermes | — | coerência entre sprint, snapshot, dashboard, débitos e evidências |

**Origem do aviso de fallback ("claude-sonnet-5 via anthropic unavailable; using gpt-5.6-sol via openai-codex"): NÃO CONFIRMADA.** Hermes investigou logs de sessão desta máquina e não encontrou nenhuma ocorrência textual exata desse aviso nos artefatos verificáveis. A hipótese anterior — de que o fallback ocorreu na execução delegada ao Claude Code, não no modelo de orquestração do próprio Hermes — é **compatível** com os metadados observados (sessões `claude-sonnet-5`/`firstParty` quando o Claude Code estava disponível; cabeçalhos `gpt-5.6-sol`/`openai` em toda chamada ao Codex, que é o comportamento normal e esperado dessa ferramenta, não um fallback dela). Mas ausência de registro do aviso nos logs e compatibilidade com uma hipótese não constituem prova de em qual camada o fallback ocorreu. Esta incerteza é registrada como tal — separada da execução efetivamente comprovada do Claude Code nesta sprint (2 revisões independentes reais, com testes empíricos próprios, nesta mesma janela em que a ferramenta esteve disponível: `claude -p "ok"` → `ok`; `claude auth status` → `loggedIn: true`, `firstParty`, `pro`, CLI `2.1.260`).

### 8.1 Auditoria de banco por evidência (exigência explícita de Rafael, 2026-09-24)

Nenhuma evidência anterior a esta seção usou PostgreSQL, salvo indicação contrária:

| Evidência | Banco realmente usado | Observação |
|---|---|---|
| Suíte pytest completa (`test_core_flow.py`, `test_review_idempotency.py`, `test_authorization_boundaries.py`) | **SQLite** em arquivo temporário (`tmp_path`, fixture `test_engine` em `conftest.py:20-23`) | Nunca foi Postgres; `postgres:16` do `ci.yml` não é exercitado pelos testes atuais (já registrado em §19.3 antiga do documento) |
| Migração isolada anterior (deduplicação 3→1, versão rejeitada por Rafael) | **SQLite** isolado (`tmp`) | Nunca testada em Postgres na época — lacuna que motivou a exigência do item 2 de Rafael |
| Validação visual pós-fix AC-04/AC-10 (`docs/governance/evidence/AV-S02-final/`, Chrome real via CDP/Playwright) | **PostgreSQL — `avalia_dev` operacional local**, via serviços reais (`uvicorn` do Core apontando para `.env`/`DATABASE_URL=postgresql+psycopg2://localhost:5432/avalia_dev`) | Esta evidência específica JÁ usava Postgres real (o `avalia_dev` de desenvolvimento local), não SQLite — mas não um ambiente isolado dedicado: o job fictício `d3c7335e-...` foi criado no mesmo banco de desenvolvimento onde já residiam os 3 duplicados legados. Nenhum dado alheio foi tocado, mas não atende à exigência de "PostgreSQL isolado" do item 2 de Rafael para os testes de idempotência/migração |
| Migração reescrita (versão atual, sem deduplicação automática) — testes de abort-sem-perda | **SQLite isolado** (Hermes, autor) **e PostgreSQL 16 isolado e descartável** (`/tmp/av_pg_isolated`, porta 55432, cluster criado via `initdb`/`pg_ctl` só para esta verificação, nunca `avalia_dev`) — confirmado independentemente por Claude Code (cluster Postgres temporário próprio) | Primeira evidência desta sprint em Postgres genuinamente isolado, atendendo à exigência do item 2 |
| Reenvio equivalente / decisão conflitante / concorrência (10 e 6 threads reais) | **PostgreSQL 16 isolado e descartável** (mesmo cluster `/tmp/av_pg_isolated`), via aplicação real (`uvicorn`) e requisições HTTP reais (`httpx`, threads de verdade, não mocks) | Nova evidência desta fatia; resultado idêntico ao observado em SQLite (1 revisão por job sob concorrência real) |

**Conclusão da auditoria:** a validação visual pós-correção (AC-04/AC-10) usou Postgres real, mas o `avalia_dev` de desenvolvimento, não um ambiente isolado — não deve ser tratada como equivalente à validação isolada exigida pelo item 2 de Rafael para a migração/idempotência. As validações de migração e de idempotência sob concorrência desta fatia (2026-09-24, tarde) SÃO em PostgreSQL genuinamente isolado, atendendo à exigência.



| ID | Critério | Método | Estado |
|---|---|---|---|
| AC-01 | Os 2 testes de reparo preservam integralmente as expectativas atuais (reparo uma vez/sucesso com flag; reparo inválido/HTTP 502) e isolam explicitamente `settings.ai_engine_mode="real"` | pytest direcionado + revisão de diff | **atendido** — diff de 2 linhas (`monkeypatch.setattr(settings, "ai_engine_mode", "real")`) em cada teste; asserções originais intactas; revertido automaticamente ao fim de cada teste; aprovado incondicionalmente por Antigravity CLI |
| AC-02 | Suíte AI Engine passa no ambiente padrão e com `AI_ENGINE_MODE=simulated` global, sem alteração de comportamento de produção ou enfraquecimento de expectativas | `pytest -q`; `AI_ENGINE_MODE=simulated pytest -q` | **atendido** — 21/21 em ambos os ambientes, reexecutado independentemente por Hermes; `app/cascade.py` não foi tocado |
| AC-03 | Workflow CI mínimo executa Core, AI Engine (dois ambientes) e frontend build, sem deploy e sem segredos de produção | validação local + execução real no GitHub Actions após autorização Git específica | **implementado e validado localmente; execução remota NÃO realizada nesta sessão** — YAML válido com 3 jobs (`core`, `ai-engine`, `frontend`), cada um com lint antes de testes/build: Ruff (E/F/I, `ruff.toml`) para Core+AI Engine e ESLint flat config mínimo para frontend; todos os comandos exatos da CI foram reexecutados por Hermes, Antigravity CLI e Claude Code e passaram (Ruff 0+0, ESLint 0, Core 42/42, AI Engine 21/21 nos dois modos, frontend build limpo); sem deploy/release/publish/secrets. **`DEBT-AV-005` permanece aberto até execução real no GitHub Actions** |
| AC-04 | Fluxo visual central completo funciona em navegador real com dados fictícios e IA simulada: login → avaliação/rubrica/publicação → resposta → job → revisão persistida | visual + integração real | **atendido após correção e revalidação real (2026-09-24)** — novo fluxo completo executado em Chrome real via CDP + Playwright com job fictício novo (`d3c7335e-419e-4d72-90c2-dbde7100c42c`): primeira decisão registrada; após reload e reabertura direta (cache de workflow removido), a tela exibiu "Revisão concluída"/"Decisão humana já registrada", autor, data e nota; contagem dos botões "Aprovar"/"Alterar" = 0; screenshot em `docs/governance/evidence/AV-S02-final/02_reabertura_decisao_somente_leitura.png` |
| AC-07 (novo, `BL-AV-1-10`) | Reenvio semanticamente equivalente pelo mesmo revisor não cria nova `HumanReview`; retorna a decisão existente | teste de integração real (2 requisições HTTP idênticas ao mesmo job) | **atendido** — `test_equivalent_retry_returns_existing_review_without_duplicate_or_audit`: reenvios `ALTER` com score `7.0`/`7.00` retornam o mesmo `id`, persistem 1 `HumanReview` e 1 `AuditEvent`; 42/42 testes Core passaram após revisão |
| AC-08 (novo, `BL-AV-1-10`) | Decisão diferente sobre job já revisado retorna 409, preservando a decisão original | teste de integração real | **atendido** — `test_different_decision_returns_conflict_and_preserves_original` + testes adicionais de justificativa em `APPROVE`; resposta 409 usa `HumanReviewSummaryOut` completo (e-mail/scores) |
| AC-09 (novo, `BL-AV-1-10`) | Sob concorrência (2 requisições simultâneas), apenas 1 `HumanReview` é persistida para o job | teste de integração real com requisições concorrentes | **atendido, validado em SQLite E em PostgreSQL isolado real (2026-09-24)** — suíte pytest (`test_review_idempotency.py`) usa `Barrier` + threads sobre SQLite: 1 revisão/1 auditoria. **Adicionalmente**, Hermes rodou a aplicação real (uvicorn) contra um cluster PostgreSQL 16 isolado e descartável (`/tmp/av_pg_isolated`, porta 55432, nunca `avalia_dev`): 10 threads reais disparando POST simultâneo idêntico → 1 única `HumanReview` persistida (log `human_review_registered` 1x); e 6 threads com decisões alternadas APPROVE/ALTER → 3×200 (equivalentes) + 3×409 (conflitantes), 1 única linha final no banco. Confirmado por consulta SQL direta ao Postgres isolado, não apenas pelo HTTP status |
| AC-10 (novo, `BL-AV-1-10`) | UI recupera e mostra a decisão persistida (autor, data, nota, justificativa quando houver) ao reabrir a revisão, sem oferecer o formulário de primeira aprovação novamente | visual + integração real | **atendido após correção e revalidação visual real** — screenshot e assertivas Playwright confirmam autor/data/nota/decisão, título somente leitura e ausência total dos botões de primeira decisão |
| AC-05 | Evidência distingue IA simulada de inferência real; nenhuma alegação de qualidade/latência do modelo real | inspeção do registro e screenshots | **atendido** — captura `06_revisao_sugestao_ia_simulada.png` mostra o banner "Análise em modo simulado" explícito na UI; `engine_mode=simulated`/`SIMULATED_MODE` confirmados via API; nenhuma menção a Ollama real nesta sprint |
| AC-06 | Nenhum dado real/token/senha aparece em logs, capturas ou artefatos versionados | inspeção + revisão cruzada | **atendido** — senha lida de `.env` para arquivo `/tmp` com permissão 600, nunca impressa em stdout, removida ao final; capturas mostram apenas e-mail de demonstração, nunca senha/token |

**Achado adicional não previsto nos critérios de aceite (registrado por transparência, não é falha de AC-04/05/06):** durante a execução de AC-04, ao testar a persistência da decisão humana após reload/reabertura (refinamento explícito de Rafael), foi descoberto que a revisão humana não é idempotente — ver `DEBT-AV-011`/`BL-AV-1-10` no registro de débitos. Isso não invalida AC-04 (o fluxo visual funciona; a decisão fica persistida no banco), mas revela uma lacuna de integridade de dados que a validação visual foi desenhada para poder encontrar.

## 10. Definition of Done

- [x] AC-01, AC-02, AC-04, AC-05, AC-06, AC-07, AC-08, AC-10 avaliados com resultado real; AC-09 validado localmente em SQLite com ressalva de ambiente Postgres; AC-03 implementado/validado localmente, execução remota pendente de autorização Git;
- [x] `DEBT-AV-009` resolvido tecnicamente (ambos os ambientes da suíte passam; revisão confirmou isolamento correto) — permanece formalmente `aberto` no registro até homologação do fechamento completo desta sprint;
- [ ] `DEBT-AV-005` **não resolvido nesta sessão** — apenas criação/validação local do YAML; requer execução real do workflow remoto, sujeita a autorização Git específica ainda não concedida;
- [x] `DEBT-AV-004` resolvido — fluxo central completo visualmente registrado com 10 capturas reais;
- [x] nenhuma inferência real alegada — toda a validação usou `AI_ENGINE_MODE=simulated`, rotulado explicitamente na UI e nas evidências;
- [x] revisão independente registrada por autor distinto em cada item (Antigravity CLI revisou BL-AV-1-09; Codex revisou BL-AV-1-06 e a correção de whitespace; Antigravity CLI revisou a correção dos comentários do YAML; Antigravity CLI confirmou o achado de idempotência);
- [x] evidências visuais versionadas sem segredos (`docs/governance/evidence/AV-S02/`);
- [x] snapshot, dashboard, sprint e registros canônicos atualizados;
- [x] closure gate preenchido (§18) — **parcial**, pela pendência explícita de AC-03/`DEBT-AV-005`;
- [ ] homologação de Rafael registrada somente se ocorrer — pendente, apresentado nesta execução para essa decisão;
- [x] nenhum commit/push/tag/deploy/baseline sem autorização específica — nenhum ocorreu nesta sessão.

## 11. Validações previstas

| Item/AC | Comando/procedimento | Ambiente | Tipo |
|---|---|---|---|
| BL-AV-1-09 | `.venv/bin/pytest tests/test_schema_repair_and_fallback.py -v` | AI Engine local, mocks explícitos | automatizada/simulação |
| BL-AV-1-09 | `env -u AI_ENGINE_MODE .venv/bin/pytest -q` | `.venv` do AI Engine | automatizada |
| BL-AV-1-09 | `AI_ENGINE_MODE=simulated .venv/bin/pytest -q` | `.venv` do AI Engine | automatizada/modo simulado explícito |
| BL-AV-1-06 | parser YAML + actionlint (se disponível) | local | automatizada/estática |
| BL-AV-1-06 | execução GitHub Actions | remoto, apenas após aprovação Git | automatizada/integração real remota |
| BL-AV-1-05 | roteiro §3 do documento do supervisor, adaptado para modo simulado explicitamente rotulado | Chrome isolado + Core/Postgres/AI Engine/Vite locais | visual + integração real + simulação da IA |
| regressão | Core pytest + frontend build | ambientes locais existentes | automatizada |

## 12. Riscos e mitigação

| Risco | Probabilidade/impacto | Mitigação | Dono |
|---|---|---|---|
| CI usar modo simulado e acidentalmente não testar o caminho real de reparo | média/alta | dois jobs/ambientes explícitos; testes do caminho real fixam modo localmente; revisão cruzada | Codex + revisor |
| alterar expectativa só para obter verde | baixa/alta | proibição explícita; AC-01 exige chamadas/HTTP/flags atuais intactos | Hermes |
| workflow existir sem nunca rodar | média/média | `DEBT-AV-005` só fecha com execução remota real; gate Git separado e honesto | Rafael/Hermes |
| evidência visual ser confundida com inferência real | média/alta | banner/registro `engine_mode=simulated`; AC-05; nenhuma comparação de qualidade | executor/revisor |
| uso de dados fictícios persistentes contaminar roteiro | média/baixa | identificadores datados; registrar dados criados e limpeza/opção de retenção | Hermes |
| working tree já contém AV-S01 não commitada | alta/média | preservar paths; apresentar diff exato antes de qualquer Git; nenhum reset/stash unilateral | todos |
| Claude Code continuar indisponível | média/baixa | reconfirmar; manter revisão cruzada Codex↔Antigravity e verificação Hermes | Hermes |

## 13. Gates e critérios de encerramento

1. **Gate de aprovação do plano:** Rafael decide se aprova `AV-S02` com os 3 itens e o ambiente local + IA simulada para BL-AV-1-05. Sem aprovação, nada é executado.
2. **Gate Git/remoto:** a aprovação deste plano **não** autoriza commit/push. Quando o workflow e demais mudanças estiverem prontos, Hermes apresenta diff e staged diff exatos; Rafael decide separadamente sobre commit/push necessários para observar GitHub Actions.
3. Sem execução remota do workflow, BL-AV-1-06 fica implementado/validado localmente, mas não validado em CI; `DEBT-AV-005` não fecha e a sprint não pode ser declarada concluída sem ressalva.
4. Inferência real/Ollama não integra o critério de aceite desta sprint. Qualquer teste real futuro será escopo separado e explicitamente classificado.
5. Aplicar o closure gate geral; homologação final é decisão separada de Rafael.

## 14. Estimativa

Método: complexidade qualitativa por item e número de integrações, sem velocity histórica suficiente. Tamanho proposto: **P/M** — alteração pequena de testes; workflow CI moderado por exigir matriz e validação remota; validação visual exige execução coordenada de 4 serviços e evidências. Estimativa não é compromisso de prazo.

## 15. Decisões solicitadas a Rafael para aprovação

Ao aprovar este plano, Rafael estaria decidindo exclusivamente:

1. autorizar a execução de `AV-S02` com BL-AV-1-05, BL-AV-1-06 e BL-AV-1-09;
2. aceitar o ambiente local do executor, dados fictícios e IA simulada como alvo da validação visual de BL-AV-1-05 nesta sprint (decisão restrita à AV-S02; não resolve o ambiente de piloto/homologação final em geral);
3. aceitar que a CI inclua dois ambientes do AI Engine (default + `AI_ENGINE_MODE=simulated` global) e que `DEBT-AV-009` só feche com ambos verdes sem expectativa enfraquecida;
4. manter commit/push/tag/deploy/promoção de baseline fora desta aprovação, sujeitos a gate posterior específico.

Estado atual: **aprovado por Rafael em 2026-09-23, com os 4 pontos confirmados e 5 refinamentos de execução adicionais (isolamento por override temporário/restaurado; validação de persistência da decisão após reload/reabertura; correção do whitespace + `git diff --check` global; vínculo explícito BL-AV-1-09↔DEBT-AV-009 e origem do aumento 68→69; reconfirmação de agentes com distribuição sem sobreposição e revisão cruzada, incluindo revisão das próprias correções de Hermes). Execução local concluída; etapa remota aguardando autorização específica.**

## 16. Ajustes de percurso

| Data/fuso | Mudança | Motivo | Impacto | Decisão/autorização |
|---|---|---|---|---|
| 2026-09-23T19:58-03:00 | Correção do comentário do YAML de CI ("SQLite em memória" → "SQLite em arquivo temporário tmp_path") + explicitação de que o serviço `postgres:16` não é exercitado pelos testes atuais | achado real da revisão cruzada de Codex (item 5 do seu parecer); comentário anterior era factualmente impreciso | nenhuma mudança funcional no workflow, apenas 2 comentários corrigidos | correção rotineira de precisão documental por Hermes, dentro da autorização geral; reconfirmada por Antigravity CLI |
| 2026-09-23T22:55-03:00 | Descoberta de `DEBT-AV-011` (falta de idempotência em `POST /v1/corrections/{job_id}/reviews`) durante o refinamento de Rafael sobre validar persistência da decisão após reload/reabertura | achado real, não hipotético, reproduzido 3x (Playwright, curl, leitura de código por Antigravity CLI) | nenhuma correção aplicada (fora do escopo autorizado desta sprint); registrado como `BL-AV-1-10`/`DEBT-AV-011` para decisão de política por Rafael antes de priorizar | registro obrigatório de achado real; nenhuma decisão de produto tomada por Hermes |
| 2026-09-23T23:00-03:00 | Ambiente local (Chrome CDP, Core, AI Engine, Vite) encerrado ao final da validação visual | disciplina operacional — não deixar serviços/processos órfãos entre sessões | nenhum | rotina de encerramento, confirmada por `lsof`/`ps` |
| 2026-09-24T05:2x-03:00 | **Incorporação de `BL-AV-1-10` ao escopo de `AV-S02`** (política de decisão humana única por `CorrectionJob`) | achado real de `DEBT-AV-011` classificado por Rafael como corrigível dentro desta sprint, não em sprint futura | escopo ampliado com contrato, mapa de impacto e critérios de aceite próprios (ver §6.4/§8 revisados abaixo); nenhuma mudança de rota/contrato fora do necessário para a idempotência | decisão explícita de Rafael, registrada nesta linha antes de qualquer implementação |
| 2026-09-24T05:2x-03:00 | Diagnóstico dos 3 registros duplicados existentes no `human_reviews` do banco local (`job_id=4f56a10b...`) | instrução explícita de Rafael de diagnosticar antes de qualquer saneamento | as 3 linhas são **idênticas em conteúdo** (mesmo `reviewer_id`, `decision=APPROVE`, mesmos `final_scores_json`, mesmo `final_total`), diferindo apenas em `id`/`created_at` — são reenvios semanticamente equivalentes do mesmo revisor, não decisões conflitantes; nenhum caso de conflito real existe nestes dados fictícios de teste | nenhuma exclusão ou escolha foi feita; os 3 registros são preservados como estão até decisão específica de saneamento (fora do escopo desta sprint, que não aplica migração no banco operacional) |

### 6.4 Contrato revisado — política de decisão humana única (ajuste incorporado em 2026-09-24)

**Regra de negócio (aprovada por Rafael):**
- Uma única decisão humana final por `CorrectionJob`.
- Reenvio **semanticamente equivalente** (mesmo `reviewer_id`, mesma `decision`, mesmos `final_scores` por critério, mesma `justification` quando aplicável) pelo mesmo revisor retorna a decisão já existente — HTTP 200, sem criar nova linha em `human_reviews`, sem novo `AuditEvent` de aprovação.
- Tentativa de registrar decisão **diferente** sobre um job já revisado retorna **HTTP 409 Conflict**, preservando a decisão existente inalterada.
- A regra vale sob concorrência: dois requests simultâneos não podem ambos criar `HumanReview` para o mesmo `job_id` — proteção por `UniqueConstraint(job_id)` no banco (nível transacional), não apenas checagem em nível de aplicação.
- Alteração posterior de uma nota já decidida (correção de erro do próprio professor) é **fora de escopo desta sprint** — exige fluxo explícito e auditável a ser desenhado separadamente (novo item de backlog, não implementado aqui).

**Contrato do endpoint `POST /v1/corrections/{job_id}/reviews` (revisado):**
```
200 OK   — reenvio equivalente à decisão existente: retorna a HumanReview já persistida (sem side-effect novo)
201/200  — primeira decisão para o job: cria e retorna a nova HumanReview (mantém o código de status já existente antes desta correção)
409 CONFLICT — decisão diferente da já registrada: retorna a decisão existente no corpo do erro, sem persistir a nova tentativa
403/404/422 — inalterados (autorização por vínculo, job/rubrica ausente, decisão inválida)
```

**Novo endpoint de leitura (necessário para a UI mostrar a decisão persistida sem reoferecer o formulário):** o contrato de leitura (`GET /v1/correction-jobs/{job_id}/context` ou um novo campo agregado) passa a incluir a `HumanReview` já registrada, se existir, com `reviewer_id`/e-mail, `created_at`, `final_total`, `final_scores` e `justification` — para a UI decidir entre "mostrar formulário de decisão" e "mostrar decisão já registrada, somente leitura".

**Migração de banco (versão atual, corrigida em 2026-09-24 à tarde, após rejeição explícita de Rafael da versão anterior):** Rafael determinou que a migração NÃO pode apagar, alterar ou escolher automaticamente entre duplicatas — a versão anterior (que deduplicava mantendo a mais antiga) foi explicitamente proibida. Hermes (autor desta versão) reescreveu `core/alembic/versions/7b1d6d853f20_add_unique_human_review_job_id.py`: a migração agora apenas **detecta** duplicatas (`SELECT ... GROUP BY job_id HAVING COUNT(*) > 1`, com `GROUP_CONCAT` em SQLite ou `STRING_AGG` em Postgres conforme `connection.dialect.name`) e, se encontrar alguma, **levanta `RuntimeError`** com diagnóstico (job_id, contagem, ids), sem nenhuma escrita. Só cria a `UniqueConstraint` quando não há duplicatas.

**Validação (item 2 de Rafael — PostgreSQL isolado, não apenas SQLite):** Hermes provisionou um cluster PostgreSQL 16 isolado e descartável (`initdb`/`pg_ctl`, diretório `/tmp/av_pg_isolated`, porta 55432, socket próprio — nunca `avalia_dev`) e validou: (a) sem duplicatas, a migração completa e cria a constraint; (b) com 3 duplicatas fictícias inseridas manualmente para um `job_id` de teste, a migração aborta com `RuntimeError`, as 3 linhas permanecem intactas, `alembic_version` não avança, a constraint não é criada. **Revisão independente por agente distinto do autor:** Claude Code (`claude-sonnet-5`, disponível nesta janela) leu o arquivo linha a linha e reexecutou os mesmos testes em SEU PRÓPRIO cluster PostgreSQL temporário e em SQLite, confirmando resultado idêntico nos dois motores; parecer: **aprovado incondicionalmente**, com observação não bloqueante sobre `models.py` já declarar a constraint no metadata SQLAlchemy (esperado, não é falha). Uma segunda tentativa de verificação por Antigravity CLI foi aberta, mas não progrediu em 20 minutos (travada em "localização do arquivo") e foi interrompida por Hermes — registrado como tentativa sem resultado, não como aprovação adicional.

**Testes de idempotência sob concorrência real em PostgreSQL isolado (item 2 de Rafael):** Hermes subiu a aplicação real (`uvicorn`, Core + AI Engine simulado) contra o mesmo cluster isolado e exercitou via HTTP real (não mock): reenvio equivalente (mesma decisão 2x) retorna a mesma linha; decisão conflitante retorna 409 preservando a original; 10 threads reais disparando a mesma decisão simultaneamente resultam em exatamente 1 `HumanReview` (log da aplicação `human_review_registered` ocorre 1 única vez); 6 threads com decisões alternadas (APPROVE/ALTER) resultam em 3×200 + 3×409 e 1 única linha final no banco — confirmado por consulta SQL direta.

**Auditoria de banco por evidência (item 2 de Rafael):** ver tabela na seção 8.1 acima. A validação visual pós-fix (AC-04/AC-10) usou o `avalia_dev` de desenvolvimento local (Postgres real, mas não isolado) — não deve ser confundida com a validação isolada exigida para migração/idempotência, que ocorreu em cluster totalmente separado.

O saneamento das 3 duplicatas legadas em `avalia_dev` (job `4f56a10b-...`) permanece **não executado**. Proposta separada, dependente de aprovação, em `docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md` — diferencia duplicatas equivalentes de conflitantes, exige backup e preserva rastreabilidade (move para tabela de arquivo em vez de `DELETE`).

## 17. Execução e review

**BL-AV-1-09 (Codex, implementação; Antigravity CLI, revisão):** diff de 2 linhas em `ai-engine/tests/test_schema_repair_and_fallback.py` — `from app.config import settings` + `monkeypatch.setattr(settings, "ai_engine_mode", "real")` em cada um dos 2 testes do caminho real. Codex reportou `pytest -q` = 21 passed e `AI_ENGINE_MODE=simulated pytest -q` = 21 passed; **Hermes reexecutou independentemente e confirmou os mesmos resultados**, incluindo execução direcionada dos 2 testes (`-v`, ambos PASSED). Antigravity CLI revisou o diff e o contexto (`app/cascade.py`, `app/config.py`) e emitiu **aprovação incondicional**, citando o mesmo padrão já usado em `tests/test_ollama_unavailable.py` e `tests/test_simulated_mode.py` (precedente do próprio projeto).

**BL-AV-1-06 (Antigravity CLI, implementação; Codex, revisão):** criado `.github/workflows/ci.yml` com 3 jobs (`core` com serviço `postgres:16` e comando idêntico ao documentado em `core/README.md`; `ai-engine` com 2 steps nomeados — padrão e `AI_ENGINE_MODE=simulated`; `frontend` com `npm ci`+`npm run build`). **Hermes validou independentemente** a sintaxe YAML (parser `PyYAML`, 3 jobs confirmados, ausência de jobs de deploy/release/publish). Codex revisou e emitiu **aprovação condicional**: achado real de que o item do backlog se chama "lint + testes" mas nenhum lint foi incluído — confirmado por Hermes que não há linter configurado no repositório (nenhum `.eslintrc*`/`ruff.toml`/`.flake8`/`pyproject.toml` com config de lint encontrado); e observação de que o serviço `postgres:16` não é exercitado pelos testes atuais (SQLite em `tmp_path`), classificada como over-engineering não bloqueante. Hermes corrigiu os 2 comentários factualmente imprecisos do YAML (não o comportamento); Antigravity CLI reconfirmou a correção como aprovada. **A divergência sobre lint não foi resolvida unilateralmente — fica registrada para decisão de Rafael** (adicionar lint fora de escopo desta sprint, ou aceitar a ausência de linter configurado como estado atual do projeto).

**Whitespace em `ReviewPage.tsx:25` (Hermes, correção; Codex, revisão):** removidos 2 espaços em branco em linha vazia. `git diff --check` local e depois **global no repositório inteiro**: sem nenhum erro. Codex revisou o diff isolado e confirmou que nenhuma mudança funcional foi introduzida além da remoção do whitespace, comparando com o diff já existente de AV-S01 (revisado anteriormente por ele) — **aprovado**.

**BL-AV-1-05 (Hermes, execução e evidência; Antigravity CLI, confirmação do achado de idempotência):** roteiro visual completo executado via Chrome real (CDP) + Playwright: login com professor de demonstração → criação de avaliação/questão/rubrica com 2 critérios → soma validada pelo servidor → publicação → resposta fictícia → acompanhamento automático do job (polling real) → redirecionamento para revisão → sugestão da IA em modo simulado, com o banner "Análise em modo simulado" visível na tela → aprovação como decisão humana → reload da página (F5), sessão mantida → reabertura direta da mesma URL de revisão (sem cache de `sessionStorage`), tela carregou sem erro. **Refinamento de Rafael cumprido e com achado real:** ao reabrir a revisão já decidida, a tela voltou a mostrar o formulário completo e ativo, não um estado "já revisado"; investigação subsequente (via Playwright + `curl` direto) confirmou que o backend aceita reenvio sem checagem de idempotência, criando 3 linhas de `HumanReview` para o mesmo job (dado fictício de teste). Antigravity CLI leu o código real (`core/app/main.py`, `core/app/models.py`, `frontend/src/pages/ReviewPage.tsx`) e **confirmou o achado como gap real de severidade alta**, não falso positivo. Registrado como `DEBT-AV-011`/`BL-AV-1-10`, sem correção nesta sessão (decisão de política de produto necessária antes de implementar).

**Verificação independente por Hermes (consolidador):** reexecução de todos os comandos de teste citados; leitura direta de todos os arquivos alterados/criados antes de aceitar qualquer alegação dos executores; reprodução do achado de idempotência por 3 vias distintas (UI, HTTP direto, leitura de código); `git diff --check` completo do repositório (sem erros); `git status --short` confirmando que apenas os arquivos previstos no mapa de impacto foram tocados.

## 18. Closure gate

Aplicado [`sprint_closure_gate.md`](../sprint_closure_gate.md):

### A. Escopo e produto
- A1: atendido — AC-01/02/04/05/06/07/08/10 avaliados item a item; AC-09 validado localmente com ressalva de ambiente Postgres; AC-03 parcial apenas no remoto, registrado como tal;
- A2: atendido — cada arquivo alterado corresponde a BL-AV-1-05/06/09;
- A3: atendido — implementado/validado localmente ≠ validado remotamente ≠ homologado, distinguidos explicitamente nesta seção;
- A4: atendido — `DEBT-AV-005` permanece aberto (CI não validada remotamente); `DEBT-AV-009` tecnicamente resolvido mas formalmente aberto até homologação; `DEBT-AV-011` novo, registrado com severidade;
- A5: nenhuma alteração de README/PRD foi necessária além da já registrada; nenhuma mudança de roadmap.

### B. Qualidade e evidência
- B1: atendido — nenhuma validação foi marcada como concluída sem execução real;
- B2: atendido — comando/data/ambiente/resultado real em cada item de §17;
- B3: atendido — automatizada (pytest/YAML), visual (screenshots), integração real (HTTP), inspeção de código (Antigravity CLI/Codex) diferenciados explicitamente;
- B4: atendido — a ausência de execução remota da CI nunca foi apresentada como sucesso; o achado de idempotência nunca foi minimizado;
- B5: **parcial apenas no remoto** — testes/build/lint locais 100% verdes (Core 42, AI 21+21, Ruff Core/AI, ESLint frontend, build); CI remota não executada;
- B6: atendido — o próprio achado de segurança/integridade (`DEBT-AV-011`) foi encontrado por esta validação e não foi minimizado; nenhum segredo exposto (verificado por Hermes e pelos revisores).

### C. Documentação e estado do repositório
- C1: atendido — este documento + snapshot desta execução;
- C2: atendido — sprint, dashboard, débitos e backlog atualizados na mesma execução;
- C3: atendido — `git status --short` e `git diff --check` registrados;
- C4/C5: não houve necessidade de alteração de README/links além do já feito;
- C6: atendido — nenhuma promoção de baseline ocorreu ou foi sugerida.

### D. Autoridade
- D1: atendido — cada revisão cruzada tem agente, comando e resultado registrados; Hermes teve suas próprias correções (whitespace, comentários do YAML) revisadas por Codex/Antigravity CLI, conforme exigido explicitamente por Rafael;
- D2: atendido — homologação apresentada para decisão, não presumida;
- D3: a divergência sobre lint ausente do escopo de BL-AV-1-06 é registrada como exceção a decidir por Rafael, não resolvida unilateralmente;
- D4: **não aplicável nesta fatia** — nenhuma ação Git/remota foi realizada; a etapa remota (execução real do workflow) permanece condicionada a autorização específica, apresentada em separado (ver relação de arquivos abaixo).

**Resultado desta sprint: implementada e validada localmente, com um único item parcial (CI remota), não "concluída" sem ressalva:**
- **local (concluído):** BL-AV-1-09 (`DEBT-AV-009` sanado), BL-AV-1-05 (`DEBT-AV-004` resolvido), BL-AV-1-10 (`DEBT-AV-011` corrigido no código e validado visualmente), lint Ruff/ESLint, whitespace, `git diff --check` global;
- **parcial:** BL-AV-1-06/`DEBT-AV-005` — workflow com lint+testes+build criado e validado localmente por Hermes/Antigravity/Claude; execução real no GitHub Actions requer autorização Git específica;
- **limite operacional:** migração de BL-AV-1-10 NÃO aplicada ao `avalia_dev`; 3 duplicados fictícios preservados; migração agora deduplica antes da constraint, mas aplicação depende de autorização;
- **revisão independente:** Claude Code (`claude-sonnet-5`, firstParty, CLI 2.1.260) emitiu parecer inicial aprovado condicional no diff `a7128afd...`; tentativa de verificação pós-correção falhou por limite de sessão, e Antigravity CLI assumiu a verificação posterior, aprovando incondicionalmente;
- **homologação do fechamento permanece pendente de Rafael** — nenhuma outra sprint autorizada.

## 19. Relação de arquivos para a etapa remota (commit/push), separando AV-S01 de AV-S02

**Nenhuma ação Git foi realizada. Esta seção apenas relaciona o estado exato do working tree para a decisão de Rafael sobre commit/push — não é uma proposta de mensagem de commit nem staging automático.**

Commit de referência (`HEAD`, ainda idêntico ao início de toda a trilha): `0be691e12e9d5d6f3ffc989237739f6559d8dacd`.

### 19.1 Herdado da execução original de AV-S01 (nenhuma mudança nesta sprint)

Modificados (já existiam antes desta sessão):
- `README.md`
- `core/README.md`
- `core/app/main.py`
- `core/app/schemas.py`
- `core/app/tests/conftest.py`
- `docs/contracts/openapi.yaml`
- `frontend/src/App.tsx`
- `frontend/src/services/api.ts`

Novos (já existiam antes desta sessão):
- `core/app/tests/test_authorization_boundaries.py`
- `AGENTS.md`
- `docs/roteiro-apresentacao-supervisor.md`
- `docs/governance/` (árvore completa, criada/atualizada ao longo de GOV-001 a EXEC-2026-09-23-06; esta sprint adiciona `sprints/sprint_AV-S02_ci_visual_isolamento_testes.md`, `evidence/AV-S01/`, `evidence/AV-S02/` e atualizações a registros/snapshots/dashboard, listados abaixo separadamente)

### 19.2 Novo nesta sprint (AV-S02)

Modificado:
- `frontend/src/pages/ReviewPage.tsx` — **apenas a remoção de 2 espaços em branco na linha 25** (o resto do diff deste arquivo é herdado de AV-S01, listado em 19.1); isolar esta mudança exigiria um `git add -p` cirúrgico se Rafael quiser separar o commit por linha — Hermes não fará isso sem instrução explícita, pois normalmente as duas mudanças (AV-S01 funcional + AV-S02 cosmético) seriam commitadas juntas por estarem no mesmo arquivo/área.
- `ai-engine/tests/test_schema_repair_and_fallback.py` — diff completo de 2 linhas (`BL-AV-1-09`), reproduzido em §17.

Novo:
- `.github/workflows/ci.yml` (`BL-AV-1-06`) — arquivo completo, ver conteúdo revisado em §17/registro de débitos.

Documentação nova/atualizada nesta sprint (dentro de `docs/governance/`, já contabilizada como parte da árvore untracked em 19.1, mas com conteúdo específico desta sessão):
- `docs/governance/sprints/sprint_AV-S02_ci_visual_isolamento_testes.md` (este documento);
- `docs/governance/evidence/AV-S02/*.png` (11 capturas);
- `docs/governance/backlog/backlog_tecnico_avalia.md` (novo `BL-AV-1-10`, status de `BL-AV-1-09` atualizado);
- `docs/governance/registers/technical_debts.md` (`DEBT-AV-011` novo; `DEBT-AV-009` com nota de resolução técnica);
- `docs/governance/executive_technical_dashboard.md` e `docs/governance/snapshots/` (snapshot desta execução, ver abaixo).

### 19.3 Diff exato dos 2 arquivos de código tocados nesta sprint

```diff
diff --git a/ai-engine/tests/test_schema_repair_and_fallback.py b/ai-engine/tests/test_schema_repair_and_fallback.py
index 6f42c09..1a1b27a 100644
--- a/ai-engine/tests/test_schema_repair_and_fallback.py
+++ b/ai-engine/tests/test_schema_repair_and_fallback.py
@@ -1,6 +1,7 @@
 import json
 from unittest.mock import AsyncMock
 import pytest
+from app.config import settings
 from app.main import ollama_client


@@ -34,6 +35,7 @@ def test_invalid_llm_json_triggers_repair_and_succeeds(client, sample_payload, m
     mock_generate = AsyncMock(return_value=broken_output)
     mock_repair = AsyncMock(return_value=valid_repaired_output)

+    monkeypatch.setattr(settings, "ai_engine_mode", "real")
     monkeypatch.setattr(ollama_client, "generate", mock_generate)
     monkeypatch.setattr(ollama_client, "repair_json", mock_repair)

@@ -60,6 +62,7 @@ def test_invalid_llm_json_fails_after_repair_returns_502(client, sample_payload,
     mock_generate = AsyncMock(return_value=broken_output)
     mock_repair = AsyncMock(return_value=still_broken_output)

+    monkeypatch.setattr(settings, "ai_engine_mode", "real")
     monkeypatch.setattr(ollama_client, "generate", mock_generate)
     monkeypatch.setattr(ollama_client, "repair_json", mock_repair)
```

O diff de `frontend/src/pages/ReviewPage.tsx` (misto AV-S01 + a linha 25 de AV-S02) e o conteúdo completo de `.github/workflows/ci.yml` estão reproduzidos integralmente no snapshot desta execução, para não duplicar ~120 linhas neste documento.

### 19.4 Pacote de revisão para publicação (preparado em 2026-09-24, não executado)

Rafael determinou a organização por finalidade integrada (não por sprint isolada, para evitar
commits incompletos) e autorizou explicitamente a preparação deste pacote. **Nenhuma ação Git foi
executada** — apenas os artefatos de revisão abaixo.

Pacote completo, inventário, diffs completos (incluindo arquivos novos), dependências entre
commits, gatilhos/checks esperados do CI e confirmação de ausência de segredos/artefatos
temporários: `docs/governance/evidence/AV-S02-review-package/00_pacote_revisao.md` (documento
principal) e os arquivos `.diff`/`.txt` irmãos no mesmo diretório.

Resumo dos 4 commits propostos:
1. **Funcionalidades integradas AV-S01+AV-S02** (contratos, migração, frontend, testes) — 16 arquivos;
2. **Isolamento dos testes do AI Engine + lint** — 21 arquivos, incluindo `ai-engine/tests/test_schema_repair_and_fallback.py` (BL-AV-1-09, explicitamente incluído por instrução de Rafael);
3. **Workflow de CI** — 1 arquivo novo (`.github/workflows/ci.yml`), depende dos commits 1 e 2;
4. **Governança e evidências** — árvore completa de `docs/governance/` (63 arquivos), excluindo `docs/roteiro-apresentacao-supervisor.md` por instrução explícita.

Destino proposto, apenas registrado (branch e PR não criados): `feat/av-s01-s02-consolidacao` →
PR para `main`, sem merge automático.

Localização dos scripts e evidências reproduzíveis dos testes de migração/concorrência em
PostgreSQL isolado (sanitizados, sem credenciais reais): `docs/governance/evidence/AV-S02-postgres-isolado/`.

`DEBT-AV-005` permanece aberto até a execução remota real do workflow no GitHub Actions — a
preparação deste pacote não constitui essa execução.

**Nenhum passo Git (`add`/`commit`/`push`/criação de branch/PR) foi executado nesta fatia.
Aguardando revisão do pacote e autorização explícita e específica de Rafael antes de qualquer
um deles.**

## 20. Fatiamento de lint Python autorizado por Rafael (2026-09-24)

Rafael autorizou explicitamente o item 3: configurar Ruff mínimo para `core/` e `ai-engine/`, sem tocar no workflow, frontend ou fazer reformatação automática. O mapa de impacto foi ampliado para `ruff.toml`, `core/requirements-dev.txt`, `ai-engine/requirements-dev.txt` e, somente se o lint apontasse achado real, arquivos Python sob `core/app` e `ai-engine/app`.

Estado factual desta fatia:

- **implementado:** `ruff>=0.6,<1.0` adicionado ao dev do Core; dev do AI Engine criado apenas com Ruff, preservando suas dependências de teste no arquivo atual; `ruff.toml` raiz com `E`, `F`, `I`, `line-length=120` e `target-version="py311"`;
- **não executado/bloqueado pelo ambiente:** Ruff não existia nas venvs ou no PATH. `core/.venv/bin/pip install 'ruff>=0.6,<1.0'` falhou após 5 tentativas por DNS/rede indisponível (`No matching distribution found`, sem qualquer versão consultável). Não havia wheel/cache/binário local, Docker, `flake8`, `pyflakes` ou `isort`; Homebrew não podia gravar em seu prefixo. Portanto, nenhuma saída de `ruff check` foi fabricada e nenhum arquivo-fonte foi alterado;
- **regressão validada:** Core 40 passed; AI Engine 21 passed no ambiente padrão e 21 passed com `AI_ENGINE_MODE=simulated`; todos exit 0;
- **estado:** parcial. Retomar instalando Ruff em ambiente com acesso ao pacote e executar `ruff check --config ruff.toml core/app ai-engine/app`; corrigir somente achados reais, reexecutar até exit 0 e repetir as três suítes se houver mudança de fonte.

**Reconciliação datada (2026-09-24T06:xx-03:00, Hermes):** a indisponibilidade acima era factual apenas no sandbox do executor Codex naquele momento. Na sessão principal de Hermes, o acesso ao pacote estava disponível: Ruff 0.16.8 foi instalado nas duas venvs, `ruff check` executou, encontrou 40 achados no Core e 13 no AI Engine (imports, variáveis não usadas e linhas longas); os achados reais foram corrigidos sem supressão/reformatação ampla. Estado final reexecutado por Hermes, Antigravity CLI e Claude Code: `ruff check` limpo nos dois projetos; Core 42/42; AI Engine 21/21 padrão e 21/21 simulado global. Portanto, o bloqueio desta fatia está **sanado** e não deve ser lido como estado atual.

Evidência completa: [`EXEC-2026-09-24-01`](../snapshots/snapshot_EXEC-2026-09-24-01_AV-S02-lint-python.md). Nenhum commit, push, tag, deploy ou alteração remota ocorreu.

## 21. Correções da revisão independente de BL-AV-1-10 (2026-09-24)

Rafael autorizou a correção dos três achados reportados por Claude Code: saneamento de duplicatas legado dentro do `upgrade()` antes da constraint, comparação simétrica de justificativa e contrato uniforme de `existing_review` no 409.

- **implementado:** a migração usa `ROW_NUMBER() OVER (PARTITION BY job_id ORDER BY created_at, id)` e remove somente linhas com posição maior que 1 antes de criar `uq_human_reviews_job_id`; `None` e `""` são equivalentes na justificativa; contexto e conflito reutilizam `HumanReviewSummaryOut`, incluindo `reviewer_email` e `final_scores`;
- **validado:** SQLite isolado com 3 duplicatas passou por `alembic upgrade head`, manteve `review-oldest-a`, deixou uma linha e rejeitou nova duplicata; Core 42 passed; Ruff limpo; `git diff --check` limpo;
- **limite operacional:** `avalia_dev` não foi acessado nem migrado. A aplicação dessa migração ao banco operacional permanece sem autorização;
- **estado:** correções implementadas e validadas localmente; revisão independente ocorreu antes desta fatia; nova homologação por Rafael permanece pendente.

Evidência completa: [`EXEC-2026-09-24-02`](../snapshots/snapshot_EXEC-2026-09-24-02_BL-AV-1-10-revisao.md).

## 22. Verificação das correções pelo revisor independente (Claude Code, 2026-09-24)

A revisão independente foi ancorada em duas versões distintas para evitar que correções posteriores fossem consideradas automaticamente cobertas:

1. **parecer inicial:** HEAD `0be691e...`, diff SHA-256 `a7128afd3ab05854046d318d0aa1d2aeaeea2f9e3ed84a3ab804aa29374d1b80`, timestamp `2026-09-24T06:18:09-03:00` — parecer **aprovado condicional**, com 4 condições: revalidação visual real AC-04/AC-10; atualização dos registros; não aplicar a migração enquanto não houver deduplicação; atualizar OpenAPI (recomendado, não bloqueante);
2. **versão após correções:** diff SHA-256 `f687f527f102a8d33fe6f94c1b30f5f5edd4b036e297a9b0be361bda0ed3800b`, timestamp `2026-09-24T07:06:00-03:00` — enviada ao mesmo revisor para verificação das correções (resultado consolidado no snapshot final desta execução).

Achados iniciais do Claude Code:
- **alto:** migração falharia no `avalia_dev` atual por causa das 3 duplicatas; confirmado pelo próprio revisor em transação `BEGIN`/`ROLLBACK` (nenhuma alteração operacional). Corrigido: `upgrade()` agora deduplica deterministicamente antes da constraint; validado em SQLite isolado com 3→1 e rejeição de nova duplicata;
- **baixo:** justification não era comparada em `APPROVE`. Corrigido: comparação simétrica com normalização `None`/`""`;
- **baixo:** resposta 409 tinha formato diferente do contexto. Corrigido: ambos reutilizam `HumanReviewSummaryOut` completo;
- **observação:** OpenAPI desatualizado. Corrigido: `409`, `ReviewConflictOut`, `HumanReviewSummaryOut` e `human_review` opcional adicionados;
- **condição de evidência:** AC-04/AC-10 precisavam de navegador real pós-fix. Atendido: novo fluxo real, screenshot somente leitura e ausência de botões (0/0);
- **governança desatualizada:** saneada nesta seção, no backlog, débitos, snapshot e dashboard.
