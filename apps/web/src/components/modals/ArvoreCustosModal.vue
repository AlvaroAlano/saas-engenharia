<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { formatCurrency } from '../../utils/formatters'
import { useFases } from '../../composables/useFases'
import {
  Network,
  Plus,
  Loader2,
  Trash2,
  X,
  Search,
  SearchCode,
  Package,
  Check,
  ChevronDown,
  AlertTriangle,
  HardHat, Layers, Building, Zap, Paintbrush,
  Wrench, Home, Settings2, LayoutGrid
} from 'lucide-vue-next'

const iconMap = {
  engineering:   HardHat,
  foundation:    Layers,
  domain:        Building,
  electric_bolt: Zap,
  format_paint:  Paintbrush,
  wrench:        Wrench,
  home:          Home,
  package:       Package,
  settings:      Settings2,
  grid:          LayoutGrid,
}

const props = defineProps({
  isOpen:    { type: Boolean, required: true },
  items:     { type: Array,   default: () => [] },
  bdi:       { type: Number,  default: 0 },
  projectId: { type: String,  default: '' },
})

const emit = defineEmits(['close', 'refresh', 'add-manual-item', 'remove-item', 'update-quantity'])

const { fases, ensureFases } = useFases()
onMounted(ensureFases)

// --- Agrupamento ---
const itensPorEtapa = computed(() => {
  const map = {}
  for (const e of fases.value) {
    map[e.value] = props.items.filter(i => i.etapa_obra === e.value)
  }
  return map
})

const filteredItensPorEtapa = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return itensPorEtapa.value
  const result = {}
  for (const e of fases.value) {
    result[e.value] = (itensPorEtapa.value[e.value] || []).filter(i =>
      i.descricao?.toLowerCase().includes(q) ||
      i.codigo_sinapi?.toLowerCase().includes(q)
    )
  }
  return result
})

const etapasComItens = computed(() =>
  fases.value.filter(e => (filteredItensPorEtapa.value[e.value] || []).length > 0)
)

// --- Pesquisa ---
const searchQuery = ref('')

// --- Accordion (todas expandidas por padrão) ---
const expandedEtapas = ref(new Set(fases.value.map(e => e.value)))

// Sincroniza expandedEtapas quando fases carregam ou mudam
watch(fases, (f) => {
  expandedEtapas.value = new Set(f.map(e => e.value))
})

const toggleEtapa = (val) => {
  const s = new Set(expandedEtapas.value)
  s.has(val) ? s.delete(val) : s.add(val)
  expandedEtapas.value = s
}

// Auto-expande fases com resultados ao pesquisar
watch(searchQuery, (q) => {
  if (!q.trim()) {
    expandedEtapas.value = new Set(fases.value.map(e => e.value))
    return
  }
  const lower = q.toLowerCase()
  const expanded = new Set()
  for (const e of fases.value) {
    const hasMatch = (itensPorEtapa.value[e.value] || []).some(i =>
      i.descricao?.toLowerCase().includes(lower) ||
      i.codigo_sinapi?.toLowerCase().includes(lower)
    )
    if (hasMatch) expanded.add(e.value)
  }
  expandedEtapas.value = expanded
})

// --- Scroll lock + reset ao abrir/fechar ---
watch(() => props.isOpen, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
  if (val) {
    selectedIds.value = new Set()
    searchQuery.value = ''
    expandedEtapas.value = new Set(fases.value.map(e => e.value))
  }
})

// --- Seleção ---
const selectedIds = ref(new Set())
const isDeleting  = ref(false)

const allSelected = computed(() =>
  props.items.length > 0 && selectedIds.value.size === props.items.length
)
const someSelected = computed(() =>
  selectedIds.value.size > 0 && selectedIds.value.size < props.items.length
)

const toggleAll = () => {
  selectedIds.value = allSelected.value
    ? new Set()
    : new Set(props.items.map(i => i.id))
}

const toggleItem = (id) => {
  const s = new Set(selectedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedIds.value = s
}

// --- Exclusão em massa ---
const excluirSelecionados = async () => {
  if (!selectedIds.value.size) return
  isDeleting.value = true
  try {
    await Promise.all([...selectedIds.value].map(id =>
      axios.delete(`/projetos/${props.projectId}/itens/${id}`)
    ))
    selectedIds.value = new Set()
    emit('refresh')
  } catch (e) {
    console.error('Erro ao excluir itens:', e)
  } finally {
    isDeleting.value = false
  }
}

const excluirItem = (id) => {
  const s = new Set(selectedIds.value)
  s.delete(id)
  selectedIds.value = s
  emit('remove-item', id)
}

// --- Edição de quantidade inline ---
const editingItemId = ref(null)
const editQty       = ref(0)
let debounceTimer   = null
let isTabbing       = false

const orderedItems = computed(() =>
  fases.value.flatMap(e => itensPorEtapa.value[e.value] || [])
)

const startEdit = (item) => {
  editingItemId.value = item.id
  editQty.value       = item.quantidade === 0 ? null : item.quantidade
}

const commitEdit = (item) => {
  if (isTabbing) return
  clearTimeout(debounceTimer)
  const val = editQty.value
  if (val != null && val > 0 && val !== item.quantidade) {
    emit('update-quantity', item.id, val)
  }
  editingItemId.value = null
}

const tabToNext = (item) => {
  isTabbing = true
  clearTimeout(debounceTimer)
  const val = editQty.value
  if (val != null && val > 0 && val !== item.quantidade) {
    emit('update-quantity', item.id, val)
  }
  const list = orderedItems.value
  const idx = list.findIndex(i => i.id === item.id)
  const next = list[idx + 1]
  if (next) {
    if (!expandedEtapas.value.has(next.etapa_obra)) {
      const s = new Set(expandedEtapas.value)
      s.add(next.etapa_obra)
      expandedEtapas.value = s
    }
    startEdit(next)
  } else {
    editingItemId.value = null
  }
  setTimeout(() => { isTabbing = false }, 0)
}

const debouncedUpdate = (item) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    if (editQty.value > 0) {
      emit('update-quantity', item.id, editQty.value)
    }
  }, 600)
}

// --- ESC para fechar ---
const onKeydown = (e) => { if (e.key === 'Escape' && props.isOpen) emit('close') }
onMounted(()   => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))

// --- Totais ---
const subtotalEtapa = (key) =>
  itensPorEtapa.value[key].reduce((s, i) => s + i.quantidade * i.valor_unitario, 0)

const totalSemBdi = computed(() =>
  props.items.reduce((s, i) => s + i.quantidade * i.valor_unitario, 0)
)
const totalComBdi    = computed(() => totalSemBdi.value * (1 + props.bdi / 100))
const itensPendentes = computed(() => props.items.filter(i => i.quantidade == 0).length)

const selectedSubtotal = computed(() =>
  props.items
    .filter(i => selectedIds.value.has(i.id))
    .reduce((s, i) => s + i.quantidade * i.valor_unitario, 0)
)

const totalFiltrados = computed(() =>
  etapasComItens.value.reduce((n, e) => n + filteredItensPorEtapa.value[e.value].length, 0)
)

// --- Cores por etapa ---
const etapaColor = {
  amber:   { header: 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400', border: 'border-l-amber-400',   badge: 'bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400' },
  orange:  { header: 'bg-orange-50 dark:bg-orange-500/10 text-orange-700 dark:text-orange-400', border: 'border-l-orange-400',  badge: 'bg-orange-100 dark:bg-orange-500/20 text-orange-700 dark:text-orange-400' },
  blue:    { header: 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400', border: 'border-l-blue-400',    badge: 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400' },
  violet:  { header: 'bg-violet-50 dark:bg-violet-500/10 text-violet-700 dark:text-violet-400', border: 'border-l-violet-400',  badge: 'bg-violet-100 dark:bg-violet-500/20 text-violet-700 dark:text-violet-400' },
  emerald: { header: 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400', border: 'border-l-emerald-400', badge: 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400' },
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 bg-black/45 dark:bg-black/65 backdrop-blur-sm flex items-stretch lg:items-start lg:justify-center lg:p-5"
        style="z-index: 150;"
        @click.self="emit('close')"
      >
        <Transition
          enter-active-class="transition-all duration-300 ease-out"
          leave-active-class="transition-all duration-250 ease-in"
          enter-from-class="opacity-0 translate-y-full lg:translate-y-4 lg:scale-95"
          enter-to-class="opacity-100 translate-y-0 lg:scale-100"
          leave-from-class="opacity-100 translate-y-0 lg:scale-100"
          leave-to-class="opacity-0 translate-y-full lg:translate-y-4 lg:scale-95"
        >
          <div
            v-if="isOpen"
            class="bg-surface lg:border lg:border-hairline rounded-none lg:rounded-md lg:shadow-2xl flex flex-col w-full lg:max-w-6xl overflow-hidden h-full lg:h-auto lg:max-h-[calc(100vh-40px)]"
          >

            <!-- ===== HEADER ===== -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-hairline bg-surface shrink-0 gap-3">
              <div class="flex items-center gap-3 min-w-0">
                <div class="w-9 h-9 rounded-md bg-brand-blue/10 flex items-center justify-center shrink-0">
                  <Network class="w-5 h-5 text-brand-blue" stroke-width="1.5" />
                </div>
                <div class="min-w-0">
                  <h2 class="text-sm font-semibold text-ink uppercase tracking-wider truncate select-none">Árvore de Custos — Visão Completa</h2>
                  <p class="text-xs text-ink-muted mt-0.5 select-none font-sans">
                    {{ items.length }} itens
                    <span v-if="itensPendentes > 0" class="text-amber-500 font-semibold"> · {{ itensPendentes }} sem quantidade</span>
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-2 shrink-0">
                <!-- Item Manual -->
                <button
                  @click="emit('add-manual-item')"
                  class="hidden sm:flex items-center gap-1.5 h-9 px-3.5 bg-surface border border-hairline rounded-md text-xs font-medium text-ink hover:bg-surface-hover hover:text-ink transition-colors cursor-pointer select-none"
                >
                  <Plus class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
                  Item Manual
                </button>

                <!-- Excluir selecionados -->
                <Transition
                  enter-active-class="transition-all duration-200"
                  enter-from-class="opacity-0 scale-90"
                  enter-to-class="opacity-100 scale-100"
                  leave-active-class="transition-all duration-150"
                  leave-from-class="opacity-100 scale-100"
                  leave-to-class="opacity-0 scale-90"
                >
                  <button
                    v-if="selectedIds.size > 0"
                    @click="excluirSelecionados"
                    :disabled="isDeleting"
                    class="flex items-center gap-1.5 h-9 px-3.5 bg-red-600 hover:bg-red-700 text-white rounded-md text-xs font-medium transition-colors disabled:opacity-60 cursor-pointer disabled:cursor-not-allowed shadow-sm select-none"
                  >
                    <Loader2 v-if="isDeleting" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
                    <Trash2 v-else class="w-3.5 h-3.5" stroke-width="1.5" />
                    {{ isDeleting ? 'Excluindo...' : `Excluir ${selectedIds.size} ${selectedIds.size === 1 ? 'item' : 'itens'}` }}
                  </button>
                </Transition>

                <button
                  @click="emit('close')"
                  class="text-ink-muted hover:text-ink transition-colors p-1.5 rounded-md hover:bg-surface-hover flex items-center justify-center cursor-pointer select-none"
                  title="Fechar (Esc)"
                >
                  <X class="w-4 h-4" stroke-width="1.25" />
                </button>
              </div>
            </div>

            <!-- ===== BARRA DE PESQUISA ===== -->
            <div class="px-6 py-3 border-b border-hairline bg-surface shrink-0 flex items-center gap-2 select-none">
              <div class="relative flex-1">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted w-4 h-4 pointer-events-none" stroke-width="1.5" />
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Pesquisar insumo por descrição ou código SINAPI..."
                  class="w-full pl-9 pr-4 py-2 bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans"
                />
              </div>
              <button
                v-if="searchQuery"
                @click="searchQuery = ''"
                class="text-xs text-ink-muted hover:text-ink font-semibold px-2.5 py-1.5 rounded-md hover:bg-surface-hover transition-colors cursor-pointer shrink-0 flex items-center gap-1 font-sans"
              >
                <X class="w-3.5 h-3.5" stroke-width="1.5" />
                Limpar
              </button>
              <!-- Botões mobile -->
              <button
                @click="emit('add-manual-item')"
                class="sm:hidden p-2 rounded-md border border-hairline text-ink-muted hover:text-ink hover:bg-surface-hover transition-colors cursor-pointer shrink-0 flex items-center justify-center"
                title="Item Manual"
              >
                <Plus class="w-4 h-4" stroke-width="1.5" />
              </button>
            </div>

            <!-- ===== CORPO SCROLLÁVEL ===== -->
            <div class="flex-1 overflow-y-auto">

              <!-- Empty state: sem itens -->
              <div v-if="items.length === 0" class="flex flex-col items-center justify-center py-20 text-center select-none">
                <div class="w-16 h-16 rounded-md bg-brand-blue/10 flex items-center justify-center mb-4">
                  <Package class="w-8 h-8 text-brand-blue" stroke-width="1.5" />
                </div>
                <p class="text-sm font-bold text-ink">Nenhum item na árvore</p>
                <p class="text-xs text-ink-muted mt-1 font-sans">Adicione insumos do SINAPI ou aplique um template padrão.</p>
              </div>

              <!-- Empty state: pesquisa sem resultado -->
              <div v-else-if="etapasComItens.length === 0" class="flex flex-col items-center justify-center py-16 text-center px-4 select-none">
                <SearchCode class="w-12 h-12 text-ink-muted mb-3" stroke-width="1.5" />
                <p class="text-sm font-bold text-ink">Nenhum resultado</p>
                <p class="text-xs text-ink-muted mt-1 font-sans">Nenhum insumo encontrado para "<span class="font-semibold">{{ searchQuery }}</span>"</p>
                <button @click="searchQuery = ''" class="mt-3 text-xs text-blue-600 font-semibold hover:underline cursor-pointer font-sans">Limpar pesquisa</button>
              </div>

              <!-- Tabela -->
              <table v-else class="w-full text-xs border-collapse">
                <!-- Cabeçalho fixo -->
                <thead class="sticky top-0 z-10 bg-canvas border-b border-hairline select-none">
                  <tr>
                    <th class="py-3 pl-4 pr-2 w-10 text-left">
                      <div
                        class="w-4 h-4 rounded border flex items-center justify-center cursor-pointer transition-all"
                        :class="allSelected ? 'bg-brand-blue border-brand-blue' : someSelected ? 'bg-brand-blue/30 border-brand-blue' : 'border-neutral-400 bg-surface hover:border-brand-blue'"
                        @click="toggleAll"
                      >
                        <Check v-if="allSelected" class="w-3 h-3 text-white" stroke-width="2" />
                        <span v-else-if="someSelected" class="block w-2 h-0.5 bg-brand-blue rounded"></span>
                      </div>
                    </th>
                    <th class="py-3 px-3 text-left font-bold text-ink-muted uppercase tracking-wider text-[10px] w-20">Código</th>
                    <th class="py-3 px-3 text-left font-bold text-ink-muted uppercase tracking-wider text-[10px]">Descrição</th>
                    <th class="py-3 px-3 text-center font-bold text-ink-muted uppercase tracking-wider text-[10px] w-36">Quantidade</th>
                    <th class="py-3 px-3 text-right font-bold text-ink-muted uppercase tracking-wider text-[10px] w-28">Preço Unit.</th>
                    <th class="py-3 px-3 text-right font-bold text-ink-muted uppercase tracking-wider text-[10px] w-28">Subtotal</th>
                    <th class="py-3 pl-2 pr-4 w-10"></th>
                  </tr>
                </thead>

                <tbody>
                  <template v-for="etapa in etapasComItens" :key="etapa.value">

                    <!-- Cabeçalho da fase (sanfona) -->
                    <tr
                      class="cursor-pointer select-none"
                      @click="toggleEtapa(etapa.value)"
                    >
                      <td colspan="7" class="p-0 border-b border-hairline">
                        <div
                          class="flex items-center justify-between px-4 py-2.5 border-l-4"
                          :class="[etapaColor[etapa.color].header, etapaColor[etapa.color].border]"
                        >
                          <div class="flex items-center gap-2.5">
                            <component :is="iconMap[etapa.icon]" class="w-4 h-4" stroke-width="1.5" />
                            <span class="font-bold text-[11px] uppercase tracking-wider">{{ etapa.label }}</span>
                            <span
                              class="text-[10px] font-semibold px-1.5 py-0.5 rounded-md"
                              :class="etapaColor[etapa.color].badge"
                            >{{ filteredItensPorEtapa[etapa.value].length }}</span>
                          </div>
                          <div class="flex items-center gap-3">
                            <span class="text-[11px] font-bold font-mono tabular-nums">{{ formatCurrency(subtotalEtapa(etapa.value)) }}</span>
                            <ChevronDown
                              class="w-4 h-4 transition-transform duration-200"
                              :class="expandedEtapas.has(etapa.value) ? 'rotate-0' : '-rotate-90'"
                              stroke-width="1.5"
                            />
                          </div>
                        </div>
                      </td>
                    </tr>

                    <!-- Itens da fase -->
                    <tr
                      v-for="item in filteredItensPorEtapa[etapa.value]"
                      :key="item.id"
                      v-show="expandedEtapas.has(etapa.value)"
                      class="border-b border-hairline transition-colors group cursor-pointer"
                      :class="editingItemId === item.id
                        ? 'bg-brand-blue/[0.06] ring-1 ring-inset ring-brand-blue/15'
                        : selectedIds.has(item.id)
                          ? 'bg-brand-blue/[0.04]'
                          : 'hover:bg-canvas/60'"
                      @click="toggleItem(item.id)"
                    >
                      <!-- Checkbox -->
                      <td class="py-3 pl-4 pr-2" @click.stop="toggleItem(item.id)">
                        <div
                          class="w-4 h-4 rounded border flex items-center justify-center cursor-pointer transition-all select-none"
                          :class="selectedIds.has(item.id) ? 'bg-brand-blue border-brand-blue' : 'border-neutral-400 bg-surface hover:border-brand-blue'"
                        >
                          <Check v-if="selectedIds.has(item.id)" class="w-3 h-3 text-white" stroke-width="2" />
                        </div>
                      </td>

                      <!-- Código -->
                      <td class="py-3 px-3 select-all">
                        <span
                          v-if="item.codigo_sinapi && item.codigo_sinapi !== 'MANUAL'"
                          class="font-mono text-[10px] text-ink-muted bg-black/[0.04] dark:bg-neutral-800/60 px-1.5 py-0.5 rounded border border-hairline font-sans"
                        >{{ item.codigo_sinapi }}</span>
                        <span v-else class="text-[9px] font-bold text-ink-muted bg-black/[0.04] dark:bg-neutral-800/60 border border-hairline px-1.5 py-0.5 rounded uppercase tracking-tighter font-sans select-none">Manual</span>
                      </td>

                      <!-- Descrição -->
                      <td class="py-3 px-3 max-w-0 select-text">
                        <p class="font-semibold text-ink truncate" :title="item.descricao">{{ item.descricao }}</p>
                      </td>

                      <!-- Quantidade -->
                      <td class="py-3 px-3 text-center" @click.stop>
                        <div class="flex items-center justify-center gap-1 select-none">
                          <AlertTriangle
                            v-if="item.quantidade == 0 && editingItemId !== item.id"
                            class="w-3.5 h-3.5 text-amber-500"
                            stroke-width="1.5"
                          />
                          <input
                            v-if="editingItemId === item.id"
                            :ref="el => { if (el) nextTick(() => el.focus()) }"
                            v-model.number="editQty"
                            type="number"
                            min="0.01"
                            step="0.01"
                            @input="debouncedUpdate(item)"
                            @blur="commitEdit(item)"
                            @keyup.enter="commitEdit(item)"
                            @keydown.tab.prevent="tabToNext(item)"
                            class="w-20 text-center text-xs font-semibold bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-1 focus:outline-none focus:ring-2 focus:ring-brand-blue/40 font-sans"
                          />
                          <button
                            v-else
                            @click="startEdit(item)"
                            class="text-xs font-medium px-2 py-1 rounded-md border border-transparent transition-colors cursor-pointer tabular-nums font-sans"
                            :class="item.quantidade == 0
                              ? 'text-amber-600 bg-amber-500/10 hover:border-amber-300'
                              : 'text-brand-blue bg-brand-blue/10 hover:border-brand-blue/30'"
                          >{{ item.quantidade }} {{ item.unidade }}</button>
                        </div>
                      </td>

                      <!-- Preço unit. -->
                      <td class="py-3 px-3 text-right font-mono tabular-nums text-ink-muted select-text">
                        {{ formatCurrency(item.valor_unitario) }}
                      </td>

                      <!-- Subtotal -->
                      <td class="py-3 px-3 text-right font-mono tabular-nums font-bold text-ink select-text">
                        {{ formatCurrency(item.quantidade * item.valor_unitario) }}
                      </td>

                      <!-- Excluir -->
                      <td class="py-3 pl-2 pr-4" @click.stop>
                        <button
                          @click="excluirItem(item.id)"
                          class="p-1 rounded-md text-ink-muted/40 hover:text-red-600 hover:bg-red-500/10 group-hover:text-ink-muted transition-all cursor-pointer flex items-center justify-center select-none"
                          title="Excluir item"
                        >
                          <X class="w-3.5 h-3.5" stroke-width="1.5" />
                        </button>
                      </td>
                    </tr>

                  </template>
                </tbody>
              </table>
            </div>

            <!-- ===== FOOTER ===== -->
            <div class="shrink-0 border-t border-hairline px-6 py-4 bg-canvas select-none rounded-b-md">
              <div class="flex items-center justify-between gap-4">
                <p class="text-xs text-ink-muted font-sans">
                  <span v-if="selectedIds.size > 0" class="font-semibold text-brand-blue">
                    {{ selectedIds.size }} {{ selectedIds.size === 1 ? 'item selecionado' : 'itens selecionados' }}
                  </span>
                  <span v-else-if="searchQuery" class="font-semibold">
                    {{ totalFiltrados }} de {{ items.length }} itens visíveis
                  </span>
                  <span v-else class="hidden sm:inline">Clique nos itens para selecionar · clique na fase para recolher</span>
                </p>

                <div class="flex items-center gap-4 sm:gap-6 shrink-0 font-sans">
                  <!-- Subtotal dos selecionados (aparece ao selecionar) -->
                  <Transition
                    enter-active-class="transition-all duration-200"
                    enter-from-class="opacity-0 scale-90"
                    enter-to-class="opacity-100 scale-100"
                    leave-active-class="transition-all duration-150"
                    leave-from-class="opacity-100 scale-100"
                    leave-to-class="opacity-0 scale-90"
                  >
                    <div v-if="selectedIds.size > 0" class="text-right pr-4 border-r border-hairline">
                      <p class="text-[10px] text-ink-muted uppercase tracking-wider font-bold">Selecionados</p>
                      <p class="text-sm font-semibold text-brand-blue tabular-nums">{{ formatCurrency(selectedSubtotal) }}</p>
                    </div>
                  </Transition>

                  <div class="text-right hidden lg:block">
                    <p class="text-[10px] text-ink-muted uppercase tracking-wider font-bold">Subtotal</p>
                    <p class="text-sm font-semibold text-ink-muted tabular-nums">{{ formatCurrency(totalSemBdi) }}</p>
                  </div>
                  <div class="text-right hidden lg:block">
                    <p class="text-[10px] text-ink-muted uppercase tracking-wider font-bold">BDI {{ bdi }}%</p>
                    <p class="text-sm font-semibold text-brand-orange tabular-nums">+ {{ formatCurrency(totalComBdi - totalSemBdi) }}</p>
                  </div>
                  <div class="text-right pl-4 border-l border-hairline">
                    <p class="text-[10px] text-ink-muted uppercase tracking-wider font-bold">Total Final</p>
                    <p class="text-xl font-bold text-brand-blue tabular-nums">{{ formatCurrency(totalComBdi) }}</p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
