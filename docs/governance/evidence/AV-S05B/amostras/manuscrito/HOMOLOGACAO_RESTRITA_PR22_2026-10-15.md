---
id: "homologacao_restrita_pr22_av-s05b"
tema: "AV-S05B manuscrito — homologação RESTRITA e integração do pacote experimental/documental (PR #22)"
data: "2026-10-15 (America/Sao_Paulo)"
estado: "HOMOLOGAÇÃO RESTRITA — pacote experimental/documental; NÃO aprova solução OCR, NÃO congela Amostra_2, NÃO encerra AV-S05B"
---

# Homologação restrita — PR #22 (investigação manuscrita + runner v3 experimental)

Rafael homologou e autorizou integrar o pacote **experimental/documental** publicado no PR #22.
Esta homologação é **restrita** e explicitamente:
- **NÃO** aprova uma solução OCR;
- **NÃO** congela a configuração da Amostra_2;
- **NÃO** encerra a AV-S05B (permanece **parcial**).

## 1. Conferência limitada (reconfirmada, sem repetir benchmark/auditoria)

- **HEAD homologado:** `ca7a0a5fb4c4053ce13e6640312aedce58024e8c` — local == `origin/docs/av-s05b-precisao-metodologica-diagnostico-http400` == `headRefOid` do PR #22.
- **Diff restrito a 31 arquivos** (`main..HEAD`); **0** imagens PNG, **0** arquivos excluídos da
  publicação no diff.
- **Checks próprios desse HEAD (CI do repositório, run 38802856329): 3/3 PASS** — Core API
  (FastAPI + Postgres), AI Engine (FastAPI), Frontend (Vite + React + TS). Sem bloqueantes;
  `mergeStateStatus=CLEAN`.
- **Distinção preservada:** os **56 testes sintéticos do runner v3** foram executados
  **localmente** (pytest + mock, sem rede/imagens/modelos). **A CI do repositório NÃO executa
  esses testes** — o workflow não os cobre. Não se atribui à CI nenhum teste do runner.

## 2. Correção de precisão — contagem de imagens (sem refazer/alterar a coleção)

A redação anterior citou "8 PNGs"; o número correto do **conjunto de trabalho** é **9 imagens**.
Distinção:
- **Existentes (conjunto de trabalho):** 9 PNGs em `local-nao-versionado/ocr/Amostra_1/trabalho_png/`
  (= 9 em `amostras/eval/` + `amostras/dev/`).
- **Encontradas no diff do PR:** 0 (nenhuma imagem publicada).
- **Excluídas da publicação:** todas (9). O "8" anterior era a contagem de um subdiretório
  específico (`amostras/` top-level), não do conjunto de trabalho — erro de redação, corrigido
  aqui. A coleção **não** foi refeita nem alterada.

## 3. Pendência local (preservada fora do Git)

`INVENTARIO_Amostra_1.sha256` (par do `INVENTARIO_Amostra_1.md` excluído) **não é publicado**.
Seu caminho exato foi adicionado a `.git/info/exclude` (local, não versionado), preservando as
regras existentes e **sem** regra ampla para outros checksums. O arquivo **não** foi movido nem
apagado — permanece no disco.

## 4. Integração

Registrada na mesma branch (novo HEAD doc-only para este registro e a correção de precisão).
Integração por **merge commit** preservando a branch; retirada do estado rascunho antes do merge.
CI pós-merge acompanhada; `main` local atualizado por fast-forward. Sem worktrees; sem outro PR
para registrar o merge. (SHA integrado e CI pós-merge registrados no encerramento em chat e no
ponteiro de execução.)

## 5. Estados e limites preservados

- `AV-S05B` **parcial**; configuração da **Amostra_2 NÃO congelada**; **nenhuma solução OCR
  aprovada**.
- **AC-05** (controle ilegível) e **revisão humana cronometrada** **pendentes**.
- Progresso homologado **22/70** inalterado; **ADR-009 sem promoção**; nenhum baseline promovido.
- Nenhuma nova implementação/experimento, inferência, instalação, alteração no produto ou em
  bancos protegidos, P5, deploy nesta rodada.
