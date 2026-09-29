# rag-web — React frontend (v2)

Web interface of the v2: a React + TypeScript SPA built with Vite,
Tailwind CSS and shadcn/ui, providing a Documents page (upload, list,
status, delete) and a Chat page (streaming answers, sources, history).

## Local development

```bash
cd src/rag-web
npm install
cp .env.example .env      # VITE_API_URL: base URL of the RAG API
npm run dev               # http://localhost:5173
```

## Quality

```bash
npm run lint              # ESLint
npm run format:check      # Prettier
npm run build             # typecheck + production build
```
