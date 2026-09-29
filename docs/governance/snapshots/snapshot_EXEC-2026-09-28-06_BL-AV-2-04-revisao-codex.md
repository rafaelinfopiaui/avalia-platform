---
id: "EXEC-2026-09-28-06"
tipo: execucao
sprint: "AV-S03"
gerado_em: "2026-09-28T21:26:00-03:00"
executor: "Codex (revisão), Hermes (consolidação)"
status: parcial
commit_referencia: "66c95201daf893fa7b2852e0d94b20314f8d8f34"
---

# Snapshot EXEC-2026-09-28-06 — revisão cruzada independente do Codex em BL-AV-2-04 (UI)

> Registro histórico. Não promover automaticamente a baseline.

## 1. Abertura

- objetivo: revisão cruzada independente e somente leitura da UI de `BL-AV-2-04` (implementada pelo
  Antigravity), como contraponto ao autor original, seguindo o mesmo padrão adversarial já aplicado a
  `BL-AV-2-03`;
- escopo autorizado: leitura de `frontend/src/pages/AcademicPage.tsx`, `AssessmentEditorPage.tsx`,
  `services/api.ts`, `types.ts`; execução de `npm run lint` e `npm run build` (sem alteração de
  arquivos);
- fora de escopo: qualquer alteração de código, `avalia_dev`, stage, commit, push, tag, deploy;
- branch/upstream/commit: `local/av-s03-recuperacao`, `origin/main`, `66c95201daf893fa7b2852e0d94b20314f8d8f34`;
- executor: Codex, via `codex exec --sandbox workspace-write` (permissão de escrita concedida ao
  sandbox, mas nenhuma escrita foi realizada — confirmado por `git status` idêntico antes/depois: 24
  caminhos, sem alteração).

## 2. Veredito do Codex

**AJUSTES NECESSÁRIOS**

### Achados bloqueantes

1. **Falhas de carregamento silenciosamente convertidas em listas vazias.** Em
   `AcademicPage.tsx:87`, as 7 requisições de carregamento usam `.catch(() => [])`. Erros 403/404/422
   e falhas de rede nunca chegam ao tratamento de erro visível; a tela termina o loading e mostra
   "nenhum encontrado", confundindo indisponibilidade/falta de autorização com ausência real de dados.
   O mesmo padrão ocorre em `AssessmentEditorPage.tsx:19` (falha de `listClassGroups()` é
   integralmente engolida, seletor de turma fica vazio sem explicação).

2. **UI trata turma como opcional, mas o backend a exige no modo acadêmico.**
   `AssessmentEditorPage.tsx:94` e a opção da linha 101 rotulam o campo "opcional"; `complete`/
   `canPublish` (linhas 41–42) não exigem turma; o payload omite o campo quando vazio (linha 66).
   Porém `core/app/main.py:146` retorna 422 quando `academic_module_enabled=true` e não há
   `class_group_id`. A UI permite ao usuário tentar uma submissão que o backend sabidamente rejeitará.

### Ressalva adicional (não bloqueante)

- Tratamento de erro compartilhado não preserva a mensagem padrão do FastAPI (`{detail: "..."}`).
  Em `api.ts:58`, o campo `detail` textual não é extraído como mensagem; um 422 como "Turma é
  obrigatória..." vira mensagem genérica sempre que o erro não é engolido pelos achados acima.

### Verificações positivas confirmadas

- `class_group_id` é realmente enviado no `POST /v1/assessments` (montagem em
  `AssessmentEditorPage.tsx:64`, chamada na linha 71) — não é apenas estado local do componente.
- Contratos de tipos em `api.ts`/`types.ts` correspondem aos schemas do backend; nenhum uso de `any`
  ocultando shape incorreto foi encontrado.
- Nenhuma ampliação de escopo de dados pelo frontend: dropdowns exibem exatamente as coleções já
  filtradas pela API; nenhuma tela expõe dado fora do escopo de autorização do papel.
- Separação Student↔Enrollment respeitada na UI: a tela de matrícula manipula turma/aluno/status,
  sem permitir edição dos dados globais do aluno.
- Estados de loading (`Spinner`) e arrays iniciais vazios evitam acesso a `undefined` capaz de
  quebrar as abas.

## 3. Validação real executada pelo Codex

```
npm run lint  → eslint src: sucesso, sem erros
npm run build → tsc -b && vite build: 33 modules transformed, built in 64ms, código 0
```

`git status` antes/depois idêntico (24 caminhos modificados/não rastreados) — confirma que a revisão
foi efetivamente somente leitura.

## 4. Estado final e limites

- `BL-AV-2-04`: **NÃO aprovado** nesta rodada; 2 achados bloqueantes pendentes de correção antes de
  qualquer homologação;
- este snapshot não reabre nem altera o status de `BL-AV-2-03` (autorização), que permanece homologado
  separadamente;
- nenhuma alteração de código foi feita; `avalia_dev` não foi acessado; nenhuma ação Git/remota
  ocorreu;
- próxima ação: delegar correção dos 2 achados bloqueantes e da ressalva ao Antigravity (autor
  original), seguindo o mesmo padrão de rodadas de correção usado em `BL-AV-2-03`, com revalidação
  independente ao final.

## 5. Próxima decisão

Hermes prossegue com a correção delegada (mecânica, sem decisão de produto) e nova revisão
independente. Nenhuma homologação de `BL-AV-2-04` é presumida por este snapshot.
