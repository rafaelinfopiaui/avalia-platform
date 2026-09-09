# ADR-008 — Fórmula inicial de confiança (heurística, não calibrada)

Status: Aceito — 09/09/2026
Responsável: G3 + IA

## Decisão
Confiança inicial = combinação determinística e versionada de:
1. validade do schema JSON retornado pelo LLM (peso alto — se inválido após
   1 tentativa de reparo, confiança cai para faixa baixa e força revisão);
2. cobertura de critérios (todos os critérios da rubrica retornados);
3. concordância com sinais de regras (conceitos obrigatórios identificados
   no texto vs. exigidos pela rubrica).

Fórmula e versão (`confidence_method_version = "heuristic-v1"`) são
registradas em cada `AIExecution`.

## Justificativa
O PRD é explícito: "a fórmula final deve ser calibrada com dados humanos"
(seção 14.3) — não há dataset piloto disponível nesta demo. A fórmula acima
é auditável, versionada e nunca apresentada como probabilidade calibrada
(RN-016, requisito explícito do pedido original).

## Consequências
Faixas (alta ≥85%, média 60-84%, baixa <60%) são as mesmas iniciais do PRD,
não recalibradas. Squad deve revisar com piloto real (D-07, backlog G3).
