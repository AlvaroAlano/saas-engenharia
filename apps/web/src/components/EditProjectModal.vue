<script setup>
import { ref, watch } from 'vue'

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
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 bg-zinc-950/40 dark:bg-zinc-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
      <div class="bg-surface rounded-2xl border border-hairline w-full max-w-lg overflow-hidden">
        
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-hairline bg-canvas">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-brand-primary">edit_square</span>
            <h3 class="text-lg font-bold text-ink">Editar Cliente/Projeto</h3>
          </div>
          <button @click="$emit('close')" class="p-1 rounded-lg hover:bg-surface-hover transition-all text-ink-muted hover:text-ink">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <!-- Form -->
        <form @submit.prevent="salvarAlteracoes" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-ink mb-1">Nome do Cliente *</label>
            <input v-model="projetoEmEdicao.cliente_nome" required class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all placeholder:text-ink-muted" placeholder="Ex: João da Silva"/>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-ink mb-1">Nome da Obra / Projeto</label>
            <input v-model="projetoEmEdicao.titulo_projeto" class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all placeholder:text-ink-muted" placeholder="Ex: Residencial Vale Verde"/>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-ink mb-1">Telefone / WhatsApp *</label>
            <input v-model="projetoEmEdicao.telefone" required class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all placeholder:text-ink-muted" placeholder="Ex: (00) 00000-0000"/>
          </div>

          <!-- Footer / Ações -->
          <div class="flex gap-3 pt-4 mt-2 border-t border-hairline">
            <button type="button" @click="$emit('close')" class="flex-1 py-2.5 border border-hairline rounded-lg text-sm font-medium text-ink-muted hover:bg-canvas transition-colors">
              Cancelar
            </button>
            <button type="submit" class="flex-1 py-2.5 bg-brand-primary hover:bg-brand-hover text-white rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2">
              Salvar Alterações
            </button>
          </div>
        </form>
        
      </div>
    </div>
  </Teleport>
</template>