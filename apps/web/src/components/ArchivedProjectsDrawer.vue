<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import {
  Archive, X, Search, Loader2, Calendar, ArchiveRestore, Trash2,
  AlertTriangle, CheckCircle2, CheckSquare, Square, FolderOpen, Eye
} from 'lucide-vue-next'
import { useToast } from '../composables/useToast'
import DrawerDetalheProjeto from './DrawerDetalheProjeto.vue'

const { showToast } = useToast()

const props = defineProps({
  isOpen: { type: Boolean, default: false }
})
const emit = defineEmits(['close', 'projeto-restaurado'])

// ─── state ───────────────────────────────────────────────────────────────────
const searchQuery  = ref('')
const isLoading    = ref(false)
const projetosArquivados = ref([])
const selectedIds  = ref(new Set())

// delete modal
const deleteModal = ref({ isOpen: false, isDeleting: false, isDone: false })

// ─── data fetching ────────────────────────────────────────────────────────────
const carregarArquivados = async () => {
  isLoading.value = true
  selectedIds.value = new Set()
  try {
    const res = await axios.get('/projetos-arquivados')
    if (res.data.success) projetosArquivados.value = res.data.data
  } catch (e) {
    console.error('Erro ao buscar projetos arquivados:', e)
  } finally {
    isLoading.value = false
  }
}

watch(() => props.isOpen, (v) => { if (v) carregarArquivados() })

// ─── computed ─────────────────────────────────────────────────────────────────
const projetosFiltrados = computed(() => {
  if (!searchQuery.value) return projetosArquivados.value
  const q = searchQuery.value.toLowerCase()
  return projetosArquivados.value.filter(p =>
    (p.nome   && p.nome.toLowerCase().includes(q)) ||
    (p.cliente && p.cliente.toLowerCase().includes(q))
  )
})

const totalSelecionados = computed(() => selectedIds.value.size)
const todosSelcionados  = computed(() =>
  projetosFiltrados.value.length > 0 &&
  projetosFiltrados.value.every(p => selectedIds.value.has(p.id))
)
const algunsSelecionados = computed(() =>
  totalSelecionados.value > 0 && !todosSelcionados.value
)

// ─── selection ────────────────────────────────────────────────────────────────
const toggleSelect = (id) => {
  const s = new Set(selectedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedIds.value = s
}

const toggleSelectAll = () => {
  if (todosSelcionados.value) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(projetosFiltrados.value.map(p => p.id))
  }
}

const limparSelecao = () => { selectedIds.value = new Set() }

// ─── helpers ──────────────────────────────────────────────────────────────────
const statusDeRestauracao = (coluna) => {
  if (coluna === 'contrato_pendente') return 'docs_validados'
  if (coluna === 'engenharia_caixa')  return 'em_analise_caixa'
  if (coluna === 'obra_liberada')      return 'liberada'
  return 'aguardando_cliente'
}

// ─── actions: restore ─────────────────────────────────────────────────────────
const isRestoring = ref(false)

const restaurarProjeto = async (id) => {
  const p = projetosArquivados.value.find(x => x.id === id)
  const coluna = p?.coluna || 'estimativa_enviada'
  try {
    await axios.patch(`/projetos/${id}`, { status: statusDeRestauracao(coluna), coluna })
    projetosArquivados.value = projetosArquivados.value.filter(x => x.id !== id)
    const s = new Set(selectedIds.value); s.delete(id); selectedIds.value = s
    emit('projeto-restaurado', id)
    showToast('Projeto restaurado com sucesso!', 'success')
  } catch (e) {
    console.error('Erro ao restaurar:', e)
    showToast('Erro ao restaurar projeto.', 'error')
  }
}

const restaurarSelecionados = async () => {
  if (!totalSelecionados.value) return
  isRestoring.value = true
  const ids = [...selectedIds.value]
  let ok = 0
  try {
    for (const id of ids) {
      const p = projetosArquivados.value.find(x => x.id === id)
      const coluna = p?.coluna || 'estimativa_enviada'
      await axios.patch(`/projetos/${id}`, { status: statusDeRestauracao(coluna), coluna })
      projetosArquivados.value = projetosArquivados.value.filter(x => x.id !== id)
      emit('projeto-restaurado', id)
      ok++
    }
    selectedIds.value = new Set()
    showToast(`${ok} projeto(s) restaurado(s) com sucesso!`, 'success')
  } catch (e) {
    console.error('Erro ao restaurar em massa:', e)
    showToast('Ocorreu um erro durante a restauração.', 'error')
  } finally {
    isRestoring.value = false
  }
}

// ─── actions: delete ──────────────────────────────────────────────────────────
// ids pendentes de exclusão (pode ser [id] individual ou todos selecionados)
const idsParaExcluir = ref([])

const abrirModalExclusao = (ids) => {
  idsParaExcluir.value = ids
  deleteModal.value = { isOpen: true, isDeleting: false, isDone: false }
}

const fecharModalExclusao = () => {
  if (deleteModal.value.isDeleting) return
  deleteModal.value.isOpen = false
  idsParaExcluir.value = []
}

const confirmarExclusao = async () => {
  deleteModal.value.isDeleting = true
  const ids = [...idsParaExcluir.value]
  let ok = 0
  try {
    for (const id of ids) {
      await axios.delete(`/projetos/${id}`)
      projetosArquivados.value = projetosArquivados.value.filter(p => p.id !== id)
      const s = new Set(selectedIds.value); s.delete(id); selectedIds.value = s
      ok++
    }
    deleteModal.value.isDone = true
    showToast(`${ok} projeto(s) excluído(s) permanentemente.`, 'success')
    setTimeout(() => fecharModalExclusao(), 900)
  } catch (e) {
    console.error('Erro ao excluir:', e)
    showToast('Erro ao excluir projeto.', 'error')
    deleteModal.value.isDeleting = false
  }
}

// ─── badge por coluna ─────────────────────────────────────────────────────────
const colunaBadge = {
  estimativa_enviada: { label: 'Estimativa Enviada',  cls: 'bg-orange-50 text-orange-600 border-orange-100 dark:bg-orange-950/20 dark:text-orange-400 dark:border-orange-900/30' },
  contrato_pendente:  { label: 'Contrato Pendente',   cls: 'bg-blue-50 text-blue-600 border-blue-100 dark:bg-blue-950/20 dark:text-blue-400 dark:border-blue-900/30' },
  engenharia_caixa:   { label: 'Engenharia & Caixa',  cls: 'bg-indigo-50 text-indigo-600 border-indigo-100 dark:bg-indigo-950/20 dark:text-indigo-400 dark:border-indigo-900/30' },
  obra_liberada:      { label: 'Obra Liberada',        cls: 'bg-violet-50 text-violet-600 border-violet-100 dark:bg-violet-950/20 dark:text-violet-400 dark:border-violet-900/30' },
}

const colunaLeftBorder = {
  estimativa_enviada: 'border-l-orange-400',
  contrato_pendente:  'border-l-blue-500',
  engenharia_caixa:   'border-l-indigo-500',
  obra_liberada:      'border-l-violet-500',
}

const formatDate = (d) => {
  if (!d) return '—'
  try { return new Date(d).toLocaleDateString('pt-BR') } catch { return d }
}

// ─── detalhe do projeto ───────────────────────────────────────────────────────
const projetoDetalhado  = ref(null)
const isDetalheOpen     = ref(false)

const abrirDetalhe = (projeto) => {
  projetoDetalhado.value = projeto
  isDetalheOpen.value = true
}

const fecharDetalhe = () => {
  isDetalheOpen.value = false
  projetoDetalhado.value = null
}

// nome do(s) projeto(s) a excluir — para exibir no modal
const nomesParaExcluir = computed(() => {
  if (!idsParaExcluir.value.length) return []
  return idsParaExcluir.value.map(id => {
    const p = projetosArquivados.value.find(x => x.id === id)
    return p?.nome || p?.titulo_projeto || 'Projeto'
  })
})
</script>

<template>
  <Teleport to="body">
    <!-- Overlay -->
    <Transition
      enter-active-class="transition-opacity duration-300 ease-out"
      enter-from-class="opacity-0" enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-300 ease-in"
      leave-from-class="opacity-100" leave-to-class="opacity-0"
    >
      <div v-if="isOpen" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100]" @click="emit('close')" />
    </Transition>

    <!-- Gaveta deslizante -->
    <Transition
      enter-active-class="transition-transform duration-300 ease-out"
      enter-from-class="-translate-y-full" enter-to-class="translate-y-0"
      leave-active-class="transition-transform duration-300 ease-in"
      leave-from-class="translate-y-0" leave-to-class="-translate-y-full"
    >
      <div
        v-if="isOpen"
        class="fixed top-0 inset-x-0 bg-canvas z-[101] rounded-b-3xl max-h-[90vh] overflow-y-auto border-b border-hairline shadow-2xl"
      >
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">

          <!-- Cabeçalho -->
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-surface border border-hairline flex items-center justify-center shrink-0">
                <Archive class="w-5 h-5 text-ink-muted" stroke-width="1.5" />
              </div>
              <div>
                <h2 class="text-xl sm:text-2xl font-bold text-ink leading-tight">Projetos Arquivados</h2>
                <p class="text-xs text-ink-muted font-medium mt-0.5">
                  {{ projetosArquivados.length }} projeto{{ projetosArquivados.length !== 1 ? 's' : '' }} arquivado{{ projetosArquivados.length !== 1 ? 's' : '' }}
                </p>
              </div>
            </div>
            <button @click="emit('close')" class="p-2 rounded-xl text-ink-muted hover:bg-surface-hover hover:text-ink transition-colors cursor-pointer">
              <X class="w-6 h-6" stroke-width="1.5" />
            </button>
          </div>

          <!-- Barra de pesquisa + Selecionar todos -->
          <div class="mb-4 flex items-center gap-3">
            <!-- Search -->
            <div class="relative flex-1 max-w-2xl">
              <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-ink-muted w-4 h-4 pointer-events-none" stroke-width="1.5" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Pesquisar por nome ou cliente..."
                class="w-full pl-11 pr-4 py-2.5 bg-surface border border-hairline rounded-xl focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all text-sm text-ink placeholder:text-ink-muted"
              />
            </div>

            <!-- Selecionar todos (só aparece quando há itens) -->
            <button
              v-if="projetosFiltrados.length > 0 && !isLoading"
              @click="toggleSelectAll"
              class="flex items-center gap-2 px-3.5 py-2.5 rounded-xl border border-hairline bg-surface hover:bg-surface-hover text-ink-muted hover:text-ink transition-colors text-xs font-semibold shrink-0 cursor-pointer"
            >
              <component
                :is="todosSelcionados ? CheckSquare : Square"
                class="w-4 h-4"
                :class="todosSelcionados ? 'text-brand-primary' : algunsSelecionados ? 'text-brand-primary opacity-60' : ''"
                stroke-width="1.5"
              />
              {{ todosSelcionados ? 'Desmarcar todos' : 'Selecionar todos' }}
            </button>
          </div>

          <!-- Barra de ações em massa (aparece ao selecionar) -->
          <Transition
            enter-active-class="transition-all duration-200 ease-out"
            enter-from-class="opacity-0 -translate-y-2 scale-98"
            enter-to-class="opacity-100 translate-y-0 scale-100"
            leave-active-class="transition-all duration-150 ease-in"
            leave-from-class="opacity-100 translate-y-0 scale-100"
            leave-to-class="opacity-0 -translate-y-2 scale-98"
          >
            <div
              v-if="totalSelecionados > 0"
              class="mb-4 flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-surface border border-brand-primary/30 shadow-sm"
            >
              <div class="flex items-center gap-2">
                <div class="w-5 h-5 rounded-full bg-brand-primary/15 flex items-center justify-center shrink-0">
                  <span class="text-[10px] font-bold text-brand-primary">{{ totalSelecionados }}</span>
                </div>
                <span class="text-sm font-semibold text-ink">
                  {{ totalSelecionados }} projeto{{ totalSelecionados > 1 ? 's' : '' }} selecionado{{ totalSelecionados > 1 ? 's' : '' }}
                </span>
                <button @click="limparSelecao" class="text-xs text-ink-muted hover:text-ink transition-colors underline underline-offset-2 cursor-pointer ml-1">
                  Limpar
                </button>
              </div>

              <div class="flex items-center gap-2">
                <button
                  @click="restaurarSelecionados"
                  :disabled="isRestoring"
                  class="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-hairline bg-canvas hover:bg-surface-hover text-ink text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  <Loader2 v-if="isRestoring" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
                  <ArchiveRestore v-else class="w-3.5 h-3.5" stroke-width="1.5" />
                  Restaurar
                </button>
                <button
                  @click="abrirModalExclusao([...selectedIds])"
                  class="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-semibold transition-colors cursor-pointer"
                >
                  <Trash2 class="w-3.5 h-3.5" stroke-width="1.5" />
                  Excluir selecionados
                </button>
              </div>
            </div>
          </Transition>

          <!-- Conteúdo principal -->
          <div class="space-y-2">

            <!-- Carregando -->
            <div v-if="isLoading" class="text-center py-16 bg-surface rounded-xl border border-hairline">
              <Loader2 class="w-9 h-9 text-brand-primary animate-spin mx-auto mb-3" stroke-width="1.5" />
              <p class="text-sm text-ink-muted font-medium">Carregando projetos arquivados...</p>
            </div>

            <!-- Vazio -->
            <div v-else-if="projetosArquivados.length === 0" class="text-center py-16 bg-surface rounded-xl border border-dashed border-hairline">
              <div class="w-14 h-14 rounded-2xl bg-canvas border border-hairline flex items-center justify-center mx-auto mb-4">
                <FolderOpen class="w-7 h-7 text-ink-muted" stroke-width="1.5" />
              </div>
              <p class="text-sm font-semibold text-ink mb-1">Nenhum projeto arquivado</p>
              <p class="text-xs text-ink-muted">Projetos arquivados aparecerão aqui.</p>
            </div>

            <!-- Sem resultados na busca -->
            <div v-else-if="projetosFiltrados.length === 0" class="text-center py-14 bg-surface rounded-xl border border-dashed border-hairline">
              <Search class="w-9 h-9 text-ink-muted mx-auto mb-3" stroke-width="1.5" />
              <p class="text-sm text-ink-muted font-medium">Nenhum resultado para <strong class="text-ink">"{{ searchQuery }}"</strong></p>
            </div>

            <!-- Cards dos projetos -->
            <div
              v-for="projeto in projetosFiltrados"
              :key="projeto.id"
              :class="[
                'group relative bg-surface border border-l-4 rounded-xl p-4 transition-all hover:shadow-sm',
                selectedIds.has(projeto.id)
                  ? 'border-brand-primary/40 bg-brand-primary/[0.02] shadow-sm'
                  : 'border-hairline hover:border-neutral-500/40',
                colunaLeftBorder[projeto.coluna] || 'border-l-slate-300'
              ]"
            >
              <div class="flex items-center gap-3">

                <!-- Checkbox -->
                <button
                  @click="toggleSelect(projeto.id)"
                  class="shrink-0 w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all cursor-pointer focus:outline-none"
                  :class="selectedIds.has(projeto.id)
                    ? 'border-brand-primary bg-brand-primary text-white'
                    : 'border-hairline bg-canvas hover:border-brand-primary/60 text-transparent'"
                  :aria-label="selectedIds.has(projeto.id) ? 'Desmarcar' : 'Selecionar'"
                >
                  <CheckCircle2 class="w-3 h-3" stroke-width="3" />
                </button>

                <!-- Info do projeto -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="text-[10px] font-bold text-ink-muted uppercase tracking-wider truncate">
                        {{ projeto.cliente || '—' }}
                      </p>
                      <h3 class="text-sm font-semibold text-ink mt-0.5 leading-snug truncate">
                        {{ projeto.nome || projeto.titulo_projeto || '—' }}
                      </h3>
                    </div>

                    <!-- Badge de fase + Data -->
                    <div class="flex flex-col items-end gap-1.5 shrink-0">
                      <span
                        v-if="colunaBadge[projeto.coluna]"
                        :class="['text-[10px] font-bold px-2 py-0.5 rounded-md border uppercase tracking-wider', colunaBadge[projeto.coluna].cls]"
                      >
                        {{ colunaBadge[projeto.coluna].label }}
                      </span>
                      <span class="flex items-center gap-1 text-[10px] text-ink-muted font-medium">
                        <Calendar class="w-3 h-3 shrink-0" stroke-width="1.5" />
                        {{ formatDate(projeto.data || projeto.created_at) }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Ações individuais -->
                <div class="flex items-center gap-1.5 shrink-0 ml-1">
                  <button
                    @click="abrirDetalhe(projeto)"
                    title="Ver detalhamento do projeto"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-hairline bg-canvas hover:bg-blue-50 dark:hover:bg-blue-950/20 hover:border-blue-200 dark:hover:border-blue-900/40 hover:text-blue-600 dark:hover:text-blue-400 text-ink-muted text-xs font-semibold transition-colors cursor-pointer whitespace-nowrap"
                  >
                    <Eye class="w-3.5 h-3.5" stroke-width="1.5" />
                    <span class="hidden sm:inline">Detalhes</span>
                  </button>
                  <button
                    @click="restaurarProjeto(projeto.id)"
                    title="Restaurar projeto"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-hairline bg-canvas hover:bg-surface-hover text-ink text-xs font-semibold transition-colors cursor-pointer whitespace-nowrap"
                  >
                    <ArchiveRestore class="w-3.5 h-3.5" stroke-width="1.5" />
                    <span class="hidden sm:inline">Restaurar</span>
                  </button>
                  <button
                    @click="abrirModalExclusao([projeto.id])"
                    title="Excluir permanentemente"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-transparent bg-red-50 dark:bg-red-950/20 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <Trash2 class="w-3.5 h-3.5" stroke-width="1.5" />
                    <span class="hidden sm:inline">Excluir</span>
                  </button>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </Transition>

    <!-- ─── Modal de Confirmação de Exclusão Permanente ──────────────────────── -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="deleteModal.isOpen"
        class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        @click.self="fecharModalExclusao"
      >
        <div class="bg-surface rounded-2xl border border-hairline shadow-2xl w-full max-w-md overflow-hidden text-ink">

          <!-- Header -->
          <div class="px-6 py-5 border-b border-hairline flex items-center gap-3.5 bg-red-50 dark:bg-red-950/20">
            <div class="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/40 flex items-center justify-center shrink-0">
              <Trash2 class="w-5 h-5 text-red-600 dark:text-red-400" stroke-width="1.5" />
            </div>
            <div>
              <h3 class="text-base font-bold text-ink">Excluir permanentemente</h3>
              <p class="text-xs text-red-600 dark:text-red-400 font-semibold mt-0.5">Esta ação não pode ser desfeita</p>
            </div>
          </div>

          <!-- Body -->
          <div class="px-6 py-5 space-y-4">

            <!-- Aviso de perigo -->
            <div class="flex items-start gap-3 p-3.5 rounded-xl bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/30">
              <AlertTriangle class="w-4 h-4 text-red-600 dark:text-red-400 shrink-0 mt-0.5" stroke-width="1.5" />
              <p class="text-xs text-red-700 dark:text-red-300 leading-relaxed font-medium">
                Todos os dados, documentos, orçamentos e histórico deste projeto serão
                <strong>apagados para sempre</strong>. Não há como recuperar após a exclusão.
              </p>
            </div>

            <!-- Lista de projetos que serão excluídos -->
            <div>
              <p class="text-xs font-semibold text-ink-muted uppercase tracking-wider mb-2">
                {{ nomesParaExcluir.length === 1 ? 'Projeto que será excluído' : `${nomesParaExcluir.length} projetos que serão excluídos` }}
              </p>
              <ul class="space-y-1.5 max-h-40 overflow-y-auto">
                <li
                  v-for="nome in nomesParaExcluir"
                  :key="nome"
                  class="flex items-center gap-2 px-3 py-2 rounded-lg bg-canvas border border-hairline text-xs font-medium text-ink"
                >
                  <Archive class="w-3.5 h-3.5 text-ink-muted shrink-0" stroke-width="1.5" />
                  {{ nome }}
                </li>
              </ul>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 bg-canvas border-t border-hairline flex items-center justify-end gap-3">
            <button
              @click="fecharModalExclusao"
              :disabled="deleteModal.isDeleting"
              class="px-4 py-2 rounded-lg text-sm font-semibold text-ink-muted hover:text-ink hover:bg-surface-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              Cancelar
            </button>
            <button
              @click="confirmarExclusao"
              :disabled="deleteModal.isDeleting || deleteModal.isDone"
              :class="[
                'flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-bold transition-all cursor-pointer disabled:cursor-not-allowed',
                deleteModal.isDone
                  ? 'bg-emerald-600 text-white border-transparent'
                  : 'bg-red-600 hover:bg-red-700 text-white disabled:bg-red-400'
              ]"
            >
              <Loader2 v-if="deleteModal.isDeleting" class="w-4 h-4 animate-spin" stroke-width="1.5" />
              <CheckCircle2 v-else-if="deleteModal.isDone" class="w-4 h-4" stroke-width="1.5" />
              <Trash2 v-else class="w-4 h-4" stroke-width="1.5" />
              {{
                deleteModal.isDeleting ? 'Excluindo...' :
                deleteModal.isDone     ? 'Excluído!'    :
                nomesParaExcluir.length === 1 ? 'Sim, excluir permanentemente' : `Sim, excluir ${nomesParaExcluir.length} projetos`
              }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Drawer de Detalhamento (z-index superior ao da gaveta de arquivados) -->
    <DrawerDetalheProjeto
      v-if="projetoDetalhado"
      :is-open="isDetalheOpen"
      :project="projetoDetalhado"
      :z-index="115"
      :is-arquivado="true"
      @close="fecharDetalhe"
      @update="() => {}"
    />
  </Teleport>
</template>
