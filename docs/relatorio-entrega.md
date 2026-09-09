# Relatório de entrega — AvalIA (demonstração experimental)

Data: 09/09/2026. Autor da execução: Claude Code (orquestrador), com
frentes delegadas a Antigravity CLI (`agy`) e Codex CLI; Claude Code
(subprocesso delegado) falhou por sessão OAuth expirada e o Core API foi
implementado diretamente pelo orquestrador (ver seção 6).

## 1. Implementado (código real, executado)

- **Core API** (`core/`): FastAPI + SQLAlchemy + Alembic + PostgreSQL.
  Auth JWT, RBAC professor/admin, CRUD de avaliação/questão/rubrica,
  validação de publicação (soma da rubrica == valor da questão, Decimal),
  correção assistida via `BackgroundTasks` chamando o AI Engine por HTTP,
  recálculo de totais e clamping de limites no Core (nunca confia
  cegamente na IA), revisão humana (aprovar/alterar com justificativa),
  auditoria, health check, logs JSON com correlation_id.
- **AI Engine** (`ai-engine/`): FastAPI + Ollama local. Cascata reduzida
  (nível 0 validação, nível 1 regras simples, nível 3 LLM local), prompt
  versionado com delimitação de dado não confiável e detecção básica de
  prompt injection, validação de saída contra JSON Schema com reparo
  controlado, cálculo heurístico de confiança (`heuristic-v1`, ADR-008),
  modo simulado explícito nunca acionado silenciosamente.
- **Frontend** (`frontend/`): React + Vite + TypeScript. Login, lista e
  editor de avaliação/rubrica com validação em tempo real, inserção de
  resposta, tela de processamento com polling, tela de revisão lado a
  lado diferenciando sugestão da IA de decisão humana, identidade visual
  do PRD, acessibilidade básica.
- **Banco de dados**: PostgreSQL 16 local, migração Alembic aplicada,
  dados fictícios via `core/app/seed.py` (professor, avaliação "Estruturas
  de Dados", questão pilha/fila, rubrica de 4 critérios, 3 respostas
  correta/parcial/errada).
- **Documentação**: README raiz, `docs/arquitetura.md`,
  `docs/requisitos-utilizados.md`, `docs/backlog.md`,
  `docs/decisoes-pendencias.md`, `docs/pendencia-regulatoria.md`, 8 ADRs
  em `docs/adr/`, contratos em `docs/contracts/` (OpenAPI + JSON Schema).

## 2. Validado (evidência real de execução nesta sessão)

- **Testes automatizados**: 8/8 testes pytest do Core + 21/21 testes
  pytest do AI Engine = **29/29 passando**, executados a partir do
  repositório final `avalia-plataform` (não apenas nos worktrees de
  desenvolvimento).
- **Inferência real de ponta a ponta** (não simulada): duas chamadas
  reais ao modelo `qwen2.5:7b-instruct-q4_K_M` via Ollama local:
  - Resposta correta → nota 6,00/6,00, tempo de resposta ~7,9s.
  - Resposta conceitualmente errada (mas com palavras-chave em comum com
    a referência) → nota 0,00/6,00, tempo ~4,8s. Confirma que o sistema
    não converte similaridade textual em nota diretamente.
- **Fluxo end-to-end via API real** (script `/tmp/e2e_test.sh`, contra
  Core+AI Engine+Postgres reais, sem mocks): login válido, login inválido
  bloqueado, acesso sem token bloqueado (401), rubrica com soma incorreta
  rejeitada com `RUBRIC_TOTAL_MISMATCH`, avaliação com rubrica correta
  publicada, correção real solicitada e processada (status
  PENDENTE→PROCESSANDO→SUGERIDA), revisão humana (APPROVE) registrada com
  `reviewer_id` correto, health check final OK.
- **Persistência após reiniciar os serviços**: Core e AI Engine
  derrubados e religados; a correção e a revisão humana anteriores
  continuaram acessíveis via GET, confirmando que os dados persistem no
  PostgreSQL e não dependem do processo em memória.
- **Build do frontend**: `npm run build` limpo (sem erros TypeScript),
  a partir do repositório final.
- **Ambiente local**: PostgreSQL 16 e Ollama instalados via Homebrew
  nesta sessão, rodando; modelo `qwen2.5:7b-instruct-q4_K_M` baixado
  (4,7 GB) e testado.

## 3. Simulado (explicitamente identificado, nunca confundido com real)

- O AI Engine possui um modo simulado (`AI_ENGINE_MODE=simulated`) para
  contingência/teste, testado nos 21 testes automatizados — mas **não foi
  usado** nas evidências de inferência real acima. Toda saída do AI
  Engine inclui o campo `engine_mode` (`real` ou `simulated`), propagado
  até o frontend, que exibe aviso visível quando `simulated`.
- O teste `test_ai_engine_unavailable_does_not_fabricate_result` do Core
  usa uma URL de AI Engine inexistente (porta 9999) para simular
  indisponibilidade de forma determinística — isso é teste de
  infraestrutura, não geração de resultado simulado disfarçado de real.

## 4. Bloqueado / não executado nesta sessão

- **Teste visual em navegador real**: o harness de browser headless
  (`browser_exec`) não conseguiu anexar a uma instância Chrome nesta
  máquina (`DevToolsActivePort not found`, provável conflito com perfil
  Chrome já aberto do usuário). Não tentei contornar isso matando
  processos do navegador do usuário. A validação do frontend foi feita
  por: build limpo, revisão manual de código linha a linha, smoke test
  HTTP do dev server, e — mais importante — validação funcional completa
  da API real que o frontend consome (o mesmo contrato, testado por
  script). Recomendo que a squad ou você mesmo abra
  http://localhost:5173 manualmente para uma verificação visual final
  antes da apresentação de sexta.
- **Delegação ao Claude Code (subprocess)**: a integração estava
  configurada e autenticada no início da sessão (`claude auth status`
  retornou `loggedIn: true`), mas ao disparar a tarefa delegada a sessão
  OAuth expirou (`Failed to authenticate: OAuth session expired and
  could not be refreshed`) e `claude setup-token` exige login interativo
  via navegador, que não pude completar de forma não supervisionada.
  Frente do Core API implementada diretamente por mim (o orquestrador,
  também Claude Code) para não bloquear o prazo. Recomendo rodar
  `claude auth login` manualmente se quiser usar a integração de
  subprocesso Claude Code no futuro.
- **Pendência regulatória CNE**: não investigada nesta sessão (fora do
  escopo técnico desta implementação) — ver
  `docs/pendencia-regulatoria.md`.
- **Calibração de confiança com dados reais** (D-07 do PRD): não feita,
  usa limiares iniciais do PRD sem piloto.
- **Nível 2 da cascata (embeddings)**: não implementado nesta demo (ver
  `docs/arquitetura.md`, seção cascata de decisão).

## 5. Não medido / sem alegação de ganho

Não há medição de precisão, redução de tempo de correção ou qualidade
pedagógica nesta entrega — nenhuma dessas alegações deve ser feita ao
coordenador. O que existe é: o fluxo funciona ponta a ponta com inferência
real, os testes automatizados passam, e duas evidências qualitativas
(resposta correta vs. conceitualmente errada) mostram que o modelo não
confunde similaridade textual com correção.

## 6. Coordenação dos agentes — o que realmente aconteceu

| Agente | Integração testada | Resultado |
|---|---|---|
| Antigravity CLI (`agy`) | `agy -p "..." --dangerously-skip-permissions` | **Sucesso.** Implementou o AI Engine completo em ~4 min, 21 testes próprios, 5 commits organizados na branch `feature/ai-engine-local`. |
| Codex CLI | `codex exec --sandbox workspace-write "..."` | **Parcial.** Implementou a maior parte do frontend (~10 min), mas seu sandbox teve bloqueio de DNS para `registry.npmjs.org` e não conseguiu rodar `npm install`/build, nem commitar. Eu completei o install/build e corrigi 3 desalinhamentos reais de contrato (nomes de campos divergentes do schema do Core) encontrados ao validar contra a API real — não apenas contra o mock. |
| Claude Code (subprocess `claude -p`) | `claude -p "..." --allowedTools ... --permission-mode acceptEdits` | **Falhou antes de iniciar** — sessão OAuth expirada. Implementei o Core API diretamente. |

Nenhuma pesquisa foi duplicada entre agentes: cada um trabalhou em
worktree/branch isolado (`feature/core-api`, `feature/frontend-app`,
`feature/ai-engine-local`), sobre os mesmos contratos definidos
previamente (`docs/contracts/`), e a integração final foi centralizada
por mim com merge sequencial sem conflitos.

## 7. Testes executados — resumo

| Componente | Testes | Resultado |
|---|---|---|
| Core API | 8 (pytest) | 8 passed |
| AI Engine | 21 (pytest) | 21 passed |
| Frontend | build TypeScript | limpo, sem erros |
| Integração E2E | script manual via curl | login, permissão, rubrica inválida, correção real, revisão, persistência — todos OK |

Casos obrigatórios do pedido, status:
- Acesso sem permissão bloqueado no backend: **validado** (401 e 403).
- Rubrica inválida recusada: **validado** (`RUBRIC_TOTAL_MISMATCH`).
- Sugestões fora dos limites rejeitadas e recalculadas com precisão
  decimal: **validado** (Core usa `Decimal`, testa `SCORE_OUT_OF_RANGE` e
  clamping).
- Indisponibilidade do modelo tratada sem fabricar resultado:
  **validado** (teste automatizado + teste manual planejado no roteiro).
- Revisão humana persistida e atribuída ao usuário responsável:
  **validado** (`reviewer_id` confirmado no teste E2E).
- Reprocessamento preservando versões anteriores: **validado** (teste
  automatizado cria dois `CorrectionJob`/`AIExecution` distintos).
- Dados persistindo após reiniciar os serviços: **validado** manualmente
  (Core e AI Engine derrubados e religados, dados intactos).
