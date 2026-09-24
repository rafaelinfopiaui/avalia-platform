---
id: GOV-001
tipo: implantacao-documental
status: concluida_aguardando_homologacao
abertura: "2026-09-21"
responsavel_consolidacao: Hermes
homologacao: pendente_Rafael
---

# GOV-001 — Instituição da governança técnica do AvalIA

> Esta é uma execução exclusivamente documental. `GOV-001` identifica o rito de implantação da governança; não renumera nem converte o desenvolvimento herdado em sprint funcional fictícia.

## 1. Objetivo

Instituir no AvalIA um rito técnico auditável para abertura de execução, planejamento e acompanhamento de sprints, registro de evidências, snapshots obrigatórios, fechamento e atualização do Dashboard Executivo de Evolução Técnica.

## 2. Escopo autorizado

- criar políticas, templates, índices, registros iniciais, snapshot e dashboard;
- registrar apenas fatos sustentados pela inspeção desta execução;
- atualizar minimamente o README e as instruções de contexto dos agentes;
- preservar código, dependências, banco, infraestrutura, serviços e alterações locais preexistentes;
- não planejar a próxima trilha funcional, fazer deploy, commit, push, tag ou alteração remota.

## 3. Artefatos previstos

1. índice e seis políticas canônicas em `docs/governance/`;
2. templates reutilizáveis de sprint, snapshot de execução e fechamento;
3. registros canônicos de débitos, bloqueantes e decisões;
4. baseline herdado, snapshot desta execução e ponteiros separados para última execução e último baseline validado;
5. Dashboard Executivo inicial;
6. instrução obrigatória de leitura da governança em `AGENTS.md` e link de entrada no `README.md`.

## 4. Mapa de impacto

| Área | Caminhos previstos | Natureza |
|---|---|---|
| Governança | `docs/governance/**` | novos documentos Markdown |
| Contexto de agentes | `AGENTS.md` | nova instrução documental |
| Entrada do projeto | `README.md` | link mínimo para a governança |
| Código e operação | `core/`, `ai-engine/`, `frontend/`, `infra/`, manifests, banco e serviços | sem alteração autorizada |

Qualquer ampliação fora deste mapa exige decisão prévia de Rafael.

## 5. Critérios de aceite

- políticas adaptadas ao AvalIA, sem regras, tecnologias, thresholds ou scores transplantados;
- papéis e autoridade explícitos, sem atribuir homologação ou revisão que não ocorreu;
- rito completo de abertura, planejamento, execução, snapshot e encerramento;
- templates utilizáveis e fontes canônicas sem duplicação desnecessária;
- baseline com limites de verificação e resultados antigos identificados como históricos;
- dashboard distingue implementação, validação, última execução e baseline;
- links locais e consistência documental verificados;
- diff limitado a documentação/contexto, preservando a alteração preexistente;
- snapshot de execução gerado, com homologação de Rafael ainda pendente.

## 6. Fontes institucionais adotadas

Fontes somente leitura consultadas em 2026-09-21:

- `sentilytics-core/docs/governance/engineering/sprint_management_policy.md`;
- `sentilytics-core/docs/governance/engineering/definition_of_ready.md`;
- `sentilytics-core/docs/governance/engineering/sprint_closure_gate.md`;
- `sentilytics-core/docs/governance/organization/execution_policy.md`;
- `escutaelege/docs/governance/sprint_management_policy.md`;
- `escutaelege/docs/governance/sprint_closure_gate.md`;
- `escutaelege/docs/governance/executive_technical_dashboard.md`;
- `escutagov/docs/governance/documentation_policy.md`;
- exemplos efetivamente usados de sprint, closure e snapshot nos três projetos.

Adotam-se os princípios de planejamento prévio, DoR, mapa de impacto, delegação delimitada, evidência real, snapshot obrigatório e consolidação centralizada. Não se adotam automaticamente: scores de maturidade/prontidão, story points, thresholds de cobertura, tecnologias, caminhos absolutos, papéis artificiais, regras específicas de outros produtos ou o preenchimento de checklists por conveniência.

O `sprint_template.md` do Sentilytics-Core e o `snapshot_template.md` do EscutaGov foram tratados como modelos genéricos/propostas: contêm caminhos e métricas específicos e não comprovam uso no AvalIA. Os registros reais mais recentes foram usados para identificar práticas efetivas e também falhas a evitar, como sprint retroativa, snapshot ausente, baseline promovido automaticamente e alegações antigas tratadas como atuais.

## 7. Estado de abertura registrado

- repositório real: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform`;
- remoto confirmado: `https://github.com/rafaelinfopiaui/avalia-platform.git`;
- branch/commit de referência: `main` em `0be691e12e9d5d6f3ffc989237739f6559d8dacd`;
- estado inicial: `main...origin/main`, com `docs/roteiro-apresentacao-supervisor.md` já não rastreado antes desta execução;
- governança versionada prévia: não encontrada;
- bloqueante desta implantação: nenhum identificado;
- homologação desta implantação: ainda não realizada por Rafael.

## 8. Backlog desta execução

| ID | Entrega | Responsável | Estado |
|---|---|---|---|
| GOV-001-01 | Políticas e índice | Hermes | implementado; validação documental concluída |
| GOV-001-02 | Templates e registros canônicos | Hermes | implementado; validação documental concluída |
| GOV-001-03 | Baseline herdado e dashboard inicial | Hermes | implementado; baseline não promovido |
| GOV-001-04 | Instruções de agentes e link no README | Hermes | implementado; validação documental concluída |
| GOV-001-05 | Validação documental e snapshot | Hermes | concluído; evidências no snapshot EXEC-2026-09-21-01 |
| GOV-001-06 | Homologação da implantação | Rafael | pendente; fora da autoridade do executor |

## 9. Validações previstas

- inventário Git antes/depois e diff por tipo de arquivo;
- verificação de links Markdown locais;
- busca por referências indevidas aos produtos-fonte, caminhos absolutos e alegações de aprovação;
- `git diff --check`;
- conferência de que nenhuma extensão funcional ou operacional foi alterada;
- registro literal dos comandos, data, ambiente e resultados no snapshot final.

## 10. Ajustes de percurso

Nenhum no momento da abertura.

## 11. Encerramento

**Estado da execução:** concluída documentalmente, aguardando homologação de Rafael.

**Snapshot:** [`EXEC-2026-09-21-01`](../snapshots/snapshot_EXEC-2026-09-21-01_GOV-001.md).

**Closure gate aplicado:**

- escopo e critérios documentais avaliados: atendidos;
- mudanças limitadas a Markdown/contexto de agentes: atendido por inspeção de paths e diff;
- evidências documentais com comando/data/ambiente/resultado: atendido no snapshot;
- snapshot e dashboard: atendidos;
- última execução e baseline validado separados: atendido;
- alteração preexistente preservada: atendido;
- código, dependências, banco, infraestrutura e serviços: sem alteração;
- commit, push, tag, deploy e alteração remota: não realizados;
- revisão independente/delegação: não ocorreram e não são declaradas;
- homologação por Rafael: pendente, sem aprovação presumida.

README, requisitos/PRD, backlog/roadmap e ADRs foram revisados. Apenas o README exigiu atualização mínima de entrada; os demais não exigiram alteração porque esta execução não mudou requisito, capacidade funcional ou prioridade.

A próxima trilha não foi iniciada. O próximo passo é a revisão desta implantação por Rafael.