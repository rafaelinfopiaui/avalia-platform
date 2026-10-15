# Registro de preparação dos candidatos — AV-S05B manuscrito (Amostra_1)

Data: 2026-10-15. Downloads = preparação (com rede), fora de qualquer métrica de latência
de inferência. Nenhuma imagem/transcrição enviada a serviço externo. Ambientes da
plataforma não alterados; nenhum modelo existente removido.

## Candidatos (4, conforme protocolo §2)

| Candidato | Versão / identificador | Origem | Isolamento |
|---|---|---|---|
| Tesseract + por | tesseract 5.5.3 (leptonica 1.87.0); langs eng+por | Homebrew (`brew install tesseract tesseract-lang`) | binário do sistema /opt/homebrew/bin/tesseract |
| EasyOCR | easyocr (import OK); torch 2.14.1 | PyPI (`pip install easyocr`) | venv dedicado `local-nao-versionado/ocr/Amostra_1/venv_bench/` |
| moondream:v2 | Ollama id 55fc3abd3867, 1.7 GB | `ollama pull moondream:v2` | Ollama local 127.0.0.1:11434 |
| qwen2.5vl:3b | Ollama id fb90415cde1e, 3.2 GB | `ollama pull qwen2.5vl:3b` | Ollama local 127.0.0.1:11434 |

## Preservado
- Modelo textual existente `qwen2.5:7b-instruct-q4_K_M` (id 845dbda0ea48, 4.7 GB) — NÃO removido.
- PaddleOCR permanece fora desta rodada (não reprovado), conforme protocolo.

## Inferência offline
- Tesseract/EasyOCR: locais por natureza. VLMs: Ollama local (sem rede durante inferência).
- Download dos pesos é a única etapa com rede; concluída na preparação.
