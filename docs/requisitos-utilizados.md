# Requisitos utilizados nesta demonstração

Fonte: `/Users/rafaeloliveira/Downloads/PRD_AvalIA_v1.0_Completo.docx` (PRD v1.0,
01/09/2026). Este documento **não copia** o PRD; referencia os requisitos
efetivamente implementados na demonstração e marca claramente o que fica de
fora (backlog).

IMPORTANTE: esta lista descreve o que foi **implementado nesta demonstração**.
Não confundir com conclusão do MVP completo do PRD (P0 do PRD é mais amplo,
ver `docs/backlog.md`).

## Requisitos funcionais (RF) cobertos, em escopo reduzido para a demo

| RF | Título no PRD | Escopo nesta demo |
|---|---|---|
| RF-01 | Autenticação e sessão | Login com e-mail/senha, JWT, sessão expira, mensagens não revelam se e-mail existe, tentativa sem permissão bloqueada e auditada |
| RF-03 | Avaliações | CRUD de avaliação em rascunho → publicada; publicação bloqueada se questão/rubrica inválida |
| RF-04 | Questões e respostas de referência | Uma questão discursiva por avaliação na demo, com valor máximo e resposta de referência |
| RF-05 | Rubricas por critérios | Critérios com peso; soma deve igualar valor da questão (RN-002); rubrica publicada é imutável (nova versão em edição) |
| RF-06 | Entrada de respostas | Resposta digital manual de aluno fictício (CSV/API ficam no backlog) |
| RF-07 | Correção unitária assistida | Fluxo completo: solicitação → pré-processamento → AI Engine → validação de schema → persistência → exibição |
| RF-09 | Confiança e roteamento | Confiança exibida com faixa (alta/média/baixa) e método declarado; nunca apresentada como probabilidade calibrada |
| RF-10 | Revisão humana | Aprovar/alterar com justificativa obrigatória em alteração; nota final separada da sugestão; auditoria de autor/data/antes/depois |

## Requisitos funcionais fora desta demo (backlog)

RF-02 (estrutura acadêmica completa — usamos apenas um vínculo mínimo
professor↔avaliação, sem cursos/turmas), RF-08 (lote), RF-11 (liberação ao
aluno/exportação), RF-12 (dashboards), RF-13 (administração avançada de
modelos — a demo tem apenas 1 modelo fixo configurável por env var), RF-14
(API pública/webhooks), RF-15 (auditoria de pesquisa/anonimização para
dataset científico).

## Regras de negócio (RN) aplicadas

RN-001 (IA sugere, humano decide), RN-002 (soma de critérios = valor da
questão), RN-003 (pontuação por critério entre 0 e máximo), RN-004 (rascunho
incompleto permitido, publicação exige validação), RN-005/RN-006
(versionamento de rubrica e reprocessamento preservando histórico), RN-008
(falha técnica nunca produz nota zero automática), RN-009 (nota total
derivada dos critérios pelo Core, não confiada ao texto da IA), RN-010
(sem atributos pessoais no prompt), RN-011 (edição humana registra autor e
justificativa), RN-016 (confiança declara método), RN-017 (IA indisponível →
correção manual), RN-018 (retentativa limitada).

## Requisitos não funcionais (RNF) aplicados na demo

RNF-01 (senha com hash forte, RBAC no servidor), RNF-02 (minimização — texto
enviado ao AI Engine não inclui nome/matrícula do aluno), RNF-03
(disponibilidade — modo de correção manual quando AI Engine falha), RNF-07
(logs JSON com correlation_id, sem respostas completas nem segredos), RNF-08
(acessibilidade básica — foco visível, teclado, contraste, mensagens claras),
RNF-13 (eventos sensíveis auditáveis).

## Exemplo de domínio usado (do PRD, seção 7)

Questão: "Explique a diferença entre pilha e fila." Rubrica com critérios
LIFO, FIFO, diferenciação e clareza. Respostas fictícias de três perfis:
correta, parcial e conceitualmente errada (ver `docs/roteiro-demo.md` e
`core/app/seed_data.py`).

## Não incluído nesta demo (mesmo estando no P0 do PRD)

OCR, redações longas, cobrança, aplicativo nativo, dashboards avançados, lote
em massa, LMS, segunda revisão configurável, exportação, API externa
pública. Ver `docs/backlog.md` para lista completa por frente.
