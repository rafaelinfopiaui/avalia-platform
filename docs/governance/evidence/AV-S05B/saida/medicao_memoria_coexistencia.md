# Medição de memória e coexistência — nota para BL-AV-4B-17

Registrado a pedido explícito de Rafael (condição 2 da autorização da
AV-S05B): "registre consumo de memória e condições de coexistência com o
modelo textual". Não fazia parte do protocolo congelado original nem do
benchmark em si — é uma medição complementar, feita após a conclusão do
benchmark, sobre a máquina real de desenvolvimento (Apple M5 Pro, 24 GB RAM
unificada), não sobre hardware-alvo de produção (`DEC-AV-009` pendente).

## Método

Comandos reais via API do Ollama (`/api/generate`) e `ollama ps`, em
2026-09-29, nesta sessão. Nenhuma amostra do benchmark foi reprocessada;
esta é uma medição de infraestrutura, não de qualidade de reconhecimento.

## Resultado observado

1. **`moondream:v2` sozinho, carregado**: `ollama ps` reporta 1.1 GB,
   100% GPU (Metal, memória unificada).
2. **`qwen2.5:7b-instruct-q4_K_M` (modelo textual já existente no ambiente,
   usado pelo AI Engine do repositório — sem registro de implantação formal
   em ambiente de produção verificado nesta sprint) sozinho, carregado**:
   `ollama ps` reporta 4.6 GB, 100% GPU.
3. **Ambos carregados simultaneamente** (chamada explícita a cada um,
   depois `ollama ps` sem descarregar nenhum): **os dois modelos
   coexistem ao mesmo tempo** — `ollama ps` lista ambos simultaneamente
   (`qwen2.5:7b-instruct-q4_K_M` 4.6 GB + `moondream:v2` 1.1 GB = **~5,7 GB
   combinados**), sem evidência de que o Ollama descarregou um para
   carregar o outro nesta configuração (`keep_alive` padrão, 24 GB de RAM
   unificada disponível).
4. O processo `ollama serve` em si mantém RSS baixo e estável
   (~23–44 MB) independente do que está carregado — a memória dos modelos
   é gerenciada separadamente pelo backend Metal/GPU, não aparece no RSS
   do processo supervisor.
5. Memória do sistema (`vm_stat`) permaneceu com milhares de páginas
   livres em todos os testes — nesta máquina (24 GB), carregar os dois
   modelos ao mesmo tempo (~5,7 GB) não esgotou a memória disponível, mas
   isso não constitui garantia para hardware-alvo menor.

## Observação para `BL-AV-4B-17` (isolamento de recursos, decisão em `AV-S07B`)

- Nesta máquina de desenvolvimento, `moondream:v2` e o modelo textual já
  existente no ambiente **podem coexistir carregados ao mesmo tempo sem
  eviction automática**, com folga de memória.
- O protocolo do benchmark (seção 4/7) já executa os candidatos de
  OCR/visão **sequencialmente**, nunca simultaneamente ao modelo textual
  durante a medição — isso evita qualquer efeito de contenção nos números
  de CER/WER/latência já reportados no relatório final.
- Esta medição **não decide a arbitragem de recursos entre os dois
  processos caso venham a coexistir em um cenário de produção futuro**
  (`BL-AV-4B-17` continua formalmente alocado a
  `AV-S07B`, conforme já registrado na sprint) — é apenas o dado bruto de
  coexistência observado nesta máquina, para informar aquela decisão
  futura, não para antecipá-la.
- Não foi medido o comportamento sob GPU/memória sob disputa concorrente
  real (chamadas simultâneas de inferência nos dois modelos ao mesmo
  tempo) — apenas carregamento simultâneo em repouso. Uma medição de
  contenção sob carga concorrente real fica como lacuna explícita, não
  como conclusão de que não há contenção.

## Estado da máquina após esta medição

Ambos os modelos foram descarregados da memória (`keep_alive: 0`) ao final
deste teste, antes da limpeza de dependências registrada em
`PREPARACAO_DOWNLOADS.md` (seção "Limpeza pós-experimento").
