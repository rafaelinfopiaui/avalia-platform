# ADR-007 — Autenticação e RBAC

Status: Aceito — 09/09/2026
Responsável: G1 + QA

## Decisão
JWT stateless (access token curto + refresh token), hash de senha com
bcrypt (via passlib), papéis reduzidos a `professor` e `admin` para a demo
(matriz completa de perfis do PRD — Coordenador/Aluno/Pesquisador/Sistema
externo — fica no backlog). Autorização checada em middleware do servidor
em toda rota sensível; nunca delegada só à interface.

## Justificativa
JWT é simples de implementar sem infraestrutura de sessão compartilhada
(sem Redis), compatível com o recorte simples da demo. Papéis reduzidos
cobrem exatamente os atores do fluxo demonstrado (professor cria/revisa,
admin existe para dados de seed).

## Consequências
Revogação de token antes da expiração não implementada nesta demo (backlog:
blacklist ou sessão revogável, RF-01 completo).
