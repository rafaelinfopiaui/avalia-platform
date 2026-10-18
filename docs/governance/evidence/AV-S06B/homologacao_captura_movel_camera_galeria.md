# Homologação — Captura móvel: câmera/galeria + remoção da seleção (AV-S06B, DEC-AV-037)

> Homologação da melhoria no escopo entregue, autorizada pelo responsável (Rafael).
> HEAD homologado: `57e008eae0c58ae12d24beace0098e93b409f52d` (PR #23).
> Sem declaração de deploy, integração de OCR ou compatibilidade universal.

## 1. Escopo homologado

- **Câmera e galeria em ações separadas:** dois inputs/botões — "Tirar foto"
  (`capture="environment"`) e "Escolher da galeria" (sem `capture`) — alimentando o mesmo estado e
  o mesmo envio.
- **Remoção da seleção antes do envio:** botão "Remover foto" (visível só com arquivo,
  `type="button"`, desabilitado no envio), que limpa a seleção local e os dois inputs, preserva
  avaliação/questão/aluno e não faz requisição ao backend (distinto da exclusão de imagem já
  enviada).

Arquivo funcional único: `frontend/src/pages/ImageAnswerPage.tsx`. Preservados sem alteração:
`accept` JPEG/PNG, limite de 10 MiB, validação server-side, autenticação, vínculos, envio,
listagem, visualização e exclusão lógica.

## 2. Testes nos aparelhos efetivamente utilizados

Confirmados pelo responsável em reteste sobre build de produção (servido localmente por
`vite preview`, sem HMR), **em iPhone e Android**: abertura da câmera por "Tirar foto"; captura +
envio; seleção pela galeria + envio; "Remover foto" removendo só a seleção com campos preservados;
re-seleção; envio e visualização da imagem enviada. Não foram repetidos testes humanos já válidos.

## 3. Conferência limitada (sem repetir auditorias válidas)

- HEAD local == remoto == autorizado: `57e008e`.
- Diff vs `main`: exatamente 2 arquivos (código + este tipo de evidência), 149 inserções /
  10 remoções; nenhum artefato de diagnóstico, imagem, log ou configuração local no diff.
- CI do HEAD: AI Engine (pass), Core API (pass), Frontend (pass). `MERGEABLE`, `mergeStateStatus
  CLEAN`. Sem bloqueantes.
- Revisão independente (Antigravity, por delta) previamente concluída sem bloqueantes, incluindo a
  remoção da instrumentação temporária de diagnóstico.

## 4. Limitações documentadas (preservadas)

- Não verificados nesta rodada: reabertura da foto após recarregar a página para os novos envios;
  cancelamento da câmera nativa.
- Comportamento de câmera/galeria válido apenas nos aparelhos efetivamente testados — não
  generalizar a outros modelos/navegadores.
- Sem evidência direta de qual bundle cada aparelho carregou em cada tentativa (o servidor de
  preview não registra assets).

## 5. Integração

Integração em `main` por merge commit, preservando a branch `feat/captura-movel-camera-galeria`.
**Não** constitui deploy, integração de OCR (frente separada) nem alteração de ambiente operacional.
Merge autorizado pelo responsável para o HEAD homologado.
