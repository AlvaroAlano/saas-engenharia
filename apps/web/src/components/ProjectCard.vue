<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useProfile } from '../composables/useProfile'
import SetupOrcamentoModal from './modals/SetupOrcamentoModal.vue'
import EditProjectModal from './EditProjectModal.vue'
import DiarioObraModal from './modals/DiarioObraModal.vue'
import RejeicaoDocumentoModal from './modals/RejeicaoDocumentoModal.vue'
import DrawerDetalheProjeto from './DrawerDetalheProjeto.vue'
import { formatCurrency } from '../utils/formatters'
import { 
  Maximize2, MoreHorizontal, MessageSquare, Camera, Pen, History, 
  Loader2, CheckCircle2, Copy, Undo, FileSignature, Archive, FolderOpen, 
  User, Home, Users, FileText, Link, AlertTriangle, HelpCircle, Send, 
  Eye, X, ExternalLink, Download, Info, Plus, ChevronDown, HardHat
} from 'lucide-vue-next'

const { empresa } = useProfile()
const router = useRouter()

const isDrawerOpen = ref(false)
const isRejeicaoModalOpen = ref(false)
const selectedDocParaRejeicao = ref(null)

const abrirModalRejeicao = (doc) => {
  selectedDocParaRejeicao.value = doc
  isRejeicaoModalOpen.value = true
}

const onDocRejeitado = () => {
  emit('update')
}


const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update', 'projeto-arquivado'])

const isMenuOpen = ref(false)
const isCopied = ref(false)

const temDocumentosPendentesRevisao = computed(() => {
  if (props.project.coluna !== 'contrato_pendente') return false
  if (props.project.status === 'docs_validados') return false
  return Array.isArray(props.project.documentos) && props.project.documentos.some(doc => !!doc.url)
})

// Estado do Modal de Contrato
const isContractModalOpen = ref(false)
const isGeneratingContract = ref(false)
const selectedTemplateId = ref('')
const pdfPreviewUrl = ref(null)
const templates = ref([])
const isLoadingTemplates = ref(false)

const isDocsExpanded = ref(false)

const docCategoriaLabels = {
  identidade:   { label: 'Identidade',   badge: 'RG/CNH',      icon: User },
  residencia:   { label: 'Residência',   badge: 'Comprovante', icon: Home },
  estado_civil: { label: 'Estado Civil', badge: 'Certidão',    icon: Users }
}
const isAdvancing = ref(false)
const isSendingToZapSign = ref(false)
const isApprovingContract = ref(false)
const isSetupModalOpen = ref(false)

const isEditModalOpen = ref(false)
const isDiarioModalOpen = ref(false)

const isBypassing = ref(false)

const toggleDocs = () => {
  isDocsExpanded.value = !isDocsExpanded.value
}

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const closeMenu = () => {
  isMenuOpen.value = false
}

// Fechar menu se clicar fora (simplificado)
onMounted(() => {
  document.addEventListener('click', closeMenu)
})
onUnmounted(() => {
  document.removeEventListener('click', closeMenu)
})

const leftBorderClass = computed(() => {
  // Coluna 1: Estimativa Enviada — Aguardando ação do CLIENTE
  if (props.project.coluna === 'estimativa_enviada') {
    return 'border-l-orange-400'
  }

  // Coluna 2: Contrato Pendente
  if (props.project.coluna === 'contrato_pendente') {
    // Docs validados + contrato já gerado — próximo passo: marcar assinado
    if (props.project.contrato_gerado) return 'border-l-emerald-500'
    // Docs validados mas sem contrato — Ação: Gerar Contrato
    if (props.project.status === 'docs_validados') return 'border-l-blue-500'
    // Docs ainda não validados — Ação: Validar Documentos
    return 'border-l-emerald-500'
  }

  // Coluna 3: Engenharia & Caixa — Ação: Orçamento SINAPI
  if (props.project.coluna === 'engenharia_caixa') {
    return 'border-l-indigo-500'
  }

  // Coluna 4: Obra Liberada
  if (props.project.coluna === 'obra_liberada') {
    return 'border-l-violet-500'
  }

  return 'border-l-slate-300'
})

const ctaInfo = computed(() => {
  if (props.project.status === 'docs_pendentes') {
    return { text: 'Aguardando Reenvio', class: 'bg-white border border-amber-200 text-amber-700 cursor-not-allowed opacity-75' }
  }
  if (props.project.coluna === 'estimativa_enviada' && props.project.status === 'aguardando_cliente') {
    return {
      text: isCopied.value ? 'Copiado!' : 'Copiar Link',
      icon: isCopied.value ? CheckCircle2 : Link,
      class: isCopied.value 
        ? 'bg-emerald-500 text-white border border-emerald-500 shadow-sm' 
        : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50',
      action: 'copy_link'
    }
  }
  if (props.project.coluna === 'estimativa_enviada') {
    return { text: 'Cobrar Cliente', class: 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50' }
  }
  if (props.project.status === 'docs_incompletos') {
    return { text: 'Lembrar Cliente', class: 'bg-white border border-amber-200 text-amber-700 hover:bg-amber-50' }
  }
  if (props.project.status === 'docs_validados') {
    // Estado A: Não Gerado
    if (!props.project.contrato_gerado) {
      return { text: 'Gerar Contrato', icon: FileText, class: 'bg-emerald-600 text-white hover:bg-emerald-700 border border-emerald-600 shadow-sm', action: 'generate_contract' }
    }
    // Estado B: Gerado/Aprovado mas não enviado
    if (!props.project.status_assinatura || props.project.status_assinatura === 'nao_enviado') {
      return { text: '✒️ Enviar ZapSign', class: 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200', action: 'send_to_zapsign' }
    }
    // Estado Final: Ambos assinaram
    if (props.project.status_assinatura === 'assinado') {
      return { text: 'Finalizar', icon: CheckCircle2, class: 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm', action: 'advance_phase' }
    }
  }
  return null
})

const handleCtaClick = () => {
  if (ctaInfo.value && ctaInfo.value.action === 'copy_link') {
    const url = `${window.location.origin}/estimativa/${props.project.id}`
    navigator.clipboard.writeText(url)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } else if (ctaInfo.value && ctaInfo.value.action === 'generate_contract') {
    openContractModal()
  } else if (ctaInfo.value && ctaInfo.value.action === 'send_to_zapsign') {
    enviarParaZapSign()
  } else if (ctaInfo.value && ctaInfo.value.action === 'advance_phase') {
    avancarParaEngenharia()
  } else if (ctaInfo.value && ctaInfo.value.action === 'send_portal_access') {
    sendPortalAccess()
  }
}

const isSendingPortalAccess = ref(false)
const isCopyingPortalLink = ref(false)
const hasCopiedPortalLink = ref(false)

const sendPortalAccess = async () => {
  if (isSendingPortalAccess.value) return
  isSendingPortalAccess.value = true
  try {
    const res = await axios.get(`/portal/projetos/${props.project.id}/link`)
    if (res.data && res.data.url_publica) {
      // Extrai o token e reconstrói a URL baseada no ambiente atual (localhost ou produção)
      const urlParts = res.data.url_publica.split('/')
      const token = urlParts[urlParts.length - 1]
      const dynamicUrl = `${window.location.origin}/portal/${token}`
      const pin = res.data.pin_acesso
      const msg = `Olá ${props.project.cliente_nome}! Segue o link para acompanhar a evolução da sua obra em tempo real:\n${dynamicUrl}\n\nPIN de acesso: ${pin}`
      
      const telefoneLimpo = props.project.telefone ? props.project.telefone.replace(/\D/g, '') : ''
      window.open(`https://wa.me/${telefoneLimpo}?text=${encodeURIComponent(msg)}`, '_blank')
    } else {
      alert('Não foi possível obter ou criar o link do portal.')
    }
  } catch (error) {
    console.error('Erro ao buscar link do portal:', error)
    alert(error.response?.data?.detail || 'Erro ao gerar/recuperar o acesso ao portal do cliente.')
  } finally {
    isSendingPortalAccess.value = false
  }
}

const copyPortalAccessLink = async () => {
  if (isCopyingPortalLink.value || hasCopiedPortalLink.value) return
  isCopyingPortalLink.value = true
  try {
    const res = await axios.get(`/portal/projetos/${props.project.id}/link`)
    if (res.data && res.data.url_publica) {
      const urlParts = res.data.url_publica.split('/')
      const token = urlParts[urlParts.length - 1]
      const dynamicUrl = `${window.location.origin}/portal/${token}`

      await navigator.clipboard.writeText(dynamicUrl)
      
      hasCopiedPortalLink.value = true
      setTimeout(() => {
        hasCopiedPortalLink.value = false
        closeMenu()
      }, 1500)
    } else {
      alert('Não foi possível obter ou criar o link do portal.')
    }
  } catch (error) {
    console.error('Erro ao copiar link do portal:', error)
    alert(error.response?.data?.detail || 'Erro ao gerar/recuperar o acesso ao portal do cliente.')
  } finally {
    isCopyingPortalLink.value = false
  }
}

const handleAbrirSinapi = () => {
  // Se já tiver os dados preenchidos, vai direto
  if (props.project.uf_obra && props.project.sinapi_mes_ano) {
    router.push(`/orcamento/${props.project.id}`)
  } else {
    isSetupModalOpen.value = true
  }
}

const onSetupSuccess = (projectId) => {
  isSetupModalOpen.value = false
  if (props.project.coluna === 'engenharia_caixa' || props.project.coluna === 'obra_liberada') {
    router.push(`/orcamento/${projectId}`)
  } else {
    emit('update')
  }
}

const openContractModal = async () => {
  isContractModalOpen.value = true
  selectedTemplateId.value = ''
  pdfPreviewUrl.value = null
  isGeneratingContract.value = false
  
  isLoadingTemplates.value = true
  try {
    const { data } = await axios.get('/contratos-templates')
    templates.value = data
    if (data.length > 0) {
      selectedTemplateId.value = data[0].id
    }
  } catch (error) {
    console.error('Erro ao buscar templates:', error)
    alert('Não foi possível carregar os templates.')
  } finally {
    isLoadingTemplates.value = false
  }
}

const closeContractModal = () => {
  isContractModalOpen.value = false
  if (pdfPreviewUrl.value) {
    URL.revokeObjectURL(pdfPreviewUrl.value)
    pdfPreviewUrl.value = null
  }
}

const generateContractPreview = async () => {
  isGeneratingContract.value = true
  try {
    const response = await axios.get(`/projetos/${props.project.id}/contrato`, {
      params: { template_id: selectedTemplateId.value },
      responseType: 'blob'
    })
    
    // Create a temporary URL for the preview
    pdfPreviewUrl.value = URL.createObjectURL(response.data)
  } catch (error) {
    console.error('Erro ao gerar contrato:', error)
    alert('Erro ao gerar o documento. Tente novamente.')
  } finally {
    isGeneratingContract.value = false
  }
}

const approveContract = async () => {
  isApprovingContract.value = true
  try {
    await axios.patch(`/projetos/${props.project.id}`, {
      contrato_gerado: true
    })
    // Atualização local para reatividade instantânea
    props.project.contrato_gerado = true
    closeContractModal()
    emit('update')
  } catch (error) {
    console.error('Erro ao aprovar contrato:', error)
    alert('Erro ao aprovar o contrato. Tente novamente.')
  } finally {
    isApprovingContract.value = false
  }
}

const downloadContract = () => {
  if (!pdfPreviewUrl.value) return
  
  const link = document.createElement('a')
  link.href = pdfPreviewUrl.value
  const projectName = props.project.cliente_nome ? props.project.cliente_nome.replace(/\s+/g, '_') : 'Projeto'
  link.setAttribute('download', `Contrato_${projectName}.pdf`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const openInNewTab = () => {
  if (pdfPreviewUrl.value) {
    window.open(pdfPreviewUrl.value, '_blank')
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
    
    // Atualiza localmente para refletir sem precisar de reload completo
    props.project.status = 'docs_validados'
    props.project.documentos = docsAtualizados
    
    emit('update')
  } catch (error) {
    console.error('Erro ao validar documentos:', error)
    alert('Erro ao validar documentos. Tente novamente.')
  }
}

const confirmModal = ref({
  isOpen: false,
  title: '',
  message: '',
  confirmText: 'Confirmar',
  loadingText: 'Processando...',
  successText: 'Concluído!',
  isDanger: false,
  onConfirm: null
})

const statusBotao = ref('idle') // 'idle' | 'loading' | 'success'

const openConfirmModal = (title, message, onConfirm, isDanger = false, confirmText = 'Confirmar', loadingText = 'Processando...', successText = 'Concluído!') => {
  confirmModal.value = {
    isOpen: true,
    title,
    message,
    confirmText,
    loadingText,
    successText,
    isDanger,
    onConfirm
  }
  statusBotao.value = 'idle'
}

const closeConfirmModal = () => {
  confirmModal.value.isOpen = false
}

const executeConfirm = async () => {
  if (confirmModal.value.onConfirm) {
    const shouldClose = await confirmModal.value.onConfirm()
    // Só fecha automaticamente se a função não retornar expressamente 'false'
    if (shouldClose !== false) {
      closeConfirmModal()
    }
  } else {
    closeConfirmModal()
  }
}

const avancarParaEngenharia = async () => {
  openConfirmModal(
    'Avançar para Engenharia',
    'Confirmar que o contrato foi assinado e mover o projeto para a fase de Engenharia? Esta ação registrará o evento no histórico.',
    async () => {
      isAdvancing.value = true
      try {
        await axios.patch(`/projetos/${props.project.id}`, {
          coluna: 'engenharia_caixa',
          status: 'em_analise_caixa'
        })
        emit('update')
      } catch (error) {
        console.error('Erro ao avançar fase:', error)
        alert('Erro ao atualizar status do projeto.')
      } finally {
        isAdvancing.value = false
      }
    }
  )
}

const voltarEtapa = async () => {
  let novaColuna = ''
  let novoStatus = ''
  
  if (props.project.coluna === 'contrato_pendente') {
    novaColuna = 'estimativa_enviada'
    novoStatus = 'aguardando_cliente'
  } else if (props.project.coluna === 'engenharia_caixa') {
    novaColuna = 'contrato_pendente'
    novoStatus = 'docs_validados'
  } else if (props.project.coluna === 'obra_liberada') {
    novaColuna = 'engenharia_caixa'
    novoStatus = 'em_analise_caixa'
  }
  
  if (!novaColuna) return

  openConfirmModal(
    'Desfazer Avanço',
    `Deseja realmente retroceder o projeto para a coluna "${novaColuna.replace('_', ' ').toUpperCase()}"? O histórico registrará esta mudança.`,
    async () => {
      try {
        await axios.patch(`/projetos/${props.project.id}`, {
          coluna: novaColuna,
          status: novoStatus
        })
        emit('update')
      } catch (error) {
        console.error('Erro ao voltar etapa:', error)
        alert('Erro ao retroceder status.')
      }
    },
    true,
    'Sim, Voltar Etapa'
  )
}

// Local formatCurrency removed (imported from formatters.js)

const formatDate = (dateString) => {
  if (!dateString) return 'Recém adicionado'
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR')
}

const sendWhatsAppReminder = () => {
  const nomeCliente = props.project.cliente_nome || 'Cliente'
  const nomeEmpresa = empresa.value?.nome_fantasia || 'Nossa Construtora'
  const telefone = props.project.telefone?.replace(/\D/g, '') || ''

  // Se engenheiro já assinou e existe URL de assinatura do cliente, enviar link da ZapSign
  if (props.project.engenheiro_assinou && props.project.url_assinatura_cliente) {
    const mensagem = encodeURIComponent(
      `Olá ${nomeCliente}, aqui é da ${nomeEmpresa}. ` +
      `Seu contrato está pronto para assinatura digital! Acesse o link abaixo para assinar: ${props.project.url_assinatura_cliente}`
    )
    window.open(`https://wa.me/${telefone ? '55' + telefone : ''}?text=${mensagem}`, '_blank')
  } else {
    const linkProjeto = `${window.location.origin}/estimativa/${props.project.id}`
    const mensagem = encodeURIComponent(
      `Olá ${nomeCliente}, aqui é da ${nomeEmpresa}. Vi que você realizou uma simulação de obra. ` +
      `Para prosseguirmos com seu projeto, acesse este link e anexe seus documentos: ${linkProjeto}`
    )
    window.open(`https://wa.me/${telefone ? '55' + telefone : ''}?text=${mensagem}`, '_blank')
  }
}

const openWhatsAppDirect = () => {
  const telefone = props.project.telefone?.replace(/\D/g, '') || ''
  window.open(`https://wa.me/${telefone ? '55' + telefone : ''}`, '_blank')
}

const enviarParaZapSign = async () => {
  // Precisa de um template selecionado — abre modal de contrato para selecionar
  if (!selectedTemplateId.value) {
    openContractModal()
    return
  }

  openConfirmModal(
    'Enviar para Assinatura Digital',
    `O contrato será enviado para a ZapSign e os links de assinatura serão gerados para você e para o cliente. Deseja continuar?`,
    async () => {
      isSendingToZapSign.value = true
      try {
        const { data } = await axios.post(`/projetos/${props.project.id}/enviar-zapsign`, {
          template_id: selectedTemplateId.value
        })
        if (data.success) {
          emit('update')
        }
      } catch (error) {
        console.error('Erro ao enviar para ZapSign:', error)
        alert('Erro ao enviar contrato para assinatura digital.')
      } finally {
        isSendingToZapSign.value = false
      }
    }
  )
}

const assinarComoEngenheiro = () => {
  if (props.project.url_assinatura_engenheiro) {
    window.open(props.project.url_assinatura_engenheiro, '_blank')
  }
}

const enviarLinkAssinaturaWhatsApp = () => {
  if (!props.project.engenheiro_assinou) return
  sendWhatsAppReminder()
}

const marcarComoAssinado = async (projetoId) => {
  isBypassing.value = true
  try {
    await axios.patch(`/projetos/${projetoId}`, {
      coluna: 'engenharia_caixa',
      status: 'em_analise_caixa',
      status_assinatura: 'assinado',
      cliente_assinou: true,
      engenheiro_assinou: true
    })
    
    // Atualização local imediata para fazer o card mudar de coluna de forma reativa
    props.project.coluna = 'engenharia_caixa'
    props.project.status = 'em_analise_caixa'
    props.project.status_assinatura = 'assinado'
    props.project.cliente_assinou = true
    props.project.engenheiro_assinou = true
    
    emit('update') // Alerta o pai (Kanban) para refazer o fetch no background, mantendo sincronizado
  } catch (error) {
    console.error('Erro ao forçar assinatura (bypass):', error)
  } finally {
    isBypassing.value = false
  }
}

const openEditModal = () => {
  isEditModalOpen.value = true
  closeMenu()
}

const handleSaveProjectEdit = async (editedData) => {
  try {
    await axios.patch(`/projetos/${props.project.id}`, editedData)
    
    // Atualiza localmente para refletir na interface
    props.project.cliente_nome = editedData.cliente_nome
    props.project.titulo_projeto = editedData.titulo_projeto
    props.project.telefone = editedData.telefone
    
    isEditModalOpen.value = false
  } catch (error) {
    console.error('Erro ao editar projeto:', error)
    alert('Erro ao salvar as alterações. Tente novamente.')
  }
}

const arquivarProjeto = () => {
  openConfirmModal(
    'Arquivar Projeto',
    'Tem certeza que deseja arquivar este projeto?',
    async () => {
      statusBotao.value = 'loading'
      try {
        await axios.patch(`/projetos/${props.project.id}`, { status: 'ARQUIVADO' })
        
        statusBotao.value = 'success'
        
        setTimeout(() => {
          closeConfirmModal()
          statusBotao.value = 'idle'
          emit('projeto-arquivado', props.project.id)
          closeMenu()
        }, 1000) // Feedback visual visível por 1 segundo
        
        return false // Impede o `executeConfirm` de fechar o modal na mesma hora
      } catch (error) {
        console.error('Erro ao arquivar projeto:', error)
        alert('Falha ao arquivar o projeto. Tente novamente.')
        statusBotao.value = 'idle'
        return true // Permite fechar o modal em caso de erro
      }
    },
    true, // Define isDanger = true para deixar o botão vermelho
    'Sim, Arquivar',
    'Arquivando...',
    'Arquivado!'
  )
}

// --- Histórico e Notas ---
const isModalHistoricoAberto = ref(false)
const projetoAtualHistorico = ref(null)
const novaNota = ref('')
const notasHistorico = ref([])

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

const fetchHistorico = async () => {
  if (!props.project?.id) return
  try {
    const res = await axios.get(`/projetos/${props.project.id}/historico`)
    if (res.data && res.data.success) {
      notasHistorico.value = res.data.data
    }
  } catch (error) {
    console.error('Erro ao buscar histórico do projeto:', error)
  }
}

const abrirModalHistorico = (projeto) => {
  projetoAtualHistorico.value = projeto
  isModalHistoricoAberto.value = true
  fetchHistorico()
  closeMenu()
}

const salvarNovaNota = async () => {
  if (!novaNota.value.trim() || !props.project?.id) return
  try {
    const res = await axios.post(`/projetos/${props.project.id}/historico`, {
      texto: novaNota.value
    })
    if (res.data && res.data.success) {
      notasHistorico.value.unshift(res.data.data)
      novaNota.value = ''
    }
  } catch (error) {
    console.error('Erro ao salvar nota de histórico:', error)
    alert('Erro ao salvar a nota. Tente novamente.')
  }
}
</script>

<template>
  <div :class="[
    'bg-white rounded-xl shadow-sm p-4 transition-all hover:shadow-md relative',
    'border border-slate-200 border-l-4',
    leftBorderClass
  ]">
    <div class="flex justify-between items-start mb-3">
      <div class="pr-6">
        <div class="flex items-center gap-1.5">
          <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{{ project.cliente_nome }}</p>
          <span 
            v-if="temDocumentosPendentesRevisao" 
            class="w-2 h-2 rounded-full bg-blue-500 animate-pulse shrink-0 cursor-help"
            title="Documento pendente de visualização"
          ></span>
        </div>
        <h4 class="text-sm font-semibold text-slate-800 mt-0.5 leading-snug">{{ project.titulo_projeto || '-' }}</h4>
      </div>
      
      <!-- Dropdown Menu -->
      <div class="absolute top-3 right-3 flex items-center gap-1" @click.stop>
        <button @click.stop="isDrawerOpen = true" class="text-slate-400 hover:text-slate-600 p-1 rounded-md hover:bg-slate-50 transition-colors" title="Ver Detalhes">
          <Maximize2 class="w-[18px] h-[18px]" stroke-width="1.5" />
        </button>
        <button @click.stop="toggleMenu" class="text-slate-400 hover:text-slate-600 p-1 rounded-md hover:bg-slate-50 transition-colors">
          <MoreHorizontal class="w-[18px] h-[18px]" stroke-width="1.5" />
        </button>
        
        <div v-if="isMenuOpen" class="absolute right-0 mt-1 w-44 bg-white rounded-md shadow-lg border border-slate-100 z-10 py-1" @click.stop>
          <button @click.stop="openWhatsAppDirect" class="w-full text-left px-4 py-2 text-xs text-emerald-600 font-semibold hover:bg-emerald-50 flex items-center gap-2">
            <MessageSquare class="w-[14px] h-[14px]" stroke-width="1.5" /> Chamar no Whats
          </button>
          <button
            v-if="project.coluna === 'obra_liberada'"
            @click.stop="isDiarioModalOpen = true; closeMenu()"
            class="w-full text-left px-4 py-2 text-xs text-indigo-600 font-semibold hover:bg-indigo-50 flex items-center gap-2"
          >
            <Camera class="w-[14px] h-[14px]" stroke-width="1.5" /> Diário de Obra
          </button>
          <div class="border-t border-slate-100 my-1"></div>
          <button @click.stop="openEditModal" class="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 flex items-center gap-2">
            <Pen class="w-[14px] h-[14px]" stroke-width="1.5" /> Editar
          </button>
          <button @click.stop="abrirModalHistorico(project)" class="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 flex items-center gap-2">
            <History class="w-[14px] h-[14px]" stroke-width="1.5" /> Histórico e Notas
          </button>
          <div class="border-t border-slate-100 my-1"></div>
          <button
            v-if="project.coluna === 'obra_liberada'"
            @click.stop="copyPortalAccessLink"
            class="w-full text-left px-4 py-2 text-xs font-semibold flex items-center gap-2 transition-colors"
            :class="hasCopiedPortalLink ? 'text-emerald-600 bg-emerald-50 hover:bg-emerald-50' : 'text-indigo-600 hover:bg-indigo-50'"
          >
            <Loader2 v-if="isCopyingPortalLink" class="w-[14px] h-[14px] animate-spin" stroke-width="1.5" />
            <CheckCircle2 v-else-if="hasCopiedPortalLink" class="w-[14px] h-[14px]" stroke-width="1.5" />
            <Copy v-else class="w-[14px] h-[14px]" stroke-width="1.5" />
            {{ hasCopiedPortalLink ? 'Copiado!' : 'Copiar Link do Portal' }}
          </button>
          <div v-if="project.coluna === 'engenharia_caixa' || project.coluna === 'obra_liberada'" class="border-t border-slate-100 my-1"></div>
          <button 
            v-if="project.coluna !== 'estimativa_enviada'"
            @click.stop="voltarEtapa" 
            class="w-full text-left px-4 py-2 text-xs text-slate-500 hover:bg-slate-50 flex items-center gap-2"
          >
            <Undo class="w-[14px] h-[14px]" stroke-width="1.5" /> Voltar Etapa
          </button>
          <button 
            v-if="project.coluna === 'contrato_pendente' && project.contrato_gerado"
            @click.stop="openContractModal" 
            class="w-full text-left px-4 py-2 text-xs text-blue-600 font-semibold hover:bg-blue-50 flex items-center gap-2"
          >
            <FileSignature class="w-[14px] h-[14px]" stroke-width="1.5" /> Atualizar/Refazer Contrato
          </button>
          <div v-if="project.coluna === 'contrato_pendente' && project.contrato_gerado" class="border-t border-slate-100 my-1"></div>
          <button @click.stop="arquivarProjeto" class="w-full text-left px-4 py-2 text-xs text-red-600 hover:bg-red-50 flex items-center gap-2">
            <Archive class="w-[14px] h-[14px]" stroke-width="1.5" /> Arquivar
          </button>
        </div>
      </div>
    </div>
    
    <!-- Parametric Data (Size, Pattern) inline near value -->
    <div class="flex items-end justify-between mb-3 gap-2">
      <div>
        <p class="text-sm font-bold" :class="project.valor ? 'text-slate-900' : 'text-slate-400 italic text-xs'">
          {{ formatCurrency(project.valor, 'Aguardando preenchimento') }}
        </p>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <span v-if="project.padrao" class="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-medium">{{ project.padrao }}</span>
        <span v-else class="text-[10px] text-slate-400 px-1 py-0.5">-</span>
        <span v-if="project.tamanho" class="text-[10px] text-slate-500 font-mono bg-slate-50 border border-slate-100 px-1.5 py-0.5 rounded">{{ project.tamanho }}</span>
      </div>
    </div>

    <!-- Checklist para contrato_pendente -->
    <div v-if="project.coluna === 'contrato_pendente' && project.documentos && project.documentos.length > 0" class="mb-4 bg-slate-50 rounded-lg border border-slate-100/60 shadow-inner overflow-hidden">
      <!-- Toggle Header -->
      <button 
        @click="toggleDocs"
        class="w-full px-3 py-2.5 flex items-center justify-between hover:bg-slate-100/50 transition-colors group"
      >
        <div class="flex items-center gap-2">
          <FolderOpen class="w-[18px] h-[18px] text-slate-400 group-hover:text-blue-500 transition-colors" stroke-width="1.5" />
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">{{ project.documentos.length }} Documentos Anexados</span>
          <span 
            v-if="temDocumentosPendentesRevisao" 
            class="w-2 h-2 rounded-full bg-blue-500 animate-pulse shrink-0"
            title="Documento pendente de visualização"
          ></span>
        </div>
        <ChevronDown 
          class="w-5 h-5 text-slate-400 transition-transform duration-300"
          :class="{ 'rotate-180': isDocsExpanded }"
          stroke-width="1.5"
        />
      </button>

      <!-- Expandable List -->
      <transition
        enter-active-class="transition-all duration-300 ease-out"
        leave-active-class="transition-all duration-300 ease-in"
        enter-from-class="max-h-0 opacity-0"
        enter-to-class="max-h-[500px] opacity-100"
        leave-from-class="max-h-[500px] opacity-100"
        leave-to-class="max-h-0 opacity-0"
      >
        <div v-show="isDocsExpanded" class="px-3 pb-3 overflow-hidden">
          <ul class="space-y-2 mb-3 mt-1">
            <li v-for="(doc, index) in project.documentos" :key="index" class="flex items-center justify-between text-xs bg-white p-2 rounded-md border border-slate-200 shadow-sm transition-all hover:border-slate-300">
              <div class="flex items-center gap-2 overflow-hidden">
                <component 
                  :is="docCategoriaLabels[doc.categoria]?.icon || FileText" 
                  class="w-4 h-4 text-blue-500 shrink-0" 
                  stroke-width="1.5" 
                />
                <div class="flex flex-col overflow-hidden">
                  <span class="text-slate-700 font-medium truncate">
                    {{ docCategoriaLabels[doc.categoria]?.label || doc.name }}
                  </span>
                  <span v-if="doc.categoria" class="text-[10px] text-slate-400 truncate">{{ doc.name }}</span>
                </div>
              </div>
              <div class="flex items-center gap-1.5 shrink-0">
                <span v-if="doc.categoria" class="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-100">
                  {{ docCategoriaLabels[doc.categoria]?.badge }}
                </span>
                <span v-if="doc.url && (project.status === 'docs_validados' || doc.status === 'aprovado')" class="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600 border border-emerald-100">
                  Aprovado
                </span>
                <span v-else-if="doc.url" class="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-50 text-amber-600 border border-amber-100">
                  Em Análise
                </span>
                <span v-if="!doc.url && doc.status === 'rejeitado'" class="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-red-50 text-red-600 border border-red-100" :title="doc.motivo">
                  Recusado
                </span>
                <a v-if="doc.url" :href="doc.url" target="_blank" class="text-blue-600 hover:text-white hover:bg-blue-600 transition-colors flex items-center gap-1 border border-blue-200 bg-blue-50 px-2 py-1 rounded">
                  <Eye class="w-[14px] h-[14px]" stroke-width="1.5" />
                  <span class="hidden sm:inline font-medium">Ver</span>
                </a>
                <button v-if="project.coluna === 'contrato_pendente' && project.status !== 'docs_validados' && doc.status !== 'aprovado' && doc.url" @click.stop="abrirModalRejeicao(doc)" class="text-red-600 hover:text-white hover:bg-red-600 transition-colors flex items-center gap-1 border border-red-200 bg-red-50 px-2 py-1 rounded">
                  <X class="w-[14px] h-[14px]" stroke-width="1.5" />
                  <span class="hidden sm:inline font-medium">Recusar</span>
                </button>
              </div>
            </li>
          </ul>

          <button 
            v-if="project.coluna === 'contrato_pendente' && project.status !== 'docs_validados'"
            @click.stop="validarDocumentos" 
            class="w-full py-2.5 bg-emerald-100 hover:bg-emerald-200 text-emerald-800 font-bold text-xs rounded-md transition-colors flex items-center justify-center gap-1.5 shadow-sm"
          >
            <CheckCircle2 class="w-4 h-4 text-emerald-800" stroke-width="1.5" /> Validar Documentos
          </button>
          <div v-else-if="project.status === 'docs_validados'" class="w-full py-2 bg-white text-emerald-600 font-bold text-xs rounded-md flex items-center justify-center gap-1.5 border border-emerald-100">
            <CheckCircle2 class="w-4 h-4 text-emerald-600" stroke-width="1.5" /> Documentos Validados
          </div>
        </div>
      </transition>
    </div>

    <!-- Compact Signature Status -->
    <div v-if="project.status_assinatura === 'pendente' && project.coluna === 'contrato_pendente'" class="mb-3 px-3 py-2 bg-slate-50 rounded-lg border border-slate-100 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-1" :title="project.engenheiro_assinou ? 'Engenheiro assinou' : 'Aguardando engenheiro'">
          <User class="w-3.5 h-3.5" :class="project.engenheiro_assinou ? 'text-emerald-500' : 'text-slate-300'" stroke-width="1.5" />
          <span class="text-[9px] font-bold" :class="project.engenheiro_assinou ? 'text-emerald-600' : 'text-slate-400'">ENG</span>
        </div>
        <div class="w-px h-3 bg-slate-200"></div>
        <div class="flex items-center gap-1" :title="project.cliente_assinou ? 'Cliente assinou' : 'Aguardando cliente'">
          <User class="w-3.5 h-3.5" :class="project.cliente_assinou ? 'text-emerald-500' : 'text-slate-300'" stroke-width="1.5" />
          <span class="text-[9px] font-bold" :class="project.cliente_assinou ? 'text-emerald-600' : 'text-slate-400'">CLI</span>
        </div>
      </div>
      
      <div class="flex gap-1">
        <button v-if="!project.engenheiro_assinou" @click.stop="assinarComoEngenheiro" class="text-[9px] px-2 py-1 bg-indigo-600 text-white font-bold rounded hover:bg-indigo-700 transition-colors">Assinar</button>
        <button v-if="project.engenheiro_assinou && !project.cliente_assinou" @click.stop="enviarLinkAssinaturaWhatsApp" class="text-[9px] px-2 py-1 bg-emerald-600 text-white font-bold rounded hover:bg-emerald-700 transition-colors">Cobrar</button>
      </div>
    </div>

    <div class="flex items-center justify-between mt-4 pt-3 border-t border-slate-100">
      <span class="text-[10px] text-slate-400 flex items-center gap-1 font-medium">
        <History class="w-3.5 h-3.5" stroke-width="1.5" />
        {{ formatDate(project.created_at) }}
      </span>
      
      <div class="flex items-center gap-2">
        <!-- Bypass Checkbox -->
        <label 
          v-if="project.coluna === 'contrato_pendente'"
          class="flex items-center gap-1.5 cursor-pointer opacity-60 hover:opacity-100 transition-opacity mr-1"
        >
          <input 
            type="checkbox" 
            :disabled="isBypassing"
            @change="marcarComoAssinado(project.id)"
            class="w-3.5 h-3.5 rounded-sm border-slate-300 text-slate-500 focus:ring-0 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all bg-slate-50"
          >
          <span class="text-[10px] font-medium text-slate-500 select-none whitespace-nowrap">
            {{ isBypassing ? 'Movendo...' : 'Cliente assinou' }}
          </span>
        </label>

        <button 
          v-if="project.coluna === 'estimativa_enviada'"
          @click.stop="sendWhatsAppReminder"
          title="Lembrar via WhatsApp"
          class="p-1.5 rounded-lg bg-emerald-50 text-emerald-600 hover:bg-emerald-100 transition-colors flex items-center justify-center border border-emerald-100 shadow-sm"
        >
          <MessageSquare class="w-[18px] h-[18px]" stroke-width="1.5" />
        </button>

      <!-- Botão SINAPI: visível em engenharia_caixa e obra_liberada -->
      <button
        v-if="project.coluna === 'engenharia_caixa' || project.coluna === 'obra_liberada'"
        @click.stop="handleAbrirSinapi"
        class="text-xs px-2.5 py-1.5 rounded-lg font-medium bg-white text-indigo-600 hover:bg-indigo-50 border border-indigo-200 transition-colors flex items-center gap-1 shadow-sm shrink-0 cursor-pointer"
      >
        <HardHat class="w-4 h-4" stroke-width="1.5" />
        SINAPI
      </button>

      <!-- Botão Portal: somente após obra liberada -->
      <div
        v-if="project.coluna === 'obra_liberada'"
        class="relative group flex items-center shrink-0"
      >
        <button
          @click.stop="sendPortalAccess"
          :disabled="isSendingPortalAccess"
          class="text-xs px-2.5 py-1.5 rounded-lg font-medium bg-indigo-600 text-white hover:bg-indigo-700 border border-indigo-600 transition-colors flex items-center gap-1 shadow-sm disabled:opacity-50 cursor-pointer"
        >
          <Loader2 v-if="isSendingPortalAccess" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          <Send v-else class="w-4 h-4" stroke-width="1.5" />
          Portal
        </button>

        <!-- Tooltip Visível no Hover -->
        <div class="absolute bottom-full right-0 mb-2 w-48 p-2 bg-slate-800 text-white text-[10px] leading-relaxed rounded-lg shadow-xl z-50 text-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          Enviar link de acesso exclusivo ao Portal da Obra para o cliente (via WhatsApp).
          <div class="absolute top-full right-5 border-4 border-transparent border-t-slate-800"></div>
        </div>
      </div>

      <button v-if="ctaInfo" @click.stop="handleCtaClick" :class="['text-xs px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer', ctaInfo.class]">
          <component v-if="ctaInfo.icon" :is="ctaInfo.icon" class="w-3.5 h-3.5" stroke-width="1.5" />
          {{ ctaInfo.text }}
        </button>
      </div>
    </div>

    <!-- Contract Modal -->
    <div v-if="isContractModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm" @click.stop>
      <div 
        class="bg-white rounded-2xl shadow-xl w-full flex flex-col overflow-hidden transition-all"
        :class="pdfPreviewUrl ? 'max-w-4xl h-[90vh]' : 'max-w-md'"
      >
        <!-- Modal Header -->
        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <h3 class="text-lg font-bold text-slate-800 flex items-center gap-2">
            <FileSignature class="w-5 h-5 text-emerald-600" stroke-width="1.5" />
            {{ pdfPreviewUrl ? 'Visualização do Contrato' : 'Gerar Contrato' }}
          </h3>
          <button @click.stop="closeContractModal" class="text-slate-400 hover:text-slate-600 p-1 rounded-md hover:bg-slate-200 transition-colors">
            <X class="w-5 h-5" stroke-width="1.5" />
          </button>
        </div>

        <!-- Mode 1: Selection -->
        <div v-if="!pdfPreviewUrl" class="p-6">
          <p class="text-sm text-slate-600 mb-4">Selecione o modelo de contrato para este projeto:</p>
          
          <div class="space-y-3 mb-6">
            <div v-if="isLoadingTemplates" class="text-sm text-slate-500 py-4 text-center">
              Carregando modelos...
            </div>
            <label 
              v-else
              v-for="tpl in templates" 
              :key="tpl.id"
              class="flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-colors" 
              :class="selectedTemplateId === tpl.id ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 hover:border-emerald-200'"
            >
              <input type="radio" v-model="selectedTemplateId" :value="tpl.id" class="mt-1 shrink-0 text-emerald-600 focus:ring-emerald-500">
              <div>
                <span class="block text-sm font-bold text-slate-800">{{ tpl.titulo }}</span>
                <span class="block text-xs text-slate-500 mt-0.5">Criado em: {{ formatDate(tpl.created_at) }}</span>
              </div>
            </label>
            <div v-if="!isLoadingTemplates && templates.length === 0" class="text-sm text-slate-500 py-4 text-center">
              Nenhum template cadastrado. Configure-os no menu Configurações.
            </div>
          </div>

          <div class="flex gap-3 justify-end mt-6 pt-4 border-t border-slate-100">
            <button @click.stop="closeContractModal" class="px-4 py-2 rounded-lg font-semibold text-slate-600 hover:bg-slate-100 transition-colors text-sm">Cancelar</button>
            <button 
              @click.stop="generateContractPreview" 
              :disabled="isGeneratingContract"
              class="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-semibold text-sm transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
            >
              <Loader2 v-if="isGeneratingContract" class="w-[18px] h-[18px] animate-spin" stroke-width="1.5" />
              {{ isGeneratingContract ? 'Gerando...' : 'Visualizar Contrato' }}
            </button>
          </div>
        </div>

        <!-- Mode 2: Preview -->
        <div v-else class="flex flex-col flex-1 overflow-hidden">
          <div class="flex-1 bg-slate-100 p-4 overflow-hidden">
            <iframe :src="pdfPreviewUrl" class="w-full h-full rounded shadow-sm border border-slate-200 bg-white"></iframe>
          </div>
          
          <div class="px-6 py-4 border-t border-slate-100 bg-white shrink-0">
            <div class="flex justify-between items-center">
              <button @click.stop="pdfPreviewUrl = null" class="text-sm font-semibold text-slate-500 hover:text-slate-800 transition-colors flex items-center gap-1">
                <ArrowLeft class="w-[18px] h-[18px]" stroke-width="1.5" /> Voltar à seleção
              </button>
              <div class="flex gap-3">
                <button @click.stop="openInNewTab" class="px-4 py-2 rounded-lg font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors text-sm flex items-center gap-2">
                  <ExternalLink class="w-[18px] h-[18px]" stroke-width="1.5" /> Abrir em Nova Aba
                </button>
                <button @click.stop="downloadContract" class="px-4 py-2 rounded-lg font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors text-sm flex items-center gap-2">
                  <Download class="w-[18px] h-[18px]" stroke-width="1.5" /> Download
                </button>
              </div>
            </div>
            <div class="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
              <p class="text-xs text-slate-500 max-w-xs leading-relaxed">
                <Info class="w-[14px] h-[14px] text-amber-500 mr-1 inline align-middle" stroke-width="1.5" />
                Revise o documento acima. Ao aprovar, o contrato será marcado como gerado e ficará disponível para envio à ZapSign.
              </p>
              <button 
                @click.stop="approveContract" 
                :disabled="isApprovingContract"
                class="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-sm transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50 flex items-center gap-2 active:scale-95 shrink-0"
              >
                <Loader2 v-if="isApprovingContract" class="w-[18px] h-[18px] animate-spin" stroke-width="1.5" />
                <CheckCircle2 v-else class="w-[18px] h-[18px]" stroke-width="1.5" />
                {{ isApprovingContract ? 'Aprovando...' : '✅ Aprovar Contrato' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Setup SINAPI Modal -->
    <SetupOrcamentoModal 
      :is-open="isSetupModalOpen" 
      :project="project"
      @close="isSetupModalOpen = false"
      @salvar="onSetupSuccess"
    />

    <!-- Modal Editar Projeto -->
    <EditProjectModal
      :is-open="isEditModalOpen"
      :projeto-origem="project"
      @close="isEditModalOpen = false"
      @save="handleSaveProjectEdit"
    />

    <!-- Modal Rejeição de Documento -->
    <RejeicaoDocumentoModal
      :is-open="isRejeicaoModalOpen"
      :projeto-id="project.id"
      :documento="selectedDocParaRejeicao"
      @close="isRejeicaoModalOpen = false"
      @rejeitado="onDocRejeitado"
    />

    <!-- Modal Diário de Obra -->
    <DiarioObraModal
      :is-open="isDiarioModalOpen"
      :project-id="project.id"
      :project-name="project.titulo_projeto || project.cliente_nome"
      @close="isDiarioModalOpen = false"
      @posted="emit('update')"
    />

    <!-- Modal Histórico e Notas -->
    <div v-if="isModalHistoricoAberto" class="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm" @click.stop>
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg flex flex-col overflow-hidden animate-in zoom-in duration-200">
        
        <!-- Header -->
        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <h3 class="text-lg font-bold text-slate-800 flex items-center gap-2">
            <History class="w-5 h-5 text-blue-600" stroke-width="1.5" />
            Histórico e Notas
          </h3>
          <button @click.stop="isModalHistoricoAberto = false" class="text-slate-400 hover:text-slate-600 p-1 rounded-md hover:bg-slate-200 transition-colors">
            <X class="w-5 h-5" stroke-width="1.5" />
          </button>
        </div>

        <!-- Corpo Superior (Nova Nota) -->
        <div class="p-6 border-b border-slate-100 bg-white">
          <textarea 
            v-model="novaNota" 
            rows="3" 
            placeholder="Digite uma nova observação..."
            class="w-full bg-slate-50 border border-slate-200 rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all resize-none"
          ></textarea>
          <div class="flex justify-end mt-3">
            <button 
              @click.stop="salvarNovaNota"
              :disabled="!novaNota.trim()"
              class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-600/50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-semibold transition-colors shadow-sm flex items-center gap-2"
            >
              <Plus class="w-4 h-4" stroke-width="1.5" /> Adicionar Nota
            </button>
          </div>
        </div>

        <!-- Corpo Inferior (Timeline) -->
        <div class="p-6 bg-slate-50 flex-1 overflow-y-auto max-h-64">
          <div class="relative border-l-2 border-gray-200 ml-3 space-y-6">
            <div v-for="nota in notasHistorico" :key="nota.id" class="relative pl-6">
              <div class="absolute -left-[7px] top-1 w-3 h-3 bg-blue-500 rounded-full ring-4 ring-slate-50"></div>
              <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-sm hover:border-blue-200 transition-colors">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs font-bold text-slate-800">{{ nota.autor }}</span>
                  <span class="text-[10px] font-medium text-slate-500">{{ formatarData(nota.data) }}</span>
                </div>
                <p class="text-sm text-slate-600 leading-relaxed">{{ nota.texto }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de Confirmação Customizado (Padrão do Sistema) -->
    <div v-if="confirmModal.isOpen" class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm" @click.stop>
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden animate-in zoom-in duration-200">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-slate-100 flex items-center gap-3 bg-slate-50">
          <div :class="confirmModal.isDanger ? 'bg-red-100 text-red-600' : 'bg-amber-100 text-amber-600'" class="p-2 rounded-full flex items-center justify-center">
            <AlertTriangle v-if="confirmModal.isDanger" class="w-5 h-5 text-red-600" stroke-width="1.5" />
            <HelpCircle v-else class="w-5 h-5 text-amber-600" stroke-width="1.5" />
          </div>
          <h3 class="text-base font-bold text-slate-800">{{ confirmModal.title }}</h3>
        </div>

        <!-- Body -->
        <div class="p-6">
          <p class="text-sm text-slate-600 leading-relaxed">{{ confirmModal.message }}</p>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-3">
          <button 
            @click.stop="closeConfirmModal" 
            :disabled="statusBotao === 'loading'"
            class="px-4 py-2 text-sm font-semibold text-slate-500 hover:text-slate-800 transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button 
            @click.stop="executeConfirm" 
            :disabled="statusBotao !== 'idle'"
            :class="[
              statusBotao === 'loading' ? 'bg-slate-400 cursor-not-allowed' :
              statusBotao === 'success' ? 'bg-emerald-600' :
              confirmModal.isDanger ? 'bg-red-600 hover:bg-red-700' : 'bg-emerald-600 hover:bg-emerald-700',
              'px-5 py-2 text-sm font-bold text-white rounded-xl transition-all shadow-md active:scale-95 flex items-center justify-center gap-2'
            ]"
          >
            <Loader2 v-if="statusBotao === 'loading'" class="w-[18px] h-[18px] animate-spin" stroke-width="1.5" />
            <CheckCircle2 v-else-if="statusBotao === 'success'" class="w-[18px] h-[18px]" stroke-width="1.5" />
            <span>{{ 
              statusBotao === 'loading' ? confirmModal.loadingText : 
              statusBotao === 'success' ? confirmModal.successText : 
              confirmModal.confirmText 
            }}</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Drawer Detalhes Projeto -->
    <DrawerDetalheProjeto
      :is-open="isDrawerOpen"
      :project="project"
      @close="isDrawerOpen = false"
      @update="emit('update')"
    />
  </div>
</template>
