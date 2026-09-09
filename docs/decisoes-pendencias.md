# Decisões a congelar e perguntas abertas (PRD seção 29) — status nesta entrega

| ID | Decisão/pergunta | Status nesta entrega |
|---|---|---|
| D-01 | Framework frontend definitivo | Decidido para a demo: React + Vite + TypeScript (ver ADR-004). Squad pode revisitar. |
| D-02 | Monorepo ou múltiplos repositórios | Decidido: monorepo dentro de `avalia-platform` (ver ADR-002). |
| D-03 | Fila/worker e semântica de entrega | Decidido para a demo: tabela Postgres + worker in-process asyncio, sem broker (ver ADR-006). Backlog: broker real para lote. |
| D-04 | Runtime local padrão | Decidido para a demo: Ollama (ver ADR-005). |
| D-05 | Modelo/quantização baseline e hardware-alvo | Decidido para a demo: qwen2.5:7b-instruct-q4_K_M, validado em Apple M5 Pro/24GB (ver ADR-005 e benchmark em `docs/relatorio-entrega.md`). Squad deve revalidar em hardware próprio. |
| D-06 | Autenticação: JWT/sessão e estratégia de renovação | Decidido para a demo: JWT access+refresh (ver ADR-007). |
| D-07 | Limites iniciais de confiança | Não recalibrado — mantidos os limiares iniciais do PRD (≥85/60-84/<60). Pendente piloto real. |
| D-08 | Política de retenção de respostas e auditoria | Em aberto — não definida nesta entrega. |
| D-09 | Escala de nota e arredondamento padrão | Decidido para a demo: decimal com 1 casa, arredondamento bancário no Core (nunca float binário como fonte de verdade, RN aplicada). |
| D-10 | Política de segunda revisão | Em aberto — fora do escopo da demo. |
| D-11 | Formato e governança do dataset científico | Em aberto — fora do escopo da demo. |
| D-12 | Modelo de implantação do primeiro piloto | Em aberto — esta entrega é local/demonstração, não implantação. |

Decisões marcadas "Decidido para a demo" seguem a regra do pedido original:
"para decisões ainda abertas, escolha a alternativa mais simples compatível,
documentando justificativa em ADR curto" — são recomendações técnicas do
Tech Leader para a squad revisar e ratificar formalmente, não substituem
decisão colegiada quando a squad retomar o trabalho.
