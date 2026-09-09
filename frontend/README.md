# AvalIA — Frontend

SPA da demonstração do AvalIA, construída com React 18, TypeScript e Vite. O frontend se comunica exclusivamente com o Core API por HTTP.

## Executar localmente

Requisitos: Node.js 20 ou superior e o Core API disponível em `http://localhost:8000/v1`.

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

A aplicação abre em **http://localhost:5173**. Para usar outro endereço do Core, altere `VITE_API_URL` no arquivo `.env`.

## Build de produção

```bash
npm run build
```

Os arquivos otimizados são gerados em `frontend/dist/`. Para conferir o resultado localmente, execute `npm run preview` e acesse **http://localhost:4173**.

## Fluxo coberto

Login, lista e edição de avaliações, questão e rubrica com validação de soma, publicação, entrada de resposta, solicitação e acompanhamento da análise, modo manual em caso de falha e revisão humana da sugestão por critério.
