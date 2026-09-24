# Política de execução técnica

## 1. Objetivo

Definir como cada sessão ou fatia formal do AvalIA é aberta, executada, comprovada e encerrada, inclusive quando parcial, interrompida ou sem alteração de código.

## 2. Autoridade

- Rafael prioriza, aprova planos funcionais, decide ampliações relevantes e homologa resultados.
- Hermes conduz o rito, coordena a execução autorizada e consolida evidências.
- O executor não presume homologação, decisão ou autorização ausente.
- Um único consolidador, nomeado na sprint, atualiza a documentação canônica.

## 3. Abertura obrigatória

Antes de modificar arquivos:

1. ler a governança, o último baseline validado, a última execução registrada e a sprint ativa;
2. confirmar caminho real, raiz Git, remoto, branch, commit, relação com upstream e working tree;
3. identificar alterações preexistentes e protegê-las do escopo atual;
4. consultar requisitos, ADRs e fontes aplicáveis ao objetivo;
5. registrar no documento da sprint ou snapshot em preparação:
   - objetivo da sessão;
   - escopo autorizado e fora de escopo;
   - executor e consolidador;
   - commit de referência e estado inicial;
   - dependências, riscos e bloqueantes;
   - validações previstas.

Um relatório antigo pode orientar a investigação, mas toda alegação sobre “agora” exige inspeção ou execução atual.

## 4. Delegação

Toda delegação deve informar:

- objetivo e resultado esperado;
- arquivos e fronteiras autorizadas;
- critérios de aceite e verificações;
- restrições operacionais e ações proibidas;
- formato de evidência e ponto de retorno ao consolidador.

O registro deve diferenciar: execução delegada, revisão independente, verificação pelo consolidador e homologação por Rafael. Não declarar nenhuma delas se não ocorreu. O consolidador verifica efeitos externos ou resultados críticos de forma independente antes de incorporá-los.

## 5. Execução controlada

- vincular cada mudança a um item da sprint;
- manter o mapa de impacto atualizado antes de tocar caminho novo;
- registrar mudança de escopo antes de executá-la;
- submeter ampliação relevante, risco novo ou conflito de requisito a Rafael;
- distinguir os estados **planejado**, **implementado**, **validado** e **homologado**;
- registrar decisões, débitos e bloqueantes nos registros canônicos com ID estável;
- preservar mudanças preexistentes e não misturá-las em commit futuro;
- não executar deploy, commit, push, tag ou ação remota sem autorização específica aplicável.

## 6. Evidências

Cada verificação registra, no mínimo:

- data e fuso;
- comando ou procedimento;
- ambiente e alvo;
- resultado real;
- tipo de validação;
- relação com item/critério de aceite.

Tipos mínimos:

- **automatizada:** teste, lint, build ou script;
- **inspeção de código/documento:** leitura estática, sem alegar comportamento em runtime;
- **visual:** renderização e interação observadas;
- **integração real:** componentes/dependências reais exercitados;
- **simulação/mock:** dependência substituída ou modo simulado explícito;
- **histórica:** resultado proveniente de registro anterior, não reexecutado agora.

Falha, teste não executado, limitação e ambiente indisponível não podem ser convertidos em sucesso. Resultado parcial conserva seu denominador e suas exclusões.

## 7. Snapshot obrigatório

Ao encerrar cada sessão ou fatia formal, gerar snapshot em `snapshots/`, mesmo que:

- a sprint continue aberta;
- nenhuma entrega tenha sido concluída;
- testes tenham falhado;
- a execução tenha sido interrompida;
- o gate tenha sido reprovado.

O snapshot inclui identificador, data/fuso, sprint, executor, referência Git, working tree inicial/final, entregas e não entregas, arquivos impactados, validações, decisões, débitos, bloqueantes, lacunas e próxima ação.

Snapshots históricos não são reescritos para alterar o fato registrado. Correções usam adendo datado, explicitamente marcado, ou novo snapshot que referencia o anterior.

Se uma interrupção impedir o snapshot, a retomada abre registrando a lacuna; resultados desconhecidos permanecem desconhecidos.

## 8. Execução versus baseline

- `snapshots/latest_execution.md` aponta a última execução registrada, independentemente do resultado.
- `snapshots/latest_validated_baseline.md` aponta somente o estado explicitamente aceito como baseline utilizável.
- execução parcial, reprovada ou ainda aguardando homologação não promove baseline automaticamente.
- a promoção deve identificar quem decidiu, quando e com qual evidência.

## 9. Encerramento da sessão

1. atualizar o documento da sprint e seus itens;
2. registrar validações e limitações;
3. atualizar registros canônicos afetados;
4. gerar snapshot;
5. atualizar o dashboard;
6. revisar README, requisitos/PRD e roadmap, registrando “sem alteração necessária” quando aplicável;
7. executar validações documentais/técnicas previstas;
8. apresentar a Rafael entregas, não entregas e decisões pendentes.

Encerrar a sessão não equivale a concluir a sprint nem homologar o resultado.
