---
id: "AV-S05B"
status: investigacao_experimental_executada_aguardando_revisao_final
objetivo_aprovado_por: "Rafael (2026-09-29; DEC-AV-017 aprovada com ajustes)"
consolidador: "Hermes"
baseline_entrada: "../snapshots/latest_execution.md (main em a5974b1ffecc18f59ed2df39bdf5ce4a210bf0e8, AV-S03 integrada e homologada; AV-S05B não depende deste baseline, mas parte dele como estado de main)"
---

# AV-S05B — Investigação de OCR/visão local e decisão arquitetural (Etapa 4B, parte 1)

> **Status: INVESTIGAÇÃO EXPERIMENTAL EXECUTADA (2026-09-29), fora do repositório
> de produção. Nenhum código de produção alterado, nenhuma ação Git/remota,
> nenhuma alteração em `avalia_dev`, nenhuma implantação de OCR na plataforma,
> nenhuma promoção de baseline, nenhuma nova sprint.**
>
> Rafael aprovou `DEC-AV-017` com ajustes em 2026-09-29 e autorizou benchmark
> local isolado, scripts experimentais, instalação de dependências em
> ambiente dedicado e download de modelos públicos com licenças compatíveis.
> Toda a execução ocorreu em
> `/Users/rafaeloliveira/Projeto Estágio/av-s05b-benchmark-experimento/`
> (fora deste repositório, diretório local durável sem Git/remote; um Git local
> chegou a ser inicializado por erro de processo e foi removido integralmente,
> preservando arquivos e checksums — ver seção de desvios).
> **Localização após a consolidação de 2026-09-30:** o caminho acima é o
> local histórico da execução. O ambiente de trabalho foi movido para
> `experiments/av-s05b/` (ignorado pelo Git); a evidência canônica permanece em
> `docs/governance/evidence/AV-S05B/`.
>
> **Escopo desta rodada: exclusivamente texto impresso.** O eixo de
> manuscrito permanece PENDENTE — Rafael determinou que exige escrita manual
> real autorizada (fonte tipográfica não é substituto aceitável) e forneceria
> essa amostra em rodada futura.



## 1. Objetivo e valor esperado

Retomar a prioridade de entrada por imagem (Etapa 4B), já decidida por Rafael em `DEC-AV-016`
(2026-09-21: imagem priorizada sobre CSV) e sequenciada como a segunda frente elegível da trilha
(`trilha_operacao_de_turma.md` §11, Fase 2 — independente da Fase 3/estrutura acadêmica, que já foi
concluída em `AV-S03`).

Resultado observável esperado desta sprint: (1) `DEC-AV-017` aprovada por Rafael — métricas e
critérios de aceite do benchmark de OCR/visão local, definidos **antes** de qualquer medição; (2)
`BL-AV-4B-20` executado — benchmark comparativo real, medido contra esses critérios, sobre um
conjunto de amostras fictícias/autorizadas; (3) `BL-AV-4B-02` decidido — ADR novo registrando a
alternativa de OCR/visão escolhida, fundamentada no benchmark, não presumida antes dele.

Não é resultado desta sprint: nenhuma linha de código de produção, nenhuma dependência instalada no
repositório, nenhuma imagem real de aluno processada, nenhuma tela de UI para upload de imagem
(isso é `AV-S06B` em diante).

## 2. Origem

| Fonte/requisito | Trecho ou decisão aplicável | Link |
|---|---|---|
| `DEC-AV-016` | imagem priorizada sobre CSV — aprovada 2026-09-21 | `registers/decisions.md` |
| `DEC-AV-018` | primeira versão: uma resposta de uma questão por foto — aprovada 2026-09-21 | `registers/decisions.md` |
| `DEC-AV-021` | seleção manual pelo professor (avaliação/questão/aluno), sem identificação automática — aprovada 2026-09-21 | `registers/decisions.md` |
| `DEC-AV-025` | autorização restrita a detalhamento documental de `BL-AV-4B-01`, sem benchmark/implementação — aprovada 2026-09-24 | `registers/decisions.md` |
| `BL-AV-4B-01` | levantamento técnico de OCR/visão local — **já concluído como detalhamento documental** | `backlog/levantamento_ocr_visao_local.md` |
| `BL-AV-4B-20` | benchmark comparativo de OCR/visão local | `backlog/backlog_tecnico_avalia.md` |
| `BL-AV-4B-02` | decisão arquitetural de motor/modelo (novo ADR) | `backlog/backlog_tecnico_avalia.md` |
| `BL-AV-4B-17` | isolamento de recursos entre processo de OCR e processo de correção | `backlog/backlog_tecnico_avalia.md` |
| Trilha, §11, Fase 2 | AV-S05B é a segunda frente elegível, independente da Fase 3 (já concluída) | `backlog/trilha_operacao_de_turma.md` |
| Regra transversal da Etapa 4B | correção assistida não inicia automaticamente antes da confirmação humana da transcrição — critério de aceite de todos os itens de associação, não recomendação | `backlog/backlog_tecnico_avalia.md` §"Etapa 4B" |

Lacunas de fonte: nenhuma. O trabalho documental de `BL-AV-4B-01` já produziu a proposta completa de
alternativas, métricas, amostras e limites que esta sprint reutiliza integralmente, sem refazer.

## 3. Escopo

Incluído:
- aprovação de `DEC-AV-017` (métricas e critérios de aceite do benchmark), a partir da proposta já
  existente em `backlog/levantamento_ocr_visao_local.md` §4 e §6;
- execução real do benchmark comparativo (`BL-AV-4B-20`) sobre as alternativas levantadas em
  `BL-AV-4B-01`, usando exclusivamente amostras fictícias ou explicitamente autorizadas;
- decisão arquitetural (`BL-AV-4B-02`), registrada como novo ADR, fundamentada no benchmark medido;
- registro documental da arbitragem de recursos entre o futuro processo de OCR e o AI Engine textual
  já existente (`BL-AV-4B-17`) — apenas como nota de dependência para a Fase 4, não uma decisão de
  implementação nesta sprint (`BL-AV-4B-17` está formalmente alocado a `AV-S07B` no backlog canônico,
  não a esta sprint; ver seção 14, "Ajustes de percurso", como nota, não mudança de escopo).

Fora de escopo:
- qualquer implementação de código (`core/`, `ai-engine/`, `frontend/`) — motor de OCR, endpoint de
  upload, tela de conferência: tudo isso é `AV-S06B` em diante;
- instalação de qualquer dependência de OCR/visão no repositório ou no ambiente (Tesseract,
  PaddleOCR, EasyOCR, modelo de VLM via Ollama) fora do necessário estritamente para rodar o
  benchmark isolado, e mesmo isso só após autorização específica de execução (esta sprint, quando
  aprovada, autoriza o benchmark; a instalação de dependências para rodá-lo é parte dessa mesma
  autorização, não uma autorização adicional separada — mas nenhuma delas está incluída neste
  documento de proposta);
- processamento de qualquer imagem real de aluno;
- qualquer alteração em `avalia_dev`;
- qualquer ação Git/remota (commit, push, PR);
- suporte a múltiplas páginas, fórmulas, tabelas, desenhos ou código manuscrito (`DEC-AV-019`,
  `DEC-AV-020`, ambas pendentes — primeira versão assume texto corrido, uma resposta por foto);
- identificação automática de aluno/questão na imagem (`DEC-AV-021`, já decidida: seleção manual).

## 4. Baseline e estado de abertura

- último baseline validado: nenhum promovido sob esta governança (`snapshots/latest_validated_baseline.md`);
- última execução registrada: `EXEC-2026-09-29-03` — fechamento de `AC-05` e reconciliação do PR #2
  (`snapshots/latest_execution.md`);
- commit/branch/upstream: `main` em `a5974b1ffecc18f59ed2df39bdf5ce4a210bf0e8` (merge do PR #4,
  encerramento documental da `AV-S03`); nenhuma branch nova criada para este documento (proposta
  documental, sem ação Git autorizada nesta demanda);
- working tree e alterações preexistentes: nenhuma alteração de código pendente; este documento é o
  único artefato novo desta preparação;
- dependências e bloqueantes: `DEC-AV-017` (bloqueante direto de `BL-AV-4B-20`, não bloqueia nada já
  concluído); `DEC-AV-009` (hardware-alvo formal, pendente em caráter geral — bloqueia apenas a
  métrica de latência representativa de produção, não o restante do benchmark, ver seção 6);
  `BKL-AV-002` (próxima sprint funcional não priorizada) — esta proposta é a resposta a esse
  bloqueante, sujeita à decisão de Rafael.

## 5. Backlog e DoR

| ID | Descrição | Responsável | DoR | Estado |
|---|---|---|---|---|
| `BL-AV-4B-01` | Levantamento técnico de OCR/visão local | Hermes (já executado) | `ready` — concluído, evidência em `backlog/levantamento_ocr_visao_local.md` | implementado (documental) |
| `BL-AV-4B-20` | Benchmark comparativo de OCR/visão local | a definir na delegação (seção 7) | `ready` condicionado à aprovação de `DEC-AV-017` — todos os demais critérios do DoR já atendidos (escopo, amostras, método propostos) | planejado |
| `BL-AV-4B-02` | Decisão arquitetural (ADR) de motor/modelo de OCR | Hermes (consolidação do ADR, com base no resultado do benchmark) | não `ready` até `BL-AV-4B-20` produzir evidência — decisão não pode anteceder medição | planejado |

Checklist DoR por item: [definition_of_ready.md](../definition_of_ready.md). Nenhuma decisão crítica
pendente torna `BL-AV-4B-20` especulativo, desde que `DEC-AV-017` seja aprovada antes de qualquer
medição — essa é exatamente a ordem que este documento propõe.

**Resumo do estado dos critérios de aceite obrigatórios (AC-01 a AC-11), nesta rodada:**
9 atendidos (AC-01, AC-03, AC-04*, AC-06, AC-07, AC-08, AC-09, AC-10, AC-11), 2 parcialmente
atendidos (AC-02 — manuscrito não executado; AC-05 — apenas imagem vazia testada, escrita
totalmente ilegível não testada). Nenhum item obrigatório permanece não executado nesta rodada
— a revisão independente do ADR-009 (AC-10) foi concluída em 2026-09-29 pelo Antigravity CLI,
com correções aplicadas ao texto do ADR.
*AC-04 está marcado "atendido" com ressalva metodológica explícita registrada na própria linha
da tabela (verificação por inspeção de código, não por tráfego de rede capturado). AC-05 é
classificado como **parcial**, não "atendido com ressalva": o requisito original do critério
cobre os dois subtipos do eixo (vazio e ilegível) e apenas um foi testado — a classificação não
foi ajustada para contabilizar cobertura parcial como atendimento pleno.
Esta sprint continua classificada como **parcialmente executada** — os itens obrigatórios
pendentes são AC-02 (eixo manuscrito) e AC-05 (subtipo "escrita ilegível"), ambos dependentes
da mesma coleta de amostras reais autorizada por Rafael, e não podem ser resolvidos nesta rodada.

**Nota independente da tabela de AC**: o esforço de revisão humana (ver "Métrica pendente" na
seção 15) **permanece não medido** nesta rodada, qualquer que seja a classificação dos critérios
de aceite acima — essa métrica não é um item AC-01 a AC-13, é uma métrica separada exigida por
`DEC-AV-017`, e sua ausência não é resolvida nem mascarada pelo estado "atendido"/"parcial" de
nenhum critério de aceite.

## 6. Mapa de impacto

| Item | Criar | Alterar | Não tocar |
|---|---|---|---|
| `BL-AV-4B-20` (quando autorizado) | script(s) de benchmark isolados (proposta de caminho: `docs/governance/evidence/AV-S05B/benchmark-scripts/`); relatório de resultado (`docs/governance/evidence/AV-S05B/AC-XX_benchmark_ocr.md`) | nenhum arquivo de `core/`, `ai-engine/`, `frontend/` | `avalia_dev`; qualquer schema de banco; qualquer endpoint de API existente |
| `BL-AV-4B-02` (quando autorizado) | novo ADR (proposta de caminho: `docs/adr/ADR-0XX-motor-ocr-visao-local.md`, número exato a confirmar contra o índice atual de ADRs) | `docs/governance/backlog/backlog_tecnico_avalia.md` (status de `BL-AV-4B-02`/`20`/`01`) | código de produção — o ADR registra a decisão, a implementação é `AV-S07B` |
| Esta proposta (`AV-S05B`, planejamento) | este documento (`sprints/sprint_AV-S05B_investigacao_ocr.md`, quando movido para o repositório); proposta de `DEC-AV-017` para aprovação | nenhum | nenhum código; nenhuma dependência instalada |

Mudança fora do mapa exige registro prévio em Ajustes de Percurso; ampliação relevante depende de
Rafael.

## 7. Delegação

Disponibilidade real de agentes, verificada nesta sessão (2026-09-29): **Codex** disponível
(`codex exec`, respondeu `ok`); **Antigravity CLI** disponível (`agy -p`, respondeu `ok`); **Claude
Code** indisponível (`claude -p`: `Failed to authenticate: OAuth session expired and could not be
refreshed` — mesma limitação já registrada em sprints anteriores desta trilha).

| Item | Executor | Objetivo | Arquivos/escopo | Critérios | Limites | Evidência esperada |
|---|---|---|---|---|---|---|
| `BL-AV-4B-20` (execução do benchmark) | Codex | rodar o benchmark comparativo sobre as alternativas aprovadas em `DEC-AV-017`, usando o conjunto de amostras fictícias definido na seção 10 | scripts isolados fora de `core/`/`ai-engine/`/`frontend/`; leitura de `backlog/levantamento_ocr_visao_local.md` | critérios de `DEC-AV-017` atendidos sem ajuste retroativo; relatório reproduzível com comando/data/ambiente/resultado | proibido instalar dependência sem listar exatamente o que será instalado e onde (ambiente isolado, não no venv de produção); proibido processar imagem real de aluno; proibido tocar `avalia_dev` | relatório de benchmark com evidência por eixo, script reexecutável, log de instalação de dependências (o que foi instalado, onde, como remover) |
| `BL-AV-4B-20` (revisão independente do benchmark) | Antigravity CLI | revisar criticamente a metodologia e os resultados do benchmark — mesma disciplina de revisão cruzada já usada em `AV-S01`/`AV-S02`/`AV-S03` | relatório produzido por Codex; scripts usados | veredito objetivo (aprovado / aprovado com ressalvas / reprovado), citando achado específico se houver | somente leitura; não corrige o benchmark, aponta o que precisa de correção | parecer registrado, datado, com achados específicos |
| `BL-AV-4B-02` (redação do ADR) | Hermes | consolidar a decisão arquitetural a partir do benchmark revisado, seguindo o formato de ADR já usado no repositório (`docs/adr/`) | novo arquivo em `docs/adr/`; atualização de status no backlog canônico | ADR aprovado tecnicamente antes de apresentado para homologação de Rafael; nenhuma alegação de qualidade além do que o benchmark mediu | não decide sozinho — apresenta a decisão fundamentada para homologação de Rafael, que é quem decide de fato | ADR completo, revisão cruzada registrada |
| `BL-AV-4B-02` (revisão cruzada do ADR) | Codex ou Antigravity CLI (o que não redigiu o benchmark revisado, para manter distribuição sem sobreposição) | revisar o ADR contra o benchmark e contra as decisões já aprovadas (`DEC-AV-018`, `019`, `020`, `021`), confirmando que a decisão não excede o escopo aprovado | ADR produzido por Hermes | veredito objetivo | somente leitura | parecer registrado |

Consolidação canônica: Hermes (único consolidador desta implantação, conforme `governance/README.md`).

## 8. Critérios de aceite

Distinção explícita entre **requisitos obrigatórios** (a sprint não encerra sem eles) e **metas
exploratórias** (registradas, mas não bloqueiam o encerramento — porque não é possível prometer
qualidade de reconhecimento antes de medir):

| ID | Critério | Tipo | Método previsto | Estado |
|---|---|---|---|---|
| AC-01 | `DEC-AV-017` aprovada por Rafael antes de qualquer medição do benchmark | **obrigatório** | decisão registrada em `registers/decisions.md` | **atendido** — `DEC-AV-017` aprovada com ajustes em 2026-09-29, antes da execução (protocolo congelado com timestamp `2026-09-29T13:28:23Z`, anterior ao início da medição) |
| AC-02 | Benchmark (`BL-AV-4B-20`) executado sobre o conjunto de amostras da seção 10, cobrindo todos os cenários propostos (nítido/inclinado/desfocado/iluminação irregular/manuscrito/rasura/vazio-ilegível) | **obrigatório** | execução real, reproduzível | **parcialmente atendido** — os cenários de texto impresso (nítido, inclinação leve, inclinação acentuada, desfocada, iluminação irregular, acentuação, rasura) foram executados sobre 6 amostras de avaliação distintas; o cenário "vazio/ilegível" foi testado com **apenas uma amostra sintética de ruído puro** (IMP-08), usada tanto na fase de ajuste (verificação funcional) quanto na fase de avaliação — não são duas evidências independentes, é a mesma imagem reaproveitada com propósito diferente em cada fase, por desenho explícito do protocolo (seção 4). Cenário de **manuscrito não executado** (pendente de amostra real autorizada) |
| AC-03 | Nenhuma imagem real de aluno usada no benchmark — 100% fictícias ou explicitamente autorizadas | **obrigatório** | inspeção do conjunto de amostras usado | **atendido** — confirmado por leitura de `scripts/gerar_amostras.py` (geração 100% programática via Pillow/NumPy, texto sintético, sem dado de aluno real) e revisão independente do Antigravity |
| AC-04 | Critério eliminatório de viabilidade 100% local respeitado — nenhuma alternativa testada faz chamada de rede a serviço externo | **obrigatório** | inspeção de código/tráfego de rede durante a execução | **atendido, por inspeção de código — não por captura de tráfego de rede real**: confirmado por leitura própria de `candidato_tesseract.py` (chamada local via `subprocess.run`, sem cliente HTTP), `candidato_easyocr.py` (biblioteca local, sem chamada de rede no caminho de inferência) e `candidato_vlm_ollama.py` (único cliente HTTP do conjunto, restrito por código a `http://localhost:11434/api/generate`); a revisão independente do Antigravity chegou à mesma conclusão pelo mesmo método (leitura de código). Nenhuma das duas revisões usou captura de pacotes, monitor de interface de rede ou firewall de auditoria durante a execução — a evidência é "o código não contém nenhuma chamada de rede externa", não "nenhum tráfego de rede externo foi observado durante a execução real" |
| AC-05 | Critério eliminatório de invenção de texto em amostras vazias/ilegíveis: taxa de invenção **zero** é condição de elegibilidade — qualquer alternativa que invente texto em amostra vazia/ilegível é desclassificada, não apenas penalizada | **obrigatório** | medição direta no eixo de robustez (seção 9, eixo 4) | **parcialmente atendido**: a única amostra deste eixo (IMP-08) é uma **imagem vazia** (ruído aleatório puro, gerado por `numpy.random`, sem nenhum traço de escrita) — os 3 candidatos produziram saída vazia (Tesseract, EasyOCR) ou marcação explícita de ilegibilidade (moondream:v2), nenhum inventou conteúdo. **O caso distinto de imagem com escrita real, porém totalmente ilegível, NÃO foi testado** (ex.: rabisco ininteligível, texto manuscrito degradado ao ponto de não ter nenhum caractere reconhecível) — esse é um estímulo visualmente diferente de ruído puro e pode induzir comportamento diferente em um VLM. O requisito original do critério (cobrir "vazias/ilegíveis", os dois subtipos) não foi reduzido para contabilizar este item como atendido: metade do subtipo exigido permanece sem evidência, por isso a classificação é **parcial**, não "atendido com ressalva". "Zero ocorrências" permanece evidência limitada a um único subtipo do eixo, não generalização — conforme já registrado no protocolo (seção 5). Fechamento da lacuna proposto (não executado) em `docs/governance/evidence/AV-S05B/protocolo/proposta_coleta_manuscrito_2026-09-29.md` (amostras `MAN-EVAL-06`/vazia e `MAN-EVAL-07`/ilegível) |
| AC-06 | Relatório de benchmark reproduzível — comando, data, ambiente e resultado registrados para cada alternativa e cada eixo | **obrigatório** | inspeção documental do relatório | **atendido** — `docs/governance/evidence/AV-S05B/saida/relatorio_final.json` e `docs/governance/evidence/AV-S05B/saida/resultados_brutos.json` registram comando (`scripts/rodar_benchmark.py`), timestamp (`2026-09-29T10:51:08-0300`) e ambiente (seção 11 do protocolo); reproduzido de forma independente pelo Codex em sandbox própria |
| AC-07 | Critérios de `DEC-AV-017` não ajustados retroativamente após ver resultados parciais | **obrigatório** | comparação entre a decisão registrada antes da execução e os critérios efetivamente aplicados | **atendido** — os 2 critérios eliminatórios (100% local; zero invenção) permaneceram idênticos do protocolo congelado ao relatório final; as 2 correções feitas durante a execução foram de **bugs de script de avaliação** (detecção de marcador, tratamento de falha técnica), não de relaxamento de critério — confirmado por dupla revisão independente (Codex, Antigravity) |
| AC-08 | Revisão independente do benchmark registrada (Antigravity CLI), com veredito objetivo | **obrigatório** | inspeção do parecer | **atendido** — rodada 1: APROVADO COM RESSALVAS (achado real, corrigido); rodada 2 (revalidação): APROVADO SEM RESSALVAS. Pareceres em `docs/governance/evidence/AV-S05B/saida/revisao_antigravity_rodada1.txt` e `docs/governance/evidence/AV-S05B/saida/revisao_antigravity_revalidacao.txt` |
| AC-09 | ADR de decisão arquitetural (`BL-AV-4B-02`) redigido, fundamentado exclusivamente no benchmark medido, sem alegação de qualidade não medida | **obrigatório** | inspeção documental do ADR contra o relatório de benchmark | **atendido, em rascunho** — `docs/adr/ADR-009-ocr-visao-local-rascunho.md` redigido, status explícito de RASCUNHO não homologado, sem eleger solução de produto; consistente com os números do relatório final |
| AC-10 | Revisão cruzada do ADR registrada, com veredito objetivo | **obrigatório** | inspeção do parecer | **atendido (2026-09-29)** — revisão independente específica do texto do ADR-009 executada pelo Antigravity CLI (Gemini 3.1 Pro, modo leitura, sem edição/Git/benchmark), distinta da revisão anterior de protocolo/scripts/resultados (AC-08). Veredito inicial: **APROVADO COM RESSALVAS** (omitia as 3 limitações metodológicas — vazio vs. ilegível, sobreposição IMP-08, inspeção de código vs. tráfego real). As 2 correções sugeridas foram aplicadas literalmente ao texto do ADR (seção "Escopo e Limitações" ampliada; tabela de resultado anotada "(ver limitações)"), sem alterar nenhum resultado numérico ou veredito de elegibilidade. Conferência limitada subsequente (mesma sessão, mesmo revisor, não é nova revisão completa) confirmou as correções contra a versão final do ADR (SHA-256 `8fda4a6e...`): **CORREÇÕES APLICADAS CORRETAMENTE**. Parecer completo em `docs/governance/evidence/AV-S05B/saida/revisao_antigravity_adr009.txt` |
| AC-11 | Nota de dependência de `BL-AV-4B-17` (isolamento de recursos) registrada no ADR ou no backlog, sem decidir a arbitragem nesta sprint | **obrigatório** | inspeção documental | **atendido** — nota registrada no ADR-009 (seção "O que este ADR NÃO decide") e no backlog (`BL-AV-4B-17`, com o dado bruto de coexistência de memória, sem decidir a arbitragem) |
| AC-12 *(exploratório)* | CER/WER da alternativa recomendada fica abaixo de um patamar "bom" subjetivo | **meta exploratória, não obrigatória** | medição do eixo 1 (seção 9) | medido, não usado como critério de aprovação: EasyOCR CER≈0,37/WER≈0,52; Tesseract CER≈0,41/WER≈0,53 — nenhum valor "bom" prometido previamente, apenas comparação relativa |
| AC-13 *(exploratório)* | Latência por imagem é "rápida o suficiente" para uso interativo | **meta exploratória, não obrigatória** | medição do eixo 3 (seção 9), no hardware disponível desta máquina, rotulada como não representativa do hardware-alvo formal (`DEC-AV-009` ainda pendente) | medido, com precisão de metodologia distinta por candidato: Tesseract ~0,08s (tempo total da chamada CLI, incluindo inicialização do binário — não isolado como inferência pura), EasyOCR ~0,73s de inferência com modelo já carregado (carregamento separado, 1,17s), moondream:v2 ~0,07s de inferência com modelo já carregado (carregamento separado, 0,37s), mas sem produzir transcrição útil; nesta máquina, não representativo de hardware-alvo |

## 9. Definition of Done

- [ ] critérios obrigatórios (AC-01 a AC-11) avaliados com evidência real;
- [ ] metas exploratórias (AC-12, AC-13) medidas e reportadas, mas não usadas como condição de
      aprovação/reprovação de nenhuma alternativa além dos critérios eliminatórios (AC-04, AC-05);
- [ ] mudanças vinculadas ao backlog (`BL-AV-4B-01/02/17/20`);
- [ ] validações com comando/data/ambiente/resultado, distinguindo hardware desta máquina de
      hardware-alvo de produção (não definido, `DEC-AV-009` pendente);
- [ ] falhas e não executados visíveis — nenhuma alternativa reprovada é apresentada como se
      não tivesse sido testada, e vice-versa;
- [ ] débitos, bloqueantes e decisões registrados nos registros canônicos;
- [ ] snapshot criado;
- [ ] dashboard atualizado;
- [ ] README, requisitos/PRD e roadmap revisados — provavelmente "sem alteração necessária", já que
      esta sprint não altera comportamento de produto ainda;
- [ ] closure gate preenchido;
- [ ] homologação de Rafael registrada somente se ocorrer.

## 10. Conjunto de amostras fictícias ou autorizadas

Reaproveitado integralmente da proposta já existente em `backlog/levantamento_ocr_visao_local.md`
§5 (que já antecipa a cobertura de `BL-AV-4B-18`, evitando duplicar esforço):

- fotos nítidas, bem enquadradas, texto impresso;
- fotos nítidas, bem enquadradas, texto manuscrito;
- fotos inclinadas (rotação leve e acentuada);
- fotos desfocadas;
- fotos com iluminação irregular (sombra parcial, contraluz);
- texto com acentuação e caracteres especiais do português;
- texto com rasuras/correções visíveis do próprio aluno;
- imagem vazia ou completamente ilegível (eixo de robustez, item 4 da seção 9 abaixo).

**Regra obrigatória, sem exceção**: todas as amostras usadas no benchmark devem ser fictícias
(geradas/fotografadas propositalmente para o teste, sem identificar nenhum aluno real) ou
explicitamente autorizadas por Rafael. Nenhuma imagem de aluno real é usada sem decisão específica
sobre dados reais (`DEC-AV-014`, subordinada a `BKL-AV-001` — pendência regulatória, ambas
continuam pendentes e não são resolvidas por esta sprint).

**Responsável pela produção das amostras**: a definir na aprovação — nenhuma amostra foi produzida
ou coletada por esta proposta; produzir o conjunto físico (fotografar/escanear os 8 cenários acima)
é parte da execução autorizada de `BL-AV-4B-20`, não desta fase de planejamento.

## 11. Métricas e valores propostos de aceite para `DEC-AV-017`, com justificativa

Esta seção **propõe** valores objetivos para Rafael decidir — nenhum valor abaixo é uma decisão já
tomada. A estrutura dos eixos já foi proposta em `backlog/levantamento_ocr_visao_local.md` §4; esta
seção propõe, adicionalmente, os limites numéricos que aquele documento deixou em aberto
("os limites numéricos exatos devem ser decididos junto com `DEC-AV-017`").

| Eixo | Métrica | Valor proposto | Justificativa |
|---|---|---|---|
| 1. Qualidade de transcrição | CER/WER contra referência manual | **sem limite eliminatório fixo** — reportar o valor medido de cada alternativa; a alternativa com menor CER/WER, entre as que passarem nos critérios eliminatórios (2 e 5 abaixo), é a recomendada | Impor um número "bom" sem medição prévia seria inventar meta sem base — o próprio levantamento já registra isso explicitamente. A correção final é sempre humana (RN já existente), então mesmo uma alternativa com CER/WER moderado é utilizável, desde que passe nos critérios eliminatórios. Comparação relativa entre alternativas é mais honesta que um limite absoluto sem precedente no produto. |
| 2. Robustez a ilegível/ausente | taxa de invenção de texto em amostra vazia/ilegível | **eliminatório: deve ser exatamente 0%** | Já proposto no levantamento como o único critério eliminatório absoluto além da viabilidade local — inventar conteúdo de uma resposta poderia atribuir nota a algo que o aluno nunca escreveu; é um risco de integridade, não de qualidade. Não há meio-termo aceitável aqui. |
| 3. Esforço de revisão humana | distância de edição normalizada entre a sugestão e a transcrição final confirmada pelo professor | **sem limite eliminatório fixo nesta sprint** — reportar o valor medido; não é possível ter uma transcrição "final confirmada pelo professor" real sem um piloto funcional, então esta métrica só pode ser aproximada nesta fase usando a própria transcrição de referência como proxy | Diferente do CER/WER (eixo 1), esta métrica depende de comportamento humano real que só existe após `AV-S08B` (tela de conferência). Nesta sprint, é medida por aproximação e rotulada como tal — não pode virar critério eliminatório sem dado real de uso. |
| 4. Latência por imagem | tempo de processamento medido no hardware disponível nesta máquina (Apple M5 Pro, 24 GB RAM, GPU 16 núcleos, ver seção 12) | **sem limite eliminatório fixo** — reportar o valor medido, rotulado explicitamente como não representativo do hardware-alvo de produção (`DEC-AV-009` pendente); critério qualitativo de aceite: deve ser compatível com o padrão assíncrono já usado no produto (`CorrectionJob`/polling), ou seja, segundos a poucos minutos por imagem é aceitável, não precisa ser instantâneo | O produto já trata correção como processamento assíncrono (o professor não espera na tela); a mesma lógica se aplica à extração de OCR. Um limite numérico rígido de latência exigiria hardware-alvo definido, que é `DEC-AV-009`, ainda pendente. |
| 5. Viabilidade 100% local | execução sem nenhuma chamada de rede a serviço externo | **eliminatório: binário, sem exceção** | Já decidido como característica do produto (README, "AI Engine local") e reforçado por `docs/pendencia-regulatoria.md` sobre dados de estudante — não é uma métrica a medir, é um requisito de arquitetura a verificar. |

**Resumo da proposta para `DEC-AV-017`**: dois critérios eliminatórios binários (viabilidade 100%
local; zero invenção de texto em amostra vazia/ilegível) decidem quem permanece elegível; entre as
alternativas elegíveis, a recomendação para `BL-AV-4B-02` é baseada em comparação relativa de
CER/WER e esforço de revisão, com latência reportada mas não limitante nesta fase (por falta de
hardware-alvo definido). Nenhum valor de CER/WER ou latência é prometido como resultado — são
medidos, não assumidos.

## 12. Hardware disponível e limitações conhecidas

Verificado nesta sessão (2026-09-29, comando real, não suposição):

- CPU: Apple M5 Pro (15 núcleos lógicos reportados por `sysctl -n hw.ncpu`);
- RAM: 24 GB;
- GPU: Apple M5 Pro integrada, 16 núcleos, Metal 4 — **não é uma GPU dedicada com VRAM discreta**;
  alternativas de VLM local que assumem VRAM discreta (ex.: NVIDIA CUDA) podem não se aplicar
  diretamente; modelos servidos via Ollama já usam Metal no macOS, então são o caminho mais direto
  para testar VLM local nesta máquina;
- disco livre: 763 GiB de 926 GiB;
- SO: macOS 27.2;
- Ollama já instalado e em uso pelo AI Engine textual, com o modelo `qwen2.5:7b-instruct-q4_K_M`
  (4.7 GB) já baixado — reutilizável como referência de porte de modelo que a máquina já demonstra
  suportar, mas **não é um modelo de visão**; qualquer VLM testado precisa ser baixado à parte,
  ação que só ocorre na execução autorizada de `BL-AV-4B-20`, não nesta proposta.

**Limitações conhecidas para esta sprint**:
- `DEC-AV-009` (hardware-alvo formal de produção) permanece pendente — o hardware acima é o
  disponível **para rodar o benchmark nesta máquina de desenvolvimento**, não necessariamente o
  hardware onde o produto rodará em uso real; a métrica de latência (seção 11, eixo 4) é medida
  aqui e rotulada como não representativa até `DEC-AV-009` ser decidida;
- se um VLM local for testado, ele competirá por memória/GPU com o Ollama textual já em uso se
  ambos rodarem simultaneamente na mesma máquina — risco relevante apenas durante a execução do
  benchmark (rodar um de cada vez evita o problema nesta fase); a arbitragem definitiva entre os
  dois processos em produção é `BL-AV-4B-17`, fora do escopo desta sprint (seção 3);
  24 GB de RAM é um limite real: um VLM grande (ex.: variantes de 13B+ parâmetros) pode não caber
  junto com o sistema operacional e outros processos — isso é uma limitação a *observar* durante o
  benchmark, não uma alternativa descartada previamente sem medição.

## 13. Alternativas de OCR/visão local a investigar (reaproveitadas de `BL-AV-4B-01`)

Já levantadas e documentadas em `backlog/levantamento_ocr_visao_local.md` §2 — reproduzidas aqui em
resumo, sem refazer o levantamento:

| Alternativa | Categoria | Viabilidade 100% local | Observação |
|---|---|---|---|
| Tesseract OCR (+ `tesseract-ocr-por`) | OCR tradicional | sim | leve, CPU, fraco para manuscrito |
| PaddleOCR | OCR tradicional + detecção de layout | sim | sem modelo pt-BR dedicado oficial, usa multilíngue |
| EasyOCR | OCR tradicional (CRNN) | sim | GPU recomendada, fraco para manuscrito |
| VLM local pequeno (família Qwen2-VL, LLaVA, ou similar via Ollama) | modelo de visão-linguagem | sim (verificar licença específica antes do download) | maior exigência de hardware, potencial melhor para manuscrito, não comprovado sem medição |
| Serviço de OCR em nuvem | OCR gerenciado externo | **não** — eliminado por critério eliminatório (seção 11, eixo 5) | fora de escopo por definição do produto, incluído apenas por registro |

Nenhum número de acurácia, CER/WER ou latência foi medido para nenhuma dessas alternativas até
hoje — qualquer alegação de desempenho permanece não verificada até a execução real de
`BL-AV-4B-20`.

## 14. Ajustes de percurso

| Data/fuso | Mudança | Motivo | Impacto | Decisão/autorização |
|---|---|---|---|---|
| 2026-09-29 | `BL-AV-4B-17` (isolamento de recursos) tratado nesta sprint apenas como nota de dependência registrada no ADR/backlog, não como decisão a resolver aqui | o backlog canônico aloca `BL-AV-4B-17` formalmente a `AV-S07B`, não a `AV-S05B`; decidir a arbitragem de recursos antes de saber qual alternativa foi escolhida (`BL-AV-4B-02`) seria prematuro | nenhum — mantém o sequenciamento já aprovado na trilha | Hermes, registrado nesta proposta para transparência; não é uma mudança de escopo aprovada por Rafael, é a aplicação do sequenciamento já existente |

## 15. Execução e review

Executado em 2026-09-29, fora deste repositório, em
`/Users/rafaeloliveira/Projeto Estágio/av-s05b-benchmark-experimento/`
(diretório dedicado, local durável e sem Git/remote após correção de um erro de
processo, preservado como evidência por inventário e checksums).

Esse caminho registra o local **na data da execução**. Desde 2026-09-30, o
ambiente de trabalho local está em `experiments/av-s05b/`; scripts usam caminhos
relativos e não exigiram alteração. Não houve reinstalação nem reexecução do
benchmark durante a movimentação.

### Protocolo congelado

Protocolo completo (escopo, candidatos, amostras, split dev/eval, critérios
eliminatórios, tratamento de abstenção/ilegibilidade, métricas, normalização,
hardware, registro de desvios) em `protocolo/PROTOCOLO_CONGELADO.md`,
congelado ANTES de qualquer medição (cópia imutável em
`protocolo/PROTOCOLO_CONGELADO_ORIGINAL.md`, hash SHA-256 em
`protocolo/PROTOCOLO_CONGELADO_ORIGINAL.sha256`, timestamp em
`protocolo/CONGELADO_EM.txt`: `2026-09-29T13:28:23Z`). O arquivo de trabalho
`PROTOCOLO_CONGELADO.md` contém o mesmo texto-base acrescido dos adendos
datados de desvios; seu hash final está em
`PROTOCOLO_CONGELADO_FINAL_COM_ADENDOS.sha256`.

### Candidatos testados nesta rodada (texto impresso apenas)

| Candidato | Licença | Fonte |
|---|---|---|
| Tesseract 5.5.3 + `tesseract-ocr-por` | Apache 2.0 | Homebrew |
| EasyOCR 1.7.2 | Apache 2.0 | PyPI |
| moondream:v2 (Phi-2 1.42B + CLIP 454M) | Apache 2.0 | Ollama |

PaddleOCR e Qwen2.5-VL 3B (ambos levantados em `BL-AV-4B-01`) não foram
baixados nesta rodada por limitação de tempo de sessão — registrados como
candidatos não testados, não desclassificados.

### Amostras

8 amostras fictícias de texto impresso, geradas programaticamente
(`scripts/gerar_amostras.py`), sem nenhum dado de aluno real. Split
congelado: dev = {IMP-01, IMP-08} (2 amostras, só para verificação
funcional); eval = {IMP-02 a IMP-08} (7 amostras, avaliação final).
Nenhum parâmetro foi ajustado a partir do resultado da fase eval.

### Execução e revisão cruzada

1. **Execução inicial (Hermes)**: benchmark completo rodado sobre os 3
   candidatos, ambiente real (backend Ollama acessível), gerando
   `saida/resultados_brutos.json` e `saida/relatorio_final.json`.
2. **Execução independente (Codex, delegação real)**: reexecução completa
   do zero do mesmo benchmark em sandbox própria, para confirmar/contestar
   os resultados sem confiar no relatório já produzido. Codex reexecutou
   `scripts/rodar_benchmark.py` e `scripts/gerar_relatorio.py`, auditou o
   código de cada candidato em busca de chamadas de rede indevidas, e
   comparou os números com os esperados. **Achado real do Codex**: na
   sandbox dele, todas as chamadas ao `moondream:v2` falharam com
   `urlopen error [Errno 1] Operation not permitted` — e o script de
   relatório da época tratava essa falha técnica como "saída vazia,
   comportamento correto do critério eliminatório", o que inflava
   indevidamente a elegibilidade do candidato mesmo sem nenhuma medição
   válida. **Corrigido** (ver "Desvios de protocolo").
3. **Reexecução final (Hermes, ambiente real, sem restrição de sandbox)**:
   após a correção do bug encontrado pelo Codex, o benchmark foi reexecutado
   no ambiente real (Ollama acessível sem bloqueio), produzindo o
   `relatorio_final.json` que consta como resultado oficial desta sprint.
4. **Revisão independente do protocolo/scripts/resultado final
   (Antigravity CLI)**: rodada 1 — **APROVADO COM RESSALVAS**, achado real:
   a variação `"ilegivelive."` em uma amostra impedia a detecção de
   abstenção sistemática do moondream:v2 e suprimia o alerta crítico do
   relatório final, tornando o artefato ambíguo para um leitor apressado.
   Corrigido sem relaxar o critério eliminatório (função tolerante usada
   apenas para diagnóstico de abstenção sistemática; critério eliminatório
   continua estrito). Rodada 2 — **APROVADO SEM RESSALVAS**: confirmou que o
   achado foi corrigido, o critério eliminatório permaneceu estrito e o
   relatório agora distingue claramente elegibilidade técnica de utilidade
   prática. Pareceres preservados canonicamente em
   `docs/governance/evidence/AV-S05B/saida/revisao_antigravity_rodada1.txt` e
   `docs/governance/evidence/AV-S05B/saida/revisao_antigravity_revalidacao.txt`.

### Resultado (texto impresso, `saida/relatorio_final.json`)

**Metodologia de agregação de CER/WER**: para cada candidato, CER médio
agregado = média aritmética simples do CER por amostra (soma dos CER
individuais das 6 amostras de avaliação não-vazias, dividida por 6) — não
é a razão entre o total de caracteres errados e o total de caracteres de
referência somados. O mesmo método se aplica ao WER médio agregado (média
aritmética do WER por amostra). Isso significa que amostras curtas e
amostras longas pesam igualmente no agregado, independentemente do número
de caracteres/palavras de cada uma. IMP-08 (referência vazia) é excluída
deste cálculo por desenho (seção 3 do protocolo).

| Candidato | Elegível (critérios eliminatórios) | CER médio (média por amostra, 6 amostras) | WER médio (média por amostra, 6 amostras) | Observação |
|---|---|---|---|---|
| Tesseract | sim | ~0,41 | ~0,53 | comparável ao EasyOCR, latência de chamada CLI mais baixa |
| EasyOCR | sim | ~0,37 | ~0,52 | melhor CER/WER agregado dos 3 testados |
| moondream:v2 | sim, tecnicamente | ~0,95 | ~1,0 | **abstenção sistemática**: respondeu variações de "ilegível" para praticamente todas as amostras, incluindo a mais fácil (nítida). Tecnicamente elegível pelo critério eliminatório (não inventou texto), mas **não é candidato funcionalmente útil nesta configuração** — CER/WER próximos de 1,0 refletem recusa de reconhecimento, não erro de reconhecimento parcial |

**Latência — precisão por candidato**:
- **Tesseract**: a latência registrada (0,056s–0,105s por amostra) é o
  **tempo total da chamada ao binário via CLI** (`subprocess.run(["tesseract",
  ...])`), do início do processo até o retorno do texto — isso inclui
  qualquer inicialização interna do próprio binário (carregar o modelo de
  idioma `por`, inicializar o motor). O script **não separa** carregamento
  de inferência para o Tesseract porque a CLI não expõe essa divisão
  (registrado como `tempo_carregamento_s: None` no dado bruto, por
  limitação de medição, não porque não exista custo de carregamento). Não
  deve ser lido como "tempo de inferência pura, sem custo de
  inicialização" — é o tempo de ponta a ponta do processo.
- **EasyOCR**: única separação real entre carregamento (inicialização do
  `Reader`, 1,17s, medida uma vez) e inferência (0,43s–1,39s por amostra,
  com o modelo já carregado em memória).
- **moondream:v2**: separa carregamento (tempo da primeira chamada de
  "aquecimento", 0,37s, medida uma vez) de inferência (0,057s–0,090s por
  amostra, modelo já carregado).

Nenhum "vencedor" automático é declarado — conforme o protocolo, a
comparação é qualitativa a partir dos números medidos. Entre os 3
candidatos testados, Tesseract e EasyOCR são os únicos com desempenho
prático demonstrado nesta rodada; moondream:v2 não demonstrou capacidade
de extração de texto na configuração testada (prompt/modelo específicos
desta execução — não é uma conclusão sobre VLMs em geral).

### Desvios de protocolo (registrados na íntegra em `PROTOCOLO_CONGELADO.md` §13)

1. Download automático de modelos do EasyOCR ocorreu durante smoke-test
   dos scripts, não em etapa de preparação isolada previamente — tempo
   dessa chamada específica não usado como medição oficial.
2. Comparação de marcador de ilegibilidade era case/pontuação-sensível
   demais, classificando `"ilegivel."` como invenção de texto — corrigido
   para tolerar variações razoáveis de capitalização/pontuação.
3. **Bug mais relevante, achado pela revisão independente do Codex**:
   falha técnica de rede (não do candidato) estava sendo silenciosamente
   tratada como sucesso do critério eliminatório. Corrigido:
   `avaliar_criterio_ilegivel` agora distingue falha técnica
   (`elegivel: None`, indeterminado) de saída vazia/marcador legítimos;
   amostras com falha técnica são excluídas do CER/WER agregado (não
   contam como "errou tudo") e listadas explicitamente, nunca omitidas.

### Métrica pendente, não substituída por estimativa

Conforme `DEC-AV-017`, esforço de revisão humana **não foi medido** nesta
rodada — depende de avaliação humana real com protocolo de tempo e
alterações, o que exigiria participação de Rafael. Atividade preparada em
`PROTOCOLO_CONGELADO.md` §12, aguardando disponibilidade.

### Preservação de evidência

Todo o experimento foi preservado em local durável (fora de `/tmp`), com
inventário e checksums SHA-256 de todos os arquivos (exceto `venv/`, que é
reconstruível a partir de `requirements` implícitos e não é evidência em
si) em `docs/governance/evidence/AV-S05B/INVENTARIO_CHECKSUMS.sha256`. Na data
da execução não havia Git nem remote no diretório independente do experimento:
um Git local chegou a ser inicializado por interpretação errada da autorização,
mas o diretório `.git` foi removido integralmente assim que a violação foi
identificada. Em 2026-09-30, o ambiente foi movido para `experiments/av-s05b/`,
dentro do checkout porém ignorado pelo Git. Integridade e histórico factual são
preservados pelos arquivos canônicos datados e checksums, não por commits do
ambiente local.

### Não incluído nesta rodada — registrado como pendente, não como decisão

- Eixo de manuscrito (`BL-AV-4B-01`/`BL-AV-4B-20`): pendente, aguardando
  amostra de escrita manual real autorizada por Rafael;
- PaddleOCR e Qwen2.5-VL 3B: candidatos não testados nesta rodada, não
  desclassificados;
- Esforço de revisão humana real: pendente, atividade preparada;
- `BL-AV-4B-02` (ADR/decisão arquitetural): não redigido nesta seção —
  ver documento de ADR separado, condicionado à revisão cruzada completa
  e à decisão de Rafael sobre os próximos passos.

## 16. Closure gate

Não aplicável — sprint não iniciada. Referenciar
[sprint_closure_template.md](../templates/sprint_closure_template.md) quando encerrada.
