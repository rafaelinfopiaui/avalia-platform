# Backlog restante (por frente)

Esta demonstração cobre uma fatia vertical do MVP do PRD (seção 4 do pedido
original), não o MVP inteiro. O restante do PRD permanece como backlog,
organizado pelas 4 frentes do PRD (seção 20).

## G1 — Core & Backend
- Estrutura acadêmica completa (Organization/Course/Subject/Class/Student,
  RF-02) — hoje reduzida a um vínculo mínimo professor↔avaliação.
- Importação de respostas via CSV com prévia/erros por linha (RF-06).
- Processamento em lote com progresso, pausa/cancelamento, retentativa
  (RF-08, EP-11).
- Segunda revisão configurável, liberação de resultado ao aluno, exportação
  (RF-11).
- API pública versionada, chaves com escopo, webhooks assinados (RF-14).
- Migração da fila in-process para broker real quando houver lote (ADR-006).
- Auditoria de pesquisa com dataset anonimizado (RF-15).

## G2 — Frontend & UX
- Dashboards pedagógicos/operacionais (RF-12).
- Wizard completo de importação CSV.
- Fila de revisão com filtros avançados (baixa confiança, falhas, grandes
  divergências) — a demo tem uma lista simples.
- Teste de usabilidade formal com usuários (meta ≥ 90% sem ajuda crítica,
  seção 4.2 do PRD) — não medido nesta entrega.
- Auditoria completa de acessibilidade (WCAG) — a demo aplica boas práticas
  básicas (foco visível, contraste, navegação por teclado) sem auditoria
  formal.

## G3 — AI Engine & Research
- Nível 2 da cascata (embeddings/Sentence Transformers) para similaridade
  semântica dedicada.
- Calibração de confiança com dataset piloto real (D-07 do PRD).
- Suite dourada de respostas para regressão (AI-012).
- Benchmark formal de modelo/quantização com hardware documentado (AI-013).
- Proteção mais robusta contra prompt injection além da checagem básica
  implementada.
- Protocolo de validação científica (seção 27 do PRD) — não iniciado.

## G4 — QA & Platform
- CI/CD completo (a demo tem workflow básico de lint+testes, sem deploy).
- Ambiente de homologação real (hoje só exemplo de configuração).
- Scanner de segredos/dependências automatizado.
- Observabilidade avançada (tracing distribuído, alertas).
- Testes de carga/concorrência (respostas simultâneas, lote grande).
- Runbooks operacionais completos (seção 19.1 do PRD) — apenas o de "AI
  Engine indisponível" foi exercitado nesta entrega.

## Transversal
- Verificação da pendência regulatória CNE (ver
  `docs/pendencia-regulatoria.md`) — bloqueante para uso real, não para a
  demo experimental.
- Decisões D-01 a D-12 do PRD (seção 29): status em
  `docs/decisoes-pendencias.md`.
