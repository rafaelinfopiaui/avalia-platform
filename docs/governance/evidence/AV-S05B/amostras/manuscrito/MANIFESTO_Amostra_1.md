---
id: "manifesto_Amostra_1_preparacao_tecnica"
tema: "AV-S05B eixo manuscrito — Amostra_1: manifesto de preparação técnica local"
data: "2026-10-15 (America/Sao_Paulo)"
estado: "PREPARAÇÃO TÉCNICA CONCLUÍDA — NÃO congelado, benchmark NÃO executado"
---

# Manifesto — Amostra_1 (eixo manuscrito, AV-S05B)

## 0. Natureza e limites

Preparação técnica LOCAL concluída. Sem OCR, sem benchmark, sem IA sobre imagem,
sem envio externo, sem publicação Git. Originais preservados (fonte intacta,
verificada byte a byte). AV-S05B permanece **parcial**; numerador 22/70 preservado.

## 1. Localização

- **Fonte (originais, preservada):** `Imagens/Amostra_1/` (9 fotos + consolidado +
  `referencias/` confirmadas + auditoria). Protegida contra Git por
  `.git/info/exclude` (`/Imagens/`), exclusão LOCAL — `.gitignore` versionado NÃO alterado.
- **Conjunto de trabalho:** `local-nao-versionado/ocr/Amostra_1/` (já ignorado por
  `.gitignore:55` `/local-nao-versionado/`), organizado em:
  - `originais/` — cópias idênticas das 9 fotos-fonte (hash conferido == fonte);
  - `trabalho_png/` — 9 cópias PNG padronizadas (ver §2);
  - `referencias/` — 9 referências confirmadas por Rafael;
  - `auditoria/` — 1 original de MAN-EVAL-07 (NÃO-referência, nunca entra nos candidatos).
- Checksums do conjunto de trabalho: `CHECKSUMS_trabalho_Amostra_1.sha256` (28 entradas,
  verificado `shasum -c` = todos OK).

## 2. Padronização (conversão para PNG)

- Ferramenta: **`sips` (sips-316)**, nativa do macOS — nenhuma instalação/download.
- Parâmetros: `sips -s format png <src> --out <dst>`. **Sem** resize, **sem** sharpen,
  **sem** melhoria por IA, **sem** upscale (MAN-01 preservada em 548×314). Orientação
  visual preservada (sips aplica a orientação EXIF; demais HEIC sem flag de rotação).
- Dimensões origem == destino em todas (confirmado). Formato real do destino: PNG válido
  (confirmado por `file`).
- Motivo: 8 das 9 fotos-fonte são HEIC (extensão `.jpeg` enganosa); MAN-01 é JPEG real.
  Os PNG servem de entrada padrão para candidatos que não leem HEIC. Hashes
  origem→destino registrados no `CHECKSUMS_trabalho_Amostra_1.sha256`.

## 3. Pares imagem/referência (lista explícita)

Entrada do candidato = imagem PNG de `trabalho_png/`; referência = `.txt` de `referencias/`.

| ID | Conjunto | Imagem (trabalho) | Referência | Observação |
|---|---|---|---|---|
| MAN-01 | **dev** | trabalho_png/MAN-01.png | referencias/MAN-01_referencia.txt | só verificação de que o candidato roda |
| MAN-02 | eval | trabalho_png/MAN-02.png | referencias/MAN-02_referencia.txt | |
| MAN-03 | eval | trabalho_png/MAN-03.png | referencias/MAN-03_referencia.txt | |
| MAN-04 | eval | trabalho_png/MAN-04.png | referencias/MAN-04_referencia.txt | |
| MAN-05 | eval | trabalho_png/MAN-05.png | referencias/MAN-05_referencia.txt | texto final pós-rasura |
| MAN-06 | eval | trabalho_png/MAN-06.png | referencias/MAN-06_referencia.txt | |
| MAN-07 | eval | trabalho_png/MAN-07.png | referencias/MAN-07_referencia.txt | |
| MAN-EVAL-06 | eval | trabalho_png/MAN-EVAL-06.png | referencias/MAN-EVAL-06_referencia.txt | controle VAZIO (ref. 0 bytes) |
| MAN-EVAL-07 | eval | trabalho_png/MAN-EVAL-07.png | referencias/MAN-EVAL-07_referencia.txt | legível → NÃO é controle de ilegibilidade |

O arquivo `auditoria/MAN-EVAL-07_texto_original_NAO_USAR_COMO_REFERENCIA.txt` **NÃO** entra
na seleção de entradas dos candidatos sob nenhuma hipótese.

## 4. Confirmação humana (Rafael, 2026-10-15)

- MAN-01..07 correspondem literalmente ao manuscrito; MAN-05 = texto final pós-rasura.
- MAN-EVAL-06 em branco; referência vazia correta.
- MAN-EVAL-07 legível, corresponde ao texto proposto; **portanto NÃO atende ao controle de
  ilegibilidade (AC-05)**.
- Avaliação feita pelo autor (Rafael), conhecendo o original — limitação metodológica
  registrada.
- Correção de inferência: checksums iguais entre referência e auditoria NÃO indicam
  ausência de avaliação humana (apenas textos idênticos byte a byte).

## 5. Lacuna metodológica preservada

- MAN-EVAL-07 **não** foi substituída; protocolo **não** alterado silenciosamente.
- **AC-05 (vazio × ilegível) NÃO está concluído**: falta um estímulo genuinamente
  ilegível. AV-S05B permanece **parcial**.
- Amostra_2 (parceiro) fica **fora desta rodada** — não é exigida para preparar ou avaliar
  a Amostra_1.

## 6. Proposta de execução PARCIAL (para próxima autorização; NÃO executada)

Candidatos obrigatórios do protocolo congelado: Tesseract+por, EasyOCR, moondream:v2,
qwen2.5vl:3b (PaddleOCR fora, não reprovado).

O que PODERÁ ser medido sobre as amostras disponíveis:
- CER/WER por amostra, por categoria e agregado, sobre MAN-01 (dev, só sanidade) e o eval
  MAN-02..07 (texto manuscrito legível real), com normalização NFC+trim preservando
  caixa/pontuação/acento (seção 9 do protocolo).
- Critério eliminatório "zero invenção em amostra vazia": MAN-EVAL-06 (referência vazia) —
  candidato que produza texto não-vazio é desclassificado.
- Latência (carga inicial separada de inferência), por amostra, no hardware local.

O que CONTINUARÁ pendente (não medível com esta coleção):
- **Controle de ilegibilidade (AC-05)**: MAN-EVAL-07 é legível; não há estímulo ilegível
  comprovado. Fica como lacuna explícita; não fecha AC-05.
- **Esforço de revisão humana** (seção 12): só com revisor humano real e protocolo de
  tempo/edição; não substituído por estimativa de agente.
- Avaliação de legibilidade por terceiro cego (atual foi do autor).

Condição de conclusão: resultado negativo é aceitável; mas o eixo manuscrito **permanece
parcial** enquanto AC-05 e o esforço humano não forem resolvidos — **não declarar AC-05 nem
AV-S05B concluídos**.

### Plano/comando de benchmark (para sua próxima autorização — NÃO rodar agora)

Execução offline, em banco/ambiente isolado de trabalho, sobre `trabalho_png/` com
referências de `referencias/`. Esboço (a detalhar no momento autorizado, versões travadas
antes de medir conforme seção 10):

```
# (ILUSTRATIVO — requer autorização explícita; nada é executado nesta rodada)
# preparar (download = preparação, fora da métrica de latência):
#   brew install tesseract tesseract-lang   # Tesseract + por
#   pip install easyocr                      # EasyOCR (venv isolado)
#   ollama pull moondream:v2 && ollama pull qwen2.5vl:3b
# medir (offline, sem rede), por candidato × amostra:
#   entrada = local-nao-versionado/ocr/Amostra_1/trabalho_png/MAN-*.png
#   referência = local-nao-versionado/ocr/Amostra_1/referencias/MAN-*_referencia.txt
#   registrar: versão/parâmetros/hardware; CER/WER por amostra/categoria/agregado;
#              latência carga vs inferência; eliminatórios (vazio/local); abstenções.
```
