<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  isOpen: Boolean,
  projetoId: String,
  documento: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close', 'rejeitado'])

const motivo = ref('')
const carregando = ref(false)
const erro = ref('')

const MAP_CATEGORIA = {
  identidade: 'Identidade (RG/CNH)',
  residencia: 'Comprovante de Residência',
  estado_civil: 'Certidão de Estado Civil'
}

const nomeDocumento = computed(() => {
  if (!props.documento) return ''
  const cat = props.documento.categoria || ''
  return MAP_CATEGORIA[cat] || props.documento.name || 'Documento'
})

const recusarDocumento = async () => {
  if (!motivo.value.trim()) {
    erro.value = 'Por favor, digite o motivo da recusa.'
    return
  }
  
  carregando.value = true
  erro.value = ''
  
  try {
    const res = await axios.post(`/projetos/${props.projetoId}/documentos/rejeitar`, {
      documento_id: props.documento.categoria,
      motivo: motivo.value
    })
    
    if (res.data.success) {
      emit('rejeitado')
      emit('close')
      motivo.value = ''
    }
  } catch (err) {
    erro.value = err.response?.data?.detail || 'Erro ao rejeitar o documento. Tente novamente.'
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 bg-zinc-950/40 dark:bg-zinc-950/60 backdrop-blur-sm z-[130] flex items-center justify-center p-4" style="z-index: 130;" @click.self="emit('close')">
      <div class="bg-surface border border-hairline w-full max-w-md overflow-hidden animate-in zoom-in duration-200 shadow-sm rounded-xl">
        <div class="flex items-center justify-between px-6 py-4 border-b border-hairline bg-canvas">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-red-500">cancel</span>
            <h3 class="text-lg font-bold text-ink">Recusar Documento</h3>
          </div>
          <button @click="emit('close')" class="p-1 rounded-lg hover:bg-surface-hover transition-all">
            <span class="material-symbols-outlined text-ink-muted">close</span>
          </button>
        </div>

        <div class="p-6">
          <p class="text-sm text-ink-muted mb-4">
            Você está rejeitando o documento <strong class="text-ink">{{ nomeDocumento }}</strong>. O cliente será notificado para enviar uma nova versão.
          </p>

          <div v-if="erro" class="bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 text-red-600 dark:text-red-400 text-sm p-3 rounded-lg flex items-start gap-2 mb-4">
            <span class="material-symbols-outlined text-base">error</span>
            <span>{{ erro }}</span>
          </div>

          <div class="mb-4">
            <label class="block text-xs font-semibold text-ink-muted uppercase tracking-wider mb-2">Motivo da Rejeição</label>
            <textarea
              v-model="motivo"
              rows="4"
              class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all placeholder:text-ink-muted/50"
              placeholder="Ex: O documento está ilegível ou cortado. Por favor, envie uma foto nítida e completa."
              required
            ></textarea>
          </div>

          <div class="flex gap-3">
            <button
              @click="emit('close')"
              class="flex-1 py-2.5 border border-hairline rounded-xl text-sm font-medium text-ink-muted hover:bg-canvas transition-colors"
            >
              Cancelar
            </button>
            <button
              @click="recusarDocumento"
              :disabled="carregando || !motivo.trim()"
              class="flex-1 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span v-if="carregando" class="material-symbols-outlined text-lg animate-spin">progress_activity</span>
              <span v-else class="material-symbols-outlined text-lg">block</span>
              Recusar
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
