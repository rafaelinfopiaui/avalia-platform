---
id: "EXEC-2026-10-14-09"
tipo: execucao
sprint: "AV-S08B (transcrição manual e confirmação humana) — conclusão do escopo autorizado"
gerado_em: "2026-10-14T11:20:00-03:00"
executor: "Claude Code (implementação do delta), Hermes (verificação independente + validação de integração + reconciliação documental), Antigravity (revisão independente do delta)"
status: "aprovação técnica local — escopo autorizado concluído, sem publicação/homologação/integração nesta rodada"
base: "main e8b08646cfee5e9fea70d8e9bbcb4cf39f5a3d2d"
branch: "feat/av-s08b-transcricao-manual"
---

# Snapshot EXEC-2026-10-14-09 — Conclusão do escopo autorizado de AV-S08B: ação de correção + validação de integração + reconciliação documental

> Continuação do snapshot de encerramento EXEC-2026-10-14-08. Rodada LOCAL:
> sem stage/commit/push nesta fatia. Não promove baseline. Esta execução
> completa o escopo JÁ AUTORIZADO da sprint (nenhuma decisão de produto nova
> foi necessária, conforme instrução explícita de Rafael) e corrige 5
> imprecisões de registro identificadas por Rafael no snapshot anterior.

## 1. Resumo

Três frentes concluídas nesta execução, todas dentro do escopo já autorizado
de `AV-S08B` — não houve necessidade de nova decisão de produto:

1. **Caminho de interface para solicitar correção da resposta IMAGE
   confirmada** (DELTA pequeno e cirúrgico sobre a entrega anterior, sem
   tocar em nenhum endpoint de backend já existente).
2. **Validação da integração completa** foto→rascunho→confirmação→correção
   (AI Engine simulado, identificado explicitamente)→revisão humana final,
   em ambiente isolado descartável.
3. **Reconciliação de 5 imprecisões** nos registros de governança anteriores,
   apontadas por Rafael (DEBT-AV-014 já integrado, DoD sem itens de
   publicação marcados como concluídos, testes PG como execução local sem
   ampliar CI, custo como estimativa reportada, e o incidente de dispatch
   duplicado preservado com a lição de processo adotada).

## 2. Frente 1 — Ação de solicitar correção (DELTA)

### 2.1 Investigação prévia (antes de qualquer código)

Confirmado que o backend **já suportava** a correção de resposta IMAGE
confirmada sem nenhuma alteração: `POST /v1/answers/{answer_id}/corrections`
(`core/app/main.py`, função `request_correction`) só verifica
`transcription_status`/`text`, sem distinguir a origem TEXT/IMAGE. Faltava
apenas o caminho de interface. Por isso o delta foi deliberadamente pequeno:
nenhum endpoint novo, nenhuma migração, nenhuma alteração em
`services/correction.py`.

### 2.2 Implementação (Claude Code, CLI real, delta isolado)

Antes de disparar, confirmei por `ps aux` que não havia nenhum processo
`claude -p` em execução nesta branch (lição direta do incidente de dispatch
duplicado da rodada anterior) e usei um arquivo de saída com nome distinto
do usado anteriormente, para não repetir a colisão de arquivo que causou
aquele incidente.

- `frontend/src/pages/ImageAnswerPage.tsx` (+61 linhas sobre o diff anterior,
  total agora +270): novo componente `CorrectionRequest` — botão "Solicitar
  análise da IA" renderizado **somente** quando
  `transcription_status === 'TRANSCRICAO_CONFIRMADA'`; reutiliza
  `requestCorrection(answer.id)` já existente em `api.ts` (mesma função usada
  pelo fluxo textual); navega para `/correcoes/{job.id}` (rota já existente);
  estados de carregamento/sucesso/erro; nova função `correctionError` tratando
  `ANSWER_NOT_TRANSCRIBED`, `RUBRIC_NOT_PUBLISHED`, 401/403/404.
- `core/app/tests/test_manual_transcription.py` (ampliado, +3 testes): texto
  exato confirmado chega ao AI Engine (não o rascunho); `attempt` incrementa
  no mesmo `answer_id` em retentativas; regressão do bloqueio pré-confirmação.
- **Nenhum arquivo de backend de produção alterado** (`main.py`, `models.py`,
  `schemas.py`, `services/correction.py` idênticos à rodada anterior —
  confirmado por mim e pelo Antigravity, independentemente).

### 2.3 Verificação independente (Hermes)

- `pytest app/tests/test_manual_transcription.py -q`: **33 passed, 5 skipped**
  (30 anteriores + 3 novos; 5 skipped = concorrência real sem env var, como
  sempre).
- `pytest app/tests -q` (suíte completa): **204 passed, 5 skipped** (201 + 3
  novos; zero regressão).
- `ruff check app`: All checks passed.

### 2.4 Revisão independente do Antigravity (SÓ o delta, sem reabrir a auditoria geral)

Prompt dedicado instruindo explicitamente a não reabrir a revisão já feita
(`revisao_implementacao_antigravity.md`) e revisar apenas os arquivos que
mudaram nesta rodada. Veredito: **APROVADO**, sem ressalva bloqueante.
Reexecutou de forma independente: os 3 testes novos + regressão, suíte
isolada, `tsc`/`build`/`lint`, e confirmou por diff que nenhum backend foi
tocado. 2 achados, ambos informativos (não-bloqueantes): rótulo "nova
análise" é só estado local de sessão (limitação documentada, aceitável sem
endpoint novo); tratamento de erro com defesa em profundidade (elogiado como
boa prática). Parecer completo:
`evidence/AV-S08B/revisao_delta_correcao_antigravity.md`.

## 3. Frente 2 — Validação da integração completa (Hermes, ambiente isolado)

Pendência explícita identificada por Rafael: a validação visual da rodada
anterior (EXEC-08 §4) comprovou que a *solicitação* de correção era aceita
(202) com engine morto de propósito — não comprovou o fluxo de correção
*completo* até a revisão humana final. Esta frente fecha essa lacuna.

### 3.1 Ambiente

- Banco PostgreSQL descartável `av_s08b_integracao_test` (migrado ao head
  `f2a9c4e6b1d3`, dropado ao final).
- **AI Engine real, em modo simulado explícito**
  (`AI_ENGINE_MODE=simulated`, porta `127.0.0.1:8401`) — modo nativo do
  próprio serviço (`ai-engine/app/cascade.py`), não um mock construído pelo
  Hermes. Log do próprio AI Engine confirma
  `"configured_engine_mode": "simulated"` e
  `"Executando em modo simulado explícito (RN-017)"`.
- Core isolado (`127.0.0.1:8411`, `ACADEMIC_MODULE_ENABLED=false`,
  `AI_ENGINE_URL=http://127.0.0.1:8401` apontando para o simulado acima) —
  `GET /v1/health` confirmou `"ai_engine": true` (conectividade real com o
  simulado, diferente da rodada anterior onde a porta estava morta).
- Vite (`127.0.0.1:5411`) e Chrome real via CDP (`127.0.0.1:9337`).
- Seed: prof1 (dono) + prof2 (não-dono); avaliação com 1 questão (rubrica já
  publicada) e 1 resposta por imagem já persistida.

### 3.2 Fluxo executado ao vivo, em navegador real, ponta a ponta

| Etapa | Resultado |
|---|---|
| Foto persistida → retomada na tela | **PASS** — resposta recuperada ao abrir a seleção |
| Rascunho digitado | — (etapa intermediária, seguiu direto à confirmação) |
| Confirmação humana (revisão em 2 passos, aviso de irreversibilidade) | **PASS** — "Transcrição confirmada" com autoria e data |
| Botão "Solicitar análise da IA" aparece só após confirmação | **PASS** |
| Solicitação explícita de correção | **PASS** — navegação automática para `/correcoes/{job_id}/revisao` |
| Resultado da IA (modo simulado) | **PASS** — alerta amarelo explícito "Análise em modo simulado. Este resultado não foi gerado pelo modelo real..." visível na tela; `flags` incluindo `SIMULATED_MODE` |
| Revisão humana final | **PASS** — decisão "Aprovar como decisão humana" registrada, navegação de volta a `/avaliacoes` |

### 3.3 Confirmações por banco de dados e log do servidor (não só pela tela)

- `answers`: 1 única linha, `source=IMAGE`, `transcription_status=TRANSCRICAO_CONFIRMADA`,
  `transcription_version=1`, `transcription_confirmed_by_id=<prof1>`, texto
  com 122 caracteres.
- `correction_jobs`: 1 linha, `answer_id` **idêntico** ao da resposta por
  imagem original (nenhuma resposta nova criada), `attempt=1`,
  `status=SUGERIDA`.
- `ai_executions`: `engine_mode=simulated` (coluna gravada no banco,
  confirmando o modo no histórico permanente, não só na tela).
- `human_reviews`: 1 linha, `decision=APPROVE`, `final_total=5.00`,
  `reviewer_id=<prof1>`.
- `audit_events`: `action=manual_transcription_confirmed`,
  `resource_id=<mesmo answer_id>`, `actor_id=<prof1>` — origem **MANUAL**
  preservada no histórico (não há nenhum evento de origem OCR/automática,
  porque esta fatia não implementa isso).
- **Texto confirmado, não aproximado**: a prova de identidade exata vem do
  teste automatizado de backend
  `test_confirmed_image_answer_correction_uses_same_answer_and_confirmed_text`
  (`core/app/tests/test_manual_transcription.py:501-522`), que intercepta o
  `httpx.AsyncClient` usado pelo worker (`_CapturingAIEngine`) e faz
  comparação de **conteúdo integral** — `assert [p["answer_text"] for p in
  ai_engine.payloads] == [confirmed_text]` — com um texto propositalmente
  diferente do rascunho anterior (`"Rascunho diferente."` vs
  `"Texto confirmado\ncom quebra de linha e acentuação: ação."`), incluindo
  quebra de linha e acentuação, não apenas um texto simples. Reexecutado de
  forma isolada nesta rodada: **1 passed**
  (`pytest -k test_confirmed_image_answer_correction_uses_same_answer_and_confirmed_text`).
  Esse teste exercita exatamente o mesmo código (`run_correction_job`,
  `payload["answer_text"] = answer.text`) usado pela validação em navegador
  real da §3.2 acima — o log do Core naquela rodada registrou
  `"answer_text_len": 122` coincidindo com o `char_length(text)` do banco
  (também 122), o que é consistente com o texto estar correto, mas **a
  igualdade de comprimento sozinha não prova identidade de conteúdo**
  (dois textos diferentes podem ter o mesmo tamanho); a prova de conteúdo
  idêntico vem do teste automatizado citado acima, não da coincidência de
  comprimento da validação manual.

### 3.4 Limpeza

AI Engine, Core, Vite e Chrome encerrados; banco `av_s08b_integracao_test`
dropado; diretórios temporários removidos. Portas 8401/8411/5411/9337
livres. `avalia_dev` (16 `human_reviews`, `a9f4c2e71b06`) e
`avalia_apresentacao_demo_20261002` (`a9f4c2e71b06`) confirmados intactos
antes e depois desta frente também.

## 4. Frente 3 — Reconciliação de registros (5 itens apontados por Rafael)

### 4.1 `DEBT-AV-014` já homologado e integrado

Corrigido em `docs/governance/registers/technical_debts.md`: a entrada
anterior dizia "integração aguarda o merge efetivo do PR #17". Isso estava
desatualizado — o PR #17 já havia sido mergeado (SHA
`e8b08646cfee5e9fea70d8e9bbcb4cf39f5a3d2d`, confirmado por `git log` e usado
como baseline de `AV-S08B` desde a sprint de abertura). Reescrito como
**RESOLVIDO, HOMOLOGADO E INTEGRADO**, com nota de reconciliação datada
explicando a correção (sem apagar o texto histórico, por convenção do
projeto).

### 4.2 DoD sem itens de publicação marcados como concluídos

Revisada a sprint `sprint_AV-S08B_transcricao_manual_confirmacao_humana.md`
§9: nenhum dos itens de DoD fala em publicação/homologação/integração da
*própria* `AV-S08B` (eles falam de evidência real, suíte sem regressão,
lint, revisão independente, AI Engine identificado, bancos protegidos
intactos, governança atualizada, diff local revisado — todos aplicáveis e
corretamente concluídos nesta rodada LOCAL). O item "Governança atualizada"
já trazia a ressalva "sem encerrar itens mais amplos que a parte manual
entregue". Nenhuma mudança necessária nesta seção — já estava correta quanto
a não reivindicar publicação/homologação da própria fatia.

### 4.3 Testes PostgreSQL como execução local, não cobertos por CI

Já registrado assim desde o snapshot anterior (EXEC-08 §3): "5 skipped =
testes de concorrência real sem `AVALIA_TEST_POSTGRES_URL`" e, nas
pendências, "CI atual não roda os 5 testes de concorrência real... candidato
a melhoria de infraestrutura, **não bloqueante**". Reforçado aqui: nesta
rodada (frente 1), os 5 testes de concorrência continuam skipped sem a env
var — comportamento esperado, não alterado, e **nenhuma infraestrutura de CI
foi ampliada** (instrução explícita de Rafael nesta autorização).

### 4.4 Custo como estimativa reportada, não cobrança comprovada

Nenhum documento desta sprint registrou o valor de US$ 3,59 como cobrança
comprovada — ele apareceu apenas na minha mensagem de chat anterior,
resumindo o JSON de retorno da CLI (`total_cost_usd`). Por clareza: esse
valor é a **estimativa que a própria ferramenta `claude -p` reportou** para
a chamada, não uma fatura, extrato ou cobrança confirmada por nenhum canal de
billing. Nenhum snapshot/sprint desta fatia cita esse número — não havia
necessidade de correção nos documentos; registrado aqui para constar que o
valor, se mencionado novamente, deve sempre vir qualificado como "estimativa
reportada pela ferramenta".

### 4.5 Incidente de dispatch duplicado preservado + lição de processo

O incidente (duas instâncias `claude -p` rodando em paralelo na rodada
anterior, por eu não ter detectado a primeira a tempo) permanece registrado
no relatório `local-nao-versionado/claude_report_av_s08b_instancia_16998_interrompida.md`
e no histórico desta conversa — não foi apagado nem reescrito. Lição
adotada nesta rodada, de forma concreta:
1. Antes de qualquer novo dispatch do Claude Code, rodei `ps aux | grep
   "claude -p"` para confirmar ausência de processo já em execução na mesma
   branch (feito antes da frente 1 desta execução).
2. Usei um arquivo de saída (`/tmp/av_s08b_delta_claude_output.json`) com
   nome **diferente** do usado na rodada anterior
   (`/tmp/av_s08b_claude_output.json`), eliminando a causa raiz que fez os
   dois processos da rodada anterior colidirem no mesmo arquivo.
3. O mesmo padrão foi aplicado ao Antigravity (nome de arquivo de saída e de
   parecer distintos: `revisao_delta_correcao_antigravity.md`, não
   sobrescrevendo `revisao_implementacao_antigravity.md`).

## 5. Integridade (confirmada ao final de todas as 3 frentes)

- `avalia_dev`: 16 `human_reviews`, `a9f4c2e71b06` — idêntico ao estado
  inicial de toda a sprint.
- `avalia_apresentacao_demo_20261002`: `a9f4c2e71b06` — idêntico.
- Nenhum banco de teste residual (`av_s08b_integracao_test` e todos os
  anteriores dropados; `psql -lqt` confirmado limpo).
- Nenhuma porta de ambiente isolado aberta ao final (8401/8411/5411/9337
  livres).

## 6. Diff local acumulado (sem stage/commit/push)

9 arquivos modificados + 2 novos de código + 4 novos de governança (contando
esta rodada):
- `core/app/main.py` (+179, inalterado nesta rodada — confirmado por diff
  idêntico ao da rodada anterior).
- `core/app/models.py` (+12, inalterado nesta rodada).
- `core/app/schemas.py` (+11, inalterado nesta rodada).
- `core/alembic/versions/f2a9c4e6b1d3_...py` (novo, inalterado nesta rodada).
- `core/app/tests/test_manual_transcription.py` (novo na rodada anterior,
  **+3 testes nesta rodada**).
- `frontend/src/types.ts` (+11, inalterado nesta rodada).
- `frontend/src/services/api.ts` (+16, inalterado nesta rodada).
- `frontend/src/pages/ImageAnswerPage.tsx` (+209 na rodada anterior,
  **+270 total nesta rodada** — delta de +61 linhas, botão de correção).
- `docs/governance/registers/decisions.md` (+2, inalterado nesta rodada).
- `docs/governance/registers/technical_debts.md` (**+1 linha reescrita nesta
  rodada** — reconciliação do DEBT-AV-014).
- `docs/governance/snapshots/latest_execution.md` (**reescrito nesta
  rodada** para apontar a este snapshot).

## 7. Estado final

- Rodada LOCAL: branch `feat/av-s08b-transcricao-manual` (base `e8b0864`);
  working tree não-staged; nenhuma ação remota; nenhum commit nesta branch
  (confirmado: `git log main..HEAD` vazio).
- Progresso homologado permanece **19/70**; `AV-S05B` parcial;
  `BL-AV-4B-05` pendente; `BL-AV-4B-10`/`11` permanecem **parciais** (falta
  a parte de OCR) — nenhuma mudança nestes números nesta rodada.
- Escopo já autorizado de `AV-S08B` está **concluído** (planejamento,
  decisões de produto, implementação, 2 rodadas de revisão independente do
  Antigravity, validação visual, validação de integração completa, e
  reconciliação documental). Publicação/homologação/integração permanecem
  decisão de Rafael, não incluída nesta rodada.
- Pacote recuperável: código e evidências no working tree da branch;
  relatórios em `docs/governance/evidence/AV-S08B/` e
  `local-nao-versionado/claude_report_av_s08b*.md` (git-ignored).
