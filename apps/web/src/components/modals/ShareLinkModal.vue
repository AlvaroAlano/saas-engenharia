<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'
import { Share2, AlertTriangle, Link, Loader2, CheckCircle2, Check, Copy } from 'lucide-vue-next'
import BaseModal from './BaseModal.vue'

const props = defineProps({
  isOpen: Boolean,
  resourceId: [String, Number],
  resourceLabel: {
    type: String,
    default: 'Orçamento'
  }
})

const emit = defineEmits(['close'])

const shareStep = ref('pin')
const sharePin = ref('')
const shareLinkUrl = ref('')
const sharePinCopy = ref('')
const shareError = ref('')
const linkCopiado = ref(false)

watch(() => props.isOpen, async (newVal) => {
  if (newVal) {
    shareStep.value = 'pin'
    sharePin.value = ''
    shareLinkUrl.value = ''
    sharePinCopy.value = ''
    shareError.value = ''
    linkCopiado.value = false

    // Busca dados do projeto para auto-preencher o PIN com os últimos 4 dígitos do telefone
    if (props.resourceId) {
      try {
        const res = await axios.get(`/api/projetos/${props.resourceId}`)
        if (res.data && res.data.telefone) {
          const apenasNumeros = res.data.telefone.replace(/\D/g, '')
          if (apenasNumeros.length >= 4) {
            sharePin.value = apenasNumeros.slice(-4)
          }
        }
      } catch (err) {
        console.warn('Erro ao carregar telefone para auto-preenchimento do PIN:', err)
      }
    }
  }
})

const gerarLinkB2C = async () => {
  if (!/^\d{4}$/.test(sharePin.value)) {
    shareError.value = 'O PIN deve ter exatamente 4 dígitos numéricos.'
    return
  }
  shareStep.value = 'loading'
  shareError.value = ''
  try {
    const res = await axios.post('/api/portal/links', {
      projeto_id: props.resourceId,
      pin_acesso: sharePin.value
    })
    if (res.data.success) {
      shareLinkUrl.value = res.data.data.url_publica
      sharePinCopy.value = sharePin.value
      shareStep.value = 'result'
    }
  } catch (e) {
    shareError.value = e.response?.data?.detail || 'Erro ao gerar link.'
    shareStep.value = 'pin'
  }
}

const copiarLink = async () => {
  try {
    await navigator.clipboard.writeText(shareLinkUrl.value)
    linkCopiado.value = true
    setTimeout(() => linkCopiado.value = false, 2500)
  } catch { /* fallback silencioso */ }
}

const enviarWhatsApp = () => {
  const label = props.resourceLabel.toLowerCase()
  const msg = `Olá! Segue o link para visualizar seu ${label}:\n${shareLinkUrl.value}\n\nPIN de acesso: ${sharePinCopy.value}`
  window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`, '_blank')
}
</script>

<template>
  <BaseModal :isOpen="isOpen" @close="emit('close')" maxWidthClass="max-w-md" zIndexClass="z-[120]">
    <template #header>
      <div class="flex items-center gap-2">
        <Share2 class="w-5 h-5 text-blue-600" stroke-width="1.5" />
        <h3 class="text-lg font-medium text-ink">Compartilhar {{ resourceLabel }}</h3>
      </div>
    </template>

    <div class="space-y-4">
      <!-- Step A: Digitar PIN -->
      <div v-if="shareStep === 'pin'" class="space-y-4">
        <p class="text-sm text-ink-muted leading-relaxed">
          Defina um <strong>PIN de 4 dígitos</strong> para proteger o acesso do cliente ao {{ resourceLabel.toLowerCase() }} online.
        </p>
        
        <div v-if="shareError" class="bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 text-red-650 dark:text-red-400 text-sm p-3 rounded-md flex items-start gap-2">
          <AlertTriangle class="w-4 h-4 text-red-650 dark:text-red-400 shrink-0 mt-0.5" stroke-width="1.5" />
          <span>{{ shareError }}</span>
        </div>

        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 text-center">PIN de Segurança</label>
          <input 
            v-model="sharePin" 
            @input="sharePin = sharePin.replace(/\D/g, '')" 
            maxlength="4" 
            inputmode="numeric" 
            pattern="\d{4}" 
            class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-3 px-4 text-center text-2xl font-bold tracking-[0.5em] focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans" 
            placeholder="••••"
          />
        </div>

        <button 
          @click="gerarLinkB2C" 
          :disabled="sharePin.length !== 4" 
          class="w-full h-10 px-4 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 cursor-pointer shadow-sm"
        >
          <Link class="w-4 h-4" stroke-width="1.5" />
          Gerar Link Seguro
        </button>
      </div>

      <!-- Step B: Loading -->
      <div v-else-if="shareStep === 'loading'" class="text-center py-8">
        <Loader2 class="w-8 h-8 text-blue-600 animate-spin mx-auto" stroke-width="1.5" />
        <p class="text-sm text-ink-muted mt-3">Gerando link seguro...</p>
      </div>

      <!-- Step C: Resultado -->
      <div v-else-if="shareStep === 'result'" class="space-y-4">
        <div class="bg-blue-500/10 dark:bg-blue-500/5 border border-blue-500/20 rounded-md p-4 space-y-3">
          <div class="flex items-center gap-2">
            <CheckCircle2 class="w-4 h-4 text-blue-600 dark:text-blue-400" stroke-width="1.5" />
            <span class="text-sm font-semibold text-blue-600 dark:text-blue-400">Link gerado com sucesso!</span>
          </div>
          <div class="bg-surface rounded-md border border-blue-500/20 px-3 py-2 flex items-center gap-2">
            <span class="text-xs text-ink-muted truncate flex-1 font-mono select-all">{{ shareLinkUrl }}</span>
            <button 
              @click="copiarLink" 
              class="shrink-0 p-1.5 rounded-md transition-all flex items-center justify-center cursor-pointer" 
              :class="linkCopiado ? 'bg-blue-500/20 text-blue-600' : 'hover:bg-canvas text-ink-muted'"
            >
              <Check v-if="linkCopiado" class="w-4 h-4 text-emerald-600" stroke-width="1.5" />
              <Copy v-else class="w-4 h-4" stroke-width="1.5" />
            </button>
          </div>
          <p class="text-xs text-ink-muted">
            <strong>PIN de Acesso:</strong> <span class="font-mono bg-canvas px-1.5 py-0.5 rounded border border-hairline font-bold text-ink">{{ sharePinCopy }}</span>
          </p>
        </div>

        <button 
          @click="enviarWhatsApp" 
          class="w-full h-10 px-4 text-sm font-semibold text-white bg-[#25D366] hover:bg-[#20BD5A] rounded-md transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-sm"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
          Enviar pelo WhatsApp
        </button>

        <button 
          @click="emit('close')" 
          class="w-full h-9 px-4 text-sm font-medium text-ink-muted hover:text-ink bg-transparent hover:bg-surface-hover rounded-md transition-colors cursor-pointer flex items-center justify-center border border-hairline"
        >
          Fechar
        </button>
      </div>
    </div>
  </BaseModal>
</template>
