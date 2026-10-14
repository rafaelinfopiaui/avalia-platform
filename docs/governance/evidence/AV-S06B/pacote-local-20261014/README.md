# Pacote local de evidência/rastreabilidade — AV-S06B (2026-10-14)

Este pacote NÃO duplica código. O código-fonte da entrega (router, testes,
migração, modelos, schemas, config) é versionado no Git em seus caminhos
canônicos sob `core/` e é rastreável pelo PR e pelos commits desta entrega.
Aqui ficam apenas metadados de rastreabilidade e as evidências de validação.

## Conteúdo deste diretório

- `README.md` — este índice.
- `git_status.txt` — snapshot do `git status --short` no momento da montagem do
  pacote (lista completa dos arquivos da entrega).
- `INVENTARIO_CHECKSUMS.sha256` — SHA-256 dos artefatos versionados da entrega
  (código em `core/` + docs de governança + evidências), para conferência de
  integridade contra o que foi publicado.

Observação: a cópia redundante de código (`arquivos-novos/`) e o diff recortado
(`diff_arquivos_rastreados.patch`) foram removidos desta versão a pedido de
Rafael — o diff oficial da entrega é o do próprio PR; o código oficial são os
arquivos versionados em `core/`.

## Evidências relacionadas (diretório pai `evidence/AV-S06B/`)

- `prompt_execucao_av-s06b_claude_code.md` — prompt de execução (sanitizado).
- `revisao_independente_antigravity.md` — parecer independente (veredito APROVADO).
- `tabela_decisoes_pendentes.md` — formato/tamanho/retenção/exclusão.
- `resumo_sessao_2026-10-14_av-s06b.txt` — resumo da sessão.

## Conferir integridade (contra o repositório)

    cd "<raiz do repo>"
    shasum -a 256 -c docs/governance/evidence/AV-S06B/pacote-local-20261014/INVENTARIO_CHECKSUMS.sha256

## Resultado técnico (resumo)

- Suíte: 136 passed (110 pré-existentes + 26 novos = 24 funções, 1 parametrizada ×3).
- Ruff `app/` limpo; I001 só nas migrações (padrão preexistente do projeto).
- Validação real: PostgreSQL isolado + Core via HTTP — 11/11 checks (AC-01..10).
- Bug real corrigido pelo Hermes: KeyError('MPO') no Pillow 12.x.
- Revisão independente Antigravity: APROVADO.
- Limite de imagem: 10_485_760 bytes (10 MiB), limite funcional aprovado.
- Somente backend/API. Sem interface de upload; exclusão NÃO implementada.
- Bancos protegidos intactos; validado só em banco isolado.
