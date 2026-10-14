# Auditoria pontual — Codex CLI (codex exec --sandbox read-only)

Papel: auditoria pontual (não revisão geral), foco exclusivo: "a flag de
capacidade não substitui autorização; ausência/falha de configuração não
pode habilitar funcionalidade indevidamente."

Resultado completo: ver log do processo `proc_5fff893678f3` (Hermes).

## Veredito inicial: RISCO CONFIRMADO

Achado 1 (BLOQUEANTE, CORRIGIDO nesta sessão): AssessmentEditorPage.tsx
tratava o estado "carregando" de capabilities (loading=true, valor
normalizado para false) de forma IDÊNTICA a "confirmadamente desligado" —
chamava listClassGroups() imediatamente e permitia salvar/publicar sem
turma durante a janela de carregamento, mesmo quando a capacidade real
(após resolver) seria "ligado". O backend protegia corretamente (422), mas
a UI não era fail-closed de verdade nessa janela. Correção aplicada por
Claude Code nesta sessão: desestruturado também `loading` do contexto,
formulário desabilitado/spinner enquanto capabilitiesLoading.

Achado 2 (NÃO BLOQUEANTE): normalização do booleano do contexto é estrita
(=== true), sem fallback para true em nenhum caminho de erro/tipo errado.
Sem timeout explícito em request() — uma chamada pendente indefinidamente
mantém loading=true (fail-closed, mas pode deixar spinner permanente;
registrado como observação, não bloqueante).

Achado 3 (NÃO BLOQUEANTE): endpoint /v1/config/capabilities é puramente
informativo, não concede acesso/token/sessão.

Achado 4 (NÃO BLOQUEANTE): autorização real (vínculo, propriedade, role)
é inteiramente independente da flag academic_module_enabled —
confirmado por diff vazio em core/app/routers/academic.py.

Achado 5 (BLOQUEANTE classificado pelo Codex, mas = comportamento
INTENCIONAL pré-existente, não um bug desta sprint): POST /v1/assessments
aceita avaliação sem turma quando a flag é false, mas exige quando true —
isso é o comportamento desenhado por DEC-AV-023 (módulo desligado = fluxo
legado permissivo por design, não uma falha de segurança). O Codex
classificou isso como "mais permissivo com falha de configuração" tomado
literalmente, mas é o comportamento correto e aprovado: ausência de
configuração explícita = modo legado (pré-existente ao módulo acadêmico),
não uma elevação de privilégio. Registrado aqui para rastreabilidade; não
tratado como bug.

Testes: `pytest app/tests -q` sob sandbox read-only falhou por
`FileNotFoundError: No usable temporary directory found` (ambiente do
Codex não tem tmpdir gravável) — limitação do sandbox, não do código.
Com `-s` (sem captura): 17 passed, 91 errors (mesma causa). Suíte
completa não foi validada pelo Codex nesta rodada; validada de forma
independente pelo Hermes e pelo Antigravity (108 passed em ambos).
