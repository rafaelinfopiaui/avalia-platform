---
id: "spec_candidata_amostra_2"
tema: "AV-S05B eixo manuscrito — especificação CANDIDATA do próximo experimento (Amostra_2)"
data: "2026-10-15 (America/Sao_Paulo)"
estado: "CANDIDATA — NÃO congelada (depende do runner v3 e de revisão independente pendentes; depende de decisão de Rafael). Não autoriza coleta nem inferência."
---

# Especificação CANDIDATA — Amostra_2 (confirmação independente)

Status: **candidata**. Não será declarada congelada enquanto houver (a) runner v3 com
implementação/revisão pendentes e (b) decisão de Rafael. **Não autoriza** coletar, instalar
ou inferir. Serve para revisão e refinamento.

Princípio de independência: a configuração é congelada ANTES de ver qualquer amostra da
Amostra_2; **nenhum** parâmetro pode ser ajustado a partir dos resultados da Amostra_2 e
depois a rodada ser chamada de "avaliação independente" (seria o mesmo viés *post-hoc* da
rodada 2 da Amostra_1). A Amostra_1 e a Amostra_2 **não** são misturadas num mesmo agregado;
MAN-EVAL-07 da Amostra_1 não é substituída.

## 1. Parâmetros por candidato (congelados antes da coleta)

Opções declaradas e versionadas por candidato (registradas no ambiente da execução):

| Candidato | Parâmetros (exemplo a congelar) |
|---|---|
| tesseract | `-l por`; CLI, sem processo residente |
| easyocr | `Reader(['pt'], download_enabled=False)`; `readtext(detail=0)` |
| ollama:moondream:v2 | `temperature=0`, `seed=<fixo>`, `num_ctx=<default do modelo>` (NÃO 8192) |
| ollama:qwen2.5vl:3b | `temperature=0`, `seed=<fixo>`, `num_ctx=8192` (declarado, não ad hoc) |

- `num_ctx` por candidato (correção C3 do v3): o 8192 do Qwen NÃO se aplica aos demais.
- `seed` fixo e `temperature=0` declarados por candidato; o relatório deve registrar que
  isso **reduz** a variação mas **não garante determinismo absoluto** (C4).
- Prompt VLM: o mesmo da spec congelada da Amostra_1 (reuso, não reinvenção).

## 2. Limites e comportamento em falha

- Teto de contexto é **limite declarado**, não alvo móvel: se uma amostra exceder o
  `num_ctx` declarado, o resultado é **`falha_execucao`** com erro diagnóstico sanitizado
  (C1/C5) — **sem** aumento automático de contexto, resize, recompressão ou retry oculto.
- Falhas permanecem no denominador (visíveis como `N/M ok, k falha_execucao`), nunca
  excluídas silenciosamente; distinção mantida entre falha ≠ abstenção ≠ saída vazia ≠
  qualidade (herança do protocolo da Amostra_1).
- Corpo de erro HTTP capturado, truncado e sanitizado (sem imagem/base64/credenciais).

## 3. Medição de carga vs inferência

- `t_carga_s` medido uma vez por candidato, **já com** a configuração de contexto final
  (C2) — a recarga de contexto não contamina a primeira `t_inferencia_s`.
- `t_inferencia_s` por amostra, com o motor já carregado.
- Latência rotulada como "hardware local, não representativo de produção" (DEC-AV-009
  pendente).

## 4. Controle ilegível genuíno + referência humana independente

- Incluir pelo menos um estímulo **comprovadamente ilegível** (não apenas vazio), para
  fechar **AC-05** (hoje em aberto — MAN-EVAL-07 da Amostra_1 é legível e não serve).
- A ilegibilidade deve ser atestada por **avaliação humana cega** (revisor sem acesso ao
  texto original), registrada como evidência.
- As referências da Amostra_2 devem ter procedência independente do autor sempre que
  possível; a limitação "referência conferida pelo próprio autor" da Amostra_1 deve ser
  evitada ou, se inevitável, explicitada.

## 5. Protocolo de revisão humana cronometrada

- Medir o esforço de revisão humana com cronômetro, pelo procedimento já previsto no
  protocolo da Amostra_1 (§12), com revisor humano real — **não** estimado por IA.
- Registrar tempo por amostra e condições (quem revisou, quando, com/sem conhecimento do
  original), como métrica separada de CER/WER.

## 6. Pré-condições de engenharia (do runner)

- Runner **v3** (correções C1–C5) implementado, revisado de forma independente e com testes
  mockados passando — ver `SPEC_correcao_runner_v3_2026-10-15.md`. A Amostra_2 só roda com
  o runner v3 congelado.
- Observabilidade do erro HTTP ativa (C1) para que qualquer falha seja diagnosticável sem
  reprodução manual.

## 7. Entregáveis da execução da Amostra_2 (quando autorizada)

- Configuração/parâmetros congelados e versionados (com checksum) antes da coleta.
- Resultados da Amostra_2 em rodada própria, **separada** da Amostra_1.
- AC-05 fechado por controle ilegível com avaliação cega; revisão humana cronometrada medida.
- Só então: comparação descritiva entre coleções/configurações; eventual insumo para
  `BL-AV-4B-02`/ADR-009 — ainda sem promover solução.

## Limites preservados

`AV-S05B` parcial; `22/70`; `ADR-009` sem promoção; nenhuma decisão arquitetural; sem
coleta/inferência/instalação autorizadas por este documento.
