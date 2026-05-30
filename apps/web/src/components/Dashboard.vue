<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
  { id: 'estimativa_enviada', title: 'ESTIMATIVA ENVIADA', dot: 'bg-brand-orange' },
  { id: 'contrato_pendente',  title: 'CONTRATO PENDENTE',  dot: 'bg-brand-blue' },
  { id: 'engenharia_caixa',   title: 'ENGENHARIA & CAIXA', dot: 'bg-brand-secure' },
  { id: 'obra_liberada',      title: 'OBRA LIBERADA',       dot: 'bg-semantic-success' },
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

// — Busca global —
const searchQuery = ref('')

const filteredKanban = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return kanbanData.value
  const match = (p) =>
    p.cliente_nome?.toLowerCase().includes(q) ||
    p.titulo_projeto?.toLowerCase().includes(q)
  return {
    estimativa_enviada: kanbanData.value.estimativa_enviada.filter(match),
    contrato_pendente:  kanbanData.value.contrato_pendente.filter(match),
    engenharia_caixa:   kanbanData.value.engenharia_caixa.filter(match),
    obra_liberada:      kanbanData.value.obra_liberada.filter(match),
  }
})

// — Métricas calculadas (sempre sobre dados não filtrados) —
const allProjects = computed(() => [
  ...kanbanData.value.estimativa_enviada,
  ...kanbanData.value.contrato_pendente,
  ...kanbanData.value.engenharia_caixa,
  ...kanbanData.value.obra_liberada
])

const totalProjetos = computed(() => allProjects.value.length)

const progressPercent = computed(() => {
  if (totalProjetos.value === 0) return 0
  return Math.round((kanbanData.value.obra_liberada.length / totalProjetos.value) * 100)
})

const totalVGV = computed(() =>
  allProjects.value.reduce((sum, p) => sum + (parseFloat(p.valor) || 0), 0)
)

const formatVGV = computed(() => {
  const v = totalVGV.value
  if (v === 0) return 'R$ —'
  if (v >= 1_000_000) return `R$ ${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `R$ ${(v / 1_000).toFixed(0)}K`
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v)
})

const projetosEsteMes = computed(() => {
  const now = new Date()
  return allProjects.value.filter(p => {
    if (!p.created_at) return false
    const d = new Date(p.created_at)
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()
  }).length
})
</script>

<template>
  <div class="bg-canvas text-ink font-sans min-h-screen overflow-x-hidden">
    <main class="ml-0 lg:ml-64 min-h-screen w-full lg:w-[calc(100vw-16rem)] transition-all duration-300">
      <TopHeader
        @new-client="isNewClientModalOpen = true"
        @open-archived="isArchivedModalOpen = true"
        @search="q => searchQuery = q"
      />
      
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

          <!-- Estimativas Ativas -->
          <div class="bg-surface border border-hairline p-6 flex flex-col justify-between hover:border-brand-orange/30 transition-all rounded-md shadow-sm">
            <div>
              <p class="text-xs font-semibold tracking-wider text-ink-muted mb-1">ESTIMATIVAS ATIVAS</p>
              <h2 class="text-3xl font-bold text-brand-orange">{{ kanbanData.estimativa_enviada.length }}</h2>
            </div>
            <div class="mt-4 flex items-center gap-1.5 text-ink-muted font-medium text-xs">
              <TrendingUp class="w-4 h-4 shrink-0 text-brand-orange" stroke-width="1.5" />
              <span v-if="projetosEsteMes > 0">+{{ projetosEsteMes }} esse mês</span>
              <span v-else-if="totalProjetos === 0">Nenhum projeto cadastrado</span>
              <span v-else>{{ totalProjetos }} projeto{{ totalProjetos !== 1 ? 's' : '' }} no pipeline</span>
            </div>
          </div>

          <!-- Aprovações Caixa -->
          <div class="bg-surface border border-hairline p-6 flex flex-col justify-between hover:border-brand-blue/30 transition-all rounded-md shadow-sm">
            <div>
              <p class="text-xs font-semibold tracking-wider text-ink-muted mb-1">APROVAÇÕES CAIXA</p>
              <h2 class="text-3xl font-bold text-brand-blue">
                {{ kanbanData.obra_liberada.length }}
                <span class="text-xl text-ink-muted font-medium">/{{ totalProjetos }}</span>
              </h2>
            </div>
            <div class="mt-4 flex items-center gap-3 w-full">
              <div class="flex-1 h-1.5 bg-canvas border border-hairline rounded-full overflow-hidden">
                <div
                  class="h-full bg-brand-blue rounded-full transition-all duration-500"
                  :style="{ width: progressPercent + '%' }"
                ></div>
              </div>
              <span class="text-brand-blue text-xs font-semibold shrink-0">{{ progressPercent }}%</span>
            </div>
          </div>

          <!-- VGV Gerenciado -->
          <div class="bg-surface border border-hairline p-6 flex flex-col justify-between hover:border-brand-blue/30 transition-all rounded-md shadow-sm">
            <div>
              <p class="text-xs font-semibold tracking-wider text-ink-muted mb-1">VGV GERENCIADO</p>
              <h2 class="text-3xl font-bold text-brand-blue">{{ formatVGV }}</h2>
            </div>
            <div class="mt-4 flex items-center gap-1.5 text-ink-muted font-medium text-xs">
              <LineChart class="w-4 h-4 shrink-0 text-brand-blue" stroke-width="1.5" />
              <span v-if="totalVGV === 0">Aguardando orçamentos SINAPI</span>
              <span v-else>Soma de todos os projetos ativos</span>
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
          <div v-for="col in columns" :key="col.id" class="flex flex-col bg-canvas/30 border border-hairline/60 rounded-md overflow-hidden min-h-[500px] max-h-[calc(100vh-280px)]">
            <!-- Cabeçalho da coluna — fixo, não acompanha o scroll -->
            <div class="flex items-center justify-between px-4 py-3 border-b border-hairline/60 shrink-0">
              <div class="flex items-center gap-2">
                <span :class="[col.dot, 'w-1.5 h-1.5 rounded-full shrink-0']"></span>
                <h3 class="text-[10px] font-bold tracking-wider text-ink-muted">{{ col.title }}</h3>
              </div>
              <span class="bg-surface border border-hairline text-ink text-[10px] px-2 py-0.5 rounded-md font-bold shadow-sm">
                {{ filteredKanban[col.id].length }}
              </span>
            </div>

            <!-- Área de cards com scroll independente -->
            <div class="flex-1 overflow-y-auto p-3 kanban-scroll">
              <TransitionGroup name="kanban-card" tag="div" class="flex flex-col gap-3 min-h-[200px]">
                <ProjectCard
                  v-for="project in filteredKanban[col.id]"
                  :key="project.id"
                  :project="project"
                  @update="fetchProjetos"
                  @projeto-arquivado="fetchProjetos"
                />

                <div v-if="filteredKanban[col.id].length === 0" key="__empty__" class="flex flex-col items-center justify-center py-10 px-4 text-center border border-dashed border-hairline rounded-md bg-canvas/50 text-ink-muted">
                  <Inbox class="w-6 h-6 mb-2 text-ink-muted" stroke-width="1.5" />
                  <p class="text-xs font-medium">
                    {{ searchQuery ? `Sem resultados para "${searchQuery}"` : 'Nenhum projeto nesta fase' }}
                  </p>
                </div>
              </TransitionGroup>
            </div>
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

/* Scrollbar fino nas colunas do kanban */
.kanban-scroll::-webkit-scrollbar { width: 4px; }
.kanban-scroll::-webkit-scrollbar-track { background: transparent; }
.kanban-scroll::-webkit-scrollbar-thumb { background: var(--color-hairline); border-radius: 9999px; }
.kanban-scroll::-webkit-scrollbar-thumb:hover { background: var(--color-ink-muted); }
.kanban-scroll { scrollbar-width: thin; scrollbar-color: var(--color-hairline) transparent; }
</style>
