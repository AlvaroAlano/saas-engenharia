<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { Archive, X, Search, Loader2, Calendar, ArchiveRestore, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})
const emit = defineEmits(['close', 'projeto-restaurado'])

const searchQuery = ref('')
const isLoading = ref(false)
const projetosArquivados = ref([])

const carregarArquivados = async () => {
  isLoading.value = true
  try {
    const res = await axios.get('/projetos-arquivados')
    if (res.data.success) {
      projetosArquivados.value = res.data.data
    }
  } catch (error) {
    console.error('Erro ao buscar projetos arquivados:', error)
  } finally {
    isLoading.value = false
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    carregarArquivados()
  }
})

const projetosFiltrados = computed(() => {
  if (!searchQuery.value) return projetosArquivados.value
  
  const query = searchQuery.value.toLowerCase()
  return projetosArquivados.value.filter(p => 
    (p.nome && p.nome.toLowerCase().includes(query)) || 
    (p.cliente && p.cliente.toLowerCase().includes(query))
  )
})

const restaurarProjeto = async (id) => {
  try {
    const p = projetosArquivados.value.find(proj => proj.id === id)
    const colunaAtual = p?.coluna || 'estimativa_enviada'
    let novoStatus = 'aguardando_cliente'
    
    if (colunaAtual === 'contrato_pendente') novoStatus = 'docs_validados'
    else if (colunaAtual === 'engenharia_caixa') novoStatus = 'em_analise_caixa'
    else if (colunaAtual === 'obra_liberada') novoStatus = 'liberada'

    await axios.patch(`/projetos/${id}`, { 
      status: novoStatus,
      coluna: colunaAtual
    })
    // Remove localmente para reatividade e UX impecável
    projetosArquivados.value = projetosArquivados.value.filter(proj => proj.id !== id)
    emit('projeto-restaurado', id)
  } catch (error) {
    console.error('Erro ao restaurar projeto:', error)
    alert('Erro ao restaurar projeto.')
  }
}

const excluirDefinitivamente = async (id) => {
  if (!confirm('Atenção: Esta ação excluirá permanentemente o projeto e todos os seus itens associados. Deseja realmente excluir?')) return
  try {
    await axios.delete(`/projetos/${id}`)
    projetosArquivados.value = projetosArquivados.value.filter(p => p.id !== id)
  } catch (error) {
    console.error('Erro ao excluir projeto:', error)
    alert('Erro ao excluir projeto permanentemente.')
  }
}

const closeDrawer = () => {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <!-- 1. Overlay (Fundo escurecido) com animação de Fade -->
    <Transition
      enter-active-class="transition-opacity duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-300 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div 
        v-if="isOpen" 
        class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100]" 
        @click="closeDrawer"
      ></div>
    </Transition>

    <!-- 2. Gaveta Deslizante com animação de Slide (Top -> Down) -->
    <Transition
      enter-active-class="transition-transform duration-300 ease-out"
      enter-from-class="-translate-y-full"
      enter-to-class="translate-y-0"
      leave-active-class="transition-transform duration-300 ease-in"
      leave-from-class="translate-y-0"
      leave-to-class="-translate-y-full"
    >
      <div 
        v-if="isOpen" 
        class="fixed top-0 inset-x-0 bg-canvas z-[101] rounded-b-3xl max-h-[90vh] overflow-y-auto border-b border-hairline"
      >
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
          
          <!-- Cabeçalho da Gaveta -->
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
              <Archive class="w-7 h-7 sm:w-8 sm:h-8 text-ink-muted" stroke-width="1.5" />
              <h2 class="text-xl sm:text-2xl font-bold text-ink">Projetos Arquivados</h2>
            </div>
            <button @click="closeDrawer" class="p-2 rounded-xl bg-canvas text-ink-muted hover:bg-surface-hover hover:text-ink transition-colors cursor-pointer">
              <X class="w-6 h-6" stroke-width="1.5" />
            </button>
          </div>

          <!-- Barra de Pesquisa -->
          <div class="mb-6 relative max-w-2xl">
            <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-ink-muted w-5 h-5" stroke-width="1.5" />
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Pesquisar por nome da obra ou cliente..." 
              class="w-full pl-12 pr-4 py-3 sm:py-3.5 bg-surface border border-hairline rounded-xl focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all text-sm sm:text-base text-ink"
            />
          </div>

          <!-- Lista de Resultados -->
          <div class="space-y-3">
            <!-- Estado de Carregamento -->
            <div v-if="isLoading" class="text-center py-12 bg-surface rounded-xl border border-hairline">
              <Loader2 class="w-10 h-10 text-brand-primary animate-spin mx-auto mb-2" stroke-width="1.5" />
              <p class="text-ink-muted font-medium">Buscando projetos arquivados...</p>
            </div>

            <!-- Estado Vazio -->
            <div v-else-if="projetosFiltrados.length === 0" class="text-center py-12 bg-surface rounded-xl border border-dashed border-hairline">
              <Search class="w-10 h-10 text-ink-muted mx-auto mb-2" stroke-width="1.5" />
              <p class="text-ink-muted font-medium">Nenhum projeto encontrado com "{{ searchQuery }}".</p>
            </div>

            <!-- Itens da Lista -->
            <div 
              v-for="projeto in projetosFiltrados" 
              :key="projeto.id"
              class="bg-surface p-4 sm:p-5 rounded-xl border border-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all hover:border-brand-primary group"
            >
              <div>
                <h3 class="text-base font-bold text-ink group-hover:text-brand-primary transition-colors">{{ projeto.nome }}</h3>
                <div class="flex items-center gap-2 mt-1 text-sm text-ink-muted">
                  <span class="font-medium">Cliente:</span> {{ projeto.cliente }}
                  <span class="text-ink-muted">•</span>
                  <span class="flex items-center gap-1"><Calendar class="w-3.5 h-3.5" stroke-width="1.5" /> {{ projeto.data }}</span>
                </div>
              </div>
              
              <div class="flex items-center gap-2 shrink-0">
                <button 
                  @click="restaurarProjeto(projeto.id)"
                  class="flex-1 sm:flex-none px-4 py-2 bg-surface border border-hairline text-ink rounded-lg hover:bg-brand-primary/10 hover:text-brand-primary hover:border-brand-primary/30 transition-colors text-sm font-semibold flex items-center justify-center gap-2 cursor-pointer"
                >
                  <ArchiveRestore class="w-[18px] h-[18px]" stroke-width="1.5" />
                  Restaurar
                </button>
                <button 
                  @click="excluirDefinitivamente(projeto.id)"
                  class="flex-1 sm:flex-none px-4 py-2 bg-red-50 dark:bg-red-950/20 text-red-655 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/40 hover:text-red-700 dark:hover:text-red-300 transition-colors text-sm font-semibold flex items-center justify-center gap-2 border border-transparent dark:border-red-900/20 cursor-pointer"
                >
                  <Trash2 class="w-[18px] h-[18px]" stroke-width="1.5" />
                  <span class="hidden sm:inline">Excluir</span>
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>