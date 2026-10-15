---
id: "runner_spec_congelada_AV-S05B_manuscrito"
tema: "Especificação CONGELADA do runner de benchmark OCR (eixo manuscrito, Amostra_1)"
data: "2026-10-15 (America/Sao_Paulo)"
estado: "CONGELADA ANTES DE MEDIR O EVAL — não ajustável com base em resultados"
protocolo_base: "docs/governance/evidence/AV-S05B/protocolo/PROTOCOLO_CONGELADO.md (seções 5,6,7,8,9,10)"
---

# Runner de benchmark OCR — especificação congelada (eixo manuscrito)

Contrato que o executor (Claude Code) implementa e que os revisores (Antigravity, Codex)
verificam usando SOMENTE dados sintéticos. Congelado ANTES de medir o eval; nenhum
parâmetro é ajustado após ver resultado de avaliação (protocolo §7, regra final).

## 1. Entradas e saídas

- Entrada de imagem: PNGs de `local-nao-versionado/ocr/Amostra_1/trabalho_png/MAN-*.png`.
- Referência: `.txt` de `local-nao-versionado/ocr/Amostra_1/referencias/MAN-*_referencia.txt`.
- PROIBIDO: fornecer a referência ou o original de auditoria como ENTRADA ao candidato.
  A referência só é lida pelo scorer, nunca pelo motor OCR.
- Saída bruta: um JSON por (candidato × amostra) em
  `local-nao-versionado/ocr/Amostra_1/resultados_brutos/`, contendo: candidato, amostra,
  conjunto (dev/eval), texto_saida_original (verbatim, sem normalizar), status
  (ok|falha_execucao|abstencao), erro (se houver), t_carga_s, t_inferencia_s,
  normalizado_saida, normalizado_ref, cer, wer, ref_vazia(bool), produziu_texto(bool).

## 2. Normalização (protocolo §9) — aplicada só para CER/WER, nunca na saída bruta

- Unicode NFC.
- Espaços múltiplos → um único espaço; trim de início/fim.
- PRESERVA maiúsculas/minúsculas e pontuação (erro de caixa/pontuação conta como erro).
- PRESERVA acentos (ç, ã, é…) como caracteres distintos (erro de acento conta).
- Sem lowercasing, sem remoção de pontuação, sem remoção de acento.

## 3. Métricas (protocolo §7)

- CER = distância de edição de Levenshtein em CARACTERES (sub/ins/del, custo 1) entre
  saída normalizada e referência normalizada, dividida por `max(1, len(ref_norm_chars))`.
- WER = idem em PALAVRAS (split por espaço após normalização), dividida por
  `max(1, len(ref_norm_words))`.
- **Referência vazia (MAN-EVAL-06): NÃO calcular CER/WER com divisão por zero.** Reportar
  cer/wer como `null` e avaliar SEPARADAMENTE o critério de invenção: se o candidato
  produz texto não-vazio sobre referência vazia → viola o critério eliminatório
  "zero invenção em amostra vazia" (protocolo §5.2). Reportar `produziu_texto` e marcar
  `invencao_em_vazio=true/false`.

## 4. Latência (protocolo §7.3 / §8)

- Separar t_carga_s (carregar binário/pesos/modelo, 1ª vez) de t_inferencia_s (inferência
  com modelo já carregado). Medir no hardware local; rotular como não representativo de
  produção. Download é PREPARAÇÃO, fora de qualquer métrica de latência.

## 5. Estados por amostra × candidato (não conflar — protocolo §6)

- `ok`: candidato produziu saída (vazia ou não) sem erro de execução.
- `falha_execucao`: o motor falhou/erro de runtime/não carregou — registrar a mensagem
  real; NÃO converter em acerto, vazio ou abstenção; NÃO remover do denominador.
- `abstencao`: candidato explicitamente se recusa/retorna marcação de ilegibilidade —
  registrado explicitamente; permanece no denominador.
- Nenhum resultado ruim é excluído silenciosamente.

## 6. Agregação (denominadores claros)

- Por candidato: média de CER e WER SOMENTE sobre amostras eval com referência não-vazia
  e status `ok`. Essas são **7 amostras legíveis do eval**: MAN-02, MAN-03, MAN-04,
  MAN-05, MAN-06, MAN-07 **e MAN-EVAL-07** (legível, entra no CER/WER). Denominador
  reportado explicitamente (ex.: "CER médio sobre 7/7 amostras ok" ou "6/7, 1
  falha_execucao"). Esclarecimento: a menção "MAN-02..07 = 6" numa versão anterior desta
  spec estava ambígua — MAN-EVAL-07 TAMBÉM entra na média por ser legível, totalizando 7.
- MAN-01 (dev) reportado à parte, só como sanidade de execução — NÃO entra na média eval.
- MAN-EVAL-06 reportado à parte (critério de invenção), fora da média CER/WER.
- MAN-EVAL-07 entra no eval como amostra LEGÍVEL (CER/WER calculados), explicitamente
  rotulada como desvio do controle de ilegibilidade — NÃO usada para comprovar
  ilegibilidade.
- Candidato que falha um critério eliminatório (local/invenção) é reportado como
  desclassificado COM motivo, não omitido; não recebe "vencedor" automático.

## 7. Candidatos (protocolo §2) e invocação

- Tesseract + `por` (`tesseract <img> stdout -l por`), versão por `tesseract --version`.
- EasyOCR (`easyocr`, `Reader(['pt'])`, `readtext`), versão por `pip show easyocr`.
- moondream:v2 via Ollama (prompt fixo de transcrição literal, registrado).
- qwen2.5vl:3b via Ollama (mesmo prompt fixo).
- Prompt dos VLMs CONGELADO (registrar texto exato); temperatura 0 / determinístico quando
  suportado. Sem rede durante inferência (verificável; só Ollama local em 127.0.0.1).

## 8. Determinismo e versões (protocolo §10)

- Antes de medir o eval: registrar versão exata de cada binário/pacote/modelo (incl. hash
  do modelo no `ollama list`), parâmetros de invocação completos, hardware (M-series,
  RAM), confirmação de inferência offline.
- O runner e estes parâmetros ficam congelados; ajuste pós-resultado é proibido.

## 9. Isolamento

- venv dedicado em `local-nao-versionado/ocr/Amostra_1/venv_bench/` (não tocar ambientes
  da plataforma). Não remover modelos Ollama existentes (ex.: qwen2.5:7b-instruct-q4_K_M).
- Resultados brutos e logs em `local-nao-versionado/` (não versionado).
