---
id: "EXEC-2026-09-28-07"
tipo: execucao
sprint: "AV-S03"
gerado_em: "2026-09-28T21:40:00-03:00"
executor: "Antigravity (correção), Codex (revalidação), Hermes (verificação independente + correção do default divergente)"
status: parcial
commit_referencia: "66c95201daf893fa7b2852e0d94b20314f8d8f34"
---

# Snapshot EXEC-2026-09-28-07 — correção e revalidação dos achados de BL-AV-2-04

> Registro histórico. Não promover automaticamente a baseline.

## 1. Abertura

- objetivo: corrigir os 2 achados bloqueantes e 1 ressalva encontrados pelo Codex na revisão
  independente de `BL-AV-2-04` (snapshot EXEC-2026-09-28-06), revalidar de forma independente, e
  corrigir uma divergência de configuração descoberta durante a revalidação;
- escopo autorizado: `frontend/src/pages/AcademicPage.tsx`, `AssessmentEditorPage.tsx`,
  `services/api.ts`, `frontend/.env.example`; leitura/execução de lint, build e suíte do Core;
- fora de escopo: `core/` (backend), testes/autorização já homologados de `BL-AV-2-03`, `avalia_dev`,
  stage, commit, push, tag, deploy;
- branch/upstream/commit: `local/av-s03-recuperacao`, `origin/main`, `66c95201daf893fa7b2852e0d94b20314f8d8f34`.

## 2. Correções aplicadas (Antigravity) e verificadas independentemente (Hermes)

| Achado | Correção alegada | Verificação independente (Hermes, leitura direta do diff) |
|---|---|---|
| 1 (bloqueante): erros de carregamento engolidos | `AcademicPage.tsx: loadData()` reescrito com `Promise.allSettled`, falhas individuais acumuladas e reportadas via `setError` | confirmado por leitura do diff real (`git diff`), não apenas pelo relato do agente |
| 1b: `listClassGroups()` engolido em `AssessmentEditorPage.tsx` | `.catch` agora chama `setError` | confirmado por leitura do diff |
| 2 (bloqueante): turma opcional na UI mas obrigatória no backend | `isAcademicModuleEnabled()` adicionada; usada em `complete`/`canPublish`/bloqueio de `persist()`; rótulo e `required` do `<select>` ajustados | confirmado por leitura do diff |
| ressalva: mensagem `detail` do FastAPI não extraída | `request()` em `api.ts` agora tenta `message`, `detail.message`, `detail` como string, e primeiro `msg` de array de validação Pydantic | confirmado por leitura do diff |

## 3. Achado adicional encontrado na revalidação (Codex) e corrigido (Hermes)

O Codex, na revalidação independente, identificou que `isAcademicModuleEnabled()` assumia `true`
como default quando `VITE_ACADEMIC_MODULE_ENABLED` não está configurada, enquanto o backend
(`core/app/config.py:18`) usa `ACADEMIC_MODULE_ENABLED` com default `"false"`. Isso cria dessincronia
real (não hipotética): em ambiente sem nenhuma das duas variáveis configuradas, a UI assumiria o
módulo ativo enquanto o backend o trata como inativo, causando comportamento de validação
incoerente entre UI e servidor.

**Correção aplicada por Hermes:** o default de `isAcademicModuleEnabled()` foi alterado de `true`
para `false`, espelhando exatamente o default do backend, com comentário explicando a necessidade de
configurar `VITE_ACADEMIC_MODULE_ENABLED=true` no frontend sempre que
`ACADEMIC_MODULE_ENABLED=true` estiver configurado no backend. `frontend/.env.example` já documenta
`VITE_ACADEMIC_MODULE_ENABLED=true` como valor de referência para ambientes com o módulo ativo,
preservado sem alteração (é opt-in explícito, não o default de código).

Esta não é uma solução definitiva de sincronização (o ideal seria o frontend consultar o valor real
do backend em vez de duplicar a configuração via env vars separadas) — permanece como débito técnico
registrado, não bloqueante, pois o backend continua sendo a autoridade final e rejeita corretamente
qualquer submissão incompatível com 422.

## 4. Validações executadas (verificação direta por Hermes, após a correção do default)

```
cd frontend && npm run lint   → eslint src: sem erros
cd frontend && npm run build  → tsc -b && vite build: 33 modules transformed, built in 43ms, código 0
```

Suíte do Core (68/68) já havia sido confirmada pelo Codex na revalidação anterior a esta correção
pontual; a mudança de default não afeta o backend nem seus testes (arquivo puramente frontend).

## 5. Veredito consolidado

- Codex (revalidação, antes da correção do default): **APROVADO COM RESSALVAS** — 2 bloqueantes e a
  ressalva original corrigidos; identificou a divergência de default como ressalva não bloqueante;
- Hermes: corrigiu a ressalva do default imediatamente (mudança de uma linha, sem risco), elevando o
  estado para: **sem bloqueantes e sem ressalvas conhecidas pendentes** nesta rodada.
- Débito técnico registrado (não bloqueante): o frontend não consulta dinamicamente o backend para
  saber se o módulo acadêmico está ativo; depende de duas variáveis de ambiente configuradas em
  paralelo. Fonte única de verdade (endpoint de capacidades do backend) é uma melhoria futura, fora
  do escopo desta correção pontual.

## 6. Estado final e limites

- `BL-AV-2-04`: correções verificadas e validadas tecnicamente; ainda sem homologação formal por
  Rafael;
- `BL-AV-2-03` permanece homologado, não reaberto por este trabalho;
- nenhuma ação Git/remota realizada; `avalia_dev` não acessado;
- este snapshot não promove baseline nem declara a sprint `AV-S03` concluída.

## 7. Próxima decisão

Rafael revisar o estado consolidado de `BL-AV-2-04` e decidir sobre homologação. AC-10 (denominador
de teste, `DEC-AV-007`) continua pendente de decisão explícita de Rafael, sem alteração nesta
execução.
