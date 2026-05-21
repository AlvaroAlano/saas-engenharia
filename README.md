# SaaS Engenharia

Plataforma SaaS para engenharia civil — orçamentos, gestão de obras e portal do cliente.

## Estrutura

```
├── apps/
│   ├── web/          # Frontend (Vue 3 + Vite + TailwindCSS) → Vercel
│   └── api/          # Backend (FastAPI + Python) → Render
├── supabase/         # Migrations do banco de dados
├── docs/             # Documentação do projeto
└── RULES.md          # Regras e convenções
```

## Setup Local

### Pré-requisitos
- Node.js 18+
- Python 3.11+

### Iniciar tudo (Windows)
```bash
.\iniciar_sistema.bat
```

### Frontend
```bash
cd apps/web
npm install
npm run dev
```

### Backend
```bash
cd apps/api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Deploy

| Serviço | Plataforma | Root Directory |
|---------|-----------|----------------|
| Frontend | Vercel | `apps/web` |
| Backend | Render | `apps/api` |
| Banco | Supabase | — |
