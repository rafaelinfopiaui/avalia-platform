---
id: "proposta_demo_fluxo_integrado_ia_real_av-s08b"
tema: "Demonstração do fluxo completo com IA local REAL: foto → transcrição manual → confirmação → análise IA real → revisão"
gerado_em: "2026-10-14T16:40:00-03:00"
status: "EXECUTADA (2026-10-14/15) — ver resultado real em snapshot_EXEC-2026-10-14-12_demonstracao_ia_real_av-s08b.md"
---

# Proposta de demonstração — fluxo integrado com IA local REAL (banco isolado)

> Esta demonstração NÃO é OCR (não há extração automática de imagem — a
> transcrição continua manual, como já entregue na AV-S08B) e NÃO é
> avaliação formal da qualidade pedagógica da IA (não mede acerto/precisão
> da correção sugerida; apenas comprova que o caminho ponta a ponta
> funciona com inferência real, em vez de simulada).
>
> **Execução concluída em 2026-10-14/15.** O plano abaixo é preservado
> como registro do planejamento original (autorizado por Rafael antes da
> execução); o resultado real, com evidências sanitizadas, está em
> `snapshot_EXEC-2026-10-14-12_demonstracao_ia_real_av-s08b.md`.

## 1. Objetivo

Comprovar, com evidência real e distinguível de simulação, o fluxo:
foto → transcrição MANUAL (rascunho + confirmação, já entregue) →
solicitação explícita de análise com **IA local REAL** (Ollama,
`qwen2.5:7b-instruct-q4_K_M`, já disponível localmente — confirmado por
`ollama list`, nenhum download necessário) → revisão humana final.

## 2. Banco e armazenamento isolados

- Novo banco PostgreSQL local descartável, nome dedicado (ex.:
  `avalia_demo_ia_real_av_s08b`), nunca `avalia_dev` nem
  `avalia_apresentacao_demo_20261002`.
- Storage de imagens em diretório temporário próprio (`AVALIA_IMAGE_STORAGE_DIR`
  apontando para um `tempfile.mkdtemp()` dedicado), nunca o storage usado
  por `avalia_dev`.
- Core apontando para esse banco via variável de ambiente isolada
  (`DATABASE_URL`), porta HTTP dedicada (ex. `:8205`, fora das usadas em
  rodadas anteriores).
- `ACADEMIC_MODULE_ENABLED=false` (não é objeto desta demonstração;
  evita dependência de estrutura acadêmica real).

## 3. Código integrado e migrações necessárias nesse banco

- Código: HEAD atual de `main` (`efaa337`, já integrado) — nenhuma
  alteração de código necessária; o fluxo completo (upload de imagem,
  rascunho/confirmação manual, solicitação de correção, `CorrectionJob`,
  `AIExecution`, `HumanReview`) já existe e está testado.
- Migrações: `alembic upgrade head` aplicado **somente** no banco novo e
  descartável `avalia_demo_ia_real_av_s08b` — nunca em `avalia_dev` ou
  apresentação. Isso não é "migração operacional" no sentido vedado
  (bancos protegidos); é setup padrão de um banco de teste efêmero, igual
  ao já usado em todas as rodadas de validação visual anteriores desta
  trilha.

## 4. Dados fictícios

- 1 organização/curso/disciplina/turma fictícia (reaproveitando o padrão
  de seed já usado nas validações visuais anteriores: nomes claramente
  fictícios, nenhum dado real de aluno).
- 1 avaliação com 1 questão publicada, 1 rubrica publicada.
- 1 professor de teste (mesmo padrão de autenticação já usado em todas as
  rodadas anteriores).
- 1 resposta por imagem (foto de texto manuscrito/impresso simples,
  gerada ou fictícia — não precisa ser uma foto real de aluno, já que
  OCR não está em escopo; o conteúdo da "foto" é irrelevante para o que
  está sendo demonstrado, pois a transcrição é manual).

## 5. Modelo local já disponível

- `qwen2.5:7b-instruct-q4_K_M` via Ollama — já presente localmente
  (`ollama list` confirma 4.7 GB, modificado há 5 semanas; nenhum
  download necessário).
- AI Engine configurado com `AI_ENGINE_MODE=real`, `OLLAMA_URL` apontando
  para a instância local já em execução (`http://localhost:11434`),
  porta HTTP dedicada da demo (ex. `:8101`).

## 6. Evidências que distinguirão inferência real de modo simulado

- `AIExecution.engine_mode` deve ser `'real'`, não `'simulated'`
  (`core/app/models.py:339`) — consultado diretamente no banco após a
  execução.
- `AIExecution.model` deve conter o nome real do modelo
  (`qwen2.5:7b-instruct-q4_K_M`), não string vazia (vazio é a assinatura
  do modo simulado, ver `ai-engine/tests/test_simulated_mode.py:12`).
- Log do AI Engine (nível INFO) deve mostrar uma chamada HTTP real ao
  Ollama (`ollama_client.generate`), com latência não-trivial (modo
  simulado responde em milissegundos de forma determinística; modo real
  tem latência de inferência real, tipicamente segundos).
- Nenhuma flag `SIMULATED_MODE` na resposta da API (presente apenas no
  modo simulado).
- Pontuação sugerida não determinística/fixa (modo simulado usa metade
  do `max_score` sempre — `test_simulated_mode.py:13`); no modo real a
  pontuação varia com o conteúdo real enviado.

## 7. Verificações realmente novas (vs. já válidas, reaproveitadas)

**Reaproveitado sem re-execução** (já comprovado em rodadas anteriores,
não será repetido):
- suíte automatizada completa (204 passed, 5 skipped) — já validada;
- identidade de conteúdo integral do texto confirmado enviado à IA
  (teste automatizado já existente e já executado);
- fluxo de transcrição manual em si (rascunho, confirmação, bloqueio de
  correção antes da confirmação) — já validado em navegador real;
- autorização e controle de acesso — já validados.

**Novo nesta demonstração** (ainda não comprovado em nenhuma rodada
anterior desta trilha):
- execução ponta a ponta com **AI Engine real** (não simulado) a partir
  de uma resposta cuja origem é IMAGEM com transcrição MANUAL confirmada
  — todas as rodadas anteriores desta trilha usaram AI Engine simulado
  para esse caminho específico (ver `DEC-AV-037`/snapshots EXEC-08/09:
  "AI Engine real em modo simulado explícito, distinto de inferência
  real");
  `engine_mode='real'` e `model` não-vazio persistidos corretamente no
  banco para esse caminho específico;
- latência e variação de pontuação compatíveis com inferência real (não
  apenas ausência de erro).

## 8. Encerramento dos serviços e destino dos artefatos de teste

- Ao final: encerrar Core (processo HTTP), AI Engine (processo HTTP) e
  qualquer processo de navegador/CDP usado para disparar a ação pela UI.
- `DROP DATABASE avalia_demo_ia_real_av_s08b;` — banco descartado por
  completo, nenhum dado retido.
- Diretório de storage temporário removido (`shutil.rmtree` do
  `tempfile.mkdtemp()` usado).
- Nenhuma alteração em `avalia_dev` ou
  `avalia_apresentacao_demo_20261002` — nenhuma conexão será aberta a
  esses bancos durante toda a demonstração.
- Resultado (log de evidência: valores de `engine_mode`, `model`,
  latência, pontuação, trecho do log HTTP) registrado em um snapshot
  dedicado da governança, não em `local-nao-versionado/` (é evidência
  permanente, não scratch).
- Ollama em si não é encerrado (é um daemon do sistema já em execução,
  compartilhado por outras ferramentas do ambiente do usuário) — apenas
  as requisições feitas durante a demo cessam ao parar o AI Engine.

## 9. O que esta demonstração NÃO prova nem reivindica

- Não prova qualidade pedagógica da correção sugerida pela IA (não é
  benchmark, não é `BL-AV-7-*`).
- Não implementa OCR nem altera `BL-AV-4B-07`/`08`/`10`/`11`/`13`/`15`
  (continuam PARCIAIS exatamente como estão).
- Não altera o numerador (22/70) nem promove baseline.
- Não é validação de produção — ambiente inteiramente descartável.

## 10. Autorização necessária antes de executar

Esta é uma proposta de planejamento. Para executar, preciso de
autorização explícita para: criar o banco descartável, iniciar Core/AI
Engine/navegador localmente, e consumir ciclos de GPU/CPU para a
inferência real (pode levar de alguns segundos a poucos minutos por
chamada, dependendo do hardware). Nenhuma dessas ações foi realizada
nesta rodada.
