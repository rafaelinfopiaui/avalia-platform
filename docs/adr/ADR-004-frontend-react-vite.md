# ADR-004 — Frontend: React + Vite + TypeScript

Status: Aceito — 09/09/2026
Responsável: Rafael Sampaio Oliveira (Tech Leader) / G2

## Contexto
PRD indica "React/Next.js ou equivalente aprovado em ADR" (D-01 em aberto).
A demo é uma SPA pura, API-first, sem necessidade de SSR/rotas de servidor.

## Decisão
React 18 + Vite + TypeScript. Roteamento client-side (react-router).
Consome exclusivamente o Core API via fetch/axios com JWT em header.

## Justificativa
- Vite tem build/dev-server mais simples que Next.js para uma SPA sem SSR,
  reduzindo tempo de setup sob prazo curto.
- Next.js adicionaria complexidade de rotas de servidor sem necessidade real
  aqui (o backend já é o Core API separado).
- Squad pode revisitar para Next.js se precisar de SSR/SEO no futuro
  (não é o caso de um painel interno autenticado).

## Consequências
Sem SSR; se precisar de SEO público futuramente (ex.: landing page
comercial), avaliar Next.js separadamente para essa parte.
