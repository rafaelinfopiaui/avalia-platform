# Parecer de Revisão Independente de Desenho Técnico — Resposta por Imagem (AV-S06B)

- **Data:** 2026-10-14T02:45:00-03:00
- **Revisor independente:** Antigravity (Gemini 3.8 Flash High)
- **Documento revisado:** [`docs/governance/evidence/AV-S06B/desenho_resposta_por_imagem.md`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/docs/governance/evidence/AV-S06B/desenho_resposta_por_imagem.md)
- **Escopo desta revisão:** EXCLUSIVAMENTE a avaliação técnica do desenho conceitual e arquitetural, antes de qualquer implementação. Não há alteração de código, não há migração ou escrita em banco de dados, e não há ações de Git (`commit`, `push`, `tag`).

---

## 1. Veredito do Desenho

**APROVADO COM AJUSTES**

O documento de desenho técnico resolve com clareza e fidelidade a direção de produto aprovada por Rafael: permite que a foto seja a entrada inicial da resposta sem exigir texto digitado, vazio ou fictício, mantendo a correção bloqueada de forma estrita até que haja transcrição confirmada. A abordagem de atomicidade e prevenção de artefatos órfãos reutiliza o padrão já homologado na AV-S06B.

O veredito é "Aprovado com Ajustes" (e não reprovação) porque a arquitetura central está sólida, e os ajustes apontados são **puramente técnicos e de detalhamento pré-implementação** — não exigem nova decisão de produto e podem ser sanados diretamente na especificação e codificação.

---

## 2. Avaliação dos 7 Pontos Solicitados

### 2.1. Coerência da direção aprovada
- **Análise:** O desenho atende aos três pilares da decisão de Rafael:
  1. A foto é a entrada primária da resposta por meio do novo endpoint transacional `POST /v1/answers/image`, sem exigir texto fictício ou strings vazias;
  2. `Answer.text` torna-se `NULL` no banco para respostas por imagem;
  3. A correção permanece rigorosamente bloqueada (§6), e o ciclo de vida termina legitimamente em `AGUARDANDO_TRANSCRICAO`, sem simulações de OCR ou transcrições falsas.
- O fluxo textual existente (`POST /v1/answers`) continua inalterado em contrato e comportamento, preservando total estabilidade.

### 2.2. Modelo e migração mínimos
- **Análise:** A combinação de `Answer.text` nullable + `source` (`TEXT` | `IMAGE`) + `transcription_status` (`AGUARDANDO_TRANSCRICAO` | `TRANSCRICAO_CONFIRMADA`) é a **menor mudança coerente**:
  - `source` registra a proveniência imutável da resposta (se nasceu texto digitado ou foto);
  - `transcription_status` gerencia o ciclo de vida da transcrição;
  - Fundir ambos em um único campo seria um erro arquitetural: quando houver OCR e o professor confirmar o texto (AV-S08B), `transcription_status` passará a `TRANSCRICAO_CONFIRMADA` e `text` será preenchido. Sem o campo `source`, o sistema perderia o registro histórico de que aquela resposta se originou de uma foto, impedindo interfaces de auditoria ou visualização lado a lado da foto com o texto corrigido.
- O backfill determinístico (`source=TEXT`, `transcription_status=TRANSCRICAO_CONFIRMADA`) é seguro e direto para os dados existentes. O downgrade recusando reversão se houver `text IS NULL` replica o padrão defensivo já estabelecido em [`core/alembic/versions/d5e3a7c19f42_add_answer_images.py#L41-L49`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/alembic/versions/d5e3a7c19f42_add_answer_images.py#L41-L49).

### 2.3. Invariantes (§3)
- **Análise:** Os invariantes propostos estão consistentes, mas identificamos **três pontos de atenção que necessitam de ajuste no detalhamento**:
  1. *Invariante 1 (`source=TEXT => text NOT NULL e não-vazio`):* Atualmente, o contrato em [`core/app/schemas.py#L144-L148`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py#L144-L148) define `AnswerInput.text: str`, sem `min_length` nem validação de espaços em branco (`.strip()`). Para assegurar o Invariante 1 na criação textual, o backend deve validar explicitamente contra strings vazias ou só de espaços.
  2. *Invariante 2 (`source=IMAGE => deve existir >= 1 AnswerImage vinculada`):* A transação de criação atômica (§5) garante isso no nascimento. Como a exclusão de imagens está explicitamente fora de escopo nesta fatia (§9), o invariante não corre risco agora; no entanto, deve constar no desenho a nota de que futuras rotas de exclusão (BL-AV-4B-05) não poderão remover a última imagem de uma resposta `source=IMAGE` enquanto `text` for nulo.
  3. *Invariantes no nível do SGBD:* O desenho cita validação em modelo/serviço. Recomenda-se adicionar `CheckConstraint` na tabela `answers` (`(source = 'TEXT' AND text IS NOT NULL) OR (source = 'IMAGE')`), garantindo integridade mesmo contra scripts manuais ou manipulações fora da API.

### 2.4. Bloqueio de correção (§6) e cobertura dos caminhos
- **Análise:** Inspeção exaustiva do repositório confirmou que:
  - `CorrectionJob` é instanciado em produção **exclusivamente** em [`core/app/main.py#L658`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L658) (`request_correction`);
  - `run_correction_job` é enfileirado **exclusivamente** em [`core/app/main.py#L665`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L665).
- Portanto, o guard posicionado em `request_correction` bloqueia 100% dos caminhos de produção.
- *Defesa em profundidade necessária:* Dentro de `run_correction_job` ([`core/app/services/correction.py#L63`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/services/correction.py#L63)), o payload monta `"answer_text": answer.text` e chama o AI Engine. No AI Engine ([`ai-engine/app/schemas.py#L43`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/ai-engine/app/schemas.py#L43)), `answer_text` é `str` obrigatório. Se por qualquer anomalia (ex.: testes chamando o serviço diretamente) `run_correction_job` receber uma resposta com `text=None`, o AI Engine responderá HTTP 422 e o Core marcará o job como falha de rede/indisponibilidade do AI Engine. Recomenda-se incluir uma guarda fail-fast também dentro de `run_correction_job`.

### 2.5. Falha banco/arquivo (§7) e repetição de requisição (§8)
- **Análise da ordem transacional:** A ordem proposta (validar -> gravar temporário -> validar com Pillow -> renomear final -> persistir banco -> commit único -> rollback + unlink se commit falhar) é matematicamente imune a órfãos:
  - Não há registro no banco sem arquivo correspondente no disco;
  - Não há arquivo solto no disco sem registro no banco.
- **Ausência deliberada de idempotência:** Está correta. A governança do projeto veda a introdução de políticas de negócio não aprovadas por Rafael (ex.: tentar deduplicar fotos idênticas ou proibir novo envio do mesmo aluno para a mesma questão). A documentação honesta do efeito de repetições (cada chamada cria uma nova `Answer`) e a recomendação de mitigação de UX no frontend (desabilitar botão ao submeter) estão perfeitamente dimensionadas.

### 2.6. Compatibilidade (§4) e consumidores existentes
- **Análise:**
  - `core/app/schemas.py`: [`AnswerOut`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py#L150-L160) atualmente tipa `text: str`. Precisa ser alterado para `text: Optional[str] = None` junto à adição de `source` e `transcription_status`.
  - `GET /v1/correction-jobs/{job_id}/context` ([`core/app/main.py#L698`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/main.py#L698)): usa `AnswerOut.model_validate(answer)`. Como a correção só é disparada com texto válido, não haverá `null` nos jobs existentes, e o schema aceitará `null` sem quebras.
  - Consumidor frontend: [`frontend/src/types.ts#L69`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/types.ts#L69) deve refletir `text?: string | null` e os novos campos. Em [`frontend/src/pages/ReviewPage.tsx#L202`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/pages/ReviewPage.tsx#L202), `<p>{answer?.text}</p>` não quebra ao receber `null`/`undefined`.

### 2.7. Riscos e omissões identificados
1. **Schema de retorno de `POST /v1/answers/image` não detalhado:** O desenho indica os campos recebidos, mas não define se a resposta é `AnswerOut` ou um schema composto que já inclua a imagem criada (ex.: `AnswerImageOut` ou lista de imagens). Se retornar apenas `AnswerOut`, o cliente não recebe o `image_id` da foto recém-anexada a menos que consulte `GET /v1/answers/{id}/images`.
2. **Parsing de formulário multipart (`max_fields`):** O endpoint homologado em [`core/app/routers/images.py#L216`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/routers/images.py#L216) usa `request.form(max_files=1, max_fields=1)`. O novo endpoint receberá 3 campos (`file`, `question_id`, `student_name_fake`). A reutilização mecânica desse trecho provocará erro 400 por estouro de campos.
3. **Ordem de checagem fail-fast:** A validação de `question_id`, autorização do professor e verificação de que `student_name_fake` não é vazio deve ocorrer **antes** de criar arquivos temporários ou ler streams no disco.
4. **Isolamento de dependências e teste AST preexistente:** O arquivo [`core/app/tests/test_answer_images.py#L420-L448`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/tests/test_answer_images.py#L420-L448) possui o teste `test_images_module_has_no_ocr_or_correction_references`, que inspeciona a AST de `images.py` e proíbe referências a correção/IA. A implementação do novo endpoint em `images.py` ou `main.py` deve manter essa estrita segregação.

---

## 3. Achados Concretos no Contrato Atual

| Ref. | Arquivo:Linha | Contrato Atual | Impacto no Desenho / Ajuste Necessário |
|---|---|---|---|
| **ACH-01** | [`core/app/schemas.py#L150-L160`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py#L150-L160) | `AnswerOut` define `text: str` obrigatório. | Tornar `text: Optional[str] = None` e adicionar `source: AnswerSource` e `transcription_status: TranscriptionStatus` para evitar `ValidationError` nas respostas por imagem. |
| **ACH-02** | [`core/app/schemas.py#L144-L148`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/schemas.py#L144-L148) | `AnswerInput.text: str` sem validação de whitespace. | Para que o Invariante 1 seja estrito no backend, adicionar validação (`min_length=1` e `.strip() != ""`) ao criar resposta textual. |
| **ACH-03** | [`core/app/routers/images.py#L216`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/routers/images.py#L216) | `request.form(max_files=1, max_fields=1)` | Em `POST /v1/answers/image`, há 3 campos de form (`file`, `question_id`, `student_name_fake`). Ajustar para `max_fields=5` ou parâmetros declarativos FastAPI para evitar HTTP 400. |
| **ACH-04** | [`core/app/services/correction.py#L63`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/services/correction.py#L63) e [`ai-engine/app/schemas.py#L43`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/ai-engine/app/schemas.py#L43) | AI Engine exige `answer_text: str`. `run_correction_job` envia `answer.text` diretamente. | Adicionar defesa em profundidade em `run_correction_job`: fail-fast se `answer.text` for nulo/vazio, registrando falha explícita antes de chamar a rede. |
| **ACH-05** | [`core/app/tests/test_answer_images.py#L420-L448`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/app/tests/test_answer_images.py#L420-L448) | AST check proíbe palavras como `run_correction_job`, `request_correction`, `CorrectionJob` em `images.py`. | Se o endpoint for colocado em `routers/images.py`, assegurar que não haja imports ou menções acidentais a esses termos; o guard de correção deve ficar estritamente em `main.py`. |
| **ACH-06** | [`frontend/src/types.ts#L69`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/frontend/src/types.ts#L69) | `export interface Answer { ... text: string }` | Atualizar tipagem no frontend para `text?: string | null; source?: 'TEXT' | 'IMAGE'; transcription_status?: ...`. |

---

## 4. Recomendações Pontuais para a Implementação

1. **Definição formal do schema de retorno do novo endpoint:**
   - Formalizar se `POST /v1/answers/image` responde com `AnswerOut` simples (e o cliente faz `GET /answers/{id}/images` para obter a URL/imagem) ou se responde com um schema composto (ex.: `AnswerOut` acrescido do array `images: list[AnswerImageOut]`). Ambas as opções são válidas; explicitar no desenho evita ambiguidades no frontend.
2. **Fail-fast estrito antes de I/O em disco:**
   - No fluxo de `POST /v1/answers/image`, checar a autenticação, existência da `Question`, autorização da avaliação (`require_assessment_mutation`) e validação de `student_name_fake` **antes** de gravar qualquer byte em arquivo temporário.
3. **Formatação de erro 422 coerente com o padrão do projeto:**
   - Em `main.py:655`, erros de negócio utilizam o helper `error_response(422, "CODIGO", "Mensagem", correlation_id)`. O guard de bloqueio de correção (§6) deve seguir essa mesma convenção padronizada do `ErrorEnvelope`.
4. **Convenção de Enums no Alembic:**
   - Assegurar que os enums `AnswerSource` e `TranscriptionStatus` sigam a convenção de tipos nomeados do PostgreSQL adotada no repositório ([`core/alembic/versions/c4a8b2d91e37_add_academic_structure.py#L88-L92`](file:///Users/rafaeloliveira/Projeto%20Est%C3%A1gio/avalia-plataform/core/alembic/versions/c4a8b2d91e37_add_academic_structure.py#L88-L92)), garantindo um downgrade seguro e idempotente.

---

## 5. Declaração de Não-Interferência Operacional

Em conformidade rigorosa com o mandato de revisor independente e com a política de governança do projeto:
- **Código:** Nenhum arquivo de código foi modificado ou executado para alterações.
- **Banco de Dados:** Nenhuma conexão de escrita, migração ou comando DDL/DML foi executado contra `avalia_dev` ou qualquer outro banco.
- **Git:** Nenhum comando `git add`, `git commit`, `git push`, `git checkout` ou criação de branch/tag foi executado.
- **Ambiente:** A working tree preexistente permanece rigorosamente intacta.
