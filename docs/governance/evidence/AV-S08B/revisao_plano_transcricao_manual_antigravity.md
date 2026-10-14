# Parecer de Revisão Crítica Independente de Desenho/Plano — Transcrição Manual e Confirmação Humana (AV-S08B)

- **Data:** 2026-10-14T09:35:00-03:00
- **Revisor independente:** Antigravity (Gemini 3.8 Flash High)
- **Documento revisado:** [`docs/governance/evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md)
- **Documentos e código de referência auditados:**
  - Modelo de dados: [`core/app/models.py`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/models.py) (classes `Answer`, `AnswerImage`, `CorrectionJob`, `AIExecution`, `HumanReview`, `AuditEvent`)
  - Endpoints e autorização: [`core/app/main.py`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py) (`create_answer`, `create_image_answer`, `list_image_answers`, `request_correction`, `review_correction`, `_get_owned_assessment`, `error_response`)
  - Regras acadêmicas: [`core/app/routers/academic.py`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/routers/academic.py) (`require_assessment_mutation`, `require_active_class_link`)
  - Schemas Pydantic: [`core/app/schemas.py`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py) (`AnswerOut`, `AnswerWithImagesOut`)
  - Frontend: [`frontend/src/types.ts`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/types.ts), [`frontend/src/pages/ImageAnswerPage.tsx`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ImageAnswerPage.tsx)
  - Backlog canônico: [`docs/governance/backlog/backlog_tecnico_avalia.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/backlog/backlog_tecnico_avalia.md) (Etapa 4B, subseções B, C, D, E)
- **Escopo desta revisão:** EXCLUSIVAMENTE a avaliação técnica crítica do plano pré-implementação da fatia AV-S08B. Não há código a executar nesta fase, não há migração de banco de dados e não há operações de Git (`stage`, `commit`, `push`, `branch`, `worktree`).

---

## 1. Veredito da Revisão

**APROVADO COM RESSALVAS**

O plano técnico proposto para a fatia AV-S08B possui fundamentação conceitual sólida e respeita integralmente as diretrizes de governança estabelecidas por Rafael:
1. Mantém a separação estrita entre confirmação de transcrição e solicitação de correção (nenhum disparo automático de IA);
2. Não inventa "OCR simulado" nem pré-preenchimentos artificiais sem base em motor real;
3. Preserva com precisão a distinção entre decisões puramente técnicas e decisões de produto (DP-1, DP-2, DP-3), mantendo estas últimas pendentes da decisão explícita de Rafael;
4. Garante total compatibilidade com o fluxo textual pré-existente e com a fatia DEBT-AV-014 recém-integrada (merge commit `e8b08646cfee5e9fea70d8e9bbcb4cf39f5a3d2d`).

O veredito é **"Aprovado com Ressalvas"** devido à detecção de **uma lacuna arquitetural crítica (leitura/retomada de rascunhos)** e quatro inconsistências pontuais de contrato/nomenclatura que precisam ser corrigidas antes de qualquer autorização de implementação.

---

## 2. Avaliação dos 7 Pontos Solicitados

### 2.1. Contrato e Padrões de Autorização e Erro (Item 1)
- **Status:** **COERENTE COM AJUSTES**
- **Análise frente ao código real:**
  - **Autorização de mutação:** O plano (§3.2, linhas 110-123) exige acertadamente que a gravação de rascunho e a confirmação sejam tratadas como mutações (`_get_owned_assessment` seguido de `require_assessment_mutation`). Isso coincide precisamente com o padrão dos endpoints de mutação em [`core/app/main.py:601-602`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L601-L602) (`create_answer`), [`core/app/main.py:638-639`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L638-L639) (`create_image_answer`) e [`core/app/main.py:806-807`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L806-L807) (`request_correction`), exigindo que o professor seja dono da avaliação e tenha vínculo ativo na turma quando houver `class_group_id` ([`core/app/routers/academic.py:165-172`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/routers/academic.py#L165-L172)). Diferencia-se corretamente da leitura histórica de DEBT-AV-014 ([`core/app/main.py:717`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L717)), que usa apenas `_get_owned_assessment`.
  - **Códigos HTTP de Erro e Envelope:** O mapeamento para 401 (não autenticado), 403 (não-dono ou sem vínculo), 404 (resposta/questão inexistente) e 422 (`ANSWER_TEXT_REQUIRED`, `ANSWER_NOT_IMAGE_SOURCE`) respeita a convenção de `error_response(...)` de [`core/app/main.py:114-124`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L114-L124).
  - **Tratamento de conflito 409 vs 422 (Ponto de Atenção):**
    - Em `confirm` (§3.3, linha 144-147 e §6, linhas 191-195), a confirmação repetida com texto diferente retorna HTTP 409 com o código `TRANSCRIPTION_ALREADY_CONFIRMED` e o estado atual no payload, espelhando com exatidão o padrão de `_review_conflict_response` em [`core/app/main.py:905-914`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L905-L914) (`REVIEW_ALREADY_EXISTS`).
    - No entanto, em `draft` (§3.3, linha 136), tentar salvar rascunho em resposta já confirmada está tipado como HTTP 422 com o mesmo código `TRANSCRIPTION_ALREADY_CONFIRMED`. semanticamente, tentar mutar rascunho de um recurso cujo ciclo de vida já foi finalizado é um conflito de estado de recurso (HTTP 409 Conflict), e não uma falha de validação de payload (HTTP 422). Recomenda-se uniformizar para HTTP 409 `TRANSCRIPTION_ALREADY_CONFIRMED` em ambos.
  - **Omissão de schema de retorno:** O plano não define qual `response_model` os dois novos endpoints retornam (se `AnswerOut`, `AnswerWithImagesOut` ou um DTO específico de transcrição). Isso precisa ser explicitado para evitar indefinição contratual com o frontend.

---

### 2.2. Modelagem de Dados e Infraestrutura de Auditoria (Item 2)
- **Status:** **RESSALVA CRÍTICA (LACUNA DE LEITURA DO RASCUNHO)**
- **Análise frente ao código real:**
  - **Reuso de `AuditEvent` vs. Tabela Nova:** A decisão técnica de reutilizar a tabela `audit_events` ([`core/app/models.py:370-380`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/models.py#L370-L380)) para guardar o histórico de edições/versões de rascunho e confirmação é **altamente recomendável e razoável**. O AvalIA já utiliza `AuditEvent` para registrar o histórico de `Assessment`, `Question`, `Rubric`, `HumanReview` e transições de `CorrectionJob` ([`core/app/main.py:196, 329, 380, 499, 985`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L196)). Criar uma tabela de versionamento dedicada para rascunhos manuais nesta fatia violaria o princípio de menor mudança coerente.
  - **A LACUNA CRÍTICA DO PLANO (Draft Retrieval Gap):**
    - O plano (§3.1, linha 83) adiciona `manual_transcription_draft: Mapped[str | None]` na tabela `answers`.
    - No entanto, no §4 (linhas 165-168), o plano afirma textualmente:
      > *"Não aparece em nenhuma leitura histórica fora do próprio professor dono editando (não é exposto via GET /v1/assessments/{id}/image-answers, que já existe e não precisa mudar — ele mostra apenas o estado confirmado/pendente, não rascunhos em edição)."*
    - **Contradição incontornável:** O plano propõe apenas DOIS endpoints: `PATCH .../draft` e `POST .../confirm`. **Não há nenhum endpoint `GET` proposto para rascunho!** E como o plano diz que `GET /assessments/{id}/image-answers` "não precisa mudar e não expõe rascunhos", **COMO O FRONTEND CARREGARÁ O RASCUNHO SALVO QUANDO O PROFESSOR VOLTAR À TELA OU DER F5?**
    - Se a API salva rascunho mas não fornece nenhum caminho de leitura (nem via listagem nem via endpoint dedicado), o rascunho torna-se um "buraco negro" de gravação sem leitura. Isso inviabilizaria o critério ACD-13 e a experiência de uso.
    - **Correção mandatória:** O plano deve explicitar que `AnswerOut` ([`core/app/schemas.py:152-164`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py#L152-L164)) e, por extensão, `AnswerWithImagesOut` ([`core/app/schemas.py:181-183`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py#L181-L183)) passarão a incluir o campo opcional `manual_transcription_draft: Optional[str] = None` (ou criar uma rota `GET /v1/answers/{id}/manual-transcription`). A inclusão em `AnswerOut` é muito mais limpa e consistente com a arquitetura existente.
  - **Nomenclatura das colunas de confirmação:**
    - O plano propõe `manual_transcription_confirmed_by_id` e `manual_transcription_confirmed_at`.
    - Nota-se que o status geral é `transcription_status` (sem prefixo `manual_`). A confirmação é **sempre humana** (realizada por um professor autenticado), quer o texto tenha vindo de digitação manual ou venha futuramente de OCR (`BL-AV-4B-11`).
    - Nomear as colunas como `transcription_confirmed_by_id` e `transcription_confirmed_at` (sem o prefixo `manual_`) tornará o modelo universal e evitará retrabalho ou migrações duplicadas quando o OCR for introduzido.
  - **Inconsistência de convenção em `AuditEvent`:**
    - No plano (§3.1, linha 103), consta `resource_type="answer"` (minúsculo).
    - No código real, todas as chamadas a `AuditEvent` usam PascalCase (`resource_type="Assessment"`, `resource_type="Question"`, `resource_type="Rubric"`, `resource_type="CorrectionJob"` — ver [`core/app/main.py:196, 380, 499, 988`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L196)).
    - Deve-se adotar obrigatoriamente `resource_type="Answer"` para preservar a integridade das consultas de auditoria.

---

### 2.3. Desacoplamento Estrito entre Confirmação e Correção (Item 3)
- **Status:** **PERFEITAMENTE GARANTIDO**
- **Análise frente ao código real:**
  - O documento dedica as seções §3.3 (linhas 152-153) e §9 (linhas 249-262), além do critério ACD-08, para blindar o sistema contra acoplamentos indevidos.
  - A confirmação manual limita-se estritamente a preencher `Answer.text`, atribuir `transcription_status = TranscriptionStatus.TRANSCRICAO_CONFIRMADA`, preencher metadados de auditoria e persistir a transação.
  - Nenhuma rotina de confirmação instancia `CorrectionJob` ([`core/app/models.py:309`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/models.py#L309)), nenhuma rotina enfileira `run_correction_job` em `BackgroundTasks`, e nenhuma rotina chama interna ou indiretamente `request_correction` ([`core/app/main.py:791-842`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L791-L842)).
  - A solicitação de correção permanece como ação HTTP separada e deliberada (`POST /v1/answers/{id}/corrections`). O guard já existente em `request_correction` ([`core/app/main.py:810-819`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L810-L819)), que bloqueia com HTTP 422 `ANSWER_NOT_TRANSCRIBED`, simplesmente deixará de bloquear de maneira natural, pois a pré-condição legítima foi satisfeita.
  - O isolamento é total e atende rigorosamente à diretriz de Rafael.

---

### 2.4. Classificação das Decisões de Produto Pendentes (DP-1, DP-2, DP-3) (Item 4)
- **Status:** **CORRETAMENTE CLASSIFICADAS E ISOLADAS**
- **Análise:**
  - O plano (§2.2, linhas 53-68) demonstra disciplina exemplar de governança:
    - **DP-1 (Múltiplos rascunhos vs. rascunho único mais recente):** Classificada corretamente como produto. Trata de política de retenção, complexidade de interface e volume de dados. O plano assume temporariamente a opção mais simples (sobrescrever rascunho na coluna + log no `AuditEvent`), sem fechar as portas para decisão posterior.
    - **DP-2 (Reabertura pós-confirmação vs. confirmação definitiva):** Classificada corretamente como produto. Afeta o ciclo pedagógico da avaliação: permitir ou proibir retificação de transcrição após a prova já ter sido homologada ou corrigida. O plano projeta a arquitetura para ambos os desfechos (§8, linhas 220-248), mantendo a confirmação definitiva como default seguro até que Rafael decida.
    - **DP-3 (Impacto da reconfirmação sobre correções existentes):** Classificada corretamente como produto. Define se a reconfirmação exige novo disparo manual de correção com incremento de `attempt` (assumido tecnicamente como o caminho limpo) ou se haveria ações automáticas de invalidação de notas.
  - Nenhuma das três decisões foi tomada de forma unilateral. O documento declara explicitamente na linha 67: *"Essas três ficam para clarify/decisão explícita de Rafael antes de qualquer implementação — não decidido nesta proposta."*

---

### 2.5. Suficiência e Testabilidade dos Critérios de Aceite (ACD-01..13) (Item 5)
- **Status:** **SUFICIENTES COM CENÁRIOS COMPLEMENTARES NECESSÁRIOS**
- **Análise:**
  - Os critérios ACD-01 a ACD-13 cobrem o núcleo funcional, autorização por papel/vínculo, idempotência, ausência de disparo acidental de correção e integridade de auditoria.
  - **Cenários faltantes e correções necessárias identificadas:**
    1. **Critério explícito de leitura/recuperação do rascunho:**
       - Falta um critério equivalente a: *"ACD-01B: Consultar respostas por imagem (GET /assessments/{id}/image-answers) retorna o campo `manual_transcription_draft` quando existente, permitindo recuperação fiel do texto em nova sessão ou após reload (F5)."* Sem isso, a retomada do rascunho não possui garantia de teste automatizado.
    2. **Validação de rejeição de `confirm` para respostas `source=TEXT`:**
       - ACD-02 testa rejeição de rascunho em resposta textual (`422 ANSWER_NOT_IMAGE_SOURCE`). Falta explicitar que o endpoint de confirmação (`POST .../confirm`) também deve rejeitar respostas `source=TEXT` com `422 ANSWER_NOT_IMAGE_SOURCE` (ou 409).
    3. **Tratamento de rascunho vazio:**
       - ACD-04 valida que `confirm` com texto vazio/espaços retorna `422 ANSWER_TEXT_REQUIRED`. Mas qual o comportamento de `draft` com texto vazio? Permitir salvar rascunho vazio (para limpar rascunho) ou rejeitar com 422? O comportamento precisa ser especificado e testado.
    4. **Cenário de recurso inexistente (HTTP 404):**
       - Deve constar teste explícito garantindo que enviar rascunho ou confirmação para `answer_id` inexistente retorne `404 Not Found` (mencionado no texto do contrato no §3.3, mas ausente da tabela de critérios de aceite).
    5. **Correção de Typo em ACD-07:**
       - Na linha 290, o código de erro consta como `422 TRANSCRIPTION_ALREADY_CONFIRMADO` (com 'O' no final). O padrão em todo o restante do plano (§3.3 linha 136, §6 linha 191) e no repositório é inglês em maiúsculas: `TRANSCRIPTION_ALREADY_CONFIRMED`. Deve ser corrigido para evitar divergência na suíte de testes.

---

### 2.6. Compatibilidade com Fluxo Textual e com DEBT-AV-014 (Item 6)
- **Status:** **TOTALMENTE COMPATÍVEL (REGRESSÃO ZERO)**
- **Análise frente ao código real:**
  - **Fluxo textual (`POST /v1/answers`):** Em [`core/app/main.py:608-618`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L608-L618), a criação de resposta textual popula `source=TEXT` e `transcription_status=TRANSCRICAO_CONFIRMADA`. As novas colunas (`manual_transcription_draft`, etc.) são estritamente `nullable=True` e permanecerão `None`. A `CheckConstraint` existente (`ck_answers_source_text`, [`core/app/models.py:273`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/models.py#L273)) não é afetada.
  - **Fatia DEBT-AV-014 (`GET /v1/assessments/{id}/image-answers`):** Em [`core/app/main.py:710-745`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L710-L745), a listagem consulta `Answer` e `AnswerImage`. Como `AnswerWithImagesOut` herda de `AnswerOut`, a adição de campos opcionais em `AnswerOut` é aditiva e não altera a estrutura dos 13 testes homologados em [`core/app/tests/test_image_answers_listing.py`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/tests/test_image_answers_listing.py).
  - Nenhuma alteração retroativa ou reabertura de migrações anteriores é necessária.

---

### 2.7. Alinhamento com o Backlog Técnico (BL-AV-4B) (Item 7)
- **Status:** **ALINHADO E RIGOROSAMENTE QUALIFICADO**
- **Conferência cruzada com [`docs/governance/backlog/backlog_tecnico_avalia.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/backlog/backlog_tecnico_avalia.md):**

| ID do Backlog | Descrição Real no Backlog | Qualificação no Plano | Verificação Crítica Independente |
|---|---|---|---|
| `BL-AV-4B-10` | *Tela de conferência exibindo imagem e texto extraído lado a lado* (backlog linha 371) | **Parcial** | **Exato.** Como não há motor de OCR, não há "texto extraído"; entrega-se a interface lado a lado para transcrição manual. O item canônico não pode ser dado como encerrado. |
| `BL-AV-4B-11` | *Edição e confirmação da transcrição pelo professor; preservação de texto bruto extraído, texto corrigido e histórico da confirmação* (backlog linha 372) | **Parcial** | **Exato.** "Texto bruto extraído" só existirá com OCR. A fatia cobre a edição, confirmação e histórico da digitação humana. Item permanece aberto para OCR posterior. |
| `BL-AV-4B-13` | *Transcrição manual quando a extração falhar* (backlog linha 374) | **Coberto integralmente** | **Correto com ressalva contextual.** A transcrição manual em si é entregue integralmente. Contudo, a transição específica "quando a extração falhar" só será exercitável quando houver motor de OCR falhando. A qualificação como entrega da via manual é coerente. |
| `BL-AV-4B-14` | *Vincular a resposta confirmada ao aluno, à avaliação e à questão correta; impedir que a correção assistida inicie antes da confirmação humana* (backlog linha 378) | **Coberto** | **Exato.** O guard pré-existente (`ANSWER_NOT_TRANSCRIBED`) e a nova transição para `TRANSCRICAO_CONFIRMADA` fecham completamente esse requisito. |
| `BL-AV-4B-15` | *Preservar a cadeia completa: imagem → execução OCR → transcrição confirmada → correção → revisão humana* (backlog linha 379) | **Parcial** | **Exato.** O elo "execução OCR" segue inexistente; todos os demais elos da cadeia são preservados e conectados. |
| `BL-AV-4B-16` | *Idempotência/deduplicação em reenvios e retentativas de imagem* (backlog linha 380) | **Não coberto** | **Exato.** Refere-se à fase de upload de imagem, fora do escopo desta fatia. |

A seção §1 do plano reflete honestidade técnica impecável ao proibir expressamente que itens mais amplos (`BL-AV-4B-10`, `BL-AV-4B-11`) sejam marcados levianamente como encerrados no backlog.

---

## 3. Quadro de Achados Técnicos Concretos

| Ref. | Seção / Linha do Plano | Arquivo:Linha do Código Real | Descrição do Achado | Gravidade | Ajuste Necessário |
|---|---|---|---|---|---|
| **ACH-01** | §4, lin. 165-168 e §3.3 | [`core/app/schemas.py:152-164`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py#L152-L164) e [`main.py:710`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L710) | **Lacuna de leitura do rascunho (Draft Retrieval Gap):** O plano afirma que `GET /image-answers` não expõe rascunhos e não cria nenhuma rota `GET` para lê-los. Salvar rascunho sem rota de consulta impede que o frontend recupere o rascunho após reload/F5. | **Crítica** | Expor `manual_transcription_draft: Optional[str] = None` em `AnswerOut` / `AnswerWithImagesOut` (ou definir `GET /v1/answers/{id}/manual-transcription`). |
| **ACH-02** | §3.1, lin. 84-89 | [`core/app/models.py:285-289`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/models.py#L285-L289) | **Prefixagem desnecessária em colunas de confirmação:** `manual_transcription_confirmed_by_id` e `manual_transcription_confirmed_at` prefixam com `manual_` uma ação de confirmação que é sempre humana, gerando dívida quando houver OCR (`BL-AV-4B-11`). | **Média** | Renomear para `transcription_confirmed_by_id` e `transcription_confirmed_at` na modelagem da tabela `answers`. |
| **ACH-03** | §3.1, lin. 103 | [`core/app/main.py:196, 380, 499, 988`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L196) | **Inconsistência de casing em AuditEvent:** O plano cita `resource_type="answer"` (minúsculo), enquanto todo o código usa PascalCase (`"Answer"`). | **Baixa** | Adotar estritamente `resource_type="Answer"`. |
| **ACH-04** | §3.3, lin. 136 vs. lin. 144 | [`core/app/main.py:905-914`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L905-L914) | **Divergência de status code para recurso já confirmado:** O rascunho retorna 422 para resposta já confirmada, enquanto a confirmação repetida conflitante retorna 409. Tentar editar rascunho de resposta já finalizada é um conflito de estado. | **Média** | Padronizar ambos para HTTP 409 `TRANSCRIPTION_ALREADY_CONFIRMED`. |
| **ACH-05** | §11, lin. 290 (ACD-07) | §3.3, lin. 136; §6, lin. 191 | **Typo no código de erro:** ACD-07 grafa `TRANSCRIPTION_ALREADY_CONFIRMADO` (em português), divergindo do padrão em inglês `TRANSCRIPTION_ALREADY_CONFIRMED`. | **Baixa** | Corrigir a grafia para `TRANSCRIPTION_ALREADY_CONFIRMED`. |
| **ACH-06** | §3.3 e §11 | [`core/app/schemas.py:152`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py#L152) | **Indefinição de schemas de resposta (`response_model`):** O contrato não especifica qual DTO JSON é retornado por `PATCH draft` e `POST confirm` em caso de sucesso (HTTP 200). | **Média** | Especificar formalmente os DTOs de retorno (ex.: `AnswerWithImagesOut` ou DTO dedicado). |
| **ACH-07** | §11 | [`core/app/main.py:603-607`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L603-L607) | **Lacunas nos critérios de aceite:** Faltam critérios para: (a) leitura/retomada de rascunho salvo; (b) rejeição de `confirm` em resposta TEXT; (c) resposta 404 para `answer_id` inexistente; (d) definição de aceite ou rejeição para rascunho de texto vazio. | **Média** | Adicionar os cenários correspondentes à suíte de critérios de aceite (ex.: ACD-01B, complemento ao ACD-02 e ACD-04). |

---

## 4. Recomendações Mandatórias Pré-Implementação

1. **Resolver a Leitura do Rascunho (ACH-01):**
   - Atualizar a especificação de `AnswerOut` e `AnswerWithImagesOut` para incluir `manual_transcription_draft: Optional[str] = None`. Garantir que `GET /v1/assessments/{id}/image-answers` popule esse campo. Dessa forma, ao carregar a tela de respostas por imagem, o frontend obtém automaticamente o rascunho pendente de cada resposta sem requisições adicionais.
2. **Harmonizar Nomes de Colunas de Auditoria e Confirmação (ACH-02 e ACH-03):**
   - Adotar `transcription_confirmed_by_id` e `transcription_confirmed_at` na migração Alembic.
   - Registrar eventos de auditoria com `resource_type="Answer"`.
3. **Formalizar os Schemas de Retorno e Resolução de Erros (ACH-04 e ACH-06):**
   - Definir se `POST /confirm` retorna `AnswerWithImagesOut` (consistente com `create_image_answer`) ou `AnswerOut`.
   - Utilizar HTTP 409 `TRANSCRIPTION_ALREADY_CONFIRMED` tanto para rascunho quanto para confirmação repetida divergente.
4. **Submeter Decisões de Produto a Rafael:**
   - Obter deliberação explícita de Rafael sobre DP-1, DP-2 e DP-3 antes de iniciar qualquer desenvolvimento.

---

## 5. Declaração de Não-Interferência Operacional

Em conformidade rigorosa com a governança do AvalIA e o papel de revisor independente delegado ao Antigravity:
- **Código:** Nenhum arquivo de código de produto foi criado, editado ou executado.
- **Banco de Dados:** Nenhuma operação DDL, DML, migração ou conexão foi realizada contra `avalia_dev` ou qualquer outro ambiente.
- **Git:** Nenhum comando `git add`, `git commit`, `git push`, `git checkout`, `git branch` ou criação de worktree foi executado. O plano original [`plano_transcricao_manual_confirmacao_humana.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md) foi mantido 100% intocado.
