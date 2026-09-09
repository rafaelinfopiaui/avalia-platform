# AvalIA — AI Engine Local

Serviço de inferência local e validação estruturada para avaliação assistida de respostas discursivas curtas e médias (produto AvalIA).

Opera de forma **independente e stateless**, aplicando uma **cascata de decisão reduzida** (Níveis 0, 1 e 3) e garantindo estrita conformidade com o contrato definido em `docs/contracts/ai-engine-output.schema.json`.

---

## Requisitos de Ambiente

- **Python**: 3.11+
- **Runtime Local**: Ollama rodando localmente (`http://localhost:11434`)
- **Modelo Baseline**: `qwen2.5:7b-instruct-q4_K_M` (ADR-005)
  - Instalação: `ollama pull qwen2.5:7b-instruct-q4_K_M`

---

## Configuração e Instalação

A partir da pasta `ai-engine/`:

```bash
# 1. Criar o ambiente virtual com Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
```

### Variáveis de Ambiente (`.env`)

| Variável | Padrão | Descrição |
|---|---|---|
| `AI_ENGINE_MODE` | `real` | Modo de execução: `real` (inferência real via Ollama) ou `simulated` (modo de contingência/teste determinístico). |
| `AI_MODEL_NAME` | `qwen2.5:7b-instruct-q4_K_M` | Nome do modelo baixado no Ollama. |
| `OLLAMA_URL` | `http://localhost:11434` | URL base do serviço Ollama local. |
| `HOST` | `0.0.0.0` | Host de escuta do servidor FastAPI. |
| `PORT` | `8001` | Porta HTTP do serviço. |
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `SCHEMA_PATH` | `../docs/contracts/ai-engine-output.schema.json` | Caminho para o JSON Schema de contrato. |

---

## Como Executar

```bash
# Ativar o ambiente virtual
source .venv/bin/activate

# Iniciar o servidor FastAPI na porta 8001
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

A documentação interativa Swagger estará acessível em: `http://localhost:8001/docs`.

---

## Endpoints

### 1. `POST /v1/analyze`
Recebe o enunciado, resposta de referência, rubrica por critérios e a resposta do aluno.

**Proteção de Privacidade (RN-010 e RNF-02):**
- Atributos pessoais (nome, matrícula) **nunca** são exigidos nem repassados ao modelo. Se fornecidos no payload, são automaticamente ignorados.

**Payload de Exemplo:**
```json
{
  "question_statement": "Explique a diferença entre pilha e fila, citando suas políticas de acesso.",
  "reference_answer": "Pilha opera com LIFO (último a entrar é o primeiro a sair). Fila opera com FIFO (primeiro a entrar é o primeiro a sair).",
  "rubric": [
    {
      "criterion_id": "c1",
      "name": "Conceito de Pilha (LIFO)",
      "description": "Identificação correta da disciplina LIFO.",
      "max_score": 2.5
    },
    {
      "criterion_id": "c2",
      "name": "Conceito de Fila (FIFO)",
      "description": "Identificação correta da disciplina FIFO.",
      "max_score": 2.5
    }
  ],
  "answer_text": "A pilha funciona como LIFO, onde o último elemento adicionado é o primeiro removido. Já a fila é FIFO, onde o primeiro elemento adicionado é o primeiro atendido."
}
```

**Saída em Conformidade com `docs/contracts/ai-engine-output.schema.json`:**
```json
{
  "schema_version": "1.0",
  "engine_mode": "real",
  "model": "qwen2.5:7b-instruct-q4_K_M",
  "criterion_scores": [
    {
      "criterion_id": "c1",
      "score": 2.5,
      "max_score": 2.5,
      "reason": "O aluno definiu perfeitamente a pilha como LIFO e explicou seu funcionamento.",
      "evidence": "A pilha funciona como LIFO, onde o último elemento adicionado é o primeiro removido.",
      "confidence": 0.95
    },
    {
      "criterion_id": "c2",
      "score": 2.5,
      "max_score": 2.5,
      "reason": "O aluno explicou com precisão a fila e a política FIFO.",
      "evidence": "Já a fila é FIFO, onde o primeiro elemento adicionado é o primeiro atendido.",
      "confidence": 0.95
    }
  ],
  "overall_confidence": 0.95,
  "confidence_method_version": "heuristic-v1",
  "review_recommendation": "REVIEW_OPTIONAL",
  "flags": [],
  "duration_ms": 1420
}
```

### 2. `GET /v1/health`
Verifica a conectividade com o Ollama local e exibe o estado operacional sem vazar credenciais ou caminhos internos:
```json
{
  "status": "healthy",
  "engine_mode": "real",
  "model": "qwen2.5:7b-instruct-q4_K_M",
  "ollama_status": "up"
}
```

---

## Arquitetura e Decisões

### Cascata de Decisão (Níveis 0, 1 e 3)
1. **Nível 0 — Validação Rápida:**
   - Respostas em branco ou com menos de 10 caracteres úteis são interceptadas imediatamente.
   - Retorna flag `EMPTY_ANSWER`, `review_recommendation="REVIEW_REQUIRED"`, confiança baixa (`0.10`), sem invocar o LLM.
2. **Nível 1 — Regras e Sinais:**
   - Extrai palavras-chave dos critérios da rubrica e verifica sua presença no texto.
   - Serve como sinal determinístico para cálculo de concordância de regras.
   - Detecta tentativas de *prompt injection* (ex.: "ignore as instruções", "you are now") sinalizando com `PROMPT_INJECTION_SUSPECTED` e exigindo revisão humana, sem penalizar o mérito conceitual diretamente.
3. **Nível 3 — LLM Local (Ollama + Prompt Versionado):**
   - Prompt de sistema versionado (`prompt-v1.0` em `app/prompts/prompt_v1.py`).
   - Trata a resposta do aluno como **dado não confiável** isolado entre tags `<resposta_do_aluno>`.
   - Avalia o **conteúdo conceitual**, não a similaridade textual superficial.
   - Gera notas por critério no intervalo `[0, max_score]`, justificativa e evidência literal em pt-BR.
   - Valida contra o schema; se inválido, executa **uma tentativa de reparo JSON**.

### Modo Simulado Explícito (RN-017)
- Quando `AI_ENGINE_MODE=simulated`, gera resultado determinístico de teste marcado com `engine_mode="simulated"` e flag `SIMULATED_MODE`.
- **Regra estrita:** Se `AI_ENGINE_MODE=real` e o Ollama estiver inacessível, o serviço retorna **HTTP 503**, **NUNCA** fabricando silenciosamente um resultado simulado disfarçado de real.

### Cálculo de Confiança Heurística (ADR-008)
- Registrado como `confidence_method_version="heuristic-v1"`.
- **Atenção (RN-016):** Trata-se de indicador heurístico operacional, **NÃO calibrado probabilisticamente**.
- Componentes ponderados: Validade do schema (40%), Cobertura de critérios (35%), Concordância com regras (25%).
- Faixas:
  - $\ge 0.85$: Alta $\rightarrow$ `REVIEW_OPTIONAL`
  - $0.60 \dots 0.84$: Média $\rightarrow$ `REVIEW_RECOMMENDED`
  - $< 0.60$: Baixa $\rightarrow$ `REVIEW_REQUIRED`

### Logs Estruturados (RNF-07)
- Formato JSON em stdout com `correlation_id` (via cabeçalho `X-Correlation-ID`).
- Nunca registra a resposta completa do aluno em log (apenas comprimento e hash SHA-256 truncado).

---

## Execução dos Testes

```bash
# Executar suíte completa de testes automatizados
pytest -v
```
