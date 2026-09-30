# Comparação da proposta local de saneamento (676 linhas)

Data da comparação: 2026-09-30 (-03:00)

## Estado e autoridade

A cópia local de 676 linhas encontrada no checkout principal é uma **proposta não
aprovada**. Este registro não homologa o plano, não autoriza saneamento operacional e
não substitui automaticamente a versão integrada.

- checkout local preservado: `/Users/rafaeloliveira/Projeto Estágio/avalia-plataform`;
- branch do checkout: `docs/av-s02-encerramento-planos-operacionais`;
- HEAD observado: `7f18ec3`;
- arquivo local: `docs/governance/backlog/proposta_saneamento_human_reviews_duplicadas.md`;
- extensão local observada: 676 linhas;
- versão integrada comparada: `main@a5974b1`, 359 linhas;
- delta integral e reversível: `diff_proposta_saneamento_676_vs_integrada.txt` (603 linhas).

A cópia original continua somente local e não foi sobrescrita. O delta publicado permite
reconstruir e revisar as diferenças sem apresentar a versão longa como plano aceito.

## Diferenças materiais que exigem revisão humana

1. **Inventário de auditoria ampliado:** a versão local acrescenta `before_json` e
   `after_json` aos três eventos de aprovação. É preciso confirmar os valores contra a
   fonte operacional antes de tratá-los como evidência.
2. **Semântica de preservação:** explicita que duas linhas seriam copiadas para arquivo e
   depois removidas da tabela ativa dentro da mesma transação; corrige a formulação antiga
   “nenhuma linha é apagada”. Exige decisão explícita sobre a política de retenção.
3. **Concorrência entre saneamento e migração:** explicita que o `LOCK TABLE` termina no
   `COMMIT` e que a proteção no intervalo até a migração depende de writers parados.
4. **Modo de execução psql:** propõe `ON_ERROR_STOP=1` e proíbe
   `--single-transaction` por haver transação/`COMMIT` explícitos no script. Precisa de
   revisão operacional antes de qualquer uso.
5. **DDL defensivo:** inclui criação condicional e validação extensa do schema de
   `human_reviews_superseded`, incluindo colunas, tipos, nulabilidade, default, PK e índice.
6. **Assertions executáveis:** transforma verificações narrativas em blocos SQL que
   abortam em divergência de IDs, equivalência, cópia integral, remoção e pós-checks.
7. **Verificação integral antes do DELETE:** compara todas as colunas copiadas com o
   original ainda ativo antes de remover duas linhas.
8. **Pós-checks e rollback compensatório:** amplia verificações da linha vencedora,
   arquivo, eventos de auditoria e recuperação após falha da migração.
9. **Separação da verificação HTTP:** posiciona a chamada real ao endpoint de contexto
   após `COMMIT` e migração, em vez de sugerir que ocorre dentro da transação SQL.

## Pendências antes de eventual incorporação

- revisão SQL independente dos blocos `DO $$`, comparações e assertions;
- validação em banco restaurado isolado, nunca diretamente em `avalia_dev`;
- confirmação dos valores de auditoria e dos IDs nominais contra uma fonte autorizada;
- decisão de Rafael sobre retenção e remoção das duas linhas da tabela ativa;
- definição da janela operacional e dos writers que devem permanecer parados;
- revisão do rollback compensatório e da interação com a migração `7b1d6d853f20`;
- somente depois disso, proposta de branch/PR própria para o plano operacional.

Nenhuma dessas pendências foi executada nesta publicação. Não houve acesso ou alteração em
`avalia_dev`, saneamento, deploy ou promoção de baseline.
