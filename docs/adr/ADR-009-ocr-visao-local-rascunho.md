# ADR-009 — OCR/visão local para entrada por imagem (Etapa 4B): candidatos investigados, nenhuma solução aprovada para uso

Status: **RASCUNHO — revisão cruzada completa (protocolo/scripts/resultados
e texto do ADR) concluída em 2026-09-29, com conferência limitada
subsequente confirmando as correções aplicadas; aguardando homologação de
Rafael. NÃO é decisão de produto aprovada.**
Responsável: Hermes (consolidação), Codex (execução independente do
benchmark), Antigravity CLI (revisão de protocolo/scripts/resultado e
revisão independente do texto do ADR)
Data: 2026-09-29

## Contexto

`BL-AV-4B-02` (decisão arquitetural do motor/modelo de OCR/visão local)
depende de `BL-AV-4B-20` (benchmark comparativo) medido sob critérios
previamente aprovados (`DEC-AV-017`). Este ADR registra o resultado da
primeira rodada experimental do benchmark, autorizada por Rafael em
2026-09-29 como investigação exploratória, fora do repositório de produção.

Protocolo completo, congelado antes de qualquer medição:
`docs/governance/evidence/AV-S05B/protocolo/PROTOCOLO_CONGELADO.md`.
Resultado bruto e relatório final:
`docs/governance/evidence/AV-S05B/saida/`. O ambiente de trabalho local
foi consolidado em `experiments/av-s05b/` em 2026-09-30 e permanece
ignorado pelo Git; a evidência canônica é a cópia versionada acima.

## Escopo e Limitações desta rodada

Exclusivamente **texto impresso**, 8 amostras fictícias sintéticas. O eixo
de **manuscrito permanece não avaliado** — exige escrita manual real
autorizada por Rafael, que ainda não foi fornecida. Nenhuma conclusão deste
ADR se estende a manuscrito.

**Limitações metodológicas conhecidas (identificadas em revisão documental
2026-09-29, confirmadas por revisão independente do Antigravity):**
- **Robustez (vazio vs. ilegível)**: o critério eliminatório de invenção de
  texto (IMP-08) foi testado com apenas uma amostra de **ruído aleatório
  puro** (imagem vazia). O comportamento dos candidatos diante de **texto
  real, porém totalmente ilegível** (ex.: rabisco/manuscrito degradado sem
  nenhum caractere reconhecível) permanece **não testado** — são estímulos
  visuais distintos, e não se pode presumir o mesmo comportamento.
- **Sobreposição de amostra (IMP-08)**: a mesma imagem vazia foi usada na
  fase de ajuste (dev, apenas para verificar que o candidato roda) e na
  fase de avaliação final (eval, para medir o critério eliminatório). Não
  constitui duas evidências independentes — é uma única amostra reaplicada
  com propósito distinto em cada fase.
- **Verificação de execução 100% local**: o cumprimento do critério "sem
  chamada de rede" foi validado por **inspeção de código** dos scripts
  candidato (`candidato_tesseract.py`, `candidato_easyocr.py`,
  `candidato_vlm_ollama.py`) — confirmando que nenhum caminho de código faz
  chamada de rede externa (o único cliente HTTP existente é restrito, por
  código, a `http://localhost:11434`). Isso **não equivale** a uma captura
  de tráfego de rede real durante a execução; não houve monitoramento de
  interface de rede nem auditoria de firewall no momento da inferência.

## Candidatos testados

Tesseract 5.5.3 + `tesseract-ocr-por` (Apache 2.0), EasyOCR 1.7.2 (Apache
2.0), moondream:v2 via Ollama (Apache 2.0). PaddleOCR e Qwen2.5-VL 3B foram
levantados mas não testados nesta rodada — candidatos não descartados, sem
evidência ainda.

## Resultado observado (texto impresso apenas)

| Candidato | Critérios eliminatórios | CER médio | WER médio |
|---|---|---|---|
| Tesseract | atendidos (ver limitações acima) | ~0,41 | ~0,53 |
| EasyOCR | atendidos (ver limitações acima) | ~0,37 | ~0,52 |
| moondream:v2 | atendidos tecnicamente (ver limitações acima; não inventou texto), mas **abstenção sistemática** — respondeu "ilegível" para quase todas as amostras, inclusive a mais fácil | ~0,95 | ~1,0 |

## Decisão desta rodada

**Nenhuma alternativa é aprovada como solução para uso em produto nesta
decisão.** Este ADR registra apenas:

1. Tesseract e EasyOCR são **candidatos para próximo experimento** — ambos
   atenderam aos critérios eliminatórios e produziram reconhecimento
   funcional real sobre texto impresso, com EasyOCR levemente à frente em
   CER/WER agregado nesta amostra pequena (7 amostras de avaliação — não é
   base estatística suficiente para eleger um vencedor definitivo).
2. moondream:v2, na configuração testada (prompt e modelo específicos desta
   execução), **não demonstrou utilidade prática** — abstenção sistemática
   não é falha de reconhecimento parcial, é ausência de reconhecimento.
   Isso não é conclusão sobre VLMs locais em geral, apenas sobre esta
   configuração específica testada.
3. Nenhum candidato foi testado contra manuscrito — condição necessária
   para qualquer decisão de produto sobre Etapa 4B, já que a Etapa 4B
   existe justamente para viabilizar respostas manuscritas de alunos.
4. O esforço de revisão humana (métrica de produto relevante) não foi
   medido — depende de avaliação humana real.

## O que este ADR NÃO decide

- Não elege Tesseract nem EasyOCR como solução de produto para `BL-AV-4B-02`.
- Não estabelece nenhuma expectativa de qualidade de reconhecimento em
  produção — os números acima são específicos deste experimento pequeno,
  neste hardware, com este conjunto de amostras, sem manuscrito.
- Não decide a arbitragem de recursos entre OCR e o AI Engine textual
  (`BL-AV-4B-17`) — nota registrada para quando essa decisão for necessária,
  fora do escopo desta rodada.
- Não autoriza nenhuma implementação em `core/`, `ai-engine/` ou `frontend/`.

## Próximos passos (propostos, não decididos por este ADR)

1. Rafael decidir se aprova a continuidade do experimento (rodada de
   manuscrito, com amostra de escrita manual real autorizada; ou candidatos
   adicionais como PaddleOCR/Qwen2.5-VL 3B).
2. Se aprovado, repetir o mesmo protocolo (ou uma versão estendida,
   igualmente congelada antes de medir) cobrindo manuscrito.
3. Só depois de manuscrito avaliado, `BL-AV-4B-02` (decisão arquitetural
   definitiva) pode ser proposto com evidência completa.

## Revisão cruzada

- Execução independente (Codex): reexecução completa do benchmark em
  sandbox própria; encontrou e reportou bug real de tratamento de falha
  técnica no script de avaliação (falha de localhost bloqueado pela sandbox
  era tratada como saída vazia legítima). Bug corrigido antes deste ADR;
  reexecução final no ambiente real confirmou os números oficiais.
- Revisão de protocolo/scripts/resultado (Antigravity CLI, rodada 1):
  **APROVADO COM RESSALVAS** — encontrou um segundo bug real de clareza do
  pós-processamento: a variação `"ilegivelive."` em uma amostra impedia a
  detecção de abstenção sistemática do moondream:v2 e suprimia o alerta
  crítico do relatório final. Corrigido com uma função de diagnóstico
  tolerante a variação curta do marcador, sem relaxar o critério eliminatório
  (que permanece estrito).
- Revalidação independente (Antigravity CLI, rodada 2): **APROVADO SEM
  RESSALVAS** — confirmou que o achado anterior foi corrigido, o critério
  eliminatório permaneceu estrito e o relatório final agora deixa clara a
  inutilidade prática do moondream:v2 nesta configuração, sem confundir isso
  com sua elegibilidade técnica binária.
- Pareceres preservados em
  `docs/governance/evidence/AV-S05B/saida/revisao_antigravity_rodada1.txt` e
  `docs/governance/evidence/AV-S05B/saida/revisao_antigravity_revalidacao.txt`;
  execução independente do Codex em
  `docs/governance/evidence/AV-S05B/saida/execucao_independente_codex.txt`.

## Nota de correção pós-ADR (2026-09-29, verificação independente posterior)

Três lacunas foram identificadas em verificação de comando real feita
depois da revalidação acima, e corrigidas na mesma rodada:

1. **Consumo de memória e coexistência com o modelo textual** (exigido
   pela condição 2 da autorização de Rafael, item `BL-AV-4B-17`): medido
   agora — `moondream:v2` (1,1 GB) e `qwen2.5:7b-instruct-q4_K_M` (4,6 GB,
   modelo textual já existente no ambiente, usado pelo AI Engine do
   repositório, sem registro de implantação formal em produção verificado
   nesta sprint) **coexistem carregados simultaneamente
   sem eviction automática** nesta máquina (24 GB RAM unificada), total
   ~5,7 GB. Detalhe completo em
   `docs/governance/evidence/AV-S05B/saida/medicao_memoria_coexistencia.md`.
   Isso não decide `BL-AV-4B-17`
   (permanece alocado a `AV-S07B`), apenas registra o dado bruto pedido.
2. **Limpeza pós-experimento incompleta**: `docs/governance/evidence/AV-S05B/protocolo/PREPARACAO_DOWNLOADS.md`
   descrevia a remoção de Tesseract e `moondream:v2` da máquina, mas as
   reinstalações feitas para as rodadas de reexecução do Codex e
   revalidação não haviam sido desfeitas. Confirmado por comando
   (`which tesseract`, `ollama list`) e corrigido nesta rodada — ambos
   removidos de fato, com verificação após a remoção.
3. **Backlog canônico desatualizado**: `BL-AV-4B-01` e `BL-AV-4B-20`
   continuavam com status `proposto` em `backlog_tecnico_avalia.md` apesar
   da execução parcial já registrada neste ADR. Atualizado para refletir o
   estado real (levantamento concluído; benchmark parcialmente executado,
   manuscrito pendente).

Nenhuma dessas correções altera o veredito técnico já registrado acima
(Tesseract/EasyOCR candidatos, moondream:v2 sem utilidade prática nesta
configuração, nenhuma solução aprovada para uso).
