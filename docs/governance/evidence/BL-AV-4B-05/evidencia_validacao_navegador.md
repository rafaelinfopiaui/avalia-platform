# Evidência — validação em navegador real (BL-AV-4B-05, 1ª fatia)

Ambiente ISOLADO e descartável (dados fictícios; bancos protegidos nunca tocados):
- PostgreSQL descartável: `avalia_browser_blav4b05_58508` (criado, migrado até
  `b8d3e5f7a2c4`, dropado ao final).
- Core (FastAPI/uvicorn) em 127.0.0.1:8099, `ACADEMIC_MODULE_ENABLED=false`,
  `AI_ENGINE_URL` morto (sem OCR), storage temporário próprio, `CORS_ORIGINS`
  restrito à origem do Vite.
- Frontend (Vite) em 127.0.0.1:5199, `VITE_API_URL` apontando ao Core isolado.
- Chrome dedicado de automação em `--remote-debugging-port=9337` com
  `--user-data-dir` próprio (nunca o perfil pessoal).
- Seed fictício: 1 professor, 1 avaliação publicada, 1 questão, 1 resposta por
  imagem no estágio A com 2 imagens ativas.

## Fluxo validado via API HTTP real (curl contra :8099)
- listar ativas = 2 → DELETE imagem → 200 → ativas = 1
- projeção de excluídas = 1, campos exatos [deleted_at, deleted_by_id, id]
- download da excluída = 410
- DELETE repetido = 200 (idempotente)
- RESTORE = 200 → ativas = 2
- Log do Core emitiu `answer_image_deleted_logically` e `answer_image_restored`
  com apenas ids (sem hash/nome/storage) — coerente com ACD-05.

## Fluxo validado visualmente no navegador (screenshots inspecionados)
1. Estágio "AGUARDANDO TRANSCRIÇÃO"; "Imagens ativas (2)" com Visualizar + Excluir.
2. Clique em "Excluir imagem" dispara confirm nativo com texto:
   "Excluir esta imagem da resposta? Ela deixará de ser exibida e não poderá ser
   usada na transcrição, mas poderá ser restaurada enquanto a transcrição não
   for confirmada." (aviso correto, D1/estágio A).
3. Após excluir: banner "Imagem excluída. Ela pode ser restaurada enquanto a
   transcrição não for confirmada."; "Imagens ativas (1)"; nova seção
   "Imagens excluídas (1)" com texto "Imagens excluídas não podem ser
   visualizadas nem usadas na transcrição. O arquivo não foi apagado do
   armazenamento." — cada excluída mostra só id + "excluída por você em [data]"
   + botão Restaurar, SEM Visualizar/download, SEM hash/nome (R1/R4/ACD-15).
4. Clique em "Restaurar": banner "Imagem restaurada."; volta a "Imagens ativas (2)".
5. Excluídas AS DUAS imagens ativas: "Imagens ativas (0)", "Imagens excluídas (2)";
   botão "Confirmar transcrição..." DESABILITADO; mensagem
   "Esta resposta não tem nenhuma imagem ativa. Restaure uma imagem excluída
   antes de confirmar a transcrição." (ACD-09 confirmado na UI).

## Encerramento
Core/Vite/Chrome encerrados; banco descartável dropado; storage temporário
removido; bancos protegidos (`avalia_dev`, `avalia_apresentacao_demo_20261002`)
intactos; nenhum artefato vazou para o working tree.
