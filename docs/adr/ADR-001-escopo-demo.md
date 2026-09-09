# ADR-001 — Contexto, visão e fronteiras da demonstração

Status: Aceito — 09/09/2026
Responsável: Rafael Sampaio Oliveira (Tech Leader)

## Contexto
Prazo curto (demo na sexta 11/09/2026), squad em treinamento paralelo no
laboratório `avalia-github-lab`, necessidade de avançar o produto real sem
depender da disponibilidade dos 9 integrantes.

## Decisão
Implementar uma fatia vertical ponta a ponta do MVP do PRD (login → criar
avaliação/questão/rubrica → validar rubrica → inserir resposta → analisar
com IA local → revisar → persistir decisão humana), com dados fictícios,
priorizada sobre dashboards, OCR, LMS, cobrança e demais funcionalidades
P1+.

## Consequências
- Boa parte do PRD (RF-02 completo, RF-08, RF-11 a RF-15) fica no backlog
  (`docs/backlog.md`).
- A demo é identificada como experimental (ver
  `docs/pendencia-regulatoria.md`).
