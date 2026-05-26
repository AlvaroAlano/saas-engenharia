<script setup>
import { ref, onMounted, computed } from 'vue'
import { formatCurrency } from '../utils/formatters'
import { useRouter } from 'vue-router'
import axios from 'axios'
import Sidebar from './Sidebar.vue'
import TopHeader from './TopHeader.vue'
import { Search, Loader2, HardHat, Building } from 'lucide-vue-next'

const router = useRouter()
const projects = ref([])
const isLoading = ref(true)
const searchQuery = ref('')

const fetchProjects = async () => {
  isLoading.value = true
  try {
    const response = await axios.get('/api/projetos')
    projects.value = response.data
  } catch (error) {
    console.error('Erro ao buscar projetos:', error)
  } finally {
    isLoading.value = false
  }
}

// Lógica Simplificada: Apenas Engenharia & Caixa + Busca
const filteredProjects = computed(() => {
  return projects.value.filter(project => {
    // 1. Filtro estrito pela fase correta do Kanban
    if (project.coluna !== 'engenharia_caixa') return false

    // 2. Filtro de Busca por Texto
    const term = (searchQuery.value || '').toLowerCase().trim()
    if (term) {
      const nomeObra = (project.nome_obra || project.titulo_projeto || '').toLowerCase()
      const nomeCliente = (project.cliente_nome || '').toLowerCase()
      if (!nomeObra.includes(term) && !nomeCliente.includes(term)) return false
    }
    
    return true
  })
})

onMounted(() => {
  fetchProjects()
})

const goToProject = (id) => {
  router.push(`/orcamento/${id}`)
}

// Local formatCurrency removed (imported from formatters.js)
</script>

<template>
  <div class="bg-canvas text-ink font-sans min-h-screen overflow-x-hidden">
    <Sidebar />
    <main class="ml-0 lg:ml-64 min-h-screen w-full lg:w-[calc(100vw-16rem)] transition-all duration-300">
      <TopHeader />
      
      <div class="p-8">
        <!-- Header Section Simplificado -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 class="text-2xl font-bold text-ink tracking-tight">Obras em Engenharia</h1>
            <p class="text-ink-muted text-sm mt-1">Selecione uma obra para gerenciar o orçamento SINAPI.</p>
          </div>
          
          <div class="relative group">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted group-focus-within:text-brand-primary transition-colors w-5 h-5" stroke-width="1.5" />
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="Buscar obra ou cliente..." 
              class="pl-10 pr-4 py-2 bg-surface border border-hairline rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary transition-all w-80 text-ink"
            >
          </div>
        </div>

        <!-- Tabela Simplificada -->
        <div class="bg-surface border border-hairline rounded-2xl overflow-hidden">
          <div v-if="isLoading" class="flex flex-col items-center justify-center py-24 gap-4">
            <Loader2 class="w-10 h-10 animate-spin text-brand-primary" stroke-width="1.5" />
            <p class="text-ink-muted font-medium">Carregando obras...</p>
          </div>

          <div v-else-if="filteredProjects.length === 0" class="flex flex-col items-center justify-center py-24 px-6 text-center">
            <div class="w-16 h-16 bg-canvas rounded-full flex items-center justify-center mb-4 border border-hairline">
              <HardHat class="w-8 h-8 text-ink-muted" stroke-width="1.5" />
            </div>
            <h3 class="text-lg font-semibold text-ink tracking-tight">Nenhuma obra na fase de Engenharia.</h3>
            <p class="text-ink-muted text-sm mt-1 max-w-sm">Avance um projeto no Dashboard para começar a orçar.</p>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-canvas/50 border-b border-hairline">
                  <th class="px-6 py-4 text-[11px] font-bold text-ink-muted uppercase tracking-widest">Nome da Obra</th>
                  <th class="px-6 py-4 text-[11px] font-bold text-ink-muted uppercase tracking-widest">Cliente</th>
                  <th class="px-6 py-4 text-[11px] font-bold text-ink-muted uppercase tracking-widest text-center">Valor do Orçamento</th>
                  <th class="px-6 py-4 text-[11px] font-bold text-ink-muted uppercase tracking-widest text-right">Ação</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="project in filteredProjects" 
                  :key="project.id"
                  @click="goToProject(project.id)"
                  class="group border-b border-hairline hover:bg-surface-hover transition-colors cursor-pointer"
                >
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                      <div class="w-10 h-10 rounded-xl bg-canvas text-ink-muted flex items-center justify-center group-hover:bg-brand-primary group-hover:text-white transition-all">
                        <Building class="w-5 h-5" stroke-width="1.5" />
                      </div>
                      <span class="font-bold text-ink group-hover:text-brand-primary transition-colors leading-tight">{{ project.nome_obra || project.titulo_projeto || 'Sem nome' }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <span class="text-sm text-ink-muted font-semibold">{{ project.cliente_nome || 'Não definido' }}</span>
                  </td>
                  <td class="px-6 py-4 text-center">
                    <div v-if="project.valor" class="text-sm font-bold text-ink">
                      {{ formatCurrency(project.valor, null) }}
                    </div>
                    <div v-else class="px-2 py-1 bg-canvas text-ink-muted rounded text-[10px] font-bold uppercase inline-block border border-hairline">
                      Não iniciado
                    </div>
                  </td>
                  <td class="px-6 py-4 text-right">
                    <button class="px-4 py-2 bg-surface border border-hairline rounded-lg text-xs font-bold text-ink-muted group-hover:border-brand-primary group-hover:text-brand-primary transition-all">
                      ABRIR ORÇAMENTO
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
</style>
