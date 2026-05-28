<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { XCircle, AlertTriangle, Loader2, Ban } from 'lucide-vue-next'
import BaseModal from './BaseModal.vue'

const props = defineProps({
  isOpen: Boolean,
  projetoId: String,
  documento: {
    type: Object,
    default: () => ({})
  },
  documentos: {
    type: Array,
    default: () => []
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
    const docsAtualizados = props.documentos.map(d => {
      if (d.categoria === props.documento.categoria) {
        return { ...d, status: 'rejeitado', url: null, done: false, motivo: motivo.value.trim() }
      }
      return d
    })

    await axios.patch(`/projetos/${props.projetoId}`, { documentos: docsAtualizados })

    emit('rejeitado', docsAtualizados)
    emit('close')
    motivo.value = ''
  } catch (err) {
    erro.value = err.response?.data?.detail || 'Erro ao rejeitar o documento. Tente novamente.'
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <BaseModal :isOpen="isOpen" @close="emit('close')" maxWidthClass="max-w-md" zIndexClass="z-[130]">
    <template #header>
      <div class="flex items-center gap-2">
        <XCircle class="w-5 h-5 text-red-600" stroke-width="1.5" />
        <h3 class="text-lg font-medium text-ink">Recusar Documento</h3>
      </div>
    </template>

    <form id="rejeitar-documento-form" @submit.prevent="recusarDocumento" class="space-y-4">
      <p class="text-sm text-ink-muted leading-relaxed">
        Você está rejeitando o documento <strong class="text-ink">{{ nomeDocumento }}</strong>. O cliente será notificado para enviar uma nova versão.
      </p>

      <div v-if="erro" class="bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 text-red-650 dark:text-red-400 text-sm p-3 rounded-md flex items-start gap-2">
        <AlertTriangle class="w-4 h-4 text-red-650 dark:text-red-400 shrink-0 mt-0.5" stroke-width="1.5" />
        <span>{{ erro }}</span>
      </div>

      <div>
        <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">Motivo da Rejeição</label>
        <textarea
          v-model="motivo"
          rows="4"
          class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans resize-none"
          placeholder="Ex: O documento está ilegível ou cortado. Por favor, envie uma foto nítida e completa."
          required
        ></textarea>
      </div>
    </form>

    <template #footer>
      <button
        type="button"
        @click="emit('close')"
        class="h-9 px-4 text-sm font-medium text-ink-muted hover:text-ink bg-transparent hover:bg-surface-hover rounded-md transition-colors cursor-pointer flex items-center justify-center"
      >
        Cancelar
      </button>
      <button
        type="submit"
        form="rejeitar-documento-form"
        :disabled="carregando || !motivo.trim()"
        class="h-9 px-4 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Loader2 v-if="carregando" class="w-4 h-4 animate-spin" stroke-width="1.5" />
        <Ban v-else class="w-4 h-4" stroke-width="1.5" />
        Recusar
      </button>
    </template>
  </BaseModal>
</template>
