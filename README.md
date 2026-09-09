# AvalIA — Plataforma independente de correção assistida com IA local

> avaliação inteligente, ensino forte

Este repositório é o produto **AvalIA**, independente do laboratório de treinamento
`avalia-github-lab`. Histórico Git, branches e remoto são próprios deste repositório.

Status atual: **demonstração experimental**, em desenvolvimento ativo. Não é MVP
completo e não está autorizado para uso com dados reais de estudantes (ver
`docs/pendencia-regulatoria.md`).

## Visão geral

O AvalIA apoia professores na correção de respostas discursivas curtas/médias.
A IA sugere pontuação por critério com justificativa e evidência; o professor
examina, altera ou confirma. A nota final é sempre uma decisão humana registrada
e auditável.

## Componentes (monorepo — ver `docs/adr/ADR-002-monorepo.md`)

| Componente | Pasta | Tecnologia | Responsabilidade |
|---|---|---|---|
| Core API | `core/` | Python + FastAPI + SQLAlchemy + Alembic | Autenticação, RBAC, avaliações, rubricas, respostas, correções, notas humanas, auditoria |
| AI Engine | `ai-engine/` | Python + FastAPI + Ollama (local) | Pré-processamento, embeddings, prompt, inferência local, schema de saída, confiança |
| Frontend | `frontend/` | React + Vite + TypeScript | Interface do professor (consome somente o Core API) |
| Infra | `infra/` | Docker Compose | Orquestração local dev/homolog |
| Docs | `docs/` | Markdown | Requisitos usados, ADRs, contratos, backlog, pendências |

## Como iniciar (macOS e Windows/WSL2)

Ver instruções completas em `docs/como-iniciar.md`. Resumo rápido (macOS):

```bash
# 1. Banco
brew services start postgresql@16

# 2. Modelo local (IA)
brew services start ollama
ollama pull qwen2.5:7b-instruct-q4_K_M

# 3. Core API
cd core && python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed  # dados fictícios
uvicorn app.main:app --reload --port 8000

# 4. AI Engine
cd ai-engine && python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001

# 5. Frontend
cd frontend && npm install && npm run dev
```

## Documentação

- `docs/requisitos-utilizados.md` — requisitos do PRD usados nesta demonstração
- `docs/arquitetura.md` — resumo de arquitetura e decisões
- `docs/adr/` — decisões arquiteturais curtas
- `docs/contracts/` — contratos de API (OpenAPI) e schema do AI Engine
- `docs/decisoes-pendencias.md` — decisões abertas do PRD e status
- `docs/backlog.md` — backlog restante por frente
- `docs/pendencia-regulatoria.md` — pendência CNE/IA em avaliações
- `docs/roteiro-demo.md` — roteiro de demonstração para o coordenador
- `docs/relatorio-entrega.md` — implementado / validado / simulado / bloqueado

## Identidade visual

Azul-marinho `#0D1B3D`, teal `#0FA49A`, ciano `#00C2E8`, violeta `#7B61FF`,
cinza-claro `#F4F6F8`. Tipografia: Poppins (títulos) + Inter (texto). Interface
em pt-BR, acessível por teclado, foco visível, mensagens de erro úteis.

## Governança deste repositório

Squad de 9 integrantes (ver PRD, seção 20) treina atualmente no laboratório
`avalia-github-lab`. Este repositório do produto real é mantido separado e não
concede acesso automático à squad — acesso será concedido pelo Tech Leader
quando decidido (ver seção "Git local e pendências" em
`docs/relatorio-entrega.md`).
