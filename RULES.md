# RULES.md — Fonte da Verdade Absoluta do Projeto

> **ESTE DOCUMENTO É IMPERATIVO. QUALQUER AGENTE, DESENVOLVEDOR OU FERRAMENTA DE IA QUE INTERAJA COM ESTE REPOSITÓRIO DEVE LER E OBEDECER INTEGRALMENTE ESTE ARQUIVO ANTES DE GERAR, MODIFICAR OU SUGERIR QUALQUER LINHA DE CÓDIGO.**

---

## 1. OBJETIVO DO SISTEMA

- **Produto:** SaaS de orçamentos para construção civil (B2B/B2C) integrado ao SINAPI.
- **Modelo:** Multi-tenant. Cada engenheiro é um tenant isolado por `usuario_id` via RLS.
- **Core Domain:** CRM de projetos (Kanban) → Orçamento paramétrico → Geração de contratos (ZapSign) → Portal do Cliente (B2C).
- **Stack:**
  - **Frontend:** Vue 3 (Composition API) + Tailwind CSS v4 + Vite 8 + Vue Router 4
  - **Backend:** Python FastAPI + Uvicorn + Pydantic v2
  - **Banco de Dados:** PostgreSQL (Supabase) com RLS obrigatório
  - **Infraestrutura:** Frontend em Vercel (SPA) | Backend em Render
  - **Integrações:** ZapSign (assinatura digital) | SINAPI (precificação de insumos/composições)

---

## 2. REGRAS INEGOCIÁVEIS (CORE)

### 2.1 SINAPI e Precificação
- A lógica de negócio e precificação do SINAPI **NÃO PODE** ser alterada sem revisão prévia explícita do proprietário do projeto.
- Os valores unitários do SINAPI são `read-only` no contexto do orçamento. O BDI é aplicado **apenas na camada de apresentação/PDF**, nunca sobre o valor persistido.
- A busca SINAPI vinculada a um projeto **DEVE** respeitar os parâmetros persistidos no projeto (`uf_obra`, `sinapi_desonerado`, `sinapi_mes_ano`). O backend impõe isso — o frontend **não** decide.

### 2.2 Banco de Dados (Supabase/PostgreSQL)
- **RLS É OBRIGATÓRIO.** Toda query ao Supabase via backend DEVE usar o `get_authenticated_supabase()` que injeta o JWT do usuário. Exceções:
  - Webhooks externos (ZapSign) → usar `get_service_supabase()` (Service Role) com validação de `secret_token`.
  - Portal B2C (acesso anônimo) → usar Service Role **somente após validação de PIN**.
  - Criação de Leads B2C via Matchmaking → usar `get_service_supabase()` (Service Role) na rota `POST /api/matchmaking/solicitar` devido ao fluxo de captação anônima de leads.
- **NUNCA** usar `SUPABASE_SERVICE_ROLE_KEY` em rotas autenticadas normais.
- **Operações em massa** (importação SINAPI, bulk inserts) DEVEM usar **Stored Procedures via RPC** (ex: `upsert_sinapi_lote`) com envio em chunks de no máximo 5.000 registros.
- `usuario_id` DEVE ser injetado no backend via `extrair_usuario_id_do_token()` ou `get_user_id()`. **NUNCA** confiar em `usuario_id` vindo do payload do cliente.

### 2.3 Segurança
- **NUNCA** expor erros crus do banco de dados, Postgres ou Supabase para o cliente. Toda exceção é sanitizada pelo `core/exceptions.py` com mapeamento heurístico.
- **NUNCA** logar dados sensíveis (tokens, PINs, senhas) em produção.
- CORS é configurado em `main.py` e **também** injetado nos Exception Handlers para evitar mascaramento de erros pelo navegador.

---

## 3. PADRÕES DE BACKEND (FastAPI)

### 3.1 Estrutura de Diretórios
```
backend-engenharia/
├── main.py              # Entry point. CORS, lifespan, registro de routers.
├── dependencies.py      # DI: get_authenticated_supabase(), get_user_id()
├── database.py          # Client admin (service role) para casos excepcionais.
├── core/
│   ├── exceptions.py    # Handlers globais. NUNCA remover.
│   └── scheduler.py     # APScheduler para jobs agendados.
├── routers/
│   ├── projetos.py      # CRUD de projetos, itens, histórico. Domínio principal.
│   ├── sinapi.py        # Busca e sync SINAPI. router + admin_router.
│   ├── integracoes.py   # Templates paramétricos, contratos, ZapSign.
│   ├── relatorios.py    # Geração de PDFs comerciais.
│   └── portal_cliente.py # Portal B2C com PIN.
├── utils/
│   └── pdf_generator.py # Helper de PDF isolado.
└── sinapi_bot.py        # Parser de planilhas SINAPI (pandas/openpyxl).
```

### 3.2 Regras de Código
- **Injeção de Dependência** é obrigatória. Parâmetros Supabase, tokens e user_id chegam via `Depends()`. NUNCA instanciar clients inline.
- **Prefixos de rota** são definidos no `APIRouter()`. Rota final = `prefix` + path do decorator. Conferir antes de alterar.
- **Pydantic v2** para validação de entrada. Usar `model_dump(exclude_unset=True)` para PATCHs parciais.
- Respostas de **sucesso** seguem: `{"success": True, "data": {...}}`.
- Respostas de **erro** seguem: `{"success": False, "message": "...", "error_code": "..."}`.
- **Nunca** usar `async def` para funções que bloqueiam CPU (pandas, fpdf). Mover para ThreadPool ou manter como `def` (FastAPI roda em thread separada automaticamente).

### 3.3 Rotas Legadas
- Existem rotas de compatibilidade (`/api/orcamentos`) que mapeiam para `projetos_clientes`. **NÃO** remover sem migrar o frontend correspondente.

---

## 4. PERFORMANCE E ASSINCRONISMO

- **NUNCA** bloquear o event loop principal do Uvicorn.
- Operações I/O-bound (Supabase, httpx) → usar `async/await`.
- Operações CPU-bound (processamento de planilhas SINAPI, geração de PDFs) → rodar como `def` (FastAPI delega para thread pool) ou usar `asyncio.to_thread()`.
- Processamento pesado agendável → usar `APScheduler` (`core/scheduler.py`).
- Importações SINAPI → chunking obrigatório (máx 5.000 registros por lote via RPC).
- O `SinapiBot` processa DataFrames grandes. Suas chamadas **NUNCA** devem ocorrer em funções `async`.

---

## 5. PADRÕES DE FRONTEND (Vue 3 + Tailwind CSS v4)

### 5.1 Estrutura de Diretórios
```
src/
├── App.vue              # Root component com <router-view>.
├── main.js              # Setup: Vue, Router, Plugins.
├── router.js            # Rotas com guards de autenticação.
├── supabase.js          # Client Supabase (anon key via env vars Vite).
├── style.css            # Global styles.
├── composables/         # Lógica reativa reutilizável (useProfile, useToast, useSidebar).
├── components/          # Componentes de página e UI.
│   └── modals/          # Modais extraídos (EditItemModal, SetupOrcamentoModal, ShareModal, etc).
└── assets/              # Recursos estáticos.
```

### 5.2 Regras de Código
- **Composition API (`<script setup>`)** é o padrão. Options API está proibida para novos componentes.
- **Padrão Smart & Dumb Components:**
  - **Views/Pages** (Dashboard, Orcamento, EngenhariaList): orquestram dados, chamam API, gerenciam estado local. Lógica pesada reside aqui.
  - **Componentes Dumb** (StatusCard, DocumentCard, ProjectCard): recebem `props`, emitem `events`. Sem chamadas API diretas.
- **Modais DEVEM ser componentes separados** em `src/components/modals/`. Nunca inline na view. Comunicação via `v-model:show` + `emit`.
- **Composables** (`composables/`) para lógica reativa compartilhada (perfil, toast, sidebar). Novos composables são encorajados.
- Chamadas à API backend usam `axios` com interceptor de token. O token JWT Supabase é injetado no header `Authorization: Bearer`.
- **Tailwind CSS v4** com `@tailwindcss/vite`. Sem `tailwind.config.js` legado.
- Roteamento usa `createWebHistory()`. O `vercel.json` redireciona tudo para `index.html` (SPA).
- **Guard de autenticação** via `router.beforeEach` com `supabase.auth.getSession()`. Rotas com `meta: { requiresAuth: true }` são protegidas.

### 5.3 Anti-padrões Proibidos
- ❌ Lógica de negócio dentro de templates (`<template>`). Extrair para `computed` ou `methods`.
- ❌ Chamar `supabase` diretamente de componentes dumb. Toda comunicação via backend API.
- ❌ Componentes com mais de 500 linhas sem justificativa. Decompor em sub-componentes.
- ❌ `v-if` + `v-for` no mesmo elemento.
- ❌ Hardcoded URLs de API. Usar variáveis de ambiente (`VITE_API_URL`).

---

## 6. TABELAS SUPABASE (SCHEMA PRINCIPAL)

| Tabela | Propósito | RLS |
|---|---|---|
| `projetos_clientes` | Tabela unificada de projetos/orçamentos (CRM + Engenharia) | ✅ por `usuario_id` |
| `orcamento_itens` | Itens do orçamento com FK `projeto_id` | ✅ via join com projeto |
| `projetos_historico` | Auditoria e notas de projeto | ✅ via join com projeto |
| `sinapi_itens` | Base de preços SINAPI (insumos) | ✅ leitura pública autenticada |
| `templates` | Templates paramétricos de orçamento | ✅ por `usuario_id` |
| `template_itens` | Itens de template com FK `template_id` | ✅ via join |
| `templates_contrato` | Templates de texto de contrato | ✅ por `usuario_id` |
| `orcamento_links` | Links B2C do portal do cliente (token + PIN) | ✅ (anon: select em links ativos) |

---

## 7. DEPLOY E AMBIENTE

- **Variáveis de ambiente obrigatórias (Backend):**
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - `FRONTEND_URL` (CORS origin em produção)
  - `ZAPSIGN_API_TOKEN`, `ZAPSIGN_WEBHOOK_SECRET`
  - `ENABLE_SCHEDULER` (default: `false`)
- **Variáveis de ambiente obrigatórias (Frontend):**
  - `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`
- **Vercel:** SPA mode. `vercel.json` com rewrite `"source": "/(.*)", "destination": "/index.html"`.
- **Render:** `build.sh` instala dependências. Entrypoint: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`.

---

## 8. INSTRUÇÃO PARA AGENTES DE IA

- **NUNCA** reescreva um arquivo inteiro a menos que seja explicitamente solicitado. Entregue **apenas os blocos de código (diffs)** que foram alterados.
- Antes de criar um novo arquivo, **verifique se já existe** uma implementação que pode ser estendida.
- Antes de criar uma nova rota, **verifique a tabela acima e o `__init__.py`** dos routers para evitar conflitos de prefixo.
- **Leia este arquivo integralmente** no início de cada sessão de trabalho.
- Ao sugerir migrações SQL, incluir **RLS policies** correspondentes. Nunca criar tabela sem política de segurança.
- Ao criar componentes Vue, **seguir o padrão existente**: `<script setup>` + Tailwind + emits tipados.
- Ao criar rotas FastAPI, **usar Pydantic models** para request/response e `Depends(get_authenticated_supabase)` para injeção do client.
- Respostas ao desenvolvedor devem ser **densas e diretas**. Sem redundância. Sem introduções prolixas.
