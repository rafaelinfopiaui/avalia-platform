---
id: BASELINE-001
capturado_em: "2026-09-21"
tipo: baseline_herdado_candidato
status: aguardando_validacao_e_homologacao
commit_referencia: 0be691e12e9d5d6f3ffc989237739f6559d8dacd
---

# BASELINE-001 — Estado herdado do AvalIA

## 1. Limite deste baseline

Registro inicial produzido por inspeção de Git, arquivos versionados e documentação. Nenhuma suíte, build, teste visual, integração real, serviço, banco ou inferência foi executada nesta coleta. Portanto, este é um **baseline documental candidato**, não um baseline funcional validado nem uma homologação.

## 2. Repositório observado

- caminho real: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform`;
- raiz Git confirmada: o mesmo caminho;
- remoto: `origin https://github.com/rafaelinfopiaui/avalia-platform.git` para fetch/push;
- branch: `main`, alinhada ao apontamento local `origin/main` no início da execução;
- commit: `0be691e12e9d5d6f3ffc989237739f6559d8dacd`;
- working tree inicial: somente `docs/roteiro-apresentacao-supervisor.md` não rastreado, preexistente e preservado;
- governança versionada prévia: não identificada.

A confirmação de `origin/main` foi local; nenhum fetch remoto foi necessário ou realizado nesta tarefa.

## 3. Estado herdado por inspeção

| Área | Evidência observada | Limite |
|---|---|---|
| Produto | README classifica o AvalIA como demonstração experimental e proíbe uso com dados reais | não houve reavaliação de produto |
| Core | código Python/FastAPI, requisitos, Alembic e `app/tests/test_core_flow.py` estão versionados | comportamento não reexecutado |
| AI Engine | código FastAPI/Ollama, requisitos, schema e sete arquivos de teste/conftest/pytest config identificados | Ollama e testes não executados |
| Frontend | React/Vite/TypeScript, `package.json` e fontes versionados | build e navegador não executados |
| Infra | pasta/configuração descrita nos documentos do projeto | operação local não inspecionada |
| ADRs | ADR-001 a ADR-008 versionados | decisões mantidas como estado herdado |
| Requisitos | `docs/requisitos-utilizados.md` referencia PRD v1.0 de 01/09/2026 | PRD não está versionado no repositório |
| Backlog | `docs/backlog.md`, `docs/decisoes-pendencias.md` e `docs/pendencia-regulatoria.md` existem | prioridade atual não foi decidida |

## 4. Requisitos e fontes

- referência de requisitos versionada: [`docs/requisitos-utilizados.md`](../../requisitos-utilizados.md);
- PRD citado: `PRD_AvalIA_v1.0_Completo.docx`, encontrado em `/Users/rafaeloliveira/Downloads/` junto de uma versão PDF, fora do repositório;
- ADRs: [`docs/adr/`](../../adr/);
- backlog: [`docs/backlog.md`](../../backlog.md);
- decisões abertas: [`docs/decisoes-pendencias.md`](../../decisoes-pendencias.md);
- pendência regulatória: [`docs/pendencia-regulatoria.md`](../../pendencia-regulatoria.md).

Não foram inventados requisitos para preencher lacunas. A decisão sobre versionar ou não o PRD é `DEC-AV-004`.

## 5. Evidências históricas — não reexecutadas

| Origem | Data declarada | Registro histórico |
|---|---|---|
| [`docs/relatorio-entrega.md`](../../relatorio-entrega.md) | 2026-09-09 | 8 testes Core e 21 AI Engine; build frontend; integração E2E e inferências reais, com limitações declaradas |
| `docs/relatorio-consolidado-avalia-2026-09-10.txt` | 2026-09-10 | 10 Core e 21 AI Engine; verificações HTTP; corrige alegação de CI e separa históricos |
| `docs/roteiro-apresentacao-supervisor.md` (não rastreado no início) | 2026-09-11 | 11 Core, 21 AI Engine, build frontend e integrações reais; também registra ausência de validação visual naquela preparação |
| commit `0be691e` | 2026-09-10 | correções de login demo, fluxo de análise e loop de sessão expirada, conforme assunto/diff do commit |

Esses resultados não são apresentados como atuais nesta execução. Divergências numéricas refletem evolução histórica da suíte e reforçam a necessidade de nova validação antes de uma alegação presente.

## 6. Débitos, bloqueantes e decisões iniciais

- débitos: [registro canônico](../registers/technical_debts.md);
- bloqueantes: [registro canônico](../registers/blockers.md);
- decisões: [registro canônico](../registers/decisions.md).

## 7. Baseline e promoção

Este registro não é promovido automaticamente. O ponteiro de baseline validado permanece sem baseline até decisão explícita de Rafael, após as revalidações que ele considerar necessárias.

## 8. Próxima ação

Homologar ou ajustar a governança e decidir quais verificações serão exigidas para promover um baseline funcional. Isso antecede o planejamento detalhado da próxima trilha.
