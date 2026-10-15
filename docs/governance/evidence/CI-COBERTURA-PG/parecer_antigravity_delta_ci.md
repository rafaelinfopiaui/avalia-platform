# Parecer independente — Antigravity (revisão do DELTA de CI)

Alvo: delta em `.github/workflows/ci.yml` (step novo "Run PostgreSQL
concurrency tests" no job core) + `escopo_ci_cobertura_postgres.md`.
Branch `ci/cobertura-postgres-concorrencia`, base main cde87cc. Modo:
somente leitura (sem escrita/git).

Revisor: Antigravity CLI (`agy`), modelo "Gemini 3.8 Flash (High)" —
família distinta do orquestrador (Opus) e do executor pretendido (Claude
Code). Nota: o Claude Code estava indisponível (OAuth expirado), então a
implementação foi feita pelo orquestrador e validada por execução local;
a revisão independente do delta coube ao Antigravity. Houve
indisponibilidade transitória de rede (DNS SERVFAIL do endpoint do
Antigravity no resolvedor local) antes desta execução bem-sucedida.

## PARECER: APROVADO COM RESSALVAS (ambas severidade BAIXA, não bloqueantes)

Conclusão do revisor: o delta atende ACD-CI-01..08; o guard anti-skip é
"efetivo e blinda a CI contra falsos-verdes"; suíte SQLite intacta;
bancos protegidos inalcançáveis (dupla proteção: assert no step +
`_PROTECTED_DATABASES` nas fixtures); dois bancos descartáveis isolados
resolvem corretamente a interferência de schema (alembic head p/
test_answer_image_deletion; create_all+drop_all p/
test_manual_transcription). Seletor `-k test_pg_` casa exatamente os 10
casos (5+5); nenhum outro símbolo `test_pg_` no repo. Credenciais: reusa
as do serviço postgres da CI, nenhum segredo novo, sem `set -x`/echo de
senha. Determinismo: `GITHUB_RUN_ID` + DROP IF EXISTS; nome < 63 chars.

Análise de brechas de falso-verde (todas fechadas pelo revisor):
skip→guard pega (skipped!=0); -k vazio→tests=0!=5→exit1 + RC; XML não
gerado→FileNotFoundError+set -e+RC; falhas/erros→guard + RC. set +e
restrito às duas invocações de pytest.

## Ressalvas (incorporadas)

- ACH-01 (baixa): bloco de limpeza final não repetia a asserção
  `"test" in name and name not in {"avalia_dev","postgres"}`. **Incorporada**:
  asserção replicada no loop de DROP (defesa em profundidade).
- ACH-02 (baixa): faltava `rm -f pg_img.xml pg_txn.xml` antes dos pytests
  (XML legado em runner persistente). **Incorporada**: `rm -f` adicionado
  antes de `set +e`.

Pós-incorporação: YAML válido, `bash -n` OK, simulação local fiel =
10 tests / 0 failures / 0 errors / 0 skipped, guard "OK".

## Verificação independente do orquestrador (execução real, não só o parecer)

Simulei a LÓGICA do step contra PostgreSQL local (2 bancos descartáveis
nomeados com "test", alembic no DB_IMG, create_all no DB_TXN): 10 passed,
0 skipped. Guard negativo (sem AVALIA_TEST_POSTGRES_URL): testes ficam
skipped/erro e o guard faz exit 1 — comprovado. Diff do ci.yml: só
adição; step SQLite intacto; nenhum arquivo de produto/teste alterado.
