# Veredito: **REPROVADO**

Há bloqueadores de segurança e correção antes de qualquer ensaio operacional ou execução em `avalia_dev`.

## Achados

### 1. **BLOQUEADOR — guard de banco aceita nomes não pretendidos**
- `core/scripts/av_s02_saneamento_human_reviews.sql:42-50`
- `core/scripts/av_s02_recuperacao_saneamento.sql:26-34`
- `core/scripts/av_s02_validacao_pos_migracoes.sql:9-20`

O padrão SQL:

```sql
v_dbname NOT LIKE 'av_s02_saneamento_%'
```

usa `_` como curinga de um caractere. Portanto, nomes como `avXs02YsaneamentoZteste` podem ser aceitos. Além disso, `avalia_dev` é liberado apenas pelo nome, sem segundo opt-in operacional, apesar de ser o alvo destrutivo real.

**Correção sugerida:**
- Usar comparação regex ancorada, por exemplo `v_dbname ~ '^av_s02_saneamento_[A-Za-z0-9_-]+$'`, ou escapar `_` explicitamente.
- Exigir um segundo guard explícito para `avalia_dev`, via variável/sessão com valor exato e específico da operação.
- Fixar `search_path` e qualificar objetos como `public.human_reviews`; atualmente o catálogo verifica `public`, mas o DDL e DML usam nomes não qualificados.

---

### 2. **BLOQUEADOR — equivalência pode produzir falso positivo e a escolha do vencedor não é provada**
- `core/scripts/av_s02_saneamento_human_reviews.sql:272-301`
- `core/scripts/av_s02_saneamento_human_reviews.sql:303-319`
- `core/scripts/av_s02_saneamento_human_reviews.sql:399-412`

A normalização converte scores com:

```sql
to_char(score::numeric, 'FM999999990.00')
```

Isso arredonda para duas casas. Valores distintos, como `1.001` e `1.004`, podem ser classificados como equivalentes. Isso não corresponde exatamente a `_review_is_equivalent`, que compara `Decimal` sem esse arredondamento (`core/app/main.py:711-727`).

Além disso, o script afirma preservar o menor `created_at`, mas:
- não compara os três timestamps;
- não prova que `31d31b5c-...` continua sendo `ORDER BY created_at, id LIMIT 1`;
- os timestamps das duas linhas removidas podem mudar para datas anteriores e o script ainda pode arquivar a linha errada e confirmar o `COMMIT`.

**Correção sugerida:**
- Normalizar score como valor `numeric`, sem `to_char(... .00)`.
- Validar ausência de `criterion_id` repetido antes de construir a representação normalizada.
- Assertar explicitamente, sob lock, que o ID vencedor é o primeiro por `created_at, id`.
- Preferencialmente validar os três registros completos contra o inventário nominal autorizado.

---

### 3. **BLOQUEADOR — assertions de `AuditEvent` não provam preservação**
- `core/scripts/av_s02_saneamento_human_reviews.sql:423-435`
- `core/scripts/av_s02_validacao_pos_migracoes.sql:55-68`
- Expectativa documental: `docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md:269-282`

O pós-check do saneamento valida somente:
- IDs;
- `resource_type`;
- `action`;
- `resource_id`.

Ele não valida `actor_id`, `before_json`, `after_json` nem `created_at`. A validação pós-migração acrescenta `actor_id`, mas ainda ignora os três últimos campos. Logo, essas colunas podem ser alteradas e as assertions continuarem verdes.

O script realmente não contém DML explícito contra `audit_events`, mas a afirmação “intocados” não é provada pelas assertions.

**Correção sugerida:**
- Sob lock, capturar os três registros completos antes da operação e comparar depois por igualdade integral/symmetric `EXCEPT`, ou comparar todas as colunas com um baseline autorizado.
- Bloquear escrita concorrente em `audit_events` durante essa comparação.
- Incluir nominalmente `actor_id`, `before_json`, `after_json` e `created_at` também na validação pós-migração.

---

### 4. **ALTA — locks deixam `human_reviews_superseded` e `audit_events` expostas**
- `core/scripts/av_s02_saneamento_human_reviews.sql:98-221`
- `core/scripts/av_s02_saneamento_human_reviews.sql:235-237`
- `core/scripts/av_s02_saneamento_human_reviews.sql:307-351`
- `core/scripts/av_s02_recuperacao_saneamento.sql:36-51`

`SHARE ROW EXCLUSIVE` é um modo adequado para impedir `INSERT/UPDATE/DELETE` concorrente em `human_reviews`. Entretanto:
- somente `human_reviews` é bloqueada;
- a tabela de arquivo é validada/criada fora da transação principal;
- não há lock em `human_reviews_superseded`;
- não há lock em `audit_events`.

Uma sessão concorrente pode alterar a cópia arquivada depois da comparação coluna-a-coluna. Alterações em campos arquivados que preservem `job_id` e `superseded_reason` podem passar pelo pós-check.

A janela entre o `COMMIT` e a migração também permanece protegida apenas pela instrução externa “writers parados”; o script não verifica nem mantém uma trava através dessa janela.

**Correção sugerida:**
- Incluir o DDL na mesma transação quando possível.
- Bloquear também `public.human_reviews_superseded` e `public.audit_events`, em ordem fixa.
- Manter controle operacional verificável dos writers ou usar uma trava consultiva/orquestração mantida durante saneamento e migração.
- Qualificar todos os objetos com `public.`.

---

### 5. **ALTA — recuperação não prova restauração completa**
- `core/scripts/av_s02_recuperacao_saneamento.sql:41-96`
- `core/scripts/av_s02_recuperacao_saneamento.sql:98-136`

A recuperação confirma apenas que as duas linhas arquivadas voltaram. Não confirma:
- existência e conteúdo integral da vencedora;
- total exato de três linhas para o job antes do `COMMIT`;
- ausência de outros grupos inesperados;
- preservação dos `AuditEvent`.

Assim, se o “problema detectado” incluir perda ou alteração da vencedora, o script pode confirmar uma recuperação incompleta e ainda declarar estado “idêntico ao pré-saneamento” nas linhas 134-136.

Também:
- em falha antes do `COMMIT` principal, a tabela de arquivo recém-criada permanece, porque seu DDL já foi confirmado em autocommit (`av_s02_saneamento_human_reviews.sql:94-96,98-221`);
- no cenário pós-constraint, `alembic downgrade e1b02279b1a5` reverte também todas as revisões descendentes aplicadas até `head`, não somente a constraint. Isso precisa ser tratado explicitamente como rollback de toda a cadeia, com efeitos verificados.

**Correção sugerida:**
- Antes do `COMMIT` de recuperação, validar as três linhas completas, vencedor, timestamps, IDs, equivalência e auditoria.
- Assertar no catálogo que a unique constraint foi removida antes do `INSERT`.
- Documentar e validar os efeitos de downgrade de `a9f4c2e71b06` e `c4a8b2d91e37`, não apenas a remoção de `7b1d6d853f20`.
- Se o requisito for retorno integral ao estado anterior, incluir a criação da tabela de arquivo na transação principal ou documentar claramente o drift de schema residual.

O procedimento documental de restore completo em `docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md:329-339` contém cautelas adequadas — checksum, restore em banco vazio e autorização — mas não corrige as lacunas do rollback compensatório.

---

### 6. **ALTA — scripts de mutação não são idempotentes**
- `core/scripts/av_s02_saneamento_human_reviews.sql:255-270`
- `core/scripts/av_s02_recuperacao_saneamento.sql:41-51`

Em banco já saneado:
- o saneamento encontra uma linha, não três, e aborta;
- portanto é fail-closed e não corrompe dados, mas não é idempotente.

Em banco já recuperado:
- a recuperação tende a falhar por conflito de PK ao reinserir as duas linhas.

**Correção sugerida:**
- Reconhecer explicitamente dois estados válidos:
  1. pré-saneamento exato → executar;
  2. pós-saneamento exato → no-op bem-sucedido.
- Qualquer estado parcial ou divergente deve continuar abortando.
- Aplicar a mesma máquina de estados ao script de recuperação.

---

### 7. **ALTA — validação da versão Alembic pode passar com versão ausente**
- `core/scripts/av_s02_validacao_pos_migracoes.sql:70-73`

Se `SELECT version_num INTO v_version FROM alembic_version` não retornar linha, `v_version` fica `NULL`. A condição:

```sql
IF v_version <> 'a9f4c2e71b06' THEN
```

também resulta em `NULL`, não em `TRUE`, e não levanta exceção. Portanto a assertion pode passar sem provar que o banco está no head esperado.

**Correção sugerida:**
- Assertar exatamente uma linha em `alembic_version`.
- Usar `IS DISTINCT FROM 'a9f4c2e71b06'`.

---

### 8. **MÉDIA — assertion “único grupo duplicado” ocorre tarde demais**
- `core/scripts/av_s02_saneamento_human_reviews.sql:239-301`
- `core/scripts/av_s02_saneamento_human_reviews.sql:391-397`

O comentário diz reconfirmar “o único grupo duplicado”, mas o bloco pré-escrita consulta somente o job nominal. Outros grupos duplicados são detectados apenas no pós-check, depois do `INSERT` e `DELETE`.

A transação será revertida, portanto não há saneamento confirmado, mas a assertion não cumpre literalmente a promessa de abortar antes da escrita.

**Correção sugerida:** sob o lock, assertar antes do `INSERT` que o conjunto completo de grupos duplicados é exatamente o grupo nominal esperado.

## Pontos corretos observados

- O `INSERT` no arquivo, a comparação das sete colunas de origem e o `DELETE` estão na mesma transação (`av_s02_saneamento_human_reviews.sql:235-440`).
- A cópia é verificada antes do `DELETE`.
- Divergências levantam exceção e, com `ON_ERROR_STOP`, impedem o `COMMIT`.
- O modo `SHARE ROW EXCLUSIVE` utilizado em `human_reviews` conflita corretamente com DML concorrente.
- Nenhum dos scripts de saneamento contém DML explícito contra `audit_events`.
- Diagnóstico e validação são essencialmente somente leitura, exceto pelas lacunas de assertion descritas.

## Escopo realizado

- Li integralmente os quatro scripts solicitados.
- Li a proposta integrada atual de 359 linhas e a comparação GOV-006.
- Reconstruí em memória e li as 676 linhas da proposta histórica usando o delta integral/reversível publicado; nenhuma operação Git foi executada.
- Confirmei a branch lendo `.git/HEAD`: `chore/preparacao-avalia-dev-av-s04`.
- Não conectei a banco algum e não executei SQL.
- **Arquivos criados ou modificados: nenhum.**