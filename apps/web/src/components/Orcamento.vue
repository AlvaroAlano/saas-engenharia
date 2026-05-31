<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import TopHeader from './TopHeader.vue'
import SinapiTable from './SinapiTable.vue'
import EditItemModal from './modals/EditItemModal.vue'
import SetupOrcamentoModal from './modals/SetupOrcamentoModal.vue'
import ConfirmarTemplateModal from './modals/ConfirmarTemplateModal.vue'
import ShareLinkModal from './modals/ShareLinkModal.vue'
import ArvoreCustos from './ArvoreCustos.vue'
import ArvoreCustosModal from './modals/ArvoreCustosModal.vue'
import ManualItemModal from './ManualItemModal.vue'
import { useToast } from '../composables/useToast'
import {
  HardHat, User, MapPin, Calendar, DollarSign, Percent, Share2, Download, Import, Star,
  Settings, ChevronRight, ChevronLeft, ChevronDown, Search, GitFork, X, FileText, Table,
  Loader2, AlertTriangle
} from 'lucide-vue-next'

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
const { showToast } = useToast()

// --- Estado: Loading da busca SINAPI ---
const isSearching = ref(false)

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

const UFS = [
  'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA',
  'MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN',
  'RS','RO','RR','SC','SP','SE','TO'
]

const ufDropdownOpen  = ref(false)
const mesDropdownOpen = ref(false)

const selectUf  = (uf)  => { filterUf.value = uf;  ufDropdownOpen.value  = false }
const selectMes = (mes) => { filterMesAno.value = mes; mesDropdownOpen.value = false }

const resetFilters = () => {
  filterUf.value         = currentProject.value?.uf_obra || ''
  filterMesAno.value     = currentProject.value?.sinapi_mes_ano || availableMeses.value[0] || ''
  filterDesonerado.value = currentProject.value?.sinapi_desonerado || false
  filterTipo.value       = 'insumo'
  searchQuery.value      = ''
}

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
const importTemplateForm = ref({ template_id: '', nova_area: null, modo: 'mesclar' })
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
  importTemplateForm.value = { template_id: '', nova_area: null, modo: 'mesclar' }
  showImportTemplateModal.value = true
  carregarTemplates()
}

const confirmarImportacaoTemplate = async () => {
  if (!importTemplateForm.value.template_id) return
  isImportingTemplate.value = true
  try {
    const payload = { nova_area: importTemplateForm.value.nova_area || null, modo: importTemplateForm.value.modo }
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
  isSearching.value = true
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
  finally { isSearching.value = false }
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


// --- Exportar Planilha SINAPI ---
const isExporting = ref(null) // 'pdf' | 'xlsx' | null

const exportarPlanilha = async (formato) => {
  if (!activeOrcamentoId.value || isExporting.value) return
  isExporting.value = formato
  try {
    const res = await axios.get(`/projetos/${activeOrcamentoId.value}/exportar-sinapi`, {
      params: { formato },
      responseType: 'blob',
    })
    const mimeType = formato === 'pdf'
      ? 'application/pdf'
      : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    const blob = new Blob([res.data], { type: mimeType })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `planilha_sinapi_${currentProject.value?.nome_obra || 'obra'}.${formato}`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    const msg = e.response?.status === 422
      ? 'Adicione itens ao orçamento antes de exportar.'
      : 'Erro ao gerar o arquivo. Tente novamente.'
    showToast(msg)
  } finally {
    isExporting.value = null
  }
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
  await Promise.all([fetchProjectData(), carregarReferencias()])
  buscarItens()
})

const onSetupSuccess = async () => {
  isSetupModalOpen.value = false
  await fetchProjectData()
  buscarItens()
}

// --- Modal: Árvore expandida ---
const showArvoreCustosModal = ref(false)

// --- Aplicar template padrão (acionado pela ArvoreCustos) ---
const showConfirmTemplate = ref(false)
const isApplyingTemplate = ref(false)

const onSolicitarTemplate = () => {
  if (cartItems.value.length > 0) {
    showConfirmTemplate.value = true
  } else {
    executarAplicarTemplate('mesclar')
  }
}

const executarAplicarTemplate = async (modo) => {
  showConfirmTemplate.value = false
  const projectId = route.params.id
  if (!projectId) return
  isApplyingTemplate.value = true
  try {
    const res = await axios.post(`/projetos/${projectId}/aplicar-template-padrao`, { modo })
    if (res.data?.sem_preco?.length) {
      console.warn('[Template] Códigos sem preço no SINAPI:', res.data.sem_preco)
    }
    showToast(`${res.data.inserted} itens adicionados à árvore!`)
    await fetchCart()
  } catch (e) {
    const detail = e.response?.data?.detail || 'Erro ao aplicar template.'
    showToast(detail)
  } finally {
    isApplyingTemplate.value = false
  }
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
    <main class="ml-0 lg:ml-64 min-h-screen w-full lg:w-[calc(100vw-16rem)] transition-all duration-300">
      <TopHeader />
      <div class="px-4 py-5 sm:px-6 sm:py-6 lg:px-8 lg:py-8">

        <!-- ========== CABEÇALHO DINÂMICO (PROJETO & CLIENTE) ========== -->
        <div class="mb-4 sm:mb-6 lg:mb-8 bg-surface p-4 sm:p-6 rounded-2xl border border-hairline shadow-sm">
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
                <div class="bg-brand-blue text-white p-2 rounded-xl flex items-center justify-center">
                  <HardHat class="w-6 h-6 text-white" stroke-width="1.5" />
                </div>
                <h1 class="text-2xl font-black text-ink tracking-tight">{{ currentProject.nome_obra }}</h1>
              </div>
              
              <div class="flex flex-col gap-3">
                <p class="text-sm font-semibold text-ink-muted flex items-center gap-1.5">
                  <User class="w-[18px] h-[18px]" stroke-width="1.5" />
                  Cliente: <span class="text-ink">{{ currentProject.cliente_nome || 'Não informado' }}</span>
                </p>
                
                <div class="flex flex-wrap items-center gap-2">
                  <span class="px-2.5 py-1 bg-brand-orange/10 text-brand-orange text-[10px] font-bold rounded-lg border border-brand-orange/20 uppercase tracking-wider flex items-center gap-1">
                    <MapPin class="w-3.5 h-3.5 text-brand-orange" stroke-width="1.5" />
                    {{ currentProject.uf_obra }}
                  </span>
                  <span class="px-2.5 py-1 bg-brand-orange/10 text-brand-orange text-[10px] font-bold rounded-lg border border-brand-orange/20 uppercase tracking-wider flex items-center gap-1">
                    <Calendar class="w-3.5 h-3.5 text-brand-orange" stroke-width="1.5" />
                    {{ currentProject.sinapi_mes_ano }}
                  </span>
                  <span class="px-2.5 py-1 bg-brand-blue/10 text-brand-blue text-[10px] font-bold rounded-lg border border-brand-blue/20 uppercase tracking-wider flex items-center gap-1">
                    <DollarSign class="w-3.5 h-3.5 text-brand-blue" stroke-width="1.5" />
                    {{ currentProject.sinapi_desonerado ? "Desonerado" : "Não Desonerado" }}
                  </span>
                  <span class="px-2.5 py-1 bg-brand-blue/10 text-brand-blue text-[10px] font-bold rounded-lg border border-brand-blue/20 uppercase tracking-wider flex items-center gap-1">
                    <Percent class="w-3.5 h-3.5 text-brand-blue" stroke-width="1.5" />
                    BDI: {{ currentProject.bdi_padrao }}%
                  </span>
                </div>
              </div>
            </div>

            <!-- Lado Direito: Ações -->
            <div class="flex flex-col gap-2 shrink-0 w-full sm:w-auto">
              <div v-if="activeOrcamentoId" class="flex items-center gap-2 w-full">
                <button @click="abrirShareModal(activeOrcamentoId)" class="flex-1 flex flex-col items-center gap-1 py-2.5 px-2 bg-surface border border-hairline hover:bg-canvas rounded-xl transition-all shadow-sm cursor-pointer group" title="Compartilhar com Cliente">
                  <Share2 class="w-5 h-5 text-brand-primary group-hover:text-brand-blue transition-colors" stroke-width="1.5" />
                  <span class="text-[10px] font-semibold text-ink-muted leading-none">Compartilhar</span>
                </button>
                <button @click="abrirImportTemplateModal" class="flex-1 flex flex-col items-center gap-1 py-2.5 px-2 bg-surface border border-hairline hover:bg-canvas rounded-xl transition-all shadow-sm cursor-pointer group" title="Importar Modelo">
                  <Import class="w-5 h-5 text-ink-muted group-hover:text-brand-blue transition-colors" stroke-width="1.5" />
                  <span class="text-[10px] font-semibold text-ink-muted leading-none">Importar</span>
                </button>
                <button @click="abrirTemplateModal" class="flex-1 flex flex-col items-center gap-1 py-2.5 px-2 bg-surface border border-hairline hover:bg-canvas rounded-xl transition-all shadow-sm cursor-pointer group" title="Guardar como Modelo">
                  <Star class="w-5 h-5 text-brand-orange group-hover:text-brand-orange-hover transition-colors" stroke-width="1.5" />
                  <span class="text-[10px] font-semibold text-ink-muted leading-none">Salvar Modelo</span>
                </button>
              </div>
              
              <button @click="isSetupModalOpen = true" class="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-surface border border-hairline text-ink hover:bg-canvas hover:text-brand-primary hover:border-brand-primary transition-all group font-bold text-sm shadow-sm cursor-pointer">
                <Settings class="w-[22px] h-[22px] group-hover:rotate-90 transition-transform duration-500" stroke-width="1.5" />
                Configurações da Obra
              </button>
            </div>
          </div>
        </div>

        <!-- Breadcrumb & Subtitle -->
        <div class="hidden sm:flex items-center justify-between mb-3 sm:mb-5 lg:mb-6">
          <div class="flex items-center gap-2 text-[11px] font-bold tracking-widest text-ink-muted uppercase">
            <span>Projetos</span>
            <ChevronRight class="w-3 h-3 text-ink-muted" stroke-width="1.5" />
            <span class="text-ink">Planilha de Custos SINAPI</span>
          </div>
        </div>

        <div class="grid grid-cols-12 gap-5">
          <div class="col-span-12 lg:col-span-8 space-y-6 relative min-w-0">
            <div class="bg-surface p-5 rounded-xl border border-hairline space-y-3 shadow-sm">

              <!-- Campo de busca -->
              <div class="relative">
                <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Buscar por nome ou código SINAPI..."
                  class="w-full pl-10 pr-4 py-2.5 bg-canvas border border-hairline rounded-lg text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all text-ink placeholder:text-ink-muted"
                />
              </div>

              <!-- Filtros inline -->
              <div class="flex flex-wrap items-center gap-2">

                <!-- Estado (UF) -->
                <div class="relative">
                  <div v-if="ufDropdownOpen" class="fixed inset-0 z-30" @click="ufDropdownOpen = false" />
                  <button
                    @click="ufDropdownOpen = !ufDropdownOpen; mesDropdownOpen = false"
                    :class="ufDropdownOpen ? 'border-brand-orange/50 ring-1 ring-brand-orange/30' : 'border-hairline hover:border-brand-orange/40'"
                    class="flex items-center gap-1.5 pl-3 pr-2.5 py-2.5 sm:py-1.5 text-xs font-semibold bg-canvas border rounded-lg transition-all cursor-pointer focus:outline-none"
                  >
                    <MapPin class="w-3 h-3 text-brand-orange shrink-0" stroke-width="2" />
                    <span :class="filterUf ? 'text-ink' : 'text-ink-muted'">{{ filterUf || 'UF' }}</span>
                    <ChevronDown
                      class="w-3 h-3 text-ink-muted transition-transform shrink-0"
                      :class="{ 'rotate-180': ufDropdownOpen }"
                      stroke-width="2"
                    />
                  </button>
                  <Transition
                    enter-active-class="transition-all duration-150 ease-out"
                    enter-from-class="opacity-0 -translate-y-1 scale-95"
                    enter-to-class="opacity-100 translate-y-0 scale-100"
                    leave-active-class="transition-all duration-100 ease-in"
                    leave-from-class="opacity-100 translate-y-0 scale-100"
                    leave-to-class="opacity-0 -translate-y-1 scale-95"
                  >
                    <div
                      v-if="ufDropdownOpen"
                      class="absolute top-full mt-1.5 left-0 z-40 bg-surface border border-hairline rounded-xl shadow-xl py-1 w-28 max-h-56 overflow-y-auto"
                    >
                      <button
                        @click="selectUf('')"
                        class="w-full text-left px-3 py-1.5 text-xs transition-colors cursor-pointer"
                        :class="filterUf === '' ? 'text-brand-orange font-bold bg-brand-orange/5' : 'text-ink-muted hover:bg-surface-hover'"
                      >Todos</button>
                      <button
                        v-for="uf in UFS"
                        :key="uf"
                        @click="selectUf(uf)"
                        class="w-full text-left px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer"
                        :class="filterUf === uf ? 'text-brand-orange font-bold bg-brand-orange/5' : 'text-ink hover:bg-surface-hover'"
                      >{{ uf }}</button>
                    </div>
                  </Transition>
                </div>

                <!-- Mês de referência -->
                <div class="relative">
                  <div v-if="mesDropdownOpen" class="fixed inset-0 z-30" @click="mesDropdownOpen = false" />
                  <button
                    @click="mesDropdownOpen = !mesDropdownOpen; ufDropdownOpen = false"
                    :class="mesDropdownOpen ? 'border-brand-orange/50 ring-1 ring-brand-orange/30' : 'border-hairline hover:border-brand-orange/40'"
                    class="flex items-center gap-1.5 pl-3 pr-2.5 py-2.5 sm:py-1.5 text-xs font-semibold bg-canvas border rounded-lg transition-all cursor-pointer focus:outline-none"
                  >
                    <Calendar class="w-3 h-3 text-brand-orange shrink-0" stroke-width="2" />
                    <span class="text-ink">{{ filterMesAno }}</span>
                    <ChevronDown
                      class="w-3 h-3 text-ink-muted transition-transform shrink-0"
                      :class="{ 'rotate-180': mesDropdownOpen }"
                      stroke-width="2"
                    />
                  </button>
                  <Transition
                    enter-active-class="transition-all duration-150 ease-out"
                    enter-from-class="opacity-0 -translate-y-1 scale-95"
                    enter-to-class="opacity-100 translate-y-0 scale-100"
                    leave-active-class="transition-all duration-100 ease-in"
                    leave-from-class="opacity-100 translate-y-0 scale-100"
                    leave-to-class="opacity-0 -translate-y-1 scale-95"
                  >
                    <div
                      v-if="mesDropdownOpen"
                      class="absolute top-full mt-1.5 left-0 z-40 bg-surface border border-hairline rounded-xl shadow-xl py-1 min-w-[120px]"
                    >
                      <button
                        v-for="mes in availableMeses"
                        :key="mes"
                        @click="selectMes(mes)"
                        class="w-full text-left px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer"
                        :class="filterMesAno === mes ? 'text-brand-orange font-bold bg-brand-orange/5' : 'text-ink hover:bg-surface-hover'"
                      >{{ mes }}</button>
                    </div>
                  </Transition>
                </div>

                <!-- Tipo: Insumo / Composição (segmented control) -->
                <div class="flex items-center bg-canvas border border-hairline rounded-lg p-0.5 gap-0.5">
                  <button
                    @click="filterTipo = 'insumo'"
                    :class="filterTipo === 'insumo'
                      ? 'bg-brand-blue text-white shadow-sm'
                      : 'text-ink-muted hover:text-ink'"
                    class="px-3 py-2 sm:py-1 text-xs font-semibold rounded-md transition-all cursor-pointer"
                  >Insumo</button>
                  <button
                    @click="filterTipo = 'composicao'"
                    :class="filterTipo === 'composicao'
                      ? 'bg-brand-blue text-white shadow-sm'
                      : 'text-ink-muted hover:text-ink'"
                    class="px-3 py-2 sm:py-1 text-xs font-semibold rounded-md transition-all cursor-pointer"
                  >Composição</button>
                </div>

                <!-- Desonerado toggle -->
                <button
                  @click="filterDesonerado = !filterDesonerado"
                  :class="filterDesonerado
                    ? 'bg-brand-blue/10 border-brand-blue/40 text-brand-blue'
                    : 'bg-canvas border-hairline text-ink-muted hover:text-ink'"
                  class="px-3 py-2.5 sm:py-1.5 text-xs font-semibold border rounded-lg transition-all cursor-pointer"
                >
                  {{ filterDesonerado ? '✓ Desonerado' : 'Desonerado' }}
                </button>

                <!-- Redefinir (só aparece quando os filtros diferem do projeto) -->
                <button
                  v-if="filterUf !== (currentProject?.uf_obra || '') || filterTipo !== 'insumo' || filterDesonerado !== (currentProject?.sinapi_desonerado ?? false) || searchQuery"
                  @click="resetFilters"
                  class="text-xs text-ink-muted hover:text-ink underline underline-offset-2 transition-colors cursor-pointer"
                >
                  Redefinir
                </button>

              </div>
            </div>

            <div class="w-full overflow-x-auto">
              <SinapiTable
                :items="items"
                :current-page="currentPage"
                :total-pages="totalPages"
                :total-items="totalItems"
                :items-per-page="itemsPerPage"
                :is-loading="isSearching"
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
            <div class="lg:hidden flex justify-between items-center p-4 border-b border-hairline bg-surface shrink-0">
              <div class="flex items-center gap-2 text-brand-blue font-bold">
                <GitFork class="w-4 h-4 text-brand-blue" stroke-width="1.5" />
                Árvore de Custos
              </div>
              <button @click="isCartOpen = false" class="p-1.5 rounded-lg bg-canvas hover:bg-surface-hover text-ink-muted hover:text-ink transition-colors flex items-center justify-center cursor-pointer">
                <X class="w-5 h-5" stroke-width="1.5" />
              </button>
            </div>
            <div class="p-4 lg:p-0 flex-1 overflow-y-auto lg:overflow-visible">
              <ArvoreCustos
                :items="cartItems"
                :bdi="currentProject?.bdi_padrao || 0"
                :is-applying-template="isApplyingTemplate"
                @remove-item="handleRemoveFromCart"
                @update-quantity="handleUpdateQuantity"
                @add-manual-item="isManualModalOpen = true"
                @import-template="abrirImportTemplateModal"
                @aplicar-template-padrao="onSolicitarTemplate"
                @expandir="showArvoreCustosModal = true"
              />

              <!-- Exportar Planilha SINAPI -->
              <div v-if="activeOrcamentoId && cartItems.length" class="mt-4 p-4 lg:p-0 space-y-2">
                <p class="text-[10px] font-bold text-ink-muted uppercase tracking-widest mb-3 flex items-center gap-1.5">
                  <Download class="w-3.5 h-3.5 text-ink-muted" stroke-width="1.5" />
                  Exportar Planilha
                </p>
                <button
                  @click="exportarPlanilha('pdf')"
                  :disabled="!!isExporting"
                  class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-surface border border-hairline text-ink-muted hover:text-red-600 hover:border-red-300 hover:bg-red-50 dark:hover:bg-red-950/20 transition-all font-semibold text-sm shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  <Loader2 v-if="isExporting === 'pdf'" class="w-5 h-5 animate-spin" stroke-width="1.5" />
                  <FileText v-else class="w-5 h-5" stroke-width="1.5" />
                  {{ isExporting === 'pdf' ? 'Gerando PDF...' : 'Exportar PDF' }}
                </button>
                <button
                  @click="exportarPlanilha('xlsx')"
                  :disabled="!!isExporting"
                  class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-surface border border-hairline text-ink-muted hover:text-emerald-600 hover:border-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-950/20 transition-all font-semibold text-sm shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  <Loader2 v-if="isExporting === 'xlsx'" class="w-5 h-5 animate-spin" stroke-width="1.5" />
                  <Table class="w-5 h-5" stroke-width="1.5" />
                  {{ isExporting === 'xlsx' ? 'Gerando Excel...' : 'Exportar Excel' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Aba Lateral (Gatilho da Árvore de Custos) -->
        <button
          v-show="currentProject && !isCartOpen"
          @click="isCartOpen = true"
          class="lg:hidden fixed top-1/2 -translate-y-1/2 right-0 z-[60] bg-brand-blue text-white py-4 px-3 rounded-l-xl shadow-lg transition-all duration-300 flex flex-col items-center justify-center gap-1.5 focus:outline-none cursor-pointer"
        >
          <ChevronLeft class="w-5 h-5 text-white" stroke-width="2" />
          <div class="relative">
            <GitFork class="w-5 h-5 text-white" stroke-width="1.5" />
            <span v-if="cartItems.length" class="absolute -top-2 -right-2.5 bg-brand-orange text-white text-[9px] font-extrabold w-4 h-4 rounded-full flex items-center justify-center">{{ cartItems.length }}</span>
          </div>
          <span class="text-[9px] font-bold uppercase tracking-wider text-white/80 leading-none">EAP</span>
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
      :cart-items-count="cartItems.length"
      :hide-template-option="true"
      @close="isSetupModalOpen = false"
      @salvar="onSetupSuccess"
    />

    <ConfirmarTemplateModal
      :is-open="showConfirmTemplate"
      :cart-items-count="cartItems.length"
      @confirmar="executarAplicarTemplate"
      @cancelar="showConfirmTemplate = false"
    />

    <ArvoreCustosModal
      :is-open="showArvoreCustosModal"
      :items="cartItems"
      :bdi="currentProject?.bdi_padrao || 0"
      :project-id="String(route.params.id)"
      @close="showArvoreCustosModal = false"
      @refresh="fetchCart"
      @remove-item="handleRemoveFromCart"
      @update-quantity="handleUpdateQuantity"
      @add-manual-item="isManualModalOpen = true"
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
              <Star class="w-5 h-5 text-amber-500" stroke-width="1.5" />
              <h3 class="text-lg font-bold text-ink">Guardar como Modelo</h3>
            </div>
            <button @click="showTemplateModal = false" class="p-1 rounded-lg hover:bg-surface-hover transition-all flex items-center justify-center cursor-pointer">
              <X class="w-5 h-5 text-ink-muted" stroke-width="1.5" />
            </button>
          </div>
          
          <form @submit.prevent="salvarComoTemplate" class="p-6 space-y-4">
            <div v-if="templateError" class="bg-red-50 dark:bg-red-900/20 border border-red-250 dark:border-red-900/50 text-red-650 dark:text-red-400 text-sm p-3 rounded-lg flex items-start gap-2 border border-red-100 dark:border-red-500/20">
              <AlertTriangle class="w-4 h-4 text-red-600 dark:text-red-450 shrink-0" stroke-width="1.5" />
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
              <button type="submit" :disabled="isSavingTemplate || !templateForm.nome || !templateForm.area_referencia_m2" class="flex-1 py-2.5 bg-brand-primary hover:bg-brand-hover text-white rounded-lg text-sm font-semibold transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer">
                <Loader2 v-if="isSavingTemplate" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
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
              <Import class="w-5 h-5 text-brand-blue" stroke-width="1.5" />
              <h3 class="text-lg font-bold text-ink">Importar Modelo</h3>
            </div>
            <button @click="showImportTemplateModal = false" class="p-1 rounded-lg hover:bg-surface-hover transition-all flex items-center justify-center cursor-pointer">
              <X class="w-5 h-5 text-ink-muted" stroke-width="1.5" />
            </button>
          </div>

          <form @submit.prevent="confirmarImportacaoTemplate" class="p-6 space-y-4">
            <p class="text-sm text-ink-muted">Selecione um modelo existente e, se desejar, defina uma nova área para adaptar as quantidades proporcionalmente.</p>

            <div>
              <label class="block text-sm font-medium text-ink mb-1">Selecione o Modelo *</label>
              <select v-model="importTemplateForm.template_id" required class="w-full bg-canvas border border-hairline rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all text-ink">
                <option value="" disabled>Escolha um modelo salvo...</option>
                <option v-for="tpl in availableTemplates" :key="tpl.id" :value="tpl.id">
                  {{ tpl.nome }} ({{ tpl.area_referencia_m2 }} m²)
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-ink mb-1">Nova Área (m²) <span class="text-ink-muted font-normal">(opcional)</span></label>
              <input v-model.number="importTemplateForm.nova_area" @keypress="(e) => { if (!/[\d,.]/.test(e.key)) e.preventDefault() }" type="number" step="0.01" min="0.1" class="w-full bg-canvas border border-hairline rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all text-ink" placeholder="Se vazio, mantém a escala original"/>
            </div>

            <!-- Modo de importação — só aparece quando já há itens na árvore -->
            <div v-if="cartItems.length > 0" class="space-y-2">
              <label class="block text-sm font-medium text-ink">O que fazer com os itens existentes?</label>
              <div class="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  @click="importTemplateForm.modo = 'mesclar'"
                  :class="importTemplateForm.modo === 'mesclar'
                    ? 'border-brand-blue bg-brand-blue/5 text-brand-blue'
                    : 'border-hairline text-ink-muted hover:border-brand-blue/40 hover:text-ink'"
                  class="flex flex-col items-start gap-1 p-3 rounded-xl border text-left transition-all cursor-pointer"
                >
                  <span class="text-xs font-bold">Mesclar</span>
                  <span class="text-[10px] leading-tight">Adiciona os itens do modelo aos existentes</span>
                </button>
                <button
                  type="button"
                  @click="importTemplateForm.modo = 'substituir'"
                  :class="importTemplateForm.modo === 'substituir'
                    ? 'border-brand-orange bg-brand-orange/5 text-brand-orange'
                    : 'border-hairline text-ink-muted hover:border-brand-orange/40 hover:text-ink'"
                  class="flex flex-col items-start gap-1 p-3 rounded-xl border text-left transition-all cursor-pointer"
                >
                  <span class="text-xs font-bold">Substituir</span>
                  <span class="text-[10px] leading-tight">Remove os atuais e importa o modelo</span>
                </button>
              </div>
            </div>

            <div class="flex gap-3 pt-2">
              <button type="button" @click="showImportTemplateModal = false" class="flex-1 py-2.5 border border-hairline rounded-lg text-sm font-medium text-ink-muted hover:bg-canvas transition-all cursor-pointer">Cancelar</button>
              <button type="submit" :disabled="isImportingTemplate || !importTemplateForm.template_id" class="flex-1 py-2.5 bg-brand-blue hover:bg-brand-blue-hover text-white rounded-lg text-sm font-semibold transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer">
                <Loader2 v-if="isImportingTemplate" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
                {{ isImportingTemplate ? 'Importando...' : 'Importar Modelo' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>


  </div>
</template>
