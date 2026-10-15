---
id: "desenho_bl-av-4b-05_retencao_exclusao_imagens"
tema: "BL-AV-4B-05 — retenção e exclusão de imagens de resposta"
gerado_em: "2026-10-15T01:40:00-03:00"
revisado_em: "2026-10-15 — 4 correções de Rafael + D1/D2/D3; revisão Antigravity (APROVADO C/ RESSALVAS) incorporada; R3 DECIDIDO por Rafael (opção a, bloquear em B)"
status: "DESENHO APROVADO PARA IMPLEMENTAÇÃO LOCAL da 1ª fatia — ressalvas R1/R2/R4 em especificação, R3 decidido; aguardando execução Claude Code + revisão Antigravity"
base: "main e21332ae1335cab7e90eb9db8450e29865057b53"
---

# Desenho técnico — BL-AV-4B-05: retenção e exclusão de imagens de resposta

> Autorizado por Rafael: planejamento técnico e análise dirigida, sem
> implementação. Reaproveita o estado já integrado em `main`
> (`e21332ae1335cab7e90eb9db8450e29865057b53`), reconfirmado nesta
> rodada (`git fetch` + `git rev-parse` independentes, local == remoto,
> working tree limpo antes de iniciar). Não repete a auditoria das
> entregas já homologadas (AV-S06B, AV-S08B) — parte delas como dado
> conhecido.

## 1. Referências institucionais (lidas, não reabertas)

- `DEC-AV-013` (`registers/decisions.md:25`): "retenção e exclusão de
  dados" — **pendente**, bloqueia uso de dados reais e parte da
  homologação final (`BL-AV-8-06`); explicitamente aplicável a
  `BL-AV-4B-05` (imagens). Não é reaberta aqui — continua pendente de
  decisão de Rafael; este documento prepara as opções, não decide por
  ele.
- `BL-AV-4B-05` (`backlog_tecnico_avalia.md:99,360`): "Retenção, exclusão
  e tratamento de metadados; exclusão de imagem, nome de aluno e texto
  de resposta completo dos logs." Tipo: decisão + implementação.
- Já entregue e homologado anteriormente (`DEC-AV-036`), **não
  reaberto**: proteção de logs contra dado sensível de imagem — logs já
  carregam só IDs/metadados, nunca bytes/caminho/conteúdo
  (`core/app/routers/images.py:16`, comentário de módulo, confirmado por
  leitura de código nesta rodada, sem reexecutar testes).
- `sprint_AV-S06B_recebimento_armazenamento_imagens.md` §7: já havia
  proposto, sem decisão formal, "nenhuma política automática de
  expiração nesta sprint; exclusão só manual/administrativa, sem
  endpoint de exclusão em massa" — proposta preservada e retomada aqui
  com mais detalhe, não descartada.
- `pendencia-regulatoria.md` / `BKL-AV-001`: qualquer retenção com dados
  reais depende de decisão regulatória externa, fora do escopo desta
  entrega (que trabalha com dados fictícios).

**Não invento prazo legal nem declaro conformidade regulatória** — essa
distinção é mantida explicitamente ao longo de todo este documento.

## 2. Ciclo de vida real, levantado no código (`main` atual)

### 2.1 Modelos e vínculos (FKs confirmadas em `core/app/models.py`)

```
Answer (id, question_id, source, transcription_status,
        manual_transcription_draft, transcription_confirmed_by_id,
        transcription_confirmed_at, transcription_version, text)
  │
  ├─ 1:N → AnswerImage (id, answer_id FK, storage_filename,
  │         original_filename, content_type, size_bytes, sha256_hash,
  │         uploaded_by_id FK→users, created_at)
  │         [core/app/models.py:305-318]
  │         FK answer_id: ForeignKey("answers.id") SEM ondelete e SEM
  │         relationship com cascade no lado Answer (confirmado em
  │         models.py:308-310 e na migração d5e3a7c19f42:34, que também
  │         não declara ondelete). AUSÊNCIA de CASCADE ≠ RESTRICT
  │         explícito: a FK não tem ação de exclusão declarada. O efeito
  │         concreto de um DELETE no pai Answer depende do backend e do
  │         default da coluna de FK no momento da criação; NÃO presumo
  │         "RESTRICT" como garantia contratual — o que o código garante
  │         é apenas que não há propagação automática (nenhum
  │         delete-orphan, nenhum ON DELETE CASCADE). Esta fatia não
  │         exclui Answer, então não dependemos desse comportamento;
  │         registro a distinção para não inventar uma semântica de FK
  │         que o schema não declara.
  │
  └─ 1:N → CorrectionJob (id, answer_id FK, rubric_id, status, attempt)
            [models.py:321-332]
            │
            ├─ 1:N → AIExecution (id, job_id FK, engine_mode, model,
            │         overall_confidence, ...) [models.py:335-350]
            │         └─ 1:N → CriterionScore (ai_execution_id FK)
            │
            └─ 0:1 → HumanReview (id, job_id FK, UNIQUE(job_id),
                      reviewer_id FK→users, decision, final_total,
                      final_scores_json) [models.py:367-379]

AuditEvent (id, actor_id FK→users nullable, action, resource_type,
            resource_id [string livre, SEM FK], before_json, after_json)
  [models.py:382-391]
  — registro genérico por (resource_type, resource_id); NÃO tem FK real
    para Answer/AnswerImage, então sobrevive à exclusão de qualquer
    recurso por desenho (é o padrão já usado por `delete_question`,
    core/app/main.py:500-510, que grava before_json ANTES do db.delete).
```

### 2.2 Armazenamento físico

- Bytes da imagem: arquivo em disco sob
  `Settings.answer_images_storage_dir` (default
  `core/var/answer_images/`, fora do Git — `.gitignore` confirmado),
  nome gerado pelo servidor (`{uuid4}.{ext}`, nunca o nome do cliente).
- Banco guarda só metadados (`storage_filename`, `sha256_hash`,
  `content_type`, `size_bytes`) — **nenhum BYTEA/blob no PostgreSQL**.
- Consequência estrutural: excluir o registro `AnswerImage` e excluir o
  arquivo em disco são **duas operações distintas**, que podem falhar
  independentemente uma da outra (ver seção 3.5, falhas parciais).

### 2.3 Estados reais do ciclo, por estágio

| Estágio | `Answer.source` | `Answer.transcription_status` | `CorrectionJob` existe? | `HumanReview` existe? |
|---|---|---|---|---|
| A. Imagem recém-enviada, aguardando transcrição | `IMAGE` | `AGUARDANDO_TRANSCRICAO` | não | não |
| B. Transcrição confirmada, sem correção solicitada | `IMAGE` | `TRANSCRICAO_CONFIRMADA` | não | não |
| C. Correção solicitada, sem revisão humana ainda | `IMAGE` | `TRANSCRICAO_CONFIRMADA` | sim (`SUGERIDA`/`PENDENTE`/`PROCESSANDO`/`FALHA`) | não |
| D. Correção + revisão humana concluída | `IMAGE` | `TRANSCRICAO_CONFIRMADA` | sim | sim |

Confirmado por inspeção de código (`core/app/main.py:989-998`,
`request_correction`): o guard
(`transcription_status != TRANSCRICAO_CONFIRMADA or not answer.text`)
só bloqueia a criação de `CorrectionJob` **enquanto a transcrição não
estiver confirmada** (estágio A). Ele NÃO impede um `CorrectionJob` no
estágio B — ao contrário: assim que a transcrição é confirmada (B), o
guard passa a **permitir** a criação do `CorrectionJob`, que leva a C e
depois D. Ou seja, B é o estado a partir do qual C/D se tornam
alcançáveis, não um estado que o guard protege contra correção. A
exclusão de imagem no estágio B precisa, portanto, considerar que uma
correção pode ser solicitada logo em seguida (transição B→C fora do
controle desta funcionalidade).

## 3. Impacto da exclusão por estágio (análise dirigida, sem presumir)

### 3.1 Estágio A — imagem ainda aguardando transcrição

- Não há `CorrectionJob`, `AIExecution`, `HumanReview` dependentes.
- `AnswerImage` existe; `Answer.text` é `NULL` (nenhum conteúdo textual
  derivado ainda).
- Excluir a imagem aqui é o caso **menos arriscado**: nenhuma avaliação
  pedagógica foi produzida a partir dela. Ainda assim, a `Answer` em si
  (o registro de que o aluno enviou algo) não deveria desaparecer
  silenciosamente — ver seção 3.6.

### 3.2 Estágio B — transcrição confirmada, sem correção

- `Answer.text` já está preenchido (confirmado pelo professor,
  `transcription_confirmed_by_id`/`_at` setados).
- Excluir a imagem aqui remove a **evidência original** (a foto) de um
  texto que já é tratado como a resposta oficial do aluno. O texto
  confirmado em si (`Answer.text`) não depende da imagem continuar
  existindo (são campos separados, sem FK um para o outro além do
  vínculo via `AnswerImage.answer_id`), mas a rastreabilidade
  "o professor leu exatamente esta imagem antes de confirmar" se perde
  se a imagem for apagada sem registro.
- **Não presumo** que apagar a imagem aqui seja equivalente a apagar a
  resposta: `Answer` e `AnswerImage` são entidades distintas; apagar uma
  não apaga a outra por desenho atual (nenhum `cascade="all,
  delete-orphan"` definido entre elas, diferente do padrão usado em
  `Rubric`→`RubricCriterion`).

### 3.3 Estágio C — correção solicitada, sem revisão humana

- Existe `CorrectionJob` (e possivelmente `AIExecution` já concluída).
  `CorrectionJob.answer_id` é FK obrigatória para `Answer` — **sem
  `ondelete`**, o padrão do PostgreSQL é bloquear (`RESTRICT`) a
  exclusão do `Answer` enquanto o `CorrectionJob` existir.
- A imagem em si (`AnswerImage`) pode, em tese, ser removida sem violar
  nenhuma FK (nada referencia `AnswerImage.id` diretamente), mas isso
  apagaria a evidência que sustenta uma correção já em andamento ou já
  produzida — um professor ou auditor futuro não conseguiria mais
  conferir a foto original contra a transcrição usada na correção.

### 3.4 Estágio D — correção e revisão humana já existentes

- Mesma restrição de FK do estágio C, mais a presença de `HumanReview`
  (decisão humana final, nota, justificativa).
- Este é o estágio de maior risco para exclusão não controlada: apagar a
  imagem aqui remove a evidência de origem de uma nota já decidida por
  um humano — exatamente o tipo de dado que a trilha de auditoria desta
  governança (ver `AuditEvent`, já usado em toda a plataforma) existe
  para preservar.

### 3.5 Conclusão da análise de impacto

**Não presumo que apagar a imagem permite apagar a `Answer` ou seu
histórico** — e o código confirma isso estruturalmente: não há cascade
automático entre `AnswerImage`, `Answer`, `CorrectionJob`,
`AIExecution`, `HumanReview`. Qualquer mecanismo de exclusão de imagem
precisa decidir explicitamente, por estágio, se:
(a) é permitida sem restrição,
(b) exige confirmação adicional,
(c) é bloqueada enquanto o estágio não permitir, ou
(d) vira só uma exclusão "lógica" (oculta/marca, sem remover o arquivo).

## 4. Proposta concreta (opções + recomendação, não aprovação)

### 4.1 Quem pode solicitar e executar exclusão

| Opção | Descrição | Recomendação |
|---|---|---|
| A | Qualquer professor dono/vinculado à avaliação pode excluir sua própria imagem, a qualquer momento | não recomendado isoladamente — colide com o estágio D (apagar evidência de correção já decidida) |
| B | Professor dono/vinculado pode solicitar; execução condicionada ao estágio (livre em A/B, bloqueada ou com confirmação extra em C/D) | **recomendado** — reaproveita o mesmo padrão de autorização já usado em `delete_question` (bloqueio por dependência + 409) |
| C | Só admin pode excluir, independente do estágio | mais restritivo que o necessário; não reaproveita o padrão de autonomia já dado ao professor dono em outros recursos |

**Recomendação**: Opção B. Mesma autorização de propriedade já usada em
toda a plataforma (`_get_owned_assessment` + `require_assessment_mutation`,
padrão idêntico ao de upload/download já homologado), com a trava de
estágio aplicada no mesmo nível (API), não só na UI.

### 4.2 Exclusão lógica vs. remoção física do arquivo

| Opção | Descrição | Recomendação |
|---|---|---|
| A | Remoção física imediata do arquivo + DELETE do registro `AnswerImage` | simples, mas irreversível e sem janela de arrependimento |
| B | Exclusão lógica primeiro (campo `deleted_at`/`deletion_reason` no `AnswerImage`, arquivo mantido), remoção física do arquivo só depois de uma janela de retenção configurável | **recomendado** — separa "o professor não quer mais ver isso" de "o byte precisa sumir do disco", permitindo auditoria e recuperação dentro da janela |
| C | Nunca remover fisicamente, só marcar como excluído para sempre | não atende ao objetivo de "retenção e exclusão" que `BL-AV-4B-05` pede — não há exclusão real nesta opção |

**Recomendação**: Opção B. Consistente com o padrão de
"nunca sobrescreve/apaga silenciosamente" já estabelecido em
`DEC-AV-040` (DP-2/DP-3, transcrição manual) e com o uso de tabelas de
arquivo em vez de `DELETE` destrutivo, já adotado na proposta de
saneamento de `human_reviews` (`proposta_saneamento_human_reviews_duplicadas.md`).

### 4.3 Tratamento de registros associados e trilha de auditoria

- `AnswerImage`: marcado com exclusão lógica (seção 4.2); nunca sofre
  `DELETE` físico do registro — preserva `sha256_hash`,
  `original_filename` (metadado), `uploaded_by_id`, `created_at` como
  colunas da tabela para auditoria, mesmo depois do arquivo físico ter
  sido removido.
- `Answer`, `CorrectionJob`, `AIExecution`, `HumanReview`: **nunca
  excluídos** por esta funcionalidade — `BL-AV-4B-05` é sobre a imagem,
  não sobre a resposta ou seu histórico de correção. Não existe cascade
  automático entre eles no modelo atual (seção 2.1); esta fatia não
  altera isso.
- `AuditEvent`: 1 evento por ação de exclusão (`action="DELETE_LOGICAL"`
  e, depois, `action="DELETE_PHYSICAL"` quando o arquivo for de fato
  removido), `resource_type="AnswerImage"`, `resource_id=image.id`.
  **Nenhum identificador é declarado universalmente "não sensível"**:
  o `before_json` registra apenas o conjunto MÍNIMO necessário para
  reconstruir a decisão de exclusão — `size_bytes`, `content_type`,
  `created_at` e a referência indireta (`image.id`, `answer_id`). NÃO
  copia para o log: o `original_filename` (pode conter nome do aluno,
  turma ou conteúdo), o `storage_filename` (caminho no disco), o
  `sha256_hash` (identificador de conteúdo que pode permitir
  correlação/vazamento por confronto), nem qualquer byte/trecho da
  imagem ou da transcrição. O hash e o nome original permanecem apenas
  nas colunas da própria tabela `answer_images` (acesso controlado pela
  autorização da API), não duplicados no log de auditoria. Mesmo padrão
  de `delete_question` quanto a gravar `before_json` ANTES da mutação,
  mas com a lista de campos restringida explicitamente ao mínimo.

### 4.4 Retenção configurável e expiração automática

| Opção | Descrição | Recomendação |
|---|---|---|
| A | Sem expiração automática nesta entrega; só exclusão manual/administrativa (mesma proposta já registrada em AV-S06B §7) | **recomendado para esta fatia** — não amplia escopo além do que `BL-AV-4B-05` pede agora |
| B | Janela de retenção configurável por variável de ambiente (ex. `ANSWER_IMAGE_RETENTION_DAYS`), job periódico de expiração automática | proposta futura, fora desta fatia — exigiria decisão de produto sobre o valor padrão e um mecanismo de agendamento (não existe nenhum scheduler/worker periódico na plataforma hoje) |

**Recomendação**: Opção A para esta fatia, com o desenho técnico já
preparado (campo `deleted_at`) para suportar a Opção B depois, sem
migração adicional quando/se for decidida.

### 4.5 Falhas parciais entre banco e armazenamento

Reaproveitando o padrão já usado e testado no upload
(`core/app/routers/images.py`, seção "Falha de armazenamento não deixa
registro no banco referenciando arquivo inexistente", AC-07 da AV-S06B):

- **Exclusão lógica**: é uma transação de banco só (`UPDATE
  answer_images SET deleted_at = ...`), sem tocar o filesystem —
  atômica por natureza, sem janela de falha parcial.
- **Remoção física** (fase posterior): existem duas ordens possíveis, e
  a classificação de cada falha precisa ser exata (não invertida):
  - **Ordem A — marcar `storage_deleted_at` no banco ANTES de apagar o
    arquivo**: se o `UPDATE` tiver sucesso mas o `unlink` falhar, sobra
    um **arquivo órfão** (bytes no disco sem registro ativo que os
    referencie) — o caso mais benigno, detectável por auditoria (4.7),
    sem risco de o sistema prometer um arquivo inexistente.
  - **Ordem B — apagar o arquivo ANTES de marcar o banco**: se o
    `unlink` tiver sucesso mas o `UPDATE` falhar, sobra um **registro
    apontando para um arquivo ausente** (o `AnswerImage` ainda tem
    `storage_filename` preenchido e `storage_deleted_at` NULL, mas o
    byte já não existe). Este é o caso **perigoso**: qualquer download
    subsequente que confie no registro tentará ler um arquivo que não
    existe. É exatamente a classe de falha que o upload já se protege
    contra na direção inversa (AC-07).
  - **Recomendação**: usar a **Ordem A** e tratar o download como
    autoritativo sobre o estado lógico (`deleted_at`), nunca sobre a
    mera presença do arquivo — assim, mesmo um arquivo órfão residual
    nunca é servido. A detecção de divergência (registro ativo apontando
    para arquivo ausente, OU arquivo sem registro ativo) é feita pela
    rotina de auditoria somente-leitura da seção 4.7, que **relata**, não
    corrige automaticamente.

### 4.6 Repetição da exclusão, concorrência e recuperação

- **Idempotência**: solicitar exclusão lógica de uma imagem já excluída
  logicamente deve ser um no-op (ou 409 com mensagem clara), nunca
  duplicar `AuditEvent` nem sobrescrever o `deleted_at` original —
  mesmo princípio de idempotência já decidido para a transcrição manual
  (`DEC-AV-040`, DP-3).
- **Concorrência**: dois pedidos simultâneos de exclusão da mesma
  imagem devem resultar em exatamente 1 efeito e 1 evento de auditoria,
  não 2 — resolvível com o mesmo padrão de `UPDATE ... WHERE deleted_at
  IS NULL` condicional já usado para lock otimista em
  `transcription_version` (`core/app/main.py`), sem precisar de nova
  infraestrutura de lock.
- **Recuperação dentro da janela de retenção**: como o arquivo físico
  só é removido depois da janela (seção 4.2, Opção B), restaurar dentro
  da janela é só reverter `deleted_at` para `NULL` — nenhuma
  reconstrução de bytes necessária. Depois da remoção física, a
  recuperação dos bytes não é mais possível pela aplicação (dependeria
  de backup externo, ver 4.8).

### 4.7 Arquivos órfãos

- **Definição operacional**: arquivo em
  `answer_images_storage_dir` sem nenhum `AnswerImage.storage_filename`
  correspondente (ou cujo registro já foi fisicamente limpo).
- Já existe um padrão de prevenção no código atual: o arquivo só é
  finalizado (`os.replace`) depois de todas as validações, e é removido
  se o commit do banco falhar (`core/app/routers/images.py`, lógica já
  homologada em AC-07 da AV-S06B — não reexecuto esse teste aqui, só
  reaproveito o padrão).
- Para exclusão, o risco inverso aparece (seção 4.5): arquivo removido
  mas registro não atualizado. Proposta: rotina de auditoria periódica
  (não um serviço automático nesta fatia — um script sob demanda,
  mesmo padrão dos scripts de verificação já usados em outras sprints)
  que compara o diretório de armazenamento com os registros no banco e
  relata divergências, sem agir automaticamente sobre elas.

### 4.8 Backups: o que a exclusão alcança e o que permanece retido

- A exclusão lógica e a remoção física alcançam exclusivamente o estado
  **corrente** do banco de dados e do diretório de armazenamento
  ativos.
- **Não há mecanismo de backup automatizado dos arquivos de imagem
  nesta plataforma hoje** (confirmado por ausência de qualquer script
  de backup para `answer_images_storage_dir` no repositório — distinto
  dos `pg_dump` manuais já usados para o banco em rodadas de migração,
  que também não cobrem o filesystem de imagens).
- Backups de banco feitos manualmente em rodadas anteriores
  (`pg_dump`, ex. `proposta_saneamento_human_reviews_duplicadas.md`)
  capturam o estado do banco **no momento do dump**, incluindo
  metadados de `AnswerImage` de imagens que, numa exclusão posterior,
  teriam sido removidas do banco corrente — ou seja, um backup de banco
  antigo pode reter metadados (não os bytes da imagem, que vivem só no
  filesystem) de uma imagem já excluída.
- **Esta é uma limitação a declarar, não a resolver nesta fatia**: não
  proponho mecanismo de expurgo retroativo de backups — isso dependeria
  de uma política de backup que não existe ainda na plataforma
  (`BL-AV-8-05`, ainda proposto). Reportar isso explicitamente evita a
  falsa impressão de que "excluir = desaparecer de todo lugar".

## 5. O que é política de produto, mecanismo técnico, e decisão institucional pendente

| Categoria | Item |
|---|---|
| **Decisão institucional pendente** (fora do controle desta trilha) | Política formal de retenção/exclusão de dados reais (LGPD/diretrizes educacionais) — depende de `DEC-AV-013`/`014` gerais e de `BKL-AV-001`; não decidida aqui, nem com prazo inventado |
| **Política de produto** (decisão de Rafael, ver tabela §6) | Quem pode excluir; exclusão lógica vs. física; janela de retenção antes da remoção física |
| **Mecanismo técnico** (não exige nova aprovação — já decorre de decisões já tomadas) | Estrutura de `AuditEvent` por exclusão; idempotência/concorrência via `UPDATE` condicional; prevenção/detecção de arquivos órfãos; ausência de cascade para `Answer`/`CorrectionJob`/`HumanReview` |

## 6. Decisões tomadas por Rafael (autorização da 1ª fatia)

> Rafael aprovou a 1ª fatia de `BL-AV-4B-05` e autorizou implementação
> LOCAL após esta revisão dirigida. As decisões abaixo estão **tomadas**
> (não mais em aberto). Observação importante: **D2 é mais restritiva do
> que a recomendação original deste desenho** — a recomendação permitia
> exclusão nos estágios A **e** B; Rafael a restringiu a permitir apenas
> no estágio A (enquanto aguarda confirmação da transcrição), bloqueando
> já no estágio B.

| # | Decisão tomada | Detalhe |
|---|---|---|
| **D1** | Exclusão **lógica reversível**, com recuperação explícita. **Sem remoção física** nesta fatia. | Campo `deleted_at` (+ `deleted_by_id`) no `AnswerImage`; nenhuma remoção de byte do disco, nenhum `DELETE` físico de registro. A coluna `storage_deleted_at`/expurgo físico (seção 4.2 Opção B) fica preparada no desenho mas **não implementada** agora. |
| **D2** | Exclusão permitida **apenas enquanto a resposta aguarda confirmação da transcrição** (estágio A). **Bloqueada após a confirmação** (estágios B, C e D), com ou sem `CorrectionJob`/`HumanReview`, **inclusive para admin** nesta funcionalidade. | O guard de estágio é `transcription_status == AGUARDANDO_TRANSCRICAO` (estágio A). Em B/C/D retorna 409 (ou equivalente) mesmo para admin. Isto substitui a recomendação anterior "livre em A/B": **B passa a ser bloqueado**. |
| **D3** | **Nenhum prazo operacional** definido agora. **Não implementar expurgo físico nem automático.** | Não aprova retenção indefinida nem resolve a política institucional geral (`DEC-AV-013`/`014`, `BKL-AV-001` seguem pendentes). Sem variável de janela ativa, sem scheduler. |

Limites preservados pela autorização: sem stage/commit/push/merge, sem
novos worktrees, sem alteração em bancos protegidos
(`avalia_dev`/apresentação), sem expurgo físico, sem P5, sem migração
operacional, sem OCR, sem deploy, sem promoção de baseline. Numerador
preservado em **22/70**; `BL-AV-4B-05` permanece **parcial** (prazo,
remoção física, tratamento posterior de metadados e backups seguem
pendentes).

Decisões **não listadas aqui** por serem puramente técnicas (não exigem
nova aprovação de Rafael, pois já decorrem de padrões/decisões
existentes): formato do `AuditEvent`, mecanismo de idempotência via
`UPDATE` condicional, ausência de cascade entre `Answer` e
`AnswerImage`, estrutura da rotina de detecção de arquivos órfãos.

## 7. Mapa de impacto técnico (arquivos a tocar, quando implementado)

> Alinhado às decisões D1/D2/D3 da seção 6: **nesta fatia NÃO há coluna
> `storage_deleted_at` nem remoção física** (D1/D3). A migração adiciona
> apenas os campos da exclusão lógica reversível.

| Arquivo | Mudança prevista | Risco |
|---|---|---|
| `core/app/models.py` | `AnswerImage` ganha `deleted_at: datetime \| None` e `deleted_by_id: str \| None` (FK users). **Sem** `storage_deleted_at` nesta fatia (D1/D3) | baixo — colunas nullable, aditivas |
| `core/alembic/versions/` | nova migração aditiva (mesmo padrão de `f2a9c4e6b1d3`): 2 colunas nullable, downgrade bloqueado se houver `deleted_at` não nulo | baixo |
| `core/app/routers/images.py` | novos endpoints `DELETE /v1/answer-images/{image_id}` (exclusão lógica) e `POST /v1/answer-images/{image_id}/restore` (restauração); guard de estágio **A apenas** (`AGUARDANDO_TRANSCRICAO`), reaproveitando o padrão de autorização por propriedade já usado no upload/download; `UPDATE ... WHERE deleted_at IS NULL` condicional para idempotência/concorrência | médio — guard de estágio novo + proteção de corrida, testado por ACD |
| `core/app/main.py` | guard de **confirmação de transcrição** passa a exigir ao menos uma imagem ativa (`deleted_at IS NULL`): confirmação é impedida se todas as imagens da resposta estiverem logicamente excluídas (requisito do item 2 de Rafael); proteção contra corrida excluir↔restaurar↔confirmar via releitura condicional dentro da transação, sem checagem de estágio que invalide antes do commit | médio — toca o fluxo de confirmação, testado por ACD de concorrência |
| `frontend/src/pages/ImageAnswerPage.tsx` | ação de exclusão visível só no estágio A; indicação visual de imagem excluída + ação de restaurar; download bloqueado durante exclusão lógica; aviso quando bloqueada (B/C/D) | baixo |
| novo script (fora da aplicação, sob demanda) | detecção somente-leitura de divergências: registro ativo sem arquivo, e arquivo sem registro ativo (seção 4.7) | baixo — somente leitura, não altera dados |

## 8. Critérios de aceite (ACD) — alinhados a D1/D2/D3

> Reformulados para refletir D2 (exclusão **permitida só no estágio A**;
> **bloqueada em B/C/D inclusive para admin**) e D1 (exclusão lógica
> reversível, **sem** remoção física).

| ID | Critério |
|---|---|
| ACD-01 | Professor dono/vinculado pode excluir logicamente a imagem **apenas no estágio A** (`transcription_status == AGUARDANDO_TRANSCRICAO`) |
| ACD-02 | Exclusão é **bloqueada (409)** nos estágios B, C e D (transcrição já confirmada), **inclusive para admin** — não só quando há `CorrectionJob`/`HumanReview`, mas a partir da confirmação (estágio B) |
| ACD-03 | Exclusão lógica **não remove o arquivo físico** nem apaga `Answer`/`CorrectionJob`/`AIExecution`/`HumanReview` |
| ACD-04 | Restauração (`restore`) reverte `deleted_at`→NULL para imagem logicamente excluída **ainda no estágio A**, restabelecendo download; registra `AuditEvent` próprio |
| ACD-05 | `AuditEvent` de exclusão/restauração registra apenas o conjunto MÍNIMO de metadados (size_bytes, content_type, created_at, ids), **nunca** original_filename, storage_filename, sha256_hash, nem conteúdo |
| ACD-06 | Repetir a exclusão lógica de uma imagem já excluída é idempotente (não duplica `AuditEvent`, não sobrescreve `deleted_at`); repetir restauração de imagem já ativa idem |
| ACD-07 | Duas solicitações concorrentes de exclusão da mesma imagem resultam em exatamente 1 efeito e 1 `AuditEvent` (lock otimista `WHERE deleted_at IS NULL`) |
| ACD-08 | Download de imagem logicamente excluída retorna 404/410, não o conteúdo |
| ACD-09 | Confirmação da transcrição é **impedida** quando não houver nenhuma imagem ativa (`deleted_at IS NULL`) na resposta |
| ACD-10 | Concorrência excluir↔confirmar: uma checagem de estágio não pode ficar inválida antes do commit — a confirmação e a exclusão não podem ambas ter sucesso para a mesma imagem no mesmo instante (testado em PostgreSQL real) |
| ACD-11 | Professor sem vínculo recebe 403 ao tentar excluir/restaurar imagem de avaliação alheia; vínculo não concede permissão a qualquer professor além das regras de mutação vigentes |
| ACD-12 | Restauração de imagem cujo arquivo esteja ausente **não** é prometida: retorna erro coerente e preserva o estado para diagnóstico (detecção somente-leitura, sem reconstrução de bytes) |
| ACD-13 | Rotina de detecção de divergências (script sob demanda, somente leitura) identifica registro-sem-arquivo e arquivo-sem-registro em cenário induzido, sem alterar dados |
| ACD-14 | (R3) Resposta com DUAS imagens ativas; uma é excluída logicamente em A; a transcrição é confirmada usando a OUTRA (resposta → B); restaurar a imagem excluída retorna **409, inclusive para admin** — o conjunto de imagens de uma transcrição confirmada não é alterado |
| ACD-15 | Imagem logicamente excluída permanece **recuperável pela interface** enquanto em A: aparece numa projeção de "excluídas" (metadados mínimos: id, deleted_at, deleted_by_id) com ação de restaurar, mas **sem download** e **sem** reexpor sha256_hash/original_filename nesse caminho; imagens ativas seguem na projeção normal com o contrato existente intacto |

## 9. Sequência de implementação e testes (autorizada — 1ª fatia)

1. Migração aditiva (`deleted_at`, `deleted_by_id` — 2 colunas nullable)
   em ambiente isolado, com teste de `downgrade` bloqueado se houver
   `deleted_at` não nulo (mesmo padrão já usado nesta trilha).
2. Endpoints de exclusão lógica + restauração + guard de estágio A, com
   proteção de corrida (lock otimista), cobrindo ACD-01 a ACD-12 —
   testes unitários/integração em PostgreSQL isolado, reaproveitando os
   fixtures de `test_answer_images.py`/`test_image_answers.py`.
3. Ajuste no guard de confirmação de transcrição (ACD-09/ACD-10) com
   teste de concorrência real em PostgreSQL isolado.
4. Script de detecção de divergências (ACD-13), somente leitura, testado
   contra diretório de teste com divergência induzida.
5. Frontend: exclusão/restauração visíveis só no estágio A, indicação de
   excluída, download bloqueado durante exclusão lógica; validação em
   navegador real (ambiente isolado próprio, mesmo padrão das demos
   desta trilha).
6. Revisão independente do Antigravity, **limitada** ao desenho (antes
   do código) e à implementação (ao final) desta fatia — sem repetir a
   auditoria geral de AV-S06B/AV-S08B.
7. Codex só é acionado se Antigravity ou a implementação revelarem um
   risco concreto (ex.: corrupção real em concorrência), não como rotina.

## 10. Papéis desta fatia

- **Claude Code**: prepara o desenho técnico detalhado (migração,
  endpoint, guard de estágio) a partir deste documento, quando
  autorizado a implementar.
- **Antigravity**: revisão independente limitada ao contrato/estágios
  desta fatia (não repete a revisão completa de AV-S06B/AV-S08B).
- **Codex**: só diante de risco concreto identificado durante a
  implementação ou revisão, não como rotina.

## 11. Não autorizado nesta rodada

Implementação de código, migração, criação ou execução de endpoint de
exclusão, início de serviços, stage/commit/push/merge, exclusão real de
qualquer arquivo ou dado, alteração em bancos protegidos
(`avalia_dev`/apresentação), OCR, deploy, promoção de baseline. Numerador
permanece **22/70**; itens parciais (`BL-AV-4B-10`/`11`/`13`/`15`)
inalterados.

## 12. Revisão independente do Antigravity e incorporação das ressalvas

Parecer completo arquivado em `parecer_antigravity_desenho.md` (mesma
pasta). Resultado: **APROVADO COM RESSALVAS**. O revisor confirmou, lendo
o código real, as 4 correções e a cobertura de D1/D2/D3, e levantou 4
ressalvas. Verifiquei cada uma de forma independente (não confiei só no
parecer) e as incorporo abaixo.

### R2 (Alta) — ponto de serialização da corrida excluir↔confirmar

Confirmado: a confirmação de transcrição executa `update(Answer) WHERE
transcription_version == expected AND transcription_status ==
AGUARDANDO_TRANSCRICAO` (`main.py:859-868`), enquanto a exclusão de
imagem operaria sobre `answer_images`. São **tabelas distintas**: o lock
otimista de `transcription_version` sozinho NÃO serializa as duas
operações. **Especificação adicionada**: ambos os caminhos (exclusão de
imagem e confirmação de transcrição) devem adquirir um lock na **linha
`answers` correspondente** antes de decidir — `SELECT ... FROM answers
WHERE id = :answer_id FOR UPDATE` dentro da transação — de modo que:
- a confirmação, já sob o lock da `Answer`, reavalia "existe imagem ativa
  (`deleted_at IS NULL`)?" imediatamente antes do `UPDATE` (ACD-09/10),
  sem que a checagem fique inválida antes do commit;
- a exclusão, sob o mesmo lock, reconfirma o estágio A da `Answer` antes
  de marcar a imagem como excluída.
Assim as duas operações se serializam no mesmo recurso (`answers.id`),
eliminando a janela em que ambas teriam sucesso. Teste de concorrência
real em PostgreSQL isolado (ACD-10) deve exercitar exatamente este
cruzamento (duas conexões simultâneas: uma excluindo a última imagem
ativa, outra confirmando).

### R1 (Média) — filtro `deleted_at IS NULL` nas leituras

Confirmado: `_answer_with_images` (`main.py:766-771`) consulta
`AnswerImage` por `answer_id` **sem** filtrar `deleted_at`; o mesmo vale
para a listagem. **Especificação adicionada ao §7**: as leituras de
imagem para uso de transcrição (`_answer_with_images`,
`list_image_answers`, download) filtram `deleted_at IS NULL` por padrão —
mas a exclusão **não** torna a imagem inacessível pela interface: existe
uma projeção/rota separada de "imagens excluídas" (metadados mínimos +
ação de restaurar, ACD-15) para que a restauração autorizada continue
alcançável pela UI enquanto em A. Ou seja, filtrar do fluxo de
transcrição ≠ sumir do sistema. Contratos existentes de imagens ativas
não têm campos removidos além do necessário a esta entrega.

### R4 (Média) — exposição de `original_filename`/`sha256_hash` na API

Confirmado: `AnswerImageOut` (`schemas.py:177-186`) expõe
`original_filename` e `sha256_hash`. Isto é **na API autenticada**, não
em log (a proibição da §4.3 continua valendo só para o `AuditEvent`/log).
**Decisão técnica desta fatia**: imagens excluídas NÃO aparecem na
listagem padrão (R1); a UI de "imagem excluída / restaurar" usa uma
projeção enxuta (id, estado `deleted_at`, quem excluiu) **sem**
reexpor `sha256_hash` nem `original_filename` para o caminho de exclusão
— mantendo o mesmo princípio de mínimo necessário da §4.3, agora também
no contrato de saída do fluxo de exclusão.

### R3 (Baixa) — DECIDIDO por Rafael: opção (a), bloquear em B

**Decisão de Rafael (produto):** a restauração é permitida **somente
enquanto a resposta aguarda confirmação da transcrição (estágio A)**.
Após a confirmação, restaurar retorna **409, inclusive para admin**. O
conjunto de imagens de uma transcrição já confirmada **não é alterado
silenciosamente**; retificação posterior fica **fora desta fatia**.

Consequência de implementação (simétrica a D2): o endpoint de
restauração aplica o mesmo guard de estágio da exclusão — só opera com
`Answer.transcription_status == AGUARDANDO_TRANSCRICAO`, sob o lock da
linha de `answers` (ver R2). Se o estágio avançou para B entre a
exclusão e a tentativa de restaurar, retorna 409 com o estado atual,
sem restaurar e sem efeito colateral. Isto é homologável como
comportamento definido (não mais um default provisório).

> Caso de borda coberto por teste dedicado (ACD-14): resposta com DUAS
> imagens ativas; uma é excluída logicamente em A; a transcrição é
> confirmada usando a OUTRA (resposta vai para B); a tentativa de
> restaurar a imagem excluída retorna **409, inclusive para admin**.
