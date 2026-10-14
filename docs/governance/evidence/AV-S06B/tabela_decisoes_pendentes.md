# AV-S06B — Tabela de decisões pendentes (formato, tamanho, retenção, exclusão)

Data: 2026-10-14 (-03). Para decisão de Rafael antes de qualquer uso além do
ambiente isolado de teste. NENHUMA destas decisões está aprovada; o que foi
implementado nesta rodada são valores técnicos padrão, revisáveis, restritos ao
ambiente isolado.

Legenda das colunas:
- Proposta: o que Hermes sugere (não é aprovação).
- Comportamento implementado: o que o código realmente faz hoje.
- Impacto da escolha: consequência de adotar/mudar.
- Restrito ao isolado: o que vale apenas no ambiente de teste até decisão.
- Depende de decisão antes do uso operacional: o gatilho de Rafael.

---

## 1. Formatos aceitos

- Proposta: aceitar apenas JPEG e PNG.
- Comportamento implementado: valida o conteúdo real com Pillow (não confia em
  Content-Type nem na extensão); aceita apenas formatos detectados como JPEG ou
  PNG (JPEGs de câmera identificados como MPO são mapeados para image/jpeg).
  Qualquer outro formato → HTTP 422.
- Impacto da escolha: JPEG+PNG cobre a quase totalidade de fotos de celular e
  evita formatos com superfície de ataque maior (ex.: SVG com script, GIF
  animado, TIFF multi-frame). Incluir mais formatos amplia compatibilidade mas
  também o risco e o custo de validação.
- Restrito ao isolado: a lista JPEG/PNG vale como limite técnico de teste.
- Depende de decisão antes do uso operacional: confirmar se JPEG+PNG basta para
  o público-alvo (professores fotografando provas) ou se é preciso incluir, por
  ex., HEIC (formato padrão de iPhone recente) ou PDF de página única.

## 2. Tamanho máximo por imagem

- Proposta: 10 MB por imagem.
- Comportamento implementado: duas defesas — (1) recusa imediata com HTTP 413 se
  Content-Length declarado exceder 10 MB + folga de 64 KB, antes de ler o corpo;
  (2) durante a gravação em chunks, conta os bytes reais e aborta com 413 ao
  ultrapassar o limite, removendo o arquivo temporário parcial. Limite
  configurável por env `ANSWER_IMAGE_MAX_BYTES`.
- Impacto da escolha: 10 MB acomoda foto de celular moderna comprimida com folga.
  Valor menor reduz uso de disco e risco de abuso; maior aceita originais sem
  compressão mas aumenta custo de armazenamento e tempo de upload.
- Restrito ao isolado: 10 MB é o default de teste.
- Depende de decisão antes do uso operacional: confirmar o teto e a política de
  armazenamento associada (volume esperado por turma/avaliação).

## 3. Retenção

- Proposta: nenhuma política de expiração automática nesta fatia.
- Comportamento implementado: a imagem é persistida em disco e referenciada no
  banco; não há job de expiração nem TTL. A migração recusa `downgrade` se a
  tabela tiver registros (evita perda de rastreabilidade por engano).
- Impacto da escolha: sem expiração, o volume cresce indefinidamente até decisão
  explícita; por outro lado, preserva o original (requisito BL-AV-4B-04) sem
  risco de apagar prova antes da revisão humana.
- Restrito ao isolado: ausência de retenção automática vale no teste.
- Depende de decisão antes do uso operacional: definir política de retenção
  (prazo, base legal — ligada a DEC-AV-013/014 e à pendência regulatória
  BKL-AV-001/CNE), especialmente por envolver dado de aluno em produção real.

## 4. Exclusão

- Proposta: exclusão apenas manual/administrativa, sem exclusão em massa.
- Comportamento implementado: NÃO IMPLEMENTADA. Não existe endpoint de exclusão
  nem procedimento documentado. Os três endpoints entregues são upload, listagem
  e download. O único comportamento de não-perda é a recusa de downgrade da
  migração com registros presentes. (Não foi criada exclusão nesta rodada por
  não estar autorizada.)
- Impacto da escolha: sem exclusão, não há como remover uma imagem enviada por
  engano a não ser por intervenção direta no banco/disco. Implementar exclusão
  exige definir quem pode excluir, se é lógica (soft) ou física, e como preservar
  trilha de auditoria.
- Restrito ao isolado: n/a (não implementado em lugar nenhum).
- Depende de decisão antes do uso operacional: decidir SE haverá exclusão e com
  qual política (ator autorizado, soft vs. hard delete, auditoria, interação com
  retenção) antes de qualquer uso com dados reais. Requer sprint/escopo próprio.

---

## Requisito técnico transversal (não é decisão de produto)

- Proteção de logs: mantida como requisito técnico já implementado — os logs
  registram apenas IDs (correlation_id, answer_id, image_id, user_id),
  content_type, size_bytes e estágio/motivo de falha. NUNCA registram o conteúdo
  binário da imagem, o caminho em disco, nem o nome de arquivo original enviado
  pelo cliente. Isto é requisito de segurança, não item sujeito a aprovação.

## Resumo para decisão

Itens que BLOQUEIAM uso operacional (produção com dados reais) até decisão de
Rafael: formato (confirmar/estender), tamanho (confirmar teto), retenção
(definir política — ligada a questão regulatória), exclusão (decidir se existe e
como — exige escopo próprio). Nenhum deles bloqueia a continuidade do
desenvolvimento local com dados fictícios.
