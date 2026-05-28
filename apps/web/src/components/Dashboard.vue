<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { supabase } from '../supabase'
import { useToast } from '../composables/useToast'
import { useNotificacoes } from '../composables/useNotificacoes'
import TopHeader from './TopHeader.vue'
import ProjectCard from './ProjectCard.vue'
import NovoClienteModal from './NovoClienteModal.vue'
import ArchivedProjectsDrawer from './ArchivedProjectsDrawer.vue'
import { TrendingUp, LineChart, Loader2, Inbox } from 'lucide-vue-next'

const { showToast } = useToast()
const { adicionarNotificacao } = useNotificacoes()

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

// --- Supabase Realtime ---

const handleRealtimeEvent = ({ eventType, new: novo, old: antigo }) => {
  if (eventType === 'INSERT') {
    const col = novo.coluna
    if (kanbanData.value[col]) {
      kanbanData.value[col].unshift(novo)
      showToast(`Novo lead: ${novo.cliente_nome}`, 'success')
    }
    return
  }

  if (eventType === 'UPDATE') {
    // Encontra o projeto em qualquer coluna pelo id
    let colunaAtual = null
    let idxAtual = -1
    for (const col in kanbanData.value) {
      const idx = kanbanData.value[col].findIndex(p => p.id === novo.id)
      if (idx !== -1) {
        colunaAtual = col
        idxAtual = idx
        break
      }
    }

    const colunaDestino = novo.coluna
    const colunaValida = !!kanbanData.value[colunaDestino]

    if (colunaAtual === colunaDestino) {
      // Mesma coluna: atualiza o card no lugar
      if (idxAtual !== -1) {
        kanbanData.value[colunaAtual][idxAtual] = novo
      }
    } else {
      // Mudou de coluna: remove da atual e insere na nova
      if (colunaAtual && idxAtual !== -1) {
        kanbanData.value[colunaAtual].splice(idxAtual, 1)
      }
      if (colunaValida) {
        kanbanData.value[colunaDestino].unshift(novo)
      }
      if (colunaValida && novo.status !== 'docs_completos') {
        const label = columns.find(c => c.id === colunaDestino)?.title
        showToast(`${novo.cliente_nome} → ${label}`, 'success')
      }
    }

    // Notificação de documentos (independente de mudança de coluna)
    if (novo.status === 'docs_completos') {
      const antigasDocs = antigo?.documentos || []
      const novasDocs = novo.documentos || []
      if (antigo?.status !== 'docs_completos') {
        adicionarNotificacao(novo, 'primeiro_envio')
        showToast(`${novo.cliente_nome} enviou os documentos!`, 'success')
      } else {
        const temReenvio = antigasDocs.some(docAntigo => {
          if (docAntigo.status !== 'rejeitado') return false
          const docNovo = novasDocs.find(d => d.categoria === docAntigo.categoria)
          return docNovo && docNovo.status !== 'rejeitado'
        })
        if (temReenvio) {
          adicionarNotificacao(novo, 'reenvio')
          showToast(`${novo.cliente_nome} reencaminhou os documentos!`, 'success')
        }
      }
    }

    return
  }

  if (eventType === 'DELETE') {
    for (const col in kanbanData.value) {
      const idx = kanbanData.value[col].findIndex(p => p.id === antigo.id)
      if (idx !== -1) {
        kanbanData.value[col].splice(idx, 1)
        break
      }
    }
  }
}

let realtimeChannel = null

const setupRealtime = () => {
  realtimeChannel = supabase
    .channel('kanban-projetos')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'projetos_clientes' }, handleRealtimeEvent)
    .subscribe()
}

onMounted(async () => {
  await fetchProjetos()
  setupRealtime()
})

onUnmounted(() => {
  if (realtimeChannel) supabase.removeChannel(realtimeChannel)
})

const handleClientCreated = () => {
  isNewClientModalOpen.value = false
  fetchProjetos()
}
</script>

<template>
  <div class="bg-canvas text-ink font-sans min-h-screen overflow-x-hidden">
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
          <div class="bg-surface border border-hairline p-6 flex flex-col justify-between hover:border-neutral-500/50 transition-all rounded-md shadow-sm">
            <div>
              <p class="text-xs font-semibold tracking-wider text-ink-muted mb-1">ESTIMATIVAS ATIVAS</p>
              <div class="flex items-baseline gap-2">
                <h2 class="text-3xl font-bold text-ink">{{ kanbanData.estimativa_enviada.length }}</h2>
              </div>
            </div>
            <div class="mt-4 flex items-center gap-1 text-ink-muted font-medium text-xs">
              <TrendingUp class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
              <span>+2 esse mês</span>
            </div>
          </div>

          <div class="bg-surface border border-hairline p-6 flex flex-col justify-between hover:border-neutral-500/50 transition-all rounded-md shadow-sm">
            <div>
              <p class="text-xs font-semibold tracking-wider text-ink-muted mb-1">APROVAÇÕES CAIXA</p>
              <h2 class="text-3xl font-bold text-ink">{{ kanbanData.obra_liberada.length }}<span class="text-xl text-ink-muted font-medium">/8</span></h2>
            </div>
            <div class="mt-4 flex items-center gap-3 w-full">
              <div class="flex-1 h-1.5 bg-canvas border border-hairline rounded-full overflow-hidden">
                <div class="h-full bg-blue-500 rounded-full w-[62.5%]"></div>
              </div>
              <span class="text-ink-muted text-xs font-medium shrink-0">62%</span>
            </div>
          </div>

          <div class="bg-surface border border-hairline p-6 flex flex-col justify-between hover:border-neutral-500/50 transition-all rounded-md shadow-sm">
            <div>
              <p class="text-xs font-semibold tracking-wider text-ink-muted mb-1">VGV GERENCIADO</p>
              <h2 class="text-3xl font-bold text-ink">R$ 4.2M</h2>
            </div>
            <div class="mt-4 flex items-center gap-1 text-ink-muted font-medium text-xs">
              <LineChart class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
              <span>Alta no semestre</span>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex items-center justify-center py-20">
          <div class="flex flex-col items-center gap-4 text-ink-muted">
            <Loader2 class="w-10 h-10 animate-spin text-brand-primary" stroke-width="1.5" />
            <p class="font-medium text-sm tracking-wide">Carregando projetos...</p>
          </div>
        </div>

        <!-- Kanban Board -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 items-start">
          <div v-for="col in columns" :key="col.id" class="flex flex-col gap-4 bg-canvas/30 border border-hairline/60 rounded-md p-3 min-h-[500px]">
            <div class="flex items-center justify-between px-1 mb-1">
              <h3 class="text-[10px] font-bold tracking-wider text-ink-muted">{{ col.title }}</h3>
              <span class="bg-surface border border-hairline text-ink text-[10px] px-2 py-0.5 rounded-md font-bold shadow-sm">
                {{ kanbanData[col.id].length }}
              </span>
            </div>
            
            <TransitionGroup name="kanban-card" tag="div" class="flex flex-col gap-3 min-h-[200px]">
              <ProjectCard
                v-for="project in kanbanData[col.id]"
                :key="project.id"
                :project="project"
                @update="fetchProjetos"
                @projeto-arquivado="fetchProjetos"
              />

              <div v-if="kanbanData[col.id].length === 0" key="__empty__" class="flex flex-col items-center justify-center py-10 px-4 text-center border border-dashed border-hairline rounded-md bg-canvas/50 text-ink-muted">
                <Inbox class="w-6 h-6 mb-2 text-ink-muted" stroke-width="1.5" />
                <p class="text-xs font-medium">Nenhum projeto nesta fase</p>
              </div>
            </TransitionGroup>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.kanban-card-enter-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.kanban-card-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.kanban-card-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.97);
}
.kanban-card-leave-to {
  opacity: 0;
  transform: scale(0.97);
}
.kanban-card-move {
  transition: transform 0.3s ease;
}
</style>
