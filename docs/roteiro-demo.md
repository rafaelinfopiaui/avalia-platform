# Roteiro de demonstração — AvalIA (experimental, dados fictícios)

Duração sugerida: 8–10 minutos. Público: coordenador do estágio.

Aviso a repetir no início da demo: "Esta é uma demonstração experimental,
com dados fictícios. Não representa avaliação real de alunos e ainda não
foi validada quanto às diretrizes do CNE sobre IA em avaliações
discursivas (pendência registrada, ver docs/pendencia-regulatoria.md)."

## Pré-requisitos para rodar a demo

```bash
brew services start postgresql@16
brew services start ollama

cd core && source .venv/bin/activate && uvicorn app.main:app --port 8000 &
cd ai-engine && source .venv/bin/activate && uvicorn app.main:app --port 8001 &
cd frontend && npm run dev &
```
Abrir http://localhost:5173. Login: `professor.demo@avalia-platform.example`
/ `DemoAvalIA123!` (ver `core/.env.example`).

## Roteiro

1. **Login** — mostrar autenticação, mensagem genérica se a senha estiver
   errada (não revela se o e-mail existe).

2. **Avaliação existente (seed)** — abrir a avaliação "Estruturas de Dados
   — Avaliação 1", já publicada, questão "Explique a diferença entre pilha
   e fila", rubrica com 4 critérios (LIFO, FIFO, Diferenciação, Clareza),
   soma 6,00 = valor da questão.

3. **Rubrica inválida (bloqueio no backend)** — criar uma nova avaliação
   com valor de questão 5,0 e uma rubrica cuja soma dê 4,0. Tentar
   publicar: o backend recusa com `RUBRIC_TOTAL_MISMATCH` e mensagem
   "A soma dos critérios deve ser 5,00." — mostrar que a validação é no
   servidor, não só na interface.

4. **Inserir resposta e solicitar análise** — na avaliação do seed, inserir
   uma resposta digital fictícia (usar uma das três variantes abaixo) e
   clicar "Solicitar análise da IA". Mostrar a tela de processamento com
   polling (PENDENTE → PROCESSANDO → SUGERIDA).

   Respostas de exemplo (já inseridas no seed, ou digitar novamente):
   - **Correta**: "Pilha segue LIFO... Fila segue FIFO..." → nota
     esperada próxima de 6,0/6,0.
   - **Parcial**: menciona LIFO mas erra ou omite a fila → nota
     intermediária.
   - **Conceitualmente errada**: "Pilha e fila são a mesma coisa..." →
     nota baixa/zero, mesmo compartilhando palavras-chave com a
     referência (mostra que o sistema não confunde similaridade textual
     com correção conceitual).

5. **Tela de revisão lado a lado** — mostrar resposta do aluno (somente
   leitura) ao lado dos critérios com sugestão da IA: pontuação,
   evidência (trecho citado), justificativa, confiança por critério e
   geral. Destacar o rótulo "Sugestão da IA — revisar" versus a área de
   decisão humana — nunca a IA aparece como nota final.

6. **Aprovar ou alterar** — aprovar rapidamente, ou alterar um critério
   (a interface exige justificativa para alterar) e mostrar o recálculo
   automático do total e o registro da divergência IA × humano.

7. **Indisponibilidade do AI Engine (opcional, se der tempo)** — parar o
   processo do AI Engine (`Ctrl+C` no terminal correspondente), solicitar
   nova análise: o job vai para FALHA com mensagem clara ("Não foi
   possível analisar esta resposta...") e a interface oferece seguir
   para revisão manual — nenhum resultado é fabricado.

8. **Persistência** — reiniciar Core e AI Engine e mostrar que a correção e
   a revisão anteriores continuam disponíveis (dados no PostgreSQL).

## O que NÃO mostrar como concluído

Dashboards, exportação, processamento em lote, CSV, gestão avançada de
usuários — fora do escopo desta demonstração (ver `docs/backlog.md`).
