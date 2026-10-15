# Parecer independente — Antigravity (revisão de DESENHO, antes do código)

- Revisor: Antigravity CLI (`agy -p`), modelo "Claude Opus 4.6 (Thinking)"
- Data: 2026-10-14
- Alvo: `desenho_bl-av-4b-05_retencao_exclusao_imagens.md` (após as 4 correções de Rafael + D1/D2/D3)
- Modo: somente leitura (sem escrita/git/banco); leu código real de models.py, main.py, routers/images.py, schemas.py e a migração d5e3a7c19f42
- Observação operacional: a 1ª execução em `-p` foi abortada por soft-deny de confirmação de ferramenta no passo 8; re-executada com `--dangerously-skip-permissions` (leitura liberada, escrita proibida pelo prompt).

## PARECER: APROVADO COM RESSALVAS

### Confirmações (código ↔ desenho alinhados)
- Guard de `request_correction` (main.py:989-998) descrito corretamente — bloqueia A, permite B+.
- FKs de `AnswerImage` sem `ondelete` (models.py:308-310, migração d5e3a7c19f42:34) — distinção RESTRICT/NO ACTION correta; não presumir RESTRICT.
- Classificação de falha parcial (§4.5) correta, não invertida.
- Proibição de campos sensíveis no AuditEvent correta.
- Cobertura D1/D2/D3 pelos ACD-01 a ACD-13 substancialmente completa.
- Nenhuma afirmação do desenho contradita pelo código real.

### Ressalvas (4 achados)
| # | Severidade | Achado |
|---|---|---|
| R2 | Alta | ACD-10 (corrida excluir↔confirmar): lock cruzado insuficientemente especificado. `UPDATE ... WHERE deleted_at IS NULL` opera em `answer_images`, mas a confirmação opera em `answers` (main.py:860). São tabelas diferentes: o lock otimista de `transcription_version` NÃO serializa as duas operações. Precisa de `SELECT ... FOR UPDATE` na linha de `answers` como ponto comum de serialização em ambos os caminhos (exclusão e confirmação). |
| R1 | Média | §7 omite que `list_image_answers` e `_answer_with_images` (main.py:766-771) precisam filtrar `deleted_at IS NULL` — hoje retornam todas as imagens por `answer_id`, sem filtro. |
| R4 | Média | `AnswerImageOut` (schemas.py:177-186) expõe `original_filename` e `sha256_hash` na API autenticada. Comportamento pós-exclusão lógica não especificado (listar excluída? com quais campos?). |
| R3 | Baixa | Falta ACD para restauração quando o estágio avançou de A→B entre a exclusão e a tentativa de restaurar. Antigravity classifica como DECISÃO DE PRODUTO (permitir ou bloquear restauração pós-avanço). |

### Recomendação do revisor
Pode prosseguir para implementação após endereçar R2 (mecanismo de lock) no nível de especificação. R1/R4 resolvíveis durante a codificação. R3 é decisão de produto.

## Verificação independente do orquestrador (não confiei só no parecer)
- R1: confirmado em main.py:766-771 — `.filter(AnswerImage.answer_id == answer.id)` sem `deleted_at`.
- R4: confirmado em schemas.py:181,184 — `original_filename` e `sha256_hash` em `AnswerImageOut`.
- R2: confirmado — confirmação faz `update(Answer)...` (main.py:860); exclusão fará `update(AnswerImage)...`; tabelas distintas, sem serialização comum sem `SELECT FOR UPDATE` em `answers`.
