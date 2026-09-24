# Proposta de saneamento de duplicatas em HumanReview — dependente de aprovação de Rafael

Status: **PROPOSTA, NÃO EXECUTADA**. Nenhuma ação deste documento foi realizada. Depende de
aprovação explícita de Rafael, item por item, antes de qualquer execução.

## 1. Contexto

A migração `7b1d6d853f20` (versão corrigida em 2026-09-24, após rejeição da versão anterior por
Rafael) verifica a existência de HumanReview duplicadas por `job_id` e **aborta sem tocar em
nenhum dado** quando encontra alguma. Isso significa que a migração NUNCA poderá avançar para
`avalia_dev` (ou qualquer banco com duplicatas reais) até que as duplicatas sejam saneadas por um
procedimento explícito, separado desta migração.

Duplicata real conhecida hoje em `avalia_dev` (dado fictício de teste, não dado real de aluno):

```
job_id=4f56a10b-3a44-4df5-9047-adef7546a3c0  review_count=3
  id=31d31b5c-05c7-4206-b2ff-43b2eda14026  decision=APPROVE  final_total=2.00  justification=(vazio)  created_at=2026-09-23 22:53:35.110755
  id=8a9c2ba6-fca4-4f47-9b2a-12f7a3e7345c  decision=APPROVE  final_total=2.00  justification=(vazio)  created_at=2026-09-23 22:55:15.904278
  id=9459489c-dd8e-4f33-936a-bc76cb7d5f0b  decision=APPROVE  final_total=2.00  justification=(vazio)  created_at=2026-09-23 22:58:47.630896
```
(consulta real executada em 2026-09-24: `SELECT id, decision, final_total, justification,
created_at FROM human_reviews WHERE job_id='4f56a10b-3a44-4df5-9047-adef7546a3c0' ORDER BY
created_at;` — reproduzível, verificável ao vivo.)

## 2. Classificação: equivalente vs. conflitante

Antes de qualquer saneamento, cada grupo de duplicatas de um mesmo `job_id` precisa ser
classificado, não tratado uniformemente:

- **Equivalentes:** mesmo `reviewer_id`, mesma `decision`, mesmos `final_scores` (normalizados) e
  mesma `justification` (normalizada None/""). Representam o **mesmo ato de decisão** registrado
  mais de uma vez pela ausência histórica de idempotência — não representam informação adicional
  perdida ao consolidar.
- **Conflitantes:** qualquer diferença real em `decision`, `final_scores` ou `justification` entre
  linhas do mesmo `job_id` (mesmo revisor ou revisores diferentes). Representam **decisões humanas
  genuinamente diferentes** sobre o mesmo job — sanear isso não é deduplicação, é uma decisão de
  produto sobre qual registro é a "decisão final" e o que fazer com os demais.

O caso conhecido em `avalia_dev` (`4f56a10b-...`) é **equivalente** pelas 3 linhas (mesmo revisor,
mesma decisão, mesma nota, sem justificativa). Não há indício de caso conflitante nesta base hoje,
mas o procedimento abaixo cobre ambos os casos para não presumir que nunca ocorrerão.

## 3. Procedimento proposto (não executado)

### 3.1 Backup

1. `pg_dump` completo e isolado de `avalia_dev` antes de qualquer saneamento, com timestamp,
   armazenado fora do repositório (não versionado).
2. Export específico da tabela `human_reviews` (todas as linhas, todos os campos) para CSV/JSON,
   como registro adicional e imutável do estado pré-saneamento — preservado independentemente do
   backup completo, para auditoria futura mesmo que o backup completo seja descartado.

### 3.2 Rastreabilidade (preservar, não apagar)

Em vez de `DELETE` das linhas excedentes, propõe-se:

- Renomear/mover as linhas excedentes para uma tabela de arquivo `human_reviews_superseded`
  (mesma estrutura de `human_reviews` + coluna `superseded_reason` e `superseded_at`), preservando
  os dados originais integralmente, em vez de apagá-los da base.
- A linha "vencedora" de cada grupo permanece em `human_reviews` — critério de qual é a vencedora
  é uma decisão de Rafael por grupo (não automática), registrada nominalmente antes da execução.
  Para grupos equivalentes, o critério provavelmente é neutro (qualquer uma serve, pois são
  idênticas); para grupos conflitantes, exige decisão explícita de política — este documento não
  presume qual seria.
- A tabela `human_reviews_superseded` não é apagada nesta sprint; sua retenção/expurgo futuro é
  decisão separada.

### 3.3 Passos de execução (somente após aprovação explícita)

1. Backup completo (3.1).
2. Rodar um script de **diagnóstico** (somente leitura) que lista todos os grupos duplicados,
   classificados como equivalente/conflitante (critério da seção 2), e imprime um relatório para
   revisão humana antes de qualquer escrita.
3. Rafael revisa o relatório e decide, por grupo conflitante (se houver), qual linha é a vencedora
   — decisão registrada nominalmente no relatório de execução.
4. Script de saneamento: dentro de uma transação, move as linhas não-vencedoras para
   `human_reviews_superseded` (não `DELETE`), preservando todos os campos originais.
5. Validação pós-saneamento: `SELECT job_id, COUNT(*) FROM human_reviews GROUP BY job_id HAVING
   COUNT(*) > 1;` deve retornar 0 linhas.
6. Só então a migração `7b1d6d853f20` pode ser executada em `avalia_dev` — como ato separado,
   também sujeito a autorização específica (não incluída nesta proposta).

### 3.4 Validação do procedimento antes de aplicar a `avalia_dev`

Todo o procedimento acima deve primeiro ser testado em uma cópia isolada de `avalia_dev` (dump
restaurado em banco descartável), nunca diretamente na base operacional na primeira execução.

## 4. O que este documento NÃO decide

- Não decide se a linha vencedora de um grupo conflitante é a mais antiga, a mais recente, ou
  outro critério — isso é decisão de produto de Rafael, caso a caso ou por política geral.
- Não decide se/quando `human_reviews_superseded` seria exposta em alguma auditoria da aplicação.
- Não executa nada — é uma proposta para aprovação.
