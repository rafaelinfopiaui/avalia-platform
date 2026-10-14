# Tarefa: AV-S06B — recebimento e armazenamento de imagens de resposta (AvalIA)

Você está no checkout principal do repositório `avalia-plataform`, branch
já criada e com checkout feito: `feat/av-s06b-recebimento-armazenamento-imagens`.
NÃO crie worktree novo, NÃO crie outra branch, NÃO faça `git stage`,
`git commit`, `git push` ou qualquer ação remota. Implementação local
apenas. NÃO toque no banco `avalia_dev` nem em
`avalia_apresentacao_demo_20261002` (nunca escrever neles). NÃO altere
`avalia-github-lab`.

Leia primeiro, por completo, antes de escrever qualquer código:
- `docs/governance/sprints/sprint_AV-S06B_recebimento_armazenamento_imagens.md`
  (documento de sprint completo: escopo §3, mapa de impacto §6, matriz de
  decisões §7, critérios de aceite AC-01 a AC-10 em §8)
- `docs/governance/registers/decisions.md`, linha `DEC-AV-035` (autorização
  desta rodada) e `DEC-AV-018`/`DEC-AV-021` (uma foto por questão, seleção
  manual — preservar, não reabrir)
- `core/app/models.py` (padrão de modelos existentes: `Answer`, `gen_uuid()`)
- `core/app/main.py`: função `create_answer` (padrão de autorização a
  reaplicar — `_get_owned_assessment`, `require_assessment_mutation`) e
  `_get_owned_assessment`/`require_role`
- `core/app/routers/academic.py`, `core/app/routers/config.py` (padrão de
  router separado já usado no projeto — NÃO alterar estes dois arquivos)
- `core/app/deps.py` (`get_current_user`, `require_role`)
- `core/requirements.txt` (dependências atuais; `python-multipart` já
  presente, `Pillow` ausente)

## Objetivo desta sprint (BL-AV-4B-03/04/05)

Implementar recebimento, armazenamento e recuperação segura de UMA imagem
associada a UMA resposta de aluno (`Answer`), SEM qualquer OCR (real ou
simulado) e SEM disparo automático de correção. Uma foto por questão
(DEC-AV-018 já aprovada — não implementar múltiplas páginas). Seleção
manual pelo professor de avaliação/questão/aluno já existe no fluxo atual
de criação de `Answer` — esta sprint apenas anexa uma imagem a uma
`Answer` existente (ou criada no mesmo fluxo).

## O que implementar

### 1. Modelo de dados: `AnswerImage`

Adicionar em `core/app/models.py`, seguindo o padrão exato das classes
existentes (`Mapped`, `mapped_column`, `gen_uuid` como default de `id`):

```python
class AnswerImage(Base):
    __tablename__ = "answer_images"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    answer_id: Mapped[str] = mapped_column(String, ForeignKey("answers.id"), nullable=False)
    storage_filename: Mapped[str] = mapped_column(String, nullable=False)  # nome gerado pelo servidor, nunca o do cliente
    original_filename: Mapped[str] = mapped_column(String, nullable=False)  # metadado, nunca usado em paths
    content_type: Mapped[str] = mapped_column(String, nullable=False)  # MIME real detectado, não o declarado pelo cliente
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String, nullable=False)  # integridade
    uploaded_by_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

Ajuste tipos/imports conforme o padrão real do arquivo (verifique se
`Integer` já está importado). Criar migração Alembic nova (autogenerate
ou manual, seguindo o padrão das migrações existentes em
`core/alembic/versions/`) para a tabela `answer_images`.

### 2. Armazenamento em disco local

- diretório de armazenamento configurável por env var nova (ex.:
  `ANSWER_IMAGES_STORAGE_DIR`, default para algo como
  `core/var/answer_images/` — adicione esse default em
  `core/app/config.py`, seguindo o padrão de `Settings` já existente);
- esse diretório NÃO deve ser versionado — adicione ao `.gitignore` do
  repositório se ainda não estiver coberto (confira primeiro se já existe
  um padrão como `var/` ou similar no `.gitignore` raiz);
- nome de arquivo em disco SEMPRE gerado pelo servidor (ex.: `{uuid4()}.{ext}`
  derivado do tipo MIME real detectado, nunca do nome enviado pelo
  cliente) — isso é crítico para AC-06 (path traversal);
- escrita atômica: grave em um arquivo temporário e só mova/finalize após
  sucesso; o registro no banco só deve ser commitado DEPOIS da gravação em
  disco confirmada (para AC-07 — nunca registro órfão).

### 3. Validação de upload (múltiplas camadas, não confiar em nenhuma isolada)

- adicionar `Pillow` a `core/requirements.txt` e instalar no venv
  (`core/.venv/bin/pip install Pillow`);
- validar o CONTEÚDO REAL do arquivo tentando abrir com
  `PIL.Image.open(...)` e chamar `.verify()` (ou equivalente) — um arquivo
  que declara `Content-Type: image/jpeg` mas não é decodificável como
  imagem deve ser rejeitado com 422, mesmo que a extensão/content-type
  pareçam corretos (AC-04);
- limite de tamanho: 10 MB (proposta registrada na sprint §7) — rejeitar
  ANTES de terminar de gravar o arquivo completo, não depois (leia em
  chunks com limite, ou valide `Content-Length` como primeira defesa e
  trunque a leitura real como segunda defesa — não confie só no header);
- formatos aceitos: JPEG e PNG apenas (verificar pelo `Pillow`, não pela
  extensão do nome enviado);
- nome enviado pelo cliente (`original_filename`) é armazenado APENAS como
  metadado de exibição — nunca usado para construir nenhum path de
  sistema de arquivos. Sanitize mesmo assim antes de guardar como
  metadado (remover caracteres de controle), mas o ponto crítico de
  segurança é nunca usá-lo para I/O.

### 4. Endpoints (novo router `core/app/routers/images.py`)

Seguir o padrão de `core/app/routers/academic.py` (APIRouter com prefix,
Depends de autorização):

- `POST /v1/answers/{answer_id}/images` (multipart/form-data, campo
  `file`): requer `require_role("professor", "admin")`; busca a `Answer`,
  sobe até a `Question`/`Assessment` dela, aplica EXATAMENTE o mesmo
  padrão de autorização já usado em `create_answer`
  (`_get_owned_assessment` + `require_assessment_mutation` — reaproveite
  essas funções de `core/app/main.py`, não duplique a lógica); valida e
  armazena a imagem; retorna metadados (sem o binário);
- `GET /v1/answers/{answer_id}/images` (listar imagens de uma resposta,
  mesma autorização);
- `GET /v1/answer-images/{image_id}/download` (retorna o binário da
  imagem, `Content-Type` real, mesma autorização reaplicada a partir do
  `answer_id` vinculado à imagem) — NUNCA sirva isso como arquivo estático
  público; sempre através deste endpoint autenticado.

Registrar o novo router em `core/app/main.py`
(`app.include_router(images_router)`, junto aos demais).

### 5. O que NÃO fazer (limites rígidos desta sprint)

- NÃO implemente OCR, real ou simulado, de forma alguma;
- NÃO dispare `request_correction`/`run_correction_job` a partir do
  upload de imagem;
- NÃO escolha nem mencione motor de OCR como se fosse decisão tomada;
- NÃO declare nenhum benchmark como concluído;
- NÃO sirva imagens por rota estática sem autenticação;
- NÃO implemente suporte a múltiplas páginas/imagens por questão além de
  permitir reenvio (uma imagem "ativa" por resposta é suficiente — se
  várias forem enviadas, documente o comportamento escolhido no
  relatório, mas não construa fluxo de múltiplas páginas);
- NÃO altere `core/app/routers/academic.py` nem `core/app/routers/config.py`;
- NÃO altere nenhuma regra de autorização existente fora do necessário
  para reaproveitar o padrão já existente.

## Testes a escrever

Novo arquivo `core/app/tests/test_answer_images.py`, cobrindo
(nomes sugeridos, ajuste como fizer sentido):

- upload válido por professor dono → 201, metadados corretos, hash bate;
- upload por professor SEM vínculo/propriedade → 403;
- upload sem autenticação → 401;
- upload de arquivo que não é imagem de verdade (ex.: bytes aleatórios ou
  um PDF) com `Content-Type: image/jpeg` forjado → 422, rejeitado por
  Pillow;
- upload acima do limite de tamanho → 413 ou 422 (escolha e documente);
- upload com nome de arquivo adversarial (`../../../etc/passwd`,
  caracteres de controle) → sucesso no upload (o nome é só metadado), mas
  CONFIRME por teste que o arquivo em disco tem nome seguro gerado pelo
  servidor, nunca o nome adversarial, e que nenhuma escrita ocorreu fora
  do diretório de armazenamento configurado;
- falha de armazenamento (ex.: monkeypatch simulando erro de I/O ao
  gravar) → nenhum registro órfão fica no banco;
- download por dono/vinculado → 200, bytes corretos, `Content-Type`
  correto;
- download por outro professor sem vínculo → 403;
- confirmar por teste (grep de código ou teste funcional) que nenhum
  `CorrectionJob` é criado como efeito colateral do upload.

## Validação real (além dos testes automatizados)

Depois de rodar a suíte local (`pytest core/app/tests -q`), se você tiver
acesso para subir um banco PostgreSQL isolado novo (nome que não seja
`avalia_dev` nem `avalia_apresentacao_demo_20261002`) e um processo Core
real, exercite pelo menos um upload e um download reais via HTTP
(curl/httpx), documentando os status codes reais observados. Se a camada
de permissões desta sessão não permitir rodar processos (psql, uvicorn,
etc.), documente isso explicitamente no relatório — não afirme "testado"
sem ter executado.

## Entregável esperado (relatório final)

Produza um relatório final em markdown, salvo em
`/tmp/claude_report_av_s06b.md`, contendo:
1. Lista exata de arquivos criados/alterados;
2. Resumo do diff de cada arquivo;
3. Resultado real da suíte de testes (contagem passou/falhou, comando
   executado);
4. Para cada critério de aceite AC-01 a AC-10 da sprint: PASSOU / FALHOU /
   NÃO VALIDADO NESTA RODADA, com evidência real (comando + saída, ou nota
   explícita de limitação de permissão);
5. Decisões de design tomadas que não estavam 100% explícitas no pedido
   (ex.: comportamento exato se múltiplas imagens forem enviadas para a
   mesma resposta; código de status escolhido para "arquivo grande demais";
   exata sanitização do nome original);
6. Confirmação explícita de que `avalia_dev` e
   `avalia_apresentacao_demo_20261002` não foram tocados;
7. Estado final do `git status --short` do repositório (sem fazer stage).

Ao final, pare e NÃO faça nada em Git (sem add/commit/push). O relatório e
o código ficam no working tree para revisão humana e de outros agentes.
