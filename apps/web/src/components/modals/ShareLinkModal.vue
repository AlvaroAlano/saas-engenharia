<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'
import { Share2, X, AlertTriangle, Link, Loader2, CheckCircle2, Check, Copy } from 'lucide-vue-next'

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
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 bg-zinc-950/40 dark:bg-zinc-950/60 backdrop-blur-sm z-[120] flex items-center justify-center p-4" style="z-index: 120;" @click.self="emit('close')">
      <div class="bg-surface border border-hairline w-full max-w-md overflow-hidden animate-in zoom-in duration-200 shadow-sm rounded-xl">
        <div class="flex items-center justify-between px-6 py-4 border-b border-hairline bg-canvas">
          <div class="flex items-center gap-2">
            <Share2 class="w-5 h-5 text-brand-primary" stroke-width="1.5" />
            <h3 class="text-lg font-bold text-ink">Compartilhar {{ resourceLabel }}</h3>
          </div>
          <button @click="emit('close')" class="p-1 rounded-lg hover:bg-surface-hover transition-all flex items-center justify-center">
            <X class="w-4 h-4 text-ink-muted" stroke-width="1.5" />
          </button>
        </div>

        <div class="p-6">
          <!-- Step A: Digitar PIN -->
          <div v-if="shareStep === 'pin'">
            <p class="text-sm text-ink-muted mb-4">
              Defina um <strong>PIN de 4 dígitos</strong> para proteger o acesso do cliente ao {{ resourceLabel.toLowerCase() }} online.
            </p>
            <div v-if="shareError" class="bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 text-red-600 dark:text-red-400 text-sm p-3 rounded-lg flex items-start gap-2 mb-4">
              <AlertTriangle class="w-4 h-4 text-red-650 dark:text-red-400 shrink-0 mt-0.5" stroke-width="1.5" />
              <span>{{ shareError }}</span>
            </div>
            <input v-model="sharePin" @input="sharePin = sharePin.replace(/\D/g, '')" maxlength="4" inputmode="numeric" pattern="\d{4}" class="w-full bg-canvas border border-hairline text-ink rounded-lg py-3 px-4 text-center text-2xl font-bold tracking-[0.5em] focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all" placeholder="• • • •"/>
            <button @click="gerarLinkB2C" :disabled="sharePin.length !== 4" class="w-full mt-4 py-3 bg-brand-primary hover:bg-brand-hover text-white rounded-xl text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
              <Link class="w-4 h-4" stroke-width="1.5" />
              Gerar Link Seguro
            </button>
          </div>

          <!-- Step B: Loading -->
          <div v-else-if="shareStep === 'loading'" class="text-center py-8">
            <Loader2 class="w-8 h-8 text-brand-primary animate-spin mx-auto" stroke-width="1.5" />
            <p class="text-sm text-ink-muted mt-3">Gerando link seguro...</p>
          </div>

          <!-- Step C: Resultado -->
          <div v-else-if="shareStep === 'result'">
            <div class="bg-brand-primary/10 dark:bg-brand-primary/5 border border-brand-primary/30 rounded-xl p-4 mb-4">
              <div class="flex items-center gap-2 mb-2">
                <CheckCircle2 class="w-4 h-4 text-brand-primary" stroke-width="1.5" />
                <span class="text-sm font-bold text-brand-primary">Link gerado com sucesso!</span>
              </div>
              <div class="bg-surface rounded-lg border border-brand-primary/20 px-3 py-2 flex items-center gap-2">
                <span class="text-xs text-ink-muted truncate flex-1 font-mono">{{ shareLinkUrl }}</span>
                <button @click="copiarLink" class="shrink-0 p-1.5 rounded-md transition-all flex items-center justify-center" :class="linkCopiado ? 'bg-brand-primary/20 text-brand-primary' : 'hover:bg-canvas text-ink-muted'">
                  <Check v-if="linkCopiado" class="w-4 h-4 text-emerald-600" stroke-width="1.5" />
                  <Copy v-else class="w-4 h-4" stroke-width="1.5" />
                </button>
              </div>
              <p class="text-xs text-brand-primary mt-2">
                <strong>PIN:</strong> {{ sharePinCopy }}
              </p>
            </div>
            <button @click="enviarWhatsApp" class="w-full py-3 bg-[#25D366] hover:bg-[#20BD5A] text-white rounded-xl text-sm font-semibold transition-colors flex items-center justify-center gap-2">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
              Enviar pelo WhatsApp
            </button>
            <button @click="emit('close')" class="w-full mt-3 py-2.5 border border-hairline rounded-xl text-sm font-medium text-ink-muted hover:bg-canvas transition-colors">Fechar</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
