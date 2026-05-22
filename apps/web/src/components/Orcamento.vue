<script setup>
import { ref, onMounted, watch, computed, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import Sidebar from './Sidebar.vue'
import TopHeader from './TopHeader.vue'
import SinapiTable from './SinapiTable.vue'
import EditItemModal from './modals/EditItemModal.vue'
import SetupOrcamentoModal from './modals/SetupOrcamentoModal.vue'
import ShareLinkModal from './modals/ShareLinkModal.vue'
import ArvoreCustos from './ArvoreCustos.vue'
import ManualItemModal from './ManualItemModal.vue'

const route = useRoute()
const currentProject = ref(null)
const isLoadingProject = ref(true)
const isSetupModalOpen = ref(false)

// --- Estado: SINAPI (existente) ---
const items = ref([])
const cartItems = ref([])
const searchQuery = ref('')
const activeOrcamentoId = ref(null)
let debounceTimer = null
const isModalOpen = ref(false)
const isManualModalOpen = ref(false)
const isSaving = ref(false)
const selectedItem = ref(null)

// --- Estado: Notificações (Toast) ---
const toastVisible = ref(false)
const toastMessage = ref('')

// --- Estado: Paginação & Filtros SINAPI ---
const currentPage = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)
const totalPages = ref(1)

const filterUf = ref('')
const filterDesonerado = ref(false)
const filterTipo = ref('insumo')
const filterMesAno = ref('')
const availableMeses = ref([])

// --- Estado: Modal Compartilhamento B2C ---
const showShareModal = ref(false)
const shareOrcamentoId = ref(null)

// --- Estado: Modal de Template ---
const showTemplateModal = ref(false)
const templateForm = ref({ nome: '', area_referencia_m2: null })
const isSavingTemplate = ref(false)
const templateError = ref('')

// --- Estado: Modal Importar Template ---
const showImportTemplateModal = ref(false)
const availableTemplates = ref([])
const isLoadingTemplates = ref(false)
const importTemplateForm = ref({ template_id: '', nova_area: null })
const isImportingTemplate = ref(false)

// --- Estado: Carrinho Mobile (Drawer) ---
const isCartOpen = ref(false)



// --- Compartilhamento B2C ---
const abrirShareModal = (orcId) => {
  shareOrcamentoId.value = orcId
  showShareModal.value = true
}

// --- Guardar como Modelo ---
const abrirTemplateModal = () => {
  if (!activeOrcamentoId.value) return
  templateForm.value = { nome: '', area_referencia_m2: null }
  templateError.value = ''
  showTemplateModal.value = true
}

const salvarComoTemplate = async () => {
  if (!templateForm.value.nome || !templateForm.value.area_referencia_m2) {
    templateError.value = 'Preencha todos os campos corretamente.'
    return
  }
  isSavingTemplate.value = true
  templateError.value = ''
  try {
    const payload = { ...templateForm.value }
    const res = await axios.post(`/projetos/${activeOrcamentoId.value}/transformar-template`, payload)
    
    if (res.data.success) {
      showToast('Modelo Salvo!')
      showTemplateModal.value = false
    }
  } catch (e) {
    templateError.value = e.response?.data?.detail || 'Erro ao salvar como modelo.'
  } finally {
    isSavingTemplate.value = false
  }
}

// --- Importar Modelo ---
const carregarTemplates = async () => {
  isLoadingTemplates.value = true
  try {
    const res = await axios.get('/templates-orcamento')
    if (res.data.success) {
      availableTemplates.value = res.data.data
    }
  } catch (e) {
    console.error('Erro ao listar templates:', e)
  } finally {
    isLoadingTemplates.value = false
  }
}

const abrirImportTemplateModal = () => {
  if (!activeOrcamentoId.value) return
  importTemplateForm.value = { template_id: '', nova_area: null }
  showImportTemplateModal.value = true
  carregarTemplates()
}

const confirmarImportacaoTemplate = async () => {
  if (!importTemplateForm.value.template_id) return
  isImportingTemplate.value = true
  try {
    const payload = { nova_area: importTemplateForm.value.nova_area || null }
    const res = await axios.post(`/projetos/${activeOrcamentoId.value}/importar-template/${importTemplateForm.value.template_id}`, payload)
    if (res.data.success) {
      showToast('Modelo importado!')
      showImportTemplateModal.value = false
      fetchCart()
    }
  } catch(e) {
    console.error('Erro importar', e)
    showToast('Erro ao importar modelo', 'error')
  } finally {
    isImportingTemplate.value = false
  }
}

// --- SINAPI (lógica existente mantida) ---
const carregarReferencias = async () => {
  try {
    const res = await axios.get('/sinapi/referencias')
    if (res.data.success && res.data.data.length > 0) {
      availableMeses.value = res.data.data
      filterMesAno.value = res.data.data[0]
    }
  } catch (e) { console.error('Erro ao buscar referências:', e) }
}

const buscarItens = async () => {
  try {
    const params = {
      page: currentPage.value,
      limit: itemsPerPage.value,
      tipo: filterTipo.value,
      desonerado: filterDesonerado.value
    }
    if (route.params.id) params.projeto_id = route.params.id
    if (searchQuery.value) params.q = searchQuery.value
    if (filterUf.value) params.estado = filterUf.value
    if (filterMesAno.value) params.mes_ano = filterMesAno.value

    const res = await axios.get('/sinapi', { params })
    if (res.data.success) {
      items.value = res.data.data
      totalItems.value = res.data.total_items
      totalPages.value = res.data.total_pages
      currentPage.value = res.data.page
    }
  } catch (e) { console.error('Erro ao buscar itens:', e) }
}

const changePage = (page) => {
  currentPage.value = page
  buscarItens()
}

const changeLimit = (limit) => {
  itemsPerPage.value = limit
  currentPage.value = 1
  buscarItens()
}

const fetchCart = async () => {
  const projectId = route.params.id
  if (!projectId) return
  try {
    const res = await axios.get(`/projetos/${projectId}/itens`)
    if (res.data.success) cartItems.value = res.data.data
  } catch (e) { console.error('Erro ao buscar itens do projeto:', e) }
}

const openQuantityModal = (item) => { selectedItem.value = item; isModalOpen.value = true }

const showToast = (msg) => {
  toastMessage.value = msg
  toastVisible.value = true
  setTimeout(() => toastVisible.value = false, 3000)
}

const handleAddToCartExpress = (item) => {
  openQuantityModal(item)
}

const handleAddToCart = async (itemPayload) => {
  const projectId = route.params.id
  if (!projectId) return
  isSaving.value = true
  try {
    const res = await axios.post(`/projetos/${projectId}/itens`, itemPayload)
    if (res.data.success) {
      cartItems.value.push(res.data.data)
      showToast('Item adicionado!')
      isModalOpen.value = false
    }
  } catch (e) { 
    console.error('Erro:', e)
    showToast('Erro ao adicionar item.', 'error')
  } finally {
    isSaving.value = false
  }
}

const handleAddManualItem = async (form) => {
  const projectId = route.params.id
  if (!projectId) return
  isSaving.value = true
  try {
    const res = await axios.post(`/projetos/${projectId}/itens`, form)
    if (res.data.success) {
      cartItems.value.push(res.data.data)
      showToast('Item manual adicionado!')
      isManualModalOpen.value = false
    }
  } catch (e) { 
    console.error('Erro ao adicionar item manual:', e)
    showToast('Erro ao adicionar item manual.', 'error')
  } finally {
    isSaving.value = false
  }
}



const handleRemoveFromCart = async (id) => {
  const projectId = route.params.id
  if (!projectId) return
  try {
    const res = await axios.delete(`/projetos/${projectId}/itens/${id}`)
    if (res.data.success) {
      cartItems.value = cartItems.value.filter(item => item.id !== id)
    }
  } catch (e) { console.error('Erro:', e) }
}

const handleUpdateQuantity = async (id, newQuantity) => {
  const projectId = route.params.id
  if (!projectId) return
  try {
    const itemIndex = cartItems.value.findIndex(item => item.id === id)
    if (itemIndex > -1) {
      cartItems.value[itemIndex].quantidade = newQuantity
    }
    await axios.patch(`/projetos/${projectId}/itens/${id}`, {
      quantidade: newQuantity
    })
  } catch (e) {
    console.error('Erro ao atualizar quantidade:', e)
    fetchCart()
  }
}

watch([filterUf, filterDesonerado, filterTipo, filterMesAno], () => {
  currentPage.value = 1
  buscarItens()
})

watch(searchQuery, () => { 
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    buscarItens()
  }, 300) 
})

const fetchProjectData = async () => {
  const projectId = route.params.id
  if (!projectId) return
  
  isLoadingProject.value = true
  try {
    const res = await axios.get(`/projetos/${projectId}`)
    if (res.data.success || res.data) {
      const data = res.data.data || res.data
      currentProject.value = {
        ...data,
        nome_obra: data.nome_obra || data.titulo_projeto || 'Obra sem nome'
      }
      activeOrcamentoId.value = currentProject.value.id
      
      filterUf.value = currentProject.value.uf_obra || 'SC'
      filterDesonerado.value = currentProject.value.sinapi_desonerado || false
      filterMesAno.value = currentProject.value.sinapi_mes_ano || ''
      
      fetchCart()
    }
  } catch (e) {
    console.error('Erro ao buscar dados do projeto:', e)
  } finally {
    isLoadingProject.value = false
  }
}

onMounted(async () => { 
  await fetchProjectData()
  await carregarReferencias()
  buscarItens() 
})

const onSetupSuccess = async () => {
  isSetupModalOpen.value = false
  await fetchProjectData()
  buscarItens()
}

watch(isCartOpen, (newVal) => {
  if (newVal) {
    document.body.classList.add('overflow-hidden')
  } else {
    document.body.classList.remove('overflow-hidden')
  }
})

onUnmounted(() => {
  document.body.classList.remove('overflow-hidden')
})
</script>

<template>
  <div class="bg-canvas text-ink font-sans min-h-screen overflow-x-hidden">
    <Sidebar />
    <main class="ml-0 lg:ml-64 min-h-screen w-full lg:w-[calc(100vw-16rem)] transition-all duration-300">
      <TopHeader />
      <div class="p-8">

        <!-- ========== CABEÇALHO DINÂMICO (PROJETO & CLIENTE) ========== -->
        <div class="mb-8 bg-surface p-6 rounded-2xl border border-hairline shadow-sm">
          <div v-if="isLoadingProject" class="animate-pulse flex items-center justify-between">
            <div class="space-y-3 flex-1">
              <div class="h-8 bg-canvas rounded-lg w-1/3"></div>
              <div class="h-4 bg-canvas rounded-lg w-1/4"></div>
              <div class="flex gap-2">
                <div class="h-6 bg-canvas rounded w-16"></div>
                <div class="h-6 bg-canvas rounded w-16"></div>
              </div>
            </div>
            <div class="h-12 bg-canvas rounded-xl w-40"></div>
          </div>

          <div v-else-if="currentProject" class="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <!-- Lado Esquerdo: Identificação -->
            <div class="space-y-2">
              <div class="flex items-center gap-3">
                <div class="bg-brand-primary text-white p-2 rounded-xl">
                  <span class="material-symbols-outlined text-[24px]">architecture</span>
                </div>
                <h1 class="text-2xl font-black text-ink tracking-tight">{{ currentProject.nome_obra }}</h1>
              </div>
              
              <div class="flex flex-col gap-3">
                <p class="text-sm font-semibold text-ink-muted flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[18px]">person</span>
                  Cliente: <span class="text-ink">{{ currentProject.cliente_nome || 'Não informado' }}</span>
                </p>
                
                <div class="flex flex-wrap items-center gap-2">
                  <span class="px-2.5 py-1 bg-canvas text-ink-muted text-[10px] font-bold rounded-lg border border-hairline uppercase tracking-wider flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px]">map</span>
                    {{ currentProject.uf_obra }}
                  </span>
                  <span class="px-2.5 py-1 bg-canvas text-ink-muted text-[10px] font-bold rounded-lg border border-hairline uppercase tracking-wider flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px]">calendar_month</span>
                    {{ currentProject.sinapi_mes_ano }}
                  </span>
                  <span class="px-2.5 py-1 bg-brand-primary/10 text-brand-primary text-[10px] font-bold rounded-lg border border-brand-primary/20 uppercase tracking-wider flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px]">payments</span>
                    {{ currentProject.sinapi_desonerado ? "Desonerado" : "Não Desonerado" }}
                  </span>
                  <span class="px-2.5 py-1 bg-brand-primary/10 text-brand-primary text-[10px] font-bold rounded-lg border border-brand-primary/20 uppercase tracking-wider flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px]">percent</span>
                    BDI: {{ currentProject.bdi_padrao }}%
                  </span>
                </div>
              </div>
            </div>

            <!-- Lado Direito: Ações -->
            <div class="flex flex-col gap-2 shrink-0 w-full sm:w-auto">
              <div v-if="activeOrcamentoId" class="flex items-center gap-2 w-full">
                <button @click="abrirShareModal(activeOrcamentoId)" class="flex-1 flex justify-center p-2.5 bg-surface border border-hairline hover:bg-canvas text-ink-muted rounded-xl transition-all group shadow-sm" title="Compartilhar com Cliente">
                  <span class="material-symbols-outlined text-[22px] text-brand-primary">share</span>
                </button>
                <button @click="abrirImportTemplateModal" class="flex-1 flex justify-center p-2.5 bg-surface border border-hairline hover:bg-canvas text-ink-muted rounded-xl transition-all group shadow-sm" title="Importar Modelo">
                  <span class="material-symbols-outlined text-[22px]">download</span>
                </button>
                <button @click="abrirTemplateModal" class="flex-1 flex justify-center p-2.5 bg-surface border border-hairline hover:bg-canvas text-ink-muted rounded-xl transition-all group shadow-sm" title="Guardar como Modelo">
                  <span class="material-symbols-outlined text-[22px] text-amber-500">star</span>
                </button>
              </div>
              
              <button @click="isSetupModalOpen = true" class="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-surface border border-hairline text-ink hover:bg-canvas hover:text-brand-primary hover:border-brand-primary transition-all group font-bold text-sm shadow-sm">
                <span class="material-symbols-outlined text-[22px] group-hover:rotate-90 transition-transform duration-500">settings</span>
                Configurações da Obra
              </button>
            </div>
          </div>
        </div>

        <!-- Breadcrumb & Subtitle -->
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-2 text-[11px] font-bold tracking-widest text-ink-muted uppercase">
            <span>Projetos</span>
            <span class="material-symbols-outlined text-[12px]">chevron_right</span>
            <span class="text-ink">Planilha de Custos SINAPI</span>
          </div>
        </div>

        <div class="grid grid-cols-12 gap-5">
          <div class="col-span-12 lg:col-span-8 space-y-6 relative min-w-0">
            <div class="bg-surface p-5 rounded-xl border border-hairline space-y-4 shadow-sm">
              <div class="relative flex-1">
                <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted">search</span>
                <input v-model="searchQuery" class="w-full pl-10 pr-4 py-2 bg-canvas border border-hairline rounded-lg text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all text-ink" placeholder="Filtrar itens da tabela pelo nome ou código..." type="text"/>
              </div>
            </div>

            <div class="w-full overflow-x-auto">
              <SinapiTable 
                :items="items" 
                :current-page="currentPage"
                :total-pages="totalPages"
                :total-items="totalItems"
                :items-per-page="itemsPerPage"
                @add-item="handleAddToCartExpress" 
                @change-page="changePage"
                @change-limit="changeLimit"
              />
            </div>
          </div>
          
          <!-- Overlay mobile do carrinho -->
          <Transition
            enter-active-class="transition-opacity duration-300 ease-out"
            enter-from-class="opacity-0"
            enter-to-class="opacity-100"
            leave-active-class="transition-opacity duration-300 ease-in"
            leave-from-class="opacity-100"
            leave-to-class="opacity-0"
          >
            <div 
              v-if="isCartOpen" 
              @click="isCartOpen = false" 
              class="fixed inset-0 bg-zinc-950/50 dark:bg-zinc-950/80 backdrop-blur-sm z-[60] lg:hidden"
            ></div>
          </Transition>

          <!-- Container do Carrinho (Drawer no mobile, Coluna no desktop) -->
          <div :class="[
            'fixed inset-y-0 right-0 z-[70] w-[92%] sm:w-[450px] bg-canvas border-l border-hairline lg:border-none transform transition-transform duration-300 ease-in-out flex flex-col',
            isCartOpen ? 'translate-x-0' : 'translate-x-full',
            'lg:sticky lg:inset-auto lg:top-24 lg:col-span-4 lg:z-auto lg:w-auto lg:bg-transparent lg:dark:bg-transparent lg:shadow-none lg:translate-x-0 lg:transform-none lg:transition-none lg:block lg:self-start'
          ]">
            <div class="lg:hidden flex justify-between items-center p-5 border-b border-hairline bg-surface shrink-0">
              <div class="flex items-center gap-2 text-brand-primary font-bold">
                <span class="material-symbols-outlined">account_tree</span>
                Árvore de Custos
              </div>
              <button @click="isCartOpen = false" class="p-1.5 rounded-lg bg-canvas hover:bg-surface-hover text-ink-muted hover:text-ink transition-colors">
                <span class="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>
            <div class="p-4 lg:p-0 flex-1 overflow-y-auto lg:overflow-visible">
              <ArvoreCustos
                :items="cartItems"
                :bdi="currentProject?.bdi_padrao || 0"
                @remove-item="handleRemoveFromCart"
                @update-quantity="handleUpdateQuantity"
                @add-manual-item="isManualModalOpen = true"
                @import-template="abrirImportTemplateModal"
              />
            </div>
          </div>
        </div>

        <!-- Aba Lateral (Gatilho da Árvore de Custos) -->
        <button 
          v-show="currentProject && !isCartOpen"
          @click="isCartOpen = true"
          class="lg:hidden fixed top-1/2 -translate-y-1/2 right-0 z-[60] bg-brand-primary text-white py-4 px-1.5 rounded-l-lg hover:bg-brand-hover transition-all duration-300 flex flex-col items-center justify-center group focus:outline-none focus:ring-1 focus:ring-brand-primary/50 border border-brand-primary"
        >
          <span class="material-symbols-outlined text-2xl group-hover:-translate-x-1 transition-transform">chevron_left</span>
          <div class="relative mt-2">
            <span class="material-symbols-outlined text-[22px]">account_tree</span>
            <span v-if="cartItems.length" class="absolute -top-2 -right-2 bg-amber-500 text-white text-[10px] font-extrabold w-5 h-5 rounded-full flex items-center justify-center border border-brand-primary">{{ cartItems.length }}</span>
          </div>
        </button>

      </div>
    </main>

    <!-- Modal: Adicionar/Editar Quantidade de Insumo -->
    <EditItemModal 
      :is-open="isModalOpen" 
      :item-data="selectedItem"
      :is-editing="false"
      :is-saving="isSaving"
      @close="isModalOpen = false" 
      @salvar-item="handleAddToCart" 
    />

    <ManualItemModal
      :is-open="isManualModalOpen"
      :is-saving="isSaving"
      @close="isManualModalOpen = false"
      @confirm="handleAddManualItem"
    />

    <!-- Setup SINAPI Modal (Reutilizado para Edição) -->
    <SetupOrcamentoModal 
      :is-open="isSetupModalOpen" 
      :project="currentProject"
      @close="isSetupModalOpen = false"
      @salvar="onSetupSuccess"
    />

    <!-- ========== MODAL: COMPARTILHAR B2C ========== -->
    <ShareLinkModal
      :is-open="showShareModal"
      :resource-id="shareOrcamentoId"
      resource-label="Orçamento"
      @close="showShareModal = false"
    />

    <!-- ========== MODAL: GUARDAR COMO MODELO ========== -->
    <Teleport to="body">
      <div v-if="showTemplateModal" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="showTemplateModal = false">
        <div class="bg-surface rounded-2xl border border-hairline w-full max-w-md overflow-hidden shadow-sm animate-in zoom-in duration-200">
          <div class="flex items-center justify-between px-6 py-4 border-b border-hairline">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-amber-500">star</span>
              <h3 class="text-lg font-bold text-ink">Guardar como Modelo</h3>
            </div>
            <button @click="showTemplateModal = false" class="p-1 rounded-lg hover:bg-surface-hover transition-all">
              <span class="material-symbols-outlined text-ink-muted">close</span>
            </button>
          </div>
          
          <form @submit.prevent="salvarComoTemplate" class="p-6 space-y-4">
            <div v-if="templateError" class="bg-red-50 dark:bg-red-900/20 border border-red-250 dark:border-red-900/50 text-red-650 dark:text-red-400 text-sm p-3 rounded-lg flex items-start gap-2 border border-red-100 dark:border-red-500/20">
              <span class="material-symbols-outlined text-base">error</span>
              <span>{{ templateError }}</span>
            </div>
            <p class="text-sm text-ink-muted">Este orçamento servirá de base parametrizada para projetos futuros.</p>
            
            <div>
              <label class="block text-sm font-medium text-ink mb-1">Nome do Modelo *</label>
              <input v-model="templateForm.nome" required class="w-full bg-canvas border border-hairline rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all text-ink" placeholder="Ex: Casa Padrão Médio"/>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-ink mb-1">Área de Referência (m²) *</label>
              <input v-model.number="templateForm.area_referencia_m2" @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }" required type="number" step="0.01" min="0.1" class="w-full bg-canvas border border-hairline rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all text-ink" placeholder="Ex: 120.50"/>
            </div>
            
            <div class="flex gap-3 pt-2 mt-4">
              <button type="button" @click="showTemplateModal = false" class="flex-1 py-2.5 border border-hairline rounded-lg text-sm font-medium text-ink-muted hover:bg-canvas transition-all">Cancelar</button>
              <button type="submit" :disabled="isSavingTemplate || !templateForm.nome || !templateForm.area_referencia_m2" class="flex-1 py-2.5 bg-brand-primary hover:bg-brand-hover text-white rounded-lg text-sm font-semibold transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                <span v-if="isSavingTemplate" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                {{ isSavingTemplate ? 'Salvando...' : 'Salvar Modelo' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- ========== MODAL: IMPORTAR MODELO ========== -->
    <Teleport to="body">
      <div v-if="showImportTemplateModal" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="showImportTemplateModal = false">
        <div class="bg-surface rounded-2xl border border-hairline w-full max-w-md overflow-hidden shadow-sm animate-in zoom-in duration-200">
          <div class="flex items-center justify-between px-6 py-4 border-b border-hairline">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-brand-primary">download</span>
              <h3 class="text-lg font-bold text-ink">Importar Modelo</h3>
            </div>
            <button @click="showImportTemplateModal = false" class="p-1 rounded-lg hover:bg-surface-hover transition-all">
              <span class="material-symbols-outlined text-ink-muted">close</span>
            </button>
          </div>
          
          <form @submit.prevent="confirmarImportacaoTemplate" class="p-6 space-y-4">
            <p class="text-sm text-ink-muted">Selecione um modelo existente e, se desejar, defina uma nova área para adaptar as quantidades proporcionalmente.</p>
            
            <div>
              <label class="block text-sm font-medium text-ink mb-1">Selecione o Modelo *</label>
              <select v-model="importTemplateForm.template_id" required class="w-full bg-canvas border border-hairline rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all text-ink">
                <option value="" disabled>Escolha um modelo salvo...</option>
                <option v-for="tpl in availableTemplates" :key="tpl.id" :value="tpl.id">
                  {{ tpl.nome }} ({{ tpl.area_referencia_m2 }} m²)
                </option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-ink mb-1">Nova Área (m²) [Opcional]</label>
              <input v-model.number="importTemplateForm.nova_area" @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }" type="number" step="0.01" min="0.1" class="w-full bg-canvas border border-hairline rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all text-ink" placeholder="Se vazio, mantém a escala original"/>
            </div>
            
            <div class="flex gap-3 pt-2 mt-4">
              <button type="button" @click="showImportTemplateModal = false" class="flex-1 py-2.5 border border-hairline rounded-lg text-sm font-medium text-ink-muted hover:bg-canvas transition-all">Cancelar</button>
              <button type="submit" :disabled="isImportingTemplate || !importTemplateForm.template_id" class="flex-1 py-2.5 bg-brand-primary hover:bg-brand-hover text-white rounded-lg text-sm font-semibold transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                <span v-if="isImportingTemplate" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                {{ isImportingTemplate ? 'Importando...' : 'Importar Modelo' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Toast Notification -->
    <div v-if="toastVisible" class="fixed bottom-6 right-6 bg-brand-primary text-white px-6 py-3 rounded-xl border border-brand-primary/20 flex items-center gap-3 animate-fade-in-up z-50">
      <span class="material-symbols-outlined">check_circle</span>
      <span class="font-semibold text-sm">{{ toastMessage }}</span>
    </div>

  </div>
</template>
