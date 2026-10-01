# Revisão Independente — Seção 3.2 (Interrupção de Escritas)

**Arquivo:** `docs/governance/backlog/plano_atualizacao_avalia_dev_av-s04_2026-10-01.md` (896 linhas, lido integralmente)
**Modo:** somente leitura — nenhum arquivo editado, nenhum comando contra banco, nenhuma operação git executada.

## Veredito: **APROVADO COM RESSALVAS**

A correção pedida por Rafael foi aplicada corretamente no núcleo da seção 3.2. Há 4 ressalvas (nenhuma bloqueante tecnicamente, mas uma é de consistência documental relevante).

---

## Verificação dos 5 pontos solicitados

**(1) Mecanismo primário = parar/verificar; REVOKE = opcional/secundário → CONFIRMADO**
`L195-217` (passos 2-3): "Mecanismo primário — parar os processos de aplicação na origem e verificar a ausência de atividade" + `pg_terminate_backend` para conexões residuais.
`L218`: "`REVOKE` como camada adicional opcional, não como padrão — só considerar se os passos 2-3 não derem confiança operacional suficiente". Ordem invertida corretamente em relação à versão anterior.

**(2) REVOKE reconhecido como alteração operacional pertencente ao bloco P4 → CONFIRMADO**
`L164-166`: "`REVOKE` é, ele próprio, uma alteração operacional em `avalia_dev` (DCL, muda o estado do banco) e portanto pertence ao mesmo bloco de autorização de P4 — não é uma ação 'grátis' de preparação".
`L221`: reforça "tratar como parte do bloco de execução de P4 (não uma ação preparatória antecipável)".

**(3) Os 5 motivos endereçados com verificação prévia → CONFIRMADO, todos os 5**
- Dono da tabela → `L240-244` (passo b, usa `relowner` capturado no passo a)
- Superusuário → `L246-248` (passo c, `rolsuper`)
- Herança de papel → `L250-257` (passo d, `pg_auth_members`, trata `CASCADE` com cautela explícita)
- `PUBLIC` → `L259-262` (passo e)
- Conexão já aberta antes do REVOKE → `L274-278` (passo f: exige que o passo 3, `pg_terminate_backend`, sempre anteceda o REVOKE, exatamente por esse motivo)

**(4) Baseline e restauração tecnicamente corretas → CORRETAS NA ESSÊNCIA, com ressalvas (ver abaixo)**
Query de baseline `L227-234` e restauração "a partir da baseline literal capturada... revalidar campo a campo" `L280-284` — a lógica está certa (não é um GRANT genérico chutado). Mas há 2 ressalvas técnicas na query (ver Ressalva 3) e uma assimetria na documentação da restauração (ver Ressalva 4).

**(5) Referências cruzadas a "passo N" apontam para o número certo → CONFIRMADO em todos os pontos verificados**
- `L320-321` (seção 3.3): "passos 1-3, mecanismo primário, e passo 4 se REVOKE adicional foi usado" ✓
- `L523` (matriz 3.8, Estado 0): "passos 2-3; se REVOKE foi usado, reconfirmar e reemitir conforme passo 4" ✓
- `L532` (matriz 3.8, Estado 9): "processos de aplicação parados (passo 2)... REVOKE foi usado... (passo 4)... restaurar... (passo 4.g)... conforme seção 3.2 passo 7" ✓ (passo 7 = liberação, bate com `L304-307`)
- `L538` (bloco de restauração de backup): "monitoramento da seção 3.2 (passo 5)" ✓ (passo 5 = monitoramento, bate com `L286-296`)

Todas as 4 referências numéricas verificadas estão corretas pós-renumeração.

---

## Ressalvas encontradas

**Ressalva 1 — Inconsistência não corrigida fora da seção 3.2 (seção 5, bloco P4)**
`L716-727`, especificamente `L722`: "...writers parados e tecnicamente travados via REVOKE." Esta frase, no bloco que define a autorização P4, ainda descreve REVOKE como o mecanismo de trava padrão — contradizendo diretamente a reescrita da 3.2, onde parar processos é o mecanismo primário e REVOKE é opcional. Não é um erro de numeração de "passo N", mas é uma referência substantiva à mesma lógica que ficou desatualizada na correção. Recomendo ajustar para algo como "processos parados e conexões residuais encerradas, com REVOKE como camada adicional opcional se necessário".

**Ressalva 2 — Clareza no histórico da seção 8**
`L833-839` (item 1 da lista de ajustes) ainda descreve a versão *anterior* da 3.2 ("prova técnica via `REVOKE`...") sem nenhum marcador indicando que foi superada — a correção só aparece mais adiante, `L878-891`, na mesma seção 8. Tecnicamente correto como narrativa histórica, mas um leitor que pare no item 1 pode concluir erroneamente que REVOKE ainda é o padrão. Sugiro uma nota inline tipo "(ver correção abaixo)".

**Ressalva 3 — Query de baseline (`L227-234`) não-idiomática e com lacuna silenciosa**
`aclexplode(relacl)` é chamado duas vezes separadamente na lista de SELECT (`.grantee` e `.privilege_type`) em vez do padrão idiomático `FROM pg_class c, aclexplode(c.relacl) a`. Funciona corretamente (o pareamento grantee/privilege_type fica correto porque ambas as chamadas fazem o unnest determinístico do mesmo array em lockstep), mas: (a) é um padrão frágil/não-idiomático; (b) mais importante — se `relacl IS NULL` (estado default do PostgreSQL quando nenhum GRANT/REVOKE explícito jamais foi emitido na tabela), `aclexplode(NULL)` não retorna linhas, e a tabela **desaparece inteiramente** da saída da baseline, sem nenhum registro explícito de "sem ACL explícita, valem os defaults". Recomendo `FROM pg_class c LEFT JOIN LATERAL aclexplode(c.relacl) a ON true` para preservar visibilidade mesmo quando não há ACL explícita.

**Ressalva 4 — Assimetria na documentação da restauração (passo g, `L280-284`)**
O passo de REVOKE (f, `L264-271`) inclui o SQL exato a ser executado. O passo de restauração (g) descreve a intenção correta ("reconstruir o GRANT a partir da baseline literal... revalidar campo a campo") mas não fornece um template SQL equivalente, ao contrário do passo f. Não é um erro técnico, mas é uma lacuna de prontidão operacional — recomendo incluir um exemplo de `GRANT` reconstruído a partir da baseline, análogo ao bloco SQL do passo f.

---

## Conclusão

Os 5 critérios centrais pedidos por Rafael estão satisfeitos: a seção 3.2 corrige corretamente a inversão conceitual (parar+verificar = primário; REVOKE = opcional e pertencente a P4), os 5 motivos de insuficiência do REVOKE isolado estão todos endereçados com checagem prévia, e as referências cruzadas internas a "passo N" (3.3, matriz 3.8 estados 0/9, bloco de restauração de backup) foram corretamente renumeradas. As 4 ressalvas acima — principalmente a Ressalva 1 (texto stale em `L722`) — devem ser corrigidas antes da publicação final para eliminar qualquer leitura contraditória sobre o papel do REVOKE, mas nenhuma delas invalida a correção técnica central feita na seção 3.2.