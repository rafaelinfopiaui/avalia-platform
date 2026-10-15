---
id: "inventario_publicacao_av-s05b_2026-10-15"
tema: "AV-S05B manuscrito — inventário final para publicação (código experimental / documentação / material local fora do Git)"
data: "2026-10-15 (America/Sao_Paulo)"
estado: "INVENTÁRIO — proposta de publicação; decisão de Git pendente de Rafael. Sem stage/commit/push/merge nesta rodada."
---

# Inventário final — proposta de publicação (branch `docs/av-s05b-precisao-metodologica-diagnostico-http400`)

Branch documental no checkout principal (sem worktree). HEAD imutável `970eb8c`; nada staged;
sem commit/push/merge. A decisão de publicação é de Rafael, sobre o pacote consolidado.

## A. Documentação de governança (rastreada — MODIFICADA, candidata a publicação)

Arquivos já versionados em `main`, modificados nesta sprint (notas datadas, sem reescrever
histórico):
- `docs/governance/executive_technical_dashboard.md` (linha "Última execução" + §13 + nota de precisão)
- `docs/governance/snapshots/latest_execution.md` (ponteiro EXEC-04 + nota de precisão)

## B. Documentação e evidência NOVA (untracked — candidata a publicação)

Snapshot:
- `docs/governance/snapshots/snapshot_EXEC-2026-10-15-04_diagnostico_http400_qwen_av-s05b.md`

Em `docs/governance/evidence/AV-S05B/amostras/manuscrito/`:

**B.1 Documentação (markdown):**
- `DIAGNOSTICO_HTTP400_qwen2.5vl_2026-10-15.md` — diagnóstico + nota de reconciliação
- `PRECISAO_METODOLOGICA_2026-10-15.md` — consolidação de precisão metodológica
- `NOTA_limitacao_latencia_rodada2_2026-10-15.md` — limitação de latência da rodada 2
- `SPEC_correcao_runner_v3_2026-10-15.md` — especificação da correção v3 (antes de implementar)
- `CONSOLIDACAO_runner_v3_2026-10-15.md` — consolidação do v3 + resolução dos achados + 4 estados
- `SPEC_CANDIDATA_Amostra_2_2026-10-15.md` — especificação **candidata** do próximo experimento
- `PROPOSTA_proximo_experimento_2026-10-15.md` — proposta de confirmação independente

**B.2 Código experimental (runner + testes; NÃO é código de produto):**
- `bench_runner_v3.py` — runner experimental revisado (C1–C5 + 2 achados de borda resolvidos)
- `bench_runner_v3.sha256` — checksum do v3 (`cc9a0a79…548a8`)
- `test_runner_v3_mock.py` — testes sintéticos/mockados (56 casos)

**B.3 Diffs e pareceres (auditoria):**
- `DELTA_runner_v1_v2.diff`, `DELTA_runner_v2_v3.diff`, `DELTA_runner_v3_fix_borda.diff`,
  `DELTA_testes_v3_fix_borda.diff`, `DIFF_governanca_rastreados_2026-10-15.diff`
- `parecer_antigravity_runner_v3_2026-10-15.txt` — revisão do delta v2→v3 (APROVADO c/ ressalvas)
- `parecer_antigravity_runner_v3_fix_borda_2026-10-15.txt` — revisão do fix de borda (CONCORDO,
  apontou o bug any/all)
- `parecer_antigravity_precisao_metodologica_2026-10-15.txt` — revisão da precisão metodológica

**B.4 Já existentes da rodada 1 (preservados, não reescritos):**
- `RUNNER_SPEC_CONGELADA.md`, `MANIFESTO_Amostra_1.md`, `PREPARACAO_candidatos.md`,
  `CHECKSUMS_referencias_*.sha256`, `parecer_antigravity_runner.txt` (path saneado),
  `parecer_codex_scoring.txt` (path saneado)

> **EXCLUÍDOS da publicação por decisão de Rafael (2026-10-15):**
> `INVENTARIO_Amostra_1.md` e `RESULTADOS_benchmark_parcial_Amostra_1.md` **NÃO** são publicados
> — contêm frases reais das referências/transcrição da coleta. Permanecem apenas locais. As
> menções a esses nomes em documentos publicados (ex.: DIAGNOSTICO cita RESULTADOS como
> proveniência) são referências textuais ao nome do arquivo, não vazam conteúdo. Os `.sha256` de
> referência listados acima NÃO contêm texto das frases (só hash + nome), por isso permanecem
> publicáveis.

> **Observação de publicação:** as imagens PNG em `docs/governance/evidence/AV-S05B/amostras/`
> (eval/, dev/, referências) são material de coleta. Se a publicação Git for autorizada, a
> decisão sobre incluir ou não as imagens da coleta no repositório é de Rafael — recomenda-se
> **não** publicar as fotos/referências originais (dado da coleta), apenas a documentação,
> o código experimental e os pareceres. O `.gitignore` do AV-S05B deve ser revisado antes de
> qualquer `git add`.

## C. Material LOCAL — deve permanecer FORA do Git (por construção)

Em `local-nao-versionado/ocr/Amostra_1/` (área não-versionada):
- Runners `bench_runner.py` (v1), `rodada2_qwen_num_ctx/bench_runner_v2.py`,
  `rodada3_runner_v3/bench_runner_v3.py` (cópia de trabalho; a versão de evidência está em B.2)
- Resultados brutos: `resultados_brutos/` (36 da rodada 1), `rodada2_qwen_num_ctx/resultados_brutos/`
  (9 da rodada 2) — **dados da coleta, fora do Git**
- `trabalho_png/`, `referencias/`, `originais/`, `auditoria/` — **fotos e referências da coleta**
- `venv_bench/` — ambiente virtual
- Artefatos de execução do Claude Code: `rodada3_runner_v3/claude_v3_*.json/.log` — logs de
  orquestração, **não publicar**

## D. Estados (resumo — ver CONSOLIDACAO_runner_v3 §topo)

1. Runner **tecnicamente revisado**: `bench_runner_v3.py` (revisado, não congelado).
2. Especificação experimental **candidata**: `SPEC_CANDIDATA_Amostra_2` (em aberto).
3. Configuração **congelada antes de medir**: ainda **não existe** (depende de escopo/parâmetros
   fixados e versionados antes da medição; independe de Git).
4. **Publicação Git**: pendente de decisão de Rafael (não impede, por si só, o congelamento futuro).

## Limites preservados

`AV-S05B` parcial; **AC-05** e **revisão humana cronometrada** pendentes; numerador **22/70**;
**ADR-009 sem promoção**. Sem stage/commit/push/merge, inferências, instalações, alterações no
produto ou em bancos protegidos nesta rodada.
