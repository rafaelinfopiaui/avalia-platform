---
id: "EXEC-AAAA-MM-DD-NN"
tipo: execucao
sprint: "<ID ou sem sprint>"
gerado_em: "AAAA-MM-DDTHH:MM:SS-03:00"
executor: "<nome>"
status: parcial
commit_referencia: "<sha>"
---

# Snapshot <ID> — <título>

> Registro histórico. Não promover automaticamente a baseline. Correções posteriores usam adendo datado ou novo snapshot.

## 1. Abertura

- objetivo da sessão: <objetivo>;
- escopo autorizado: <escopo>;
- fora de escopo: <limites>;
- branch/upstream/commit: <valores>;
- working tree inicial: <saída ou resumo fiel>;
- alterações preexistentes protegidas: <paths>;
- dependências/bloqueantes: <IDs/nenhum>.

## 2. Entregas

| Item | Estado | Entrega | Evidência |
|---|---|---|---|
| <ID> | planejado/implementado/validado/homologado | <fato> | <link> |

## 3. Não entregas e lacunas

- <item, motivo e impacto>.

## 4. Arquivos impactados

| Caminho | Natureza | Item |
|---|---|---|
| <path> | criado/alterado/excluído | <ID> |

## 5. Validações executadas

| Data/fuso | Item/AC | Comando/procedimento | Ambiente | Tipo | Resultado real |
|---|---|---|---|---|---|
| <data> | <ID> | `<comando>` | <ambiente> | <tipo> | <resultado> |

Validações não executadas: <listar>.
Resultados históricos usados apenas como contexto: <listar origem/data>.

## 6. Decisões, débitos e bloqueantes

- decisões: <links/nenhuma>;
- débitos: <links/nenhum>;
- bloqueantes: <links/nenhum>.

## 7. Estado final

- working tree final: <registro>;
- entregas não versionadas/sem commit: <paths>;
- commit/push/deploy/tag/ação remota: <não realizados ou evidência autorizada>;
- status da execução: concluída/concluída com débitos/parcial/reprovada/bloqueada;
- homologação por Rafael: pendente/registrada com referência.

## 8. Baseline

- esta execução promove baseline? não, salvo decisão explícita registrada;
- último baseline validado permanece: <link/nenhum>;
- condição para promoção: <condição>.

## 9. Próxima ação

<uma ação objetiva; não iniciar trabalho não autorizado>.

## 10. Adendos

Nenhum. Adendos preservam o texto original, trazem data/fuso, autor, motivo e evidência.
