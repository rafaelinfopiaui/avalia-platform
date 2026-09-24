# Política de documentação

## 1. Princípios

- documentação descreve fatos, fontes, decisões e limites verificáveis;
- código e ambiente são fontes do estado técnico atual; relatórios antigos são fontes históricas;
- cada informação possui uma fonte canônica e é referenciada, não copiada integralmente;
- ausência de evidência é registrada como “não verificado” ou “não medido”;
- datas usam ISO 8601 e fuso quando houver horário;
- documentos de governança são escritos em português do Brasil; identificadores e nomes técnicos existentes são preservados.

## 2. Precedência

Em conflito:

1. manifestação explícita e atual de Rafael sobre prioridade/homologação;
2. requisitos/PRD e decisões aceitas aplicáveis;
3. políticas em `docs/governance/`;
4. sprint ativa aprovada;
5. código, Git e execução real para estado técnico;
6. snapshot/baseline validado;
7. relatórios e roteiros históricos.

Conflitos não são silenciosamente resolvidos: registrar decisão pendente ou correção necessária.

## 3. Fontes canônicas e atualização

- sprint: objetivo, backlog, mapa de impacto, ajustes e resultado do gate;
- snapshot: fato histórico de uma execução;
- dashboard: visão executiva derivada, com links;
- registros: inventário atual de débitos, bloqueantes e decisões;
- ADR: decisão arquitetural e consequências;
- requisitos/PRD: necessidade de produto e escopo;
- README: porta de entrada e operação consolidada, não relatório de sprint.

## 4. Snapshot histórico

Após encerrado, o snapshot é preservado. Correção factual usa:

- adendo datado no próprio arquivo, sem apagar o texto original, quando a correção precisa acompanhar aquele registro; ou
- novo snapshot referenciando o anterior, quando representa nova verificação/execução.

Nunca reescrever um resultado antigo para parecer que foi validado depois. A origem e a data de cada evidência permanecem visíveis.

## 5. Atualizações obrigatórias no fechamento

| Artefato | Regra |
|---|---|
| sprint | sempre atualizar estado, itens, ajustes e gate |
| snapshot | sempre criar por execução/fatia |
| dashboard | sempre atualizar última execução, sprint e impactos |
| registros | atualizar se débito, bloqueante ou decisão mudou |
| README | revisar; alterar somente se entrada/capacidade/operação mudou |
| requisitos/PRD | revisar; alterar quando escopo, requisito ou estado formal mudou |
| roadmap/backlog | revisar; alterar quando prioridade ou composição mudou |

Quando não houver alteração, o fechamento registra “revisado; sem alteração necessária”.

## 6. Métricas

Percentual só pode ser publicado com:

- escopo e universo definidos;
- numerador e denominador explícitos;
- data/ambiente de coleta;
- exclusões e falhas visíveis.

Indicador sem medição aparece como “não medido”. Score de maturidade só pode existir após uma rubrica própria do AvalIA, aprovada e versionada; até lá, não atribuir nota.

## 7. Links e caminhos

Usar links relativos em documentos versionados. Caminhos absolutos podem aparecer apenas como evidência de ambiente em snapshot, não como instrução portátil. Referências a projetos institucionais externos devem ser marcadas como fontes somente leitura e não como dependências do AvalIA.

## 8. Revisão e homologação

Autoria, revisão, verificação e homologação são campos distintos. Uma caixa marcada ou um texto produzido pelo executor não cria aprovação de Rafael. Documentos preparados para revisão usam estado `aguardando_homologacao` ou equivalente.
