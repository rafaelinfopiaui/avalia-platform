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

## Distribuição de trabalho entre CLIs de IA (Claude Code, Antigravity, Codex)

Instituído em 2026-10-02, a pedido de Rafael, para priorizar a assinatura
Claude Code Max e reduzir o consumo de Codex. Esta regra é de orquestração de
tarefas (qual CLI executa o quê), não de inferência do próprio Hermes — ver
decisão separada sobre o orquestrador abaixo.

### Claude Code — executor principal

- Usar prioritariamente para implementação, testes, correções, documentação
  e tarefas extensas, sempre dentro do escopo/autorização já concedidos pela
  governança (seção "Autoridade e limites" acima).
- Mecanismo de uso da assinatura Max: a delegação de tarefa é feita pela CLI
  `claude` oficial (não pelo provedor `anthropic` do próprio Hermes), via
  login de assinatura (`claude auth login`, sem `ANTHROPIC_API_KEY` no
  ambiente) e invocação `-p`/print para tarefas pontuais ou PTY+tmux para
  sessões multi-turno. Segundo a documentação oficial da Anthropic
  (support.claude.com/en/articles/11145838), esse caminho consome a cota
  incluída da assinatura Pro/Max por padrão, migrando para cobrança adicional
  só se uma API key estiver definida ou o usuário aceitar créditos de uso após
  esgotar a cota. **O mecanismo de cobrança do provider `anthropic` do
  próprio Hermes (usado como orquestrador, não como executor delegado) é uma
  questão separada, não comprovada para esta instalação/versão** — ver
  `docs/governance/evidence/GOV-007-distribuicao-clis/mecanismo_cobranca_hermes_claude_code.md`
  para fontes e limitações. Esta distinção não compromete a priorização de
  Claude Code como executor: a delegação de tarefa usa a CLI `claude`
  diretamente, não o provider do orquestrador.
- Login/auth da CLI `claude` são geridos pelo próprio Rafael via
  `claude auth login` (fluxo interativo). O Hermes não extrai nem reutiliza
  esse token para fins diferentes de invocar a CLI.
- Há mais de um binário `claude` nesta máquina (PATH: v2.1.260; embutido na
  extensão do Antigravity IDE: v2.1.284, com `CLAUDE_CONFIG_DIR`/keychain
  potencialmente distintos). Antes de declarar Claude Code disponível para
  delegação, confirmar `claude auth status --text` no binário do PATH
  especificamente — um login feito no binário do IDE não necessariamente
  autentica o binário que o Hermes invoca.
- **Pendência de 2026-10-02 RESOLVIDA em 2026-10-02 (mesma data, rodada
  seguinte):** `claude auth status --text` no binário do PATH
  (`/Users/rafaeloliveira/.local/bin/claude`, v2.1.260) agora retorna
  `Login method: Claude Max account`, sem "Expired"/"Not logged in". Chamada
  funcional mínima (`claude -p`) confirmou `is_error:false`,
  `subtype:success`. Claude Code está disponível para delegação de tarefas
  a partir desta data. Ver snapshot `snapshot_EXEC-2026-10-02-02_gov-007-distribuicao-clis.md`,
  §10 (adendo), para evidência completa.

### Antigravity CLI (`agy`) — segundo executor e revisor cruzado

- Papel: frontend/interface, testes e validação de fluxos, tarefas paralelas
  com arquivos e responsabilidades claramente separados das de outro agente,
  e revisão independente de entregas implementadas pelo Claude Code.
- Claude Code pode revisar entregas feitas pelo Antigravity. Nunca o mesmo
  agente que implementou é o único revisor da própria mudança.
- Capacidades comprovadas nesta máquina: CLI `agy` instalada, autenticação
  por keyring/OAuth do Google funcional, execução `-p`/print funcional.
  Não há navegador/ferramenta adicional comprovada para o Antigravity nesta
  configuração — não atribuir essa capacidade sem nova verificação.

### Codex — uso pontual, não executor padrão

- Reservado para: auditorias pontuais de segurança/autorização/migrações/
  concorrência, revisão de diffs críticos, e ajustes pequenos explicitamente
  atribuídos a ele.
- Não é revisor obrigatório de toda tarefa, nem executor padrão de trabalho
  extenso.
- Contexto enviado ao Codex deve ser reduzido: objetivo, critérios de
  aceite, diff pertinente, evidências e dúvidas concretas — não replicar a
  conversa inteira nem repetir testes sem motivo novo.
- Removido do fallback automático de provedor/modelo do Hermes
  (`~/.hermes/config.yaml`, chave `fallback_providers` removida em
  2026-10-02; Hermes não tinha roteamento nativo por tarefa/custo para
  diferenciar "fallback de inferência" de "delegação de tarefa" além dessa
  chave de nível de provedor — por isso a regra abaixo é aplicada aqui, como
  instrução de orquestração, e não como config nativa).

### Indisponibilidade e substituições

- Se o Claude Code ficar indisponível, a tarefa pode ser redistribuída
  explicitamente ao Antigravity somente quando: (a) a tarefa está dentro das
  capacidades comprovadas do Antigravity; (b) o escopo já estava autorizado
  para a tarefa original; (c) não há cobrança nova envolvida; (d) a
  substituição é registrada (sprint/snapshot) antes da execução.
- O modelo principal do Hermes (`anthropic`/`claude-sonnet-5`) nunca é trocado
  silenciosamente para Antigravity ou Codex como consequência dessa regra —
  fallback de inferência do orquestrador é decisão separada, tratada em
  `~/.hermes/config.yaml`, não aqui.
- Se Claude Code e Antigravity estiverem ambos indisponíveis, preservar o
  trabalho já feito, registrar o bloqueio no snapshot/sprint e informar
  Rafael. Não usar Codex automaticamente como substituto de última instância.

### Identificação correta de quem executou

- Registrar nas evidências/snapshots a ferramenta, o provedor e o modelo
  realmente usados em cada tarefa.
- Um subagente genérico do Hermes (`delegate_task`) não deve ser identificado
  como Claude Code, Antigravity ou Codex quando a CLI real não foi invocada —
  ver também a regra equivalente na skill
  `multi-agent-infra-orchestration` (seção "delegate_task não é o mesmo
  backend que uma CLI nomeada").
