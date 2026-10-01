---
id: "BL-AV-4B-01"
status: "detalhamento_documental_autorizado"
autorizado_por: "Rafael (2026-09-24; DEC-AV-025; somente detalhamento documental)"
consolidador: "Hermes"
---

# Levantamento técnico inicial de OCR/visão local (BL-AV-4B-01)

> **DETALHAMENTO DOCUMENTAL. NÃO AUTORIZA BENCHMARK NEM IMPLEMENTAÇÃO.** Autorizado por Rafael em
> 2026-09-24 (DEC-AV-025) apenas para produzir a proposta de alternativas, métricas, amostras e
> limites de aceite descrita abaixo. `BL-AV-4B-20` (benchmark comparativo) e `BL-AV-4B-02` (decisão
> arquitetural) continuam não iniciados e dependentes de `DEC-AV-017` (aprovação prévia dos
> critérios de medição). Nenhuma imagem foi processada, nenhum modelo foi baixado ou executado, e
> nenhuma dependência de OCR foi adicionada ao repositório nesta execução.

## 1. Objetivo deste documento

Cumprir o escopo de `BL-AV-4B-01`: levantar alternativas de OCR/visão local para texto impresso e
manuscrito em português, suas licenças, requisitos de hardware e limitações conhecidas, e propor
(sem medir) os eixos de métrica, o conjunto de amostras e os limites de aceite que `DEC-AV-017`
precisa aprovar antes de `BL-AV-4B-20` poder ser executado.

Regra explícita já registrada no backlog: não presumir que o modelo textual atual do AI Engine
(Ollama/`qwen2.5:7b-instruct-q4_K_M`) atende à leitura de imagens. OCR/visão é um componente novo,
não uma extensão do pipeline textual existente.

## 2. Alternativas levantadas (inspeção documental, sem execução)

| Alternativa | Categoria | Licença | Requisito de hardware conhecido | Suporte a manuscrito | Suporte a pt-BR |
|---|---|---|---|---|---|
| Tesseract OCR (+ `tesseract-ocr-por`) | OCR tradicional (motor clássico, baseado em LSTM desde 4.x) | Apache 2.0 | CPU; leve; sem GPU obrigatória | Fraco/inexistente para manuscrito corrido | Pacote de idioma `por` disponível oficialmente |
| PaddleOCR | OCR tradicional + detecção de layout (redes neurais) | Apache 2.0 | CPU viável; GPU acelera; modelos "mobile" mais leves existem | Limitado; melhor em impresso | Sem modelo pt-BR oficial dedicado no repositório principal; normalmente usa modelo multilíngue/latin |
| EasyOCR | OCR tradicional baseado em deep learning (CRNN) | Apache 2.0 | GPU recomendada para desempenho aceitável; roda em CPU mais lentamente | Fraco para manuscrito | Suporta português como idioma da lista oficial |
| VLM local pequeno (ex.: família Qwen2-VL, LLaVA, ou modelo de visão servido via Ollama) | Modelo de visão-linguagem local | Varia por modelo (verificar licença específica antes de qualquer download) | Exige GPU/VRAM significativamente maior que os motores tradicionais acima; latência maior por imagem | Potencial melhor para manuscrito e para reconhecer contexto semântico, mas não comprovado nesta investigação | Depende do modelo; modelos multilíngues costumam cobrir português, mas qualidade específica não medida aqui |
| Serviço de OCR em nuvem (Google Vision, AWS Textract, Azure Document Intelligence) | OCR gerenciado externo | Comercial/uso pago | Nenhum requisito de hardware local | Geralmente forte, inclusive para manuscrito em alguns serviços | Suporte a português tipicamente disponível | 

Nota sobre a última linha: qualquer serviço em nuvem está **fora de escopo** por definição do
produto (AvalIA usa IA local — ver `README.md`, `AI Engine (Ollama, local)`) e por
`docs/pendencia-regulatoria.md` sobre dados de estudantes. Incluído apenas para registrar que foi
considerado e descartado, não como candidato viável.

Esta tabela é levantamento documental (fontes públicas dos próprios projetos), não benchmark. Nenhum
número de acurácia, CER/WER ou latência real foi medido nesta sessão — qualquer alegação de
desempenho de qualquer alternativa acima permanece **não verificada** até `BL-AV-4B-20`.

## 3. Limitações conhecidas, por categoria

- **OCR tradicional (Tesseract/PaddleOCR/EasyOCR):** desempenho tipicamente forte em texto impresso
  bem escaneado; degrada significativamente com inclinação, iluminação irregular, baixa resolução e
  principalmente com manuscrito corrido — cursos de letra manuscrita não seguem um padrão
  tipográfico fixo, o que é a limitação estrutural desses motores.
- **VLM local:** exige recursos de hardware muito maiores (GPU com VRAM suficiente para o modelo
  escolhido); tempo de inferência por imagem tende a ser maior que OCR tradicional; comportamento
  com manuscrito e com texto em português não está documentado de forma confiável o bastante para
  ser tratado como fato sem medição própria (`BL-AV-4B-20`).
- **Ambas as categorias:** nenhuma delas garante ausência de alucinação/invenção de texto quando a
  imagem é ilegível ou vazia — isso é um requisito específico de aceite proposto na seção 4
  (robustez a ilegível/ausente sem invenção de texto), não uma característica presumida de nenhuma
  alternativa.

## 4. Proposta de eixos de métrica para `DEC-AV-017` (não são critérios aprovados)

Eixos propostos, cada um mensurável de forma objetiva e reproduzível quando `BL-AV-4B-20` for
autorizado:

1. **Qualidade de transcrição** — CER (Character Error Rate) e WER (Word Error Rate) contra uma
   transcrição de referência produzida manualmente para cada amostra do conjunto de teste.
2. **Esforço de revisão humana** — proporção de caracteres/palavras que o professor precisaria
   corrigir manualmente após a sugestão automática, medida por distância de edição normalizada.
3. **Latência no hardware-alvo** — tempo de processamento por imagem, medido no hardware que
   `DEC-AV-009` (ainda pendente) definir como alvo; até essa decisão, a latência pode ser registrada
   apenas no hardware disponível nesta máquina, rotulada explicitamente como não representativa do
   hardware-alvo final.
4. **Robustez a ilegível/ausente** — taxa de casos em que a alternativa reconhece corretamente que
   não há texto extraível (imagem vazia, ilegível, cortada) em vez de inventar conteúdo; qualquer
   invenção de texto em uma amostra vazia/ilegível é tratada como falha crítica desse eixo, não como
   erro comum de qualidade.
5. **Viabilidade 100% local** — critério eliminatório binário: a alternativa deve rodar inteiramente
   local, sem chamada de rede a serviço externo, para permanecer candidata (elimina a linha de
   "serviço em nuvem" da seção 2 automaticamente).

## 5. Proposta de conjunto de amostras (reaproveitando a cobertura de `BL-AV-4B-18`)

Proposta de cobertura mínima do conjunto de teste, para evitar que `BL-AV-4B-20` produza um
resultado enviesado por amostras não representativas:

- fotos nítidas, bem enquadradas, texto impresso;
- fotos nítidas, bem enquadradas, texto manuscrito;
- fotos inclinadas (rotação leve e acentuada);
- fotos desfocadas;
- fotos com iluminação irregular (sombra parcial, contraluz);
- texto com acentuação e caracteres especiais do português;
- texto com rasuras/correções visíveis do próprio aluno;
- imagem vazia ou completamente ilegível (para o eixo de robustez da seção 4, item 4).

Todas as amostras devem ser fictícias ou explicitamente autorizadas — nenhuma imagem de aluno real
deve ser usada em `BL-AV-4B-20` sem decisão específica sobre dados reais (`DEC-AV-014`,
`BKL-AV-001`), que continuam pendentes.

## 6. Proposta de limites de aceite (para `DEC-AV-017` decidir, não uma decisão já tomada)

Proposta, sujeita a ajuste por Rafael antes de virar critério de aceite de `BL-AV-4B-20`:

- CER/WER da alternativa vencedora deve estar em patamar que exija revisão humana como regra do
  produto (a correção final é sempre humana — RF já registrado), não que substitua a leitura do
  professor;
- taxa de invenção de texto em amostras vazias/ilegíveis deve ser **zero** para a alternativa ser
  elegível — este é o único critério eliminatório absoluto além da viabilidade 100% local;
- latência por imagem deve ser compatível com um fluxo de correção assíncrono (o produto já usa
  `CorrectionJob` assíncrono com polling), não bloqueando a interação do professor.

Estes números-limite específicos (percentuais, segundos) não são propostos aqui como valores fixos
— a proposta é a estrutura dos critérios; os limites numéricos exatos devem ser decididos junto com
`DEC-AV-017`, após eventualmente uma medição preliminar de referência.

## 7. Isolamento de recursos (nota para `BL-AV-4B-17`, não decidido aqui)

Caso um VLM local seja escolhido em `BL-AV-4B-02`, ele competirá por GPU/memória com o AI Engine
textual existente (Ollama/`qwen2.5:7b-instruct-q4_K_M`) se ambos rodarem na mesma máquina. Esta
arbitragem já está registrada como item de arquitetura próprio, `BL-AV-4B-17`, e não é decidida
neste levantamento — apenas citada aqui para registrar a dependência.

## 8. O que este documento NÃO decide nem executa

- Não decide qual alternativa da seção 2 será escolhida — isso é `BL-AV-4B-02`, dependente do
  benchmark medido (`BL-AV-4B-20`), não deste levantamento.
- Não aprova `DEC-AV-017` — apenas propõe a estrutura que `DEC-AV-017` precisa decidir.
- Não executa nenhum benchmark, download de modelo, instalação de dependência de OCR, ou
  processamento de imagem real ou fictícia.
- Não altera `core/`, `ai-engine/`, `frontend/`, `requirements.txt` nem nenhuma dependência do
  repositório.
- Não amplia o escopo de `AV-S03`, que permanece isolado de OCR/imagem por definição de escopo (ver
  `sprint_AV-S03_estrutura_academica.md`, seção 3, "fora de escopo").
