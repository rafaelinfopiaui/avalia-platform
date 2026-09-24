# Instruções para agentes no AvalIA

## Governança obrigatória

Antes de planejar ou modificar o AvalIA, leia:

1. `docs/governance/README.md`;
2. `docs/governance/execution_policy.md`;
3. `docs/governance/snapshots/latest_validated_baseline.md`;
4. `docs/governance/snapshots/latest_execution.md`;
5. a sprint ativa, se houver;
6. `docs/governance/sprint_management_policy.md`, `definition_of_ready.md` e `sprint_closure_gate.md` quando o trabalho fizer parte de sprint.

Confirme o estado real do Git e não use relatório antigo como prova atual.

## Autoridade e limites

- Rafael prioriza e homologa; nenhuma aprovação é presumida.
- Hermes conduz o rito e consolida as evidências.
- Agente delegado atua apenas no objetivo, arquivos/escopo, critérios de aceite e limites recebidos.
- Não declare delegação, revisão independente, validação ou homologação que não ocorreu.
- Mudança de escopo relevante volta à decisão de Rafael.
- Não executar commit, push, tag, deploy ou ação remota sem autorização específica.
- Preservar alterações locais preexistentes e nunca ler/expor segredos.

## Registros obrigatórios

Vincule mudanças a itens da sprint; diferencie planejado, implementado, validado e homologado. Registre comando/procedimento, data/fuso, ambiente, tipo e resultado real. Gere snapshot ao encerrar toda sessão/fatia, inclusive parcial, falha ou interrompida, e atualize o dashboard.
