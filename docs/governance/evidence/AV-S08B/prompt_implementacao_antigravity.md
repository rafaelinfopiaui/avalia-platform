# Revisão independente da implementação — AV-S08B (transcrição manual e confirmação humana)

Repo: /Users/rafaeloliveira/Projeto Estágio/avalia-plataform
Branch (checkout atual): feat/av-s08b-transcricao-manual (base main e8b0864)

Você é o revisor INDEPENDENTE desta implementação. Quem implementou foi o Claude
Code (CLI); você NÃO deve confiar no relatório dele como fato verificado — releia
o código-fonte você mesmo e re-execute o que puder.

NÃO faça stage/commit/push/merge. NÃO altere avalia_dev nem
avalia_apresentacao_demo_20261002. NÃO rode migração em banco protegido. Pode
criar e dropar bancos de teste descartáveis próprios (nome contendo "test",
nunca "avalia_dev"/"avalia_apresentacao").

## Contexto obrigatório — leia nesta ordem
1. docs/governance/evidence/AV-S08B/plano_transcricao_manual_confirmacao_humana.md
   (plano técnico aprovado por Rafael via DEC-AV-040 — fonte de verdade do contrato,
   com os 2 pareceres anteriores seus já incorporados)
2. docs/governance/sprints/sprint_AV-S08B_transcricao_manual_confirmacao_humana.md
3. docs/governance/evidence/AV-S08B/prompt_av_s08b_claude_code.md (o prompt que o
   Claude Code recebeu)
4. local-nao-versionado/claude_report_av_s08b.md (relatório do Claude Code — trate
   como alegação a verificar, não como fato)
5. O diff real: `git diff` e os arquivos novos (core/alembic/versions/f2a9c4e6b1d3_*,
   core/app/tests/test_manual_transcription.py)

## O que verificar (contrato do plano, não o relatório)
1. Migração Alembic: puramente aditiva, downgrade seguro/bloqueado quando há dados
   não-default, FK correta. Rode você mesmo contra um banco de teste descartável
   (upgrade, downgrade com dados, upgrade de novo).
2. Os dois endpoints (PATCH draft, POST confirm) em core/app/main.py: ordem de
   verificação de erros, autorização (require_assessment_mutation, diferente do
   endpoint de leitura da fatia anterior), os códigos de erro exatos do plano
   §3.3/§6 (404/403/401/422 ANSWER_NOT_IMAGE_SOURCE/422 ANSWER_TEXT_REQUIRED/
   409 TRANSCRIPTION_ALREADY_CONFIRMED/409 TRANSCRIPTION_VERSION_CONFLICT).
3. O mecanismo de concorrência: é de fato um UPDATE condicional dentro de
   transação (WHERE id=:id AND transcription_version=:expected_version AND
   status=...), não um lock em memória/aplicação. Confirme lendo o código.
4. Re-execute os testes de concorrência real (5 testes marcados pg_concurrent em
   test_manual_transcription.py) contra um Postgres descartável SEU (crie um
   banco com "test" no nome, rode com AVALIA_TEST_POSTGRES_URL apontando pra ele,
   depois drope). Não aceite "passou" sem rodar você mesmo.
5. Que NENHUM caminho de código novo chama request_correction nem cria
   CorrectionJob (ACD-08) — confira por leitura direta do código, não só pelo
   teste do Claude Code.
6. AuditEvent: before/after corretos, na mesma transação do UPDATE.
7. Regressão: rode a suíte completa (SQLite) e confirme "201 passed, 5 skipped"
   (os 5 skipped são os pg_concurrent sem a env var — normal sem Postgres).
8. Frontend: leia ImageAnswerPage.tsx — o fluxo de confirmação em 2 passos com
   aviso de irreversibilidade antes da ação definitiva realmente existe no código
   (não module tsx/build sozinho — leia o JSX). Build/tsc/lint reais.
9. Desvios reportados pelo Claude Code (seção 6 do relatório, D-1 e D-2): avalie
   se são aceitáveis dentro do espírito do plano ou se extrapolam o contrato
   aprovado por Rafael (sinalize se achar que precisam de decisão dele).
10. Pendências reportadas (P-1 a P-4): confirme se são reais e se alguma deveria
    ter sido resolvida nesta rodada.

## Entregável
Escreva o parecer em
docs/governance/evidence/AV-S08B/revisao_implementacao_antigravity.md com:
veredito (aprovado / aprovado com ressalvas / reprovado), achados numerados
(ACH-NN), para cada um: severidade, evidência real que você observou (comando
rodado + saída, ou trecho de código com caminho:linha), e se é bloqueante.
Não presuma nada do relatório do Claude Code sem conferir.
