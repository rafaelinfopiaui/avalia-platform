# Evidência — Captura móvel: câmera e galeria + remoção da seleção (AV-S06B, DEC-AV-037)

> Melhoria da tela "Resposta por foto" para o uso em celular. Rodada LOCAL em ambiente
> isolado descartável; sem publicação de dados; evidências sanitizadas (sem tokens, sem
> bytes de imagem, sem dados pessoais). Testes humanos conduzidos pelo responsável
> (Rafael) em aparelhos reais. **OCR não faz parte desta feature** — permanece frente
> separada.

## 1. Escopo da mudança

Arquivo único alterado: `frontend/src/pages/ImageAnswerPage.tsx`. Sem alterações de backend,
contrato, limites, autenticação ou vínculos.

1. **Câmera e galeria em ações separadas.** O campo de foto passou de um único `<input type="file">`
   para dois caminhos explícitos, ambos alimentando o MESMO estado e o MESMO envio:
   - "Tirar foto": input dedicado com `capture="environment"` (solicita a câmera traseira).
   - "Escolher da galeria": input separado, sem `capture`.
   - Motivação: em pelo menos um Android testado, o input sem `capture` abria apenas a galeria,
     sem oferecer a câmera.
2. **Remoção da seleção antes do envio.** Botão "Remover foto", visível apenas quando há arquivo
   selecionado, `type="button"` (não submete o formulário), desabilitado durante o envio. Limpa
   a seleção local e os dois inputs (permitindo re-selecionar o mesmo arquivo), preserva
   avaliação/questão/aluno e limpa apenas a mensagem de erro da seleção removida. Não faz
   requisição ao backend nem afeta imagens já enviadas (distinta da exclusão de imagem persistida).

Preservados sem alteração: `accept="image/jpeg,image/png"`, limite de 10 MiB, validação server-side
por conteúdo, autenticação, vínculos, envio (`POST /answers/image`), listagem, visualização por
download autenticado e exclusão lógica de imagem já enviada.

Sem `getUserMedia`/câmera ao vivo embutida; sem storage persistente no navegador; sem envio
automático (o envio continua exclusivamente pelo botão).

## 2. Testes humanos efetivamente confirmados (iPhone e Android, aparelhos reais)

Confirmados pelo responsável em reteste sobre build de produção (servido localmente por
`vite preview`, sem HMR):

| Passo | iPhone | Android |
|---|---|---|
| "Tirar foto" abre a câmera (seletor nativo) | Confirmado | Confirmado |
| Captura pela câmera + envio | Confirmado | Confirmado |
| Seleção pela galeria + envio | Confirmado | Confirmado |
| "Remover foto" visível; remove só a seleção; campos preservados | Confirmado | Confirmado |
| Re-seleção (câmera ou galeria) após remover | Confirmado | Confirmado |
| Envio e visualização da imagem enviada | Confirmado | Confirmado |

Corroboração de backend (ambiente isolado): para os envios do reteste, o servidor registrou
`POST /v1/answers/image → 201` seguido de `GET /v1/answer-images/<id>/download → 200`
(visualização), a partir de dois endereços de aparelho distintos.

## 3. Limitações e testes NÃO realizados (registrados; não são falhas)

- **Não verificados nesta rodada:** reabertura/retomada da foto após recarregar a página para os
  novos envios; cancelamento da câmera nativa (sair sem concluir a captura).
- **Não generalizar** o comportamento de câmera/galeria a outros modelos/navegadores além dos
  efetivamente testados.
- **Limitação histórica de evidência:** durante uma fase anterior, observou-se perda de estado do
  formulário ao retornar da câmera. A causa foi atribuída, com base em log do servidor, à
  recompilação a quente (HMR) do Vite em modo de desenvolvimento, disparada por edições do código
  enquanto a página estava aberta no aparelho (incluindo um `ReferenceError` transitório que caiu
  no ErrorBoundary e recriou a árvore) — artefato do ambiente de desenvolvimento, não do produto.
  Após o reteste em build de produção (sem HMR), a remoção/reseleção/envio foram confirmados.
  Observação: `React.StrictMode` executa ciclos de montagem em duplicata apenas em
  desenvolvimento, não em produção. Não há evidência direta de qual bundle cada aparelho carregou
  durante cada tentativa (o servidor de preview não registra os assets); isso permanece como
  limitação de evidência.

## 4. Autoria e revisão

- Implementação (dois botões; "Remover foto"; correção do tratamento de erro ao remover):
  Claude Code, sob especificação e verificação independente do Hermes.
- **Remoção da instrumentação temporária de diagnóstico: realizada pelo Hermes** diretamente,
  durante uma indisponibilidade de autenticação do Claude Code (OAuth expirado), com autorização
  explícita do responsável. A instrumentação temporária (painel de diagnóstico, listeners, logs e
  persistência diagnóstica) foi integralmente removida; câmera, galeria e "Remover foto" foram
  preservados.
- Verificação do Hermes: `npm run build` e `eslint` sem erros no delta final.
- **Revisão independente final (Antigravity):** APROVADO, sem bloqueantes — confirmou a remoção
  completa da instrumentação e a integridade funcional da feature. Revisões intermediárias por
  delta (dois botões; "Remover foto", com um bloqueante corrigido e re-aprovado; instrumentação)
  também foram conduzidas pelo Antigravity pelo fluxo legítimo.

## 5. Pendências para decisão

- Testes humanos restantes do item 3 (reabertura após reload dos novos envios; cancelamento da
  câmera), se desejado — sem defeito concreto conhecido que os exija.
- Ambiente de produção real (domínio/HTTPS, motor de IA) permanece fora do escopo desta feature.
