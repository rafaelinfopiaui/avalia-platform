# Tarefa: revisão independente — DEBT-AV-014 (retomada de respostas por imagem)

Repo: /Users/rafaeloliveira/Projeto Estágio/avalia-plataform
Branch atual (NÃO mude, NÃO crie outra, NÃO faça checkout de main): feat/av-s06b-debt-014-retomada-respostas-imagem
Base: main cf81109655713fac856aab0b26ba36e1bb5f15bc

Você é o revisor INDEPENDENTE desta fatia. Claude Code implementou; Hermes já fez
uma rodada própria de verificação (ver docs/governance/evidence/AV-S06B/verificacao_debt_014_hermes.md).
NÃO reaproveite as afirmações de Claude Code nem do Hermes como fato — rode você
mesmo, do zero, em ambiente isolado seu.

PROIBIDO nesta tarefa: qualquer stage/commit/push/merge; tocar `avalia_dev` ou
`avalia_apresentacao_demo_20261002`; qualquer migração operacional; OCR; transcrição
manual ou automática; qualquer ativação operacional. Não altere código do produto —
você é revisor, não executor. Se encontrar um defeito, DESCREVA no parecer; não
corrija você mesmo.

## Insumos para ler antes de revisar
- docs/governance/evidence/AV-S06B/desenho_debt_014_retomada.md (desenho e ACD-01..10)
- docs/governance/evidence/AV-S06B/prompt_debt_014_claude_code.md (o que foi pedido ao Claude Code)
- docs/governance/evidence/AV-S06B/verificacao_debt_014_hermes.md (rodada do Hermes — para comparar, não para confiar)
- Diff real: `git diff cf81109655713fac856aab0b26ba36e1bb5f15bc -- core/app/main.py core/app/tests/test_image_answers_listing.py frontend/src/pages/ImageAnswerPage.tsx frontend/src/services/api.ts`

## O que fazer (execução própria, independente)
1. Suíte automatizada: `cd core && .venv/bin/python -m pytest app/tests -q` (espera-se
   171 passed) e `.venv/bin/ruff check --config ../ruff.toml app`. Frontend:
   `cd frontend && npm run build` (tsc+vite) e, se configurado, `npm run lint`.
2. Monte SEU PRÓPRIO ambiente isolado e descartável: banco PostgreSQL novo (nome
   próprio, ex. `av_s06b_debt014_rev_agy`), migrado via alembic à head, Core próprio
   (porta livre, `ACADEMIC_MODULE_ENABLED=false`, AI_ENGINE_URL morto/sem OCR), Vite
   próprio (porta livre). NÃO reutilize portas/bancos de outras rodadas.
3. HTTP real contra seu ambiente, cobrindo ACD-01..05 do desenho (lista IMAGE com
   estado+imagens; filtro por question_id e 404; 401/403/200; storage_filename nunca
   exposto; e **ACD-04 leitura histórica**: crie uma avaliação com `class_group_id` e
   ZERO `ProfessorClassLink` do dono — confirme que o dono ainda recebe 200, sem
   exigir vínculo ativo).
4. Navegador real (Chromium via CDP, como você já fez nas rodadas anteriores desta
   sprint) cobrindo, especificamente, os 5 pontos que Rafael pediu para comprovar:
   a. retomada após RELOAD (F5) da tela de resposta por foto, com respostas
      semeadas/persistidas antes do reload (não enviadas pela UI na sua sessão);
   b. retomada em NOVA SESSÃO (login novo) — mesmas respostas persistidas aparecem;
   c. bloqueio para outro professor (não-dono) — 403, sem conseguir ver nem sondar;
   d. troca de avaliação/questão SEM reter dados/imagens da seleção anterior;
   e. correção ainda bloqueada sem transcrição confirmada — nenhuma ação de
      correção/nota/IA disponível na tela de resposta por foto; backend mantém 422
      ANSWER_NOT_TRANSCRIBED para resposta IMAGE não transcrita.
5. Confirme a integridade dos bancos protegidos ANTES e DEPOIS da sua rodada
   (`avalia_dev` e a apresentação) — não devem mudar.
6. Ao final, derrube seu ambiente (Core, Vite, Chromium) e dropee seu banco de teste.

## Entregável
Escreva o parecer em:
docs/governance/evidence/AV-S06B/revisao_debt_014_antigravity.md

Siga o formato já usado em revisao_implementacao_antigravity.md desta mesma pasta
(cabeçalho com data/revisor/branch/commit base/artefatos revisados/metodologia,
depois "## 1. Veredito" com APROVADO / APROVADO COM RESSALVAS / REPROVADO em
destaque, depois a execução independente com comandos e resultados reais, depois
avaliação crítica por requisito com evidência arquivo:linha, depois ressalvas se
houver). Seja crítico e específico — se algo não comprovar, diga isso claramente,
não suavize.

Quando terminar, imprima no stdout apenas uma linha final no formato:
VEREDITO_ANTIGRAVITY: <APROVADO|APROVADO_COM_RESSALVAS|REPROVADO> — <resumo de 1 linha>
