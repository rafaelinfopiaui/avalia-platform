# Registro da etapa de preparação (download) — AV-S05B

Conforme protocolo congelado seção 8: esta etapa é registrada separadamente
e NÃO conta como parte de nenhuma métrica de latência de inferência.

| Data/hora (UTC) | Item | Comando | Origem | Tamanho | Resultado |
|---|---|---|---|---|---|
| 2026-09-29 ~13:30 | Tesseract 5.5.3 + tesseract-lang (162 idiomas, incluindo `por`) | `brew install tesseract tesseract-lang` | Homebrew | ~pacote padrão do formula | sucesso |
| 2026-09-29 ~13:30 | moondream:v2 (Apache 2.0, Phi-2 1.42B + CLIP 454M) | `ollama pull moondream:v2` | Ollama registry local (`ollama.com/library/moondream`) | 828 MB + 909 MB (2 blobs) | sucesso |
| 2026-09-29 ~13:30 | EasyOCR 1.7.2 + dependências (torch 2.14.0, torchvision, opencv-headless etc.) | `pip install easyocr` (venv isolado `av-s05b-benchmark-experimento/venv`) | PyPI | ~300 MB agregado (torch é a maior parcela) | sucesso |

**Candidatos não baixados nesta rodada** (fora de escopo desta execução,
não reprovados):

- PaddleOCR — registrado no protocolo como fora desta execução por limitação
  de tempo/recursos da sessão.
- Qwen2.5-VL 3B (Apache 2.0, `ollama pull qwen2.5vl:3b`, ~3,2 GB) — listado no
  protocolo como candidato, mas não baixado nesta execução para manter o
  tempo de sessão administrável; registrado como candidato não testado, não
  desclassificado. Pode ser adicionado em rodada futura sem alterar o
  protocolo já congelado para os candidatos testados.

Verificação de licença de cada modelo/pacote baixado (busca real, 2026-09-29):
Tesseract (Apache 2.0), moondream:v2 (Apache 2.0, confirmado na página do
Ollama), EasyOCR (Apache 2.0). Todas compatíveis com o experimento.

## Desvio de protocolo registrado

**2026-09-29, ~13:33 UTC**: o teste funcional do script `candidato_easyocr.py`
sobre a amostra `IMP-01_nitida.png` (fase de smoke-test dos scripts, antes de
rodar o benchmark oficial) disparou o download automático dos modelos de
detecção e reconhecimento do EasyOCR (mensagem "Downloading detection model...
Downloading recognition model..."), que a biblioteca faz na primeira
inicialização do `Reader`. Este download não havia sido isolado previamente
como as demais preparações (Tesseract, moondream:v2). **Motivo**: a API do
EasyOCR baixa o modelo de forma transparente na primeira instanciação, sem
etapa de "pull" separada como Ollama ou "install" separado como Homebrew.
**Decisão**: o tempo desta chamada específica (que incluiu o download) não é
usado como amostra de tempo de carregamento no benchmark oficial — o
benchmark oficial roda depois deste download já estar em cache local, então
todas as medições de tempo de carregamento do EasyOCR no benchmark oficial
refletem apenas inicialização do `Reader` com modelo já em disco, sem rede.
Nenhuma amostra de avaliação final (fase eval) foi processada durante este
smoke-test — apenas a amostra de dev `IMP-01_nitida.png`, que já fazia parte
do split de ajuste e não é usada para medir qualidade.

## Limpeza pós-experimento

**Nota de correção (2026-09-29, verificação independente posterior):** esta
seção descrevia uma limpeza que havia sido *planejada*, mas que ficou
incompleta na prática — as reinstalações feitas para as rodadas de
reexecução do Codex e de revalidação (necessárias para reproduzir o
benchmark de forma independente) não foram desfeitas na sequência. Uma
verificação de comando real, feita depois, confirmou que Tesseract e
`moondream:v2` ainda estavam presentes na máquina. A limpeza foi então
executada de fato nesta correção, com verificação de comando após cada
etapa (não apenas descrita).

Ao final da execução e após a preservação dos resultados:

- `brew uninstall tesseract tesseract-lang` — removeu Tesseract 5.5.3 e o
  pacote de idiomas (ambos inexistentes antes da sprint), executado e
  **confirmado** em 2026-09-29 (`which tesseract` retorna vazio, exit 1);
  Homebrew também removeu automaticamente 29 dependências órfãs
  (cairo, pango, leptonica, harfbuzz, libtiff, etc.) que não existiam antes
  da instalação do Tesseract para este experimento;
- `ollama rm moondream:v2` — removeu o modelo de visão baixado para o
  experimento (inexistente antes da sprint), executado e **confirmado**
  em 2026-09-29 (`ollama list` mostra apenas `qwen2.5:7b-instruct-q4_K_M`,
  o modelo textual preexistente do AI Engine em produção);
- o venv EasyOCR permanece exclusivamente dentro do diretório dedicado do
  experimento (`av-s05b-benchmark-experimento/venv/`), fora do repositório
  AvalIA, para reprodução local futura; não foi copiado para o pacote de
  evidência versionável (é reconstruível pelo registro de preparação).

Essa limpeza restaura o ambiente global da máquina e preserva scripts,
amostras, configurações, saídas e evidências em localização durável.

