# Registro de publicação — Pacote B / AV-S05B

## Abertura (2026-09-30, -03:00)

- objetivo: publicar a investigação OCR parcial em branch dedicada e PR em rascunho;
- checkout: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform-worktrees/av-s05b-publish`;
- raiz Git: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform-worktrees/av-s05b-publish`;
- branch: `docs/av-s05b-investigacao`;
- base Git: `origin/main@a5974b1ffecc18f59ed2df39bdf5ce4a210bf0e8`;
- estado inicial deste worktree: limpo antes da cópia seletiva dos arquivos;
- fonte local: worktree `av-s03-work`, branch `main`, mesma base Git, com alterações
  documentais não incorporadas dos pacotes A e B;
- alterações locais conhecidas fora deste pacote: GOV-006, correções de
  backlog/dashboard/AV-S03, snapshots da reconciliação e a proposta de saneamento de 676
  linhas no checkout principal;
- consolidador: Hermes;
- autorização: Rafael autorizou stage/commit/push e PR em rascunho, sem merge.

## Escopo desta branch

- ADR-009 em rascunho;
- sprint AV-S05B;
- snapshot do benchmark;
- protocolo, scripts e evidências permitidas em `docs/governance/evidence/AV-S05B/`;
- DEC-AV-017 em `decisions.md`.

## Fora de escopo

- homologação de solução OCR para produto;
- execução de coleta manuscrita ou revisão humana;
- código de produção, deploy, `avalia_dev`, saneamento operacional e merge;
- arquivos compartilhados `dashboard`, `backlog` e `latest_execution`, que serão
  consolidados pelo Pacote A empilhado sobre este HEAD para evitar sobrescrita.

## Estado factual obrigatório

A investigação é parcial. Manuscrito e medição de revisão humana permanecem pendentes.
Nenhuma solução OCR foi homologada para o produto.
