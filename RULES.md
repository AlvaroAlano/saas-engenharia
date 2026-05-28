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
- **Nunca** usar `async def` para funções que bloqueiam CPU (pandas, fpdf). Manter como `def` (FastAPI delega para thread pool automaticamente).

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
├── style.css            # Tokens de design global (@theme, :root, .dark).
├── composables/
│   ├── useProfile.js    # Perfil do usuário autenticado.
│   ├── useToast.js      # Toast global: showToast(msg, type, duration).
│   ├── useNotificacoes.js # Notificações em tempo real (docs recebidos).
│   ├── useSidebar.js    # Estado da sidebar.
│   └── useTheme.js      # Modo claro/escuro.
├── components/
│   ├── ui/              # Primitivos: BaseButton.vue, etc.
│   └── modals/          # BaseModal.vue + todos os modais de ação.
└── assets/              # Recursos estáticos.
```

### 5.2 Regras de Código
- **Composition API (`<script setup>`)** é o padrão. Options API está proibida para novos componentes.
- **Padrão Smart & Dumb Components:**
  - **Views/Pages** (Dashboard, Orcamento, EngenhariaList): orquestram dados, chamam API, gerenciam estado local.
  - **Componentes Dumb** (StatusCard, DocumentCard): recebem `props`, emitem `events`. Sem chamadas API diretas.
  - **Exceção pragmática:** `ProjectCard.vue` e `DrawerDetalheProjeto.vue` fazem chamadas API internas para ações pontuais (aprovar doc, validar, liberar obra). Isso é aceitável porque extrair para a view geraria prop-drilling excessivo. Não estender esse padrão a novos componentes sem justificativa.
- **Modais DEVEM ser componentes separados** em `src/components/modals/`. Nunca inline na view. Todo modal usa `BaseModal.vue` como wrapper. Comunicação via `emit('close')` + `emit('update'/'salvar'/'rejeitado')`.
- **Composables** (`composables/`) para lógica reativa compartilhada. Novos composables são encorajados para qualquer estado compartilhado entre mais de um componente.
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
- ❌ `alert()` nativo para feedback de erro. Usar `useToast()`.
- ❌ Verificar ausência de estado para inferir presença de outro (ex: "nenhum 'em análise' = todos aprovados"). Sempre verificar o estado explicitamente.
- ❌ Early-return em computed que bypasse a validação real (ex: `if (status === 'X') return true` antes de checar os itens individuais).

### 5.4 Sistema de Tokens de Design (CSS Custom Properties)
O projeto usa um sistema de tokens semânticos definido em `style.css`. **NUNCA** usar classes hardcoded do Tailwind como `bg-neutral-900` ou `text-white` onde um token semântico exista.

| Token | Light | Dark | Uso |
|---|---|---|---|
| `bg-canvas` | `#f4f4f5` | `#000000` | Fundo da página, inputs |
| `bg-surface` | `#ffffff` | `#0a0a0a` | Cards, painéis, headers |
| `bg-surface-hover` | `#eaeaea` | `#1a1a1a` | Hover de itens interativos |
| `border-hairline` | `#e5e5e5` | `#1f1f1f` | Bordas sutis universais |
| `text-ink` | `#000000` | `#ffffff` | Texto primário |
| `text-ink-muted` | `#666666` | `#888888` | Texto secundário/placeholder |
| `bg-brand-primary` | `#000000` | `#ffffff` | CTAs principais |
| `bg-brand-hover` | `#111111` | `#eaeaea` | Hover de CTAs |

Cores semânticas fixas (não variam com tema): `emerald-*` (sucesso), `red-*` (erro/recusa), `amber-*` (atenção/análise), `blue-*` (info/ação), `indigo-*` (engenharia).

### 5.5 Sistema de Arredondamento
O `style.css` define um sistema de raios com escala explícita. O padrão base é `rounded-md` (8px).

| Classe | Valor | Uso |
|---|---|---|
| `rounded-sm` | 6px | Tags, badges, chips |
| `rounded-md` | 8px | **Padrão base:** botões, inputs, cards compactos |
| `rounded-lg` | 12px | Cards de conteúdo, dropdowns |
| `rounded-xl` | 16px | Painéis, drawers, seções internas de modais |
| `rounded-2xl` | ~24px | Container externo de modais e drawers grandes |
| `rounded-full` | 9999px | Avatares, dots de status, pills |

Regra prática: quanto maior o elemento na hierarquia visual, maior o raio permitido. Não usar `rounded-xl` em botões ou inputs isolados.

### 5.6 Padrão Visual de Modais (Vercel Style)
- **Componente Base:** Todo modal DEVE usar `BaseModal.vue` (`src/components/modals/BaseModal.vue`).
- **Overlay:** `bg-black/45 dark:bg-black/65 backdrop-blur-sm p-4`.
- **Container:** `bg-surface border border-hairline shadow-2xl overflow-hidden rounded-md` (ou `rounded-xl` para modais grandes/drawers).
- **Header:** `bg-surface border-b border-hairline`. Botão X: `<X stroke-width="1.25">` com `p-1.5 rounded-md hover:bg-surface-hover transition-colors text-ink-muted hover:text-ink`.
- **Footer:** `bg-canvas border-t border-hairline px-6 py-4`. Botões alinhados à direita, altura `h-9`, `rounded-md`.
- **Inputs:** `bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all`.

### 5.7 Padrão Visual de Dashboard e Kanban
- **Ícones:** Biblioteca oficial: `lucide-vue-next`. `stroke-width="1.5"` obrigatório em todos os ícones. Ícones solid ou de outras bibliotecas são proibidos.
- **Fundo Global:** Usar tokens (`bg-canvas`, `bg-surface`). Não usar `bg-neutral-*` hardcoded.
- **Cards de Projetos (ProjectCard):** `bg-surface border border-hairline rounded-md`. Status indicado por dot circular 8px (`w-2 h-2 rounded-full`) na cor correspondente à coluna. Sem bordas laterais coloridas.
- **Navegação/Hover na Sidebar:** Efeito "flutuante" com `mx-2 rounded-md`. Não ocupar 100% da largura colando nas bordas.
- **Barras de Progresso:** Altura `h-1.5` ou `h-2`, `rounded-full`.
- **Empty States:** Toda lista/coluna vazia DEVE ter um estado visual significativo (ícone + texto descritivo). Usar `border-dashed border-hairline rounded-md` para contornos de placeholder.
- **Colunas Kanban vazias:** `border border-dashed border-hairline/80 rounded-md bg-canvas/10 text-ink-muted`.

### 5.8 UX e Feedback ao Usuário

**Toda ação assíncrona deve seguir este checklist:**
1. **Loading state:** O botão que dispara a ação deve entrar em estado `disabled` e mostrar um spinner `<Loader2 class="animate-spin">` enquanto aguarda.
2. **Toast de confirmação:** Ao concluir com sucesso, chamar `showToast('Mensagem.', 'success')` via `useToast()`.
3. **Toast de erro:** Em catch, chamar `showToast(err.message || 'Erro genérico.', 'error')`. **Nunca** usar `alert()`.
4. **Otimismo controlado:** Atualizar o estado local (`props.project.X = valor`) após a resposta da API confirmar sucesso, não antes — exceto em ações de baixo risco e sem efeitos colaterais críticos.

**Transições e animações:**
- Usar `<Transition>` do Vue para toda entrada/saída de elementos no DOM. Nunca usar `v-show` sem transição em elementos visualmente proeminentes.
- Padrões globais definidos em `style.css`: `page-enter-active` (fade 150ms), `menu-slide` (slide lateral 200ms).
- Para elementos internos de componente: `transition-all duration-200` ou `transition-colors duration-150` no Tailwind.
- Animação de loading pulsante: `animate-pulse` (skeleton) para carregamento de conteúdo; `animate-spin` para spinners de ação pontual.

**Confirmação de ações destrutivas:**
- Ações irreversíveis (arquivar projeto, rejeitar documento, deletar item) DEVEM usar um modal de confirmação — nunca `confirm()` nativo.

**Formulários:**
- Validação client-side ANTES da chamada à API. Nunca enviar requisição com campos obrigatórios vazios.
- Campos inválidos devem receber feedback visual imediato (`border-red-400`, mensagem de erro inline).

### 5.9 Propriedades Computadas — Boas Práticas

- **Verificação explícita de estado:** Sempre checar o estado que importa diretamente, nunca inferir por exclusão.
  ```js
  // ❌ Frágil: infere "aprovado" pela ausência de "em análise"
  return !docs.some(d => d.status === null)

  // ✅ Explícito: cada doc deve ter status === 'aprovado'
  return categorias.every(cat => {
    const doc = docs.find(d => d.categoria === cat)
    return doc?.status === 'aprovado'
  })
  ```
- **Sem early-return que bypasse validações reais.** Um `if (project.status === 'X') return true` no início de uma computed pode esconder inconsistências de dados introduzidas depois que o status foi setado.
- **Computed para visibilidade de UI** deve refletir o estado *atual* dos dados, não o estado histórico (status do projeto).
- Computeds que calculam elegibilidade para ações críticas (gerar contrato, avançar fase) devem ser **restritivas por padrão**: retornam `false` se qualquer condição não for satisfeita, nunca `true` por atalho.

---

## 6. REGRAS DE DOMÍNIO DE NEGÓCIO

### 6.1 Fluxo de Colunas do Kanban

```
estimativa_enviada → contrato_pendente → engenharia_caixa → obra_liberada
```

| Coluna | Gatilho de Entrada | Status de Projeto Relevante |
|---|---|---|
| `estimativa_enviada` | Projeto criado pelo engenheiro | — |
| `contrato_pendente` | Cliente aprovou estimativa e enviou documentos (`status: 'docs_completos'`) | `docs_validados` (após validação pelo engenheiro) |
| `engenharia_caixa` | Contrato assinado por ambas as partes (`status_assinatura: 'assinado'`) | — |
| `obra_liberada` | Engenheiro clica em "Liberar Obra" | `status: 'liberada'` |

### 6.2 Checklist de Documentos (Regra Rígida)

Os 3 documentos obrigatórios são: `identidade`, `residencia`, `estado_civil`.

| Status do doc | Significado | `url` | `status` |
|---|---|---|---|
| Enviado / Em Análise | Cliente enviou, engenheiro ainda não avaliou | presente | `null` ou ausente |
| Aprovado | Engenheiro aprovou explicitamente | presente | `'aprovado'` |
| Rejeitado | Engenheiro recusou com motivo | `null` (limpo) | `'rejeitado'` |

**Regra inviolável:** O botão "Gerar Contrato" e a seção de contrato comercial só podem ser exibidos quando **todos os 3 documentos** tiverem `status === 'aprovado'`. A verificação correta:
```js
['identidade', 'residencia', 'estado_civil'].every(cat => {
  const doc = docs.find(d => d.categoria === cat)
  return doc?.status === 'aprovado'
})
```
Esta regra é reforçada também no **backend** (`integracoes.py`): os endpoints `GET /projetos/{id}/contrato` e `POST /projetos/{id}/enviar-zapsign` retornam HTTP 403 se qualquer documento não estiver aprovado.

**O botão "Validar Documentos" / "Aprovar Todos"** só deve aparecer quando houver ao menos um documento com URL e sem avaliação:
```js
docs.some(doc => !!doc.url && doc.status !== 'aprovado' && doc.status !== 'rejeitado')
```

### 6.3 Assinatura de Contratos (ZapSign)

| `status_assinatura` | Significado |
|---|---|
| `null` / `'nao_enviado'` | Contrato ainda não enviado |
| `'pendente'` | Contrato enviado, aguardando assinaturas |
| `'assinado'` | Ambas as partes assinaram |

O botão "Enviar para ZapSign" só habilita após o engenheiro ter **pré-visualizado** o documento (`foiPrevisualizando === true`). Isso evita envios sem revisão.

### 6.4 Visualizador de Documentos

O visualizador do painel lateral (DrawerDetalheProjeto) bifurca o renderer pelo tipo do arquivo:
- **Imagens** (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`, `.bmp`): usa `<img>` com `transformOrigin: 'center center'`, `max-w-full max-h-full object-contain`, sem `<iframe>`, sem scrollbars.
- **Outros (PDF, etc.)**: usa `<iframe>` com overlay transparente para captura de eventos de mouse (o iframe bloqueia eventos nativos).

Pan/zoom em imagens usa matemática de `transformOrigin: center`:
```js
panX = (mx - cx) * (1 - ratio) + panX * ratio
panY = (my - cy) * (1 - ratio) + panY * ratio
```
Pan/zoom em iframe usa `transformOrigin: '0 0'` (matemática diferente — ver `handleWheel`).

---

## 7. TABELAS SUPABASE (SCHEMA PRINCIPAL)

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

## 8. DEPLOY E AMBIENTE

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

## 9. INSTRUÇÃO PARA AGENTES DE IA

- **NUNCA** reescreva um arquivo inteiro a menos que seja explicitamente solicitado. Entregue **apenas os blocos de código (diffs)** que foram alterados.
- **Leia este arquivo integralmente** no início de cada sessão de trabalho.
- Antes de criar um novo arquivo, **verifique se já existe** uma implementação que pode ser estendida.
- Antes de criar uma nova rota, **verifique a tabela acima e o `__init__.py`** dos routers para evitar conflitos de prefixo.
- Ao sugerir migrações SQL, incluir **RLS policies** correspondentes. Nunca criar tabela sem política de segurança.
- Ao criar componentes Vue, **seguir o padrão existente**: `<script setup>` + tokens do design system + emits tipados.
- Ao criar rotas FastAPI, **usar Pydantic models** para request/response e `Depends(get_authenticated_supabase)` para injeção do client.
- **Ao implementar qualquer verificação de elegibilidade** (exibir botão, avançar fase, gerar documento), usar verificação **explícita e restritiva** do estado atual dos dados — nunca inferir por exclusão ou confiar em campos de status do projeto como atalho.
- **Ao escrever feedback de UI**, sempre usar `useToast()` para sucesso e erro. Nunca `alert()`. Sempre desabilitar o botão que disparou a ação enquanto a requisição está em andamento.
- Respostas ao desenvolvedor devem ser **densas e diretas**. Sem redundância. Sem introduções prolixas.
