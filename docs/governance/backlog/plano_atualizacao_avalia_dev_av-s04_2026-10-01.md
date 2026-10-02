# Plano consolidado — atualização de `avalia_dev` (migrações + saneamento + demonstração)

Status: **PLANO. NADA FOI EXECUTADO.** Documento de leitura e planejamento
local, conforme autorizado. Nenhuma escrita em `avalia_dev`, nenhum
saneamento, nenhuma migração aplicada, nenhuma ação Git/remota, nenhuma
promoção de baseline. Todos os comandos abaixo são propostos, não
executados.

Data de elaboração: 2026-10-01 (-03:00).
Base: `main@9ab6e43b99e87d9114416fcb776cbfb0903b0935` (PR #9 integrado,
homologado por Rafael, `DEC-AV-029`).

---

## 1. Cadeia Alembic completa — verificada, não presumida

Verificação real, não apenas leitura dos arquivos:

```
$ cd core && .venv/bin/python -m alembic -c alembic.ini heads
a9f4c2e71b06 (head)

$ .venv/bin/python -m alembic -c alembic.ini history
c4a8b2d91e37 -> a9f4c2e71b06 (head), add question position and assessment clone provenance
7b1d6d853f20 -> c4a8b2d91e37, add academic structure
e1b02279b1a5 -> 7b1d6d853f20, add unique human review job id
<base> -> e1b02279b1a5, schema inicial avalia
```

Confirmado: **cadeia linear única, um único head, sem branches nem merge
points**. A ordem de aplicação é determinada pelos `down_revision`
declarados em cada arquivo (não pela ordem alfabética/cronológica dos
nomes de arquivo, que poderia enganar):

| Ordem | Revision | down_revision (depende de) | Arquivo | O que faz |
|---|---|---|---|---|
| 1 | `e1b02279b1a5` | `None` (base) | `e1b02279b1a5_schema_inicial_avalia.py` | Cria o schema inicial completo: `users`, `assessments`, `audit_events`, `questions`, `answers`, `rubrics`, `correction_jobs`, `rubric_criteria`, `ai_executions`, `human_reviews`, `criterion_scores`, e os enums `role`, `assessmentstatus`, `jobstatus`, `reviewdecision`. |
| 2 | `7b1d6d853f20` | `e1b02279b1a5` | `7b1d6d853f20_add_unique_human_review_job_id.py` | Adiciona `UniqueConstraint uq_human_reviews_job_id` em `human_reviews(job_id)`. **Antes de criar a constraint, executa uma query de diagnóstico (`GROUP BY job_id HAVING COUNT(*) > 1`) e, se encontrar qualquer duplicata, levanta `RuntimeError` e aborta sem tocar em nenhum dado.** Não apaga, altera nem escolhe entre duplicatas — isso é delegado a um procedimento de saneamento separado (seção 3). |
| 3 | `c4a8b2d91e37` | `7b1d6d853f20` | `c4a8b2d91e37_add_academic_structure.py` | Cria a estrutura acadêmica completa: `organizations`, `courses`, `disciplines`, `course_disciplines`, `class_groups`, `students`, `enrollments`, `professor_class_links`; adiciona `assessments.class_group_id` (nullable) + FK `fk_assessments_class_group_id`. Downgrade bloqueia (`RuntimeError`) se houver qualquer dado dependente em qualquer uma dessas tabelas. |
| 4 | `a9f4c2e71b06` | `c4a8b2d91e37` | `a9f4c2e71b06_add_question_position_and_clone.py` | Adiciona `questions.position` (ordenação, `UniqueConstraint uq_questions_assessment_position` via `CREATE UNIQUE INDEX CONCURRENTLY` + `ADD CONSTRAINT ... USING INDEX`), `questions.created_at` (backfill heurístico via `AuditEvent` de criação da avaliação pai), e `assessments.cloned_from_id` (self-FK nullable, proveniência de clonagem). Idempotente/recuperável após falha parcial (detecta checkpoints compatíveis vs. objetos homônimos incompatíveis). |

**Dependência real confirmada:** `7b1d6d853f20` precede `c4a8b2d91e37` e
`a9f4c2e71b06` não porque seja "mais importante", mas porque é
literalmente o que cada arquivo declara em `down_revision` — a ordem
acima é a única sequência executável; `alembic upgrade head` a partir de
`e1b02279b1a5` aplica exatamente essas 3 migrações, nessa ordem, sem
alternativa.

**Estado atual real de `avalia_dev`** (lido agora, não presumido):

```
$ psql -d avalia_dev -Atc "SELECT version_num FROM alembic_version;"
e1b02279b1a5
```

`avalia_dev` está parado na migração 1 de 4. As migrações `7b1d6d853f20`,
`c4a8b2d91e37` e `a9f4c2e71b06` estão versionadas em `main`, revisadas,
testadas (localmente contra PostgreSQL 16 isolado — ver pacotes de
evidência de AV-S02, AV-S03 e AV-S04) mas **nenhuma delas foi aplicada**
ao ambiente operacional.

---

## 2. Reconciliação do plano de saneamento — duas versões, revisável

### 2.1 Proveniência das duas versões

- **Versão integrada em `main`** (359 linhas):
  `docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md`
  — já publicada no histórico Git, mas **continua como proposta não
  aprovada** (o próprio documento declara isso no cabeçalho: "PROPOSTA
  PARA APROVAÇÃO. NADA FOI EXECUTADO.").
- **Versão local de 676 linhas**, encontrada em checkout anterior (branch
  `docs/av-s02-encerramento-planos-operacionais`, HEAD `7f18ec3`), nunca
  commitada à parte — **mais extensa e mais defensiva** que a integrada.
  Comparação já registrada em GOV-006:
  `docs/governance/evidence/GOV-006/comparacao_proposta_saneamento_676.md`
  e `docs/governance/evidence/GOV-006/diff_proposta_saneamento_676_vs_integrada.txt`
  (603 linhas de diff).

**Nenhuma das duas versões foi aprovada por Rafael.** Este documento não
presume aprovação de nenhuma delas; reconcilia as diferenças materiais
para que a decisão seja tomada com o delta explícito, não com um texto
genérico.

### 2.2 Diferenças materiais entre as duas versões (preservadas, não resolvidas aqui)

| # | Tema | Versão integrada (359L) | Versão local (676L) | O que a decisão de Rafael precisa resolver |
|---|---|---|---|---|
| 1 | Inventário de auditoria | Lista os 3 `AuditEvent` com `id`/`actor_id`/`action`/`created_at` apenas | Acrescenta `before_json`/`after_json` de cada evento | Confirmar os valores de `before_json`/`after_json` contra `avalia_dev` antes de aceitar como evidência (não foram revalidados nesta sessão) |
| 2 | Formulação de "preservação" | Diz "nenhuma linha é apagada" (impreciso — há `DELETE`, só que precedido de cópia) | Corrige explicitamente: é cópia-então-`DELETE` na mesma transação, nunca perda | A versão local é **mais correta tecnicamente**; recomendo adotar essa formulação |
| 3 | Escopo do `LOCK TABLE` | Implica que o lock protege até a migração | Corrige: `LOCK TABLE` é liberado no `COMMIT`; a proteção real entre saneamento e migração é a continuidade dos **writers parados**, não o lock | A versão local está tecnicamente correta (fato do PostgreSQL); recomendo adotar |
| 4 | Modo de execução `psql` | Não especifica | Exige `psql -v ON_ERROR_STOP=1`, proíbe `--single-transaction` (conflitaria com o `COMMIT` explícito do script) | Decisão operacional objetiva a favor da versão local — evita execução parcial silenciosa |
| 5 | DDL da tabela de arquivo | `CREATE TABLE` direto (falharia se a tabela já existisse com schema diferente, de forma não controlada) | Bloco `DO $$` condicional: cria se não existe; se existe, valida colunas/tipos/nulabilidade/PK/índice via `information_schema`/`pg_catalog` e aborta com `RAISE EXCEPTION` em qualquer divergência | A versão local é estritamente mais segura; recomendo adotar |
| 6 | Assertions | Comentários SQL narrativos ("esperado: 2 linhas") que dependem de inspeção humana do resultado | Blocos `DO $$ ... RAISE EXCEPTION ...` que abortam a transação automaticamente em caso de divergência | A versão local é executável e auto-verificável; a integrada depende de revisão manual do operador em cada passo — risco maior de erro humano sob pressão de janela de manutenção |
| 7 | Comparação pré-`DELETE` | Não compara explicitamente a cópia contra o original antes de apagar | Compara **todas as colunas**, linha a linha, antes do `DELETE` | A versão local fecha uma lacuna real (cópia poderia silenciosamente divergir do original por erro de digitação do SQL) |
| 8 | Pós-checks e rollback compensatório | Consultas `SELECT` com comentário "esperado: X" | Blocos `DO $$` com `RAISE EXCEPTION` comparando contagens e comparando colunas linha a linha entre `human_reviews` e `human_reviews_superseded` | A versão local é mais rigorosa |
| 9 | Verificação HTTP de contexto | Menciona junto dos pós-checks SQL, como se fizesse parte da mesma transação | Explicitamente posicionada **depois** do `COMMIT` e da migração, como chamada HTTP real separada | A versão local evita a confusão de misturar verificação de aplicação dentro de uma transação SQL |

### 2.3 Recomendação objetiva (não é aprovação — é recomendação técnica)

Os 9 pontos acima são, sem exceção, **a versão local sendo mais precisa
ou mais defensiva que a integrada** — nenhum deles introduz um
comportamento diferente da intenção original (ainda é: preservar por
cópia, nunca perder dado; mover exatamente 2 linhas equivalentes;
auditoria intocada). Recomendo que a versão a ser efetivamente executada
(se e quando Rafael autorizar) seja a **versão local de 676 linhas**,
formalizada nesta ocasião como a versão canônica substituindo a
integrada de 359 linhas — mas essa substituição em si é uma decisão que
cabe a Rafael, não uma conclusão automática deste documento.

**Pendências explícitas antes de qualquer execução** (herdadas de GOV-006,
reconfirmadas aqui):
- revisão SQL independente dos blocos `DO $$`, por agente diferente do
  autor;
- validação completa do script em banco restaurado isolado, nunca
  diretamente em `avalia_dev` (ver seção 3.3);
- confirmação dos valores de `before_json`/`after_json` contra a fonte
  operacional real (`avalia_dev`), não assumidos do texto da proposta;
- decisão explícita de Rafael sobre retenção/expurgo futuro de
  `human_reviews_superseded` (nenhuma das duas versões decide isso — é
  escopo deliberadamente fora de ambas);
- decisão explícita de Rafael: adotar a versão local como canônica, ou
  manter a integrada, ou pedir ajustes adicionais.

---

## 3. Backup, duplicatas, interrupção de escritas, migrações, validação, recuperação

Sequência técnica única, consolidando os dois planos (adotando os pontos
mais defensivos da versão local, conforme seção 2.3) com as migrações
`c4a8b2d91e37` e `a9f4c2e71b06` (que a proposta original de saneamento,
escrita antes de AV-S03/AV-S04 existirem, não cobria).

### 3.1 Estado real inventariado agora (não presumido do texto da proposta)

```
$ psql -d avalia_dev -Atc "SELECT job_id, COUNT(*) FROM human_reviews GROUP BY job_id HAVING COUNT(*) > 1;"
4f56a10b-3a44-4df5-9047-adef7546a3c0|3
```

Confirma: **o mesmo e único grupo duplicado** documentado em 2026-09-24
continua intacto, sem alteração, nesta data. Nenhum novo grupo duplicado
apareceu.

```
$ psql -d avalia_dev -Atc "SELECT 'users', COUNT(*) FROM users UNION ALL SELECT 'assessments', COUNT(*) FROM assessments UNION ALL SELECT 'questions', COUNT(*) FROM questions UNION ALL SELECT 'human_reviews', COUNT(*) FROM human_reviews UNION ALL SELECT 'audit_events', COUNT(*) FROM audit_events;"
users|4
assessments|10
questions|10
human_reviews|18
audit_events|36
```

Banco pequeno (8.4 MB em disco), todos dados fictícios de demonstração —
confirma que o risco de blast radius de qualquer erro é limitado, mas
isso não dispensa nenhuma das proteções abaixo.

### 3.2 Interrupção de escritas — barreira primária não-invasiva, escalonamento documentado

**Revisão de 2026-10-01 (pós-aprovação da preparação por Rafael, 2ª
correção):** a versão anterior desta seção tratava `REVOKE` de privilégios
como a prova técnica padrão de interrupção de escritas. Rafael corrigiu
isso: **`REVOKE` é, ele próprio, uma alteração operacional em
`avalia_dev`** (DCL, muda o estado do banco) e portanto pertence ao mesmo
bloco de autorização de P4 — não é uma ação "grátis" de preparação que
possa ser tratada como padrão antes de P4 ser concedido. Além disso,
`REVOKE` sozinho não é uma garantia automática: não afeta o dono da
tabela, não afeta superusuários, não afeta privilégio herdado por
associação de papel (`GRANT role_b TO app_role`), não afeta `PUBLIC`, e
não interrompe uma conexão/transação já aberta antes da revogação.
Reescrito abaixo para preferir parar os writers conhecidos e **verificar**
a ausência de atividade como mecanismo primário; `REVOKE` passa a ser uma
camada adicional opcional, só usada com os privilégios originais, o
alcance exato e a restauração exata documentados.

**Ordem correta: identificar e travar os writers ANTES do backup final
(seção 3.3), não depois.** O backup só tem valor como ponto de retomada
confiável se nada escrever no banco entre o backup e o fim da operação.

1. **Inventariar todo processo com capacidade de escrita** antes de tocar
   em qualquer coisa:
   ```sql
   SELECT pid, usename, application_name, client_addr, state, query,
          backend_start, query_start
   FROM pg_stat_activity
   WHERE datname = 'avalia_dev';
   ```
   Classificar cada conexão: processo Core/uvicorn conhecido, worker/
   background task conhecido, sessão administrativa do operador (`psql`
   interativo rodando este próprio procedimento), ou **desconhecida**.
   Qualquer conexão desconhecida com potencial de escrita **aborta a
   operação** até ser identificada e explicitamente autorizada ou parada.

2. **Mecanismo primário — parar os processos de aplicação na origem e
   verificar a ausência de atividade** (não inferir, confirmar): parar
   (`systemctl stop`/equivalente) o processo Core/uvicorn, scheduler/
   worker, qualquer cron ou script batch com capacidade de
   `INSERT`/`UPDATE`/`DELETE` em `avalia_dev`. Depois de cada parada,
   reconsultar `pg_stat_activity` (consulta do passo 1) até que **nenhuma**
   conexão do papel/processo de aplicação apareça — não apenas confiar que
   o comando de parada retornou sucesso (processos podem demorar a fechar
   conexões, ou manter um pool de conexões vivo mesmo parados).

3. **Encerrar explicitamente qualquer conexão residual inesperada**, em
   vez de presumir que vai fechar sozinha:
   ```sql
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE datname = 'avalia_dev' AND pid = <PID identificado no passo 1/2>;
   ```
   Repetir o passo 1 depois de cada `pg_terminate_backend` para confirmar
   que a conexão realmente caiu (um processo supervisionado pode
   reconectar automaticamente — se isso acontecer, é sinal de que o
   processo de origem não foi de fato parado no passo 2, e a operação deve
   abortar até a causa ser corrigida).

4. **`REVOKE` como camada adicional opcional, não como padrão** — só
   considerar se os passos 2-3 não derem confiança operacional suficiente
   (ex.: processo de aplicação gerenciado por infraestrutura fora do
   controle direto do operador nesta janela). Se usado, tratar como parte
   do bloco de execução de P4 (não uma ação preparatória antecipável) e
   seguir **obrigatoriamente** esta sequência, nunca um `REVOKE` isolado:

   a. **Capturar a baseline exata de privilégios ANTES de revogar algo**
      (nunca assumir um `GRANT` genérico para restaurar depois; usar
      `LEFT JOIN LATERAL` para que uma tabela sem ACL explícita — `relacl
      IS NULL`, estado default do PostgreSQL quando nenhum `GRANT`/`REVOKE`
      jamais foi emitido nela — continue aparecendo na saída em vez de
      desaparecer silenciosamente):
      ```sql
      SELECT c.relname, c.relowner::regrole AS owner,
             a.grantee::regrole AS grantee, a.privilege_type
      FROM pg_class c
      LEFT JOIN LATERAL aclexplode(c.relacl) a ON true
      WHERE c.relname IN ('human_reviews','audit_events','questions','assessments','users')
        AND c.relnamespace = 'public'::regnamespace;
      -- grantee/privilege_type NULL para uma linha = a tabela não tem ACL
      -- explícita (valem os defaults do dono); registrar isso também —
      -- restaurar para "sem ACL explícita" significa não emitir nenhum
      -- GRANT de volta para essa tabela, e sim confirmar ausência de ACL.
      ```
      Registrar esta saída literal no relatório de execução real — é o
      único texto-fonte válido para a restauração (passo g), não uma
      suposição de que o `GRANT` original era exatamente
      `INSERT, UPDATE, DELETE`.

   b. **Confirmar que `<APP_DB_ROLE>` não é dono das tabelas afetadas**
      (`owner` do passo a) — o dono tem privilégio implícito completo
      independente de qualquer `REVOKE`. Se for dono, `REVOKE` não tem
      efeito algum sobre esse papel; a barreira real precisa vir
      inteiramente dos passos 2-3 (parar o processo), não de `REVOKE`.

   c. **Confirmar que `<APP_DB_ROLE>` não é superusuário**
      (`SELECT rolsuper FROM pg_roles WHERE rolname = '<APP_DB_ROLE>'`) —
      superusuário ignora toda checagem de privilégio.

   d. **Enumerar a árvore de associação de papéis** (`pg_auth_members`)
      para `<APP_DB_ROLE>`: se ele herda de outro papel que também tem
      `INSERT`/`UPDATE`/`DELETE` nessas tabelas, revogar diretamente de
      `<APP_DB_ROLE>` não remove o privilégio herdado — é preciso revogar
      do papel intermediário também, ou usar `REVOKE ... FROM <role> CASCADE`
      com plena consciência de quem mais é afetado por esse papel
      intermediário (nunca `CASCADE` sem antes listar explicitamente todos
      os papéis que dependem dele).

   e. **Confirmar que `PUBLIC` não tem o privilégio** nas mesmas tabelas
      (visível na mesma saída do passo a, como uma linha com `grantee`
      correspondente ao pseudo-papel `PUBLIC`) — um `REVOKE` em
      `<APP_DB_ROLE>` não revoga de `PUBLIC`.

   f. **Emitir o `REVOKE`** somente depois de a-e confirmarem que ele terá
      efeito real:
      ```sql
      REVOKE INSERT, UPDATE, DELETE ON
        public.human_reviews, public.audit_events, public.questions,
        public.assessments, public.users
      FROM <APP_DB_ROLE>;
      ```
      Isto **não substitui** os passos 2-3 — é uma camada adicional sobre
      processos já parados e conexões já encerradas, nunca a única
      barreira. Uma conexão/transação que já estava aberta **antes** do
      `REVOKE` pode já ter passado pela checagem de privilégio referente a
      uma operação em andamento; por isso o passo 3
      (`pg_terminate_backend` de toda conexão não identificada) deve
      sempre vir antes do `REVOKE`, não depois.

   g. **Restauração exata ao final** (não um `GRANT` genérico chutado):
      reconstruir o `GRANT` a partir da baseline literal capturada no
      passo a — para cada linha da baseline com `privilege_type` não nulo,
      reemitir exatamente aquele privilégio para aquele `grantee`:
      ```sql
      -- Exemplo, assumindo que a baseline do passo a mostrou
      -- INSERT/UPDATE/DELETE concedidos a <APP_DB_ROLE> nestas 5 tabelas
      -- (substituir pelos privilégios/grantees realmente capturados —
      -- nunca assumir este exemplo como valor universal):
      GRANT INSERT, UPDATE, DELETE ON
        public.human_reviews, public.audit_events, public.questions,
        public.assessments, public.users
      TO <APP_DB_ROLE>;
      -- Se alguma tabela da baseline não tinha ACL explícita (grantee
      -- NULL no passo a), NÃO emitir GRANT para ela — restaurar "sem ACL
      -- explícita" significa não ter ACL, não conceder e depois revogar.
      ```
      E **revalidar** executando a mesma consulta do passo a de novo,
      comparando campo a campo (`grantee`, `privilege_type`, inclusive as
      linhas com `NULL` esperado) contra a baseline original antes de
      liberar a aplicação.

5. **Monitoramento contínuo durante toda a janela** (independente de
   `REVOKE` ter sido usado ou não — este é o sinal de detecção real):
   ```sql
   SELECT schemaname, relname, n_tup_ins, n_tup_upd, n_tup_del
   FROM pg_stat_user_tables
   WHERE relname IN ('human_reviews','audit_events','questions','assessments','users');
   -- capturar um snapshot ANTES de iniciar a barreira (baseline) e comparar
   -- a cada checagem, em intervalo curto. Contadores são agregados e podem
   -- ter atraso: não identificam autor nem provam ausência de escrita.
   -- Saneamento e migrações autorizados também alteram estes contadores.
   -- Conciliar variações com as etapas e sessões autorizadas; variação
   -- inesperada exige pausa e investigação (seção 3.8, Estado 0).
   ```

6. Manter a barreira (processos parados e confirmadamente sem conexão +
   `REVOKE` ativo e documentado, se usado + monitoramento) **continuamente**
   desde antes do backup final (3.3) até a aplicação de `a9f4c2e71b06`
   (última das 4 migrações, contando o saneamento como passo 0) e a
   verificação completa da seção 3.7 — não apenas até o saneamento.

7. Só então: se `REVOKE` foi usado, restaurar exatamente a baseline
   (passo 4.g); liberar os processos de aplicação; confirmar reconexão
   normal com uma operação de baixo risco (ex.: leitura seguida de no-op)
   antes de declarar a janela encerrada.

### 3.3 Backup final (imediatamente antes da primeira escrita operacional)

**O ensaio em PostgreSQL isolado já realizado (seção 7 da reconciliação,
`ALL_DRY_RUN_SCENARIOS_GREEN`) usou um backup capturado em 2026-10-01
10:18 para fins de ENSAIO. Esse backup não substitui o backup final desta
seção** — qualquer escrita real em `avalia_dev` exige um backup capturado
*depois* que a barreira de escritas da seção 3.2 estiver comprovadamente
ativa, para garantir que o ponto de retomada reflita o estado exato no
instante em que as escritas pararam.

```bash
# Executar SOMENTE depois que a seção 3.2 (passos 1-3, mecanismo primário,
# e passo 4 se REVOKE adicional foi usado) estiver confirmada.
DUMP=/caminho/fora_do_repo/avalia_dev_pre_migracao_av-s04_$(date +%Y%m%d_%H%M%S).dump
pg_dump -Fc -d avalia_dev -f "$DUMP"
shasum -a 256 "$DUMP" > "$DUMP.sha256"
pg_restore --list "$DUMP" > "$DUMP.contents.txt"
```

Critério de prosseguir: `pg_dump` e `pg_restore --list` retornam exit 0;
checksum registrado no relatório de execução real (não neste documento,
que é só planejamento).

Export adicional, independente do dump completo, específico da tabela
afetada pelo saneamento:

```bash
psql -d avalia_dev -c "\copy (SELECT * FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0') TO '/caminho/fora_do_repo/human_reviews_pre_saneamento.csv' WITH CSV HEADER"
```

### 3.4 Validação de restauração testada, em ambiente isolado, antes de tocar `avalia_dev`

Esta validação roda **duas vezes com propósitos distintos**: (a) já foi
executada nesta rodada preparatória contra um backup de ensaio, como parte
do `ALL_DRY_RUN_SCENARIOS_GREEN` registrado na seção 7; (b) deve ser
repetida contra o **backup final** da seção 3.3, pois esse backup é capturado
num instante diferente (depois da barreira de escritas confirmada) e nunca
foi, ele próprio, restaurado e validado — validar o backup de ensaio não
comprova a integridade do backup final.

```bash
# cluster PostgreSQL isolado e descartável, mesmo padrão já usado
# nas validações locais de AV-S02/AV-S03/AV-S04
initdb -D /tmp/av_pg_update_avalia_dev_test -U postgres --auth=trust
pg_ctl -D /tmp/av_pg_update_avalia_dev_test -o "-p 55433 -k /tmp/av_pg_update_avalia_dev_test" -l /tmp/av_pg_update_avalia_dev_test/server.log start
createdb -h /tmp/av_pg_update_avalia_dev_test -p 55433 -U postgres avalia_dev_restore_test
pg_restore -h /tmp/av_pg_update_avalia_dev_test -p 55433 -U postgres -d avalia_dev_restore_test "$DUMP"

# confirmar que o restore reproduz exatamente o estado atual
psql -h /tmp/av_pg_update_avalia_dev_test -p 55433 -U postgres -d avalia_dev_restore_test -c \
  "SELECT COUNT(*) FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0';"
# esperado: 3

# Todo o restante desta seção (3.5 a 3.7) já foi exercitado neste banco
# restaurado isolado durante o ensaio da seção 7 (ALL_DRY_RUN_SCENARIOS_GREEN).
# Antes da execução real, o backup FINAL exige revalidação própria: este
# restore reflete o estado PRÉ-saneamento (3 duplicatas, version_num =
# e1b02279b1a5) — rodar os pós-checks de 3.7 diretamente aqui FALHARIA por
# definição (eles esperam 0 duplicatas e version_num = a9f4c2e71b06).
# Portanto: repetir a SEQUÊNCIA COMPLETA 3.5 → 3.6 → 3.7 neste restore do
# backup final antes de considerá-lo validado — não apenas os checks de
# 3.7 isolados. Só depois dessa sequência completa passar neste restore é
# que o backup final está confirmado como íntegro e restaurável.
```

Ao final da validação isolada:
```bash
pg_ctl -D /tmp/av_pg_update_avalia_dev_test stop
rm -rf /tmp/av_pg_update_avalia_dev_test
```

### 3.5 Tratamento das duplicatas (saneamento, antes de `7b1d6d853f20`)

Pré-requisito objetivo: `7b1d6d853f20` aborta com `RuntimeError` se
encontrar qualquer `job_id` com mais de uma `HumanReview` — portanto o
saneamento do único grupo duplicado conhecido (`4f56a10b-...`, 3 linhas,
confirmadas equivalentes byte-a-byte em 2026-09-24 e não revalidadas
nesta sessão) é **obrigatório antes** de `alembic upgrade head` conseguir
avançar além de `e1b02279b1a5`.

Procedimento proposto (adotando os pontos defensivos da versão local —
seção 2.3 — sujeito à decisão de Rafael sobre qual versão adotar como
canônica):

1. Script de diagnóstico somente leitura (confirma que o único grupo
   duplicado continua sendo exatamente o esperado, com os 3 IDs
   nominais, e que é semanticamente equivalente — não conflitante — em
   `reviewer_id`, `decision`, `final_total`, `final_scores_json`
   normalizado, `justification`). Se qualquer outro grupo aparecer, ou
   se este grupo deixar de ser equivalente, a operação para e exige
   decisão manual de Rafael.
2. Criar/validar `human_reviews_superseded` (DDL condicional e validado
   contra `information_schema`/`pg_catalog`, não `CREATE TABLE` cego).
3. Transação explícita: `BEGIN` → `LOCK TABLE human_reviews IN SHARE ROW
   EXCLUSIVE MODE` → reconfirmar diagnóstico sob lock → `INSERT` das 2
   linhas não-vencedoras (`8a9c2ba6-...`, `9459489c-...`) em
   `human_reviews_superseded` → comparação integral coluna-a-coluna da
   cópia contra o original ainda ativo → só então `DELETE` das 2 linhas
   da tabela ativa → pós-checks (seção 3.7, itens a-d) ainda dentro da
   transação → `COMMIT`.
4. Nenhum `AuditEvent` é tocado — preservados como estão, sem FK direta
   com `human_reviews` (associação lógica/temporal por `resource_id`).
5. A linha vencedora (`31d31b5c-...`, menor `created_at`) permanece com
   o mesmo `id` em `human_reviews` — nenhuma referência futura à chave
   primária é afetada.

**Script versionável proposto** (já existe localmente, não commitado):
`core/scripts/av_s02_saneamento_human_reviews.sql`, revisado em 3 rodadas
de revisão independente (REPROVADO → REPROVADO → **APROVADO** final) e
ensaiado com sucesso no banco isolado da seção 3.4
(`ALL_DRY_RUN_SCENARIOS_GREEN`, seção 7).

### 3.6 Aplicação das migrações

Somente depois que o saneamento (3.5) confirmar 0 grupos duplicados
restantes (ver pós-check "a" abaixo):

```bash
cd core
DATABASE_URL="<URL real de avalia_dev>" .venv/bin/python -m alembic -c alembic.ini upgrade head
```

Isso aplica, em sequência, `7b1d6d853f20` → `c4a8b2d91e37` → `a9f4c2e71b06`
(a cadeia completa da seção 1, a partir do estado atual `e1b02279b1a5`).
Todas as 3 já foram validadas localmente em PostgreSQL 16 isolado (ver
`docs/governance/evidence/AV-S02-postgres-isolado/`,
`docs/governance/evidence/AV-S03/`, e
`docs/governance/evidence/AV-S04/pacote-execucao-local/validate_migration_recovery.sh`
— este último também cobre especificamente a recuperação de
`a9f4c2e71b06` após falha parcial, incluindo o cenário de índice
`INVALID` por `CREATE UNIQUE INDEX CONCURRENTLY` interrompido).

Se qualquer uma falhar, **não liberar writers** — seguir o plano de
recuperação (seção 3.8), que distingue falha antes/depois de cada
`COMMIT` individual.

### 3.7 Validações posteriores (antes de considerar a operação concluída)

**(a) Saneamento — nenhum grupo duplicado resta:**
```sql
SELECT job_id, COUNT(*) FROM human_reviews GROUP BY job_id HAVING COUNT(*) > 1;
-- esperado: 0 linhas
```

**(b) Linha vencedora intacta:**
```sql
SELECT * FROM human_reviews WHERE id = '31d31b5c-05c7-4206-b2ff-43b2eda14026';
-- esperado: 1 linha, dados idênticos ao inventário original
```

**(c) Linhas arquivadas preservadas:**
```sql
SELECT id, job_id, superseded_reason, superseded_at FROM human_reviews_superseded
WHERE job_id = '4f56a10b-3a44-4df5-9047-adef7546a3c0';
-- esperado: 2 linhas
```

**(d) Auditoria intocada (nominal, não por contagem ampla):**
```sql
SELECT id, actor_id, action, resource_type, resource_id, before_json, after_json, created_at
FROM audit_events
WHERE id IN ('b12db6d4-3b44-42ca-aa9a-99748fc4b982', '4f737eab-3ba0-40af-8738-ae847377ba34', 'cad4d910-8c91-4a7e-9714-266fac3f7ee6')
ORDER BY created_at;
-- esperado: exatamente esses 3 IDs, conteúdo idêntico ao inventário pré-operação
```

**(e) Constraints das migrações aplicadas:**
```sql
SELECT conname FROM pg_constraint WHERE conrelid = 'human_reviews'::regclass AND conname = 'uq_human_reviews_job_id';
-- esperado: 1 linha
SELECT conname FROM pg_constraint WHERE conrelid = 'questions'::regclass AND conname = 'uq_questions_assessment_position';
-- esperado: 1 linha
SELECT conname FROM pg_constraint WHERE conrelid = 'assessments'::regclass AND conname = 'fk_assessments_class_group_id';
-- esperado: 1 linha
SELECT conname FROM pg_constraint WHERE conrelid = 'assessments'::regclass AND conname = 'fk_assessments_cloned_from_id';
-- esperado: 1 linha
SELECT version_num FROM alembic_version;
-- esperado: a9f4c2e71b06
```

**(f) Contexto de aplicação funcional** (HTTP real, fora de qualquer
transação SQL, depois do `COMMIT` e das migrações):
`GET /v1/correction-jobs/4f56a10b-3a44-4df5-9047-adef7546a3c0/context`
deve continuar retornando `human_review` com os dados da linha vencedora.

**(g) Avaliações legadas de questão única continuam acessíveis** (AC-13
de AV-S04): `GET /v1/assessments/{id}` para as 10 avaliações já
existentes deve continuar retornando `200`, com `position=1` em cada
questão legada e conteúdo preservado.

Somente depois que **todos** os itens (a)-(g) passarem, liberar a
aplicação para escrita.

### 3.8 Matriz de estados — diagnóstico, retomada e recuperação

**Revisão de 2026-10-01 (pós-aprovação da preparação por Rafael):** a
versão anterior desta seção descrevia 4 cenários de falha isolados, sem
diagnóstico explícito de "em qual estado estou agora" e sem tratar
explicitamente o índice concorrente interrompido como estado próprio.
Reescrita como matriz: para cada estado possível, como diagnosticar que
você está nele, qual ação é testada/segura, e quando usar restauração do
backup em vez de recuperação por script.

**Princípio geral, válido para todos os estados:** nenhuma recuperação
aplica downgrade automaticamente. Antes de qualquer `alembic downgrade`,
confirmar explicitamente a precondição de segurança de cada migração (a
própria migração já bloqueia com `RuntimeError` se houver dado dependente
— ver coluna "Precondição" abaixo) e preservar qualquer dado novo que não
seja produzido pela própria migração/saneamento. Se a precondição não for
atendida, ou se houver dúvida sobre a origem de algum dado presente,
**parar e tratar como incidente** (não forçar downgrade).

| Estado | Como diagnosticar | Ação testada | Precondição antes de downgrade | Quando usar restauração do backup em vez de script |
|---|---|---|---|---|
| **0. Escrita detectada durante a janela (barreira da seção 3.2 falhou)** | Atividade de escrita não autorizada confirmada, ou variação nos contadores sem explicação pelas operações autorizadas; contadores agregados isoladamente não identificam a origem | Parar imediatamente toda e qualquer operação desta seção 3 em andamento; não prosseguir para backup/saneamento/migração até identificar a origem da escrita e confirmar que a barreira está efetivamente ativa (reconfirmar que os processos de aplicação estão parados e sem conexão — passos 2-3; se `REVOKE` foi usado, reconfirmar e reemitir conforme passo 4) | N/A — este estado é sempre tratado como incidente, nunca como recuperação automática | Sempre registrar como incidente; decisão de Rafael sobre se a escrita detectada invalida o backup já capturado |
| **1. Antes do saneamento (estado original)** | `SELECT version_num FROM alembic_version` = `e1b02279b1a5` **e** `human_reviews_superseded` não existe (ou existe vazia para o job) **e** `SELECT COUNT(*) FROM human_reviews WHERE job_id=...` = 3 | Estado seguro para iniciar ou reiniciar do zero. Nenhuma ação de recuperação necessária | — | Não aplicável (nada foi alterado ainda) |
| **2. Falha durante o saneamento, antes do `COMMIT` da transação de saneamento** | A sessão psql que rodou `av_s02_saneamento_human_reviews.sql` terminou com erro e a conexão caiu antes de qualquer `COMMIT` visível no log | `ROLLBACK` automático do próprio PostgreSQL (nenhuma ação manual: `INSERT` em `human_reviews_superseded` e `DELETE` em `human_reviews` estavam na mesma transação, nunca commitada). Diagnosticar de novo com o Estado 1 para confirmar o retorno ao original | — | Não deveria ser necessária; se a reconfirmação do Estado 1 falhar de forma inesperada, tratar como incidente antes de prosseguir |
| **3. Saneamento commitado, mas nenhuma migração aplicada ainda (`version_num = e1b02279b1a5`)** | `version_num` ainda `e1b02279b1a5` **e** `human_reviews_superseded` contém as 2 linhas nominais **e** `human_reviews` tem 1 linha ativa para o job | Rollback compensatório testado: `av_s02_recuperacao_saneamento.sql` (ensaiado `RECOVERY_AFTER_SANITATION_BEFORE_CONSTRAINT_GREEN`, idempotente em reexecução). Reinsere as 2 linhas a partir do arquivo, com prova de conteúdo campo a campo antes de remover do arquivo | Nenhuma migração aplicada ainda — não há downgrade envolvido neste estado | Alternativa se o script de recuperação falhar ou o estado não bater exatamente com a máquina de estados do script (ele aborta fail-closed em vez de "consertar"): restaurar o backup final em banco isolado, inspecionar manualmente, só então decidir |
| **4. `7b1d6d853f20` aplicada (`uq_human_reviews_job_id` já existe), `c4a8b2d91e37` e `a9f4c2e71b06` não aplicadas** | `version_num = 7b1d6d853f20` | Para desfazer o saneamento a partir daqui: **primeiro** `alembic downgrade e1b02279b1a5` (remove a constraint que bloquearia a reinserção das 2 linhas arquivadas), **depois** `av_s02_recuperacao_saneamento.sql` (ensaiado `RECOVERY_AFTER_CONSTRAINT_GREEN`) | Confirmar `version_num = 7b1d6d853f20` antes do downgrade; confirmar que nenhuma tabela de `c4a8b2d91e37` existe ainda (ela não foi aplicada, então não há dado novo a preservar nesta migração específica) | Se o downgrade de `7b1d6d853f20` falhar por qualquer motivo não previsto no ensaio: não insistir — restaurar backup final em isolado e investigar antes de tocar `avalia_dev` de novo |
| **5. Falha em `c4a8b2d91e37` (estrutura acadêmica), depois de `7b1d6d853f20` já aplicada e saneamento intacto** | `version_num` preso em estado intermediário ou erro reportado durante `c4a8b2d91e37`; `7b1d6d853f20` confirmadamente aplicada | `alembic downgrade 7b1d6d853f20`. **Precondição que a própria migração já impõe e deve ser reconfirmada manualmente antes de confiar nela**: a migração de downgrade bloqueia com `RuntimeError` se houver qualquer dado em `organizations`, `courses`, `disciplines`, `course_disciplines`, `class_groups`, `students`, `enrollments`, `professor_class_links` ou `assessments.class_group_id` não nulo — como os writers estão parados (seção 3.2) desde antes do saneamento, não deveria existir dado novo além do que a própria migração interrompida criou, mas **confirmar isso explicitamente com um `SELECT COUNT(*)` em cada uma dessas tabelas antes do downgrade**, não assumir | Precondição acima falhou (existe dado inesperado): não forçar o downgrade — isso descartaria dado real sem explicação. Tratar como incidente, investigar a origem do dado, só então decidir entre correção manual pontual ou restauração do backup |
| **6. Índice concorrente interrompido em `a9f4c2e71b06` (`CREATE UNIQUE INDEX CONCURRENTLY` commitou DDL parcial fora de transação)** | `SELECT indisvalid FROM pg_index WHERE indexrelid = 'ix_questions_assessment_position'::regclass` = `false`, **ou** a migração reporta erro mencionando o nome do índice; `version_num` ainda não avançou para `a9f4c2e71b06` | **Não fazer downgrade.** Reexecutar `alembic upgrade head` diretamente — a migração já é desenhada para detectar o índice `INVALID` residual, descartá-lo e recriar do zero (ensaiado em `validate_migration_recovery.sh`, cenário "B recovery-invalid-index", `B GREEN`, nesta mesma rodada: `DURATION_MIGRATION_CONCURRENT_INDEX_RECOVERY_SECONDS=2.577`) | Nenhuma — este é o único estado em que a ação testada é reexecutar para frente, não downgrade | Se a reexecução também falhar (ex.: dado real viola a futura `UNIQUE(assessment_id, position)`, não apenas índice órfão): parar, investigar o dado conflitante antes de qualquer nova tentativa — nunca descartar dado para forçar o índice a passar; se a investigação não identificar rapidamente a causa, restaurar o backup final em isolado, comparar o conflito contra o estado do backup, e só então decidir no ambiente real |
| **7. `a9f4c2e71b06` aplicada, mas algum checkpoint helper (`_ensure_not_null`/`_ensure_unique_constraint`/`_ensure_clone_provenance`) aborta por objeto incompatível (nome reutilizado com definição diferente da esperada)** | Erro explícito de `RuntimeError` mencionando "Incompatible checkpoint" no log da migração | **Parar — isto não é um estado de retomada automática.** Um objeto com o nome esperado pelo script mas definição diferente é evidência de drift não previsto (ex.: criado manualmente fora do fluxo desta preparação). Investigar manualmente a origem antes de decidir entre ajustar o script, renomear o objeto conflitante, ou restaurar o backup | — | Recomendado como primeira opção segura: restaurar o backup final em isolado, comparar o objeto conflitante contra o que o backup tinha, só então decidir no ambiente real |
| **8. Cadeia concluída (`version_num = a9f4c2e71b06`), pós-checks 3.7 ainda não confirmados** | `version_num = a9f4c2e71b06` mas alguma das verificações (a)-(g) da seção 3.7 ainda não rodou ou não passou | **Não liberar writers.** Rodar os pós-checks (3.7) completos antes de qualquer decisão. Se algum pós-check falhar apesar de `version_num` correto, tratar como incidente (a migração reportou sucesso mas o estado de dados diverge do esperado) — não é um cenário coberto pelos scripts de recuperação, que assumem estados intermediários conhecidos, não um "sucesso aparente divergente" | — | Se a causa da divergência não for identificável rapidamente: restaurar o backup final em isolado, comparar estado esperado vs. obtido, decidir com Rafael antes de tentar de novo em `avalia_dev` |
| **9. Cadeia concluída e todos os pós-checks (a)-(g) confirmados** | Todos os itens de 3.7 passaram | Liberar writers: reiniciar os processos de aplicação parados (passo 2) e, se `REVOKE` foi usado como camada adicional (passo 4), restaurar exatamente a baseline de privilégios capturada (passo 4.g), ambos conforme seção 3.2 passo 7. Encerrar a janela. Nenhuma recuperação necessária | — | Não aplicável — este é o estado de sucesso final |

**Restauração completa do backup — quando nenhuma linha da matriz acima se
aplica com segurança, não apenas "último recurso" genérico:**
1. validar SHA-256 do `.dump` contra o checksum registrado no backup final
   (seção 3.3);
2. confirmar, usando o monitoramento da seção 3.2 (passo 5), que nenhuma
   escrita ocorreu depois do backup — se houve, a restauração descartaria
   essa escrita e exige decisão de incidente por Rafael antes de prosseguir;
3. restaurar primeiro em banco vazio isolado (`createdb` + `pg_restore
   --exit-on-error`), validar contagens/FKs/constraints contra o inventário
   da seção 3.1;
4. só restaurar `avalia_dev` mediante nova autorização explícita separada,
   com conexões bloqueadas e banco destino recriado;
5. registrar comandos/saídas exatas em snapshot de incidente real (não
   neste documento de planejamento).

Em nenhum estado desta matriz os writers são liberados antes do Estado 9
ser alcançado e confirmado.

---

## 4. Configuração para demonstrar estrutura acadêmica e múltiplas questões

Distinção explícita, como exigido: **código integrado** (já em `main`,
sempre disponível em qualquer deploy a partir deste commit) vs.
**funcionalidade disponível no ambiente** (depende de configuração E das
migrações da seção 1 estarem aplicadas em `avalia_dev`).

### 4.1 Código já integrado em `main` (independente de `avalia_dev`)

- Estrutura acadêmica completa (AV-S03): modelos, endpoints, autorização
  por vínculo professor↔turma — `core/app/models.py`, `core/app/main.py`.
- Múltiplas questões por avaliação (AV-S04): `position`, clonagem,
  endpoints de coleção, limites — mesmo arquivos, mais
  `core/alembic/versions/a9f4c2e71b06_*.py`.
- Frontend completo para ambos: `frontend/src/pages/AssessmentEditorPage.tsx`
  (edição de N questões, seleção de turma), `AnswerPage.tsx`, `ReviewPage.tsx`.

Este código **já está presente** em qualquer checkout de `main` a partir
de `9ab6e43`, independentemente do estado de `avalia_dev`.

### 4.2 Funcionalidade disponível no ambiente — depende de 3 fatores independentes

| Fator | Estado atual de `avalia_dev` | O que falta |
|---|---|---|
| **1. Migrações aplicadas** | `e1b02279b1a5` apenas | `7b1d6d853f20`, `c4a8b2d91e37`, `a9f4c2e71b06` pendentes (seção 1) — sem elas, as tabelas de estrutura acadêmica e as colunas `position`/`cloned_from_id` **não existem fisicamente no banco**; qualquer tentativa de usar essas funcionalidades contra `avalia_dev` hoje falharia com erro de coluna/tabela inexistente |
| **2. Flag de backend `ACADEMIC_MODULE_ENABLED`** | Não configurada no ambiente de `avalia_dev` (default do código: `false`, `core/app/config.py:18-20`) | Definir `ACADEMIC_MODULE_ENABLED=true` no `.env`/ambiente do processo Core que aponta para `avalia_dev`, **depois** das migrações da seção 1 estarem aplicadas (a flag liga a exigência de `class_group_id`; sem as tabelas, ativá-la antes quebraria a criação de avaliação) |
| **3. Flag de frontend `VITE_ACADEMIC_MODULE_ENABLED`** | Documentada em `frontend/.env.example` como `true`, mas é **build-time** (Vite) — precisa estar definida no ambiente de build do frontend que serve a demonstração, não apenas documentada | Build do frontend com `VITE_ACADEMIC_MODULE_ENABLED=true` no momento do `npm run build` (ou `.env` lido pelo `vite dev`, se a demonstração rodar em modo dev) |

**Débito técnico já registrado e aceito** (`DEBT-AV-012`): as duas flags
(`ACADEMIC_MODULE_ENABLED` no backend, `VITE_ACADEMIC_MODULE_ENABLED` no
frontend) são configurações independentes sem fonte única de verdade —
se só uma for ativada, a UI pode permitir submissão que o backend
rejeita, ou exigir turma quando o backend não exigiria. Para a
demonstração, **as duas devem ser setadas com o mesmo valor** (`true`),
manualmente, até que a solução estrutural recomendada (endpoint de
capacidades consultado pelo frontend) seja implementada — não prioritária
hoje, conforme `DEC-AV-027`.

### 4.4 Ativação (P5) — procedimento separado de P4, detalhado

**Revisão de 2026-10-01:** descrito aqui em detalhe operacional porque P5
é uma decisão e um procedimento distintos de P4 (execução das migrações),
conforme já estabelecido na seção 5. P5 só pode começar depois que P4
estiver concluído e os pós-checks da seção 3.7 tiverem passado — as 4
migrações precisam existir fisicamente antes de a flag de backend exigir
`class_group_id`.

1. **Configuração do backend.** Definir `ACADEMIC_MODULE_ENABLED=true` no
   `.env` (ou variável de ambiente equivalente do processo gerenciado) do
   processo Core que aponta para `avalia_dev`. O valor é lido uma vez por
   processo em `get_settings()` (`core/app/config.py:18-20`, decorado com
   `@lru_cache`) — não é hot-reload.

2. **Reinício do backend, obrigatório.** Por causa do `@lru_cache` em
   `get_settings()`, a flag só passa a valer depois que o processo Core é
   reiniciado (não basta editar o `.env` com o processo already rodando).
   Reiniciar o serviço (`systemctl restart`/equivalente, ou matar e
   recriar o processo uvicorn gerenciado) e confirmar com:
   ```bash
   curl -s http://<host-core>/v1/health
   ```
   seguido de uma chamada a qualquer endpoint que dependa da flag (ex.:
   tentativa de criar avaliação sem `class_group_id`, que deve passar a
   ser rejeitada se a flag exigir turma) para confirmar que o processo
   reiniciado está de fato lendo o novo valor, não apenas que subiu.

3. **Rebuild do frontend com a flag de build-time.** `VITE_ACADEMIC_MODULE_ENABLED`
   é lida em tempo de build pelo Vite (`frontend/.env.example`) — definir
   em `.env`/ambiente do processo de build e **rebuildar** (não basta
   reiniciar um servidor estático servindo um build antigo):
   ```bash
   cd frontend
   VITE_ACADEMIC_MODULE_ENABLED=true npm run build
   # ou, se a demonstração roda em modo dev (vite dev), garantir que o
   # mesmo valor está no .env lido pelo dev server e reiniciar o dev server
   ```
   Publicar/servir o novo `dist/` no lugar do build anterior. Confirmar
   via inspeção do bundle servido (ou de uma tela que só aparece com a
   flag ativa) que o build publicado é de fato o novo, não um cache de
   CDN/proxy do build antigo.

4. **Teste funcional pós-ativação, com as duas flags confirmadamente
   coerentes** (mesmo valor `true` em backend e frontend — `DEBT-AV-012`):
   - criar uma avaliação com `class_group_id` preenchido via UI, confirmar
     que o backend aceita;
   - confirmar que uma avaliação com `class_group_id` ausente é rejeitada
     de forma coerente entre UI e backend (nenhum dos dois lados permite o
     que o outro rejeitaria);
   - confirmar que as 10 avaliações legadas (pré-existentes,
     `class_group_id` nulo) continuam acessíveis e funcionais (AC-13 de
     AV-S04, já coberto no pós-check (g) da seção 3.7, reconfirmar aqui no
     contexto da flag ativa).

5. **O seed de demonstração continua restrito ao ambiente isolado.**
   `core/scripts/seed_academic_multi_question_demo.py` tem um guard
   fail-closed (`require_isolated_database`, revisado e aprovado nas 3
   rodadas de revisão independente desta preparação) que recusa qualquer
   banco cujo nome não bata com `^av_s02_saneamento_[A-Za-z0-9_-]+$` —
   isso inclui `avalia_dev` explicitamente. **Este guard não deve ser
   enfraquecido, contornado ou ter exceção aberta para popular
   `avalia_dev`** — se for necessário popular dados de demonstração reais
   em `avalia_dev`, isso é escopo de P6 (extensão de `core/app/seed.py`,
   seção 4.5), uma decisão e um script deliberadamente separados, não uma
   flexibilização do seed isolado.

6. **Reversão, se necessário:** `ACADEMIC_MODULE_ENABLED=false` + reinício
   do backend; rebuild do frontend com `VITE_ACADEMIC_MODULE_ENABLED=false`
   (ou ausente). As migrações permanecem aplicadas (não é necessário nem
   desejável fazer downgrade só para desativar a flag — as colunas são
   nullable e retrocompatíveis, conforme já registrado na seção 5, bloco
   [P5]).

### 4.5 Dados de demonstração — seed existente não cobre os cenários novos

`core/app/seed.py` atual cria apenas 1 avaliação com 1 questão, sem turma
vinculada (pré-AV-S03/AV-S04). Para demonstrar efetivamente estrutura
acadêmica + múltiplas questões, é necessário **novo conteúdo de seed**
(fora do escopo deste documento executar, mas identificado como
pendência real):
- pelo menos 1 `Organization` → `Course` → `Discipline` →
  `CourseDiscipline` → `ClassGroup`, com `ProfessorClassLink` vinculando
  o professor demo;
- pelo menos 1 `Avaliação` com `class_group_id` preenchido e 2+ questões
  (demonstrando `position`, reordenação, rubrica por questão);
- opcionalmente, 1 clonagem de avaliação publicada, demonstrando
  `cloned_from_id`.

Isso exigiria uma extensão de `core/app/seed.py` (ou um script de seed
específico de demonstração), que **não existe hoje** — proposta de
trabalho futuro, não parte deste plano de atualização de `avalia_dev`
em si; mencionado aqui apenas para que "demonstrar" não seja confundido
com "o ambiente já tem dados prontos para mostrar" — ele não tem.

---

## 5. Sequência executável e pontos exatos de autorização

Numerados por ordem de execução real; cada bloco é atômico quanto à
autorização necessária.

```
[P0] JÁ CONCLUÍDO — nenhuma ação pendente
  - Código integrado em main (PR #9), homologado (DEC-AV-029).

[P1] AUTORIZAÇÃO NECESSÁRIA #1 — decidir qual versão do plano de
     saneamento adotar como canônica (seção 2.3): local de 676 linhas,
     integrada de 359, ou versão ajustada por Rafael. Sem esta decisão,
     nenhum passo de saneamento pode começar.

[P2] Após P1 — criar o script SQL versionado do saneamento
     (core/scripts/av_s02_saneamento_human_reviews.sql), com base na
     versão decidida em P1. Revisão por agente diferente do autor.
     -- Não exige autorização de escrita em avalia_dev (é trabalho local
        de código/script, análogo ao já autorizado nesta rodada).

[P3] AUTORIZAÇÃO NECESSÁRIA #2 — executar a validação completa (backup
     fictício + restore + saneamento + migrações + pós-checks) em banco
     ISOLADO descartável (seção 3.4), não avalia_dev. **CONCLUÍDA em
     2026-10-01**, com revisão independente em 3 rodadas (REPROVADO →
     REPROVADO → APROVADO final) e ensaio `ALL_DRY_RUN_SCENARIOS_GREEN`
     (seção 7). Autorização recebida de Rafael em 2026-10-01.

[P4] AUTORIZAÇÃO NECESSÁRIA #3 — EXECUÇÃO REAL CONTRA avalia_dev:
     interrupção de escritas comprovada (3.2) + backup final + validação
     de restore (3.3-3.4) + saneamento real (3.5) + aplicação das 3
     migrações (3.6) + pós-checks (3.7), seguindo a matriz de estados
     (3.8) em caso de qualquer desvio. Esta é a autorização de maior
     risco: escrita operacional real, janela de manutenção, writers
     parados na origem e conexões residuais encerradas (mecanismo
     primário), com REVOKE como camada adicional opcional documentada se
     necessário. Deve ser concedida como
     um bloco (não é seguro autorizar "só o backup" ou "só uma migração"
     isoladamente, dado que o saneamento é pré-requisito físico de
     7b1d6d853f20, que por sua vez precede as outras duas na cadeia
     linear). **NÃO AUTORIZADA nesta rodada** (confirmado por Rafael em
     2026-10-01).

[P5] AUTORIZAÇÃO NECESSÁRIA #4 — ativar ACADEMIC_MODULE_ENABLED=true
     (backend, com reinício do processo) + VITE_ACADEMIC_MODULE_ENABLED=true
     (rebuild do frontend) no ambiente de avalia_dev, seguido de teste
     funcional (procedimento detalhado na seção 4.4). Só pode ocorrer
     depois de P4 concluído (as migrações precisam existir fisicamente
     antes da flag exigir class_group_id). Separada de P4 porque é uma
     decisão de produto (ligar o módulo acadêmico para demonstração), não
     uma necessidade técnica da migração em si — avalia_dev pode ficar
     com as 4 migrações aplicadas e o módulo acadêmico desligado
     indefinidamente, sem problema algum (nullable, retrocompatível). O
     seed de demonstração (`seed_academic_multi_question_demo.py`)
     permanece restrito ao ambiente isolado em qualquer cenário — não é
     reaproveitado para popular avalia_dev sob P5. **NÃO AUTORIZADA nesta
     rodada** (confirmado por Rafael em 2026-10-01).

[P6] AUTORIZAÇÃO NECESSÁRIA #5 (opcional, separada) — estender/criar
     seed de demonstração com estrutura acadêmica + múltiplas questões
     (seção 4.5). Não é pré-requisito técnico de nada acima; é
     conveniência de demonstração. Pode ser adiada indefinidamente.
```

**Fora do escopo de qualquer autorização aqui prevista** (reafirmado):
deploy, promoção de baseline, saneamento operacional de qualquer outro
dado além do grupo já inventariado, exclusão de branches/backups, nova
sprint, retomada de AV-S05B (que permanece parcial, aguardando coleta
manuscrita, eixo tecnicamente independente desta atualização de
`avalia_dev`).

---

## 6. Resumo do que está pendente de decisão de Rafael

1. ~~**P1** — qual versão do saneamento adotar~~ — **resolvido**: versão
   local de 676 linhas adotada como base, com as 9 melhorias GOV-006.
2. ~~**P3** — autorizar o ensaio isolado completo~~ — **concluído e
   aprovado** em 2026-10-01 (seção 7).
3. **P4** — autorizar a execução real contra `avalia_dev` (interrupção de
   escritas comprovada + backup final + saneamento real + as 3 migrações
   pendentes + pós-checks), como bloco único, em janela de manutenção.
   **Confirmado NÃO autorizado nesta rodada.**
4. **P5** — autorizar ativar o módulo acadêmico no ambiente, com
   procedimento detalhado na seção 4.4 (depois de P4). **Confirmado NÃO
   autorizado nesta rodada.**
5. **P6** — autorizar (opcional) estender o seed para incluir cenários de
   demonstração de estrutura acadêmica/múltiplas questões em `avalia_dev`
   (seção 4.5). Não solicitado nesta rodada.

P4 e P5 permanecem explicitamente pendentes de decisão futura de Rafael.
Nenhuma escrita, saneamento, migração ou ativação foi feita em
`avalia_dev` em nenhuma rodada desta preparação.

---

## 7. Reconciliação desta rodada preparatória autorizada (2026-10-01)

A rodada preparatória foi executada **somente** contra PostgreSQL 16 isolado,
sem escrita em `avalia_dev`:

- proposta local de 676 linhas recuperada exatamente do commit `aa8031a` e
  preservada como
  `proposta_saneamento_human_reviews_duplicadas_v2_consolidada.md`, sem
  sobrescrever a versão integrada de 359 linhas nem o delta GOV-006;
- scripts locais criados em `core/scripts/`: diagnóstico, saneamento,
  validação pós-migração, recuperação compensatória, runner completo e seed
  acadêmico/múltiplas questões idempotente;
- backup somente leitura de `avalia_dev` criado fora do Git, modo `0600`,
  checksum SHA-256 validado, restaurado efetivamente em cluster PostgreSQL
  16 temporário com `pg_restore --exit-on-error --no-owner`;
- cadeia ensaiada: `e1b02279b1a5` → saneamento → `7b1d6d853f20` →
  `c4a8b2d91e37` → `a9f4c2e71b06`;
- cenários de falha/retomada ensaiados: grupo conflitante aborta sem DML/DDL
  confirmado; falha depois da cópia e antes do COMMIT reverte integralmente;
  recuperação pós-COMMIT/pré-constraint; recuperação pós-constraint após
  downgrade; reexecução idempotente; índice concorrente INVALID e checkpoint
  válido da migração AV-S04; guard contra nome lookalike;
- configuração demonstrativa validada apenas no isolado, com as duas flags
  coerentes (`ACADEMIC_MODULE_ENABLED=true`,
  `VITE_ACADEMIC_MODULE_ENABLED=true`) e seed fictício idempotente com
  estrutura acadêmica + avaliação de duas questões posições `1,2`.

Resultado: `ALL_DRY_RUN_SCENARIOS_GREEN`. Durações e evidência integral em
`docs/governance/evidence/AV-OPER-001-avalia-dev-preparacao/`.

**Estado de autorização após esta rodada:** P3 (ensaio isolado) concluído.
P4 (execução real em `avalia_dev`) e P5 (ativação das flags no ambiente)
continuam não autorizados. O parecer independente passou por 3 rodadas:
rodada 1 REPROVADO (7 bloqueadores: guard LIKE inseguro, score arredondado,
auditoria incompleta, locks ausentes, recuperação incompleta, não
idempotente, alembic_version NULL-unsafe); correções aplicadas; rodada 2
REPROVADO (6 achados: guard do seed por substring, estado pós-
saneamento/recovery sem prova integral de ausência de linhas extras,
idempotência do seed superficial, search_path ausente no diagnóstico,
cenário de falha pré-commit sintético); correções aplicadas; **rodada 3
APROVADO**, sem ressalvas, confirmando as 6 correções linha a linha contra
`core/app/models.py` e sem identificar regressão ou guard enfraquecido.

---

## 8. Ajustes ao procedimento operacional, pós-aprovação de Rafael (2026-10-01)

Rafael recebeu a aprovação da preparação (seção 7) e, nesta mesma data,
solicitou 5 ajustes concretos ao procedimento operacional ANTES de decidir
sobre P4/P5 — ainda **não autorizados**. Ajustes aplicados neste documento:

1. **Janela sem escritas (seção 3.2, reescrita):** identificação e
   interrupção dos writers passa a ocorrer explicitamente ANTES do backup
   final (ordem corrigida), com prova técnica via `REVOKE` de privilégios
   de escrita do papel de aplicação (não apenas parar processos e confiar
   em `LOCK TABLE`, que é liberado no `COMMIT` e não cobre o intervalo até
   as migrações) e monitoramento contínuo via `pg_stat_user_tables`
   durante toda a janela. **(Ver correção desta abordagem logo abaixo,
   nesta mesma seção 8 — o uso de `REVOKE` como padrão foi revisto.)**
2. **Backup final (seção 3.3, nova; seção 3.4 reescrita):** o backup usado
   no ensaio isolado (10:18 de 2026-10-01) é explicitamente qualificado
   como backup de ENSAIO, que não substitui o backup final — este só pode
   ser capturado depois que a barreira de escritas da seção 3.2 estiver
   comprovadamente ativa, e deve ser restaurado e validado em isolado
   antes da primeira escrita operacional real.
3. **Falhas e recuperação (seção 3.8, reescrita como matriz):** substituída
   a lista de 4 cenários por uma matriz de 10 estados (0 a 9), cada um com
   diagnóstico, ação testada, precondição explícita antes de qualquer
   `alembic downgrade` (nenhum downgrade é automático — a precondição de
   ausência de dado novo dependente é sempre reconfirmada manualmente) e
   indicação de quando usar restauração do backup em vez de recuperação
   por script. Inclui o estado de índice concorrente interrompido como
   item próprio (estado 6) e o estado de escrita indevida durante a janela
   (estado 0).
4. **Ativação — P5 (seção 4.4, nova):** procedimento detalhado e separado
   de P4 — configuração do backend com nota sobre `@lru_cache` exigindo
   reinício, rebuild (não apenas restart) do frontend para a flag
   build-time do Vite, teste funcional pós-ativação, e reafirmação
   explícita de que o guard do seed de demonstração não é e não deve ser
   enfraquecido para popular `avalia_dev` — isso seria escopo de P6,
   deliberadamente separado.
5. **Publicação preparatória:** autorizada por Rafael nesta mesma rodada
   (stage seletivo, commit, push, PR rascunho). Detalhes de execução e
   resultado (URL, SHA, checks de CI) registrados no snapshot de execução
   correspondente (`docs/governance/snapshots/`, ponteiro em
   `latest_execution.md`) e no dashboard executivo — não neste documento
   de planejamento, que antecede a publicação em si.

Nenhuma repetição do ensaio completo foi feita nesta rodada: os ajustes
acima são documentais/de procedimento (texto do plano), não alterações aos
scripts SQL/Python já aprovados na 3ª revisão independente (seção 7) — não
há lacuna técnica nova que justifique reexecutar `ALL_DRY_RUN_SCENARIOS_GREEN`.
Uma revisão independente limitada, focada exclusivamente nestes 5 ajustes
textuais, foi solicitada antes da publicação — resultado: **APROVADO COM
RESSALVAS** (4 ressalvas, todas de texto/numeração, todas corrigidas neste
mesmo documento antes da publicação; nenhuma apontou defeito nos scripts).

Em seguida, Rafael identificou um problema técnico real na primeira versão
desta seção 3.2: `REVOKE` de privilégios havia sido descrito como a prova
técnica padrão de interrupção de escritas, mas `REVOKE` é, ele próprio,
uma alteração operacional em `avalia_dev` (pertence ao bloco de
autorização de P4, não é uma ação preparatória antecipável), e não é uma
garantia automática (não afeta dono da tabela, superusuários, privilégio
herdado por papel, `PUBLIC`, nem conexões já abertas). A seção 3.2 foi
reescrita para tratar "parar processos e verificar ausência de atividade"
como mecanismo primário, com `REVOKE` relegado a camada adicional opcional
sujeita a captura de baseline exata, verificação de ownership/superusuário/
herança de papéis, e restauração exata documentada — não um `REVOKE`
isolado. Nenhum defeito foi encontrado nos scripts SQL/Python já aprovados
(`core/scripts/`) nesta correção — o ajuste foi inteiramente textual/de
procedimento, na seção 3.2 deste documento.

Uma segunda revisão independente limitada, focada exclusivamente nesta
correção da seção 3.2, confirmou: **APROVADO COM RESSALVAS** — a inversão
conceitual (parar+verificar como primário, `REVOKE` como opcional
pertencente a P4) e os 5 motivos de insuficiência do `REVOKE` isolado
(dono, superusuário, herança de papel, `PUBLIC`, conexão já aberta) foram
todos corretamente endereçados; 4 ressalvas de consistência textual foram
identificadas (uma referência stale a `REVOKE` como padrão no bloco P4 da
seção 5, uma falta de nota inline no item 1 desta seção 8, uma query de
baseline não-idiomática com lacuna silenciosa para tabelas sem ACL
explícita, e ausência de template SQL para a restauração) — todas
corrigidas neste mesmo documento antes da publicação. Nenhuma ressalva
apontou defeito nos scripts SQL/Python.

P4 e P5 permanecem explicitamente **não autorizados** nesta rodada. Nenhum
merge, escrita em `avalia_dev`, saneamento, migração, ativação, deploy ou
promoção de baseline foi feito.


## 9. Conferência limitada pré-integração em 2026-10-02

Codex conferiu independentemente as ressalvas dos dois pareceres documentais contra o HEAD `6c20bb83ee1c9bee136dc1b74ff6c5bfe29a9dec`: sequência completa no restore final, alternativa de recuperação do índice, referências, REVOKE opcional, nota histórica, LEFT JOIN LATERAL e exemplo de restauração presentes. Nenhum ensaio foi repetido. Corrigida a interpretação dos contadores: operações autorizadas também os alteram; são sinais auxiliares, não prova de autoria ou ausência de escrita. P4/P5 seguem não autorizados. Qualquer uso futuro da camada opcional de ACL requer preservar também grantor, grant options e privilégios efetivos; o exemplo resumido não é um restaurador universal.
