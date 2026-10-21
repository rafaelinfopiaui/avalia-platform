# Roteiro de aceite — Fluxo funcional do professor (sem OCR automático / CSV / módulo acadêmico)

> **HOMOLOGADO (restrito) em 2026-10-21 — `DEC-AV-045`.** Roteiro de aceite (`BL-AV-8-06`) do marco
> definido por Rafael em 2026-10-17: aceite do **fluxo funcional já entregue**, em **ambiente local
> isolado com dados fictícios**, SEM OCR automático, SEM importação CSV, SEM módulo acadêmico ativo.
> A execução end-to-end do §4 foi concretizada no ensaio do registro `c0091673` e homologada por
> Rafael no escopo demonstrado — ver
> [`ensaio_c0091673_2026-10-21.md`](ensaio_c0091673_2026-10-21.md) e
> [`DEC-AV-045`](../../registers/decisions.md).
>
> **Natureza deste documento vs. do ensaio:** este roteiro é **preparação documental** (não executa
> código nem inferência). O ensaio que ele referencia, por outro lado, incluiu **inferência real** do
> AI Engine (ver §4 do ensaio). Não confundir a redação do roteiro com a execução histórica que ela
> descreve.
>
> Este aceite **não encerra o projeto** nem substitui a entrega futura com OCR; não altera o
> numerador (22/70) nem promove baseline; não toca bancos protegidos.

Data do roteiro: 2026-10-17 (-03). Homologação restrita: 2026-10-21 (-03).

---

## 0. Escopo registrado como decisão (DEC-AV-045 — HOMOLOGADA restrita 2026-10-21)

- **Marco de aceite:** fluxo funcional do professor pelo caminho por IMAGEM com **transcrição
  MANUAL explicitamente identificada** → **confirmação humana** → **solicitação explícita de
  análise** → **revisão humana**. Sem OCR automático, CSV ou módulo acadêmico ativo.
- **Base de autorização:** autorização desta conversa (2026-10-17); homologação restrita concedida
  em 2026-10-21 após a execução end-to-end do §4 no ensaio `c0091673`. O rótulo "Entrega A" não está
  nomeado nos documentos canônicos; isto **não invalida** a autorização. Formaliza-se o escopo SEM
  inventar homologação passada: é o marco corrente, não um aceite retroativo.
- **Estado:** HOMOLOGADA no escopo restrito demonstrado (resposta por imagem, transcrição manual
  confirmada, solicitação explícita de análise local real, resultado persistido, revisão humana
  APPROVE 6,00). Evidência versionável: [`ensaio_c0091673_2026-10-21.md`](ensaio_c0091673_2026-10-21.md).
- **Não encerra:** `AV-S05B` (permanece PARCIAL), a frente OCR (entrega futura), nem o projeto.
- **Não altera o numerador** (segue **22/70**) nem promove baseline.

## 1. Ambiente deste aceite (NÃO resolve DEC-AV-006 em geral)

- **Ambiente:** **local isolado, dados fictícios** — mesma PREMISSA aprovada para `AV-S03`
  (`DEC-AV-006`: "pendente em caráter geral; premissa aprovada somente para AV-S03" —
  `registers/decisions.md:18`). Banco descartável/isolado; **nunca** `avalia_dev` nem o banco de
  apresentação. (O ensaio de 2026-10-21 usou o banco fictício isolado `avalia_demo_movel_20261016`.)
- **Alcance de `DEC-AV-006` conferido:** **NÃO é declarada integralmente resolvida.** A decisão de
  ambiente da trilha completa (`BL-AV-8-05`/`BL-AV-8-06` em produção/piloto) permanece **pendente**.
  Este aceite usa só a premissa local/fictícia. **NÃO autorizado:** piloto com dados reais, deploy,
  uso operacional.

## 2. Lacunas — CORRIGIDO

- **DEBT-AV-014 (retomada de respostas por imagem após reload/nova sessão): RESOLVIDO, HOMOLOGADO E
  INTEGRADO** — `DEC-AV-039`, PR #17 mergeado em `main` (SHA `e8b08646cfee5e9fea70d8e9bbcb4cf39f5a3d2d`).
  Endpoint leitura `GET /v1/assessments/{id}/image-answers` + retomada na tela. **Removido da lista
  de lacunas**; evidência reutilizada (`evidence/AV-S06B/verificacao_debt_014_hermes.md`,
  `revisao_debt_014_antigravity.md`). **Só reabrir diante de regressão concreta.**
- Lacunas concretas remanescentes (ver §4): (a) decisão de ambiente geral `DEC-AV-006` (fora deste
  aceite, só premissa local aqui); (b) governança de retenção/remoção física `BL-AV-4B-05` +
  `DEC-AV-013` — **só relevante se o aceite previr dado real; NÃO previsto aqui** (fictício); (c)
  execução final observável dos passos do roteiro (§4) — **concretizada em 2026-10-21** no ensaio
  `c0091673`.

---

## 3. Critérios observáveis com EVIDÊNCIA JÁ EXISTENTE (reaproveitada; não repetir)

| # | Critério observável | Evidência existente (reaproveitar) | Estado |
|---|---|---|---|
| C1 | Captura por **câmera** e por **galeria** em ações separadas (mobile) | PR #23 (`DEC` captura móvel); testes humanos iPhone+Android | homologado/integrado |
| C2 | **Remoção da seleção** antes do envio (sem apagar backend) | PR #23; evidência `AV-S06B/evidencia_captura_movel...md` | homologado/integrado |
| C3 | Resposta por imagem nasce "aguardando transcrição" (sem texto fictício); **correção bloqueada** até confirmar | `DEC-AV-037/038`, PR #16; suíte 158 passed; 422 `ANSWER_NOT_TRANSCRIBED` | homologado/integrado |
| C4 | **Persistência / retomada** após reload e nova sessão (respeitando propriedade) | `DEC-AV-039`, PR #17; 171 passed; 403 p/ não-dono | homologado/integrado |
| C5 | **Transcrição MANUAL** explicitamente identificada + **confirmação humana** definitiva; concorrência por `transcription_version`; confirmar ≠ disparar correção | produto DP-1/2/3 `DEC-AV-040`; **homologação/integração da fatia MANUAL `DEC-AV-041` (PR #18, HEAD `ea512099`)**; `sprint_AV-S08B_transcricao_manual_confirmacao_humana.md` | homologado/integrado (parte manual) |
| C6 | **Solicitação explícita** de análise (ação HTTP deliberada, nunca automática) | botão "Solicitar análise da IA" reusa `requestCorrection`/`request_correction` (zero endpoint novo), `DEC-AV-041`; DP-3 `DEC-AV-040` | homologado/integrado |
| C7 | **Revisão humana** do resultado | fluxo `HumanReview` (fatia MANUAL `DEC-AV-041`/AV-S08B; demo ponta a ponta AV-S03B) | homologado/integrado |
| C8 | Módulo acadêmico **desligável/coerente** (menu e rota guardados) | AV-S03B, `DEC-AV-032`; `DEBT-AV-012/013` resolvidos — solução técnica **homologada e integrada** pelo PR #14 (`DEC-AV-034`, 2026-10-14) | homologado/integrado (ativação operacional não é objeto deste aceite) |

> Reaproveitamento explícito: câmera, galeria, remoção da seleção, persistência/retomada,
> transcrição manual e revisão **não serão repetidos** — a evidência acima é válida. Nova execução
> só para o que o §4 exige observar end-to-end em conjunto.

## 4. Passos do fluxo — cronologia efetiva (evidência anterior reaproveitada + ensaio final em 2026-10-21)

Fluxo completo observado em conjunto no registro `c0091673`, detalhado em
[`ensaio_c0091673_2026-10-21.md`](ensaio_c0091673_2026-10-21.md). A cronologia abaixo distingue o que
é **anterior a 21/10** (com datas conforme os registros existentes) do que ocorreu **em 21/10**, e o
que é **evidência anterior reaproveitada** (não reexecutada):

**Anterior a 21/10 (registros do próprio `c0091673`, fuso -03):**
1. Preparação do ambiente local isolado (banco fictício, serviços dedicados, módulo acadêmico
   desligado, sem OCR/CSV). Identidade dos serviços registrada no ensaio.
2. Upload da resposta por **foto** → estado "aguardando transcrição". `answers.created_at` do
   `c0091673` = 2026-10-20 20:03:46 UTC (17:03:46 -03).
3. **Transcrição manual** e **confirmação humana** (definitiva). `transcription_confirmed_at` =
   2026-10-20 20:06:13 UTC (17:06:13 -03), por usuário humano (`transcription_confirmed_by_id`
   preenchido). Confirmar transcrição não dispara correção.

**Em 21/10 (ensaio desta rodada):**
4. **Retomada** do registro já confirmado (reabertura do `c0091673` persistido na sessão do ensaio).
5. **Solicitação explícita** da primeira análise (ação HTTP deliberada) → `CorrectionJob` attempt 1
   (`732edfe0`), criado em 2026-10-21 16:53:59 UTC (13:53:59 -03).
6. **Execução real** da análise, correlacionada ao servidor Ollama (ver §4 do ensaio); total sugerido
   6,00; `AIExecution` real em 2026-10-21 16:54:12 UTC (13:54:12 -03).
7. **Revisão humana** do resultado → `HumanReview` **APPROVE** 6,00, com autoria autenticada e
   `AuditEvent`, em 2026-10-21 16:54:30 UTC (13:54:30 -03).

**Evidência anterior reaproveitada (NÃO reexecutada em 21/10):**
- Captura por **câmera** e **galeria**, **remoção da seleção** antes do envio e **retomada após
  reload/nova sessão** (C1/C2/C4) foram validadas nas entregas anteriores homologadas/integradas
  (ver §3) e **não foram repetidas** neste ensaio. A observação de 21/10 cobriu a retomada do
  registro confirmado, a solicitação, a execução real e a revisão humana (itens 4–7 acima).

**Limitação de cronologia registrada:** os horários dos itens 2 e 3 vêm dos campos `created_at` e
`transcription_confirmed_at` do `c0091673`; o item 1 (preparação do ambiente) não tem carimbo de
tempo persistido próprio — é descrito a partir da identidade dos serviços registrada no ensaio, não
de um timestamp comprovado.

Conferência de invariantes no ensaio: nenhuma correção disparada sem confirmação; nenhuma automação
de OCR; nada em banco protegido; dados fictícios.

## 5. Responsabilidades humanas

- **Rafael:** executa os passos observáveis nos aparelhos/navegador; confirma transcrição; solicita
  análise; faz a revisão humana; decide aceite.
- **Hermes:** prepara ambiente isolado, roteiro e coleta de evidência sanitizada; NÃO decide aceite.
- **Revisão independente (Antigravity):** quando aplicável, sobre o delta/roteiro — sem fotos/refs.
- Revisão humana cronometrada (métrica de esforço) **não** é objeto deste aceite (ver §7).

## 6. Condições de falha e encerramento

- **Aceite concedido:** fundamenta-se na **combinação** das evidências anteriores já homologadas e
  integradas (C1–C8 do §3) com o **ensaio final** observado end-to-end no `c0091673` (§4). NÃO se
  afirma que C1–C8 foram todos reobservados numa única execução em 21/10: o ensaio cobriu a retomada
  do registro confirmado, a solicitação, a execução real e a revisão humana; câmera/galeria/remoção/
  reload permanecem sustentados pela evidência anterior reaproveitada. Concedido no escopo restrito em
  2026-10-21 — `DEC-AV-045`.
- **Falha/bloqueio:** qualquer passo que dispare correção sem confirmação, perca dado persistido,
  exija OCR para completar, ou toque banco protegido → **parar e registrar**; aceite NÃO concedido;
  tratar como regressão/pendência concreta (reabrir o item correspondente, ex.: DEBT-AV-014 só se
  houver regressão real de retomada).
- **Encerramento:** aceite é do **fluxo funcional sem OCR**; não encerra `AV-S05B`, a frente OCR nem
  o projeto.

## 7. Delimitação entre análise REAL e SIMULADA

- A "solicitação de análise" (C6) e a correção por IA: este aceite cobre o **fluxo do professor**
  (disparo manual, bloqueio até confirmar, revisão humana). **Distinguir sempre:**
  - **análise real** = AI Engine real executando inferência; **análise simulada** = modo simulado.
  - O roteiro deve **rotular explicitamente** qual modo foi usado em cada execução; um não substitui
    o outro, e sucesso em modo simulado **não** comprova inferência real (lição `DEBT-AV-009`/AV-S01).
  - No ensaio de 2026-10-21 a análise foi **real**, correlacionada ao servidor Ollama (ver §4 do
    ensaio), com a limitação de digest truncado registrada para a consistência do texto enviado.
- **OCR permanece fora**: a transcrição é MANUAL; não há extração automática neste marco.

## 8. Preservações obrigatórias (invariantes)

- **AC-05**: cobertura dos dois subtipos ≠ resultado eliminatório por candidato ≠ revisão humana
  cronometrada — **mantidos separados**; nada disso é alterado por este aceite.
- `AV-S05B` **PARCIAL** (não encerrada); resultado eliminatório por candidato preservado; **revisão
  humana cronometrada pendente** pelo critério próprio (`DEC-AV-017` item 6).
- **Numerador 22/70 inalterado**.
- Sem OCR, CSV, módulo acadêmico ativo, dados reais, piloto, deploy, baseline ou bancos protegidos.
