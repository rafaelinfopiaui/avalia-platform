# Parecer independente — Antigravity (revisão de IMPLEMENTAÇÃO)

Alvo: implementação da 1ª fatia de BL-AV-4B-05 (migração b8d3e5f7a2c4,
endpoints delete/restore, guards, auditoria, script diagnóstico, frontend).
Branch docs/bl-av-4b-05-plano-retencao-exclusao-imagens (não commitada).
Modo: somente leitura (sem escrita/git; rodou testes em modo leitura).

## Duas execuções (transparência de cota)

1. 1ª execução — modelo "Claude Opus 4.6 (Thinking)": leu todo o código e
   verificou os pontos críticos, mas foi CORTADA por cota antes do veredito:
   HTTP 429 "Individual quota reached" (cota do modelo premium, reset ~5h).
   Não houve parecer final nessa execução.
2. 2ª execução — modelo "Gemini 3.8 Flash (High)": concluída com parecer
   completo. Família de modelo DISTINTA do orquestrador (Opus) e do executor
   (Claude Code) — portanto esta revisão tem diversidade real de arquitetura,
   não apenas independência de execução.

## PARECER (Gemini 3.8 Flash High): APROVADO — sem ressalvas, sem defeitos impeditivos

Verificou os 10 itens obrigatórios com citação de arquivo:linha no código real:
1. Guards de estágio (D2/R3): delete/restore só em A; 409 em B/C/D inclusive
   admin; guard reavaliado DEPOIS de _lock_answer_row (SELECT FOR UPDATE).
2. Ponto único de serialização (R2/ACD-10): delete/restore (images.py:417) e
   confirmação (main.py:851) travam a MESMA linha answers via _lock_answer_row
   (with_for_update().populate_existing()). Sem travas em tabelas distintas.
3. ACD-09: confirmação bloqueada (409 ANSWER_HAS_NO_ACTIVE_IMAGE) se não há
   imagem ativa, checado sob o lock.
4. R1/ACD-15: leituras filtram deleted_at IS NULL; download de excluída => 410;
   projeção DeletedAnswerImageOut só (id, deleted_at, deleted_by_id) — omite
   original_filename/storage_filename/sha256_hash/size_bytes/content_type;
   restauração acessível na UI.
5. R4/ACD-05: AuditEvent grava só id/answer_id/uploaded_by_id/content_type/
   size_bytes/created_at — nunca nome original, nome em storage, hash ou conteúdo.
6. ACD-06: UPDATE condicional WHERE deleted_at IS NULL (e IS NOT NULL no
   restore); rowcount 0 => rollback, sem duplicar AuditEvent.
7. ACD-12: restore com arquivo ausente => 409 ANSWER_IMAGE_FILE_MISSING, banco
   intacto.
8. ACD-11: professor sem vínculo/sem propriedade => 403 via
   require_assessment_mutation + require_active_class_link.
9. Migração: aditiva (deleted_at, deleted_by_id FK users, nullable),
   down_revision f2a9c4e6b1d3, sem storage_deleted_at, downgrade bloqueado se
   houver deleted_at/deleted_by_id não nulo.
10. Testes de concorrência test_pg_* são REAIS: ThreadPoolExecutor + TestClient
    com sessões Postgres independentes; threading.Barrier só alinha a partida
    antes do SELECT FOR UPDATE; a serialização ocorre no PostgreSQL. 10 rodadas
    provam sorted([delete, confirm]) == [200, 409] (exatamente um vence).

Testes rodados pelo revisor em modo leitura: test_answer_image_deletion (28
unitários passed, 5 pg deselecionados), test_manual_transcription (33 passed),
test_answer_images (26 passed), tsc --noEmit (0 erros).

## Verificação independente do orquestrador (execução real, NÃO só o parecer)

Rodei eu mesmo, em banco PostgreSQL descartável (avalia_test_blav4b05_56799,
criado e dropado) + SQLite:
- pytest geral: 232 passed, 10 skipped
- test_answer_image_deletion.py com AVALIA_TEST_POSTGRES_URL: 33 passed,
  incluindo os 4 de concorrência real (delete-vs-confirm, concurrent-deletes[2]
  e [8], restore-after-confirm-409, restore-vs-confirm).
- Migração: upgrade cadeia completa -> b8d3e5f7a2c4, colunas+FK OK, downgrade +
  reaplicação OK.
- Frontend: build (tsc+vite) + lint (eslint) limpos.
- Banco descartável dropado; avalia_dev/apresentação intactos; nenhum db vazou
  para o working tree.

Conclusão: implementação APROVADA pela revisão independente E validada por
execução real independente. Nenhum defeito a corrigir.
