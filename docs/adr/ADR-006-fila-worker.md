# ADR-006 — Fila/worker: tabela Postgres + asyncio in-process (sem broker)

Status: Aceito — 09/09/2026
Responsável: G1 + G4

## Contexto
PRD pede fila/worker para processamentos demorados, mas orienta: "a escolha
de fila e worker deve ser proporcional ao recorte". A demo processa
correções unitárias (uma resposta por vez), não lote em massa.

## Decisão
`CorrectionJob` como tabela Postgres com estado explícito (PENDENTE,
PROCESSANDO, SUGERIDA, FALHA), reivindicado de forma idempotente por uma
tarefa assíncrona in-process (`asyncio.create_task` disparada pelo próprio
processo do Core). Sem RabbitMQ/Redis/Celery.

## Justificativa
Evita infraestrutura adicional sem necessidade (diretriz explícita do
pedido). Suficiente para demonstrar estados, tratamento de falha e
retomada. Simples de rodar em qualquer máquina sem serviços extras.

## Consequências / débito técnico
Não escala horizontalmente (um único processo Core consome os jobs). Para
lote real (RF-08, EP-11) será necessário migrar para um broker real —
registrado no backlog G1/G4. Idempotência é garantida por chave única de
job (answer_id + tentativa), evitando duplicação em reprocessamento.
