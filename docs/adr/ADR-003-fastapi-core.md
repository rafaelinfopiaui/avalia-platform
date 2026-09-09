# ADR-003 — FastAPI e organização do Core

Status: Aceito — 09/09/2026
Responsável: G1 (Core)

## Decisão
Core API em Python 3.11 + FastAPI, camadas: `api/` (rotas), `services/`
(regras de negócio), `models/` (SQLAlchemy ORM), `schemas/` (Pydantic),
`db/` (sessão/engine), `alembic/` (migrações). Segue diretamente a
tecnologia de referência do PRD (seção 11).

## Justificativa
Tecnologia já indicada no PRD como referência; sem decisão nova necessária.
