<script setup>
import { ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['close', 'created'])

const cliente_nome = ref('')
const titulo_projeto = ref('')
const telefone = ref('')
const observacoes = ref('')
const isSubmitting = ref(false)
const errorMessage = ref('')

const handleSubmit = async () => {
  if (!cliente_nome.value.trim()) {
    errorMessage.value = 'O nome do cliente é obrigatório.'
    return
  }

  if (!telefone.value.trim() || telefone.value.replace(/\D/g, '').length < 10) {
    errorMessage.value = 'O telefone/WhatsApp é obrigatório e deve ser válido.'
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    const payload = {
      cliente_nome: cliente_nome.value.trim(),
      titulo_projeto: titulo_projeto.value.trim() || undefined,
      telefone: telefone.value.replace(/\D/g, ''), // Salva apenas números
      observacoes: observacoes.value.trim() || undefined
    }
    
    await axios.post('/projetos', payload)
    
    // Clear form
    cliente_nome.value = ''
    titulo_projeto.value = ''
    telefone.value = ''
    observacoes.value = ''
    
    emit('created')
  } catch (error) {
    console.error('Erro ao cadastrar cliente:', error)
    errorMessage.value = 'Erro ao conectar ao servidor. Tente novamente.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-zinc-950/40 dark:bg-zinc-950/60 backdrop-blur-sm p-4">
    <div class="bg-surface rounded-2xl w-full max-w-md overflow-hidden border border-hairline shadow-sm">
      
      <!-- Header -->
      <div class="px-6 py-4 border-b border-hairline flex items-center justify-between bg-canvas">
        <h3 class="text-lg font-bold text-ink">Novo Cliente</h3>
        <button @click="$emit('close')" class="text-ink-muted hover:text-ink transition-colors p-1 rounded-md hover:bg-surface-hover">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      
      <!-- Form Body -->
      <div class="p-6">
        <div v-if="errorMessage" class="mb-4 p-3 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-sm rounded-lg border border-red-100 dark:border-red-500/20 flex items-center gap-2">
          <span class="material-symbols-outlined text-[18px]">error</span>
          {{ errorMessage }}
        </div>
        
        <form @submit.prevent="handleSubmit" class="space-y-4">
          
          <div>
            <label class="block text-sm font-semibold text-ink mb-1">Nome do Cliente <span class="text-red-500">*</span></label>
            <input 
              v-model="cliente_nome" 
              type="text" 
              class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all placeholder:text-ink-muted"
              placeholder="Ex: João da Silva"
              required
            />
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-ink mb-1">Nome da Obra / Projeto</label>
            <input 
              v-model="titulo_projeto" 
              type="text" 
              class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all placeholder:text-ink-muted"
              placeholder="Ex: Residência MCMV - Lote 12"
            />
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-ink mb-1">Telefone / WhatsApp <span class="text-red-500">*</span></label>
            <input 
              v-model="telefone" 
              v-maska="'(##) #####-####'"
              type="tel" 
              class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all placeholder:text-ink-muted"
              placeholder="Ex: (11) 99999-9999"
              required
            />
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-ink mb-1">Observações Iniciais</label>
            <textarea 
              v-model="observacoes" 
              rows="3" 
              class="w-full bg-canvas border border-hairline text-ink rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all placeholder:text-ink-muted resize-none"
              placeholder="Ex: Cliente tem urgência no financiamento."
            ></textarea>
          </div>
          
        </form>
      </div>
      
      <!-- Footer Actions -->
      <div class="px-6 py-4 bg-canvas border-t border-hairline flex items-center justify-end gap-3">
        <button 
          @click="$emit('close')" 
          type="button" 
          class="px-4 py-2 text-sm font-medium text-ink-muted bg-surface border border-hairline rounded-lg hover:bg-canvas transition-colors"
          :disabled="isSubmitting"
        >
          Cancelar
        </button>
        <button 
          @click="handleSubmit" 
          type="button" 
          class="px-5 py-2 text-sm font-medium text-white bg-brand-primary rounded-lg hover:bg-brand-hover transition-colors flex items-center gap-2"
          :disabled="isSubmitting"
        >
          <span v-if="isSubmitting" class="material-symbols-outlined animate-spin text-[18px]">sync</span>
          <span v-else class="material-symbols-outlined text-[18px]">check_circle</span>
          {{ isSubmitting ? 'Cadastrando...' : 'Cadastrar Cliente' }}
        </button>
      </div>
      
    </div>
  </div>
</template>
