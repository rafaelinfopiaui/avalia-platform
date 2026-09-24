# Backlog técnico canônico — Trilha "Operação de uma turma"

> Fonte canônica desta trilha. Sprint, snapshot e dashboard referenciam os IDs abaixo; não duplicam o conteúdo completo.
> Estado desta trilha: **PARCIALMENTE EXECUTADA**. `AV-S01` foi homologada em 2026-09-23 (6 itens); os demais itens permanecem propostos, salvo decisão explícita em seu próprio registro. Homologação e priorização continuam cabendo a Rafael (ver [`registers/decisions.md`](../registers/decisions.md)).
> Convenção de ID: `BL-AV-<etapa>-<seq>`. A convenção foi adotada em `AV-S01`; novos IDs mantêm a sequência e exigem rastreabilidade no plano de sprint.

## 0. Como ler este backlog

- **Tipo**: `requisito_existente` (já previsto em fonte aprovada), `debito_correcao` (falha/lacuna real já identificada), `proposta_nova` (capacidade ainda não decidida), `investigacao` (não sabemos o suficiente para prometer solução), `decisao` (escolha técnica a registrar, não implementação em si).
- **Status factual**: `proposto` (nenhum item nasce `ready` ou `aprovado` neste documento).
- Nenhuma prioridade abaixo é aprovação; é recomendação técnica para a decisão de Rafael.
- Itens com evidência de código desta sessão citam o arquivo/linha inspecionado; nenhuma reprodução em runtime foi executada nesta tarefa (apenas leitura estática — ver metodologia no documento da trilha).

## 1. Reconciliação com o backlog anterior

O backlog pré-governança (`docs/backlog.md`, grupos G1–G4) não foi apagado. Mapeamento:

| Item do backlog anterior | Tratamento nesta trilha |
|---|---|
| G1 — estrutura acadêmica completa (RF-02) | Etapa 2 (`BL-AV-2-*`) |
| G1 — importação CSV (RF-06/RF-08) | Etapa 4 (`BL-AV-4-*`) |
| G1 — processamento em lote / migração de fila (EP-11, ADR-006) | Etapa 5 (`BL-AV-5-*`) |
| G1 — segunda revisão, liberação ao aluno, exportação (RF-11) | Etapa 6 (`BL-AV-6-*`) |
| G1 — API pública/webhooks (RF-14) | **Mantido fora desta trilha** — sem item nesta rodada |
| G1 — auditoria de pesquisa anonimizada (RF-15) | **Mantido fora desta trilha** — depende de decisão de dados reais (`BKL-AV-001`) |
| G2 — dashboards pedagógicos/operacionais (RF-12) | Etapa 8 (`BL-AV-8-01`) |
| G2 — wizard de importação CSV | Etapa 4 (`BL-AV-4-02`) |
| G2 — fila de revisão com filtros | Etapa 6 (`BL-AV-6-01`) |
| G2 — teste de usabilidade formal (meta ≥90%) | **Mantido fora desta trilha** — não há critério nem responsável definidos |
| G2 — auditoria WCAG completa | **Mantido fora desta trilha** — etapa 8 cobre apenas acessibilidade dos fluxos centrais, não auditoria formal |
| G3 — embeddings (nível 2) | Etapa 7 (`BL-AV-7-07`), mediante hipótese/benefício mensurável |
| G3 — calibração de confiança com piloto real (D-07) | Etapa 7 (`BL-AV-7-08`), sujeito a `BKL-AV-001` para qualquer dado real |
| G3 — suíte dourada de regressão | Etapa 7 (`BL-AV-7-03`) |
| G3 — benchmark formal | Etapa 7 (`BL-AV-7-05`) |
| G3 — robustez a prompt injection | Etapa 7 (`BL-AV-7-04`) |
| G3 — protocolo de validação científica (seção 27 PRD) | **Mantido fora desta trilha** — escopo maior que operação de uma turma |
| G4 — CI/CD completo | Etapa 1 (`BL-AV-1-06`) e etapa 8 |
| G4 — homologação real | Etapa 8 (`BL-AV-8-06`) |
| G4 — scanner de segredos/dependências | **Mantido fora desta trilha** |
| G4 — observabilidade avançada | **Mantido fora desta trilha** |
| G4 — testes de carga | Etapa 8 (`BL-AV-8-04`) |
| G4 — runbooks operacionais completos | Parcial na etapa 8 (`BL-AV-8-06`); runbook completo **mantido fora desta trilha** |
| Transversal — pendência CNE | Permanece `BKL-AV-001`, não resolvida por esta trilha |
| Transversal — D-01 a D-12 | Permanecem em [`docs/decisoes-pendencias.md`](../../decisoes-pendencias.md); D-07, D-08, D-10, D-11, D-12 são referenciados nas decisões desta trilha |

Nenhuma sprint histórica foi inventada para justificar este mapeamento.

## 1.1 Confronto com o PRD — entrada por imagem (atualização de escopo, 2026-09-21)

Rafael solicitou a inclusão explícita de entrada de respostas por imagem (incluindo manuscritas) com OCR/visão local. Confronto com o PRD (`/Users/rafaeloliveira/Downloads/PRD_AvalIA_v1.0_Completo.docx`, controle de versão "1.0", 01/09/2026):

| Trecho do PRD | Linha (extração) | Leitura |
|---|---|---|
| RF-06 — Entrada de respostas: "Fluxo esperado: Digitação/CSV/API → validação → deduplicação → persistência → fila." | 462–464 | Entrada por imagem **não estava prevista** no fluxo de RF-06 tal como escrito. |
| P0 — MVP obrigatório: inclui "respostas digitais/CSV"; não incluído: "OCR manuscrito, redações longas, cobrança, aplicativo nativo." | 258–260 | OCR manuscrito é **explicitamente excluído do MVP obrigatório (P0)**. |
| P2 — Evolução: inclui "OCR/HTR experimental" | 264–265 | OCR/HTR **já estava previsto no roadmap do PRD**, como item de evolução (P2), não como P0/P1. |
| 5.1 Fora do escopo do primeiro ciclo: "Reconhecimento manuscrito em produção" | 271–272 | O PRD exclui apenas o reconhecimento manuscrito **em produção**; não exclui investigação, experimentação ou um fluxo assistido com confirmação humana obrigatória. |

**Conclusão registrada (não é diagnóstico de código, é reconciliação documental):** o requisito de Rafael não contradiz o PRD. Ele antecipa um item que já constava do roadmap como P2/experimental (`OCR/HTR experimental`) para dentro desta trilha, mantendo o limite que o próprio PRD já impunha — "reconhecimento manuscrito em produção" continua fora de escopo, mas um fluxo **assistido**, com confirmação humana obrigatória antes da correção (ver seção 6 abaixo), é compatível com a leitura "experimental" do PRD e com o princípio geral do produto (IA sugere, humano decide — RN-001).

Este documento não reescreve os itens de reconciliação da seção 1 acima; a linha correspondente a "OCR/HTR experimental (nível 2 backlog G3 anterior)" permanece como estava. Esta seção 1.1 é um adendo de reconciliação, datado, registrando a origem e o alcance da mudança de escopo.

## 1.2 Reconciliação com a proposta de trilha anterior (GOV-002)

A trilha documentada em GOV-002 (`trilha_operacao_de_turma.md`) não continha nenhuma etapa de entrada por imagem. Nenhum item de GOV-002 é removido ou renumerado por esta atualização. A nova frente é adicionada como **Etapa 4B — Entrada por imagem e transcrição assistida**. Em 2026-09-21, Rafael decidiu `DEC-AV-016`: a entrada por imagem é priorizada em relação à importação CSV. Em 2026-09-23 (GOV-004), essa decisão foi propagada ao resequenciamento completo da trilha em 5 fases — ver §11 de [`trilha_operacao_de_turma.md`](trilha_operacao_de_turma.md). A Etapa 4 (CSV) não foi removida nem descartada; passa a compor a fase "Ampliação operacional", após a primeira entrega completa por imagem.

## 2. Tabela-resumo

| ID | Título | Tipo | Etapa | Marco | Sprint candidata | Prioridade proposta | Status |
|---|---|---|---|---|---|---|---|
| BL-AV-1-01 | Auditoria de autorização por vínculo em rotas de resposta/correção/revisão | investigacao | 1 | 1 | AV-S01 | alta | homologado em AV-S01 (2026-09-23) |
| BL-AV-1-02 | Corrigir verificação de vínculo do professor nas rotas identificadas | debito_correcao | 1 | 1 | AV-S01 | alta | homologado em AV-S01 (2026-09-23) |
| BL-AV-1-03 | Retomada de fluxo via API, não apenas sessionStorage | debito_correcao | 1 | 1 | AV-S01 | alta | homologado em AV-S01 (2026-09-23) |
| BL-AV-1-04 | Suíte de regressão para autorização cruzada entre professores | proposta_nova | 1 | 1 | AV-S01 | alta | homologado em AV-S01 (2026-09-23) |
| BL-AV-1-05 | Validação visual documentada do fluxo central | debito_correcao | 1 | 1 | AV-S02 | média | homologado (2026-09-24, PR #1 integrado) |
| BL-AV-1-06 | CI mínima versionada (lint + testes) | debito_correcao | 1 | 1 | AV-S02 | média | homologado (2026-09-24, PR #1 integrado; execução remota real 3/3 jobs verdes) |
| BL-AV-1-07 | Revalidação datada da suíte existente e do build, com resultado registrado | investigacao | 1 | 1 | AV-S01 | alta | homologado em AV-S01 (2026-09-23), com IA simulada e sem alegação de inferência real |
| BL-AV-1-08 | Confirmar RN-017 (IA indisponível) após as correções de autorização | debito_correcao | 1 | 1 | AV-S01 | alta | homologado em AV-S01 (2026-09-23) |
| BL-AV-1-09 | Isolar testes do caminho de reparo de JSON do modo global do AI Engine (`DEBT-AV-009`) | debito_correcao | 1 | 1 | AV-S02 | média | homologado (2026-09-24, PR #1 integrado) |
| BL-AV-1-10 | Idempotência da revisão humana (`DEBT-AV-011`, achado real da validação visual de AV-S02) | debito_correcao | 1 | 1 | AV-S02 | alta | código homologado e integrado a `main` (2026-09-24, PR #1); migração operacional a `avalia_dev` continua PENDENTE — o código exige a `UniqueConstraint` real do banco, mas o ambiente operacional ainda não a recebeu; saneamento de duplicatas legadas é proposta separada, não autorizada |
| BL-AV-2-01 | Modelo de dados Organização/Curso/Disciplina/Turma/Aluno | proposta_nova | 2 | 1 | AV-S03 | alta | proposto |
| BL-AV-2-02 | Migração Alembic da estrutura acadêmica | proposta_nova | 2 | 1 | AV-S03 | alta | proposto |
| BL-AV-2-03 | Permissões por vínculo professor↔turma nos endpoints | proposta_nova | 2 | 1 | AV-S03 | alta | proposto |
| BL-AV-2-04 | Telas mínimas de cadastro de turma/aluno e vínculo à avaliação | proposta_nova | 2 | 1 | AV-S03 | média | proposto |
| BL-AV-2-05 | Critério de aceite do marco: turma fictícia + alunos + vínculo respeitando acesso | proposta_nova | 2 | 1 | AV-S03 | alta | proposto |
| BL-AV-3-01 | Suportar múltiplas questões por avaliação | proposta_nova | 3 | 1 | AV-S04 | alta | proposto |
| BL-AV-3-02 | Regras de edição/publicação/imutabilidade com múltiplas questões | proposta_nova | 3 | 1 | AV-S04 | alta | proposto |
| BL-AV-3-03 | Versionamento de questão preservado nas correções já feitas | requisito_existente | 3 | 1 | AV-S04 | alta | proposto |
| BL-AV-3-04 | Atualizar contrato OpenAPI/schema para múltiplas questões | debito_correcao | 3 | 1 | AV-S04 | média | proposto |
| BL-AV-4-01 | Contrato de importação CSV (schema/campos/erros por linha) | proposta_nova | 4 | 2 | AV-S05 | alta | proposto |
| BL-AV-4-02 | Prévia de importação com relatório de erros por linha | proposta_nova | 4 | 2 | AV-S05 | alta | proposto |
| BL-AV-4-03 | Vínculo aluno↔avaliação↔questão↔resposta via estrutura acadêmica | requisito_existente | 4 | 2 | AV-S06 | alta | proposto |
| BL-AV-4-04 | Regras de duplicidade, reenvio e confirmação | decisao | 4 | 2 | AV-S06 | alta | proposto |
| BL-AV-4-05 | Registro de importação e tratamento de falha parcial | proposta_nova | 4 | 2 | AV-S06 | média | proposto |
| BL-AV-4B-01 | Investigação técnica de OCR/visão local (texto impresso e manuscrito, pt-BR) | investigacao | 4B | 2 | AV-S05B | alta | proposto |
| BL-AV-4B-02 | Decisão arquitetural de motor/modelo de OCR local (novo ADR) | decisao | 4B | 2 | AV-S05B | alta | proposto |
| BL-AV-4B-03 | Recebimento e armazenamento de imagens (formato, tamanho, páginas, validação de conteúdo) | proposta_nova | 4B | 2 | AV-S06B | alta | proposto |
| BL-AV-4B-04 | Controle de acesso, preservação do original e metadados de vínculo/autoria/data | proposta_nova | 4B | 2 | AV-S06B | alta | proposto |
| BL-AV-4B-05 | Retenção, exclusão e proteção de logs contra dado sensível de imagem | decisao | 4B | 2 | AV-S06B | alta | proposto |
| BL-AV-4B-06 | Preparação de imagem (orientação/inclinação, detecção de captura inadequada) | proposta_nova | 4B | 2 | AV-S07B | média | proposto |
| BL-AV-4B-07 | Execução local de extração (OCR/visão), sem envio a API externa | proposta_nova | 4B | 2 | AV-S07B | alta | proposto |
| BL-AV-4B-08 | Registro de motor/modelo/versão/parâmetros/duração/resultado; diferenciação falha/ausência/ilegível | proposta_nova | 4B | 2 | AV-S07B | alta | proposto |
| BL-AV-4B-09 | Tratar instrução presente na imagem como conteúdo não confiável (extensão de RN-010/prompt injection) | debito_correcao | 4B | 2 | AV-S07B | alta | proposto |
| BL-AV-4B-10 | Tela de conferência lado a lado (imagem + transcrição) | proposta_nova | 4B | 2 | AV-S08B | alta | proposto |
| BL-AV-4B-11 | Edição/confirmação da transcrição pelo professor; preservar bruto, corrigido e histórico | proposta_nova | 4B | 2 | AV-S08B | alta | proposto |
| BL-AV-4B-12 | Sinalização de incerteza sem apresentá-la como probabilidade calibrada (alinhado a RN-016/ADR-008) | debito_correcao | 4B | 2 | AV-S08B | alta | proposto |
| BL-AV-4B-13 | Transcrição manual quando a extração falhar | proposta_nova | 4B | 2 | AV-S08B | média | proposto |
| BL-AV-4B-14 | Vínculo aluno/avaliação/questão da resposta confirmada; bloqueio de início automático da correção antes da confirmação | proposta_nova | 4B | 2 | AV-S09B | alta | proposto |
| BL-AV-4B-15 | Preservar cadeia imagem→OCR→transcrição confirmada→correção→revisão | requisito_existente_parcial | 4B | 2 | AV-S09B | alta | proposto |
| BL-AV-4B-16 | Idempotência/deduplicação em reenvio e retentativa de imagem | proposta_nova | 4B | 2 | AV-S09B | média | proposto |
| BL-AV-4B-17 | Isolamento de recursos entre processo de OCR/visão e processo de correção (memória/CPU/GPU) | decisao | 4B | 2 | AV-S07B | alta | proposto |
| BL-AV-4B-18 | Conjunto de testes de imagem (nitidez, inclinação, desfoque, iluminação, manuscrito, rasura, vazio/ilegível) | proposta_nova | 4B | 2 | AV-S10B | alta | proposto |
| BL-AV-4B-19 | Teste ponta a ponta demonstrando correção de erro de OCR antes da avaliação pedagógica | proposta_nova | 4B | 2 | AV-S10B | alta | proposto |
| BL-AV-4B-20 | Benchmark comparativo de OCR/visão com critérios previamente aprovados | investigacao | 4B | 2 | AV-S05B | alta | proposto |
| BL-AV-4B-21 | Processamento assíncrono confiável da extração de uma imagem, persistente e recuperável | proposta_nova | 4B | 2 | AV-S07B | alta | proposto |
| BL-AV-5-01 | Revisar ADR-006 à luz do volume-alvo real | investigacao | 5 | 2 | AV-S07 | alta | proposto |
| BL-AV-5-02 | Decisão de arquitetura de worker/persistência para lote (novo ADR) | decisao | 5 | 2 | AV-S07 | alta | proposto |
| BL-AV-5-03 | Idempotência e concorrência no processamento em lote | proposta_nova | 5 | 2 | AV-S08 | alta | proposto |
| BL-AV-5-04 | Progresso, retentativa e recuperação após reinício sem duplicar correção | proposta_nova | 5 | 2 | AV-S08 | alta | proposto |
| BL-AV-5-05 | Semântica de pausa/cancelamento | investigacao | 5 | 2 | AV-S08 | média | proposto |
| BL-AV-5-06 | Tratamento de indisponibilidade da IA em lote (extensão de RN-017) | requisito_existente | 5 | 2 | AV-S08 | alta | proposto |
| BL-AV-6-01 | Fila de revisão com filtros (confiança baixa, falha, divergência) | proposta_nova | 6 | 2 | AV-S09 | alta | proposto |
| BL-AV-6-02 | Revisão por critério em lote e tratamento manual em massa | proposta_nova | 6 | 2 | AV-S09 | média | proposto |
| BL-AV-6-03 | Histórico agregado de decisões e reprocessamentos | requisito_existente | 6 | 2 | AV-S09 | média | proposto |
| BL-AV-6-04 | Exportação de notas finais separada da sugestão da IA | proposta_nova | 6 | 2 | AV-S09 | alta | proposto |
| BL-AV-6-05 | Mapear dependências de segunda revisão e liberação ao aluno | investigacao | 6 | 2 | AV-S09 | média | proposto |
| BL-AV-7-01 | Conjunto de referência revisado por humanos | proposta_nova | 7 | 2→3 | AV-S10 | alta | proposto |
| BL-AV-7-02 | Framework de avaliação (pontuação, evidência, justificativa vs. referência) | proposta_nova | 7 | 2→3 | AV-S10 | alta | proposto |
| BL-AV-7-03 | Regressão de modelos/prompts sobre o framework | proposta_nova | 7 | 2→3 | AV-S11 | média | proposto |
| BL-AV-7-04 | Robustez a entradas adversariais (extensão do sinal já existente) | debito_correcao | 7 | 2→3 | AV-S11 | média | proposto |
| BL-AV-7-05 | Benchmark de latência/recursos no hardware-alvo | investigacao | 7 | 2→3 | AV-S11 | média | proposto |
| BL-AV-7-06 | Definir métricas e critérios de aceitação antes de medir | decisao | 7 | 2→3 | AV-S10 | alta | proposto |
| BL-AV-7-07 | Avaliar embeddings mediante hipótese e benefício mensurável | investigacao | 7 | 2→3 | AV-S11 | baixa | proposto |
| BL-AV-7-08 | Separar confiança heurística de confiança calibrada | debito_correcao | 7 | 2→3 | AV-S10 | alta | proposto |
| BL-AV-8-01 | Dashboard pedagógico/operacional do produto | proposta_nova | 8 | 3 | AV-S12 | média | proposto |
| BL-AV-8-02 | Acessibilidade dirigida dos fluxos centrais | debito_correcao | 8 | 3 | AV-S12 | média | proposto |
| BL-AV-8-03 | Testes ponta a ponta automatizados | proposta_nova | 8 | 3 | AV-S13 | alta | proposto |
| BL-AV-8-04 | Teste de carga proporcional ao cenário-alvo | investigacao | 8 | 3 | AV-S13 | média | proposto |
| BL-AV-8-05 | Instalação reproduzível, configuração, backup e recuperação | debito_correcao | 8 | 3 | AV-S13 | alta | proposto |
| BL-AV-8-06 | Roteiro de homologação e evidências de aceite | proposta_nova | 8 | 3 | AV-S13 | alta | proposto |

## 3. Detalhamento — Etapa 1 (Consolidação do fluxo existente)

### BL-AV-1-01 — Auditoria de autorização por vínculo em rotas de resposta/correção/revisão

- Objetivo/valor: confirmar por reprodução em runtime se um professor pode agir sobre dados de outro, fechando a lacuna encontrada por inspeção.
- Requisito/fonte: RF-01 (RBAC no servidor), RNF-01, item de escopo explícito da tarefa do usuário ("verificar autorização por vínculo").
- Tipo: investigação (parte diagnóstico já concluída por inspeção; falta reprodução).
- Achado por inspeção de código nesta sessão (não reproduzido em runtime): `create_answer`, `request_correction`, `get_correction_job` e `review_correction` em `core/app/main.py` não chamam `_get_owned_assessment` nem qualquer verificação equivalente — apenas `create_assessment`, `get_assessment` e `publish_assessment` verificam `assessment.owner_id != user.id`. Isso contrasta com o texto do roteiro do supervisor, que descreve a checagem de permissão como algo garantido "em cada endpoint sensível".
- Prioridade proposta: alta — risco de acesso indevido entre professores, mencionado explicitamente pelo usuário como observação preliminar.
- Dependências: nenhuma para iniciar a investigação; bloqueia `BL-AV-1-02`.
- Critérios de aceite: existe evidência de runtime (dois usuários professor distintos, tentativa cruzada) confirmando ou refutando cada rota citada; resultado registrado com comando e saída real.
- Validações/evidências esperadas: teste automatizado ou chamada HTTP real com dois tokens de professores diferentes contra cada rota listada.
- Riscos: se confirmado, é uma falha de isolamento de dados entre professores — deve ser tratada como prioridade alta, não como debito cosmético.
- Decisões pendentes: nenhuma decisão de produto; é verificação técnica.
- Etapa/Marco/Sprint: 1 / Marco 1 / AV-S01.
- Status: proposto.

### BL-AV-1-02 — Corrigir verificação de vínculo do professor nas rotas identificadas

- Objetivo/valor: garantir que nenhuma rota de resposta/correção/revisão opere sobre recurso de avaliação que não pertença ao professor autenticado (papel `admin` mantém acesso amplo, conforme já ocorre nas rotas corrigidas).
- Requisito/fonte: RF-01, RNF-01; decorre de `BL-AV-1-01`.
- Tipo: débito/correção.
- Prioridade proposta: alta.
- Dependências: `BL-AV-1-01` confirmando o achado.
- Critérios de aceite: as quatro rotas citadas retornam 403/404 apropriado quando o professor autenticado não é o dono da avaliação; papel `admin` continua funcional; testes de regressão cobrem os quatro casos.
- Validações/evidências esperadas: suíte automatizada (nova) + execução manual documentada.
- Riscos: correção mal calibrada pode quebrar o fluxo legítimo do próprio professor; exige teste de caminho feliz junto com o caminho negativo.
- Decisões pendentes: nenhuma.
- Etapa/Marco/Sprint: 1 / Marco 1 / AV-S01.
- Status: proposto.

### BL-AV-1-03 — Retomada de fluxo via API, não apenas sessionStorage

- Objetivo/valor: permitir que o professor retome correção/revisão ao reabrir o navegador, mudar de aba ou abrir a URL diretamente, sem depender de estado voláteis do navegador.
- Requisito/fonte: escopo explícito da tarefa do usuário ("verificar retomada do trabalho após sair da sessão ou abrir uma URL diretamente").
- Tipo: débito/correção.
- Achado por inspeção de código nesta sessão: `frontend/src/services/workflow.ts` guarda `assessment`/`answer`/`job` em `sessionStorage`; `ReviewPage.tsx` lê exclusivamente `readWorkflow()` (linha 10) e, se vazio, mostra aviso de dados indisponíveis (linha 18) em vez de buscar os dados pelo `id` da URL via API. `CorrectionPage.tsx` já busca o job pela API a cada poll, mas depende do `id` da rota, que só é preenchido corretamente se a navegação ocorreu dentro do mesmo fluxo.
- Prioridade proposta: alta — impacta diretamente o resultado esperado do marco ("um professor completa e retoma o fluxo").
- Dependências: nenhuma técnica; compartilha contexto com `BL-AV-1-01`/`02` por tocar as mesmas telas.
- Critérios de aceite: abrir a URL de revisão diretamente (nova aba, sem navegação prévia) carrega os dados via API quando o usuário está autenticado e autorizado; sessão de navegador fechada e reaberta não perde acesso ao trabalho em andamento.
- Validações/evidências esperadas: teste de frontend/e2e reproduzindo abertura direta da URL; inspeção de código confirmando a chamada à API.
- Riscos: pode expor a necessidade de endpoints adicionais (buscar resposta/avaliação por `job_id`) hoje inexistentes — mapear no design antes de implementar.
- Decisões pendentes: nenhuma.
- Etapa/Marco/Sprint: 1 / Marco 1 / AV-S01.
- Status: proposto.

### BL-AV-1-04 — Suíte de regressão para autorização cruzada entre professores

- Objetivo/valor: impedir reincidência da falha investigada em `BL-AV-1-01`/`02`.
- Requisito/fonte: decorrente dos itens anteriores.
- Tipo: proposta nova (de teste).
- Prioridade proposta: alta.
- Dependências: `BL-AV-1-02`.
- Critérios de aceite: suíte cobre todas as rotas de resposta/correção/revisão com dois professores distintos; roda em CI (ver `BL-AV-1-06`).
- Validações/evidências esperadas: `pytest` com resultado real anexado ao snapshot de fechamento da sprint.
- Riscos: nenhum relevante além de manutenção contínua da suíte.
- Decisões pendentes: nenhuma.
- Etapa/Marco/Sprint: 1 / Marco 1 / AV-S01.
- Status: proposto.

### BL-AV-1-05 — Validação visual documentada do fluxo central

- Objetivo/valor: ter evidência visual atual (não histórica) de que o fluxo login→avaliação→resposta→correção→revisão funciona na interface.
- Requisito/fonte: `DEBT-AV-004`; três documentos históricos (relatório de entrega, relatório consolidado, roteiro do supervisor) relatam repetidamente a ausência dessa validação.
- Tipo: débito/correção.
- Prioridade proposta: média — não é uma falha de dado, mas uma lacuna de evidência recorrente há três sessões.
- Dependências: ambiente local funcional (Postgres, Ollama, Core, AI Engine, Frontend).
- Critérios de aceite: passo a passo do roteiro de demonstração executado com captura/registro real, datado.
- Validações/evidências esperadas: evidência visual (captura de tela ou gravação) referenciada no snapshot de fechamento.
- Riscos: ambiente local pode ter drift desde 11/09/2026; validar setup antes de assumir que "só falta abrir o navegador".
- Decisões pendentes: ambiente-alvo desta validação (local do executor vs. ambiente compartilhado) — ver `DEC-AV-006`.
- Etapa/Marco/Sprint: 1 / Marco 1 / AV-S02.
- Status: proposto.

### BL-AV-1-06 — CI mínima versionada (lint + testes)

- Objetivo/valor: parar de depender de execução manual para saber se a suíte está passando; fechar `DEBT-AV-005`.
- Requisito/fonte: backlog G4 anterior ("CI/CD completo... sem deploy"); `.github/workflows/` confirmado vazio nesta sessão (`find .github -type f` sem resultados).
- Tipo: débito/correção.
- Prioridade proposta: média.
- Dependências: nenhuma; pode iniciar em paralelo a `BL-AV-1-01`–`04`.
- Critérios de aceite: workflow versionado executa lint e testes do Core, AI Engine (modo simulado) e build do frontend a cada push/PR, com resultado real observado ao menos uma vez.
- Validações/evidências esperadas: execução real do workflow (não apenas arquivo criado) com link/registro do resultado.
- Riscos: AI Engine real depende de Ollama — decidir se CI roda apenas em modo simulado (mais provável) e registrar a limitação.
- Decisões pendentes: nenhuma bloqueante para iniciar; escopo exato (quais jobs) é detalhe de implementação.
- Etapa/Marco/Sprint: 1 / Marco 1 / AV-S02.
- Status: proposto.

### BL-AV-1-07 — Revalidação datada da suíte existente e do build, com resultado registrado

- Objetivo/valor: produzir uma medição atual (não herdada de 09–11/09/2026) para permitir considerar a promoção de `BASELINE-001`.
- Requisito/fonte: `BKL-AV-003`; política de execução (relatório antigo não é prova do estado atual).
- Tipo: investigação/validação.
- Prioridade proposta: alta — pré-requisito para qualquer alegação de saúde funcional atual.
- Dependências: nenhuma código-dependente; pode ocorrer antes ou em paralelo a `BL-AV-1-01`.
- Critérios de aceite: `pytest` do Core e do AI Engine e `npm run build` do frontend executados nesta trilha, com contagem de passed/failed real e data.
- Validações/evidências esperadas: saída de comando anexada ao snapshot de fechamento da sprint.
- Riscos: divergência entre o número histórico (11 Core / 21 AI Engine) e o atual deve ser explicada, não ocultada.
- Decisões pendentes: nenhuma.
- Etapa/Marco/Sprint: 1 / Marco 1 / AV-S01.
- Status: proposto.

### BL-AV-1-08 — Confirmar RN-017 (IA indisponível) após as correções de autorização

- Objetivo/valor: garantir que a correção de `BL-AV-1-02` não quebrou o comportamento já validado de "falha da IA não fabrica resultado".
- Requisito/fonte: RN-017; teste existente `test_ai_engine_unavailable_does_not_fabricate_result` em `core/app/tests/test_core_flow.py`.
- Tipo: débito/correção (guarda de regressão).
- Prioridade proposta: alta.
- Dependências: `BL-AV-1-02`.
- Critérios de aceite: teste existente continua passando após as correções de autorização; se o comportamento mudar, isso é decisão explícita, não efeito colateral silencioso.
- Validações/evidências esperadas: execução do teste citado após as mudanças, com resultado real.
- Riscos: baixo, é validação de não regressão.
- Decisões pendentes: nenhuma.
- Etapa/Marco/Sprint: 1 / Marco 1 / AV-S01.
- Status: proposto.

### BL-AV-1-09 — Isolar testes do caminho de reparo de JSON do modo global do AI Engine (`DEBT-AV-009`)

- Objetivo/valor: tornar os testes que validam o caminho real de reparo de JSON determinísticos e independentes de `AI_ENGINE_MODE` herdado do processo, sem alterar o comportamento da cascata nem suas expectativas funcionais.
- Requisito/fonte: `DEBT-AV-009`, investigado no saneamento `EXEC-2026-09-23-05` e explicitamente aceito por Rafael como débito residual a priorizar na próxima sprint elegível.
- Tipo: débito/correção de isolamento de teste.
- Causa raiz confirmada: `test_invalid_llm_json_triggers_repair_and_succeeds` e `test_invalid_llm_json_fails_after_repair_returns_502` exercitam deliberadamente o caminho real (`ollama_client.generate`/`repair_json`) mas não fixam `settings.ai_engine_mode="real"`; com `AI_ENGINE_MODE=simulated` global, a RN-017 desvia corretamente para o ramo simulado antes dos mocks.
- Prioridade proposta: média — não é defeito do produto nem falha do comando oficial (`pytest -v` passa 21/21), mas prejudica isolamento e reprodutibilidade da suíte sob ambiente globalmente simulado.
- Dependências: causa raiz já confirmada em `EXEC-2026-09-23-05`; nenhuma decisão de produto pendente; não depende de Ollama real.
- Escopo incluído: fixar explicitamente o modo `real` dentro dos 2 testes (preferencialmente via fixture/`monkeypatch` localizado), preservar todas as expectativas atuais e adicionar/confirmar teste específico do ramo simulado.
- Fora de escopo: alterar RN-017, modificar o comportamento do modo simulado, suavizar expectativas para obter verde, ou alegar validação de inferência real.
- Critérios de aceite: (1) `pytest -q` sem variável externa passa 21/21; (2) `AI_ENGINE_MODE=simulated pytest -q` também passa, porque os 2 testes do caminho real isolam seu pré-requisito e os testes do ramo simulado continuam validando `engine_mode="simulated"`/`SIMULATED_MODE`; (3) os 2 testes ainda comprovam chamada única de reparo e HTTP 502 após reparo inválido; (4) nenhuma expectativa funcional é removida ou enfraquecida.
- Validações/evidências esperadas: suíte completa nos dois ambientes (default e simulado global), execução direcionada dos 2 testes, diff de expectativas revisado por agente distinto do autor.
- Riscos: monkeypatch no alvo errado ou fixture ampla mascarar o ramo simulado; mitigar limitando o override aos 2 testes que exigem caminho real e reexecutando explicitamente os testes do modo simulado.
- Decisões pendentes: nenhuma de produto; inclusão na AV-S02 depende apenas da aprovação do plano por Rafael.
- Etapa/Marco/Sprint: 1 / Marco 1 / AV-S02.
- Status: **implementado e validado em AV-S02 (2026-09-23)** — diff mínimo em `ai-engine/tests/test_schema_repair_and_fallback.py` (2 linhas, `monkeypatch.setattr(settings, "ai_engine_mode", "real")`, revertido automaticamente ao fim de cada teste); suíte padrão (`pytest -q`) e suíte com `AI_ENGINE_MODE=simulated` global ambas 21/21 passed, reexecutadas independentemente por Hermes; revisão cruzada por Antigravity CLI: aprovação incondicional, citando aderência ao padrão já usado em `tests/test_ollama_unavailable.py` e `tests/test_simulated_mode.py`. `DEBT-AV-009` permanece formalmente aberto no registro de débitos até homologação explícita do fechamento de AV-S02 por Rafael, mas sua causa técnica está sanada nesta implementação — origem deste item: aumento do backlog canônico de 68 para 69 itens (registrado em GOV-005/dashboard), pois `BL-AV-1-09` não existia antes do saneamento de AV-S01 que investigou `DEBT-AV-009`.

### BL-AV-1-10 — Idempotência da revisão humana (`DEBT-AV-011`, achado real da validação visual de AV-S02)

- Objetivo/valor: impedir que a mesma correção (`CorrectionJob`) receba múltiplas `HumanReview` conflitantes, preservando uma única fonte de verdade para a nota final e para a auditoria.
- Requisito/fonte: achado real durante a execução de `BL-AV-1-05` (validação visual completa do fluxo, AV-S02, 2026-09-23) — não é uma hipótese, foi reproduzido 3 vezes por vias independentes: Playwright (UI real), `curl` direto ao Core, e leitura de código por Antigravity CLI.
- Tipo: débito/correção (integridade de dados).
- Achado técnico confirmado: `POST /v1/corrections/{job_id}/reviews` (`core/app/main.py`, rota `review_correction`) não verifica se já existe uma `HumanReview` para o `job_id`; o modelo `HumanReview` (`core/app/models.py`) não tem `UniqueConstraint`/índice único em `job_id`; `job.status` nunca transiciona para um estado do tipo "revisado" (o enum `JobStatus` só tem `PENDENTE`/`PROCESSANDO`/`SUGERIDA`/`FALHA`); o frontend (`ReviewPage.tsx`) não recebe nenhum sinal de que a revisão já ocorreu, então reabrir a URL sempre mostra o formulário completo, com os botões "Aprovar"/"Alterar sugestão" ativos.
- Reprodução real: um mesmo job fictício (`4f56a10b-3a44-4df5-9047-adef7546a3c0`, dados de teste de AV-S02) acumulou 3 linhas em `human_reviews`, todas `decision=APPROVE`, `final_total=2.00`, sem nenhum erro ou aviso em nenhuma das 3 tentativas.
- Prioridade proposta: alta — integridade de dados e auditoria pedagógica; qualquer exportação de notas por `job_id` sem `ORDER BY`/`LIMIT 1` explícito é não determinística; múltiplos `AuditEvent` poluem o log de conformidade.
- Dependências: nenhuma decisão de produto pendente para investigar; a correção em si (política de "última revisão vence" vs. "primeira revisão é definitiva" vs. bloquear resubmissão) é uma decisão de produto que cabe a Rafael antes de implementar.
- Escopo proposto (não implementado nesta sprint — fora da autorização de AV-S02): decisão de política de idempotência; enforcement no backend (unique constraint ou checagem explícita); comunicação clara no frontend quando o job já foi revisado.
- Fora de escopo desta descoberta: qualquer correção de código — este item apenas registra o achado para decisão e priorização futuras.
- Critérios de aceite (quando priorizado): reabrir a revisão de um job já decidido mostra o resultado já registrado, não um formulário editável; tentativa de reenvio é bloqueada ou tratada explicitamente conforme a política decidida; nenhuma duplicata é criada em `human_reviews` para o mesmo `job_id`.
- Validações/evidências esperadas: reprodução automatizada (teste de integração tentando revisar 2x o mesmo job) + verificação de idempotência real via HTTP.
- Riscos: se corrigido sem decisão de política, pode-se silenciosamente perder a decisão mais recente do professor (se "primeira revisão vence" for a escolha errada) ou impedir correções legítimas de erro de digitação do próprio professor (se bloquear totalmente reenvio).
- Decisões pendentes: política aprovada por Rafael em 2026-09-24 — uma única decisão final por job; reenvio equivalente retorna existente; tentativa diferente retorna 409; alteração posterior exige fluxo auditável separado.
- Etapa/Marco/Sprint: 1 / Marco 1 / AV-S02.
- Status: **implementado e validado localmente em AV-S02 (2026-09-24)** — backend idempotente/transacional (`UniqueConstraint` + tratamento de `IntegrityError`), contexto retorna `human_review`, frontend somente leitura, 42/42 Core, concorrência/equivalência/conflito/autorização cobertos, revalidação visual real AC-04/AC-10 confirmada. Migração Alembic criada e testada em SQLite isolado com 3 duplicatas (3→1), mas **não aplicada ao `avalia_dev` operacional**; os 3 duplicados fictícios existentes permanecem preservados até autorização específica de saneamento/migração.

## 4. Detalhamento — Etapas 2 a 8

### Etapa 2 — Estrutura acadêmica (Marco 1, AV-S03)

- **BL-AV-2-01** Modelo de dados Organização/Curso/Disciplina/Turma/Aluno. Fonte: RF-02 do PRD (hoje reduzido a vínculo mínimo professor↔avaliação, ver `docs/arquitetura.md`). Tipo: proposta nova. Prioridade: alta — pré-requisito de toda a etapa. Dependências: nenhuma. Critério de aceite: modelo suporta pelo menos Organização→Curso→Disciplina→Turma→Aluno com FK coerentes. Validação: migração aplicada e testada em ambiente local. Risco: sobre-modelagem além do necessário para uma turma piloto — escopo deve ser mínimo viável, não o modelo conceitual completo do PRD. Decisão pendente: nenhuma trava o início do desenho, mas o volume-alvo (`DEC-AV-007`) deve orientar o dimensionamento.
- **BL-AV-2-02** Migração Alembic da estrutura acadêmica. Tipo: proposta nova. Prioridade: alta. Dependência: `BL-AV-2-01`. Critério de aceite: `alembic upgrade head` aplica sem erro em base local limpa e em base com dados de seed existentes. Validação: execução real registrada.
- **BL-AV-2-03** Permissões por vínculo professor↔turma nos endpoints. Tipo: proposta nova. Prioridade: alta. Dependência: `BL-AV-2-01`/`02` e a correção de `BL-AV-1-02` (mesmo padrão de verificação de vínculo). Critério de aceite: endpoints de turma/aluno seguem o mesmo padrão de autorização corrigido na etapa 1.
- **BL-AV-2-04** Telas mínimas de cadastro de turma/aluno e vínculo à avaliação. Tipo: proposta nova. Prioridade: média. Dependência: `BL-AV-2-03`.
- **BL-AV-2-05** Critério de aceite do marco: criar turma fictícia, cadastrar alunos e vincular avaliação respeitando limites de acesso — este item é o "resultado esperado" da etapa 2 formalizado como item de aceite, não uma tarefa de código isolada.

Decisões pendentes desta etapa: quantidade de turmas/alunos-alvo (`DEC-AV-007`); ambiente-alvo (`DEC-AV-006`).

### Etapa 3 — Avaliações completas (Marco 1, AV-S04)

- **BL-AV-3-01** Suportar múltiplas questões por avaliação. Achado por inspeção: `core/app/models.py` já modela `Assessment 1:N Question`, mas `AssessmentCreate` (schema) e os endpoints atuais só criam/lêem uma questão por chamada (`payload.question`, singular). Tipo: proposta nova (extensão de contrato + telas). Prioridade: alta. Dependência: nenhuma código-bloqueante; recomenda-se depois da etapa 1 para não sobrepor mudanças de autorização.
- **BL-AV-3-02** Regras de edição/publicação/imutabilidade com múltiplas questões. Tipo: proposta nova. Prioridade: alta. Dependência: `BL-AV-3-01`. Risco: revisitar a regra "rubrica publicada é imutável" (RF-05) para múltiplas questões sem alterar a garantia de auditoria de correções já feitas.
- **BL-AV-3-03** Versionamento de questão preservado nas correções já feitas. Tipo: requisito existente (parcial — `Rubric.version` já existe; `Question` não tem versionamento). Prioridade: alta. Dependência: `BL-AV-3-01`.
- **BL-AV-3-04** Atualizar contrato OpenAPI/schema (`docs/contracts/openapi.yaml`) para múltiplas questões. Tipo: débito de documentação. Prioridade: média. Dependência: `BL-AV-3-01`/`02`.

### Etapa 4 — Entrada de respostas em escala (Marco 2, AV-S05/AV-S06)

- **BL-AV-4-01** Contrato de importação CSV. Fonte: RF-06/RF-08 (backlog). Tipo: proposta nova. Prioridade: alta. Dependência: nenhuma.
- **BL-AV-4-02** Prévia de importação com relatório de erros por linha. Tipo: proposta nova. Prioridade: alta. Dependência: `BL-AV-4-01`.
- **BL-AV-4-03** Vínculo aluno↔avaliação↔questão↔resposta via estrutura acadêmica. Tipo: requisito existente, mas depende de infraestrutura ainda não construída. Dependência: etapa 2 concluída.
- **BL-AV-4-04** Regras de duplicidade, reenvio e confirmação. Tipo: decisão + implementação. Prioridade: alta. Decisão pendente: política de reenvio (`DEC-AV-008`).
- **BL-AV-4-05** Registro de importação e tratamento de falha parcial. Tipo: proposta nova. Prioridade: média.

### Etapa 4B — Entrada por imagem e transcrição assistida (Marco 2, AV-S05B a AV-S10B)

> Frente incluída em 2026-09-21 a pedido explícito de Rafael. Ver reconciliação com o PRD em §1.1. Regra transversal desta etapa, decorrente do fluxo funcional definido pelo usuário: **a correção assistida pela rubrica não inicia automaticamente antes da confirmação humana da transcrição** — este é um critério de aceite de todos os itens de associação (`BL-AV-4B-14`), não apenas uma recomendação.

**A. Investigação técnica de OCR local**

- **BL-AV-4B-01** Investigação técnica de OCR/visão local para texto impresso e manuscrito em português. Tipo: investigação. Prioridade: alta. Escopo: comparar OCR tradicional (ex.: motores baseados em Tesseract/PaddleOCR ou equivalentes) e modelos locais de visão (ex.: VLMs pequenos executáveis localmente), usando amostras fictícias ou autorizadas. Regra explícita do usuário: não presumir que o modelo textual atual (Ollama/`qwen2.5:7b-instruct`) atende à leitura de imagens — este é um componente novo, não uma extensão do AI Engine textual existente. **Escopo redefinido em 2026-09-22 (GOV-004):** este item é o *levantamento técnico inicial* — comparação de alternativas, licenças, requisitos de hardware e limitações conhecidas — e sua saída é uma **proposta** de métricas, amostras e limites de aceite para o benchmark comparativo (`BL-AV-4B-20`), não a medição em si. Dependência: nenhuma técnica; é uma frente independente da consolidação (Etapa 1) e pode ser planejada em paralelo a ela.
- **BL-AV-4B-02** Decisão arquitetural de motor/modelo de OCR local, registrada em novo ADR. Tipo: decisão. Prioridade: alta. Dependência: `BL-AV-4B-20` (benchmark comparativo) concluído com evidência; `DEC-AV-009` (hardware). **Reposicionado em 2026-09-22 (GOV-004):** não decorre diretamente do levantamento (`BL-AV-4B-01`), e sim do benchmark comparativo já medido — ver `BL-AV-4B-20`.
- **BL-AV-4B-17** Isolamento/arbitragem de recursos entre o processo de OCR/visão e o processo de correção local (ambos podem competir por memória/CPU/GPU no mesmo hardware). Tipo: decisão. Prioridade: alta. Regra explícita do usuário: processamento de OCR e processamento de correção devem ser tratados como serviços separados, ainda que compartilhem infraestrutura — não fundir os dois em um único processo/modelo. Dependência: `BL-AV-4B-02`, `DEC-AV-009`.
- **BL-AV-4B-20** *(novo, GOV-004, 2026-09-22; detalhamento completo em 2026-09-23)* Benchmark comparativo de OCR/visão local. Tipo: investigação/validação. Prioridade: alta.
  - Objetivo/valor: medir, com critérios já aprovados por Rafael, qual alternativa de OCR/visão local (dentre as levantadas em `BL-AV-4B-01`) melhor atende texto impresso e manuscrito em português, produzindo a evidência que fundamenta a decisão arquitetural (`BL-AV-4B-02`).
  - Requisito/fonte: instrução explícita de Rafael de separar levantamento e benchmark, com critérios aprovados antes de medir; proposta de eixos de métrica registrada no pacote de revisão desta sessão (qualidade de transcrição/CER-WER, esforço de revisão humana, latência no hardware-alvo, robustez a ilegível/ausente sem invenção de texto, viabilidade 100% local como critério eliminatório).
  - Escopo: executar a medição comparativa sobre um conjunto de amostras (fictícias ou autorizadas) cobrindo fotos nítidas, inclinadas, desfocadas, com iluminação irregular, texto impresso e manuscrito, acentuação, rasuras, respostas vazias/ilegíveis — mesma cobertura prevista em `BL-AV-4B-18`, para reaproveitar o conjunto de teste.
  - Tipo: investigação/validação.
  - Prioridade: alta — é o item que fundamenta a única decisão arquitetural de toda a Etapa 4B (`BL-AV-4B-02`).
  - Dependências: `DEC-AV-017` (métricas e critérios de aceite aprovados por Rafael, antes de qualquer medição) e a proposta produzida por `BL-AV-4B-01`; `DEC-AV-009` (hardware-alvo) para a métrica de latência especificamente — as demais métricas (qualidade, esforço de revisão, robustez) não dependem de hardware definido.
  - Critérios de aceite: relatório comparativo reproduzível, com cada alternativa avaliada nos eixos aprovados em `DEC-AV-017`, critérios não ajustados retroativamente para favorecer um resultado (regra explícita do usuário), e recomendação explícita registrada como insumo para `BL-AV-4B-02` — não como decisão em si.
  - Validações/evidências esperadas: execução real do benchmark sobre o conjunto de amostras definido, com resultado datado e método registrado (mesmo padrão de rigor já exigido para `BL-AV-7-06`/`BL-AV-7-01` na qualidade da IA de correção).
  - Riscos: amostras não representativas podem favorecer uma alternativa por acaso, não por qualidade real — mitigação é o próprio conjunto amplo já herdado de `BL-AV-4B-18`; viés de escolha de critérios após ver resultados parciais — mitigado pela regra de não ajustar critérios retroativamente.
  - Decisões pendentes: `DEC-AV-017` (bloqueante direto, não bloqueia o levantamento `BL-AV-4B-01`); `DEC-AV-009` (bloqueia apenas a métrica de latência, medida no hardware-alvo real).
  - Etapa/Marco/Sprint: 4B / Marco 2 / AV-S05B (reposicionado em GOV-004 — antes listado em AV-S06B).
  - Status: proposto.
- **BL-AV-4B-21** *(novo, GOV-004, 2026-09-22; detalhamento completo em 2026-09-23)* Processamento assíncrono confiável da extração de uma imagem, persistente e recuperável. Tipo: proposta nova. Prioridade: alta.
  - Objetivo/valor: garantir que a extração de uma imagem (execução do OCR/visão sobre uma resposta) não perca trabalho nem duplique resultado se o processo for reiniciado, sem depender de infraestrutura de lote — é um requisito de confiabilidade da *primeira entrega* (uma imagem por vez), não do processamento em volume tratado na Etapa 5.
  - Requisito/fonte: instrução explícita de Rafael — "Não adie requisitos de confiabilidade indispensáveis à primeira entrega. Diferencie processamento assíncrono confiável de processamento em lote." Mesmo princípio já aplicado ao fluxo de correção textual existente (`CorrectionJob`/`BackgroundTasks`, `core/app/main.py`, rota `request_correction`), estendido ao novo canal de imagem.
  - Escopo: persistir o estado da extração (pendente/processando/concluída/falha) de forma equivalente ao já existente em `CorrectionJob.status`/`attempt`; permitir retomada após reinício do processo sem duplicar a extração nem perder o resultado já obtido; **não inclui** fila de lote, múltiplos workers concorrentes ou priorização de fila — isso é escopo da Etapa 5 (`BL-AV-5-02/03/04`), item explicitamente distinto.
  - Tipo: proposta nova.
  - Prioridade: alta — é pré-requisito funcional da Fase 4 (primeira entrega completa por imagem), não uma otimização posterior.
  - Dependências: decisão arquitetural de motor/modelo já implementável (`BL-AV-4B-02`, que por sua vez depende de `BL-AV-4B-20`); não depende de `BL-AV-5-02` (arquitetura de lote) — são mecanismos distintos, ainda que o mesmo padrão de idempotência de `CorrectionJob.attempt` sirva de referência de design.
  - Critérios de aceite: reiniciar o processo do Core durante uma extração em andamento não duplica a extração nem perde o resultado; o estado da extração é consultável (mesmo padrão de polling já usado por `CorrectionPage.tsx` para `CorrectionJob`); falha de extração é diferenciada de ausência de texto (mesma regra de não completar por suposição já registrada em `BL-AV-4B-07`).
  - Validações/evidências esperadas: teste de integração simulando reinício do processo durante extração pendente, confirmando ausência de duplicação e de perda de resultado.
  - Riscos: se implementado de forma acoplada à futura arquitetura de lote (`BL-AV-5-02`) sem essa distinção clara, pode gerar retrabalho quando a Etapa 5 for desenhada — mitigação é a separação explícita já registrada nesta entrada e no §11 da trilha (Fase 4 vs. Fase 5).
  - Decisões pendentes: nenhuma decisão de produto bloqueia o desenho; a implementação depende de `BL-AV-4B-02` estar resolvida (motor/modelo escolhido).
  - Etapa/Marco/Sprint: 4B / Marco 2 / AV-S07B (junto da preparação/extração local).
  - Status: proposto.

**B. Recebimento e armazenamento de imagens**

- **BL-AV-4B-03** Formatos, tamanho, resolução e quantidade de páginas suportados; validação do conteúdo real do arquivo (não apenas a extensão declarada). Tipo: proposta nova. Prioridade: alta. Decisão pendente: `DEC-AV-018` (uma resposta por imagem ou prova inteira) e `DEC-AV-019` (suporte a múltiplas páginas) — este item não deve assumir suporte ao caso mais amplo sem essas decisões.
- **BL-AV-4B-04** Controle de acesso por professor/avaliação (mesmo padrão de vínculo da etapa 1/`BL-AV-1-02`); preservação do arquivo original; registro de vínculo, autoria e data. Tipo: proposta nova. Prioridade: alta. Dependência: correção de autorização da etapa 1 já aplicada, para não repetir a lacuna em um novo tipo de recurso.
- **BL-AV-4B-05** Retenção, exclusão e tratamento de metadados; exclusão de imagem, nome de aluno e texto de resposta completo dos logs. Tipo: decisão + implementação. Prioridade: alta. Decisão pendente: `DEC-AV-013` (retenção geral de dados, já registrada em GOV-002) aplicada especificamente a imagens.

**C. Preparação e extração local**

- **BL-AV-4B-06** Tratamento de orientação/inclinação quando necessário; detecção de imagem inadequada com solicitação de nova captura; preservação do original com derivados identificados separadamente. Tipo: proposta nova. Prioridade: média.
- **BL-AV-4B-07** Execução local da extração, sem envio a API externa — mesmo princípio já aplicado ao AI Engine textual (ADR-005), estendido ao componente de imagem. Tipo: proposta nova. Prioridade: alta. Regra explícita do usuário: não completar por suposição trechos ilegíveis — extração deve sinalizar incerteza, nunca inventar texto.
- **BL-AV-4B-08** Registro de motor/modelo, versão, parâmetros relevantes, duração e resultado da extração; diferenciação explícita entre falha de processamento, ausência de texto e trecho ilegível. Tipo: proposta nova. Prioridade: alta. Padrão a seguir: mesmo nível de transparência que `AIExecution`/`engine_mode` já aplicam no fluxo textual (`core/app/models.py`).
- **BL-AV-4B-09** Tratar qualquer instrução textual presente na imagem como conteúdo não confiável. Tipo: débito/correção — extensão direta da detecção de prompt injection já existente em `ai-engine/app/cascade.py` (flag `PROMPT_INJECTION_SUSPECTED`) para o novo canal de entrada. Prioridade: alta.

**D. Conferência da transcrição**

- **BL-AV-4B-10** Tela de conferência exibindo imagem e texto extraído lado a lado. Tipo: proposta nova. Prioridade: alta. Padrão de UI a reaproveitar: mesmo princípio de "resposta do aluno — somente leitura" já usado em `ReviewPage.tsx`, adaptado para imagem + texto editável.
- **BL-AV-4B-11** Edição e confirmação da transcrição pelo professor; preservação de texto bruto extraído, texto corrigido e histórico da confirmação (mesmo padrão de auditoria de `HumanReview`/`AuditEvent`). Tipo: proposta nova. Prioridade: alta.
- **BL-AV-4B-12** Sinalizar incerteza de leitura sem apresentá-la como probabilidade calibrada. Tipo: débito/correção — mesma regra já aplicada à confiança de correção (RN-016, ADR-008, `DEBT-AV-002`), estendida à confiança de leitura. Prioridade: alta. Regra explícita do usuário e desta governança: não confundir confiança de leitura com confiança de correção pedagógica (ver item E abaixo).
- **BL-AV-4B-13** Transcrição manual quando a extração falhar. Tipo: proposta nova. Prioridade: média. Mesmo princípio de RN-017 (IA indisponível → correção manual) aplicado à falha do componente de OCR.

**E. Associação e correção**

- **BL-AV-4B-14** Vincular a resposta confirmada ao aluno, à avaliação e à questão correta; **impedir que a correção assistida inicie antes da confirmação humana da transcrição**. Tipo: proposta nova. Prioridade: alta — este é o critério funcional central da etapa, definido explicitamente pelo usuário. Dependência: `BL-AV-4B-11` (tela de confirmação existente) e, quando aplicável, etapa 2 (vínculo aluno/turma).
- **BL-AV-4B-15** Preservar a cadeia completa: imagem → execução OCR → transcrição confirmada → correção → revisão humana. Tipo: requisito existente parcial — a cadeia correção→revisão já existe (`CorrectionJob`→`AIExecution`→`HumanReview`); os dois elos novos (imagem, execução OCR, transcrição confirmada) precisam de modelagem própria, preservando o restante sem alterá-lo.
- **BL-AV-4B-16** Idempotência/deduplicação em reenvios e retentativas de imagem, evitando duplicar resposta ou correção. Tipo: proposta nova. Prioridade: média. Mesmo princípio já aplicado a `CorrectionJob.attempt` (`core/app/main.py`, linha do contador `prior_attempts`).

Regra explícita desta subseção: não confundir confiança de leitura (qualidade da extração de texto) com confiança de correção pedagógica (qualidade da nota sugerida) — são dois indicadores distintos, com fontes e semânticas diferentes, e nenhum documento desta trilha deve apresentá-los como equivalentes ou combiná-los em um único número sem justificativa registrada.

**F. Avaliação e testes**

- **BL-AV-4B-18** Conjunto de testes cobrindo: fotos nítidas, inclinadas, desfocadas, com iluminação irregular; texto impresso e manuscrito; acentuação, rasuras, linhas; respostas vazias ou ilegíveis; isolamento de acesso; preservação do original; medição de qualidade de transcrição, esforço de revisão humana e latência. Tipo: proposta nova. Prioridade: alta. Dependência: `DEC-AV-017` (critérios de qualidade mínimos, definidos antes da medição, mesmo princípio já registrado para a etapa 7/IA em `BL-AV-7-06`).
- **BL-AV-4B-19** Teste ponta a ponta demonstrando que um erro de OCR pode ser corrigido pelo professor antes de qualquer avaliação pedagógica ocorrer — este é o teste de aceite que comprova a regra "correção não inicia antes da confirmação" (`BL-AV-4B-14`). Tipo: proposta nova. Prioridade: alta.

**Decisões específicas desta etapa** (ver seção 7 do documento de trilha para o mapa completo de bloqueio): `DEC-AV-016` (ordem relativa entre Etapa 4 e 4B), `DEC-AV-017` (métricas e critérios de aceite de OCR, definidos antes do benchmark), `DEC-AV-018` (uma resposta por imagem vs. prova inteira na primeira versão), `DEC-AV-019` (suporte a múltiplas páginas), `DEC-AV-020` (necessidade de fórmulas/tabelas/desenhos/código manuscrito), `DEC-AV-021` (identificação manual vs. automática de aluno/questão na imagem).

**Regra explícita de não-presunção:** esta etapa não assume suporte a múltiplas páginas, fórmulas, tabelas, desenhos, código manuscrito ou identificação automática de aluno/questão na primeira entrega. Cada um desses cenários só entra no escopo de uma sprint mediante decisão explícita nas linhas acima.

### Etapa 5 — Processamento confiável em lote (Marco 2, AV-S07/AV-S08)

- **BL-AV-5-01** Revisar ADR-006 à luz do volume-alvo real. Tipo: investigação. Prioridade: alta. Dependência: `DEC-AV-007` (quantidade de respostas-alvo) e `DEC-AV-009` (hardware).
- **BL-AV-5-02** Decisão de arquitetura de worker/persistência para lote, registrada em novo ADR. Tipo: decisão. Prioridade: alta. Regra explícita do usuário: não escolher broker antecipadamente sem avaliar necessidade.
- **BL-AV-5-03** Idempotência e concorrência no processamento em lote. Tipo: proposta nova. Dependência: `BL-AV-5-02`.
- **BL-AV-5-04** Progresso, retentativa e recuperação após reinício sem duplicar correção. Tipo: proposta nova. Dependência: `BL-AV-5-02`/`03`. Este é o critério de aceite central do marco 2 para esta etapa.
- **BL-AV-5-05** Semântica de pausa/cancelamento. Tipo: investigação — não há requisito explícito localizado no PRD/backlog para isso; precisa confirmar se é necessidade real do piloto ou escopo futuro.
- **BL-AV-5-06** Tratamento de indisponibilidade da IA em lote. Tipo: requisito existente (extensão do padrão RN-017 já implementado unitariamente em `core/app/services/correction.py`).

### Etapa 6 — Revisão e resultados (Marco 2, AV-S09)

- **BL-AV-6-01** Fila de revisão com filtros. Fonte: RF-12/backlog G2. Tipo: proposta nova. Prioridade: alta.
- **BL-AV-6-02** Revisão por critério em lote e tratamento manual em massa. Tipo: proposta nova. Prioridade: média. Dependência: etapa 5.
- **BL-AV-6-03** Histórico agregado de decisões e reprocessamentos. Tipo: requisito existente parcial — `HumanReview`/`AuditEvent` já existem por job individual (ver `core/app/models.py`); falta visão agregada por turma/avaliação.
- **BL-AV-6-04** Exportação de notas finais separada da sugestão da IA. Fonte: RF-11 (backlog). Tipo: proposta nova. Prioridade: alta.
- **BL-AV-6-05** Mapear dependências de segunda revisão e liberação ao aluno. Tipo: investigação. Decisões pendentes: `DEC-AV-010` (segunda revisão), `DEC-AV-011` (liberação ao aluno).

### Etapa 7 — Qualidade da IA (atravessa Marco 2 e antecede Marco 3, AV-S10/AV-S11)

- **BL-AV-7-01** Conjunto de referência revisado por humanos. Tipo: proposta nova. Prioridade: alta. Decisão pendente: `DEC-AV-012` (responsáveis pelas referências humanas).
- **BL-AV-7-02** Framework de avaliação (pontuação por critério, evidência, justificativa vs. referência humana). Tipo: proposta nova. Dependência: `BL-AV-7-01`.
- **BL-AV-7-06** Definir métricas e critérios de aceitação antes de medir. Tipo: decisão. Prioridade: alta — regra explícita do usuário ("definir critérios antes das medições"). Deve ocorrer antes ou junto de `BL-AV-7-01`/`02`, não depois.
- **BL-AV-7-08** Separar confiança heurística de confiança calibrada. Tipo: débito/correção (`DEBT-AV-002`, ADR-008). Prioridade: alta — hoje já é declarado no código como não calibrado; falta um mecanismo formal de comparação quando houver dados humanos.
- **BL-AV-7-03** Regressão de modelos/prompts sobre o framework. Dependência: `BL-AV-7-02`.
- **BL-AV-7-04** Robustez a entradas adversariais. Tipo: débito/correção — hoje existe apenas detecção básica de prompt injection (`ai-engine/app/cascade.py`, flag `PROMPT_INJECTION_SUSPECTED`); ampliar cobertura de casos.
- **BL-AV-7-05** Benchmark de latência/recursos no hardware-alvo. Dependência: `DEC-AV-009` (hardware disponível).
- **BL-AV-7-07** Avaliar embeddings mediante hipótese e benefício mensurável. Tipo: investigação, prioridade baixa — só avança se `BL-AV-7-02` mostrar necessidade real, evitando repetir a decisão não fundamentada de excluir/incluir componentes da cascata sem medição (`DEBT-AV-003`).

Regra explícita desta etapa: nenhum resultado de exemplo isolado ou teste de software será apresentado como qualidade pedagógica, calibração ou ganho de produtividade.

### Etapa 8 — Integração e homologação (Marco 3, AV-S12/AV-S13)

- **BL-AV-8-01** Dashboard pedagógico/operacional do produto — explicitamente distinto do Dashboard Executivo de Evolução Técnica da governança. Fonte: RF-12. Tipo: proposta nova.
- **BL-AV-8-02** Acessibilidade dirigida dos fluxos centrais (não auditoria WCAG completa). Tipo: débito/correção parcial.
- **BL-AV-8-03** Testes ponta a ponta automatizados. Tipo: proposta nova. Prioridade: alta — hoje só existe `core/app/tests` e `ai-engine/tests`; nenhum teste e2e cobrindo frontend+Core+AI Engine foi encontrado nesta sessão.
- **BL-AV-8-04** Teste de carga proporcional ao cenário-alvo. Dependência: `DEC-AV-007`/`DEC-AV-009`.
- **BL-AV-8-05** Instalação reproduzível, configuração, backup e recuperação. Tipo: débito/correção — `infra/compose/` e `scripts/` estão vazios nesta inspeção (`ls -la` executado nesta sessão).
- **BL-AV-8-06** Roteiro de homologação e evidências de aceite. Tipo: proposta nova. Dependência: `DEC-AV-006` (ambiente-alvo) e conclusão das etapas 1–7 aplicáveis ao piloto decidido.

## 5. Itens mantidos fora desta trilha (não descartados)

- API pública/webhooks (RF-14).
- Auditoria de pesquisa com dataset anonimizado (RF-15) — depende de `BKL-AV-001`.
- Teste de usabilidade formal com meta quantitativa (seção 4.2 do PRD).
- Auditoria de acessibilidade WCAG completa.
- Protocolo de validação científica (seção 27 do PRD).
- Scanner automatizado de segredos/dependências.
- Observabilidade avançada (tracing distribuído, alertas).
- Runbooks operacionais completos (seção 19.1 do PRD) além do necessário para o piloto decidido.
- Decisões D-08, D-11, D-12 do PRD, exceto quando um item desta trilha as referencia explicitamente como dependência.

Esses itens permanecem candidatos a trilhas futuras e não perdem rastreabilidade: continuam descritos em `docs/backlog.md` (histórico) e nesta seção.
