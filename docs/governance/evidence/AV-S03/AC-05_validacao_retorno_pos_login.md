# Validacao AC-05 — retorno ao destino apos login (rota /academico)

Data: 2026-09-29
Decisao base: reconciliacao pre-merge solicitada por Rafael antes do encerramento
documental da AV-S03. Esta validacao NAO reusa evidencia do codigo perdido de
2026-09-24; toda a evidencia abaixo foi produzida nesta rodada, contra o codigo
da reconstrucao (branch `feat/av-s03-estrutura-academica`, ja integrada a `main`
via PR #3, merge commit `c391865`).

## 1. Requisito exato (AC-05, secao 9 do documento da sprint)

> AC-05 | usuário não autenticado recebe 401 e retorna ao destino após login
> quando aplicável | integração + visual

## 2. O que ja estava comprovado na implementacao reconstruida (antes desta rodada)

- `test_academic_routes_require_authentication` (suite automatizada,
  `core/app/tests/test_academic_authorization.py:237`), executado como parte
  da suite completa (68/68) em multiplas rodadas desta sprint, inclusive apos
  a integracao do PR #3: confirma que `GET /v1/class-groups` e
  `POST /v1/enrollments` retornam 401 sem token. Esta parte permanece
  comprovada e reconfirmada nesta rodada (secao 4 abaixo).
- O que **faltava**: a segunda metade do criterio — "retorna ao destino apos
  login quando aplicavel" — nunca foi verificada visualmente na reconstrucao.
  O registro anterior dizia explicitamente "retorno pos-login nao
  reverificado visualmente nesta rodada" (documento da sprint, linha AC-05,
  antes desta correcao).

## 3. Lacuna identificada e por que estava dentro do escopo ja autorizado

A lacuna era puramente de validacao visual de um fluxo ja implementado em
codigo (`frontend/src/App.tsx`, `SessionGuard`, e `frontend/src/pages/
LoginPage.tsx`), sem exigir nenhuma mudanca de escopo, arquitetura ou dado.
A implementacao usa `location.state.from` (React Router) para lembrar o
destino original e `navigate(location.state.from ?? '/avaliacoes')` apos
login bem-sucedido. Por ser validacao de comportamento ja implementado, em
ambiente local isolado, esta dentro do escopo ja autorizado por Rafael para
a AV-S03 (execucao local, PostgreSQL isolado, revisao/validacao visual).
Nao houve necessidade de nova decisao para executar esta validacao.

## 4. Ambiente de validacao (isolado, descartavel)

- PostgreSQL 16 dedicado, instancia isolada (`initdb` propria, porta 55440,
  socket em `/tmp/ac05_validacao`, fora de `avalia_dev` e de qualquer outro
  ambiente do projeto); banco `avalia_ac05_validacao`; schema aplicado via
  `alembic upgrade head` (mesma cadeia de migracoes da suite homologada);
  seed via `python -m app.seed` (professor de demonstracao fictício).
- Backend real (`uvicorn app.main:app`), no codigo da branch integrada, porta
  18100, `127.0.0.1` apenas.
- Frontend real (`vite`), no codigo da branch integrada, porta 5183,
  `127.0.0.1` apenas, apontando para o backend acima
  (`VITE_API_URL=http://127.0.0.1:18100/v1`).
- Navegador real: Chromium via Playwright (headless), instalado em venv
  descartavel dedicado a esta validacao (`/tmp/ac05_pw_venv`), nao reaproveitado
  de nenhuma sessao anterior.
- Todo o ambiente (Postgres, backend, frontend, venv do Playwright) foi
  encerrado e removido ao final desta validacao.

## 5. Execucao e resultado real

Script: `script_validacao_playwright.py` (preservado nesta pasta como
evidencia reexecutavel). Passos e resultados, extraidos de
`resultados_estruturados.json` (preservado nesta pasta):

| # | Passo | Resultado real |
|---|---|---|
| 1 | Navegar diretamente para `/academico` sem sessao autenticada | Redirecionado automaticamente para `/login` — confirmado por `page.url` |
| 2 | Inspecionar `window.history.state` apos o redirect | `{"usr": {"from": "/academico"}, ...}` — o destino original foi preservado no estado de navegacao |
| 3 | Preencher e submeter o formulario de login com credenciais reais do professor de demonstracao | login efetuado (screenshot `02_formulario_login_preenchido.png`) |
| 4 | Aguardar navegacao apos o clique em "Entrar" (`page.wait_for_url("**/academico")`, timeout 10s) | navegou para `/academico` dentro do timeout — confirmado |
| 5 | URL final apos login | `http://127.0.0.1:5183/academico` |

Confirmacao complementar via HTTP direto (reforca o automatizado ja existente
na suite, contra o backend real desta rodada, nao reaproveitado):
- `GET /v1/class-groups` sem token → `401`
- `POST /v1/enrollments` sem token → `401`

Evidencia visual (capturas desta rodada, preservadas nesta pasta):
- `01_redirect_para_login_nao_autenticado.png` — tela de login limpa, exibida
  automaticamente ao tentar acessar `/academico` sem sessao;
- `02_formulario_login_preenchido.png` — credenciais preenchidas antes do
  envio;
- `03_retorno_academico_pos_login.png` — apos o login, a tela mostra
  "Gestão Acadêmica" ativa na navegacao, titulo "Estrutura Acadêmica e
  Turmas", usuario autenticado (`professor.demo@avalia-platform.example`)
  visivel no cabecalho — confirma que o destino original (`/academico`) foi
  o efetivamente carregado, nao uma pagina padrao diferente.

## 6. Nota de transparencia sobre um falso alarme desta execucao

A primeira execucao do script (sem `wait_for_url` explicito, apenas
`networkidle` + `sleep`) reportou falha: apos o login, a URL permaneceu em
`/login`. Investigacao imediata do log do backend mostrou
`OPTIONS /v1/auth/login HTTP/1.1 400 Bad Request` — nao era defeito do
produto, era erro de configuracao desta validacao: `CORS_ORIGINS` do backend
isolado estava setado para `http://localhost:5183`, enquanto o frontend
rodava em `http://127.0.0.1:5183` (origens distintas para CORS, mesmo
sendo o mesmo host fisico). Corrigido o `CORS_ORIGINS` para
`http://127.0.0.1:5183` e reexecutado: preflight OPTIONS passou a `200 OK`,
e uma segunda tentativa (ainda sem `wait_for_url` explicito) mostrou
condicao de corrida — a navegacao real ocorria, mas depois da janela de
`networkidle` capturada. A terceira execucao, com espera explicita e
correta (`page.wait_for_url("**/academico", timeout=10000)`), confirmou o
comportamento correto de forma determinística. Nenhuma alteracao de codigo
de producao foi necessaria — a causa raiz de ambas as falhas iniciais foi
configuracao/temporizacao do proprio roteiro de validacao, nao do produto.

## 7. Veredito

**AC-05: ATENDIDO, agora com evidencia completa na reconstrucao.** A parte
automatizada (401 sem autenticacao) ja estava comprovada e foi
reconfirmada; a parte que faltava (retorno ao destino apos login) foi
executada nesta rodada em ambiente isolado, contra o codigo integrado a
`main`, com evidencia visual e estrutural real, sem reaproveitar nenhuma
evidencia do codigo perdido de 2026-09-24. Nenhum defeito de produto foi
encontrado — o unico problema identificado durante a execucao foi de
configuracao do proprio ambiente de teste (CORS), corrigido sem tocar
codigo de producao.

## 8. Limpeza do ambiente

PostgreSQL isolado parado e removido (`pg_ctl stop` + remocao do diretorio
de dados); processos do backend e frontend isolados encerrados; venv do
Playwright preservado em `/tmp` (fora do repositorio, descartavel);
`.env.local` do frontend usado nesta validacao removido do working tree.
