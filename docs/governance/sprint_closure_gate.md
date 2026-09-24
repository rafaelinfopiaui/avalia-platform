# Gate de encerramento de sprint

## 1. Objetivo

Avaliar o estado real de uma sprint sem transformar pendências em sucesso documental.

## 2. Níveis

- **CRÍTICO:** falha impede `concluída` ou `concluída com débitos`, salvo exceção explícita de Rafael registrada com risco.
- **IMPORTANTE:** falha exige débito, justificativa e próxima ação.
- **CONDICIONAL:** aplica-se apenas se a sprint impactou a área indicada.

## 3. Gate

### A. Escopo e produto

| ID | Nível | Critério |
|---|---|---|
| A1 | CRÍTICO | objetivo e critérios de aceite avaliados item a item |
| A2 | CRÍTICO | mudanças vinculadas ao backlog e ao mapa de impacto; desvios registrados antes ou como incidente de processo |
| A3 | CRÍTICO | planejado, implementado, validado e homologado não foram confundidos |
| A4 | IMPORTANTE | não entregas, riscos, débitos e bloqueantes registrados com IDs |
| A5 | CONDICIONAL | requisitos/PRD e roadmap atualizados quando capacidade, escopo ou prioridade mudou |

### B. Qualidade e evidência

| ID | Nível | Critério |
|---|---|---|
| B1 | CRÍTICO | validações previstas executadas ou marcadas honestamente como não executadas/falhas |
| B2 | CRÍTICO | evidências registram comando/procedimento, data/fuso, ambiente e resultado real |
| B3 | CRÍTICO | simulação, mock, inspeção, automação, integração real e teste visual estão diferenciados |
| B4 | CRÍTICO | nenhuma limitação, falha ou resultado histórico foi promovido a sucesso atual |
| B5 | CONDICIONAL | mudanças de código passaram pelos testes/lint/build aplicáveis definidos na sprint |
| B6 | CONDICIONAL | segurança, privacidade, migração, infraestrutura e operação foram verificadas quando impactadas |

### C. Documentação e estado do repositório

| ID | Nível | Critério |
|---|---|---|
| C1 | CRÍTICO | snapshot desta execução existe, mesmo para estado parcial/reprovado |
| C2 | CRÍTICO | sprint, dashboard e registros canônicos refletem o mesmo estado |
| C3 | CRÍTICO | working tree final e alterações preexistentes estão registrados |
| C4 | IMPORTANTE | README revisado e atualizado ou marcado “sem alteração necessária” |
| C5 | IMPORTANTE | links locais e referências documentais foram verificados |
| C6 | CRÍTICO | última execução e último baseline validado permanecem separados |

### D. Autoridade

| ID | Nível | Critério |
|---|---|---|
| D1 | CRÍTICO | delegação e revisão independente só aparecem se ocorreram |
| D2 | CRÍTICO | nenhuma decisão/homologação foi atribuída a Rafael sem manifestação explícita |
| D3 | CONDICIONAL | exceções críticas identificam decisão, data, risco e alcance |
| D4 | CRÍTICO | commit, push, tag, deploy ou ação remota respeitou autorização específica; “não aplicável” quando não ocorreu |

## 4. Resultado

Classificar como:

- **concluída**;
- **concluída com débitos**;
- **parcial**;
- **reprovada**;
- **bloqueada**.

A justificativa aponta critérios falhos e evidências. Não marcar todos os itens como concluídos por conveniência.

## 5. Pós-gate

1. preencher o fechamento;
2. gerar snapshot;
3. atualizar dashboard e registros;
4. revisar README, requisitos/PRD e roadmap;
5. atualizar `latest_execution.md`;
6. promover `latest_validated_baseline.md` apenas com decisão explícita aplicável;
7. apresentar decisões pendentes a Rafael.
