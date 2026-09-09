# ADR-002 — Monorepo

Status: Aceito — 09/09/2026
Responsável: Rafael Sampaio Oliveira (Tech Leader)
Decisão do PRD: D-02 / ARCH-003

## Contexto
O PRD deixa em aberto monorepo vs. multirepo. É preciso escolher algo simples
e compatível com paralelização de 3 agentes autônomos trabalhando ao mesmo
tempo em componentes diferentes, sob prazo curto.

## Decisão
Um único repositório Git (`avalia-platform`) contendo `core/`, `ai-engine/`,
`frontend/`, `infra/`, `docs/`. Isolamento de trabalho paralelo via branches
de feature + git worktrees, não via repositórios separados.

## Justificativa
- Contratos (OpenAPI, JSON Schema do AI Engine) versionam junto com quem os
  consome, reduzindo risco de dessincronia entre Core/AI Engine/Frontend
  durante desenvolvimento paralelo.
- Um único PR de integração final é mais simples de revisar que sincronizar
  3 repositórios e 3 pipelines de CI nesta fase.
- Squad pequena (9 pessoas) não paga o custo de coordenação de multirepo
  ainda.

## Consequências
- CI precisa restringir jobs por pasta alterada (path filters) para não
  rodar tudo a cada commit — registrado no backlog G4.
- Se o produto crescer para múltiplos times/deploys independentes, revisitar
  esta decisão (não é definitiva).

## Alternativas consideradas
Multirepo (Core/AI Engine/Frontend separados): rejeitado por aumentar
coordenação necessária durante a demonstração paralela desta entrega.
