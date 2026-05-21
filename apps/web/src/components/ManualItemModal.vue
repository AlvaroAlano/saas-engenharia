<script setup>
import { ref, watch } from 'vue'
import { ETAPAS_OBRA } from '../constants/etapas'

const props = defineProps({
  isOpen: Boolean,
  isSaving: Boolean
})

const emit = defineEmits(['close', 'confirm'])

const form = ref({
  descricao: '',
  unidade: 'UN',
  quantidade: 1,
  valor_unitario: 0,
  etapa_obra: 'servicos_preliminares'
})

const unidades = ['UN', 'M²', 'M³', 'KG', 'MES', 'CJ', 'VB']

const etapas = ETAPAS_OBRA

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    form.value = {
      descricao: '',
      unidade: 'UN',
      quantidade: 1,
      valor_unitario: 0,
      etapa_obra: 'servicos_preliminares'
    }
  }
})

const handleConfirm = () => {
  if (!form.value.descricao || form.value.quantidade <= 0) return
  emit('confirm', { ...form.value, codigo_sinapi: 'MANUAL' })
  emit('close')
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-zinc-950/40 dark:bg-zinc-950/60 backdrop-blur-sm">
    <div class="bg-surface rounded-2xl w-full max-w-md overflow-hidden border border-hairline shadow-sm">
      <div class="p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-ink flex items-center gap-2">
            <span class="material-symbols-outlined text-brand-primary">post_add</span>
            Item Manual
          </h3>
          <button @click="emit('close')" class="p-1 rounded-lg hover:bg-surface-hover text-ink-muted hover:text-ink transition-colors">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        
        <div class="space-y-4">
          <!-- Descrição -->
          <div class="space-y-1.5">
            <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider">Descrição do Item</label>
            <input 
              v-model="form.descricao" 
              type="text" 
              class="w-full px-4 py-2.5 bg-canvas border border-hairline text-ink rounded-xl text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all font-medium placeholder:text-ink-muted"
              placeholder="Ex: Taxa de Alvará, Frete Especial..."
            />
          </div>

          <!-- Etapa da Obra -->
          <div class="space-y-1.5">
            <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider">Etapa da Obra</label>
            <div class="relative">
              <select 
                v-model="form.etapa_obra" 
                class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary appearance-none cursor-pointer font-medium"
              >
                <option v-for="etapa in etapas" :key="etapa.value" :value="etapa.value">{{ etapa.label }}</option>
              </select>
              <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none text-[20px]">expand_more</span>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <!-- Unidade -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider">Unidade</label>
              <div class="relative">
                <select 
                  v-model="form.unidade" 
                  class="w-full bg-canvas border border-hairline text-ink rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-primary focus:border-brand-primary appearance-none cursor-pointer font-medium"
                >
                  <option v-for="un in unidades" :key="un" :value="un">{{ un }}</option>
                </select>
                <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none text-[20px]">expand_more</span>
              </div>
            </div>

            <!-- Quantidade -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider">Quantidade</label>
              <input 
                v-model.number="form.quantidade" 
                type="number" 
                step="0.01"
                class="w-full px-4 py-2.5 bg-canvas border border-hairline text-ink rounded-xl text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all font-medium"
              />
            </div>
          </div>

          <!-- Valor Unitário -->
          <div class="space-y-1.5">
            <label class="block text-xs font-bold text-ink-muted uppercase tracking-wider">Valor Unitário (R$)</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-ink-muted text-sm font-bold">R$</span>
              <input 
                v-model.number="form.valor_unitario" 
                type="number" 
                step="0.01"
                class="w-full pl-11 pr-4 py-2.5 bg-canvas border border-hairline text-ink rounded-xl text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all font-bold placeholder:text-ink-muted"
                placeholder="0,00"
              />
            </div>
          </div>
        </div>
      </div>
      
      <div class="px-6 py-4 bg-canvas border-t border-hairline flex justify-end gap-3">
        <button 
          @click="emit('close')"
          class="px-5 py-2.5 text-sm font-semibold text-ink-muted hover:text-ink hover:bg-surface-hover rounded-xl transition-colors"
        >
          Cancelar
        </button>
        <button 
          @click="handleConfirm"
          :disabled="isSaving || !form.descricao"
          class="px-6 py-2.5 text-sm font-bold text-white bg-brand-primary hover:bg-brand-hover rounded-xl transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="isSaving" class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
          <span v-else class="material-symbols-outlined text-[18px]">check_circle</span>
          {{ isSaving ? 'Adicionando...' : 'Adicionar Item' }}
        </button>
      </div>
    </div>
  </div>
</template>
