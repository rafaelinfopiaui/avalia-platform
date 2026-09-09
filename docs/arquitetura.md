# Arquitetura — resumo e decisões

Ver ADRs completos em `docs/adr/`. Este documento resume o desenho aplicado.

## Visão de componentes

```
[Frontend React/Vite] --HTTP/JSON--> [Core API FastAPI] --HTTP/JSON--> [AI Engine FastAPI]
                                            |
                                       [PostgreSQL]
                                            |
                              [Job de correção: tabela + worker assíncrono
                               in-process (asyncio), sem broker externo]
```

- O frontend consome **somente** o Core API (nunca acessa banco, fila ou o
  AI Engine diretamente) — boundary do PRD seção 11.2.
- O Core é dono de usuários, permissões, avaliações, rubricas, respostas,
  notas finais e auditoria.
- O AI Engine é stateless, não decide autorização nem nota final; devolve
  saída estruturada validada por JSON Schema.
- O Core recalcula os totais a partir dos `criterion_scores` retornados —
  nunca confia cegamente no total vindo da IA (RN-009).

## Fila/worker — decisão de simplicidade (ADR-006)

Dado o recorte da demonstração (uma correção por vez, poucos usuários
fictícios, prazo curto), a fila é **um estado em tabela Postgres**
(`correction_jobs`, estados PENDENTE/PROCESSANDO/SUGERIDA/FALHA) processado
por uma tarefa assíncrona in-process do próprio Core (`asyncio.create_task`),
sem broker externo (Celery/Redis/RabbitMQ). Isso evita infraestrutura
desnecessária, mantém idempotência via chave de job, e é suficiente para
demonstrar estados, falha tratada e retomada. Fica registrado como débito
técnico: para lote real e múltiplos workers horizontais, será necessário
migrar para uma fila real (RabbitMQ/Redis/Celery ou similar) — backlog
EP-11.

## Cascata de decisão do AI Engine (reduzida para a demo)

Implementados os níveis 0, 1 e 3 do PRD (seção 14.1):
- Nível 0 — validação (resposta vazia/curta demais → falha tratada, sem IA).
- Nível 1 — regras/conceitos obrigatórios simples (contribuem como sinal de
  confiança, não substituem a IA).
- Nível 3 — LLM local (Ollama, modelo configurável via `.env`) aplica a
  rubrica e devolve JSON validado por schema.
- Nível 2 (embeddings) fica no backlog: normalmente comporia parte do sinal
  de confiança/roteamento; a demo calcula confiança combinando validade do
  schema + concordância de regras + resposta do LLM, mas sem embeddings
  dedicados (ver `docs/backlog.md` e a limitação registrada no relatório
  final).
- Nível 4 — humano: sempre presente (revisão obrigatória na tela de
  aprovação).

## Confiança — cálculo e limitação (RN-016)

A confiança é calculada e versionada (`confidence_method_version` no
`AIExecution`), combinando: validade do schema retornado, presença de
evidência textual por critério, e sinal de regras (conceitos obrigatórios
identificados). **Não é uma probabilidade calibrada** — é um indicador
heurístico operacional de necessidade de revisão, como o PRD exige (seção
14.3). Faixas: alta ≥ 85%, média 60–84%, baixa < 60% (mesmos limiares
iniciais do PRD, ainda não calibrados com dados humanos — pendência D-07).

## Modo simulado (contingência) — RN-017

Existe um modo simulado explícito no AI Engine (`AI_ENGINE_MODE=simulated`),
usado apenas quando o runtime Ollama está indisponível ou para testes sem
GPU/CPU suficiente. Ele **nunca é acionado silenciosamente**: toda saída
inclui o campo `"engine_mode": "real" | "simulated"`, e o Core propaga esse
campo para a interface, marcando claramente análises simuladas.

## Autenticação e RBAC (ADR-007)

JWT stateless (access + refresh), hash de senha com bcrypt, papéis
`professor`/`admin` (demo reduz a matriz de perfis do PRD aos dois
necessários ao fluxo). Autorização checada no servidor em cada endpoint
sensível, nunca só na interface (RNF-01, checklist de PR do PRD).

## Banco de dados

PostgreSQL 16, migrações versionadas com Alembic. Entidades mínimas da demo:
`User`, `Assessment`, `Question`, `Rubric`, `RubricCriterion`, `Answer`,
`CorrectionJob`, `AIExecution`, `CriterionScore`, `HumanReview`,
`AuditEvent`. Entidades do modelo conceitual completo do PRD (Organization,
Course/Subject/Class, Student, Submission separada de Answer,
IntegrationClient, ExportJob, ModelRegistry) ficam no backlog — ver
`docs/backlog.md`.

## Ambientes

`ENV=development|homolog|production` via `.env` (ver `.env.example` em cada
serviço). Nesta entrega, apenas `development` foi de fato executado e
validado localmente; `homolog` e `production` têm configuração de exemplo
preparada mas não implantada (ver `docs/relatorio-entrega.md`).
