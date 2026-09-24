---
tipo: proposta_sprints
status: PROPOSTA
trilha: trilha_operacao_de_turma
gerado_em: "2026-09-21"
autor: Hermes
homologacao: pendente_Rafael
---

# Proposta de divisão em sprints — Trilha "Operação de uma turma"

> **Nenhuma sprint abaixo está aprovada.** Todas estão em `PROPOSTA`. Datas e velocidade não são fixadas por ausência de histórico de velocity sob esta governança. Estimativas são identificadas como estimativas e carregam suas premissas.
> **Atualização de escopo (2026-09-21):** adicionadas as sprints AV-S05B a AV-S10B (Etapa 4B — entrada por imagem). Nenhuma sprint pré-existente (AV-S01 a AV-S13) foi removida ou renumerada.
> **Reconciliação (2026-09-23, GOV-004):** `DEC-AV-016` foi aprovada por Rafael em 2026-09-21 (imagem priorizada sobre CSV). A leitura de sequenciamento vigente é a de 5 fases em §11 de [`trilha_operacao_de_turma.md`](trilha_operacao_de_turma.md): Fase 1 (AV-S01/S02) → Fase 2 (AV-S05B) → Fase 3 (AV-S03/S04) → Fase 4 (AV-S06B a AV-S10B) → Fase 5, ampliação operacional (AV-S05/S06 CSV, AV-S07/S08 lote, AV-S09). A tabela abaixo preserva a ordem de leitura original de GOV-002/GOV-003 (por etapa numérica) e não foi reordenada linha a linha; a coluna "Dependências" de cada sprint já refletia dependências técnicas reais, não a ordem de leitura — usar §11 da trilha como referência de sequência de execução.

## 1. Tabela das sprints propostas

| Sprint | Etapa(s) | Marco | Foco | Itens (backlog) | Tamanho estimado* | Dependências |
|---|---|---|---|---|---|---|
| AV-S01 | 1 | 1 | Autorização por vínculo, retomada de fluxo, revalidação | BL-AV-1-01, 02, 03, 04, 07, 08 | M | Nenhuma; primeira sprint candidata |
| AV-S02 | 1 | 1 | CI mínima, validação visual documentada e isolamento de testes do AI Engine | BL-AV-1-05, 06, 09 | P/M | AV-S01 homologada; decisão sobre ambiente de BL-AV-1-05 (`DEC-AV-006`) incorporada à aprovação deste plano; execução remota da CI exige autorização Git específica posterior |
| AV-S03 | 2 | 1 | Estrutura acadêmica mínima | BL-AV-2-01..05 | G | AV-S01; `DEC-AV-007` (dimensionamento inicial pode usar suposição documentada) |
| AV-S04 | 3 | 1 | Avaliações com múltiplas questões | BL-AV-3-01..04 | M | AV-S03 |
| AV-S05 | 4 (parte 1) | 2 | Contrato e prévia de importação CSV | BL-AV-4-01, 02 | M | AV-S04 (rubrica/questão estáveis) |
| AV-S06 | 4 (parte 2) | 2 | Vínculo, duplicidade e registro de importação | BL-AV-4-03, 04, 05 | M | AV-S05; `DEC-AV-008` |
| AV-S05B | 4B (parte 1) | 2 | Investigação de OCR/visão local e decisão arquitetural | BL-AV-4B-01, 02, 17 | M | AV-S01 (padrão de autorização); `DEC-AV-017`, `DEC-AV-009` |
| AV-S06B | 4B (parte 2) | 2 | Recebimento, armazenamento e controle de acesso de imagens | BL-AV-4B-03, 04, 05 | M | AV-S05B aprovada; `DEC-AV-018`, `DEC-AV-019`, `DEC-AV-013` |
| AV-S07B | 4B (parte 3) | 2 | Preparação e extração local (execução real de OCR) | BL-AV-4B-06, 07, 08, 09 | G | AV-S06B; decisão arquitetural de AV-S05B implementável |
| AV-S08B | 4B (parte 4) | 2 | Conferência e confirmação da transcrição | BL-AV-4B-10, 11, 12, 13 | M | AV-S07B |
| AV-S09B | 4B (parte 5) | 2 | Associação, cadeia de rastreabilidade e idempotência | BL-AV-4B-14, 15, 16 | M | AV-S08B; etapa 2 (estrutura acadêmica) quando aplicável |
| AV-S10B | 4B (parte 6) | 2 | Avaliação e testes de OCR ponta a ponta | BL-AV-4B-18, 19 | M | AV-S09B |
| AV-S07 | 5 (parte 1) | 2 | Decisão de arquitetura de lote (ADR novo) | BL-AV-5-01, 02 | P | AV-S06; `DEC-AV-007`, `DEC-AV-009`; considerar `BL-AV-4B-17` se 4B e 5 competirem por hardware |
| AV-S08 | 5 (parte 2) | 2 | Implementação do processamento em lote | BL-AV-5-03, 04, 05, 06 | G | AV-S07 aprovado |
| AV-S09 | 6 | 2 | Fila de revisão, histórico agregado, exportação | BL-AV-6-01..05 | G | AV-S08 |
| AV-S10 | 7 (parte 1) | 2→3 | Conjunto de referência, framework e critérios de aceitação | BL-AV-7-01, 02, 06, 08 | M | Nenhuma técnica; pode correr em paralelo a AV-S05..S09 |
| AV-S11 | 7 (parte 2) | 2→3 | Regressão, robustez, benchmark, avaliação de embeddings | BL-AV-7-03, 04, 05, 07 | M | AV-S10; `DEC-AV-009` para benchmark |
| AV-S12 | 8 (parte 1) | 3 | Dashboard do produto e acessibilidade dirigida | BL-AV-8-01, 02 | M | AV-S09 |
| AV-S13 | 8 (parte 2) | 3 | E2E, carga, instalação reproduzível, homologação | BL-AV-8-03, 04, 05, 06 | G | AV-S12; `DEC-AV-006`; AV-S11; considerar AV-S10B se 4B estiver no escopo do piloto |

*Tamanho estimado: P (pequena), M (média), G (grande) — estimativa qualitativa por número/complexidade de itens, não por story points ou horas, na ausência de velocity histórica sob esta governança. Método: contagem de itens do backlog e dependências cruzadas por sprint, revisão qualitativa de complexidade técnica.

**Incertezas explícitas desta tabela:**

- AV-S07/AV-S08 podem ser fundidas ou divididas de novo após a decisão de arquitetura (`BL-AV-5-02`) revelar a complexidade real.
- AV-S10 pode iniciar antes de AV-S05 se Rafael priorizar a preparação da qualidade da IA; a ordem entre elas não é uma dependência técnica rígida.
- **A ordem relativa entre a linha AV-S05/S06 (CSV) e a linha AV-S05B..S10B (imagem) foi decidida por Rafael em 2026-09-21 (`DEC-AV-016`): imagem priorizada sobre CSV.** A tabela lista AV-S05B após AV-S06 apenas por convenção de leitura (agrupamento por número de etapa); a ordem de execução vigente é a de 5 fases do §11 do documento de trilha, onde a investigação de OCR (`AV-S05B`) é a segunda frente elegível (após a Fase 1) e o CSV (`AV-S05`/`S06`) passa a compor a Fase 5 (ampliação operacional), após a primeira entrega completa por imagem.
- AV-S07B (extração local real) e AV-S07/AV-S08 (lote) podem competir pelo mesmo hardware; se ambas forem priorizadas em paralelo, a decisão de isolamento de recursos (`BL-AV-4B-17`) deve ser resolvida antes de as duas rodarem simultaneamente no mesmo ambiente.
- Nenhuma data de calendário é proposta. Sequenciar por dependência, não por prazo, até haver decisão de prazo (`DEC-AV-015`).

## 2. Primeira sprint candidata — AV-S01

### 2.1 Objetivo e valor

Eliminar a lacuna de autorização por vínculo encontrada por inspeção nas rotas de resposta, correção e revisão, e resolver a retomada de fluxo que hoje depende de `sessionStorage` do navegador — ambos condição para o resultado esperado da Etapa 1 ("um professor completa e retoma o fluxo; outro professor não acessa seus dados"). Produzir, junto, uma revalidação datada da suíte existente.

### 2.2 Origem

| Item | Fonte |
|---|---|
| BL-AV-1-01/02 | Observação preliminar do usuário; achado de código nesta sessão em `core/app/main.py` |
| BL-AV-1-03 | Escopo explícito da tarefa do usuário; achado de código em `frontend/src/services/workflow.ts` e `ReviewPage.tsx` |
| BL-AV-1-04 | Decorrente de 01/02 |
| BL-AV-1-07 | Política de execução (não tratar relatório antigo como prova atual) |
| BL-AV-1-08 | RN-017, teste já existente em `core/app/tests/test_core_flow.py` |

### 2.3 Escopo

Incluído:
- reprodução em runtime da lacuna de autorização nas rotas `create_answer`, `request_correction`, `get_correction_job`, `review_correction`;
- correção dessas rotas para exigir vínculo de propriedade (mesmo padrão de `_get_owned_assessment`), preservando acesso do papel `admin`;
- suíte de regressão cobrindo os quatro endpoints com dois professores distintos;
- alteração do frontend para que a tela de revisão (e, se necessário, a de correção) recupere dados via API a partir do `id` da URL, em vez de depender exclusivamente de `sessionStorage`;
- revalidação da suíte pytest do Core e AI Engine e do build do frontend, com resultado datado.

Fora de escopo:
- estrutura acadêmica (etapa 2);
- CI versionada (AV-S02);
- validação visual completa do roteiro de demonstração (AV-S02);
- qualquer mudança de schema de banco além da estritamente necessária para a correção de autorização (não se prevê nenhuma nesta sprint).

### 2.4 Baseline e estado de abertura

- último baseline validado: nenhum (ver `BASELINE-001`, candidato);
- última execução registrada: GOV-001 (documental);
- commit/branch de referência a confirmar na abertura real (não fixado aqui, pois esta sprint ainda não foi aprovada);
- alterações preexistentes a proteger: `docs/roteiro-apresentacao-supervisor.md` e toda a árvore `docs/governance/` desta e da execução anterior.

### 2.5 Backlog e DoR

| ID | Descrição | Responsável | DoR | Estado |
|---|---|---|---|---|
| BL-AV-1-01 | Reproduzir em runtime a lacuna de autorização | a definir | refinado — falta decidir se dois usuários de teste serão criados via seed ou fixture nova | proposto |
| BL-AV-1-02 | Corrigir as quatro rotas | a definir | refinado — depende do resultado de 01 para confirmar escopo exato | proposto |
| BL-AV-1-03 | Retomada via API na tela de revisão/correção | a definir | refinado — falta decidir se é necessário novo endpoint (buscar resposta/avaliação a partir do `job_id`) ou se os dados já são suficientes | proposto |
| BL-AV-1-04 | Suíte de regressão de autorização cruzada | a definir | ready após 01/02 definirem o comportamento esperado | proposto |
| BL-AV-1-07 | Revalidação datada da suíte e build | a definir | ready — não depende de nenhuma decisão de produto | proposto |
| BL-AV-1-08 | Confirmar RN-017 após as correções | a definir | ready após 02 | proposto |

Nenhum item está `ready` sem ressalva; a sprint precisa de refinamento adicional (decisão de fixtures de teste e de necessidade de novo endpoint) antes do início formal, conforme a Definition of Ready.

### 2.6 Mapa de impacto provável

| Item | Criar | Alterar | Não tocar |
|---|---|---|---|
| BL-AV-1-01/04 | `core/app/tests/test_authorization_boundaries.py` (novo, nome provisório) | — | modelos e schemas existentes |
| BL-AV-1-02 | — | `core/app/main.py` (rotas `create_answer`, `request_correction`, `get_correction_job`, `review_correction`) | `core/app/deps.py` (reutilizar padrão existente, não recriar) |
| BL-AV-1-03 | possivelmente novo endpoint de leitura (ex.: `GET /v1/answers/{id}` ou equivalente, a decidir no refinamento) | `frontend/src/pages/ReviewPage.tsx`, `frontend/src/services/api.ts`, possivelmente `frontend/src/services/workflow.ts` | `frontend/src/pages/CorrectionPage.tsx` (já busca via API; validar se precisa de ajuste) |
| BL-AV-1-07 | — | nenhum arquivo de produto; apenas execução de comando e registro de resultado | — |
| BL-AV-1-08 | — | nenhuma alteração de código prevista; apenas execução do teste existente | `core/app/tests/test_core_flow.py` (não modificar o teste, só executá-lo) |

Qualquer novo endpoint necessário para BL-AV-1-03 deve ser registrado como ajuste de percurso e, se alterar o contrato público, refletido em `docs/contracts/openapi.yaml`.

### 2.7 Critérios de aceite

| ID | Critério | Método previsto | Estado |
|---|---|---|---|
| AC-01 | Professor B autenticado não consegue criar resposta, solicitar correção, consultar job ou registrar revisão sobre avaliação de Professor A | integração real (dois tokens reais) | não executado |
| AC-02 | Papel `admin` continua funcional nas quatro rotas após a correção | integração real | não executado |
| AC-03 | Abrir a URL de revisão diretamente (sem navegação prévia, sessionStorage vazio) carrega os dados corretos via API para um usuário autorizado | teste de frontend/e2e ou inspeção + teste manual documentado | não executado |
| AC-04 | Suíte de regressão dos quatro endpoints roda e passa | automatizada (pytest) | não executado |
| AC-05 | `test_ai_engine_unavailable_does_not_fabricate_result` continua passando após as mudanças | automatizada (pytest) | não executado |
| AC-06 | Suíte completa do Core e do AI Engine e build do frontend executados nesta sprint, com contagem real e data | automatizada + inspeção de saída | não executado |

### 2.8 Definition of Done

- [ ] AC-01 a AC-06 avaliados com evidência real;
- [ ] nenhuma rota de admin quebrada;
- [ ] mudanças vinculadas aos itens BL-AV-1-01 a 04, 07, 08;
- [ ] débitos/decisões residuais registrados nos registros canônicos com ID;
- [ ] snapshot de execução gerado;
- [ ] dashboard atualizado;
- [ ] closure gate desta sprint preenchido;
- [ ] README/contrato OpenAPI atualizado apenas se um endpoint novo for de fato criado.

### 2.9 Testes previstos

| Item/AC | Comando ou procedimento | Ambiente | Tipo |
|---|---|---|---|
| AC-01/02 | `pytest core/app/tests/test_authorization_boundaries.py -v` (novo arquivo) | SQLite de teste local | automatizada |
| AC-03 | teste de frontend (a definir framework) ou roteiro manual documentado com captura | navegador local | visual/integração real |
| AC-04 | `pytest core/app/tests -q` | ambiente de teste do Core | automatizada |
| AC-05 | `pytest core/app/tests/test_core_flow.py::test_ai_engine_unavailable_does_not_fabricate_result -v` | ambiente de teste do Core | automatizada |
| AC-06 | `pytest` (Core), `pytest` (AI Engine, modo simulado), `npm run build` (frontend) | ambiente local do executor | automatizada |

### 2.10 Riscos

| Risco | Impacto | Mitigação | Dono |
|---|---|---|---|
| BL-AV-1-01 pode não confirmar a lacuna (falso positivo da inspeção estática) | baixo — economiza trabalho, mas exige atualizar o backlog | registrar o resultado real e ajustar o item antes de prosseguir para 02 | executor da sprint |
| Correção de autorização quebra fluxo legítimo do próprio professor | médio | testar caminho feliz junto com caminho negativo (AC-02 cobre admin; adicionar caso equivalente para professor dono) | executor da sprint |
| BL-AV-1-03 exigir endpoint novo não previsto no contrato atual | médio | tratar como ajuste de percurso explícito, com decisão registrada antes de implementar | consolidador (Hermes) |
| Ambiente local desatualizado desde 11/09/2026 dificulta revalidação (AC-06) | médio | registrar exatamente o que falhou por ambiente vs. por código, sem misturar as duas causas | executor da sprint |

### 2.11 Closure gate previsto

Aplicar [`sprint_closure_gate.md`](../sprint_closure_gate.md) na íntegra ao encerrar. Critérios A1–A3, B1–B4, C1–C3 e D1–D2 são particularmente aplicáveis: nenhuma alegação de "corrigido" sem reprodução real prévia (B4), e nenhuma homologação presumida (D2).

## 3. Sprints AV-S02 a AV-S13 — nível de sequenciamento

As sprints abaixo estão detalhadas o suficiente para avaliar sequência e dependências. Cada uma será detalhada no nível da AV-S01 apenas quando a sprint anterior da mesma linha estiver encerrada ou explicitamente antecipada por decisão de Rafael.

- **AV-S02** (Etapa 1, Marco 1): CI mínima (`BL-AV-1-06`) e validação visual documentada do roteiro de demonstração (`BL-AV-1-05`). Depende de AV-S01 para não validar visualmente um fluxo com a lacuna de autorização ainda aberta.
- **AV-S03** (Etapa 2, Marco 1): modelo de dados acadêmico, migração, permissões por vínculo turma↔professor, telas mínimas. Depende de AV-S01 (padrão de autorização corrigido) e de decisão preliminar de dimensionamento (`DEC-AV-007`, pode usar suposição documentada se não houver decisão a tempo).
- **AV-S04** (Etapa 3, Marco 1): múltiplas questões por avaliação, regras de edição/publicação/imutabilidade, atualização de contrato. Depende de AV-S03 para vínculo coerente com turma.
- **AV-S05** (Etapa 4, parte 1, Marco 2): contrato de importação CSV e prévia com erros por linha. Depende de AV-S04 (rubrica/questão estáveis).
- **AV-S06** (Etapa 4, parte 2, Marco 2): vínculo aluno↔avaliação↔resposta via estrutura acadêmica, duplicidade/reenvio, registro de importação. Depende de AV-S05 e de `DEC-AV-008`.
- **AV-S05B** (Etapa 4B, parte 1, Marco 2): investigação técnica de OCR/visão local, decisão arquitetural (novo ADR) e decisão de isolamento de recursos frente ao processo de correção. Depende de AV-S01 (padrão de autorização) e de `DEC-AV-017`/`DEC-AV-009`. Predominantemente investigação/decisão, não implementação — resultado é um ADR e um relatório de benchmark, não código em produção.
- **AV-S06B** (Etapa 4B, parte 2, Marco 2): recebimento e armazenamento de imagens, controle de acesso, preservação do original, retenção. Depende de AV-S05B aprovada e de `DEC-AV-018`/`DEC-AV-019`/`DEC-AV-013`.
- **AV-S07B** (Etapa 4B, parte 3, Marco 2): implementação real da preparação de imagem e execução local de OCR/visão, com registro de motor/modelo/parâmetros e tratamento de instrução não confiável. Depende de AV-S06B e da decisão arquitetural de AV-S05B já estar implementável (motor/modelo escolhido).
- **AV-S08B** (Etapa 4B, parte 4, Marco 2): tela de conferência lado a lado, edição/confirmação, sinalização de incerteza não calibrada, transcrição manual de contingência. Depende de AV-S07B.
- **AV-S09B** (Etapa 4B, parte 5, Marco 2): associação da resposta confirmada, bloqueio de início automático de correção antes da confirmação, cadeia de rastreabilidade completa, idempotência em reenvio. Depende de AV-S08B e, quando aplicável, da estrutura acadêmica da etapa 2.
- **AV-S10B** (Etapa 4B, parte 6, Marco 2): conjunto de testes de imagem (nitidez, inclinação, manuscrito, rasura, ilegível) e teste ponta a ponta demonstrando correção de erro de OCR antes da avaliação pedagógica. Depende de AV-S09B.
- **AV-S07** (Etapa 5, parte 1, Marco 2): revisão do ADR-006 e decisão de arquitetura de lote (novo ADR). Depende de AV-S06 e de `DEC-AV-007`/`DEC-AV-009`. Esta sprint é predominantemente de decisão/documentação, não de implementação — resultado é um ADR aprovado, não código em produção. Se AV-S05B também estiver em andamento, a decisão de isolamento de recursos (`BL-AV-4B-17`) deve ser considerada em conjunto, para não desenhar duas arquiteturas de processo concorrentes sem avaliar a disputa por hardware entre elas.
- **AV-S08** (Etapa 5, parte 2, Marco 2): implementação de idempotência, concorrência, progresso, retentativa, recuperação e pausa/cancelamento (se confirmado necessário). Depende da decisão de AV-S07 estar aprovada, não apenas proposta.
- **AV-S09** (Etapa 6, Marco 2): fila de revisão com filtros, revisão em lote, histórico agregado, exportação de notas finais, mapeamento de dependências de segunda revisão/liberação ao aluno. Depende de AV-S08 para ter volume de correções e reprocessamentos reais para revisar.
- **AV-S10** (Etapa 7, parte 1, Marco 2→3): conjunto de referência humano, framework de avaliação, critérios de aceitação definidos antes da medição, separação de confiança heurística vs. calibrada. Sem dependência técnica das sprints de S05 a S09 — pode correr em paralelo, sujeito a `DEC-AV-012`.
- **AV-S11** (Etapa 7, parte 2, Marco 2→3): regressão de modelos/prompts, robustez adversarial, benchmark de hardware, avaliação de embeddings mediante hipótese. Depende de AV-S10 (framework definido) e de `DEC-AV-009` para o benchmark.
- **AV-S12** (Etapa 8, parte 1, Marco 3): dashboard do produto e acessibilidade dirigida dos fluxos centrais. Depende de AV-S09 (resultados e fluxos já existentes para instrumentar o dashboard).
- **AV-S13** (Etapa 8, parte 2, Marco 3): testes e2e, teste de carga, instalação reproduzível/backup/recuperação, roteiro de homologação e evidências de aceite. Depende de AV-S12, de `DEC-AV-006` (ambiente-alvo) e dos resultados de AV-S11 para poder homologar com qualidade da IA já caracterizada.

## 4. Premissas gerais desta proposta

- Cada sprint entrega um incremento verificável isoladamente; nenhuma sprint depende de "terminar tudo" para mostrar resultado parcial.
- Nenhuma sprint superior a uma etapa foi proposta; etapas maiores (4, 4B, 5, 7, 8) foram divididas em sprints menores (4B em seis partes, por ser a maior frente nova).
- A ordem entre AV-S10/S11 (qualidade da IA) e AV-S05–S09 (operação em lote) é uma escolha de paralelismo, não uma dependência rígida — Rafael pode priorizar de forma diferente sem invalidar o restante da tabela.
- A ordem entre a linha CSV (AV-S05/S06) e a linha imagem (AV-S05B..S10B) foi decidida por Rafael em 2026-09-21 (`DEC-AV-016`): imagem priorizada sobre CSV — ver §11 do documento de trilha para o sequenciamento completo em 5 fases.
- Nenhuma sprint desta lista está aprovada para execução. Este documento é insumo para a próxima decisão de Rafael, não uma autorização.
