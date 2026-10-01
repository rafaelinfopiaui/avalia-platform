# Revisão Independente — 5 Ajustes ao Plano de Atualização `avalia_dev`

**Arquivo revisado:** `docs/governance/backlog/plano_atualizacao_avalia_dev_av-s04_2026-10-01.md` (800 linhas, lido integralmente)
**Escopo:** somente os 5 ajustes textuais (seção 8, linhas 751-799); scripts SQL/Python não reavaliados (conforme instrução).

## Veredito: **APROVADO COM RESSALVAS**

---

### 1. Janela sem escritas (seção 3.2) — ✅ APROVADO
- Ordem lógica confirmada: interrupção de escritas (3.2, L.159-236) precede explicitamente o backup final (3.3, L.238-265). Texto é explícito: "Ordem correta: identificar e travar os writers ANTES do backup final (seção 3.3), não depois" (L.166-167).
- `REVOKE INSERT/UPDATE/DELETE` (L.198-205) é prova técnica **real**, não cosmética — bloqueio em nível de ACL do Postgres, independente de boa vontade de processos externos.
- Monitoramento via `pg_stat_user_tables` (L.218-225) é complementar/auditável, não o único mecanismo.
- Explicação de por que `LOCK TABLE ... SHARE ROW EXCLUSIVE MODE` não cobre o intervalo pós-`COMMIT` está correta e tecnicamente precisa (L.192-193, referenciando corretamente seção 2.2 item 3, L.92).

### 2. Backup final (seções 3.3/3.4) — ⚠️ APROVADO COM RESSALVA
- Exigência de backup novo + checksum + restauração validada está clara e sem ambiguidade (L.240-246, L.272-275).
- **Ressalva:** L.290-296 (seção 3.4) instrui "repetir **ao menos** os pós-checks (3.7) contra este restore do backup FINAL" — mas o backup final captura o estado **pré-saneamento** (3 duplicatas, `version_num = e1b02279b1a5`), então rodar diretamente os checks de 3.7 (que esperam 0 duplicatas e `version_num = a9f4c2e71b06`) falharia por definição, a menos que 3.5→3.6 também sejam reexecutados nesse restore antes. O texto não deixa isso explícito — risco real de alguém interpretar literalmente e pular 3.5/3.6 na revalidação do backup final. Recomendo reescrever para "repetir a sequência completa 3.5→3.6→3.7 neste restore".

### 3. Matriz de estados (seção 3.8) — ⚠️ APROVADO COM RESSALVA
- Cobre os 5 estados pedidos: antes do saneamento (Estado 1), saneamento commitado (Estado 3), migrações parcialmente aplicadas (Estados 4 e 5), índice concorrente interrompido (Estado 6), cadeia concluída (Estados 8/9).
- Princípio geral (L.436-443) e cada downgrade mencionado (Estados 4 e 5, L.451-452) têm precondição explícita de confirmação manual — nenhum automático. Correto.
- Restauração de backup aparece como alternativa na maioria dos estados (0, 3, 4, 7, 8).
- **Ressalva menor:** Estado 6 (índice concorrente interrompido, L.453) não menciona explicitamente restauração de backup como alternativa se a reexecução também falhar — apenas "parar, investigar". Como é o único estado sem essa menção, recomendo adicioná-la por consistência com o padrão dos demais estados.

### 4. Ativação P5 (seção 4.4) — ✅ APROVADO
- Cobre reinício do backend por causa do `@lru_cache` (L.531-533) — confirmado real em `core/app/config.py:32-33`.
- Rebuild (não restart) do frontend para `VITE_ACADEMIC_MODULE_ENABLED` (L.544-557) — correto.
- Teste funcional pós-ativação (L.559-569) presente.
- Reafirmação do guard do seed não enfraquecido (L.571-581) — nome `require_isolated_database` e regex `^av_s02_saneamento_[A-Za-z0-9_-]+$` conferem exatamente com `core/scripts/seed_academic_multi_question_demo.py:69-85`.

### 5. Consistência de referências cruzadas — ⚠️ 2 REFERÊNCIAS ÓRFÃS
- **L.580:** "(extensão de `core/app/seed.py`, **seção 4.3**)" — seção 4.3 **não existe** (numeração salta de 4.2 para 4.4). O conteúdo referido corresponde à **seção 4.5** ("Dados de demonstração — seed existente não cobre os cenários novos", L.590). Referência errada/órfã.
- **L.788 e L.795:** ambas referenciam "**seção 9**" para detalhes de publicação (URL, SHA, checks) — **seção 9 não existe no documento**, que termina na seção 8 (L.751-800, última linha do arquivo). Referência órfã — ou a seção 9 ainda não foi anexada, ou o texto foi escrito antecipando um conteúdo que não chegou a ser incluído neste arquivo.
- Demais referências cruzadas verificadas (3.2↔3.3, 3.3↔3.4, 3.7↔3.8 Estado 0, 2.2 item 3, seção 5 P4/P5) apontam corretamente para o conteúdo renumerado.

---

## Resumo das ressalvas (não bloqueiam o conteúdo técnico, mas devem ser corrigidas antes da publicação final)
1. L.290-296 — clarificar que a revalidação do backup final deve rerodar 3.5→3.6→3.7, não só os checks de 3.7 isolados.
2. L.453 (Estado 6 da matriz) — adicionar restauração de backup como alternativa de fallback.
3. L.580 — corrigir "seção 4.3" para "seção 4.5".
4. L.788 e L.795 — corrigir ou completar a referência a "seção 9", que não existe no arquivo lido (800 linhas, sem heading `## 9`).

Nenhum problema encontrado nos pontos 1 e 4 (interrupção de escritas e ativação P5); verificação de código confirma que as afirmações técnicas sobre `lru_cache` e o guard do seed batem com `core/app/config.py` e `core/scripts/seed_academic_multi_question_demo.py`.