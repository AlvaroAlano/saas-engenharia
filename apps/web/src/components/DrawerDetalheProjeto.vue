<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { formatCurrency } from '../utils/formatters'
import SetupOrcamentoModal from './modals/SetupOrcamentoModal.vue'
import RejeicaoDocumentoModal from './modals/RejeicaoDocumentoModal.vue'
import {
  X,
  Pen,
  HardHat,
  Info,
  UserCheck,
  Check,
  Copy,
  MessageSquare,
  Share2,
  Loader2,
  CheckCircle2,
  Lock,
  FolderOpen,
  Eye,
  XCircle,
  FileText,
  User,
  History,
  IdCard,
  Home,
  Users
} from 'lucide-vue-next'

const iconMap = {
  badge: IdCard,
  home_work: Home,
  family_restroom: Users
}

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  project: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'update'])

const router = useRouter()

const isLoadingHistory = ref(false)
const historico = ref([])
const portalUrl = ref('')
const portalPin = ref('')
const isLoadingPortal = ref(false)

const isQualificacaoCopied = ref(false)
const isPortalCopied = ref(false)

// Modals State
const isSetupOpen = ref(false)
const isRejeicaoModalOpen = ref(false)
const selectedDocParaRejeicao = ref(null)

const docCategoriaLabels = {
  identidade:   { label: 'Identidade',   badge: 'RG/CNH',      icon: 'badge' },
  residencia:   { label: 'Residência',   badge: 'Comprovante', icon: 'home_work' },
  estado_civil: { label: 'Estado Civil', badge: 'Certidão',    icon: 'family_restroom' }
}

const statusColunaLabels = {
  estimativa_enviada: { label: 'Estimativa Enviada', class: 'bg-orange-55/10 text-orange-600 dark:text-orange-400 border-orange-100 dark:border-orange-950/30' },
  contrato_pendente: { label: 'Contrato Pendente', class: 'bg-blue-55/10 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-950/30' },
  engenharia_caixa: { label: 'Engenharia & Caixa', class: 'bg-indigo-55/10 text-indigo-600 dark:text-indigo-400 border-indigo-100 dark:border-indigo-950/30' },
  obra_liberada: { label: 'Obra Liberada', class: 'bg-violet-55/10 text-violet-600 dark:text-violet-400 border-violet-100 dark:border-violet-950/30' }
}

const qualificacaoUrl = computed(() => {
  if (!props.project?.id) return ''
  return `${window.location.origin}/estimativa/${props.project.id}`
})

const getDocumentStatus = (categoria) => {
  const isEstimativa = props.project?.coluna === 'estimativa_enviada'
  
  if (!props.project?.documentos) {
    if (isEstimativa) {
      return { text: 'Não solicitado', class: 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-zinc-800/30 dark:text-zinc-500 dark:border-zinc-800/50', isPending: true }
    }
    return { text: 'Pendente', class: 'bg-amber-55/10 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-950/30', isPending: true }
  }
  
  const doc = props.project.documentos.find(d => d.categoria === categoria)
  if (!doc) {
    if (isEstimativa) {
      return { text: 'Não solicitado', class: 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-zinc-800/30 dark:text-zinc-500 dark:border-zinc-800/50', isPending: true }
    }
    return { text: 'Pendente', class: 'bg-amber-55/10 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-950/30', isPending: true }
  }
  
  if (!doc.url && doc.status === 'rejeitado') {
    return { text: 'Recusado', class: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/20 dark:text-red-400 dark:border-red-900/30', isRejected: true, motivo: doc.motivo }
  }
  
  if (doc.url) {
    if (props.project.status === 'docs_validados' || doc.status === 'aprovado') {
      return { text: 'Aprovado', class: 'bg-emerald-55/10 text-emerald-600 dark:text-emerald-400 border-emerald-100 dark:border-emerald-950/30', doc }
    }
    return { text: 'Em Análise', class: 'bg-amber-55/10 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-950/30', doc }
  }
  
  if (isEstimativa) {
    return { text: 'Não solicitado', class: 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-zinc-800/30 dark:text-zinc-500 dark:border-zinc-800/50', isPending: true }
  }
  return { text: 'Pendente', class: 'bg-amber-55/10 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-950/30', isPending: true }
}

const temDocumentosPendentesRevisao = computed(() => {
  if (props.project?.coluna !== 'contrato_pendente') return false
  if (props.project?.status === 'docs_validados') return false
  return Array.isArray(props.project?.documentos) && props.project.documentos.some(doc => !!doc.url)
})

const documentsList = computed(() => {
  return ['identidade', 'residencia', 'estado_civil'].map(cat => {
    const statusInfo = getDocumentStatus(cat)
    return {
      categoria: cat,
      label: docCategoriaLabels[cat].label,
      badge: docCategoriaLabels[cat].badge,
      icon: docCategoriaLabels[cat].icon,
      status: statusInfo
    }
  })
})

const getContractStatus = computed(() => {
  if (props.project?.status_assinatura === 'assinado') {
    return { text: 'Assinado', class: 'bg-emerald-55/10 text-emerald-600 dark:text-emerald-400 border-emerald-100 dark:border-emerald-950/30' }
  }
  if (props.project?.status_assinatura === 'pendente') {
    return { text: 'Aguardando Assinatura', class: 'bg-blue-55/10 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-950/30' }
  }
  if (props.project?.contrato_gerado) {
    return { text: 'Gerado (Não enviado)', class: 'bg-amber-55/10 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-950/30' }
  }
  return { text: 'Não Gerado', class: 'bg-slate-50 text-slate-500 border-slate-200 dark:bg-zinc-800/50 dark:text-zinc-400 dark:border-zinc-800' }
})

const fetchHistorico = async () => {
  if (!props.project?.id) return
  isLoadingHistory.value = true
  try {
    const res = await axios.get(`/projetos/${props.project.id}/historico`)
    if (res.data && res.data.success) {
      historico.value = res.data.data.slice(0, 5) // Top 5
    }
  } catch (error) {
    console.error('Erro ao buscar histórico do projeto:', error)
  } finally {
    isLoadingHistory.value = false
  }
}

const fetchPortalLink = async () => {
  if (!props.project?.id) return
  isLoadingPortal.value = true
  try {
    const res = await axios.get(`/portal/projetos/${props.project.id}/link`)
    if (res.data && res.data.url_publica) {
      const urlParts = res.data.url_publica.split('/')
      const token = urlParts[urlParts.length - 1]
      portalUrl.value = `${window.location.origin}/portal/${token}`
      portalPin.value = res.data.pin_acesso
    } else {
      portalUrl.value = ''
      portalPin.value = ''
    }
  } catch (error) {
    console.error('Erro ao carregar link do portal:', error)
    portalUrl.value = ''
    portalPin.value = ''
  } finally {
    isLoadingPortal.value = false
  }
}

const handleWhatsAppShare = () => {
  if (!portalUrl.value) return
  const msg = `Olá ${props.project.cliente_nome}! Segue o link para acompanhar a evolução da sua obra em tempo real:\n${portalUrl.value}\n\nPIN de acesso: ${portalPin.value}`
  const telefoneLimpo = props.project.telefone ? props.project.telefone.replace(/\D/g, '') : ''
  window.open(`https://wa.me/${telefoneLimpo}?text=${encodeURIComponent(msg)}`, '_blank')
}

const handleCopyLink = () => {
  if (!portalUrl.value || isPortalCopied.value) return
  navigator.clipboard.writeText(portalUrl.value)
  isPortalCopied.value = true
  setTimeout(() => {
    isPortalCopied.value = false
  }, 2000)
}

const handleCopyQualificacao = () => {
  if (!qualificacaoUrl.value || isQualificacaoCopied.value) return
  navigator.clipboard.writeText(qualificacaoUrl.value)
  isQualificacaoCopied.value = true
  setTimeout(() => {
    isQualificacaoCopied.value = false
  }, 2000)
}

const handleWhatsAppQualificacao = () => {
  if (!qualificacaoUrl.value) return
  const msg = `Olá ${props.project.cliente_nome}! Segue o link para realizar a simulação da sua obra e enviar os documentos:\n${qualificacaoUrl.value}`
  const telefoneLimpo = props.project.telefone ? props.project.telefone.replace(/\D/g, '') : ''
  window.open(`https://wa.me/${telefoneLimpo}?text=${encodeURIComponent(msg)}`, '_blank')
}

const formatarData = (dataStr) => {
  if (!dataStr) return ''
  try {
    const dateObj = new Date(dataStr.includes('T') ? dataStr : dataStr.replace(' ', 'T') + 'Z')
    if (isNaN(dateObj.getTime())) {
      const partes = dataStr.split(' ')
      if (partes.length < 2) return dataStr
      const dataPart = partes[0]
      const horaPart = partes[1].slice(0, 5)
      const dataSplit = dataPart.split('-')
      if (dataSplit.length < 3) return dataStr
      const [ano, mes, dia] = dataSplit
      return `${dia}/${mes}/${ano} ${horaPart}`
    }
    const dia = String(dateObj.getDate()).padStart(2, '0')
    const mes = String(dateObj.getMonth() + 1).padStart(2, '0')
    const ano = dateObj.getFullYear()
    const hora = String(dateObj.getHours()).padStart(2, '0')
    const minuto = String(dateObj.getMinutes()).padStart(2, '0')
    return `${dia}/${mes}/${ano} ${hora}:${minuto}`
  } catch (e) {
    const partes = dataStr.split(' ')
    if (partes.length < 2) return dataStr
    const dataPart = partes[0]
    const horaPart = partes[1].slice(0, 5)
    const dataSplit = dataPart.split('-')
    if (dataSplit.length < 3) return dataStr
    const [ano, mes, dia] = dataSplit
    return `${dia}/${mes}/${ano} ${horaPart}`
  }
}

const irParaOrcamento = () => {
  router.push(`/orcamento/${props.project.id}`)
  emit('close')
}

const closeDrawer = () => {
  emit('close')
}

const abrirModalRejeicao = (doc) => {
  selectedDocParaRejeicao.value = doc
  isRejeicaoModalOpen.value = true
}

const onDocRejeitado = () => {
  emit('update')
}

const onSetupSuccess = () => {
  isSetupOpen.value = false
  emit('update')
}

const isLiberandoObra = ref(false)

const liberarObra = async () => {
  if (isLiberandoObra.value) return
  isLiberandoObra.value = true
  try {
    await axios.patch(`/projetos/${props.project.id}`, {
      coluna: 'obra_liberada',
      status: 'liberada'
    })
    props.project.coluna = 'obra_liberada'
    props.project.status = 'liberada'
    emit('update')
  } catch (error) {
    console.error('Erro ao liberar obra:', error)
    alert('Erro ao liberar a obra. Tente novamente.')
  } finally {
    isLiberandoObra.value = false
  }
}

const validarDocumentos = async () => {
  try {
    const docsAtualizados = (props.project.documentos || []).map(doc => {
      if (doc.url) {
        return { ...doc, status: 'aprovado', done: true }
      }
      return doc
    })

    await axios.patch(`/projetos/${props.project.id}`, {
      status: 'docs_validados',
      documentos: docsAtualizados
    })
    
    // Atualiza localmente
    props.project.status = 'docs_validados'
    props.project.documentos = docsAtualizados
    
    emit('update')
  } catch (error) {
    console.error('Erro ao validar documentos:', error)
    alert('Erro ao validar documentos. Tente novamente.')
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    fetchHistorico()
    fetchPortalLink()
  }
})
</script>

<template>
  <Teleport to="body">
    <!-- Overlay backdrop -->
    <Transition
      enter-active-class="transition-opacity duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div 
        v-if="isOpen" 
        class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100] flex items-center justify-center p-0 lg:p-4" 
        style="z-index: 100;"
        @click.self="closeDrawer"
      >
        <!-- Modal Panel -->
        <div 
          class="bg-canvas border border-hairline shadow-2xl flex flex-col w-full h-full lg:w-[600px] lg:h-auto lg:max-h-[85vh] lg:rounded-2xl overflow-hidden animate-in zoom-in duration-200"
          @click.stop
        >
          <!-- Header -->
          <div class="px-6 py-5 border-b border-hairline bg-surface shrink-0 flex items-center justify-between">
            <div>
              <span class="text-[10px] font-bold text-ink-muted uppercase tracking-wider block">Detalhamento do Projeto</span>
              <h2 class="text-lg font-bold text-ink truncate max-w-[320px] mt-0.5" :title="project.titulo_projeto || project.cliente_nome">
                {{ project.titulo_projeto || 'Sem título' }}
              </h2>
            </div>
            <button @click="closeDrawer" class="p-2 rounded-xl bg-canvas text-ink-muted hover:bg-surface-hover hover:text-ink transition-colors cursor-pointer flex items-center justify-center">
              <X class="w-5 h-5" stroke-width="1.5" />
            </button>
          </div>

          <!-- Scrollable Content -->
          <div class="p-6 space-y-6 flex-1 overflow-y-auto">
            
            <!-- 1. Identificação -->
            <div class="bg-surface border border-hairline p-5 rounded-xl shadow-sm space-y-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs text-ink-muted">Cliente</p>
                  <p class="text-sm font-bold text-ink mt-0.5">{{ project.cliente_nome }}</p>
                </div>
                <div class="flex items-center gap-2">
                  <!-- Botão Editar Configurações da Obra -->
                  <button 
                    @click="isSetupOpen = true"
                    class="p-1.5 rounded-lg bg-canvas border border-hairline hover:bg-surface-hover text-ink-muted hover:text-ink transition-colors flex items-center justify-center cursor-pointer shadow-sm"
                    title="Editar Configurações da Obra"
                  >
                    <Pen class="w-4 h-4" stroke-width="1.5" />
                  </button>
                  <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full border shrink-0', statusColunaLabels[project.coluna]?.class]">
                    {{ statusColunaLabels[project.coluna]?.label || project.coluna }}
                  </span>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4 pt-3 border-t border-hairline">
                <div>
                  <p class="text-[11px] text-ink-muted">UF da Obra</p>
                  <p class="text-xs font-semibold text-ink mt-0.5">{{ project.uf_obra || 'Não informado' }}</p>
                </div>
                <div>
                  <p class="text-[11px] text-ink-muted">BDI Padrão</p>
                  <p class="text-xs font-semibold text-ink mt-0.5">{{ project.bdi_padrao != null ? `${project.bdi_padrao}%` : '20%' }}</p>
                </div>
                <div>
                  <p class="text-[11px] text-ink-muted">Mês SINAPI</p>
                  <p class="text-xs font-semibold text-ink mt-0.5">{{ project.sinapi_mes_ano || 'Não informado' }}</p>
                </div>
                <div>
                  <p class="text-[11px] text-ink-muted">Metragem (m²)</p>
                  <p class="text-xs font-mono font-semibold text-ink mt-0.5">{{ project.tamanho || '-' }} m²</p>
                </div>
              </div>
              
              <div class="pt-3 border-t border-hairline flex items-center justify-between">
                <p class="text-xs text-ink-muted">Valor Total Estimado</p>
                <p class="text-base font-bold text-ink">{{ formatCurrency(project.valor, 'Aguardando preenchimento') }}</p>
              </div>
            </div>

            <!-- 2. Ações Rápidas (Acesso & Compartilhamento) -->
            <div class="space-y-4">
              <!-- Orçamento Completo Visível Apenas em Engenharia & Caixa ou Obra Liberada -->
              <button 
                v-if="project.coluna === 'engenharia_caixa' || project.coluna === 'obra_liberada'"
                @click="irParaOrcamento"
                class="w-full py-3 bg-brand-primary hover:bg-brand-hover text-white rounded-xl font-semibold text-sm transition-all shadow-md flex items-center justify-center gap-2 group cursor-pointer"
              >
                <HardHat class="w-4 h-4 group-hover:translate-x-0.5 transition-transform" stroke-width="1.5" />
                Acessar Orçamento Completo
              </button>

              <div v-else-if="project.coluna === 'estimativa_enviada'" class="p-4 bg-amber-55/10 border border-amber-100 dark:border-amber-950/30 rounded-xl flex items-start gap-3">
                <Info class="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" stroke-width="1.5" />
                <p class="text-xs text-amber-800 dark:text-amber-300 leading-relaxed font-medium">
                  O orçamento detalhado estará disponível após o cliente realizar a simulação e enviar os documentos para análise.
                </p>
              </div>

              <div v-else-if="project.coluna === 'contrato_pendente'" class="p-4 bg-amber-55/10 border border-amber-100 dark:border-amber-950/30 rounded-xl flex items-start gap-3">
                <Info class="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" stroke-width="1.5" />
                <p class="text-xs text-amber-800 dark:text-amber-300 leading-relaxed font-medium">
                  O orçamento detalhado estará disponível após a validação dos documentos e a assinatura do contrato (esteira Engenharia & Caixa).
                </p>
              </div>

              <!-- B2C Jornada de Qualificação -->
              <div v-if="project.coluna === 'estimativa_enviada' || project.coluna === 'contrato_pendente'" class="bg-surface border border-hairline p-4 rounded-xl shadow-sm space-y-3">
                <div class="flex items-center gap-2">
                  <UserCheck class="w-4 h-4 text-blue-600" stroke-width="1.5" />
                  <span class="text-xs font-bold text-ink uppercase tracking-wider">Jornada de Qualificação (B2C)</span>
                </div>
                <p class="text-xs text-ink-muted leading-relaxed">
                  Link para o cliente realizar a simulação Caixa, especificar padrão/tamanho da obra e anexar documentos iniciais.
                </p>
                <div class="space-y-3">
                  <div class="flex items-center gap-2">
                    <div class="flex-1 bg-canvas border border-hairline rounded-lg px-3 py-2 text-xs font-mono text-ink select-all overflow-x-auto whitespace-nowrap">
                      {{ qualificacaoUrl }}
                    </div>
                    <button 
                      @click="handleCopyQualificacao"
                      class="p-2 rounded-lg bg-canvas border border-hairline hover:bg-surface-hover text-ink-muted hover:text-ink transition-colors cursor-pointer flex items-center justify-center shrink-0"
                      title="Copiar Link"
                    >
                      <Check v-if="isQualificacaoCopied" class="w-4 h-4 text-emerald-600" stroke-width="1.5" />
                      <Copy v-else class="w-4 h-4" stroke-width="1.5" />
                    </button>
                  </div>
                  <div class="flex justify-end">
                    <button 
                      @click="handleWhatsAppQualificacao"
                      class="px-3 py-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                    >
                      <MessageSquare class="w-4 h-4 text-emerald-700" stroke-width="1.5" />
                      Compartilhar no WhatsApp
                    </button>
                  </div>
                </div>
              </div>

              <!-- B2C Portal de Acompanhamento (Obra Liberada) -->
              <div v-if="project.coluna === 'obra_liberada'" class="bg-surface border border-hairline p-4 rounded-xl shadow-sm space-y-3">
                <div class="flex items-center gap-2">
                  <Share2 class="w-4 h-4 text-indigo-600" stroke-width="1.5" />
                  <span class="text-xs font-bold text-ink uppercase tracking-wider">Portal de Acompanhamento</span>
                </div>
                <p class="text-xs text-ink-muted leading-relaxed">
                  Este cliente possui acesso ao Portal da Obra para acompanhar o feed e a medição Caixa em tempo real.
                </p>
                <div v-if="isLoadingPortal" class="flex items-center gap-2 text-xs text-ink-muted">
                  <Loader2 class="w-4 h-4 animate-spin text-brand-primary" stroke-width="1.5" />
                  Carregando link do portal...
                </div>
                <div v-else class="space-y-3">
                  <div class="flex items-center gap-2">
                    <div class="flex-1 bg-canvas border border-hairline rounded-lg px-3 py-2 text-xs font-mono text-ink select-all overflow-x-auto whitespace-nowrap">
                      {{ portalUrl }}
                    </div>
                    <button 
                      @click="handleCopyLink"
                      class="p-2 rounded-lg bg-canvas border border-hairline hover:bg-surface-hover text-ink-muted hover:text-ink transition-colors cursor-pointer flex items-center justify-center shrink-0"
                      title="Copiar Link"
                    >
                      <Check v-if="isPortalCopied" class="w-4 h-4 text-emerald-600" stroke-width="1.5" />
                      <Copy v-else class="w-4 h-4" stroke-width="1.5" />
                    </button>
                  </div>
                  <div class="flex items-center justify-between gap-3">
                    <div class="text-xs">
                      <span class="text-ink-muted">PIN de Acesso: </span>
                      <span class="font-bold font-mono text-ink">{{ portalPin }}</span>
                    </div>
                    <button 
                      @click="handleWhatsAppShare"
                      class="px-3 py-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                    >
                      <MessageSquare class="w-4 h-4 text-emerald-700" stroke-width="1.5" />
                      Enviar WhatsApp
                    </button>
                  </div>
                </div>
              </div>

              <!-- Botão Liberar Obra (Engenharia & Caixa → Obra Liberada) -->
              <button
                v-if="project.coluna === 'engenharia_caixa'"
                @click="liberarObra"
                :disabled="isLiberandoObra"
                class="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-xl font-semibold text-sm transition-all shadow-md flex items-center justify-center gap-2 group cursor-pointer"
              >
                <Loader2 v-if="isLiberandoObra" class="w-4 h-4 animate-spin" stroke-width="1.5" />
                <CheckCircle2 v-else class="w-4 h-4" stroke-width="1.5" />
                {{ isLiberandoObra ? 'Liberando...' : 'Aprovar e Liberar Obra' }}
              </button>

              <!-- B2C Portal Bloqueado (Engenharia & Caixa) -->
              <div v-if="project.coluna === 'engenharia_caixa'" class="bg-surface/60 border border-hairline p-4 rounded-xl shadow-sm space-y-2.5">
                <div class="flex items-center gap-2 text-ink-muted">
                  <Lock class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
                  <span class="text-xs font-bold uppercase tracking-wider">Acesso ao Portal de Obra</span>
                </div>
                <p class="text-xs text-ink-muted leading-relaxed font-medium">
                  O Portal de Acompanhamento da Obra (feed em tempo real e medições da Caixa) será liberado automaticamente após a assinatura do contrato e a liberação da obra (coluna Obra Liberada).
                </p>
              </div>
            </div>

            <!-- 3. Vault de Documentos -->
            <div class="bg-surface border border-hairline p-5 rounded-xl shadow-sm space-y-4">
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <FolderOpen class="w-4 h-4 text-blue-600" stroke-width="1.5" />
                  <span class="text-xs font-bold text-ink uppercase tracking-wider">Cofre de Documentos</span>
                  <span 
                    v-if="temDocumentosPendentesRevisao" 
                    class="w-2 h-2 rounded-full bg-blue-500 animate-pulse shrink-0 cursor-help"
                    title="Documento pendente de visualização"
                  ></span>
                </div>
                <!-- Botão Aprovar Todos (visível se tiver documentos pendentes de validação) -->
                <button
                  v-if="project.coluna === 'contrato_pendente' && project.status !== 'docs_validados'"
                  @click="validarDocumentos"
                  class="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-lg transition-colors text-xs font-bold flex items-center gap-1.5 cursor-pointer shadow-sm"
                >
                  <CheckCircle2 class="w-4 h-4 text-emerald-700" stroke-width="1.5" />
                  Aprovar Todos
                </button>
              </div>
              
              <ul class="space-y-3">
                <li 
                  v-for="doc in documentsList" 
                  :key="doc.categoria"
                  class="flex flex-col gap-2 p-3 rounded-lg border border-hairline bg-canvas/50"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <component :is="iconMap[doc.icon]" class="w-4 h-4 text-blue-500" stroke-width="1.5" />
                      <span class="text-xs font-bold text-ink">{{ doc.label }}</span>
                    </div>
                    <span :class="['text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider', doc.status.class]">
                      {{ doc.status.text }}
                    </span>
                  </div>
                  
                  <div v-if="doc.status.doc" class="flex items-center justify-between text-xs mt-1 bg-surface p-2 rounded border border-hairline">
                    <span class="text-ink-muted truncate max-w-[200px]" :title="doc.status.doc.name">{{ doc.status.doc.name }}</span>
                    <div class="flex items-center gap-2 shrink-0">
                      <a :href="doc.status.doc.url" target="_blank" class="text-brand-primary hover:underline flex items-center gap-1 font-semibold">
                        <Eye class="w-3.5 h-3.5" stroke-width="1.5" />
                        Visualizar
                      </a>
                      <!-- Botão Recusar Documento específico -->
                      <button 
                        v-if="project.coluna === 'contrato_pendente' && project.status !== 'docs_validados' && doc.status.text !== 'Aprovado' && doc.status.doc.url" 
                        @click.stop="abrirModalRejeicao(doc.status.doc)" 
                        class="text-red-650 hover:text-white hover:bg-red-600 transition-colors flex items-center gap-1 border border-red-200 bg-red-50/50 px-2 py-0.5 rounded cursor-pointer font-bold"
                      >
                        <XCircle class="w-3.5 h-3.5" stroke-width="1.5" />
                        Recusar
                      </button>
                    </div>
                  </div>
                  
                  <div v-else-if="doc.status.isRejected" class="text-xs text-red-600 bg-red-50/50 p-2 rounded border border-red-100 leading-relaxed">
                    <span class="font-bold">Motivo da recusa:</span> {{ doc.status.motivo }}
                  </div>
                </li>
              </ul>
            </div>

            <!-- 4. Contrato de Prestação de Serviços -->
            <div class="bg-surface border border-hairline p-5 rounded-xl shadow-sm space-y-4">
              <div class="flex items-center gap-2">
                <FileText class="w-4 h-4 text-emerald-600" stroke-width="1.5" />
                <span class="text-xs font-bold text-ink uppercase tracking-wider">Contrato de Serviço</span>
              </div>

              <div class="flex items-center justify-between p-3 rounded-lg border border-hairline bg-canvas/50">
                <span class="text-xs text-ink-muted">Status do Contrato</span>
                <span :class="['text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider', getContractStatus.class]">
                  {{ getContractStatus.text }}
                </span>
              </div>
              
              <!-- ZapSign Signature Progression -->
              <div v-if="project.status_assinatura === 'pendente' || project.status_assinatura === 'assinado'" class="p-3 bg-canvas/30 rounded-lg border border-hairline space-y-2">
                <p class="text-[10px] font-bold text-ink-muted uppercase tracking-wider">Assinaturas</p>
                <div class="flex items-center justify-between text-xs">
                  <div class="flex items-center gap-1.5">
                    <User class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
                    <span class="font-medium" :class="project.engenheiro_assinou ? 'text-emerald-600 font-bold' : 'text-ink-muted'">Engenheiro</span>
                  </div>
                  <span class="text-[10px] font-bold" :class="project.engenheiro_assinou ? 'text-emerald-600' : 'text-ink-muted'">
                    {{ project.engenheiro_assinou ? 'Assinou' : 'Pendente' }}
                  </span>
                </div>
                <div class="flex items-center justify-between text-xs">
                  <div class="flex items-center gap-1.5">
                    <User class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
                    <span class="font-medium" :class="project.cliente_assinou ? 'text-emerald-600 font-bold' : 'text-ink-muted'">Cliente</span>
                  </div>
                  <span class="text-[10px] font-bold" :class="project.cliente_assinou ? 'text-emerald-600' : 'text-ink-muted'">
                    {{ project.cliente_assinou ? 'Assinou' : 'Pendente' }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 5. Histórico de Auditoria & Notas -->
            <div class="bg-surface border border-hairline p-5 rounded-xl shadow-sm space-y-4">
              <div class="flex items-center gap-2">
                <History class="w-4 h-4 text-indigo-600" stroke-width="1.5" />
                <span class="text-xs font-bold text-ink uppercase tracking-wider">Histórico Recente (Últimos 5)</span>
              </div>

              <!-- Loading State -->
              <div v-if="isLoadingHistory" class="flex flex-col items-center justify-center py-6 text-ink-muted text-xs gap-2">
                <Loader2 class="w-6 h-6 animate-spin text-brand-primary" stroke-width="1.5" />
                Carregando histórico...
              </div>

              <!-- Empty State -->
              <div v-else-if="historico.length === 0" class="text-center py-4 text-xs text-ink-muted">
                Nenhuma entrada de histórico encontrada.
              </div>

              <!-- Timeline -->
              <div v-else class="relative border-l-2 border-hairline ml-3 space-y-5 py-1">
                <div v-for="item in historico" :key="item.id" class="relative pl-6">
                  <!-- Dot -->
                  <div class="absolute -left-[7px] top-1.5 w-3 h-3 bg-brand-primary rounded-full ring-4 ring-surface"></div>
                  <div class="space-y-0.5">
                    <div class="flex items-center justify-between text-[10px] text-ink-muted">
                      <span class="font-bold text-ink">{{ item.autor }}</span>
                      <span>{{ formatarData(item.data) }}</span>
                    </div>
                    <p class="text-xs text-ink leading-relaxed font-medium bg-canvas/30 p-2 rounded border border-hairline mt-1">
                      {{ item.texto }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </Transition>

    <!-- Modais adicionais -->
    <RejeicaoDocumentoModal
      v-if="isRejeicaoModalOpen"
      :is-open="isRejeicaoModalOpen"
      :projeto-id="project.id"
      :documento="selectedDocParaRejeicao"
      @close="isRejeicaoModalOpen = false"
      @rejeitado="onDocRejeitado"
    />

    <SetupOrcamentoModal
      v-if="isSetupOpen"
      :is-open="isSetupOpen"
      :project="project"
      @close="isSetupOpen = false"
      @salvar="onSetupSuccess"
    />
  </Teleport>
</template>
