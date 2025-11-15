# Graph Pipeline Frontend

Vite + React single-page application that manages GraphRAG indexes/documents and triggers RAG searches via the FastAPI backend.

## Features

- LocalStorage-based login/register experience (per requirements)
- CRUD operations for indexes and documents via backend API
- RAG search UI with keyword filters and chunk inspection
- shadcn-inspired design system (Tailwind + custom UI primitives)

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

Set the backend API URL through `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api`).
