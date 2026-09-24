# Política de gestão de sprints

## 1. Propósito

Garantir que a evolução funcional e técnica do AvalIA ocorra com plano aprovado, escopo rastreável, evidência real e fechamento honesto.

## 2. Regra de início

Nenhuma sprint funcional começa sem:

1. documento de sprint preenchido;
2. itens atendendo à [Definition of Ready](definition_of_ready.md), ou exceções explicitamente decididas;
3. mapa de impacto e validações previstas;
4. aprovação explícita de Rafael sobre o plano e o escopo.

A aprovação da política GOV-001 não aprova a próxima sprint funcional. Planejamento, implementação e homologação são decisões separadas.

## 3. Conteúdo obrigatório

Toda sprint deve registrar:

- identificador, status, período ou janela estimada e responsável pela consolidação;
- objetivo e valor esperado;
- requisitos/fontes de origem, sem inventar requisitos ausentes;
- baseline de entrada e última execução relevante;
- backlog com IDs, responsáveis e estado;
- escopo incluído e excluído;
- dependências e bloqueantes;
- mapa de impacto por arquivo/componente;
- avaliação DoR de cada item;
- critérios de aceite verificáveis;
- Definition of Done da sprint;
- validações previstas e ambientes necessários;
- riscos e mitigação;
- critérios de encerramento e tratamento de exceções;
- estimativas identificadas como estimativas e método usado.

## 4. Estados de item

`proposto` → `refinado` → `ready` → `em execução` → `implementado` → `validado` → `homologado`.

Também são permitidos `bloqueado`, `parcial`, `não entregue` e `cancelado`. Estados posteriores não são inferidos: implementado não significa validado; validado não significa homologado.

## 5. Estados de sprint

- **planejada:** documento existente, sem aprovação para execução;
- **aprovada:** Rafael autorizou o plano;
- **em execução:** ao menos um item autorizado iniciado;
- **concluída:** objetivo, critérios críticos e DoD atendidos, sem débito que altere a conclusão;
- **concluída com débitos:** objetivo e critérios críticos atendidos; débitos residuais estão registrados e aceitos;
- **parcial:** parte do escopo entregue, sem satisfação do objetivo integral;
- **reprovada:** critério crítico falhou ou evidência é insuficiente;
- **bloqueada:** impedimento impede avanço relevante;
- **cancelada:** Rafael encerrou o trabalho sem conclusão.

## 6. Mudança de escopo

Antes da mudança:

1. registrar item, motivo, impacto, risco e arquivos adicionais;
2. indicar o que será removido, adiado ou reestimado;
3. obter decisão de Rafael quando houver ampliação relevante, alteração de requisito, risco crítico ou impacto operacional.

Correção necessária para preservar um critério existente pode ser proposta pelo executor, mas deve ser registrada; não autoriza expansão funcional silenciosa.

## 7. Execução e rastreabilidade

- cada arquivo alterado deve corresponder ao mapa de impacto e a pelo menos um item;
- cada critério de aceite deve apontar para evidência ou para “não validado”;
- decisões, débitos e bloqueantes usam os registros canônicos;
- uma única pessoa/agente consolida sprint, snapshot e dashboard;
- trabalho delegado segue a [política de execução](execution_policy.md).

## 8. Encerramento

Aplicar o [closure gate](sprint_closure_gate.md), preencher o template de fechamento, atualizar o documento da sprint, gerar snapshot obrigatório e atualizar o dashboard. README, requisitos/PRD e roadmap são revisados; quando não precisarem mudar, registrar isso no fechamento.

Critério crítico não atendido impede conclusão automática. Exceção só existe com decisão explícita e registrada de Rafael, sem apagar a falha ou reclassificar evidência.

## 9. Histórico herdado

O desenvolvimento anterior a esta política não será convertido retroativamente em sprints. Ele permanece descrito no baseline herdado e em documentos históricos com suas datas, autores e limitações originais.
