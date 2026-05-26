<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { X, AlertTriangle, Loader2, Check } from 'lucide-vue-next'

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
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/45 dark:bg-black/65 backdrop-blur-sm p-4">
    <div class="bg-surface rounded-md w-full max-w-md overflow-hidden border border-hairline shadow-2xl transition-all">
      
      <!-- Header -->
      <div class="px-6 py-4 border-b border-hairline flex items-center justify-between bg-surface">
        <h3 class="text-lg font-medium text-ink">Novo Cliente</h3>
        <button @click="$emit('close')" class="text-ink-muted hover:text-ink transition-colors p-1.5 rounded-md hover:bg-surface-hover flex items-center justify-center cursor-pointer">
          <X class="w-4 h-4" stroke-width="1.25" />
        </button>
      </div>
      
      <!-- Form Body -->
      <div class="p-6">
        <div v-if="errorMessage" class="mb-4 p-3 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-sm rounded-md border border-red-100 dark:border-red-500/20 flex items-center gap-2">
          <AlertTriangle class="w-4 h-4 text-red-600 dark:text-red-400 shrink-0" stroke-width="1.5" />
          {{ errorMessage }}
        </div>
        
        <form @submit.prevent="handleSubmit" class="space-y-4">
          
          <div>
            <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 flex items-center gap-0.5">
              Nome do Cliente
              <span class="text-red-500/70 font-normal">*</span>
            </label>
            <input 
              v-model="cliente_nome" 
              type="text" 
              class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans"
              placeholder="Ex: João da Silva"
              required
            />
          </div>
          
          <div>
            <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">Nome da Obra / Projeto</label>
            <input 
              v-model="titulo_projeto" 
              type="text" 
              class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans"
              placeholder="Ex: Residência MCMV - Lote 12"
            />
          </div>
          
          <div>
            <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 flex items-center gap-0.5">
              Telefone / WhatsApp
              <span class="text-red-500/70 font-normal">*</span>
            </label>
            <input 
              v-model="telefone" 
              v-maska="'(##) #####-####'"
              type="tel" 
              class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans"
              placeholder="Ex: (11) 99999-9999"
              required
            />
          </div>
          
          <div>
            <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">Observações Iniciais</label>
            <textarea 
              v-model="observacoes" 
              rows="3" 
              class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans resize-none"
              placeholder="Ex: Cliente tem urgência no financiamento."
            ></textarea>
          </div>
          
        </form>
      </div>
      
      <!-- Footer Actions -->
      <div class="px-6 py-4 bg-canvas border-t border-hairline flex items-center justify-end gap-2">
        <button 
          @click="$emit('close')" 
          type="button" 
          class="h-9 px-4 text-sm font-medium text-ink-muted hover:text-ink bg-transparent hover:bg-surface-hover rounded-md transition-colors cursor-pointer flex items-center justify-center"
          :disabled="isSubmitting"
        >
          Cancelar
        </button>
        <button 
          @click="handleSubmit" 
          type="button" 
          class="h-9 px-4 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm disabled:opacity-50"
          :disabled="isSubmitting"
        >
          <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          <Check v-else class="w-4 h-4" stroke-width="1.5" />
          {{ isSubmitting ? 'Cadastrando...' : 'Cadastrar Cliente' }}
        </button>
      </div>
      
    </div>
  </div>
</template>

