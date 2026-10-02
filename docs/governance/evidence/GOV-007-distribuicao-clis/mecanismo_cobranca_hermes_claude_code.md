# Mecanismo de cobrança: Hermes (provider anthropic) vs. CLI `claude` — o que está comprovado e o que não está

Documento de configuração (GOV-007 — distribuição de trabalho entre CLIs de IA). Não é snapshot de execução funcional do AvalIA; é evidência de configuração do ambiente do agente orquestrador.

Gerado em: 2026-10-02T14:50:00-03:00
Autor: Hermes (consolidação), a pedido de Rafael.

## 1. Pergunta que este documento responde

Quando o Hermes usa `model.provider: anthropic` (OAuth, credencial rotulada `claude_code` em `hermes auth list`), o consumo cai sobre:
(a) a cota base incluída na assinatura Claude Max/Pro; ou
(b) apenas créditos de "extra usage" (overage, cobrados à parte)?

**Resposta honesta: não está comprovado para esta instalação/versão, e a própria documentação da Nous está sob disputa ativa e não resolvida nos repositórios oficiais do Hermes.** Não habilitei nenhum mecanismo de cobrança para obter essa comprovação — a lacuna permanece registrada como lacuna.

## 2. Fontes da Nous (documentação de integração do Hermes)

**Fonte 1 — página de providers do Hermes (texto vigente, apresentado como aviso):**
URL: https://hermes-agent.nousresearch.com/docs/integrations/providers

> "Anthropic — Claude Max + OAuth ... Requires Max **and** purchased extra usage credits | The **extra/overage credits** you've added on top of the Max plan | The **base Max plan allowance** (the usage included in Claude Code by default) | All Hermes usage bills as 'extra usage' even while your included Max allowance sits untouched"

> ":::caution Requires Claude Max 'extra usage' credits — When you authenticate via `hermes model` → Anthropic OAuth ... Hermes routes as Claude Code against your Anthropic account. **It only works if you're on a Claude Max plan and have purchased extra usage credits.** ... Claude Pro subscribers cannot use this path."

Este é o texto que citei na resposta anterior como "mecanismo confirmado". Nesta rodada, aprofundando a verificação, encontrei que esse próprio texto está contestado nos repositórios oficiais da Nous (ver Fonte 2 e 3) — portanto não deveria ter sido apresentado como fato assentado sem essa ressalva.

**Fonte 2 — issue aberta, não resolvida, no repositório oficial `NousResearch/hermes-agent`:**
URL: https://github.com/NousResearch/hermes-agent/issues/72171
Título: "Anthropic OAuth: system-prompt shape routes subscription requests into the metered 'extra usage' lane (root cause + bisection for #65564)"
Estado: **open** (não fechada), labels: `type/bug`, `provider/anthropic`, `area/billing`, `needs-decision`.

Trecho literal do corpo da issue:

> "`website/docs/integrations/providers.md:112-115` currently states that Anthropic OAuth requires Max extra-usage credits rather than consuming the included allowance. Based on the bisection above, **that describes the symptom of this bug, not an Anthropic policy**: with a Claude-Code-shaped payload, the identical account bills against the included allowance. If this diagnosis is accepted, that section should be corrected — otherwise the documentation cements the bug as intended behavior."

Ou seja: há uma alegação técnica (não aceita/fechada formalmente pelos mantenedores até a data desta consulta) de que o comportamento "cai em extra usage" é um **bug de formato de payload** do Hermes, não uma regra da Anthropic — e que, corrigindo o formato da requisição para se parecer exatamente com o da CLI `claude` oficial, a mesma conta passaria a consumir a cota incluída normalmente.

**Fonte 3 — segunda issue, também aberta, não resolvida:**
URL: https://github.com/NousResearch/hermes-agent/issues/47260
Título: "Anthropic Claude Code OAuth still appears to consume extra usage credits after June 16 policy rollback email"
Estado: **open**, labels: `type/bug`, `area/billing`, `area/auth`, `needs-decision`.

Trecho literal do corpo da issue (citando um e-mail da própria Anthropic aos usuários, datado de 16 de junho):

> "Nothing changes for now. Agent SDK, `claude -p`, and third-party app usage continues to work with your subscription exactly as it did before today, and there's no credit to claim. Your subscription limits are unchanged."
>
> "However, when using Hermes with the Anthropic / Claude Code OAuth route, usage still appears to be charged against extra usage credits rather than the normal Claude subscription allowance."

**Leitura dessas três fontes em conjunto:** a documentação oficial da Nous (Fonte 1) ainda publica o aviso de "requer extra usage", mas duas issues abertas no mesmo repositório (Fontes 2 e 3) argumentam, com evidência técnica própria, que isso é um bug específico do Hermes (formato de requisição), não uma política permanente da Anthropic — e citam a própria Anthropic dizendo que não deveria haver essa cobrança adicional para uso de Agent SDK / `claude -p` / apps de terceiros. **Nenhuma das duas issues foi fechada como resolvida.** Portanto, não é seguro afirmar nem "confirmado que cobra extra usage" nem "confirmado que NÃO cobra extra usage" para a versão instalada (Hermes Agent v0.20.6).

### 2.1 O que a instalação local efetivamente contém

Inspecionei o código-fonte local (`~/.hermes/hermes-agent/agent/anthropic_adapter.py`) e confirmei que esta instalação **já contém** o workaround mencionado na issue 72171: há uma constante `_CLAUDE_CODE_SYSTEM_PREFIX = "You are Claude Code, Anthropic's official CLI for Claude."` injetada no prompt de sistema, mais sanitização de nomes de produto (`Hermes Agent` → `Claude Code`, `Nous Research` → `Anthropic`) e normalização de nomes de ferramenta (`mcp_` → `mcp__`) — ou seja, o Hermes já tenta fazer a requisição "parecer" com uma da CLI oficial para fins de classificação de cobrança. Não tenho evidência própria (nem gerada nesta sessão, nem documentada de forma conclusiva nas issues) de que esse workaround elimina completamente a classificação como "extra usage" nesta versão — as duas issues continuam abertas, o que sugere que o problema (ou parte dele) persiste mesmo com esse workaround presente no código.

## 3. Fontes da Anthropic (oficiais, sobre Claude Code/Max/cobrança)

**Fonte 4 — Anthropic Help Center, uso de Claude Code com plano Pro/Max:**
URL: https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan

Trecho literal:

> "Important: If you have an `ANTHROPIC_API_KEY` environment variable set on your system, Claude Code will use this API key for authentication instead of your Claude subscription (Pro, Max, Team, or Enterprise plans), resulting in API usage charges rather than using your subscription's included usage."

> "Both Pro and Max plans offer usage limits that are shared across Claude and Claude Code, meaning all activity in both tools counts against the same usage limits."

> "If you want to use API credits through Claude Code: Usage will be billed at standard API rates (distinct from Pro/Max Plan pricing)."

> "- Run `claude logout` in your terminal. - Run `claude login` and authenticate using only your Pro or Max plan credentials. - Avoid adding any Claude Console credentials during the login process. This ensures Claude Code will only use your plan allocation and you won't be prompted to use API credits when you reach your limits."

**Fonte 5 — Claude Code Docs, gestão de custos:**
URL: https://code.claude.com/docs/en/costs

Trecho literal:

> "Claude Max and Pro subscribers have usage included in their subscription, so the session cost figure isn't relevant for billing purposes."

> "Usage credits let you keep working past your plan's usage limit. ... run `/usage-credits` after signing in with your claude.ai subscription through `/login`"

**Fonte 6 — Anthropic Help Center, o que é o plano Max:**
URL: https://support.claude.com/en/articles/11049741-what-is-the-max-plan

Trecho literal:

> "Access to Claude Code: Use Claude Code for your terminal-based coding workflows with one unified subscription."

**Síntese das fontes da Anthropic:** a CLI `claude` oficial, autenticada por login de assinatura (não API key), consome a cota incluída do Pro/Max por padrão; só migra para cobrança adicional ("usage credits"/API) se (a) `ANTHROPIC_API_KEY` estiver definida no ambiente, ou (b) o usuário aceitar explicitamente continuar via créditos de uso após esgotar a cota da sessão/semana. **Essas fontes descrevem o comportamento da CLI `claude` oficial, não o do provider `anthropic` do Hermes** — são integrações diferentes (ver seção 4).

## 4. Por que as duas fontes não respondem à mesma pergunta

- As fontes da Anthropic (4, 5, 6) descrevem o comportamento quando você usa a **CLI `claude` oficial** (`claude -p`, `claude` interativo) autenticada via `claude login`/`claude auth login` com credenciais de assinatura.
- As fontes da Nous (1, 2, 3) descrevem o comportamento quando o **Hermes** se autentica via `hermes model` → Anthropic OAuth e faz chamadas diretas à API da Anthropic (`api.anthropic.com`) usando esse token — isto é, o Hermes está se passando por um cliente OAuth de assinatura, mas não é literalmente o binário `claude`.
- Mesmo a Anthropic dizendo "Agent SDK, `claude -p` e apps de terceiros usam a cota da assinatura normalmente" (citado dentro da issue 47260), há relatos abertos e não resolvidos de que, na prática, requisições do Hermes especificamente caem no balde de "extra usage". Não há fechamento dessas issues confirmando correção, nem uma declaração oficial da Anthropic especificamente sobre o Hermes.

## 5. Conclusão operacional desta configuração

- **Não habilitei `model.provider: anthropic` com OAuth do Hermes nesta sessão.** O provider principal do Hermes já estava configurado assim antes desta tarefa (`model: {default: claude-sonnet-5, provider: anthropic}`) — não é uma mudança feita por mim, e não ativei extra usage nem qualquer outro mecanismo de cobrança.
- **Não afirmo mais, como fato confirmado, que "o OAuth do Hermes usa somente extra usage".** Isso corrige a imprecisão da minha resposta anterior. O estado correto é: "a documentação oficial da Nous publica esse aviso, mas duas issues abertas no mesmo projeto contestam tecnicamente que seja esse o comportamento real, sem resolução até a data desta consulta; não testei este caminho especificamente para gerar evidência própria, porque isso envolveria gastar uso real contra sua conta sem necessidade para o pedido de configuração."
- **A forma de priorizar o consumo garantido pela assinatura Max continua sendo a CLI `claude` oficial** (login próprio via `claude auth login`, uso via `claude -p`/interativo), que é o caminho coberto com clareza pelas fontes 4-6 da Anthropic, e que é exatamente o mecanismo de delegação de tarefa descrito em `AGENTS.md` (seção "Claude Code — executor principal"). Isso não depende de resolver a ambiguidade do provider `anthropic` do Hermes.
- Se, no futuro, Rafael quiser investigar ativamente se o workaround já presente nesta instalação elimina ou não a cobrança de extra usage no provider `anthropic` do Hermes, isso exigiria um teste controlado contra a conta real (ex.: checar `/usage-credits` antes/depois de uma chamada mínima via `hermes model`) — não foi feito aqui por não ser necessário para esta tarefa de configuração, e por envolver risco de cobrança real sem autorização prévia específica para esse teste.

## 6. Pendência de autenticação da CLI `claude` (achado desta rodada)

Rafael reportou ter concluído o login da CLI `claude`. Testes realizados nesta rodada (ver snapshot EXEC-2026-10-02-02):

- `claude auth status --text` → ainda retorna "Login: Expired — log in again" / "Not logged in."
- `claude -p "Responda apenas: OK" --output-format json` → `Failed to authenticate: OAuth session expired and could not be refreshed`.
- O arquivo lido por essa CLI, `~/.claude/.credentials.json`, tem `mtime` = `2026-10-02 13:21:43`, **idêntico** ao valor já observado antes do pedido de login de Rafael — ou seja, o arquivo não foi reescrito por nenhum login novo até o momento desta consulta.
- Encontrado um binário `claude` adicional no sistema, de versão diferente (2.1.284, mais recente que a 2.1.260 do PATH), pertencente à extensão do Antigravity IDE (`~/.antigravity-ide/extensions/anthropic.claude-code-2.1.284-darwin-arm64/resources/native-binary/claude`), com processos ativos rodando sob esse binário. É possível que o login relatado por Rafael tenha sido feito nesse binário embutido no Antigravity IDE (que pode ter seu próprio `CLAUDE_CONFIG_DIR`/keychain), e não na CLI `claude` standalone do PATH que o Hermes invocaria para delegação de tarefas.

Esta é uma pendência técnica real, não apenas "aguardar login" — precisa de esclarecimento de qual `claude` Rafael autenticou.
