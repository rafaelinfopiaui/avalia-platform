# REPROVADO

## Achados bloqueadores

1. **CRÍTICA — guard do seed não valida o banco efetivamente selecionado**  
   **Arquivo:** `core/scripts/seed_academic_multi_question_demo.py:69-75`  
   O guard procura substrings na URL completa:
   ```python
   if "avalia_dev" in lowered or "av_s02_saneamento_" not in lowered:
   ```
   Assim, uma URL apontando para outro banco pode passar se o marcador aparecer em usuário, senha, host ou query string, por exemplo `...?application_name=av_s02_saneamento_x`. O script deve extrair o database name da URL e validá-lo com regex ancorada.

2. **ALTA — estado pós-saneamento não é validado integralmente**  
   **Arquivo:** `core/scripts/av_s02_saneamento_human_reviews.sql:185-221`  
   `is_post` verifica apenas:
   - uma linha ativa e presença da vencedora;
   - presença dos dois IDs arquivados;
   - ausência de duplicatas ativas.

   Não valida conteúdo integral das duas linhas arquivadas, `superseded_reason`, nem ausência de outras linhas arquivadas para o mesmo `job_id`. Uma linha arquivada corrompida, mas com o ID esperado, resulta em `SANITATION_ALREADY_COMPLETE_VALID_NOOP`.

3. **ALTA — estado “já recuperado” não prova as três linhas restauradas**  
   **Arquivo:** `core/scripts/av_s02_recuperacao_saneamento.sql:46-58`  
   O ramo `recovered` aceita apenas três linhas com o `job_id` e ausência dos dois IDs nominais no arquivo. Ele não comprova que as outras duas linhas ativas são os IDs esperados nem seus campos e timestamps. A assertion integral das três linhas, em `:70-82`, é pulada pelo `\quit`. Portanto, vencedor e auditoria corretos mais duas linhas arbitrárias podem produzir `RECOVERY_ALREADY_COMPLETE_VALID_NOOP`.

4. **ALTA — idempotência do seed aceita conteúdo divergente como válido**  
   **Arquivo:** `core/scripts/seed_academic_multi_question_demo.py:88-144`  
   `validate_existing()` verifica existência e alguns vínculos, mas não valida grande parte do conteúdo determinístico, incluindo:
   - email, role e `is_active` do usuário;
   - nomes e códigos;
   - role/`active` do vínculo do professor;
   - título/status da avaliação;
   - enunciados, respostas e pontuações;
   - versão/publicação das rubricas;
   - nomes, descrições e pontuações dos critérios.

   Com todos os IDs presentes e links corretos, conteúdo divergente retorna `DEMO_SEED_ALREADY_VALID`, contrariando o comportamento fail-closed documentado.

5. **MÉDIA — diagnóstico depende do `search_path` externo**  
   **Arquivo:** `core/scripts/av_s02_diagnostico_human_reviews.sql:9-66`  
   Não há `SET search_path`, e `human_reviews`/`audit_events` são usados sem `public.` nas linhas 23, 52 e 60. O diagnóstico pode consultar objetos de outro schema ou falhar conforme a sessão, enquanto os demais SQLs fixam o `search_path` e qualificam tabelas.

6. **MÉDIA — cenário de falha pós-cópia não exercita o script real**  
   **Arquivo:** `core/scripts/run_avalia_dev_update_dry_run.sh:231-261`  
   O cenário D executa uma transação sintética própria, não `av_s02_saneamento_human_reviews.sql`. Portanto, ele comprova a atomicidade genérica do PostgreSQL, mas não que o script real permaneça atômico após alterações em suas assertions, locks e DDL.

## Pontos verificados como corretos

- Regex ancorada e opt-in adicional para `avalia_dev` nos SQLs operacionais.
- Equivalência de scores por `numeric`, sem arredondamento.
- Detecção de `criterion_id` duplicado.
- Verificação do único grupo duplicado antes do `INSERT`.
- Escolha explícita do vencedor por `ORDER BY created_at, id`.
- Auditoria com `before_json`/`after_json` e demais campos sob lock.
- DDL do arquivo na mesma transação do saneamento.
- Locks das três tabelas na mesma ordem em saneamento e recuperação.
- `alembic_version` exige exatamente uma linha e usa `IS DISTINCT FROM`.
- Runner possui happy path, conflito, recuperação pré/pós-constraint, retomada de índice e teste de nome lookalike.
- Constraint de `human_reviews` é recusada antes da recuperação.

## Escopo da revisão

- Li integralmente os seis arquivos solicitados.
- Não executei banco nem comandos Git.
- Nenhum arquivo foi criado ou modificado.