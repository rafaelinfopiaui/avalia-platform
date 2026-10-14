---
id: "EXEC-2026-10-14-05"
tipo: execucao
sprint: "AV-S06B (fatia DEBT-AV-014 — retomada de respostas por imagem)"
gerado_em: "2026-10-14T06:00:00-03:00"
executor: "Hermes (desenho/verificação), Claude Code (implementação), Antigravity (revisão independente)"
status: "aberta — planejamento registrado antes do código; rodada LOCAL (sem git nesta fatia)"
base: "main cf81109655713fac856aab0b26ba36e1bb5f15bc"
branch: "feat/av-s06b-debt-014-retomada-respostas-imagem"
---

# Snapshot EXEC-2026-10-14-05 — Abertura: retomada de respostas por imagem (DEBT-AV-014)

> Registro de abertura. Rodada LOCAL. Sem stage/commit/push nesta fatia (ordem de
> Rafael). Não promove baseline. Planejamento (escopo/ACs) registrado ANTES do código.

## 1. Autorização e alcance

Rafael autorizou (2026-10-14), após a homologação (DEC-AV-038) e integração do
PR #16 (merge commit `cf81109655713fac856aab0b26ba36e1bb5f15bc`, CI pós-merge
success), o planejamento e a implementação **LOCAL** da recuperação de envios
persistidos de resposta por imagem — resolução do `DEBT-AV-014`. Branch dedicada no
checkout principal, sem worktree. Claude Code implementa; Antigravity revisa de
forma independente; Codex só diante de risco concreto.

## 2. Escopo

- Backend: endpoint GET de listagem autenticada de respostas por imagem por
  avaliação (filtrável por questão), com estado e imagens (sem `storage_filename`).
- Frontend: a tela de resposta por foto busca e reexibe as respostas por imagem
  persistidas da avaliação/questão ao carregar, após recarregar e em nova sessão.

Fora de escopo: transcrição manual, confirmação, OCR, exclusão/retenção, qualquer
correção/IA sobre resposta por imagem.

## 3. Regra de autorização (leitura histórica)

Leitura por **propriedade** (padrão homologado `list_assessments`/`get_assessment`),
SEM exigir vínculo ativo de turma. Dono lê; não-dono 403; sem token 401. Não
introduzir `require_active_class_link` na leitura.

## 4. Critérios de aceite

ACD-01..ACD-10 em `evidence/AV-S06B/desenho_debt_014_retomada.md` §6.

## 5. Limites

Sem stage/commit/push nesta fatia. Sem bancos protegidos, migração operacional, P5,
seed, deploy, baseline, OCR, transcrição manual. Progresso homologado permanece
**19/70**; AV-S05B parcial; BL-AV-4B-05 pendente.

## 6. Encerramento

A preencher no snapshot de encerramento desta fatia (EXEC-2026-10-14-06), com
resultado, diff local e revisão independente.
