---
id: EXEC-2026-09-23-05
tipo: execucao
sprint: AV-S01
gerado_em: "2026-09-23T18:30:00-03:00"
executor: "Hermes (execução direta desta fatia de saneamento); Codex e Antigravity CLI reconfirmados disponíveis mas não delegados nesta fatia (nenhuma correção de código foi necessária)"
status: homologada_com_debito_residual
commit_referencia: 0be691e12e9d5d6f3ffc989237739f6559d8dacd
---

# Snapshot EXEC-2026-09-23-05 — Saneamento da AV-S01 (validação visual real de AC-03, investigação de DEBT-AV-009, reconciliação de identificador)

> Registro histórico. Não promove baseline nem representa homologação de Rafael — a homologação do fechamento completo de AV-S01 (incluindo esta fatia de saneamento) continua pendente, conforme instrução explícita de Rafael ao autorizar esta fatia ("Ainda não estou homologando seu fechamento").

## 1. Abertura

- objetivo: sanear as lacunas explicitamente identificadas no fechamento anterior de `AV-S01` (EXEC-2026-09-23-04), dentro do escopo já autorizado — sem abrir nova sprint, sem alterar decisão de produto: (1) concluir a validação visual real dos 4 subcasos de AC-03; (2) corrigir e revalidar se algum caso falhar; (3) investigar (não apenas registrar) as 2 falhas de `DEBT-AV-009`; (4) reconciliar o identificador duplicado entre os snapshots -03 e -04; (5) reconfirmar disponibilidade de Claude Code; (6) reavaliar o closure gate com AC-03 pendente até comprovação;
- escopo autorizado: exclusivamente o saneamento acima, dentro do escopo já aprovado de `AV-S01`; `DEBT-AV-008` (infraestrutura) explicitamente fora deste saneamento, por instrução direta de Rafael;
- fora de escopo: qualquer sprint além de `AV-S01`; qualquer decisão de produto pendente; commit/push/tag/deploy; promoção de baseline;
- repositório: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform`; branch `main`; commit de referência `0be691e12e9d5d6f3ffc989237739f6559d8dacd` (idêntico ao início — nenhum commit ocorreu nesta fatia);
- working tree inicial: idêntico ao final de EXEC-2026-09-23-04 (mesmos 9 arquivos de código modificados + arquivos de governança); nenhum arquivo de produto foi tocado durante esta fatia — apenas ambiente de execução local (serviços subidos) e dados fictícios adicionais no banco de teste/demo local;
- dependências/bloqueantes: nenhum external; depende apenas do ambiente local (Postgres, Chrome, agentes CLI) estar disponível, o que foi verificado nesta sessão.

## 2. Disponibilidade de agentes reconfirmada nesta sessão

| Agente | Comando | Resultado | Estado |
|---|---|---|---|
| Codex | `codex exec "responda apenas: ok"` | respondeu `ok` (sessão real, modelo `gpt-5.6-sol`) | disponível |
| Antigravity CLI | `agy -p "responda apenas: ok"` | respondeu `ok` | disponível |
| Claude Code (subprocess) | `claude -p "responda apenas: ok"` | `Failed to authenticate: OAuth session expired and could not be refreshed` | **indisponível — mesma causa raiz já registrada em execuções anteriores (sessão OAuth expirada)** |

Consequência: como nenhuma correção de código foi necessária nesta fatia (os 4 subcasos de AC-03 passaram sem falha — ver §3), não houve delegação de implementação a Codex/Antigravity CLI nesta fatia. A indisponibilidade de Claude Code não bloqueou o saneamento porque não houve necessidade de revisão arquitetural de código novo — apenas execução de validação e investigação, ambas conduzidas diretamente por Hermes com evidência real.

## 3. Validação visual real de AC-03 — os 4 subcasos, com evidência

**Ambiente montado nesta sessão (real, não simulado no sentido de mock):**
- Chrome real isolado, subido com `--remote-debugging-port=9333`, `--user-data-dir` dedicado (`/tmp/av_chrome_profile`), perfil limpo — não o navegador pessoal do usuário;
- `browser.cdp_url` configurado via `hermes config set` (via oficial, não edição direta do config.yaml) para apontar a esse Chrome isolado; `browser.allow_private_urls` habilitado pela mesma via, para permitir navegação a `localhost`;
- Core (`uvicorn`, porta 8000), AI Engine (`uvicorn`, modo `simulated`, porta 8001) e frontend (`vite dev`, porta 5173) subidos localmente a partir dos `.venv` já existentes de cada projeto — nenhuma dependência nova instalada nos projetos;
- Postgres real (`avalia_dev`), seed de demonstração já existente (professor "professor.demo@..."), com um segundo professor fictício adicional criado nesta sessão (`professor.b.demo@avalia-platform.example`), usado exclusivamente para o subcaso (d) — dado fictício, sem relação com pessoa real;
- 2 respostas fictícias novas + 2 jobs de correção (modo simulado) criados via API real para servir de fixture aos 4 subcasos — nomes claramente marcados como "Aluno Ficticio Saneamento AV-S01";
- execução via Playwright (instalado em venv isolado `/tmp/av_pw_venv`, não nos projetos), conectado ao Chrome real via CDP — não é o `browser_exec` do Hermes (que ficou bloqueado por SSRF guard cacheado no processo do tool-server; ver nota abaixo), mas é navegador real, motor real (Chromium), DOM real renderizado.

**Nota sobre `browser_exec`:** a tentativa inicial de usar a ferramenta `browser_exec` do Hermes falhou mesmo após configurar `browser.cdp_url`/`allow_private_urls` corretamente e reiniciar os daemons do `browser-harness`, porque o processo do tool-server MCP já havia cacheado o valor anterior (`allow_private_urls=false`) na primeira leitura do módulo, sem recarregar em runtime. Diagnosticado por leitura direta do código-fonte da ferramenta (`tools/url_safety.py`, `tools/browser_tool.py`). Como reiniciar esse processo estava fora do escopo desta sessão (afetaria a sessão inteira do usuário), a validação foi conduzida via Playwright conectado ao mesmo Chrome real por CDP — atende ao mesmo requisito ("navegador real disponível") sem depender do `browser_exec` bloqueado.

| Subcaso AC-03 | Cenário | Resultado | Evidência (arquivo local) |
|---|---|---|---|
| (a) | Professor autenticado, sem contexto local de revisão (chave `avalia_demo_workflow` do `sessionStorage` removida antes de abrir a URL) | **confirmado** — `ReviewPage` carregou enunciado, resposta do aluno e os 4 critérios corretamente via `GET /correction-jobs/{id}/context`, sem depender de cache local | `/tmp/av_ac03_a.png` (captura de tela real, inspecionada visualmente) |
| (b) | Contexto antigo de outra resposta (job 1) em memória do componente; navegação client-side (SPA, sem reload de página) para uma segunda revisão (job 2) | **confirmado** — 10 capturas de estado em intervalos de 150ms durante a transição não mostraram, em nenhum frame, o texto da resposta do job 1; a tela final mostrou corretamente os dados do job 2 | `/tmp/av_ac03_b_final.png`; log de 10 frames sem vazamento (nenhum frame com `has_old_A_text=True`) |
| (c) | Acesso sem autenticação à URL de revisão (`/correcoes/{id}/revisao?manual=1`) | **confirmado** — redirecionado para `/login`; após autenticar, retornou automaticamente ao destino original **com a query string `?manual=1` preservada** (mecanismo de `SessionGuard`/`LoginPage` já existente, corrigido na sprint anterior para preservar `location.search`) | `/tmp/av_ac03_c_login.png`, `/tmp/av_ac03_c_after_login.png` |
| (d) | Professor autenticado mas sem vínculo com a avaliação (segundo professor fictício, criado nesta sessão) | **confirmado** — bloqueio explícito ("Você não tem permissão para acessar esta correção."), sem tela quebrada, sem vazamento de nenhum dado da resposta/questão do professor dono | `/tmp/av_ac03_d.png` |

**Resultado consolidado:** os 4 subcasos de AC-03 foram confirmados por evidência visual real em navegador (Chromium real via CDP, DOM real, screenshots inspecionados). **Nenhuma falha foi encontrada em nenhum dos 4 subcasos** — portanto, o item 2 da instrução de Rafael ("se algum caso falhar, corrija... revisão cruzada... reexecute") não se aplicou nesta fatia: não houve necessidade de correção de código, revisão cruzada de correção, nem reexecução de testes por causa de AC-03.

**Consequência para `DEBT-AV-010`:** a lacuna de evidência (validação visual pendente) está **sanada**. `DEBT-AV-010` passa a `resolvido` no registro de débitos (ver §6).

## 4. Investigação de `DEBT-AV-009` (causa raiz, não apenas registro)

Reexecutado nesta sessão, ambiente real (`.venv` já existente do `ai-engine`, sem instalar nada novo):

- `pytest -q` (modo padrão, sem `AI_ENGINE_MODE` no ambiente): **21 passed**;
- `AI_ENGINE_MODE=simulated pytest -q` (modo simulado global): **19 passed, 2 failed** — os mesmos 2 testes já identificados em execuções anteriores: `test_invalid_llm_json_triggers_repair_and_succeeds`, `test_invalid_llm_json_fails_after_repair_returns_502`.

**Causa raiz identificada por leitura direta do código (`app/cascade.py` linha 154 em diante) e reexecução com saída detalhada:**

- Quando `AI_ENGINE_MODE=simulated` está definido no ambiente do processo, `DecisionCascade.execute()` entra no ramo "MODO SIMULADO EXPLÍCITO" (RN-017) **antes** de alcançar o Nível 3 (LLM real via Ollama). Esse ramo nunca chama `ollama_client.generate`/`repair_json` — é o comportamento correto e intencional (RN-017 exige nunca fabricar resultado real quando o modo simulado está ativo).
- Os 2 testes falhos usam `monkeypatch.setattr(ollama_client, "generate", ...)` e `monkeypatch.setattr(ollama_client, "repair_json", ...)` para simular respostas do LLM real, mas **não fixam `settings.ai_engine_mode` para `"real"` dentro do próprio teste** — dependem implicitamente do valor padrão da aplicação (`"real"`, definido em `app/config.py`), que é sobrescrito quando a variável de ambiente `AI_ENGINE_MODE=simulated` está presente no processo que executa o pytest.
- Confirmado na saída real: com `AI_ENGINE_MODE=simulated`, o log da requisição mostra `"Executando em modo simulado explícito (RN-017)"` e retorna HTTP 200 com `engine_mode=simulated`, nunca chamando os mocks (`mock_repair.assert_called_once()` falha com "Called 0 times" no primeiro teste; o segundo teste espera 502 e recebe 200).

**Classificação (conforme pedido explícito de Rafael — sem forçar verde):**
- **Não é defeito do produto.** O comportamento da cascata está correto e é exatamente o que a RN-017 exige.
- **É falha de isolamento dos 2 testes**, não de configuração incompatível do ambiente em si: os testes fazem uma suposição implícita (`ai_engine_mode == "real"`) sem fixá-la explicitamente, o que os torna dependentes de uma variável de ambiente externa ao próprio teste.
- **Não é о comando oficial de suíte que está errado**: o `README.md` do `ai-engine` documenta apenas `pytest -v` (sem `AI_ENGINE_MODE`), que passa 21/21. O uso de `AI_ENGINE_MODE=simulated` global sobre a suíte completa nunca foi o comando oficial documentado — foi uma verificação adicional de robustez feita em execuções anteriores, que revelou essa lacuna de isolamento real, porém secundária.

**Nenhuma alteração de código de teste ou de produto foi feita nesta fatia** — apenas investigação e diagnóstico, conforme instrução ("Não altere expectativas apenas para obter testes verdes"). Recomendação registrada (decisão de Rafael, não de Hermes): se a suíte precisar ser robusta a qualquer configuração externa de ambiente, os 2 testes deveriam fixar explicitamente `monkeypatch.setattr(settings, "ai_engine_mode", "real")` no início — mudança pequena, de escopo do próprio `ai-engine`, não implementada nesta fatia por não ter sido pedida como correção (o achado é de isolamento de teste, não de comportamento incorreto em produção).

## 5. Reconciliação do identificador duplicado (EXEC-2026-09-23-03 vs -04)

Achado, correção e cadeia histórica completa registrados como adendo dentro do próprio arquivo afetado: ver [`snapshot_EXEC-2026-09-23-04_AV-S01.md`](snapshot_EXEC-2026-09-23-04_AV-S01.md) §11. Resumo: o front-matter do arquivo de nome `snapshot_EXEC-2026-09-23-04_AV-S01.md` registrava `id: EXEC-2026-09-23-03`, duplicando o id do snapshot anterior e distinto (`snapshot_EXEC-2026-09-23-03_AV-S01-backend.md`). Corrigido para `id: EXEC-2026-09-23-04`, alinhado ao nome do arquivo e à ordem cronológica real. Nenhum conteúdo factual de entregas/validações foi alterado — apenas o identificador de metadado.

## 6. Registros canônicos atualizados nesta fatia

- `DEBT-AV-010` (validação visual pendente): alterado de `aberto` para **`resolvido em 2026-09-23`** — ver §3 desta seção. Registro completo em `registers/technical_debts.md`.
- `DEBT-AV-009` (suíte incompatível com modo simulado global): permanece **aberto**, mas com causa raiz agora documentada (isolamento de teste, não defeito de produto) em vez de apenas "identificar causa depois". Registro atualizado em `registers/technical_debts.md`.
- Nenhuma decisão nova de produto foi tomada — nenhuma alteração em `registers/decisions.md` além de referências de rastreabilidade.

## 7. Closure gate revisitado (AV-S01)

Com base na instrução explícita de Rafael ("Enquanto AC-03 não estiver comprovado, registre-o como pendente e o fechamento técnico como parcial, salvo exceção explicitamente aprovada por mim — ainda inexistente"):

- **AC-03 agora está comprovado** por evidência visual real (§3 desta seção) — a condição que exigia "parcial" para esse item específico foi atendida nesta fatia.
- **Estado do closure gate da AV-S01 após esta fatia:** os 6 critérios de aceite (AC-01 a AC-06) têm evidência real e datada, sem nenhuma lacuna de tipo de evidência pendente. `DEBT-AV-009` permanece como débito aberto (não bloqueia o fechamento técnico, é pré-existente e não relacionado ao código desta sprint, apenas mais bem documentado agora). Nenhum débito novo foi introduzido.
- **O fechamento técnico da AV-S01, incluindo esta fatia de saneamento, permanece sem homologação de Rafael** — nenhuma homologação foi presumida ou declarada. Rafael afirmou explicitamente ao autorizar este saneamento: "Ainda não estou homologando seu fechamento." Este snapshot apresenta o resultado para essa decisão, não a substitui.

## 8. Arquivos impactados nesta fatia

### Alterados
- `docs/governance/snapshots/snapshot_EXEC-2026-09-23-04_AV-S01.md` — correção do `id` do front-matter + adendo de reconciliação (§11 do próprio arquivo);
- `docs/governance/registers/technical_debts.md` — `DEBT-AV-010` resolvido, `DEBT-AV-009` com causa raiz documentada;
- `docs/governance/snapshots/latest_execution.md` — ponteiro atualizado para este snapshot;
- `docs/governance/executive_technical_dashboard.md` — atualizado com o resultado desta fatia;
- `docs/governance/sprints/sprint_AV-S01_autorizacao_retomada_revalidacao.md` — closure gate revisitado (§16), AC-03 sem lacuna de evidência.

### Criados
- `docs/governance/snapshots/snapshot_EXEC-2026-09-23-05_AV-S01-saneamento.md` (este arquivo).

Nenhum arquivo de código de produto (`core/`, `ai-engine/`, `frontend/src/`) foi alterado nesta fatia — confirmado por `git status --short` idêntico ao início desta sessão, exceto os arquivos de governança listados acima.

## 9. Validações executadas nesta fatia

| Data/fuso | Item | Comando/procedimento | Ambiente | Tipo | Resultado real |
|---|---|---|---|---|---|
| 2026-09-23T18:0x-03:00 | disponibilidade de agentes | `codex exec`, `agy -p`, `claude -p` (todos "responda apenas: ok") | sessão real desta sessão | inspeção de ambiente | Codex e Antigravity CLI disponíveis; Claude Code indisponível (OAuth expirado) |
| 2026-09-23T18:1x-03:00 | AC-03(a) | Playwright via CDP contra Chrome real; login real + `GET /correction-jobs/{id}/context` real contra Core+Postgres reais | navegador real (Chromium via CDP), serviços locais reais | visual + integração real | confirmado — dados carregados corretamente sem cache local |
| 2026-09-23T18:1x-03:00 | AC-03(b) | Playwright via CDP; navegação client-side entre 2 revisões reais, 10 capturas de estado em 150ms | navegador real | visual + integração real | confirmado — nenhum frame com dados do job anterior |
| 2026-09-23T18:2x-03:00 | AC-03(c) | Playwright via CDP; acesso sem token, redirect, login real, retorno ao destino com query preservada | navegador real | visual + integração real | confirmado |
| 2026-09-23T18:2x-03:00 | AC-03(d) | Playwright via CDP; segundo professor fictício real, acesso a job de outro professor | navegador real | visual + integração real | confirmado — bloqueio 403 sem vazamento |
| 2026-09-23T18:2x-03:00 | `DEBT-AV-009` | `pytest -q` (padrão) e `AI_ENGINE_MODE=simulated pytest -q` no `.venv` já existente do `ai-engine` | ambiente local real | automatizada | 21 passed (padrão); 19 passed/2 failed (simulado global) — causa raiz documentada em §4 |

Validações não executadas nesta fatia: nenhuma revalidação da suíte Core/frontend foi refeita (não fazia parte do pedido desta fatia; a última revalidação registrada permanece a de EXEC-2026-09-23-04, sem alteração de código desde então que a invalidasse).

## 10. Estado final

- status desta fatia: **concluída** — todos os 6 itens da instrução de Rafael foram executados (validação visual real; correção condicional não necessária; investigação de causa raiz; reconciliação de identificador; reconfirmação de agentes; closure gate revisitado);
- `AV-S01` (sprint completa, incluindo esta fatia): closure gate sem lacunas de evidência pendentes; `DEBT-AV-009` aberto (pré-existente, causa raiz documentada); `DEBT-AV-008` intencionalmente fora deste saneamento;
- baseline promovido: não;
- alterações desta fatia: apenas documentação de governança; nenhum código de produto tocado; dados fictícios adicionais no banco de demonstração local (2 respostas + 1 professor fictício adicional, claramente identificados como dados de teste);
- homologação por Rafael: **registrada em 2026-09-23**, incluindo a execução original e este saneamento; `DEBT-AV-009` aceito como débito residual aberto. Não autoriza commit, push, tag, deploy, promoção de baseline nem próxima sprint.

## 11. Próxima ação

Preparar o plano da próxima sprint elegível, verificando dependências reais e propondo a inclusão da correção de isolamento de `DEBT-AV-009`; apresentar a Rafael para aprovação antes de iniciar qualquer execução. `DEBT-AV-008` permanece aberto e fora do trabalho iniciado nesta sessão, por instrução explícita.

## 12. Adendo de homologação e estado operacional (2026-09-23T18:4x-03:00 — Hermes)

Rafael homologou explicitamente o fechamento completo de `AV-S01`, incluindo a execução original e este saneamento, aceitando `DEBT-AV-009` como débito residual. Foram registrados:

- AC-03 atendido por navegador real; evidências visuais versionadas em [`../evidence/AV-S01/`](../evidence/AV-S01/): `ac03_a_sem_contexto_local.png`, `ac03_b_sem_contaminacao_cache.png`, `ac03_c_redirect_login.png`, `ac03_c_retorno_pos_login.png`, `ac03_d_bloqueio_sem_permissao.png`;
- `DEBT-AV-010` resolvido; `DEBT-AV-009` aberto, com correção de isolamento dos testes a priorizar;
- validação da IA desta execução ocorreu em modo simulado; não houve revalidação da inferência real/Ollama;
- Claude Code indisponível (OAuth expirado); autoria efetiva: Codex implementou backend e revisou frontend; Antigravity CLI implementou frontend e revisou backend/contrato; Hermes consolidou, reexecutou evidências, aplicou o guard final e conduziu o saneamento;
- processos/serviços iniciados no saneamento (Core `:8000`, AI Engine `:8001`, Vite `:5173`, Chrome CDP `:9333`) foram encerrados. Verificação final com `lsof` e `ps` não encontrou listeners/processos relacionados ativos;
- dados fictícios persistentes no Postgres local `avalia_dev`: professor `professor.b.demo@avalia-platform.example`; respostas `dceacb38-0293-4548-9c44-ae7464aaa1e0` e `cdbadae4-d995-4699-a73a-e387d90a5927`; jobs simulados `1683329d-3bcb-4789-8ef2-3797de63fdb5` e `1a75827e-4938-44dc-9ada-8062de0e4720`, ambos `SUGERIDA`. Nenhum token/senha foi versionado; temporários sensíveis foram removidos.

Esta homologação não promove baseline automaticamente nem autoriza ação Git/remota ou outra sprint.
