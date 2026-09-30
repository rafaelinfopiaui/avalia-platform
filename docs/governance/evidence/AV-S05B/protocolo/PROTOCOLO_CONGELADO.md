# Protocolo congelado — Benchmark de OCR/visão local (AV-S05B)

**CONGELADO EM: 2026-09-29, ANTES de qualquer medição.** Este arquivo não pode
ser alterado após o início da execução do benchmark, exceto por adendo datado
que preserve o texto original (mesma regra de `documentation_policy.md` §4
para snapshots). Qualquer desvio do que está aqui, descoberto durante a
execução, é registrado como desvio de protocolo, não como correção retroativa
silenciosa.

Base: `DEC-AV-017` (aprovada com ajustes, 2026-09-29) e
`docs/governance/backlog/levantamento_ocr_visao_local.md`.

## 1. Escopo desta execução

**Eixo de manuscrito: PENDENTE nesta rodada.** Rafael determinou que o
eixo de manuscrito exige escrita manual real autorizada — fonte tipográfica
"cursiva" não é substituto aceitável e não será usada para simular
manuscrito. Nenhuma amostra de manuscrito é incluída nesta execução. Este
protocolo cobre exclusivamente **texto impresso** (fontes tipográficas
reais, geradas para o teste). O eixo de manuscrito fica registrado como
não avaliado, não como "reprovado" ou "não suportado" — apenas sem
evidência nesta rodada.

## 2. Candidatos avaliados

Licenças verificadas nesta data (2026-09-29, busca real, não presumida):

| Candidato | Categoria | Licença | Fonte de instalação | Tamanho aproximado |
|---|---|---|---|---|
| Tesseract OCR + `tesseract-ocr-por` | OCR tradicional | Apache 2.0 | Homebrew (`brew install tesseract tesseract-lang`) | ~50 MB |
| EasyOCR | OCR tradicional (deep learning, CRNN) | Apache 2.0 | PyPI (`pip install easyocr`), modelos baixados na primeira execução | ~100 MB (modelos pt+en) |
| Moondream2 (`moondream:v2`) | VLM local pequeno | Apache 2.0 | Ollama (`ollama pull moondream:v2`) | 1,7 GB |
| Qwen2.5-VL 3B (`qwen2.5vl:3b`) | VLM local | Apache 2.0 | Ollama (`ollama pull qwen2.5vl:3b`) | 3,2 GB |

PaddleOCR (levantado em `BL-AV-4B-01`) fica **fora desta execução** por
limitação de tempo/recursos da sessão — registrado como candidato não
testado nesta rodada, não como candidato reprovado, disponível para
investigação futura.

Todos os 4 candidatos acima: **100% locais, sem chamada de rede durante a
inferência** (critério eliminatório, seção 5). Download de pesos/binários é
etapa de preparação, distinta de inferência — ver seção 8.

## 3. Conjunto de amostras — texto impresso

8 amostras fictícias, geradas programaticamente para este teste (texto
sintético em português, sem nenhum dado de aluno real):

| ID | Categoria | Descrição |
|---|---|---|
| IMP-01 | nítida, bem enquadrada | imagem limpa, fonte legível, sem distorção |
| IMP-02 | inclinação leve | rotação de ~5° |
| IMP-03 | inclinação acentuada | rotação de ~20° |
| IMP-04 | desfocada | blur gaussiano aplicado |
| IMP-05 | iluminação irregular | gradiente de sombra parcial sobreposto |
| IMP-06 | acentuação/caracteres especiais pt-BR | texto com ç, ã, é, ô, ü etc. |
| IMP-07 | rasura/correção visível | marca de rasura sintética sobre parte do texto |
| IMP-08 | vazia/ilegível | imagem em branco ou ruído puro, sem texto legível |

**Transcrição de referência**: cada amostra (exceto IMP-08) tem uma
transcrição de referência exata, produzida ANTES de qualquer execução dos
candidatos, gravada em texto simples, imutável durante o benchmark.
IMP-08 tem referência vazia (string vazia), usada exclusivamente para o
critério eliminatório de invenção de texto (seção 5).

## 4. Split: amostras de ajuste vs. amostras de avaliação final

Regra exigida por Rafael: nenhuma amostra usada para ajustar configuração
(prompt do VLM, parâmetros do OCR tradicional) pode ser reaproveitada na
avaliação final.

- **Conjunto de ajuste (dev)**: IMP-01 e IMP-08 (2 amostras). Usadas
  exclusivamente para verificar que cada candidato está minimamente
  funcional (roda sem erro, produz alguma saída) e para calibrar parâmetros
  básicos de invocação (ex.: linguagem do Tesseract, prompt do VLM). Nenhum
  ajuste feito a partir da qualidade do texto de saída em relação à
  referência — apenas "o comando roda e retorna algo".
- **Conjunto de avaliação final (eval)**: IMP-02 a IMP-07 (6 amostras) +
  IMP-08 reavaliada no conjunto eval para o critério eliminatório
  (IMP-08 aparece em ambos os splits porque seu uso no dev é apenas
  "verificar que roda", não "medir qualidade de reconhecimento vazio" —
  a medição do critério eliminatório de invenção de texto ocorre
  exclusivamente na fase de avaliação final, tratando a execução do dev
  como não contabilizada para essa métrica).
- Nenhum parâmetro é reajustado após a fase de ajuste. A configuração
  usada na avaliação final é congelada antes de rodar IMP-02 a IMP-07.

## 5. Critérios eliminatórios (binários, sem exceção)

1. **100% local**: nenhuma chamada de rede durante a inferência. Verificado
   por inspeção do comando/código de cada candidato (nenhum candidato desta
   lista faz chamada de rede por desenho) e, adicionalmente, pela ausência
   de qualquer credencial de API externa configurada no ambiente de
   execução.
2. **Zero invenção de texto em amostra vazia/ilegível**: para IMP-08
   (referência vazia), qualquer candidato que produza texto não-vazio como
   saída é **desclassificado**. Produzir uma marcação explícita de "sem
   texto detectável" ou saída vazia é o comportamento correto.

**Nota explícita exigida por Rafael**: "zero ocorrências no conjunto
avaliado" (uma única amostra vazia, IMP-08) não constitui garantia
universal de que o candidato nunca inventa texto — é evidência limitada a
esta amostra específica, neste experimento, não uma generalização de
robustez. Isso será reafirmado no relatório final e no ADR.

## 6. Tratamento de casos parcialmente legíveis, abstenções e marcações de ilegibilidade

Definido previamente, antes de qualquer medição:

- **Parcialmente legível** (nenhuma amostra deste conjunto de 8 é
  parcialmente legível por desenho — IMP-04/05/07 são degradadas mas
  o texto de referência é integralmente legível por um humano; nenhuma
  amostra desta rodada testa "meio da imagem ilegível, meio legível").
  Registrado aqui como definição para uso em rodadas futuras, caso
  amostras parcialmente legíveis sejam adicionadas: a métrica de CER/WER
  é calculada apenas sobre a porção que a referência humana considera
  legível; a porção ilegível é excluída do denominador de caracteres,
  não contada como erro nem como acerto.
- **Abstenção** (candidato se recusa a transcrever ou retorna
  explicitamente "não sei"/"ilegível"): tratada como saída válida, não
  como falha de execução. Contabilizada separadamente na métrica de
  esforço de revisão (o professor precisaria transcrever manualmente,
  esforço = 100% da amostra) e não conta como "invenção de texto" desde
  que a abstenção não inclua texto inventado junto.
- **Marcação de ilegibilidade explícita pelo candidato**: tratada como
  acerto para o critério eliminatório de IMP-08, e registrada como tal no
  relatório (diferente de simplesmente não produzir saída por erro de
  execução, que é uma falha técnica, registrada separadamente).
- **Falha técnica de execução** (erro, crash, timeout): registrada
  explicitamente no relatório por amostra e por candidato — **nunca**
  excluída silenciosamente da contagem. Uma falha técnica em uma amostra
  não remove essa amostra do denominador do candidato; é contada como
  "não avaliável nesta amostra", visível no relatório.

## 7. Métricas medidas e regra de comparação

Conforme `DEC-AV-017`:

1. **CER/WER** (exploratório, comparativo) — calculado contra a
   transcrição de referência, usando distância de edição normalizada por
   caracteres (CER) e por palavras (WER), com normalização definida na
   seção 9. Reportado por amostra, por categoria e agregado. Nenhum valor
   limite é usado para aprovar/reprovar — apenas comparação relativa entre
   candidatos elegíveis.
2. **Esforço de revisão humana** — **PENDENTE nesta rodada**, conforme
   `DEC-AV-017`: só pode ser apresentado como medido se houver avaliação
   humana real, com protocolo de tempo e alterações registradas. Esta
   execução não inclui avaliação humana real (dependeria da participação
   de Rafael). Esta métrica permanece **não medida**, não substituída por
   estimativa de agente algum. Ver seção 12 para a atividade preparada.
3. **Latência** (exploratório, comparativo) — medida separando
   explicitamente (a) tempo de carregamento inicial do modelo/motor
   (carregar pesos, inicializar) de (b) tempo de inferência com o
   modelo já carregado em memória, por amostra. Medido no hardware
   desta máquina (Apple M5 Pro, 24 GB RAM — ver seção 11), rotulado
   como não representativo de hardware-alvo de produção (`DEC-AV-009`
   pendente).
4. **Robustez a ilegível/ausente** — critério eliminatório, seção 5.
5. **Viabilidade 100% local** — critério eliminatório, seção 5.

**Regra de comparação**: candidatos que falham em qualquer critério
eliminatório (seção 5) são desclassificados e não entram na comparação de
CER/WER/latência — são reportados como desclassificados, com o motivo
específico, não omitidos do relatório. Entre os candidatos elegíveis, o
relatório apresenta os valores medidos lado a lado, sem calcular um
"vencedor" automático — a recomendação para o ADR é qualitativa, baseada
nos números apresentados, não em uma fórmula de pontuação oculta.

**Nenhum critério deste protocolo pode ser ajustado após ver resultado
parcial de qualquer candidato.**

## 8. Distinção entre preparação (download) e inferência offline

Etapa de preparação (antes de medir latência/qualquer métrica): baixar
Tesseract, `tesseract-ocr-por`, EasyOCR e seus modelos, `moondream:v2`,
`qwen2.5vl:3b` via `ollama pull`. Esta etapa é feita uma vez, com rede,
registrada separadamente (o quê foi baixado, de onde, tamanho, hash
quando disponível) e **não conta como parte de nenhuma métrica de
latência de inferência**.

Etapa de inferência (medição real): a partir do momento em que a etapa de
preparação termina, toda a execução do benchmark ocorre sem rede — nenhuma
chamada de rede, nenhum acesso à internet durante o processamento de
nenhuma amostra. Verificável observando que os comandos de inferência não
fazem requisição HTTP/DNS após os pesos estarem em disco/carregados.

## 9. Normalização de texto para CER/WER

Definida previamente:

- normalização Unicode NFC;
- espaços múltiplos colapsados em um único espaço;
- espaços de início/fim removidos (trim);
- **preserva** maiúsculas/minúsculas e pontuação (não normaliza — erro de
  capitalização/pontuação conta como erro real, porque no produto a
  transcrição confirmada pelo professor precisa refletir a resposta real
  do aluno, não uma versão normalizada);
- caracteres acentuados do português (ç, ã, é, ô, ü etc.) tratados como
  caracteres distintos de suas formas sem acento — erro de acentuação
  conta como erro de caractere (relevante para pt-BR, item IMP-06).

## 10. Versões e configuração (a preencher no momento da execução, antes de medir)

Campos obrigatórios a registrar no relatório final para cada candidato,
travados antes da avaliação final (não alteráveis depois):

- versão exata do binário/pacote/modelo (ex.: `tesseract --version`,
  `pip show easyocr`, `ollama list` com hash do modelo);
- parâmetros de invocação completos (idioma, prompt exato para VLMs,
  qualquer flag não-padrão);
- hardware/ambiente de execução (confirmação de que é a máquina descrita
  na seção 11, sem GPU externa, sem aceleração de nuvem).

## 11. Hardware desta execução

Apple M5 Pro, 24 GB RAM, GPU integrada 16 núcleos (Metal 4, sem VRAM
discreta), macOS 27.2. Confirmado por `sysctl`/`system_profiler` em
2026-09-29 (mesmos dados já registrados na proposta de sprint). Latência
medida aqui não representa hardware-alvo de produção (`DEC-AV-009`
pendente).

## 12. Atividade preparada para medição futura de esforço de revisão humana

Não executada nesta rodada. Proposta de protocolo para quando Rafael (ou
outro revisor humano designado) estiver disponível:

1. Selecionar as transcrições produzidas pelos candidatos elegíveis (que
   passaram nos critérios eliminatórios) sobre o conjunto de avaliação
   final;
2. apresentar ao revisor humano, uma de cada vez, a imagem original e a
   transcrição sugerida (sem revelar qual candidato produziu qual);
3. cronometrar o tempo até o revisor confirmar ou corrigir a transcrição;
4. registrar o texto final confirmado e a distância de edição entre a
   sugestão e o texto confirmado;
5. repetir para todas as combinações candidato×amostra relevantes.

Esta atividade fica pendente, aguardando disponibilidade do revisor
humano — não é substituída por estimativa de agente.

## 13. Registro de desvio de protocolo

Se, durante a execução, qualquer passo divergir deste protocolo congelado
(ex.: candidato indisponível, erro técnico não previsto, necessidade de
ajuste de parâmetro), o desvio é registrado nesta seção com data, motivo e
decisão tomada — nunca como alteração silenciosa da seção correspondente
acima.

| Data/hora | Desvio | Motivo | Decisão |
|---|---|---|---|
| 2026-09-29 ~13:33 UTC | Download de modelos do EasyOCR ocorreu durante smoke-test dos scripts (amostra de dev), não em etapa de preparação isolada previamente | EasyOCR baixa modelos automaticamente na primeira inicialização do `Reader`, sem "pull" separado | detalhado em `PREPARACAO_DOWNLOADS.md`; tempo desta chamada não usado como medição oficial; nenhuma amostra eval processada durante o desvio |
| 2026-09-29 ~13:40 UTC | Script de avaliação do critério eliminatório (invenção de texto em IMP-08) comparava a resposta do candidato de forma exata (`!= "ILEGIVEL"`), sem tolerar pontuação/capitalização. `moondream:v2` respondeu `"ilegivel."` (minúsculo, com ponto final) para IMP-08 em ambas as fases (dev e eval), e o script marcou isso incorretamente como invenção de texto | bug de avaliação, não do candidato — protocolo seção 6 trata "marcação de ilegibilidade explícita" como acerto, e `"ilegivel."` é claramente essa marcação, não texto inventado sobre o conteúdo da imagem | corrigida a função de comparação para normalizar pontuação final e capitalização antes de comparar com o marcador esperado; reavaliação feita sobre o texto bruto já gravado (não repetida a chamada de inferência, que é imutável); resultado corrigido documentado no relatório final |
| 2026-09-29 ~13:52 UTC | Execução independente delegada ao Codex (reexecução do benchmark completo em sua própria sandbox) revelou bug mais grave: todas as chamadas ao `moondream:v2` falharam na sandbox do Codex com `urlopen error [Errno 1] Operation not permitted` (a sandbox `workspace-write` do Codex bloqueia até conexões `localhost`), e `scripts/gerar_relatorio.py` tratava essas falhas técnicas como `texto=""`, classificando-as como "saída vazia — comportamento correto" do critério eliminatório — ou seja, uma falha de rede seria erroneamente contabilizada como sucesso do candidato | protocolo seção 6 exige que falha técnica de execução seja "registrada explicitamente... nunca excluída silenciosamente da contagem"; o script anterior não distinguia falha técnica de saída vazia legítima | `avaliar_criterio_ilegivel` reescrita para receber o campo `erro` e retornar `inventou_texto: None` (indeterminado, não aprovado) quando há falha técnica; `elegivel` passa a ser `None` (não `True`) quando o critério eliminatório não pôde ser medido; amostras com falha técnica são excluídas do CER/WER agregado (não contam como "errou tudo") e listadas explicitamente em `amostras_com_falha_tecnica_eval`; benchmark reexecutado no ambiente real (fora da sandbox do Codex, com Ollama acessível), produzindo o relatório final válido: `moondream:v2` respondeu de fato (sem falha técnica), permitindo avaliação completa — ver seção de resultados |
| 2026-09-29 ~14:10 UTC | Revisão independente Antigravity CLI detectou que o diagnóstico auxiliar de "abstenção sistemática" exigia marcador exato de ilegibilidade; a saída `"ilegivelive."` do moondream:v2 em IMP-05 quebrava o `all(...)`, resultando em `abstencao_sistematica=false` e suprimindo `observacao_critica` no relatório, mesmo com 8/9 saídas `"ilegivel."` e CER/WER ~1,0 | função diagnóstica estrita demais para reconhecer variação curta/alucinada do mesmo marcador; critério eliminatório estrito estava correto, mas o campo de diagnóstico podia induzir leitor apressado a erro sobre utilidade prática | criada `eh_variacao_de_abstencao()` exclusivamente para diagnóstico (aceita marcador exato ou radical `ILEGIVEL` + até 6 caracteres de ruído curto); critério eliminatório continua usando `eh_marcacao_ilegivel()` estrita, sem relaxamento; relatório regenerado com `abstencao_sistematica=true` e `observacao_critica` explícita; Antigravity revalidou: **APROVADO SEM RESSALVAS** |
| 2026-09-29 ~14:30 UTC | Hermes inicializou um repositório Git local no diretório experimental e criou 3 commits locais, interpretando incorretamente que a proibição de ações Git/remotas da autorização se aplicava apenas ao repositório AvalIA | violação de processo: Rafael havia confirmado literalmente "apenas arquivos locais, sem commit/push nenhum artefato desta sprint nesta rodada"; mesmo sem remote/push e fora do repo AvalIA, commits locais ainda são ações Git | diretório `.git` do experimento removido integralmente; todos os arquivos/evidências preservados; integridade passa a ser garantida exclusivamente por `INVENTARIO_CHECKSUMS.sha256` (43/43 verificados), sem qualquer histórico Git local ou remoto |
