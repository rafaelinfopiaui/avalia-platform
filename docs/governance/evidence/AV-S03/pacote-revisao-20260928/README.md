# Pacote de revisão — AV-S03 (BL-AV-2-01 a BL-AV-2-05)

Gerado em: 2026-09-28
Consolidador: Hermes
Base: `local/av-s03-recuperacao` @ `66c95201daf893fa7b2852e0d94b20314f8d8f34` (idêntico a
`origin/main`, 0 commits de divergência — este pacote representa o diff completo sobre `main`,
não um pacote parcial de rodada anterior).

## Propósito

Pacote completo e autossuficiente para revisão de Rafael antes de qualquer stage/commit/push,
conforme autorização registrada em `docs/governance/registers/decisions.md` (nota de 2026-09-28) e
homologação prévia de `BL-AV-2-03` (`DEC-AV-026`).

## Conteúdo

| Arquivo/pasta | Conteúdo |
|---|---|
| `00_base_git.txt` | branch, HEAD, upstream, divergência — prova de que a base é `main` sem deriva |
| `01_git_status.txt` | `git status --porcelain=v1` completo no momento da geração |
| `02_diffstat.txt` | `git diff --stat` dos arquivos rastreados modificados |
| `03_diff_arquivos_rastreados.patch` | diff completo (`git diff`) dos 14 arquivos rastreados modificados |
| `04_lista_arquivos_novos.txt` | lista dos 17 arquivos novos/não rastreados (expandida via `git ls-files --others`, sem diretórios nem `__pycache__`) |
| `05_diff_arquivos_novos.patch` | diff de cada arquivo novo contra `/dev/null` (`git diff --no-index`) |
| `06_inventario_completo.txt` | inventário dos 31 arquivos (14 modificados + 17 novos) com tamanho em bytes e SHA-256 individual |
| `arquivos_novos_raw/` | cópia byte-a-byte de cada um dos 17 arquivos novos, verificada idêntica ao worktree via `cmp` |
| `CHECKSUMS_SHA256.txt` | checksum SHA-256 de cada arquivo deste próprio pacote (gerado por último, cobre todos os itens acima) |

## Resumo das entregas cobertas por este pacote

- `BL-AV-2-01/02`: modelo e migração da estrutura acadêmica (`core/app/models.py`,
  `core/alembic/versions/c4a8b2d91e37_add_academic_structure.py`);
- `BL-AV-2-03`: autorização por vínculo professor↔turma (`core/app/routers/academic.py`,
  alterações em `core/app/main.py`), **homologado por Rafael em `DEC-AV-026`** — 3 rodadas de
  revisão adversarial independente (Antigravity), 68/68 testes verdes
  (`core/app/tests/test_academic_authorization.py`, `test_academic_structure.py`);
- `BL-AV-2-04`: UI mínima (`frontend/src/pages/AcademicPage.tsx`, alterações em
  `AssessmentEditorPage.tsx`, `api.ts`, `types.ts`, `App.tsx`, `Layout.tsx`, `theme.css`,
  `.env.example`) — 2 rodadas de revisão adversarial independente (Codex), 2 achados bloqueantes
  corrigidos e revalidados, 1 ajuste pontual adicional (default de configuração) revisado e
  aprovado com ressalvas (débito `DEBT-AV-012` registrado);
- `BL-AV-2-05`/AC-01 a AC-12: evidências de validação, incluindo `AC-10` (denominador aprovado em
  2026-09-28, `DEC-AV-007`) executado em PostgreSQL isolado dedicado com 16/16 cenários reais
  passando (`docs/governance/evidence/AV-S03/AC-10_validacao_denominador.md`, scripts em
  `docs/governance/evidence/AV-S03/AC-10-scripts/`), e `AC-07`/`AC-09` (revisão de arquitetura,
  `Organization` não é tenant) fechados com evidência dedicada.

## O que este pacote NÃO cobre

- CI remota (AC-08 permanece parcial — sprint ainda local no momento da geração deste pacote);
- homologação formal de `BL-AV-2-04` e da `AV-S03` completa (aguardando Rafael);
- qualquer ação de stage/commit/push (autorizada separadamente, a ser executada após esta revisão).

## Como verificar a integridade deste pacote

```
cd docs/governance/evidence/AV-S03/pacote-revisao-20260928
shasum -a 256 -c CHECKSUMS_SHA256.txt
```

Todos os itens devem reportar `OK`.
