# Tarefa: resolver DEBT-AV-014 — retomada de respostas por imagem (AvalIA)

Repo: /Users/rafaeloliveira/Projeto Estágio/avalia-plataform
Branch (já criada e em checkout): feat/av-s06b-debt-014-retomada-respostas-imagem (a partir de main cf81109)

NÃO faça commit/push/stage. NÃO toque avalia_dev nem avalia_apresentacao_demo_20261002.
NÃO implemente OCR, transcrição (manual ou automática), confirmação, nem exclusão.
Grave seu relatório em local-nao-versionado/claude_report_debt_014.md (é git-ignored).

## Contexto
A tela "Resposta por foto" (frontend/src/pages/ImageAnswerPage.tsx) só mostra os
envios da sessão atual (estado React volátil). Após recarregar (F5) ou nova sessão,
as respostas por imagem persistidas no backend não reaparecem. Resolva isso.
Desenho e critérios de aceite (ACD-01..10) em:
docs/governance/evidence/AV-S06B/desenho_debt_014_retomada.md — SIGA-O.

## Backend (core/app/main.py)
Adicione um endpoint SOMENTE LEITURA:
  GET /v1/assessments/{assessment_id}/image-answers?question_id=<opcional>
- Autorização por PROPRIEDADE, usando _get_owned_assessment(db, assessment_id, user)
  (professor dono; admin vê tudo). NÃO use require_assessment_mutation nem
  require_active_class_link — isto é LEITURA HISTÓRICA e NÃO pode exigir vínculo
  ativo de turma (o contrato homologado permite consulta histórica por propriedade,
  igual a list_assessments/get_assessment).
- Retorna list[AnswerWithImagesOut] (schema já existente), filtrando
  Answer.source == AnswerSource.IMAGE, ordenado por created_at. Carregue as imagens
  de cada resposta (AnswerImage). NUNCA exponha storage_filename (AnswerImageOut já
  não expõe).
- Se question_id for informado: valide que a questão pertence à avaliação; restrinja
  a ela. Questão inexistente/de outra avaliação -> 404.
- require_role("professor","admin"). Sem token -> 401; não-dono -> 403.
- Não cria, não altera, não dispara nada.

## Frontend (frontend/src/pages/ImageAnswerPage.tsx, services/api.ts, types.ts)
- Em api.ts: adicione listImageAnswers(assessmentId, questionId?) chamando o novo GET.
- Na ImageAnswerPage: ao selecionar avaliação/questão (e ao montar com ?avaliacao=),
  BUSQUE do backend as respostas por imagem persistidas e exiba-as (com estado
  "aguardando transcrição") — de modo que apareçam após reload e em nova sessão, não
  só os envios desta sessão. Una os envios da sessão com os persistidos sem duplicar
  (dedup por answer.id).
- Estados: carregando (spinner), vazio ("Nenhuma resposta por foto nesta seleção."),
  erro (mensagem + repetir). Preserve: ao trocar avaliação/questão, NÃO exibir
  dados/imagens da seleção anterior (limpe antes de buscar).
- Mantenha a visualização por download autenticado (downloadAnswerImage) já existente.
- NÃO introduza ação de correção para resposta por imagem. NÃO mostre nota/IA.

## Testes (core/app/tests/)
Crie testes do novo endpoint cobrindo ACD-01..05 e 09:
- lista respostas IMAGE da avaliação com estado+imagens; não inclui textuais;
- filtro por question_id; questão de outra avaliação -> 404;
- dono 200; não-dono 403; sem token 401;
- LEITURA HISTÓRICA: avaliação com class_group_id e SEM ProfessorClassLink do dono
  -> dono ainda recebe 200 (não exige vínculo ativo);
- storage_filename não aparece no corpo;
- bloqueio de correção permanece (resposta IMAGE sem transcrição -> 422).

## Ao terminar, no relatório
- arquivos alterados/criados; mapeamento ACD-01..10 ao que foi feito;
- comandos para rodar (pytest, ruff, npm run build) — note se seu ambiente não roda;
- quaisquer decisões/dúvidas.
