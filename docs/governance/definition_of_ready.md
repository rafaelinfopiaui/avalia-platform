# Definition of Ready (DoR)

## 1. Objetivo

Definir a qualidade mínima de entrada de um item antes de sua inclusão em uma sprint funcional do AvalIA.

## 2. Critérios por item

Um item está `ready` somente quando possui:

- [ ] ID estável e título objetivo;
- [ ] problema/necessidade e incremento esperado descritos sem ambiguidade relevante;
- [ ] requisito, decisão, incidente ou evidência de origem identificada;
- [ ] escopo incluído e fora de escopo;
- [ ] critérios de aceite observáveis;
- [ ] responsável por execução e responsável por validação, sem simular independência;
- [ ] dependências e bloqueantes conhecidos;
- [ ] mapa de impacto inicial por componente/arquivo;
- [ ] riscos, incluindo segurança, privacidade, dados educacionais e regressão;
- [ ] validações previstas, ambiente e tipo de evidência;
- [ ] estimativa identificada como estimativa, quando necessária para priorização;
- [ ] nenhuma decisão crítica pendente que torne a implementação especulativa.

## 3. Prontidão da sprint

Além dos itens, a sprint precisa de:

- baseline de entrada identificado;
- objetivo único e critério de encerramento;
- capacidade/ordem de execução compatível com dependências;
- plano de consolidação documental;
- autorização explícita de Rafael.

## 4. Exceções

Item não pronto permanece `proposto` ou `refinado`. Se Rafael decidir incluir uma exceção, o documento da sprint registra critério ausente, motivo, risco aceito, responsável pela decisão e condição para saneamento. A exceção não altera o estado factual do critério.

## 5. Evidência e métricas

Não adotar metas numéricas por herança de outro projeto. Cobertura, latência, precisão, volume ou prazo só viram critérios quando sua origem, denominador, ambiente e método estiverem definidos para o AvalIA. Caso contrário, registrar “não medido”.
