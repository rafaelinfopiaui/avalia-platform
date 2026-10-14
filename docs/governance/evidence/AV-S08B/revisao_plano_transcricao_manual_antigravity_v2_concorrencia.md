# Parecer de Revisão Crítica Independente (v2 — Limitada) — Decisões de Produto DP-1/2/3 e Controle de Concorrência (AV-S08B)

- **Data:** 2026-10-14T09:55:00-03:00
- **Revisor independente:** Antigravity (Gemini 3.8 Flash High)
- **Documento revisado:** [`docs/governance/evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md)
- **Documentos e referências auditadas:**
  - Decisão formal de produto: [`docs/governance/registers/decisions.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/registers/decisions.md) (`DEC-AV-040`)
  - Parecer v1 anterior: [`docs/governance/evidence/AV-S08B/revisao_plano_transcricao_manual_antigravity.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/evidence/AV-S08B/revisao_plano_transcricao_manual_antigravity.md)
  - Padrão de versionamento e concorrência no modelo: [`core/app/models.py:246`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/models.py#L246) (`Rubric.version`), [`core/app/models.py:270-292`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/models.py#L270-L292) (`Answer`)
  - Endpoints de resposta e auditoria: [`core/app/main.py`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py)
- **Escopo desta revisão:** LIMITADO aos 5 pontos específicos decorrentes da aprovação de `DEC-AV-040` (DP-1, DP-2, DP-3 e requisito de controle de concorrência por versão). Os 7 achados da rodada v1 (ACH-01 a ACH-07) já foram incorporados e não foram reavaliados do zero.
- **Limites operacionais:** Nenhum código implementado, nenhuma migração executada, nenhum banco protegido tocado e nenhuma ação Git realizada.

---

## 1. Veredito da Revisão

**APROVADO COM RESSALVA PONTUAL (DOCUMENTAL)**

O plano técnico v2 incorpora com precisão técnica e maturidade arquitetural as diretrizes de `DEC-AV-040`:
1. O mecanismo de lock otimista por versão (`transcription_version` + `expected_version`) amparado em transação atômica de banco de dados é tecnicamente correto para eliminar race conditions tanto em rascunhos concorrentes quanto em confirmações concorrentes.
2. A decisão DP-2 (confirmação definitiva, sem reabertura) foi aplicada com consistência exemplar em todas as seções técnicas, contratos HTTP e critérios de aceite.
3. A decisão DP-1 (um rascunho atual em coluna simples + histórico append-only em `AuditEvent`) respeita o princípio de menor mudança coerente e elimina a necessidade de tabelas adicionais.
4. Os critérios ACD-15, ACD-16 e ACD-17 fornecem cobertura suficiente e são tecnicamente executáveis contra PostgreSQL real.
5. A nomenclatura `transcription_version` é consistente com a convenção do projeto e previne retrabalho com a futura chegada de OCR.

A única ressalva que motivou o status "Com Ressalva Pontual" é estritamente **documental (ACH-08)**: a existência de um resquício textual no cabeçalho introdutório do documento (linhas 15-17) que ainda classifica DP-1/DP-2/DP-3 como "pendentes de Rafael", apesar de terem sido formalmente aprovadas em `DEC-AV-040` e devidamente atualizadas no corpo do plano.

---

## 2. Avaliação dos 5 Pontos de Escopo

### 2.1. Mecanismo de Controle de Concorrência por Versão (Item 1)
- **Status:** **TECNICAMENTE CORRETO E SEGURO**
- **Análise frente aos cenários solicitados:**
  - **(a) Edições concorrentes de rascunho:** Se duas sessões/abas carregam a mesma versão $V$ da resposta e submetem `PATCH .../draft` concorrentemente com `expected_version = V`, a execução do `UPDATE ... WHERE id = :id AND transcription_version = :expected_version` na transação do PostgreSQL garante que a primeira conexão a obter o row-lock atômico avança a versão para $V+1$. A segunda conexão, ao inspecionar a linha sob isolamento MVCC (`READ COMMITTED`), detecta que `transcription_version` já não coincide com $V$. A transação afeta 0 linhas (`rowcount == 0`), abortando com rollback e retornando HTTP 409 `TRANSCRIPTION_VERSION_CONFLICT` com o estado vigente no corpo. Nenhuma sobrescrita silenciosa é possível.
  - **(b) Confirmações concorrentes com textos distintos:** Duas requisições `POST .../confirm` concorrentes com o mesmo `expected_version` competem pelo mesmo recurso. A transação vencedora define `text`, altera `transcription_status = TRANSCRICAO_CONFIRMADA`, avança a versão para $V+1$ e persiste exatamente um `AuditEvent`. A transação perdedora é interceptada pela divergência de versão (ou de status terminal) e rejeitada com HTTP 409 (`TRANSCRIPTION_VERSION_CONFLICT` ou `TRANSCRIPTION_ALREADY_CONFIRMED`). Em nenhuma hipótese haverá dois `AuditEvent` de confirmação ou coexistência de textos concorrentes.
  - **Garantia por transação de banco vs. lock em memória:** A escolha de apoiar o lock otimista na transação do PostgreSQL (e não em primitivas de memória como `threading.Lock` ou `asyncio.Lock`) é **a única arquiteturalmente correta**. Locks em memória operam apenas dentro do mesmo processo e seriam completamente ineficazes em ambientes com múltiplos workers Uvicorn/Gunicorn ou múltiplas réplicas de contêiner.

### 2.2. Consistência na Aplicação da Decisão DP-2 (Confirmação Definitiva) (Item 2)
- **Status:** **APLICADA DE FORMA CONSISTENTE, COM RESQUÍCIO DOCUMENTAL NO CABEÇALHO**
- **Verificação das seções do plano:**
  - **§2.2 (linhas 68-83):** Registra formalmente DP-2 como decidida, caracterizando `TRANSCRICAO_CONFIRMADA` como status terminal nesta fatia e unificando o retorno para 409 `TRANSCRIPTION_ALREADY_CONFIRMED`.
  - **§3.3 (linhas 230-232, 248-253):** Tanto `draft` quanto `confirm` pós-confirmação são bloqueados com HTTP 409 `TRANSCRIPTION_ALREADY_CONFIRMED`, sem condicionais.
  - **§4 (linhas 288-293):** Exige na UX o aviso explícito de confirmação definitiva e irrevogável nesta fatia.
  - **§6 (linhas 316-317):** Confirmação repetida divergente categorizada como definitivamente proibida (HTTP 409).
  - **§8 (linhas 360-388):** Simplificado para o ramo estritamente definitivo; jobs e reviews pré-existentes tornam-se inalcançáveis para mutação.
  - **ACD-07 e ACD-11 (linhas 436 e 440):** Critérios reescritos como regras fechadas e definitivas, sem condicionais.
  - **§13 (linha 466):** Reabertura e retificação listadas expressamente como limites fora de escopo.
- **Resquício detectado (ACH-08):**
  - No bloco de citação introdutório do documento ([`plano_transcricao_manual_confirmacao_humana.md:15-17`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md#L15-L17)), ainda consta:
    > *"As 3 decisões de produto (DP-1/DP-2/DP-3, §2.2) permanecem explicitamente pendentes de Rafael — a revisão confirmou que não foram decididas unilateralmente."*
  - Este trecho é uma sobra textual da v1 anterior à aprovação de `DEC-AV-040` e deve ser ajustado para registrar que as decisões foram homologadas por Rafael em 2026-10-14.

### 2.3. Coerência da Decisão DP-1 com Infraestrutura Existente (Item 3)
- **Status:** **TOTALMENTE COERENTE (MENOR MUDANÇA COERENTE)**
- **Análise:**
  - Armazenar o rascunho ativo diretamente em `Answer.manual_transcription_draft` permite leitura direta em $O(1)$ na rota já existente `GET /v1/assessments/{id}/image-answers` (via `AnswerWithImagesOut`), atendendo à recomendação ACH-01 sem sobrecarga de rede.
  - O reaproveitamento da tabela genérica `audit_events` ([`core/app/models.py:370-380`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/models.py#L370-L380)) com `resource_type="Answer"` para armazenar os deltas (`before_json`/`after_json`) a cada save segue à risca o padrão já adotado para `Assessment`, `Question` e `Rubric`.
  - Evita-se a criação de uma tabela desnecessária de versionamento de rascunhos, mantendo a base enxuta e alinhada à política de menor mudança coerente.

### 2.4. Suficiência e Testabilidade dos Novos Critérios de Aceite (ACD-15/16/17) (Item 4)
- **Status:** **SUFICIENTES E TESTÁVEIS CONTRA POSTGRESQL REAL**
- **Análise de testabilidade técnica:**
  - Ao contrário do SQLite (que frequentemente serializa ou trava operações via lock de arquivo no nível do SO), o PostgreSQL real suporta concorrência fina de transações independentes via MVCC.
  - Conforme comprovado na sprint AV-S04 (para race condition de exclusão de questão), a execução de testes com `ThreadPoolExecutor` ou conexões concorrentes reais via `pytest` é perfeitamente viável e determinística.
  - **ACD-15:** Cobre a rejeição de save concorrente de rascunho com versão desatualizada (409 `TRANSCRIPTION_VERSION_CONFLICT`).
  - **ACD-16:** Cobre o cenário crítico de confirmações concorrentes com textos distintos (exclusão mútua: 1 sucesso e 1 conflito 409, garantindo unicidade do evento de auditoria e do texto final).
  - **ACD-17:** Valida a monotonicidade estrita de `transcription_version` (sem retrocessos e sem saltos em falhas).
  - **Recomendação complementar:** Recomenda-se incluir nos testes a corrida mista (`confirm` concorrente com `draft`), assegurando que um `draft` tardio com versão desatualizada seja barrado e não reverta uma confirmação recém-comitada.

### 2.5. Nomenclatura da Nova Coluna `transcription_version` (Item 5)
- **Status:** **TOTALMENTE ALINHADA ÀS CONVENÇÕES DO PROJETO**
- **Análise:**
  - A coluna foi definida como `transcription_version` (sem o prefixo `manual_`).
  - Segue exatamente a mesma diretriz adotada em ACH-02 da revisão anterior para `transcription_confirmed_by_id` e `transcription_confirmed_at`, bem como o enum pré-existente `transcription_status`.
  - A versão é uma propriedade intrínseca da transcrição da resposta (seja ela gerada manualmente ou posteriormente pré-preenchida por OCR). Omitir o prefixo `manual_` evita duplicidade futura e preserva a extensibilidade do modelo.

---

## 3. Quadro de Achados Técnicos Desta Revisão Limitada

| Ref. | Seção / Linha do Plano | Arquivo:Linha do Código Real / Governança | Descrição do Achado | Gravidade | Ajuste Necessário |
|---|---|---|---|---|---|
| **ACH-08** | Bloco de citação inicial, lin. 15-17 | [`docs/governance/registers/decisions.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/registers/decisions.md) (`DEC-AV-040`) | **Resquício de pendência no cabeçalho:** O texto introdutório ainda afirma que "As 3 decisões de produto (DP-1/DP-2/DP-3, §2.2) permanecem explicitamente pendentes de Rafael", colidindo com a aprovação formal de `DEC-AV-040` e com o §2 do próprio plano. | **Baixa (Documental)** | Atualizar o aviso do cabeçalho registrando a aprovação das decisões em DEC-AV-040. |

---

## 4. Recomendações Técnicas para a Implementação

1. **Garantia de Atomicidade no SQLAlchemy (Implementação do Lock Otimista):**
   - Na implementação do backend (a ser realizada pelo Claude Code), assegurar que o update condicional seja executado com verificação estrita de linhas afetadas:
     ```python
     stmt = (
         update(Answer)
         .where(Answer.id == answer_id, Answer.transcription_version == payload.expected_version)
         .values(
             manual_transcription_draft=payload.text,
             transcription_version=Answer.transcription_version + 1,
         )
     )
     result = db.execute(stmt)
     if result.rowcount == 0:
         db.rollback()
         raise HTTPException(status_code=409, detail=...)
     ```
     Ou, alternativamente, utilizar `select(Answer).where(...).with_for_update()` dentro do bloco transacional para inspecionar `transcription_version` e `transcription_status` sob row-lock pessimista antes de comitar. Ambas as abordagens blindam o PostgreSQL contra race conditions.
2. **Ambiente Obrigatório para Testes de Concorrência:**
   - Assegurar que os testes automatizados de ACD-15 e ACD-16 sejam executados exclusivamente contra a instância de PostgreSQL isolada (e não em SQLite em memória), utilizando threads com conexões de banco separadas para reproduzir a concorrência real.

---

## 5. Declaração de Não-Interferência Operacional

Em estrita conformidade com a governança do AvalIA e o papel de revisor independente delegado ao Antigravity:
- **Código:** Nenhum código de produção foi alterado ou implementado.
- **Plano:** O arquivo [`plano_transcricao_manual_confirmacao_humana.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md) foi mantido estritamente inalterado pelo revisor (não editado).
- **Banco de Dados:** Nenhuma operação DDL/DML ou migração foi aplicada em `avalia_dev` ou qualquer outro ambiente.
- **Git:** Nenhuma operação `stage`, `commit`, `push`, `branch` ou `worktree` foi executada.
