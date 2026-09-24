# Trilha "Operação de uma turma" — AvalIA

> Estado: **PROPOSTA**. Documento de planejamento; nenhuma sprint funcional está aprovada por este arquivo. Homologação, priorização e escolha do ambiente-alvo são de Rafael.
> Fonte canônica do backlog detalhado: [`backlog_tecnico_avalia.md`](backlog_tecnico_avalia.md). Este documento não repete o detalhamento item a item.
> **Atualização de escopo (2026-09-21, GOV-003):** inclusão da Etapa 4B — Entrada por imagem e transcrição assistida, a pedido explícito de Rafael. Ver §1.1 do backlog canônico para o confronto com o PRD e §10 deste documento para o registro de mudança de escopo. Nenhuma seção anterior a esta atualização foi apagada; apenas complementada.
> **Reconciliação (2026-09-23, GOV-004):** Rafael aprovou `DEC-AV-016` (imagem priorizada sobre CSV), `DEC-AV-018` (primeira versão: uma resposta por foto) e `DEC-AV-021` (seleção manual pelo professor) em 2026-09-21; esta atualização propaga essas decisões à sequência da trilha. Ver §11 para a leitura em 5 fases de execução (substitui a leitura de "Etapa 4 vs. Etapa 4B em paralelo, ordem pendente" das seções 3 e 7, que ficou desatualizada após a decisão). As seções 1–10 permanecem como registro histórico do que foi proposto em GOV-002/GOV-003 e não foram apagadas; a leitura vigente de sequenciamento é a do §11.

## 1. Objetivo e limites

**Objetivo proposto:** evoluir a demonstração experimental do AvalIA para sustentar o fluxo completo de avaliação de uma turma — estrutura acadêmica mínima, avaliação com múltiplas questões, entrada de respostas em escala (digitação, CSV **e imagem/manuscrito com confirmação humana obrigatória**), processamento confiável em lote, revisão humana rastreável e um ciclo de homologação documentado.

**Isto não é:**

- autorização para produção;
- autorização para uso de dados reais de estudantes (`BKL-AV-001` permanece aberto);
- decisão sobre o ambiente-alvo do piloto (local, homologação compartilhada ou piloto supervisionado — `DEC-AV-006`);
- promoção do estado atual a baseline validado (`BASELINE-001` continua candidato até `BKL-AV-003` ser resolvido);
- autorização para reconhecimento manuscrito em produção sem revisão humana — o PRD exclui esse cenário explicitamente (ver §1.1 do backlog canônico), e esta trilha preserva esse limite: a entrada por imagem é sempre assistida, com confirmação humana obrigatória antes da correção.

O objetivo só se torna executável mediante planos de sprint aprovados individualmente, conforme [`sprint_management_policy.md`](../sprint_management_policy.md).

## 2. Marcos

| Marco | Etapas | Resultado observável |
|---|---|---|
| Marco 1 — Avaliação estruturada | 1, 2, 3 | Fluxo unitário consolidado e auditado; estrutura acadêmica mínima; avaliação com múltiplas questões versionadas |
| Marco 2 — Operação de uma turma | 4, 4B, 5, 6 | Importação em escala (CSV e imagem), processamento em lote confiável, revisão e resultados rastreáveis para uma turma completa |
| Marco 3 — Versão avaliada e homologada | 7 (preparação antecipada), 8 | Relatório reproduzível de qualidade da IA (textual e de OCR/visão); ciclo completo executado e homologado no ambiente decidido |

A preparação da etapa 7 (conjunto de referência, framework de avaliação, critérios de aceitação) começa durante o Marco 2, não é adiada para o Marco 3. A investigação de OCR/visão local (Etapa 4B, itens A) é, pela mesma lógica, antecipável dentro do Marco 2 — ver seção 6. Segurança, testes, acessibilidade, observabilidade proporcional e documentação são tratadas dentro de cada etapa correspondente (etapas 1, 2, 4, 4B, 5, 8), não concentradas ao final.

## 3. Sequência e dependências entre etapas

```text
Etapa 1 (consolidação) ──┬──> Etapa 2 (estrutura acadêmica) ──> Etapa 3 (avaliações completas)
                          │                                              │
                          └──────────────────────────────────────────────┤
                                                                          v
                                                            Etapa 4 (respostas em escala — CSV)
                                                                          │
                          Etapa 4B (entrada por imagem) ── ordem relativa a Etapa 4 pendente (DEC-AV-016);
                          pode ser desenhada em paralelo a partir da conclusão da Etapa 3               │
                                                                          │
                                                                          v
                                                            Etapa 5 (processamento em lote)
                                                                          │
                                                                          v
                                                            Etapa 6 (revisão e resultados)
                                                                          │
Etapa 7 (qualidade da IA) ── inicia em paralelo à Etapa 5/6, antes do Marco 3
                                                                          │
                                                                          v
                                                            Etapa 8 (integração e homologação)
```

Justificativa das dependências:

- Etapa 2 depende de a etapa 1 ter corrigido o padrão de autorização por vínculo, para que a estrutura acadêmica nova siga o mesmo padrão corrigido, não o padrão com lacuna.
- Etapa 3 depende de estrutura acadêmica para vincular avaliação↔turma de forma coerente, embora o suporte a múltiplas questões possa ser desenhado em paralelo.
- Etapa 4 depende da etapa 2 para o vínculo aluno↔avaliação↔resposta.
- **Etapa 4B** depende da etapa 1 (padrão de autorização, reaplicado ao novo recurso "imagem") e, para o item de associação (`BL-AV-4B-14`), da mesma estrutura acadêmica da etapa 2. Não depende da etapa 4 (CSV) tecnicamente — são canais de entrada paralelos e independentes, compartilhando apenas o destino final (fila de correção). A investigação técnica (item A, `BL-AV-4B-01`/`02`) não depende de nenhuma das duas e pode ser antecipada (ver seção 6).
- Etapa 5 depende de decisão de arquitetura de lote (`BL-AV-5-02`), que por sua vez depende de decisões de volume/hardware (`DEC-AV-007`, `DEC-AV-009`). O mesmo hardware é compartilhado com a Etapa 4B — ver `BL-AV-4B-17` e a nota de disputa de recursos na seção 5.
- Etapa 6 depende de etapa 5 (e, quando aplicável, de 4B) para produzir volume de correções e reprocessamentos.
- Etapa 7 é iniciada em paralelo (conjunto de referência e framework não dependem de código de lote), mas o benchmark de latência (`BL-AV-7-05`) depende do hardware-alvo decidido; o benchmark de OCR/visão (`BL-AV-4B-01`) é análogo, mas é tratado como investigação própria da Etapa 4B, não fundido ao framework de qualidade da IA de correção — são avaliações de componentes distintos.
- Etapa 8 depende de todas as etapas anteriores aplicáveis ao ambiente decidido, incluindo 4B se estiver no escopo do piloto decidido.

## 4. Entregas por etapa (resumo executável)

| Etapa | Entrega mínima verificável |
|---|---|
| 1 | Autorização por vínculo corrigida e testada; retomada de fluxo via API; CI mínima; suíte revalidada com data atual |
| 2 | Criar turma fictícia, cadastrar alunos e vincular avaliação, respeitando limites de acesso |
| 3 | Publicar avaliação com várias questões preservando versões usadas em cada correção |
| 4 | Importar respostas de uma turma com rastreabilidade e comportamento definido para reenvio, sem duplicação indevida |
| 4B | Professor envia imagem de resposta (impressa ou manuscrita), confere e confirma a transcrição lado a lado com a imagem, e só então o texto confirmado segue para a correção assistida; erro de OCR é corrigível antes de qualquer avaliação pedagógica |
| 5 | Processar lote e recuperar trabalho após reinício sem perder resultado nem duplicar correção |
| 6 | Localizar pendências, registrar decisões humanas auditáveis, exportar resultados finais separados da sugestão da IA |
| 7 | Relatório reproduzível de desempenho e limitações da IA, com critérios atendidos/não atendidos explícitos |
| 8 | Executar o ciclo completo de uma turma no ambiente acordado, com evidências formais de aceite |

## 5. Critérios de entrada e saída por marco

### Marco 1

- **Entrada:** GOV-001 homologada; decisão sobre promoção/rejeição de `BASELINE-001`; prioridade confirmada por Rafael para iniciar esta trilha.
- **Saída:** achados de autorização da etapa 1 resolvidos e testados; estrutura acadêmica mínima funcional; avaliação com múltiplas questões publicável com rubrica correspondente; suíte revalidada com resultado atual registrado.

### Marco 2

- **Entrada:** Marco 1 com closure gate aplicado (concluído ou concluído com débitos aceitos); decisões de volume-alvo, hardware e política de reenvio resolvidas o suficiente para dimensionar a etapa 5; para a Etapa 4B especificamente, `DEC-AV-017` (critérios de aceite de OCR) resolvida antes do benchmark (`BL-AV-4B-01`).
- **Saída:** lote de respostas de uma turma importado (via CSV e, se decidido, via imagem), processado e revisado com resultados exportáveis; débitos residuais registrados com ID.
- **Nota de recursos compartilhados:** se a Etapa 4B e a Etapa 5 forem executadas no mesmo hardware local, a decisão de arquitetura de lote (`BL-AV-5-02`) e a decisão de isolamento OCR/correção (`BL-AV-4B-17`) devem ser tratadas em conjunto antes de qualquer implementação de execução simultânea — não presumir que o hardware atual (validado para um único modelo de correção por vez, ADR-005) suporta os dois processos concorrentes sem medição.

### Marco 3

- **Entrada:** Marco 2 com closure gate aplicado; framework e critérios de qualidade da IA definidos (etapa 7 iniciada); ambiente-alvo de homologação decidido (`DEC-AV-006`).
- **Saída:** relatório de qualidade da IA reproduzível (incluindo, se a Etapa 4B estiver no escopo do piloto, o relatório de qualidade de OCR/visão separado); ciclo completo de uma turma executado e homologado no ambiente decidido, com evidências de aceite registradas.

## 6. Atividades antecipáveis

Podem começar antes da aprovação formal da sprint correspondente, por não implicarem código em produção nem decisão irreversível:

- `BL-AV-1-01` (auditoria de autorização) e `BL-AV-1-07` (revalidação da suíte) — são investigação/leitura, não mudança de comportamento.
- `BL-AV-7-01`/`BL-AV-7-06` (conjunto de referência e critérios de aceitação da IA) — podem ser desenhados durante o Marco 1, desde que não dependam de dados reais.
- `BL-AV-5-01` (revisão do ADR-006) — é análise documental, não implementação.
- `BL-AV-4B-01` (levantamento técnico inicial de OCR/visão local — **escopo redefinido em GOV-004**: compara alternativas, licenças, hardware e limitações, e produz uma proposta de métricas/amostras/limites para `BL-AV-4B-20`) — não depende de nenhuma decisão prévia; pode ser planejado em paralelo à Etapa 1 (ver §11, Fase 2).

Não antecipar: qualquer item que exija migração de schema, dependência nova instalada, ou dado real de estudante, mesmo que classificado como "poderia começar mais cedo". Isso inclui `BL-AV-4B-20` (benchmark comparativo, depende de `DEC-AV-017` aprovada), `BL-AV-4B-02` (decisão arquitetural, depende do benchmark) e qualquer implementação de recebimento/armazenamento de imagem (`BL-AV-4B-03` em diante) — apenas o levantamento inicial (`BL-AV-4B-01`) é antecipável.

## 7. Decisões necessárias (associadas aos itens que bloqueiam)

Ver detalhamento completo em [`registers/decisions.md`](../registers/decisions.md). Resumo com escopo de bloqueio:

| ID | Decisão | Bloqueia diretamente | Não bloqueia |
|---|---|---|---|
| `DEC-AV-006` | Ambiente-alvo (local / homologação compartilhada / piloto supervisionado) | `BL-AV-1-05`, `BL-AV-8-05`, `BL-AV-8-06` | Etapas 1–7 podem avançar tecnicamente em ambiente local de desenvolvimento |
| `DEC-AV-007` | Quantidade de professores, turmas, alunos e respostas-alvo | `BL-AV-2-01` (dimensionamento), `BL-AV-5-01`, `BL-AV-5-02`, `BL-AV-8-04` | Desenho inicial de modelo de dados pode iniciar com suposições conservadoras documentadas |
| `DEC-AV-009` | Hardware disponível e limites de processamento | `BL-AV-5-01`, `BL-AV-5-02`, `BL-AV-7-05`, `BL-AV-4B-02`, `BL-AV-4B-17` | Framework de avaliação da IA (`BL-AV-7-01`/`02`) e investigação inicial de OCR (`BL-AV-4B-01`) não dependem disso |
| `DEC-AV-008` | Política de reenvio/duplicidade na importação | `BL-AV-4-04` | Contrato de importação (`BL-AV-4-01`) pode ser desenhado sem essa decisão, deixando o campo explícito como pendente |
| `DEC-AV-010` | Política de segunda revisão | `BL-AV-6-05` e qualquer extensão de `BL-AV-6-01` que dependa de segunda revisão | Fila de revisão de primeira instância (`BL-AV-6-01`) não depende disso |
| `DEC-AV-012` | Critérios de qualidade da IA e responsáveis pelas referências humanas | `BL-AV-7-01`, `BL-AV-7-02`, `BL-AV-7-06` | Nada nas etapas 1–6 depende disso |
| `DEC-AV-013` | Retenção e exclusão de dados | Uso de dados reais em qualquer etapa; homologação final (`BL-AV-8-06`); `BL-AV-4B-05` (retenção específica de imagens) | Etapas com dados fictícios não são bloqueadas |
| `DEC-AV-014` | Condições para uso de dados reais | Qualquer piloto com dados reais; permanece subordinado a `BKL-AV-001` | Todo o trabalho com dados fictícios prossegue independente |
| `DEC-AV-011` | Escopo de liberação de resultados ao aluno | `BL-AV-6-05` (parte de liberação) | Exportação para o professor (`BL-AV-6-04`) não depende disso |
| `DEC-AV-015` | Prazo e prioridades dos próximos entregáveis | Sequenciamento/velocidade das sprints propostas | Não bloqueia o detalhamento técnico já registrado no backlog |
| `DEC-AV-016` | Ordem relativa entre Etapa 4 (CSV) e Etapa 4B (imagem) | Sequenciamento de AV-S05..S06 vs. AV-S05B..S10B | **Aprovada em 2026-09-21: imagem priorizada sobre CSV.** Ver §11 para o resequenciamento aplicado. |
| `DEC-AV-017` | Métricas e critérios de aceite do benchmark de OCR, definidos antes de medir | `BL-AV-4B-01`, `BL-AV-4B-02`, `BL-AV-4B-18` | Não bloqueia o levantamento inicial de opções de motor/modelo |
| `DEC-AV-018` | Primeira versão: uma resposta por imagem ou prova inteira | `BL-AV-4B-03` | **Aprovada em 2026-09-21: uma resposta de uma questão por foto** — investigação de OCR (`BL-AV-4B-01`) não dependia disso |
| `DEC-AV-019` | Suporte a múltiplas páginas na primeira entrega | `BL-AV-4B-03` | Não bloqueia `BL-AV-4B-01`/`02`; nota: `DEC-AV-018` já implica ausência de suporte a múltiplas páginas na prática, mas esta linha permanece formalmente pendente |
| `DEC-AV-020` | Necessidade de fórmulas, tabelas, desenhos ou código manuscrito | Ampliação de escopo de `BL-AV-4B-01`/`07` além de texto corrido | Primeira versão pode assumir apenas texto corrido enquanto pendente |
| `DEC-AV-021` | Identificação manual ou automática de aluno/questão na imagem | `BL-AV-4B-14` | **Aprovada em 2026-09-21: professor seleciona manualmente avaliação, questão e aluno** — identificação automática fica fora de escopo desta trilha |

Nenhuma decisão marcada `pendente` acima foi tomada nesta execução. As três marcadas `aprovada` refletem exclusivamente a manifestação explícita de Rafael em 2026-09-21, propagada ao sequenciamento em §11 nesta execução (GOV-004, 2026-09-23).

## 8. Itens fora desta trilha

Ver seção 5 do backlog técnico canônico para a lista completa preservada do backlog anterior (API pública/webhooks, auditoria de pesquisa anonimizada, teste de usabilidade formal, auditoria WCAG completa, protocolo de validação científica, scanner de segredos, observabilidade avançada, runbooks completos).

Permanecem fora também, especificamente para entrada por imagem, até decisão explícita: reconhecimento manuscrito em produção sem confirmação humana (excluído pelo próprio PRD, §5.1); correção completa de redações extensas a partir de imagem; qualquer inferência de nota diretamente da imagem sem transcrição confirmada; suporte a fórmulas/tabelas/desenhos/código manuscrito enquanto `DEC-AV-020` estiver pendente.

## 9. Metodologia desta análise

Achados de código citados no backlog (autorização por vínculo, retomada via `sessionStorage`, ausência de CI, `infra/compose` e `scripts/` vazios) vêm de leitura estática de arquivos nesta sessão (`core/app/main.py`, `core/app/deps.py`, `frontend/src/services/workflow.ts`, `frontend/src/pages/ReviewPage.tsx`, `find .github -type f`, `ls -la infra/compose scripts`), não de execução em runtime. Cada item correspondente está classificado como `investigacao` até reprodução real confirmar o comportamento, conforme instruído pela tarefa.

## 10. Registro de mudança de escopo (2026-09-21, GOV-003)

- **Origem:** solicitação explícita de Rafael para incorporar entrada de respostas por imagem, incluindo manuscritas, com OCR/visão local.
- **Confronto com o PRD:** documentado em §1.1 do backlog técnico canônico. Conclusão: não é uma contradição do PRD — é a antecipação controlada de um item já previsto no roadmap como P2/experimental ("OCR/HTR experimental"), respeitando o limite que o PRD já impunha (reconhecimento manuscrito em produção permanece fora de escopo; esta trilha trata apenas de um fluxo assistido com confirmação humana obrigatória).
- **O que foi adicionado:** Etapa 4B com 19 itens de backlog (`BL-AV-4B-01` a `19`), 6 novas decisões pendentes (`DEC-AV-016` a `021`), atualização dos marcos, da sequência de dependências, das entregas por etapa e dos critérios de entrada/saída do Marco 2.
- **O que não foi alterado:** nenhum item das Etapas 1, 2, 3, 4, 5, 6, 7 ou 8 já registrado em GOV-002 foi removido, renumerado ou teve seu conteúdo reescrito. A Etapa 4 (CSV) permanece como estava; a ordem relativa entre ela e a Etapa 4B é uma decisão nova (`DEC-AV-016`), não uma substituição.
- **O que continua não autorizado:** nenhuma sprint da Etapa 4B foi aprovada; nenhuma implementação, instalação de dependência (incluindo bibliotecas de OCR/visão) ou execução de benchmark foi realizada nesta atualização de planejamento.

## 11. Sequenciamento em 5 fases (2026-09-23, GOV-004)

> Propaga as decisões aprovadas em 2026-09-21 (`DEC-AV-016`, `DEC-AV-018`, `DEC-AV-021`) ao sequenciamento da trilha. Substitui, como leitura vigente de ordem de execução, o diagrama do §3 e a tabela do §7 quanto à ordem CSV/imagem — aqueles permanecem no documento como registro histórico do estado antes da decisão, não como sequenciamento atual. Nenhum ID de sprint é renumerado; apenas reagrupado por fase. Nenhuma sprint é aprovada por este registro — aprovação de execução continua sendo decisão específica de Rafael por sprint, conforme [`sprint_management_policy.md`](../sprint_management_policy.md).

### Fase 1 — Consolidação do fluxo atual

Permissões, retomada do trabalho, revisão manual, persistência e testes. Sprints: `AV-S01`, `AV-S02`. Sem dependência de decisão pendente; primeira frente elegível para abertura de sprint.

### Fase 2 — Investigação de viabilidade do OCR local

Levantamento de alternativas, licenças, requisitos de hardware e limitações (`BL-AV-4B-01`, escopo redefinido em GOV-004 — ver backlog canônico). Frente independente da Fase 1; pode ser planejada em paralelo. Produz a proposta de métricas/amostras/limites de aceite que, aprovada por Rafael (`DEC-AV-017`), habilita o benchmark comparativo (`BL-AV-4B-20`) e, com o benchmark medido, a decisão arquitetural (`BL-AV-4B-02`). Sprint: `AV-S05B` (itens `BL-AV-4B-01`, `20`, `02`).

### Fase 3 — Estrutura acadêmica e avaliações

Vínculos e capacidades necessários à entrada por imagem: modelo de dados acadêmico, permissões por vínculo, múltiplas questões por avaliação. Depende da Fase 1 (padrão de autorização corrigido, reaplicado à estrutura nova). Sprints: `AV-S03` (Etapa 2), `AV-S04` (Etapa 3).

### Fase 4 — Primeira entrega completa por imagem

Upload → extração → conferência → confirmação → correção → revisão → consulta do resultado persistido. Depende da Fase 2 (decisão arquitetural de OCR implementável) e da Fase 3 (vínculo aluno/avaliação/questão). Inclui, sem adiamento, os requisitos de confiabilidade indispensáveis à primeira entrega: processamento assíncrono confiável da extração de uma imagem, persistente e recuperável (`BL-AV-4B-21`) — distinto de processamento em lote, que só entra na Fase 5. Sprints: `AV-S06B` (recebimento/armazenamento), `AV-S07B` (preparação/extração local, inclui `BL-AV-4B-21`), `AV-S08B` (conferência/confirmação), `AV-S09B` (associação/rastreabilidade/idempotência), `AV-S10B` (testes ponta a ponta).

### Fase 5 — Ampliação operacional

Processamento persistente em lote, importação CSV e demais capacidades para operação de uma turma completa (múltiplos alunos/avaliações em volume). A Etapa 4 (CSV) passa a compor esta fase — não foi removida, apenas reordenada após a primeira entrega por imagem, conforme `DEC-AV-016`. Sprints: `AV-S05`, `AV-S06` (CSV), `AV-S07`, `AV-S08` (lote), `AV-S09` (revisão/resultados). A decisão de isolamento de recursos entre OCR/visão e correção (`BL-AV-4B-17`) deve ser resolvida antes de a Fase 4 (extração local real) e esta fase (processamento em lote) rodarem simultaneamente no mesmo hardware — ver nota de recursos compartilhados no §5.

A Etapa 7 (qualidade da IA) e a Etapa 8 (integração e homologação) não são fases numeradas nesta leitura porque atravessam as fases acima por desenho (Etapa 7 inicia em paralelo desde a Fase 1; Etapa 8 depende de todas as fases aplicáveis ao ambiente decidido) — ver §2 e §3 para a leitura completa de marcos e dependências, que continuam válidas para essas duas etapas.

**Investigação vs. benchmark, explicitamente separados (regra de Rafael):** o levantamento técnico inicial (`BL-AV-4B-01`, Fase 2) produz uma proposta de métricas, amostras e critérios de aceite. Rafael aprova esses critérios (`DEC-AV-017`) antes de qualquer medição usada para escolher a solução. Só então o benchmark comparativo (`BL-AV-4B-20`) é executado. Os critérios aprovados não podem ser ajustados retroativamente para favorecer um resultado.
