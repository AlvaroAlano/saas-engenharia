<script setup>
import { ref, watch } from 'vue'
import { SquarePen } from 'lucide-vue-next'
import BaseModal from './modals/BaseModal.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  projetoOrigem: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close', 'save'])

const projetoEmEdicao = ref({
  cliente_nome: '',
  titulo_projeto: '',
  telefone: ''
})

// @watch - Atualiza os campos do formulário sempre que o projeto passado para edição mudar
watch(
  () => props.projetoOrigem,
  (newVal) => {
    if (newVal) {
      projetoEmEdicao.value = {
        cliente_nome: newVal.cliente_nome || '',
        titulo_projeto: newVal.titulo_projeto || '',
        telefone: newVal.telefone || ''
      }
    }
  },
  { immediate: true, deep: true }
)

const salvarAlteracoes = () => {
  emit('save', projetoEmEdicao.value)
}
</script>

<template>
  <BaseModal :isOpen="isOpen" @close="$emit('close')" maxWidthClass="max-w-md" zIndexClass="z-50">
    <template #header>
      <div class="flex items-center gap-2">
        <SquarePen class="w-5 h-5 text-blue-600" stroke-width="1.5" />
        <h3 class="text-lg font-medium text-ink">Editar Cliente/Projeto</h3>
      </div>
    </template>

    <!-- Form -->
    <form id="edit-project-form" @submit.prevent="salvarAlteracoes" class="space-y-4">
      <div>
        <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 flex items-center gap-0.5">
          Nome do Cliente
          <span class="text-red-500/70 font-normal">*</span>
        </label>
        <input 
          v-model="projetoEmEdicao.cliente_nome" 
          type="text" 
          class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans" 
          placeholder="Ex: João da Silva"
          required
        />
      </div>
      
      <div>
        <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">Nome da Obra / Projeto</label>
        <input 
          v-model="projetoEmEdicao.titulo_projeto" 
          type="text"
          class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans" 
          placeholder="Ex: Residencial Vale Verde"
        />
      </div>
      
      <div>
        <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 flex items-center gap-0.5">
          Telefone / WhatsApp
          <span class="text-red-500/70 font-normal">*</span>
        </label>
        <input 
          v-model="projetoEmEdicao.telefone" 
          type="tel"
          class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans" 
          placeholder="Ex: (11) 99999-9999"
          required
        />
      </div>
    </form>

    <template #footer>
      <button 
        type="button" 
        @click="$emit('close')" 
        class="h-9 px-4 text-sm font-medium text-ink-muted hover:text-ink bg-transparent hover:bg-surface-hover rounded-md transition-colors cursor-pointer flex items-center justify-center"
      >
        Cancelar
      </button>
      <button 
        type="submit" 
        form="edit-project-form"
        class="h-9 px-4 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center justify-center cursor-pointer shadow-sm"
      >
        Salvar Alterações
      </button>
    </template>
  </BaseModal>
</template>