# ATENÇÃO AGENTES FLASH: Seu trabalho é ESTRITAMENTE VISUAL. Alterem APENAS as classes CSS do Tailwind. É expressamente PROIBIDO alterar a lógica reativa do Vue (`ref`, `computed`, `watch`), modificar propriedades `props`, `emits` ou chamadas de API.

# Plano de Refatoração de UI: Estética Linear (Light & Dark Mode)

Este documento descreve as fases lógicas para converter todo o frontend do projeto para a estética inspirada no [Linear](https://linear.app), adotando o Light Mode refinado e o Dark Mode (`dark:`) via Tailwind CSS, com a cor Lavanda (`#5e6ad2`) como acento principal. Toda noção de "profundidade via sombreamento" (`shadow-md`, etc.) deve ser substituída por `border` (hairlines).

## FASE 1: Core Layout e Navegação Global
Nesta fase, substituímos os alicerces visuais da aplicação, configurando os backgrounds principais, tipografia e navegação.

- [x] `src/App.vue` (se aplicável, para setar classes globais de bg e dark mode no `body`/`html`)
- [x] `src/components/Sidebar.vue`
- [x] `src/components/TopHeader.vue`
- [x] `src/components/GlobalToast.vue`

## FASE 2: Shared UI & Dumb Components
Componentes genéricos ou menores que servem como blocos de montar.

- [x] `src/components/StatusCard.vue`
- [x] `src/components/DocumentCard.vue`
- [x] `src/components/SinapiTable.vue`
- [x] `src/components/ArvoreCustos.vue`
- [x] `src/components/ProjectCard.vue`

## FASE 3: Modais Especializados e Genéricos
Remover *TODAS* as classes de shadow e implementar o overlay/cards com borders e fundo sólido. Trocar de verde/indigo para o Lavanda Linear primário.

- [x] `src/components/modals/CompartilhamentoModal.vue`
- [x] `src/components/modals/EditItemModal.vue`
- [x] `src/components/modals/SetupOrcamentoModal.vue`
- [x] `src/components/modals/ShareModal.vue`
- [x] `src/components/NovoClienteModal.vue`
- [x] `src/components/EditProjectModal.vue`
- [x] `src/components/ManualItemModal.vue`

## FASE 4: Smart Components e Drawers
Componentes complexos que contêm lógicas densas e combinam vários blocos.

- [x] `src/components/Dashboard.vue`
- [x] `src/components/Orcamento.vue`
- [x] `src/components/FinancialSummary.vue`
- [x] `src/components/ArchivedProjectsDrawer.vue`

## FASE 5: Views e Páginas de Configuração
Páginas inteiras que agem como contêineres e formulários de configuração.

- [x] `src/components/Configuracoes.vue`
- [x] `src/components/ConfiguracoesGeral.vue`
- [x] `src/components/ConfiguracoesEmpresa.vue`
- [x] `src/components/ConfiguracoesContratos.vue`
- [x] `src/components/AdminSync.vue`
- [x] `src/components/Auth.vue`
- [x] `src/components/PortalCliente.vue`
- [x] `src/components/EngenhariaList.vue`
- [x] `src/components/EstimativaWizard.vue`

## Checklist de Conformidade por Arquivo:
Para cada arquivo refatorado, os agentes devem garantir rigorosamente que:
1. Nenhuma classe `shadow-*` permaneceu no arquivo. A profundidade vem das hairlines (`border`).
2. Todo elemento que tinha background fixo (ex: `bg-white`) recebeu seu equivalente dark (ex: `dark:bg-[#0f1011]`).
3. O Fundo primário utiliza `bg-slate-50 dark:bg-[#010102]`.
4. Todas as bordas utilizam o padrão hairline: `border border-slate-200 dark:border-[#23252a]`.
5. Os CTAs primários foram migrados de `bg-emerald-600` ou `bg-indigo-600` para `bg-[#5e6ad2] hover:bg-[#828fff] text-white`.
6. Inputs, selects e textareas adotaram o focus ring lavanda: `focus:ring-[#5e6ad2]/50 focus:border-[#5e6ad2]`.
7. A lógica, os eventos (`@click`, etc.) e estados do Vue **NÃO FORAM MODIFICADOS** de forma alguma.
