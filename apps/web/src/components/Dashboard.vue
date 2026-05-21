<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Sidebar from './Sidebar.vue'
import TopHeader from './TopHeader.vue'
import ProjectCard from './ProjectCard.vue'
import NovoClienteModal from './NovoClienteModal.vue'
import ArchivedProjectsDrawer from './ArchivedProjectsDrawer.vue'

const kanbanData = ref({
  estimativa_enviada: [],
  contrato_pendente: [],
  engenharia_caixa: [],
  obra_liberada: []
})
const isLoading = ref(true)
const isNewClientModalOpen = ref(false)
const isArchivedModalOpen = ref(false)

const columns = [
  { id: 'estimativa_enviada', title: 'ESTIMATIVA ENVIADA' },
  { id: 'contrato_pendente', title: 'CONTRATO PENDENTE' },
  { id: 'engenharia_caixa', title: 'ENGENHARIA & CAIXA' },
  { id: 'obra_liberada', title: 'OBRA LIBERADA' }
]

const fetchProjetos = async () => {
  isLoading.value = true
  try {
    const response = await axios.get('/projetos')
    
    const grouped = {
      estimativa_enviada: [],
      contrato_pendente: [],
      engenharia_caixa: [],
      obra_liberada: []
    }
    
    response.data.forEach(p => {
      if (grouped[p.coluna]) {
        grouped[p.coluna].push(p)
      }
    })
    
    kanbanData.value = grouped
  } catch (error) {
    console.error('Erro ao buscar projetos:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchProjetos()
})

const handleClientCreated = () => {
  isNewClientModalOpen.value = false
  fetchProjetos()
}
</script>

<template>
  <div class="bg-canvas text-ink font-sans min-h-screen overflow-x-hidden">
    <Sidebar />
    <main class="ml-0 lg:ml-64 min-h-screen w-full lg:w-[calc(100vw-16rem)] transition-all duration-300">
      <TopHeader @new-client="isNewClientModalOpen = true" @open-archived="isArchivedModalOpen = true" />
      
      <!-- Modal de Novo Cliente -->
      <NovoClienteModal 
        v-if="isNewClientModalOpen" 
        @close="isNewClientModalOpen = false" 
        @created="handleClientCreated" 
      />

      <!-- Gaveta de Projetos Arquivados -->
      <ArchivedProjectsDrawer 
        :is-open="isArchivedModalOpen" 
        @close="isArchivedModalOpen = false" 
        @projeto-restaurado="fetchProjetos"
      />
      
      <div class="p-4 lg:p-8">
        <!-- Metric Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div class="bg-surface border border-hairline p-6 flex flex-col justify-between group hover:border-brand-primary transition-all rounded-xl shadow-sm">
            <div>
              <p class="text-xs font-semibold tracking-wider text-ink-muted mb-1">ESTIMATIVAS ATIVAS</p>
              <div class="flex items-baseline gap-2">
                <h2 class="text-3xl font-bold text-ink">{{ kanbanData.estimativa_enviada.length }}</h2>
              </div>
            </div>
            <div class="mt-4 flex items-center gap-1 text-brand-primary font-medium text-xs">
              <span class="material-symbols-outlined text-sm">trending_up</span>
              <span>+2 esse mês</span>
            </div>
          </div>

          <div class="bg-surface border border-hairline p-6 flex flex-col justify-between group hover:border-brand-primary transition-all rounded-xl shadow-sm">
            <div>
              <p class="text-xs font-semibold tracking-wider text-ink-muted mb-1">APROVAÇÕES CAIXA</p>
              <h2 class="text-3xl font-bold text-ink">{{ kanbanData.obra_liberada.length }}<span class="text-xl text-ink-muted font-medium">/8</span></h2>
            </div>
            <div class="mt-4 flex items-center gap-3">
              <div class="flex-1 h-2 bg-canvas rounded-full overflow-hidden">
                <div class="h-full bg-brand-primary w-[62.5%] rounded-full"></div>
              </div>
              <span class="text-ink-muted text-xs font-medium">62%</span>
            </div>
          </div>

          <div class="bg-surface border border-hairline p-6 flex flex-col justify-between group hover:border-brand-primary transition-all rounded-xl shadow-sm">
            <div>
              <p class="text-xs font-semibold tracking-wider text-ink-muted mb-1">VGV GERENCIADO</p>
              <h2 class="text-3xl font-bold text-ink">R$ 4.2M</h2>
            </div>
            <div class="mt-4 flex items-center gap-1 text-brand-primary font-medium text-xs">
              <span class="material-symbols-outlined text-sm">auto_graph</span>
              <span>Alta no semestre</span>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex items-center justify-center py-20">
          <div class="flex flex-col items-center gap-4 text-ink-muted">
            <span class="material-symbols-outlined text-4xl animate-spin text-brand-primary">sync</span>
            <p class="font-medium text-sm tracking-wide">Carregando projetos...</p>
          </div>
        </div>

        <!-- Kanban Board -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 items-start">
          <div v-for="col in columns" :key="col.id" class="flex flex-col gap-4 bg-canvas/55 rounded-xl p-3 border border-hairline/50 min-h-[500px]">
            <div class="flex items-center justify-between px-1 mb-1">
              <h3 class="text-[11px] font-bold tracking-wider text-ink-muted">{{ col.title }}</h3>
              <span class="bg-surface border border-hairline text-ink text-[10px] px-2 py-0.5 rounded-full font-bold shadow-sm">
                {{ kanbanData[col.id].length }}
              </span>
            </div>
            
            <div class="flex flex-col gap-3 min-h-[200px]">
              <ProjectCard 
                v-for="project in kanbanData[col.id]" 
                :key="project.id" 
                :project="project" 
                @update="fetchProjetos"
                @projeto-arquivado="fetchProjetos"
              />
              
              <div v-if="kanbanData[col.id].length === 0" class="flex flex-col items-center justify-center py-10 px-4 text-center border-2 border-dashed border-hairline/30 rounded-lg bg-canvas/30 text-ink-muted">
                <span class="material-symbols-outlined text-2xl mb-2 text-ink-muted">inbox</span>
                <p class="text-xs font-medium">Nenhum projeto nesta fase</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
