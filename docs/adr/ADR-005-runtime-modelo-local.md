# ADR-005 — Runtime local e modelo baseline

Status: Aceito — 09/09/2026
Responsável: Rafael Sampaio Oliveira (Tech Leader) / G3

## Contexto
Requisito do produto: inferência local, sem dependência obrigatória de API
comercial. Hardware desta máquina de desenvolvimento: macOS, Apple M5 Pro,
24 GB RAM, ~818 GB livres em disco (verificado nesta sessão).

## Decisão
Runtime: **Ollama** (open source, MIT license, já empacotado via Homebrew,
expõe API HTTP local em `localhost:11434`).
Modelo baseline: **qwen2.5:7b-instruct-q4_K_M** (~4,7 GB em disco,
quantização Q4_K_M, licença Apache 2.0/Qwen license conforme distribuição
oficial).

## Justificativa
- Ollama é a tecnologia de referência citada no PRD (seção 11, junto com
  llama.cpp) e tem instalação/operação mais simples via Homebrew.
- Qwen2.5 7B tem desempenho competitivo em português e em geração de JSON
  estruturado (necessário para o schema de saída do AI Engine), e cabe
  folgadamente em 24 GB de RAM nesta máquina.
- Alternativa mais leve (Llama 3.2 3B) ficaria mais rápida mas com qualidade
  menor em tarefas de rubrica interpretativa — não escolhida como padrão,
  mas documentada como fallback de contingência caso o hardware da squad
  seja mais limitado (ver `.env.example` do AI Engine, variável
  `AI_MODEL_NAME` configurável).

## Antes do download
Tamanho: ~4,7 GB. Finalidade: inferência local de correção assistida.
Alternativa mais leve: Llama 3.2 3B (~2 GB), menor qualidade em rubricas
complexas. Esta decisão foi tomada sob timeout de confirmação do usuário
(ver relatório final) e deve ser revisada por Rafael.

## Consequências
Squad deve revalidar em hardware próprio (nem todo integrante terá 24 GB de
RAM); modelo é configurável via variável de ambiente, não hardcoded.
