---
id: "diagnostico_http400_qwen2.5vl_Amostra_1"
tema: "AV-S05B eixo manuscrito — diagnóstico dirigido do HTTP 400 do qwen2.5vl:3b (rodada 1) e correção de transporte (rodada 2)"
data: "2026-10-15 (America/Sao_Paulo)"
estado: "DIAGNÓSTICO CONCLUÍDO — causa comprovada; correção de transporte validada; AV-S05B permanece parcial; AC-05 NÃO concluído; nenhuma solução promovida"
autorizacao: "Rafael — diagnóstico e correção LOCAL do caminho experimental, sem alterações no produto; num_ctx classificado por Rafael como transporte/serialização, reexecução do Qwen autorizada nesta rodada"
hardware: "Apple M5 Pro, 24 GB RAM, macOS 27.2 — latência não representativa de produção"
---

# Diagnóstico do HTTP 400 do qwen2.5vl:3b (AV-S05B, eixo manuscrito, Amostra_1)

> **RECONCILIAÇÃO DATADA (2026-10-15T16:10-03:00) — precisão metodológica.**
> Esta nota corrige e delimita afirmações deste documento SEM reescrever o texto
> original abaixo (preservado como registro do que foi escrito na primeira passagem).
>
> **(1) Classificação de `num_ctx` corrigida.** A alteração `num_ctx` 4096→8192 é uma
> **alteração da configuração de contexto de inferência**, motivada pelos erros de limite
> de contexto do eval — NÃO "somente transporte/serialização" como está escrito nas §4–§5
> originais e nos documentos de governança da primeira passagem. A autorização recebida de
> Rafael (classificar como transporte e reexecutar) é preservada e permanece válida como
> decisão de processo, mas a autorização **não muda a natureza técnica do parâmetro**:
> `num_ctx` é um parâmetro de inferência (teto da janela de contexto do modelo). A expressão
> "transporte/serialização" deve ser lida, deste ponto em diante, como "configuração de
> contexto de inferência".
>
> **(2) Natureza da rodada 2.** A rodada 2 é um **resultado exploratório sobre as MESMAS
> amostras, após um ajuste de configuração informado pelas falhas do eval**. NÃO é uma
> avaliação independente nem uma reprodução do protocolo original sem alteração — a
> configuração mudou (num_ctx) e a mudança foi informada pelos próprios casos que falharam.
>
> **(3) Delimitação da comparação.** Os denominadores agora coincidem (7 amostras legíveis
> de avaliação), o que permite **comparação descritiva** entre candidatos — desde que
> explicitado que o Qwen rodou em **configuração diferente** (num_ctx=8192) e com **ajuste
> posterior** informado pelas falhas, enquanto os demais candidatos foram medidos uma única
> vez. CER/WER, agregação e resultados por amostra estão preservados e não foram recalculados.
> **CER 0,077 NÃO deve ser lido como "92,3% de acurácia"** (CER é taxa de erro por caractere
> sobre texto normalizado, não acurácia; não há conversão válida para porcentagem de acerto).
> A leitura honesta é: **"melhor resultado observado entre os candidatos nesta coleção e nesta
> configuração"** — não uma conclusão geral sobre capacidade de transcrição de manuscrito em
> português.
>
> **(4) Observabilidade do corpo do erro HTTP — LACUNA AINDA ABERTA.** Verificado nesta
> rodada: o runner v2 **não** corrigiu o gap descrito na §3. O `_post` usa
> `urllib.request.urlopen`, que levanta `HTTPError` antes de ler o corpo; o `except` em
> `executar()` grava apenas `type(exc).__name__ + str(exc)` (ex.: "HTTPError: HTTP Error 400:
> Bad Request"), sem o JSON sanitizado do Ollama. O `num_ctx=8192` apenas evitou o 400 nesta
> coleção; se uma imagem futura exceder 8192, o corpo do erro continuará sendo descartado.
> A correção da observabilidade (ler e registrar `e.read()` sanitizado) permanece **pendente**
> e é item da proposta de próximo experimento, não foi aplicada nesta rodada de consolidação.

## 0. Natureza e preservação da rodada 1

Este documento NÃO altera a rodada 1. Os 36 JSON brutos, o agregado, o ambiente,
as referências, o `RESULTADOS_benchmark_parcial_Amostra_1.md` e o
`RUNNER_SPEC_CONGELADA.md` originais permanecem imutáveis. A reexecução do Qwen
(rodada 2) foi gravada em área separada, sem substituir a rodada 1. Nenhuma imagem,
transcrição ou saída de coleta foi enviada a qualquer agente ou serviço externo — todo
o diagnóstico foi feito localmente contra o Ollama em 127.0.0.1.

## 1. A hipótese original ("limite de payload") estava INCORRETA

O `RESULTADOS_benchmark_parcial_Amostra_1.md` (§3) registrou, como hipótese não
investigada, "limite de tamanho de payload de imagem do Ollama". O diagnóstico
dirigido **refuta** essa hipótese com evidência, por dois fatos:

(a) **O tamanho do arquivo PNG não prediz a falha.** Bytes do arquivo de trabalho vs
resultado do Qwen na rodada 1:

| Amostra | Bytes PNG | Base64 (bytes) | Rodada 1 |
|---|---|---|---|
| MAN-01 (dev) | 189.002 | — | ok |
| MAN-02 | 5.902.508 | 7.870.012 | **ok** |
| MAN-03 | 7.244.820 | 9.659.760 | **ok** |
| MAN-04 | 5.680.906 | 7.574.544 | falha 400 |
| MAN-05 | 7.091.413 | — | falha 400 |
| MAN-06 | 6.770.477 | — | falha 400 |
| MAN-07 | 6.397.417 | — | falha 400 |
| MAN-EVAL-06 | 8.927.611 | — | **ok** (vazio) |
| MAN-EVAL-07 | 9.266.153 | — | falha 400 |

MAN-03 (7,2 MB) PASSOU, sendo maior que quatro das que falharam (MAN-04 5,7 MB,
MAN-06 6,8 MB, MAN-07 6,4 MB). MAN-EVAL-06 (8,9 MB), a segunda maior de todas, PASSOU.
Não há relação monotônica entre bytes e falha. Logo, não é limite de payload de transporte.

(b) **O corpo real do erro — que o runner v1 nunca leu — diz outra coisa.** O v1
capturava apenas `str(exc)` da exceção (resultando em `"HTTPError: HTTP Error 400: Bad
Request"`), descartando o corpo da resposta HTTP. Lendo o corpo real da `HTTPError`
(`e.read()`) numa reprodução local idêntica à do runner, o Ollama retorna:

```
exceed_context_size_error
"request (4131 tokens) exceeds the available context size (4096 tokens), try increasing it"
n_prompt_tokens: 4131, n_ctx: 4096
```

## 2. Causa comprovada: janela de contexto (num_ctx) padrão, não payload

A causa é o **num_ctx padrão do Ollama (4096)** estourado pelos **tokens de visão** que a
imagem gera depois de decodificada — não pelos bytes do arquivo. O número de tokens de
visão depende das dimensões em pixels da imagem (tiles), não do tamanho do PNG; por isso
o tamanho do arquivo não predizia a falha.

Prova determinística — `n_prompt_tokens` de cada amostra (lido do corpo do erro / forçando
`num_ctx=1` para revelar o valor nas que passavam), medido localmente nesta rodada:

| Amostra | n_prompt_tokens | vs 4096 | Rodada 1 |
|---|---|---|---|
| MAN-02 | 4073 | ≤ 4096 | ok |
| MAN-03 | 4084 | ≤ 4096 | ok |
| MAN-EVAL-06 | 4073 | ≤ 4096 | ok (vazio) |
| MAN-EVAL-07 | 4107 | **> 4096** | falha 400 |
| MAN-05 | 4121 | **> 4096** | falha 400 |
| MAN-07 | 4121 | **> 4096** | falha 400 |
| MAN-04 | 4131 | **> 4096** | falha 400 |
| MAN-06 | 4156 | **> 4096** | falha 400 |

A separação é limpa e sem exceção, exatamente na fronteira 4096: todas as que passaram
ficaram em 4073–4084; todas as que falharam, em 4107–4156. A rodada 1 já continha a
assinatura compatível: os JSON brutos das falhas têm `ollama_meta.prompt_eval_duration`
≈ 8,5 s, ou seja, o Ollama **processou a imagem inteira** antes de rejeitar — incompatível
com rejeição de transporte por payload, compatível com verificação de contexto após a
tokenização da visão.

Ambiente observado: Ollama 0.33.3; modelo `qwen2.5vl:3b` (ID `fb90415cde1e`); endpoint
`POST http://127.0.0.1:11434/api/generate`.

## 3. Defeito de observabilidade do runner v1 (registrado, não é a causa do 400)

Independentemente da causa, o runner v1 tinha um defeito que impediu o diagnóstico na
hora: no caminho de erro HTTP, ele só guardava `str(exc)`; para `urllib.error.HTTPError`
isso descarta o corpo da resposta (o JSON `{"error": ...}` do Ollama). A verificação de
`dados.get("error")` em `_post` só ocorre no caminho 200. Por isso o `erro` registrado
na rodada 1 foi genérico ("HTTP Error 400: Bad Request"). Isso é um gap de observabilidade,
não a causa; fica registrado como lição para o runner.

## 4. Correção: exclusivamente de transporte/serialização (classificação de Rafael)

A correção testada é elevar `options.num_ctx` de 4096 para 8192, **sem** redimensionar,
recortar, comprimir ou alterar a imagem (mesmo base64), **sem** mudar o prompt, o modelo
ou a temperatura (=0). Rafael classificou `num_ctx`, para efeito do item 4 do protocolo
desta rodada, como **transporte/serialização** (eleva o teto de contexto para o prompt
caber, não altera como o modelo lê a imagem nem o conteúdo), autorizando a reexecução do
Qwen nas 9 amostras numa rodada nova.

Validação dirigida (local): com `num_ctx=8192` e imagem/prompt/modelo/temperatura
idênticos, as **5 amostras que davam HTTP 400 passaram a retornar HTTP 200 com
transcrição real** (MAN-04, MAN-05, MAN-06, MAN-07, MAN-EVAL-07).

## 5. Runner v2 (congelado)

- Arquivo: `local-nao-versionado/ocr/Amostra_1/rodada2_qwen_num_ctx/bench_runner_v2.py`
  (checksum em `bench_runner_v2.sha256`).
- Única diferença funcional vs v1: `OLLAMA_OPCOES = {"temperature": 0, "num_ctx": 8192}`
  (resto é docstring/comentário). Scoring, prompt, modelo, temperatura e manejo de imagem
  idênticos ao v1.
- Validado: 19/19 testes sintéticos do runner passam no v2; `--dry-run` OK.

## 6. Rodada 2 — reexecução do Qwen nas 9 amostras (eval completo)

Registro bruto: `local-nao-versionado/ocr/Amostra_1/rodada2_qwen_num_ctx/resultados_brutos/`
(agregado + 9 JSON por amostra). A rodada 1 permanece intocada em `resultados_brutos/`.

Agregado eval (7 amostras legíveis; CER/WER menor = melhor):

| Métrica | Rodada 1 | Rodada 2 |
|---|---|---|
| eval_denominador | 2/7 ok, 5 falha_execucao | **7/7 ok** |
| CER médio eval | 0,318 (só 2 amostras, não comparável) | **0,077** |
| WER médio eval | 0,350 (só 2 amostras, não comparável) | **0,168** |
| t_inferência médio | 9,09 s | 9,06 s |

CER/WER por amostra (rodada 2): MAN-02 0,122/0,20 · MAN-03 0,162/0,214 · MAN-04 0,179/0,40
· MAN-05 0,033/0,143 · MAN-06 0,000/0,000 · MAN-07 0,019/0,118 · MAN-EVAL-07 0,021/0,10.
Controle vazio MAN-EVAL-06: saída vazia, zero invenção — não desclassificado. Dev MAN-01:
CER 0,030 (fora do agregado eval).

O CER médio de 0,318 da rodada 1 era condicionado a apenas MAN-02 e MAN-03 e NÃO era
comparável; o de 0,077 da rodada 2 é sobre o eval completo (7/7) e é a primeira medida
comparável do Qwen. Este resultado é **parcial e exploratório**: não promove nenhuma
solução a produção.

## 7. Limites preservados (inalterados por esta rodada)

- **AC-05 NÃO concluído**: MAN-EVAL-07 é legível; não há estímulo ilegível comprovado.
- **Revisão humana cronometrada**: pendente; não estimada por IA.
- Referências conferidas pelo próprio autor (limitação registrada).
- Amostra_2: fora desta rodada.
- `AV-S05B` permanece **parcial**; nenhuma solução promovida; numerador **22/70** inalterado;
  nenhuma decisão arquitetural (`BL-AV-4B-02`/ADR-009) tomada.
- O caminho MANUAL já entregue/homologado (AV-S08B) permanece preservado e independente.

## 8. Recomendação para o próximo experimento (não é decisão de produto)

Com a falha de transporte resolvida, o Qwen2.5-VL:3b é o único candidato com sinal real de
transcrição manuscrita pt-BR nesta coleção (CER 0–0,18 por amostra no eval). Antes de
qualquer decisão arquitetural permanecem pendentes: fechar AC-05 (coletar estímulo ilegível
real), medir o esforço de revisão humana cronometrada, e ampliar para a Amostra_2. A latência
(~9 s/amostra no M5 Pro) não é representativa de hardware de produção (DEC-AV-009 pendente).
