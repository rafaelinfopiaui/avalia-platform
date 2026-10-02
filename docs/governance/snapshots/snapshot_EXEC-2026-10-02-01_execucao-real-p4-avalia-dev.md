# EXEC-2026-10-02-01 — Execução real de P4 contra `avalia_dev` (saneamento + 3 migrações)

---
id: "EXEC-2026-10-02-01"
tipo: "execucao_operacional_real"
consolidador: "Hermes"
data: "2026-10-02"
autorizado_por: "Rafael (2026-10-02; autorização explícita de P4, exclusivamente no banco local avalia_dev, usando os scripts integrados em main@9310b545cd332948104edf44e555eff5f2582e4c; confirmação adicional do comando exato de saneamento pelo mecanismo de aprovação do terminal)"
carater: "execucao_real_local_sem_P5"
---

## Resumo

Primeira execução real (não ensaio) do saneamento de duplicatas em
`human_reviews` e das 3 migrações Alembic pendentes, contra a instância
**local** de `avalia_dev` (banco de desenvolvimento no PostgreSQL local do
operador, não um ambiente remoto/produção). P5 (ativação do módulo
acadêmico) **não foi executado** — permanece não autorizado.

## 1. Identificação do alvo (confirmada antes de qualquer escrita)

```
$ psql -d avalia_dev -c "\conninfo"
You are connected to database "avalia_dev" as user "rafaeloliveira" via socket in "/tmp" at port "5432".
```

- Host: localhost (socket Unix `/tmp`, não TCP remoto) — porta 5432.
- Banco: `avalia_dev`, confirmado via `current_database()`.
- Versão Alembic pré-execução: `e1b02279b1a5` (esperado, confere com o
  plano consolidado, seção 3.1).
- Inventário pré-execução: `users=4, assessments=10, questions=10,
  human_reviews=18, audit_events=36` — idêntico ao inventário registrado
  no plano.
- Duplicatas: 1 grupo (`4f56a10b-3a44-4df5-9047-adef7546a3c0`), 3 linhas —
  idêntico ao esperado.
- `human_reviews_superseded`: não existia (esperado, pré-saneamento).
- Nenhuma divergência encontrada — prosseguiu conforme plano.
- Outros bancos do cluster (`av_s04_browser_test`,
  `av_s04_migration_recovery`, `av_s04_migration_test`,
  `av_s04_reviewindep_*`) identificados e **não tocados** em nenhum
  momento desta execução. `avalia-github-lab` confirmado inexistente
  neste cluster.

## 2. Janela sem escritas

- Inventário de conexões a `avalia_dev`
  (`pg_stat_activity WHERE datname='avalia_dev'`), excluindo o próprio
  backend do operador (`pid != pg_backend_pid()`): **0 conexões de
  aplicação encontradas** antes, durante e depois da janela.
- O único processo uvicorn local em execução no host
  (`pid 24495`, `av_s04_browser_test`) foi confirmado via `DATABASE_URL`
  real do processo como conectado a um banco diferente — não tocado, não
  parado, não reiniciado.
- Como não havia nenhum writer conectado a `avalia_dev`, **nenhum
  processo precisou ser parado e nenhuma sessão residual precisou ser
  encerrada** nesta execução. Nenhuma conexão desconhecida foi
  encontrada.
- `REVOKE` **não foi usado** (não autorizado nesta rodada) — a barreira
  foi satisfeita integralmente pela ausência confirmada de writers, sem
  necessidade de camada adicional.
- Baseline de monitoramento (`pg_stat_user_tables`) capturado antes do
  backup final: `assessments 4/3/0, audit_events 25/0/0,
  human_reviews 15/0/0, questions 4/0/0, users 2/0/0` (inserções/
  atualizações/remoções acumuladas desde a criação do banco — não é o
  inventário de linhas ativas, é o contador histórico do PostgreSQL).
  Reconfirmado idêntico imediatamente antes da execução do saneamento.

## 3. Backup final

- Caminho: diretório protegido fora do Git, `0700`
  (`~/avalia-backups/`), arquivo criado com `umask 077` → permissões
  `0600` em dump, `.sha256`, `.contents.txt` e CSV auxiliar.
- Nome do arquivo (sem publicar o diretório absoluto do operador):
  `avalia_dev_P4_execucao_real_20261002_101544.dump` (42.217 bytes).
- `shasum -a 256` gerado e verificado imediatamente (`OK`).
- `pg_restore --list` executado com sucesso (contents.txt gerado).
- Export CSV adicional do grupo duplicado, mesmo diretório protegido,
  mesmas permissões, checksum próprio verificado.
- **Restauração e validação completas em PostgreSQL 16 isolado antes de
  qualquer escrita real**: `DUMP_SHA256` do restore confere com o backup;
  sequência completa 3.5→3.6→3.7 reexecutada neste restore específico —
  resultado `ALL_DRY_RUN_SCENARIOS_GREEN`. Evidência completa em
  `P4-execucao-real-2026-10-02/01_validacao_backup_final_isolado.txt`.

## 4. Execução real (sequência exata, scripts sem ajuste improvisado)

Todos os scripts usados são exatamente os integrados em
`main@9310b545cd332948104edf44e555eff5f2582e4c` — hash SHA-256 do arquivo
em disco confirmado idêntico ao hash do arquivo nesse commit antes da
execução do saneamento (`git diff HEAD` vazio).

1. **Diagnóstico** (`av_s02_diagnostico_human_reviews.sql`, somente
   leitura): confirmou 1 grupo, classificação `EQUIVALENT`, 3 linhas com
   os IDs nominais esperados. Evidência:
   `P4-execucao-real-2026-10-02/02_diagnostico_real.txt`.

2. **Saneamento** (`av_s02_saneamento_human_reviews.sql`, executado com
   `PGOPTIONS='-c avalia.allow_sanitation=AV_S02_SANITATION_20261001'`,
   opt-in de sessão exigido pelo guard de duas camadas do próprio
   script): `SANITATION_APPLIED_GREEN`. Timestamp real de arquivamento
   (`superseded_at`): `2026-10-02 10:44:52.945851`. Pós-checks confirmam:
   0 grupos duplicados restantes; linha vencedora `31d31b5c-...` intacta
   (mesmo `created_at`, `final_total`, `final_scores_json`); 2 linhas
   arquivadas em `human_reviews_superseded` com `superseded_reason`
   nominal; os 3 `AuditEvent` originais (`b12db6d4-...`,
   `4f737eab-...`, `cad4d910-...`) com `created_at` idênticos ao
   inventário pré-operação — auditoria comprovadamente intocada.
   Evidência: `P4-execucao-real-2026-10-02/03_saneamento_real.txt`.

3. **Migrações** (`alembic upgrade head`, a partir de `e1b02279b1a5`):
   aplicou `7b1d6d853f20` → `c4a8b2d91e37` → `a9f4c2e71b06`, nessa ordem,
   sem erro. Evidência:
   `P4-execucao-real-2026-10-02/04_migracoes_real.txt`.

4. **Validação pós-migração** (`av_s02_validacao_pos_migracoes.sql`):
   `POST_MIGRATION_VALIDATION_GREEN`. Evidência:
   `P4-execucao-real-2026-10-02/05_validacao_pos_migracao_real.txt`.

### Pós-checks completos (a)–(g), seção 3.7 do plano

| Check | Resultado |
|---|---|
| (a) nenhum grupo duplicado resta | Confirmado — consulta vazia |
| (b) linha vencedora intacta | Confirmado — `31d31b5c-...`, dados idênticos |
| (c) linhas arquivadas preservadas | Confirmado — 2 linhas, `superseded_reason` nominal |
| (d) auditoria intocada | Confirmado — 3 `AuditEvent` nominais, `created_at` idênticos |
| (e) constraints das 3 migrações | Confirmado — `uq_human_reviews_job_id`, `uq_questions_assessment_position`, `fk_assessments_class_group_id`, `fk_assessments_cloned_from_id`, `version_num=a9f4c2e71b06` |
| (f) contexto HTTP funcional | Confirmado via instância local temporária do Core (ver seção 5) — `GET /v1/correction-jobs/4f56a10b-.../context` retorna `human_review` da linha vencedora |
| (g) avaliações legadas acessíveis | Confirmado — 9/10 avaliações do professor autenticado retornam `200`, `position=1`; a 10ª pertence a outro professor e retorna `403` por autorização de propriedade (comportamento correto, não falha de migração) |

Nenhuma falha ocorreu em nenhuma etapa — não foi necessário acionar a
matriz de recuperação (seção 3.8).

## 5. Validação funcional (checks HTTP, separados de P4/P5)

- Instância local temporária do Core iniciada **restrita a
  `127.0.0.1:8030`** (porta isolada, distinta da instância pré-existente
  em `:8024` que serve `av_s04_browser_test`), com
  `DATABASE_URL=postgresql+psycopg2://localhost:5432/avalia_dev`
  explícito, sem `ACADEMIC_MODULE_ENABLED` (flags de P5 não tocadas).
- Login real via credencial de demonstração já documentada publicamente
  no `.env.example` do repositório (`professor.demo@avalia-platform.example`
  / senha padrão de exemplo, não uma credencial de produção).
- Apenas leituras executadas: `GET /v1/correction-jobs/{id}/context` e
  `GET /v1/assessments/{id}` × 10. **Nenhum seed, nenhuma criação de
  dado de demonstração.**
- Instância temporária **encerrada** ao final (`process kill`),
  confirmado via `lsof` (porta `8030` livre) e `pg_stat_activity` (zero
  conexões residuais a `avalia_dev`).
- Processo pré-existente `pid 24495` (`av_s04_browser_test`, porta
  `8024`) **não foi tocado** em nenhum momento — confirmado ativo e
  inalterado antes e depois.

## 6. Falhas

**Nenhuma falha ocorreu.** Todas as etapas retornaram sucesso na primeira
tentativa, com as precondições de cada passo confirmadas antes da
execução (ver seções 1–3). A matriz de recuperação (seção 3.8 do plano)
não precisou ser acionada. Nenhum downgrade, nenhuma restauração do
backup sobre `avalia_dev`, nenhuma tentativa repetida.

## 7. Durações observadas (execução real, não ensaio)

- Backup final + validação completa em isolado (restore + 3.5→3.6→3.7):
  medido pelo log, duração total da reexecução da sequência de validação
  no isolado — ver `01_validacao_backup_final_isolado.txt`
  (`DURATION_*` somados ficam abaixo de 1 segundo de tempo de banco;
  o tempo de parede real desta etapa, incluindo `pg_dump`/`pg_restore`/
  inicialização do cluster temporário, foi de alguns segundos).
- Diagnóstico real: sub-segundo.
- Saneamento real: sub-segundo (transação única, `COMMIT` imediato).
- Migrações reais (3): segundos (tempo de parede entre o disparo do
  comando `alembic upgrade head` em 2026-10-02 ~10:45 e sua conclusão
  logo em seguida, sem erro).
- Validação pós-migração: sub-segundo.
- Validação funcional via API: dezenas de chamadas HTTP locais,
  concluídas em poucos segundos.
- **Janela total de ponta a ponta** (do início da identificação do alvo
  até a confirmação final de encerramento): aproximadamente 35 minutos
  nesta sessão — a maior parte do tempo foi gasta em confirmação de
  precondições, reapresentação do comando para aprovação explícita do
  operador, e leitura/registro de evidência, não em tempo de execução de
  banco (que permanece, como já estimado antes da execução, da ordem de
  segundos). Esta duração reflete uma execução local assistida passo a
  passo, não uma estimativa de janela de manutenção em produção.

## 8. Localização do backup (protegida, não publicada)

Backup final e CSV auxiliar armazenados em diretório local protegido
(`0700`) fora do Git, com arquivos em `0600`, nome do arquivo registrado
nesta seção (seção 3) sem expor o caminho absoluto do operador. Checksums
SHA-256 gerados e verificados, path completo registrado apenas em
`/tmp/av_p4_dump_path.env` (efêmero, fora do repositório).

## 9. Estado final confirmado

```
version_num = a9f4c2e71b06
users=4, assessments=10, questions=10,
human_reviews=16, human_reviews_superseded=2, audit_events=36,
organizations=0, courses=0, class_groups=0
```

Estrutura acadêmica (AV-S03) e suporte a múltiplas questões (AV-S04)
agora existem fisicamente no banco `avalia_dev`, mas **sem nenhum dado**
— nenhuma `Organization`/`Course`/`ClassGroup` foi criada, nenhum seed de
demonstração foi executado. P5 (flags de ativação) permanece **não
configurado** nesta instância.

## 9b. Reconciliação de contagens (2026-10-02, pós-execução)

A pedido de Rafael, as contagens antes/depois foram reconciliadas usando
exclusivamente evidência já preservada (backup final, diagnóstico real,
CSV pré-saneamento, logs do saneamento), sem nova escrita em `avalia_dev`.
Relatório completo:
`docs/governance/evidence/AV-OPER-001-avalia-dev-preparacao/P4-execucao-real-2026-10-02/06_reconciliacao_contagens.md`.

Resumo: `human_reviews` 18→16, `human_reviews_superseded` 0→2 (soma
constante em 18 — nenhuma linha perdida), `audit_events` 36→36
(inalterado). As 2 linhas arquivadas (`8a9c2ba6-...`, `9459489c-...`)
correspondem integralmente ao conteúdo original (comparação campo a
campo contra o CSV pré-saneamento), e a vencedora (`31d31b5c-...`) e os
demais 15 registros permanecem intactos.

A contagem de 18 (maior que as "8 linhas" documentadas em snapshots de
2026-09-24) se explica por 10 linhas adicionais com `created_at` de
2026-09-25 — criadas um dia depois da última verificação histórica,
por atividade não precisamente identificada nos registros de governança
revisados. Uma pequena divergência adicional (7 linhas reconstituídas
por timestamp até o corte histórico de 09:44 de 2026-09-24, versus "8"
frequentemente citado nos documentos) não foi resolvida por esta
reconciliação e fica registrada como tal — sem atribuição de causa não
comprovada. Nenhuma das 10 linhas de 2026-09-25 foi tocada por este P4.

## 9c. Correção do indicador global (2026-10-02, 2ª rodada pós-integração do PR #11)

Rafael apontou que a exclusão de `BL-AV-3-01` a `BL-AV-3-04` (AV-S04) do
numerador na rodada anterior (seção 9b/dashboard antigo) estava incorreta:
"fora do escopo desta rodada" não é motivo para excluir uma entrega já
homologada do progresso global. Verificado nesta sessão, não presumido:
PR #9 está de fato `MERGED` (`gh pr view 9` → `state: MERGED`, merge
commit `9ab6e43`), a entrega funcional de AV-S04 foi homologada por
`DEC-AV-029` (AC-01 a AC-18 cumpridos, `sprint_AV-S04...md` §10-11), e a
migração operacional `a9f4c2e71b06` foi de fato aplicada a `avalia_dev`
nesta mesma rodada de P4 (ela depende de `c4a8b2d91e37`, aplicada na
mesma transação de `alembic upgrade head` — ver seção 4). Os 4 itens
foram incluídos no numerador do dashboard executivo: **15/70 → 19/70**.
`BL-AV-3-04` (contrato OpenAPI) não depende de migração operacional e já
estava tecnicamente completo desde a integração do PR #9.

## Proveniência da atualização documental pendente (pós-PR #10)

O pacote local `~/avalia-local-packages/snapshot-update-pos-pr10-2026-10-02/`
(diff de 51 linhas registrando a publicação do PR #10 e a intervenção do
Codex via commit `e8a994e`, nunca publicado em nenhum commit) permanece
preservado e recuperável (checksums verificados). Esta seção o referencia
explicitamente para incorporação futura: ao consolidar a documentação
desta execução de P4, a atualização pendente deve ser reaplicada ao
snapshot `EXEC-2026-10-01-03` com a proveniência registrada em seu
próprio `README.md`, antes ou junto da publicação deste snapshot
`EXEC-2026-10-02-01`.

## Pendências

- **P5 permanece não autorizado.** Nenhuma ativação de
  `ACADEMIC_MODULE_ENABLED`/`VITE_ACADEMIC_MODULE_ENABLED` foi feita.
- Esta execução foi contra a instância **local** de `avalia_dev**, não um
  ambiente remoto/produção. Se Rafael pretende replicar esta operação em
  outro ambiente, isso exige nova autorização e nova identificação de
  alvo (seção 1 deste documento, repetida para o ambiente real).
- Nenhum commit/push/merge foi feito nesta execução. Esta documentação
  (snapshot, dashboard, evidência) permanece local até revisão e
  autorização explícita de publicação por Rafael.
