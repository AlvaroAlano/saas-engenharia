# UI_COMPONENTS.md — Catálogo de Componentes e Design Tokens (Linear Aesthetic)

> **REGRA DE UI: Ao criar novas telas, é OBRIGATÓRIO reutilizar os componentes listados abaixo. É ESTRITAMENTE PROIBIDO criar HTML bruto e classes Tailwind do zero para elementos que já possuem um componente correspondente.**

---

## 1. PALETA DE CORES OFICIAL E TOKENS (LIGHT E DARK MODE)

A partir de agora, o projeto adota a estética minimalista, precisa e baseada no design system do Linear. O sistema de "profundidade via sombreamento" (`shadow-md`, etc.) está abolido. A elevação é definida por cores de superfície e bordas finas (hairlines). O dark mode será implementado usando o prefixo `dark:` do Tailwind.

| Função | Token Tailwind (Light + Dark) | Descrição |
|---|---|---|
| **Canvas (Fundo da Página)** | `bg-slate-50 dark:bg-[#010102]` | Body, seções de conteúdo, fundo base |
| **Surface 1 (Cards, Painéis)** | `bg-white dark:bg-[#0f1011] border border-slate-200 dark:border-[#23252a]` | Containers padrão, cards, modais |
| **Surface 2 (Hover/Featured)** | `bg-slate-50 dark:bg-[#141516] border border-slate-300 dark:border-[#34343a]` | Cards destacados, fundos de hover |
| **CTA Primário (Lavanda)** | `bg-[#5e6ad2] hover:bg-[#828fff] text-white` | Botões de ação principal. Única cor de acento real na UI. |
| **CTA Secundário (Charcoal)** | `bg-white dark:bg-[#0f1011] hover:bg-slate-50 dark:hover:bg-[#141516] text-slate-900 dark:text-[#f7f8f8] border border-slate-200 dark:border-[#23252a]` | Ações secundárias (Cancelar, Fechar) |
| **Texto Principal (Ink)** | `text-slate-900 dark:text-[#f7f8f8]` | Títulos, headers, textos em foco |
| **Texto Secundário (Muted)** | `text-slate-500 dark:text-[#d0d6e0]` | Subtítulos, labels, meta infos |
| **Texto Terciário (Subtle)** | `text-slate-400 dark:text-[#8a8f98]` | Metadados pequenos, placeholders |
| **Focus Ring (Lavanda)** | `focus:outline-none focus:ring-2 focus:ring-[#5e6ad2]/50 focus:border-[#5e6ad2]` | Usado ao redor de inputs ativos |
| **Bordas (Hairlines)** | `border-slate-200 dark:border-[#23252a]` | Divisores, separadores, contornos |
| **Sucesso (Semantic Green)** | `bg-green-50 dark:bg-[#27a644]/10 text-green-700 dark:text-[#27a644] border-green-200 dark:border-[#27a644]/30` | Apenas para pílulas de status e confirmações |
| **Perigo / Aviso** | `bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border-red-200 dark:border-red-500/30` | Destruição e exclusão |

### Ícones
- **Biblioteca:** Google Material Symbols Outlined → `<span class="material-symbols-outlined">`
- **Preenchido (filled):** `style="font-variation-settings: 'FILL' 1;"`
- **Tamanhos:** `text-[14px]` (inline), `text-[18px]` (botão), `text-[20px]` (header), `text-3xl` (empty state)

### Geometria e Formas
- **Shadows Abolidas:** NUNCA utilize `shadow-sm`, `shadow-md`, `shadow-lg`, etc. A separação é feita exclusivamente por `border`.
- `rounded-md` (8px) para botões, inputs, tags.
- `rounded-lg` (12px) ou `rounded-xl` (16px) para cards, painéis principais, e modais.
- `rounded-full` (9999px) apenas para avatares e certas pílulas/status.

---

## 2. PADRÃO DE INPUTS (Reutilizar Sempre)

```html
<!-- Input Text Padrão -->
<input class="w-full bg-white dark:bg-[#0f1011] border border-slate-200 dark:border-[#23252a] rounded-md py-2 px-3 text-sm text-slate-900 dark:text-[#f7f8f8] placeholder:text-slate-400 dark:placeholder:text-[#8a8f98] focus:outline-none focus:border-[#5e6ad2] focus:ring-2 focus:ring-[#5e6ad2]/50 transition-colors" />

<!-- Label Padrão -->
<label class="block text-sm font-medium text-slate-700 dark:text-[#d0d6e0] mb-1">Label</label>

<!-- Select Padrão (com seta custom) -->
<div class="relative">
  <select class="w-full bg-white dark:bg-[#0f1011] border border-slate-200 dark:border-[#23252a] rounded-md px-3 py-2 text-sm text-slate-900 dark:text-[#f7f8f8] focus:outline-none focus:border-[#5e6ad2] focus:ring-2 focus:ring-[#5e6ad2]/50 appearance-none cursor-pointer transition-colors">...</select>
  <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-[#8a8f98] pointer-events-none text-[18px]">expand_more</span>
</div>
```

---

## 3. PADRÃO DE MODAIS (Anatomia Obrigatória)

Sem sombras pesadas. Overlay com leve escurecimento, modal com borda de alto contraste.

```html
<!-- Overlay padrão -->
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 dark:bg-[#000000]/70" @click.self="emit('close')">
  <div class="bg-white dark:bg-[#0f1011] border border-slate-200 dark:border-[#23252a] rounded-xl w-full max-w-md overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-slate-100 dark:border-[#23252a] flex items-center justify-between bg-white dark:bg-[#0f1011]">
      <h3 class="text-lg font-medium text-slate-900 dark:text-[#f7f8f8]">Título</h3>
      <button @click="emit('close')" class="p-1 rounded-md hover:bg-slate-100 dark:hover:bg-[#141516] text-slate-400 dark:text-[#8a8f98] transition-colors">
        <span class="material-symbols-outlined text-[18px]">close</span>
      </button>
    </div>
    <!-- Body -->
    <div class="p-6 text-slate-900 dark:text-[#d0d6e0]">...</div>
    <!-- Footer -->
    <div class="px-6 py-4 bg-slate-50/50 dark:bg-[#141516]/50 border-t border-slate-100 dark:border-[#23252a] flex justify-end gap-3">
      <!-- Secondary Button -->
      <button class="bg-white dark:bg-[#0f1011] hover:bg-slate-50 dark:hover:bg-[#141516] text-slate-900 dark:text-[#f7f8f8] border border-slate-200 dark:border-[#23252a] px-4 py-2 text-sm font-medium rounded-md transition-colors">Cancelar</button>
      <!-- Primary CTA Button -->
      <button class="bg-[#5e6ad2] hover:bg-[#828fff] text-white px-4 py-2 text-sm font-medium rounded-md transition-colors">Confirmar</button>
    </div>
  </div>
</div>
```

---

## 4. COMPOSABLES (Estado Global Reativo)

### `useToast()` — `src/composables/useToast.js`
- **Retorna:** `{ toastVisible, toastMessage, toastType, showToast, pauseTimer, resumeTimer }`

### `useSidebar()` — `src/composables/useSidebar.js`
- **Retorna:** `{ isSidebarOpen, toggleSidebar }`

### `useProfile()` — `src/composables/useProfile.js`
- **Retorna:** `{ profile, empresa, isLoading, refreshProfile }`

---

## 5. CATÁLOGO DE COMPONENTES

### 5.1 `GlobalToast` — `src/components/GlobalToast.vue`
### 5.2 `Sidebar` — `src/components/Sidebar.vue`
### 5.3 `TopHeader` — `src/components/TopHeader.vue`
### 5.4 `StatusCard` — `src/components/StatusCard.vue`
### 5.5 `DocumentCard` — `src/components/DocumentCard.vue`
### 5.6 `ProjectCard` — `src/components/ProjectCard.vue`
### 5.7 `ArvoreCustos` — `src/components/ArvoreCustos.vue`
### 5.8 `SinapiTable` — `src/components/SinapiTable.vue`
### 5.9 `FinancialSummary` — `src/components/FinancialSummary.vue`
### 5.10 `ArchivedProjectsDrawer` — `src/components/ArchivedProjectsDrawer.vue`
### 5.11 `NovoClienteModal` — `src/components/NovoClienteModal.vue`
### 5.12 `EditProjectModal` — `src/components/EditProjectModal.vue`

---

## 6. MODAIS ESPECIALIZADOS (`src/components/modals/`)

### 6.1 `EditItemModal` — `src/components/modals/EditItemModal.vue`
### 6.2 `SetupOrcamentoModal` — `src/components/modals/SetupOrcamentoModal.vue`
### 6.3 `ShareLinkModal` — `src/components/modals/ShareLinkModal.vue`
### 6.4 `ManualItemModal` — `src/components/ManualItemModal.vue`

---

## 7. DÍVIDA TÉCNICA DE UI

| Componente | Problema | Ação Futura |
|---|---|---|
| `ShareModal` vs `CompartilhamentoModal` | Duplicação funcional — ambos geram link B2C com PIN | **Resolvido:** Unificados no componente `ShareLinkModal.vue` ✅ |
| `FinancialSummary.vue` | Contém modal de item manual inline (HTML duplicado com `ManualItemModal`) | Extrair e usar `ManualItemModal` como sub-componente |
| `formatCurrency()` | Função utilitária duplicada em 4+ componentes | Extrair para `src/utils/formatters.js` |
| `etapas[]` array | Definição duplicada em `ArvoreCustos`, `EditItemModal`, `ManualItemModal` | Extrair para `src/constants/etapas.js` |
