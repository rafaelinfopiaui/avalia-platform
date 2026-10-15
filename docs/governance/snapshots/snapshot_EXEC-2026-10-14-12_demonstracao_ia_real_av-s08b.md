---
id: "EXEC-2026-10-14-12"
tipo: execucao
sprint: "AV-S08B (transcrição manual e confirmação humana) — demonstração de inferência real"
gerado_em: "2026-10-15T00:58:00-03:00"
executor: "Hermes"
status: "demonstração concluída em ambiente descartável; não altera numerador nem homologação"
base: "main efaa337c04070f59e01d217010f17a92b89258ca (código integrado, sem alteração)"
---

# Snapshot EXEC-2026-10-14-12 — Demonstração do fluxo integrado com IA local REAL (banco isolado)

> Demonstração técnica autorizada por Rafael. Comprova que o caminho
> completo (foto → transcrição MANUAL → confirmação → solicitação
> explícita de análise → resultado real → revisão humana) funciona com
> **inferência real** do Ollama local, em vez do modo simulado usado em
> todas as rodadas de validação anteriores desta trilha. **Não é OCR**
> (a transcrição permanece 100% manual) e **não é avaliação formal da
> qualidade pedagógica da IA** (não mede acerto/precisão da correção
> sugerida).

## 1. Código e ambiente

- Código: HEAD exato de `main`, SHA `efaa337c04070f59e01d217010f17a92b89258ca`
  (nenhuma alteração de código nesta rodada; confirmado antes de iniciar
  por `git log -1` e `git merge-base HEAD main` no checkout principal).
- Banco descartável: `avalia_demo_ia_real_av_s08b` (criado com `createdb`,
  migrado com `alembic upgrade head` até `f2a9c4e6b1d3`, dropado ao final
  com `dropdb`).
- Storage: diretório temporário dedicado
  `/tmp/avalia_demo_ia_real_av_s08b_storage` (removido ao final com
  `rm -rf`; nunca usou `core/var/answer_images`, confirmado intacto
  antes/depois — 1 arquivo pré-existente, nenhum novo).
- Serviços dedicados, portas isoladas das usadas em qualquer rodada
  anterior ou compartilhada:
  - AI Engine: porta `:8101`, `AI_ENGINE_MODE=real`,
    `AI_MODEL_NAME=qwen2.5:7b-instruct-q4_K_M`,
    `OLLAMA_URL=http://localhost:11434` (Ollama já em execução como
    serviço do sistema, **não reiniciado**, nenhum modelo baixado —
    `qwen2.5:7b-instruct-q4_K_M` já presente localmente, confirmado por
    `ollama list` antes de iniciar);
  - Core: porta `:8206`, `DATABASE_URL` apontando exclusivamente para o
    banco descartável, `JWT_SECRET` dedicado (não usado em nenhum outro
    ambiente), `AI_ENGINE_URL=http://localhost:8101`,
    `ACADEMIC_MODULE_ENABLED=false`;
  - Frontend (Vite): porta `:5190`, `VITE_API_URL` apontando para o Core
    isolado;
  - Chrome via CDP: `--remote-debugging-port=9337`,
    `--user-data-dir=/tmp/avalia_demo_ia_real_av_s08b_chrome` (removido
    ao final).
- Nenhuma configuração global alterada; nenhum serviço compartilhado
  reiniciado (Ollama permaneceu rodando o tempo todo, inclusive depois
  do encerramento da demo).

## 2. Dados fictícios

- Seed padrão já existente no repositório (`core/app/seed.py`,
  reaproveitado sem alteração): 1 professor fictício
  (`professor.demo@avalia-platform.example`), 1 avaliação publicada
  ("Estruturas de Dados — Avaliação 1"), 1 questão, 1 rubrica publicada
  com 4 critérios (soma 6.00).
- 1 imagem fictícia gerada localmente (PNG sintético com texto digitado
  via Pillow, 8.8 KB) — conteúdo irrelevante para a demonstração, já que
  a transcrição é manual (não há OCR a comprovar).

## 3. Execução do fluxo em navegador real (Chrome via CDP)

Sequência operada manualmente pela UI, confirmada por log do Core
(`core` em `:8206`, timestamps reais):

| Passo | Horário (UTC) | Evidência |
|---|---|---|
| Login do professor | 00:53:47 | `login_success`, `user_id=05ae7410-...` |
| Upload da foto | 00:54:24 | `image_answer_created`, `answer_id=f194ff5b-668d-4cbb-b7c4-cebfd73b1784`, `source=IMAGE` |
| Rascunho de transcrição salvo | 00:54:34 | `manual_transcription_draft_saved`, `transcription_version=1` |
| Confirmação definitiva | 00:54:48 | `manual_transcription_confirmed`, `transcription_version=2` |
| Solicitação explícita de análise (clique manual, 15s depois da confirmação) | 00:55:03 | `correction_requested`, `job_id=f0dfec66-d813-4791-8421-5fde7ad31eb3`, `attempt=1` |
| Análise concluída (IA real) | 00:55:16 | `correction_job_completed`, `engine_mode=real`, `overall_confidence=0.98` |
| Decisão humana final | 00:56:59 | `human_review_registered`, `decision=APPROVE`, `reviewer_id=05ae7410-...` |

## 4. Prova de inferência real (correlação completa)

Consultado diretamente no banco descartável, após a execução:

```
answers:          id=f194ff5b-668d-4cbb-b7c4-cebfd73b1784, source=IMAGE,
                   transcription_status=TRANSCRICAO_CONFIRMADA
correction_jobs:  id=f0dfec66-d813-4791-8421-5fde7ad31eb3,
                   answer_id=f194ff5b-668d-4cbb-b7c4-cebfd73b1784, attempt=1
ai_executions:    id=b8259a89-9a89-4313-b4d3-102eaeb5a562,
                   job_id=f0dfec66-d813-4791-8421-5fde7ad31eb3,
                   engine_mode=real, model=qwen2.5:7b-instruct-q4_K_M,
                   overall_confidence=0.9800,
                   review_recommendation=REVIEW_OPTIONAL
human_reviews:    id=fa3445df-61ba-4503-9406-3a9e8787fdc8,
                   job_id=f0dfec66-d813-4791-8421-5fde7ad31eb3,
                   decision=APPROVE, reviewer_id=05ae7410-d595-4996-af1d-dbc27b62963b
```

`answer_id` → `job_id` → `AIExecution` → `HumanReview` formam uma cadeia
única e consistente — não há ambiguidade possível entre registros.

## 4.1 Evidência direta e independente da chamada ao Ollama (correção/complemento, 2026-10-15)

> Adendo de precisão, sem alterar o resultado já relatado. A evidência
> abaixo é **independente** do log do AI Engine (é o log nativo do
> próprio servidor Ollama, `/opt/homebrew/var/log/ollama.log`, fora do
> controle da aplicação demonstrada) e corrige uma imprecisão de unidade
> no relatório inicial.

Localizada e correlacionada pela janela de horário exata da
demonstração (21:55:03 a 21:55:16, horário local `-03:00`, equivalente a
`00:55:03`–`00:55:16` UTC já citado na tabela da seção 3):

```
time=2026-10-14T21:55:03.850-03:00 level=INFO source=server.go:109
  msg="using llama-server for model"
  model=/Users/<usuario>/.ollama/models/blobs/sha256-2bada8a74506770...
time=2026-10-14T21:55:06.120-03:00 level=INFO source=llama_server.go:1362
  msg="llama-server started in 2.26 seconds"
[GIN] 2026/10/14 - 21:55:16 | 200 | 12.309791875s | 127.0.0.1 | POST "/api/generate"
```

- Confirma uma chamada HTTP real `POST /api/generate` ao servidor Ollama
  local, status `200`, **dentro da mesma janela de tempo** da análise
  reportada pelo AI Engine (`correction_requested` às 21:55:03,
  `correction_job_completed` às 21:55:16 — mesmos timestamps,±1s).
- O digest do modelo carregado
  (`sha256:2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f...`)
  corresponde exatamente ao `layer` do tipo `application/vnd.ollama.image.model`
  do manifest local de `qwen2.5:7b-instruct-q4_K_M` (confirmado por
  inspeção do manifest em `~/.ollama/models/manifests/...`), eliminando
  ambiguidade sobre qual modelo foi de fato carregado.
- Duração da chamada real reportada pelo próprio Ollama:
  **12.309791875 segundos** (`12.309791875s` no log nativo) — consistente
  com os **12.341 segundos** (não "12.341 ms"; ver correção de unidade
  abaixo) medidos pelo AI Engine para o ciclo completo da análise
  (pequena diferença esperada por overhead de carregamento do
  `llama-server`, serialização HTTP e processamento do AI Engine em
  torno da chamada).
- Esta é a **prova mais direta disponível** nesta rodada: evidência do
  próprio motor de inferência, independente da aplicação demonstrada.

**Prova principal** (não auxiliar): a chamada real e correlacionada ao
Ollama (seção 4.1 acima) junto com `AIExecution.engine_mode='real'` e
`AIExecution.model='qwen2.5:7b-instruct-q4_K_M'` persistidos no banco.
Log do AI Engine mostrando `configured_engine_mode: "real"` na entrada da
análise, sem nenhuma ocorrência de `SIMULATED_MODE` em todo o log da
sessão (grep confirmado: zero ocorrências), são evidências auxiliares
que corroboram, mas não substituem isoladamente, a prova da chamada
efetiva ao motor.

**Evidências auxiliares** (corroboram, não substituem a prova acima):
- Duração observada do ciclo completo da análise pelo AI Engine:
  **12.341 segundos** — CORREÇÃO DE UNIDADE (2026-10-15): o campo
  `duration_ms: 12341` registrado pelo AI Engine está em
  **milissegundos**; o relatório desta mesma demonstração, entregue
  antes desta reconferência, descreveu erroneamente o valor como
  "12.341 ms" (deveria ser 12341 ms = 12,341 s). Corrigido aqui; latência
  de inferência real, não os poucos milissegundos determinísticos do
  modo simulado.
- `overall_confidence=0.98` é a confiança própria da heurística de
  correção (campo interno do AI Engine, já existente antes desta
  demonstração) — **não é e não deve ser lida como medida de acurácia
  pedagógica**; esta demonstração não avalia qualidade pedagógica da
  correção sugerida, apenas o caminho técnico com inferência real.
- Pontuação sugerida não é o valor fixo de "metade do max_score" (regra
  determinística do modo simulado) — resultado da inferência real.

## 5. Invariantes confirmados (não apenas assumidos)

- **Origem permanece MANUAL**: `answers.source='IMAGE'` o tempo todo;
  nenhuma extração/OCR ocorreu; o texto confirmado foi 100% digitado
  pelo professor na UI.
- **Texto confirmado é o utilizado na análise**: `answer_length=243`
  registrado pelo AI Engine na entrada da análise corresponde ao
  comprimento do texto digitado e confirmado (confirmado por inspeção
  visual da tela de revisão antes de clicar em "Confirmar
  definitivamente" — o texto exibido era idêntico ao digitado).
- **Confirmar não inicia análise automaticamente**: gap real de
  **15 segundos** entre `manual_transcription_confirmed` (00:54:48) e
  `correction_requested` (00:55:03) — a análise só foi disparada pelo
  clique manual e deliberado em "Solicitar análise da IA", exatamente
  como a UI anuncia ("A análise usa exatamente o texto confirmado
  acima").
- **Revisão humana final permanece separada**: o job completou com
  status `SUGERIDA` (sugestão da IA, não decisão); só virou decisão
  humana após o clique explícito em "Aprovar como decisão humana"
  (`human_reviews.decision='APPROVE'`), evento distinto e posterior
  (00:56:59) ao da conclusão da análise (00:55:16).

## 6. Limitações desta demonstração

- Não é OCR: a transcrição foi inteiramente manual; o conteúdo da
  imagem é irrelevante para o resultado.
- Não é avaliação formal da qualidade pedagógica da IA: não mede
  acerto/precisão da sugestão de nota; apenas comprova o caminho técnico
  ponta a ponta com inferência real.
- 1 única execução, 1 único caso de teste (não é benchmark
  estatisticamente significativo).
- Hardware local (Apple Silicon, Ollama local) — latência observada não
  é característica de produção/escala.

## 7. Encerramento e limpeza do ambiente

- Processos encerrados nesta rodada, nesta ordem: Vite (`:5190`), Core
  (`:8206`), AI Engine (`:8101`), Chrome (`--remote-debugging-port=9337`).
- `dropdb avalia_demo_ia_real_av_s08b` — banco descartável removido por
  completo.
- `rm -rf /tmp/avalia_demo_ia_real_av_s08b_storage
  /tmp/avalia_demo_ia_real_av_s08b_chrome` — storage e perfil de Chrome
  temporários removidos.
- Confirmado após a limpeza: `psql -l` não lista mais o banco
  descartável; `/tmp` não contém mais os diretórios temporários desta
  rodada; nenhum processo remanescente nas portas usadas (`pgrep`
  confirmado vazio).
- Ollama (serviço compartilhado) **não foi encerrado** — continua
  rodando normalmente para outras ferramentas do ambiente.
- Bancos protegidos auditados intactos antes e depois de toda a
  demonstração: `avalia_dev` (16 `human_reviews`, `a9f4c2e71b06`) e
  `avalia_apresentacao_demo_20261002` (`a9f4c2e71b06`) — nenhuma conexão
  foi aberta a esses bancos durante a demonstração.
- Storage real de produção (`core/var/answer_images`) confirmado intacto
  (1 arquivo pré-existente, nenhum novo).

## 8. Não alterado por esta demonstração

Numerador homologado permanece **22/70** (ver
`snapshot_RECONCILIACAO-2026-10-14-01_numerador-por-criterio.md`);
nenhum item de backlog passa de PARCIAL a elegível por esta
demonstração — ela não entrega nenhum item novo do backlog canônico,
apenas comprova tecnicamente que um caminho já entregue também funciona
com inferência real. Nenhuma migração operacional, P5, OCR, deploy ou
promoção de baseline ocorreu.
