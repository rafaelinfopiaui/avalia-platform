---
id: "EXEC-2026-10-14-03"
tipo: execucao
sprint: "AV-S06B (complemento — resposta por imagem)"
gerado_em: "2026-10-14T03:00:00-03:00"
executor: "Hermes (desenho + consolidação), Antigravity (revisão independente do desenho e, depois, da implementação), Claude Code (implementação), Codex (auditoria pontual condicional)"
status: "abertura — desenho aprovado com ajustes; implementação local a seguir, sem publicação"
commit_referencia: "b818961 (main, backend AV-S06B integrado); branch feat/av-s06b-resposta-por-imagem"
---

# Snapshot EXEC-2026-10-14-03 — Abertura: resposta por imagem (complemento AV-S06B)

> Registro histórico. Não promove baseline. Snapshot de abertura de sub-fatia.

## 1. Abertura

- objetivo: resolver a lacuna contratual identificada na homologação do backend
  AV-S06B (upload exigia `Answer` pré-existente, mas `Answer` exigia `text`
  não-vazio) adotando o fluxo de resposta por imagem (`DEC-AV-037`): a foto é a
  entrada inicial da resposta, sem texto fictício; correção bloqueada até
  transcrição confirmada. Inclui a interface de upload (complemento frontend);
- autorização: `DEC-AV-037` — direção de produto aprovada; execução local
  autorizada após a revisão do desenho;
- escopo: contrato (modelo/migração/endpoint/guard) + interface; reuso do backend
  de imagens homologado sem ampliar sua homologação;
- fora de escopo: OCR, transcrição simulada, confirmação fictícia, exclusão,
  retenção operacional, stage/commit/push/merge nesta rodada, migração
  operacional em bancos protegidos, P5, seed, deploy, baseline, novo benchmark;
- branch: `feat/av-s06b-resposta-por-imagem` (checkout principal, sem worktree),
  criada a partir de `main` em `b818961`;
- working tree inicial: só o plano de complemento frontend (untracked), preservado.

## 2. Desenho e sua revisão independente

- desenho técnico: `evidence/AV-S06B/desenho_resposta_por_imagem.md` (v2);
- revisão independente do DESENHO (Antigravity, Gemini 3.8 Flash High):
  **APROVADO COM AJUSTES** — parecer em
  `evidence/AV-S06B/revisao_desenho_antigravity.md`. 6 achados (ACH-01..06) e
  recomendações, todos técnicos/detalhamento, nenhum exigindo decisão de produto
  nova. Ajustes incorporados na v2 do desenho (seção 12);
- validação própria do Hermes (pré-desenho): confirmado por varredura que
  `CorrectionJob(`/`run_correction_job` têm ponto único de criação/disparo
  (`request_correction`, main.py:658/665) — o guard cobre 100% dos caminhos.

## 3. Entregas

| Item | Estado | Entrega | Evidência |
|---|---|---|---|
| Contrato resposta por imagem (DEC-AV-037) | desenho aprovado com ajustes | ver sprint §17 e desenho v2 | implementação/validação a registrar no encerramento |
| Interface de upload (complemento frontend) | planejado | ver plano + sprint §17 | a registrar no encerramento |

## 4. Não entregas e lacunas

A preencher no encerramento. Nesta fatia a resposta por imagem termina
legitimamente em "aguardando transcrição" (sem OCR). `BL-AV-4B-05` permanece
pendente (retenção/exclusão operacional não decididas).

## 5. Validações executadas (até a abertura)

| Data/fuso | Item | Procedimento | Tipo | Resultado |
|---|---|---|---|---|
| 2026-10-14 | caminhos de correção | grep de `CorrectionJob(`/`run_correction_job`/`background_tasks.add_task` em `app/` | inspeção | ponto único em `request_correction` (main.py:658/665) — guard cobre tudo |
| 2026-10-14 | contrato atual Answer | leitura de models.py/main.py/schemas.py | inspeção | `Answer.text` NOT NULL; `POST /v1/answers` exige text; upload exige Answer existente — lacuna confirmada |
| 2026-10-14 | revisão do desenho | `agy -p` (Antigravity) sobre o desenho | revisão independente | APROVADO COM AJUSTES, 6 achados incorporados |

## 6. Decisões, débitos e bloqueantes

- decisão: `DEC-AV-037` (direção de resposta por imagem) registrada;
- débitos: lacuna contratual sendo resolvida por esta sub-fatia; `BL-AV-4B-05`
  segue pendente;
- bloqueantes: nenhum novo. Confirmar transcrição (AV-S08B) depende de OCR
  (`BL-AV-4B-02`), fora desta fatia.

## 7. Estado final

A preencher no encerramento desta sub-fatia (após implementação + validação em
banco isolado + revisão independente da implementação).

## 8. Baseline

- promove baseline? não;
- condição para promoção: inalterada.

## 9. Próxima ação

Claude Code implementa o contrato e a interface; Hermes valida em banco isolado;
Antigravity revisa a implementação de forma independente. Sem publicação nesta
rodada.

## 10. Adendos

Nenhum ainda.
