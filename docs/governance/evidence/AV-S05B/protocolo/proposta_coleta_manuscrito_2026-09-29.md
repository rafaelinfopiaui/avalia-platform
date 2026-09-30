# Instrução para coleta de amostras manuscritas — próxima rodada AV-S05B (eixo manuscrito)

Status: **coleta autorizada por Rafael (2026-09-29); pré-registro congelado
ANTES de qualquer fotografia.** Nenhuma foto foi tirada ainda — Rafael
prepara as fotos separadamente. Este documento fixa, antes da existência de
qualquer imagem, as decisões abaixo, para que não possam ser ajustadas
depois de ver o resultado de nenhum candidato (mesma regra do protocolo
tipográfico já congelado).

## 0. Pré-registro congelado (2026-09-29, antes de qualquer foto)

1. **Split dev/eval, fixado agora**:
   - **Desenvolvimento (dev)**: `MAN-01` — usada exclusivamente para
     verificar que cada candidato roda sobre uma imagem manuscrita (não
     para calibrar qualidade).
   - **Avaliação final (eval), exclusiva**: `MAN-02`, `MAN-03`, `MAN-04`,
     `MAN-05`, `MAN-06`, `MAN-07`, `MAN-EVAL-06`, `MAN-EVAL-07`. Nenhuma
     destas é reaproveitada no dev — corrige o problema de sobreposição
     identificado em IMP-08 no eixo tipográfico.
2. **Rasura (MAN-05)**: a transcrição de referência congelada é o **texto
   final corrigido** (o que ficou pretendido após a correção), não a
   palavra riscada. Fixado agora, não ajustável depois de ver resultado de
   candidato.
3. **Independência do classificador de ilegibilidade (MAN-EVAL-07)**: a
   pessoa que determina o "texto visualmente recuperável" (seção 4, item 2
   abaixo) **deve ser alguém que não conhece o texto originalmente
   escrito** — inclusive, se possível, alguém que não seja Rafael (autor
   da amostra). Se não houver disponibilidade de um segundo revisor
   independente e Rafael tiver que fazer essa classificação sabendo o que
   escreveu, **isso deve ser registrado explicitamente como limitação
   metodológica** no momento da entrega da amostra (não omitido, não
   contornado por "fingir esquecer" o texto original).
4. **Papel de Hermes quando as fotos chegarem**: ao receber as fotos e
   referências localmente, a conferência se limita a **inventário,
   formato e presença/consistência das referências** (nomes de arquivo
   correspondentes, transcrição presente para cada foto, split dev/eval
   respeitado, regra da rasura respeitada). **Nenhum OCR será executado
   e nenhuma imagem será enviada a agentes externos** (Codex, Antigravity
   CLI ou qualquer outro) nesta etapa — isso segue aguardando autorização
   separada para a execução do benchmark manuscrito em si.

## 1. O que escrever à mão e fotografar

- Use **frases fictícias**, no estilo de resposta curta de aluno a uma
  questão de prova (1 a 3 frases, como nas amostras tipográficas
  IMP-01 a IMP-07). Não copie as mesmas frases já usadas no texto
  impresso — use conteúdo novo, para não contaminar a comparação com
  memorização de padrão.
- **Proibido**: nome, matrícula, turma, escola, ou qualquer dado que
  identifique uma pessoa real. Apenas conteúdo fictício de resposta a
  questão.
- Sugestão de temas (mesmo espírito das amostras impressas — respostas
  curtas de geografia/ciências/história fictícias), por exemplo:
  1. Uma frase respondendo "qual é a capital de um país fictício" (nítida,
     letra legível, caneta escura).
  2. Uma frase mais longa (2 frases), letra normal, levemente inclinada
     na foto (~5°).
  3. Uma frase com pelo menos 2 palavras contendo acentos/cedilha em
     português (ç, ã, é) — para testar o mesmo eixo de acentuação do
     conjunto tipográfico (equivalente a IMP-06).
  4. Uma frase com uma palavra riscada/corrigida no meio (rasura real
     de próprio punho) — equivalente a IMP-07.
  5. Uma frase escrita mais rápido/corrido, letra menos caprichada mas
     ainda legível para um humano.

## 2. Quantidade e condições das fotos

- **Total fixado: 7 fotos no eixo principal** (`MAN-01` a `MAN-07`, uma por
  item da lista acima) **+ 2 fotos do eixo vazio/ilegível** (`MAN-EVAL-06`,
  `MAN-EVAL-07`, seção 4) = **9 fotos no total**, conforme pré-registro da
  seção 0.
  - `MAN-01`: nítida, bem iluminada, ângulo frontal (dev);
  - `MAN-02`: leve inclinação da câmera/folha (~5°) (eval);
  - `MAN-03`: iluminação irregular, sombra parcial sobre parte do texto
    (eval);
  - `MAN-04`: levemente desfocada, leve movimento da câmera (eval);
  - `MAN-05`: com a rasura mencionada no item 4 da lista acima (eval);
  - `MAN-06`: escrita mais rápida/corrida, nítida (eval);
  - `MAN-07`: condição livre, realista, à sua escolha (eval).
- Fundo simples (papel branco/pauta comum), sem necessidade de scanner —
  uma foto de celular já é suficiente, igual ao uso real do produto.
- Cada foto deve conter **uma única resposta** (não uma folha inteira
  com várias respostas), mantendo o mesmo formato de "uma foto = uma
  resposta" já usado no eixo tipográfico e já decidido em `DEC-AV-018`.

## 3. Como fornecer a transcrição de referência

- Para cada foto, forneça um arquivo de texto simples (`.txt`) com a
  transcrição **exata** do que você escreveu, incluindo:
  - pontuação exatamente como escrita;
  - maiúsculas/minúsculas exatamente como escrita;
  - acentuação exata;
  - se houver rasura: registre a transcrição do texto **final**
    pretendido (não a palavra riscada), já que é isso que representaria
    a resposta correta do aluno.
- Nomeie os arquivos de forma correspondente à foto (ex.:
  `MAN-01_nitida.jpg` + `MAN-01_nitida_referencia.txt`), no mesmo padrão
  do conjunto tipográfico já existente.
- Essa transcrição deve ser fornecida **antes** de qualquer candidato
  processar a imagem — mesma regra de protocolo congelado já usada no
  eixo tipográfico (a referência não pode ser ajustada depois de ver o
  resultado de nenhum candidato).

## 4. Duas amostras adicionais e separadas (vazio × ilegível)

Distintas de MAN-01 a MAN-07 acima, propostas para fechar a lacuna
registrada em AC-05.

- **MAN-EVAL-06 (vazia)**: uma foto nova de uma folha em branco (sem
  nenhuma escrita) — equivalente ao papel do IMP-08 atual, mas fotografada
  como as demais (não gerada sinteticamente). Referência: string vazia.
  Não há ambiguidade aqui — não existe texto original nem texto
  recuperável.

- **MAN-EVAL-07 (ilegível)**: uma foto de uma escrita manuscrita real
  (não um rabisco abstrato) que se tornou **visualmente ilegível** por
  degradação — por exemplo, letra muito apertada/sobreposta, tinta
  borrada de propósito, ou múltiplas camadas de escrita no mesmo espaço.
  Diferente de MAN-EVAL-06: aqui existe uma tentativa real de escrita.

  **Distinção obrigatória entre duas transcrições separadas, para não
  presumir que o OCR "deveria" recuperar o texto original:**
  1. **Texto originalmente escrito** — o que você de fato escreveu ao
     produzir a amostra, registrado por você, em arquivo separado
     (`MAN-EVAL-07_texto_original_NAO_USAR_COMO_REFERENCIA.txt`), rotulado
     explicitamente como não-referência. Este texto existe apenas para
     documentação/auditoria de como a amostra foi produzida — **não é a
     transcrição de referência usada para avaliar nenhum candidato**.
  2. **Texto visualmente recuperável** — determinado por um revisor
     (você ou outra pessoa) observando **apenas a foto**, sem consultar o
     texto original, registrando exatamente o que consegue ler com
     confiança. Se nada for seguramente legível, este texto é a **string
     vazia** — igual ao tratamento de MAN-EVAL-06. Este é o único texto que
     serve como transcrição de referência oficial da amostra.
  - Esta separação evita o erro metodológico de, sabendo o que foi
    escrito, cobrar de um candidato que ele "adivinhe" ou reconstrua
    conteúdo que não está de fato disponível na imagem. O critério
    eliminatório de invenção de texto (seção 5 do protocolo) continua
    avaliando o candidato contra o texto visualmente recuperável (item 2),
    nunca contra o texto originalmente escrito (item 1).

- As duas amostras (`MAN-EVAL-06`, `MAN-EVAL-07`) ficam **exclusivas do
  conjunto eval**, sem uso no conjunto dev, para não repetir o problema de
  sobreposição identificado em IMP-08 (ver correção metodológica desta
  rodada). Isso cobre a lacuna descrita em AC-05: "vazio" e "ilegível"
  passam a ser dois estímulos visuais distintos e testados separadamente,
  cada um com sua própria amostra e sua própria transcrição de referência.

## 5. Como será medida a revisão humana (protocolo já congelado, seção 12
do `PROTOCOLO_CONGELADO.md`, ainda não executado)

Quando você (ou outro revisor humano designado) estiver disponível, com os
seguintes controles metodológicos explícitos (fixados agora, antes de
qualquer execução):

1. Para cada amostra elegível × candidato que passou nos critérios
   eliminatórios, o revisor vê a imagem original e a transcrição sugerida
   por um candidato, **sem saber qual candidato gerou aquela sugestão**
   (identidade do candidato ocultada/às cegas).
2. **A ordem de apresentação das combinações amostra × candidato é
   variada/randomizada** entre revisores e entre sessões — não segue
   sempre a mesma sequência fixa (ex.: sempre Tesseract → EasyOCR →
   moondream:v2 na mesma ordem), para reduzir efeito de aprendizado ou
   fadiga sistematicamente associado a um candidato específico.
3. O revisor confirma a transcrição como está, ou a corrige.
4. É cronometrado o tempo entre a exibição e a confirmação/correção.
5. É registrada a distância de edição entre a sugestão do candidato e o
   texto que o revisor confirmou como correto.
6. **É registrado explicitamente se o revisor também é autor da resposta
   manuscrita que está revisando** (ex.: Rafael revisando uma amostra que
   ele próprio escreveu) — essa condição é anotada por amostra × revisor,
   porque conhecer o próprio texto de antemão pode facilitar a revisão
   (menor tempo, menor taxa de correção) de forma não representativa de
   um revisor real avaliando texto de terceiros. Não impede a medição,
   mas exige que o resultado seja interpretado com essa ressalva.
7. Repete-se para todas as combinações candidato × amostra relevantes do
   conjunto eval.

Essa atividade não é substituída por estimativa de nenhum agente — só
conta como "medida" quando executada com um revisor humano real
participando de fato.

## 6. O que esta instrução autoriza e o que continua NÃO autorizado

**Autorizado por Rafael (2026-09-29)**: a coleta das fotos (Rafael prepara
localmente) e, quando disponíveis, a conferência por Hermes de inventário,
formato e presença/consistência das referências (seção 0, item 4).

**Continua NÃO autorizado nesta etapa**:
- rodar benchmark (nenhum candidato processa as imagens ainda);
- executar OCR de qualquer tipo sobre as fotos;
- enviar as imagens a Codex, Antigravity CLI ou qualquer agente externo;
- instalar/reinstalar modelo;
- qualquer ação Git/remota;
- alteração em `avalia_dev` ou em código de produção.

A ausência de execução do benchmark manuscrito não é reprovação de
Tesseract, EasyOCR ou moondream:v2 no eixo manuscrito — é sequenciamento:
primeiro a coleta e conferência de inventário, depois (com nova
autorização explícita) a execução propriamente dita, seguindo o mesmo
modelo de protocolo congelado ANTES de medir já usado no eixo tipográfico.
