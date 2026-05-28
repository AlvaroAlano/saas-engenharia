<script setup>
import { ref, watch } from 'vue'
import { ETAPAS_OBRA } from '../constants/etapas'
import { FilePlus, ChevronDown, Loader2, Check } from 'lucide-vue-next'
import BaseModal from './modals/BaseModal.vue'

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
  <BaseModal :isOpen="isOpen" @close="emit('close')" maxWidthClass="max-w-md" zIndexClass="z-[100]">
    <template #header>
      <div class="flex items-center gap-2">
        <FilePlus class="w-5 h-5 text-blue-600" stroke-width="1.5" />
        <h3 class="text-lg font-medium text-ink">Item Manual</h3>
      </div>
    </template>

    <form id="manual-item-form" @submit.prevent="handleConfirm" class="space-y-4">
      <!-- Descrição -->
      <div>
        <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5 flex items-center gap-0.5">
          Descrição do Item
          <span class="text-red-500/70 font-normal">*</span>
        </label>
        <input 
          v-model="form.descricao" 
          type="text" 
          class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans"
          placeholder="Ex: Taxa de Alvará, Frete Especial..."
          required
        />
      </div>

      <!-- Etapa da Obra -->
      <div>
        <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">Etapa da Obra</label>
        <div class="relative">
          <select 
            v-model="form.etapa_obra" 
            class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 pl-3 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all appearance-none cursor-pointer font-medium font-sans"
          >
            <option v-for="etapa in etapas" :key="etapa.value" :value="etapa.value">{{ etapa.label }}</option>
          </select>
          <ChevronDown class="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <!-- Unidade -->
        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">Unidade</label>
          <div class="relative">
            <select 
              v-model="form.unidade" 
              class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 pl-3 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all appearance-none cursor-pointer font-medium font-sans"
            >
              <option v-for="un in unidades" :key="un" :value="un">{{ un }}</option>
            </select>
            <ChevronDown class="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none" stroke-width="1.5" />
          </div>
        </div>

        <!-- Quantidade -->
        <div>
          <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">Quantidade</label>
          <input 
            v-model.number="form.quantidade" 
            type="number" 
            step="0.01"
            min="0.01"
            class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all font-medium font-sans"
            required
          />
        </div>
      </div>

      <!-- Valor Unitário -->
      <div>
        <label class="block text-xs font-semibold text-neutral-500 dark:text-neutral-300 mb-1.5">Valor Unitário (R$)</label>
        <div class="relative">
          <span class="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted text-sm font-semibold select-none font-sans">R$</span>
          <input 
            v-model.number="form.valor_unitario" 
            type="number" 
            step="0.01"
            min="0"
            class="w-full pl-9 pr-3 py-2 bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all font-semibold font-sans placeholder:text-ink-muted/80"
            placeholder="0,00"
          />
        </div>
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
        form="manual-item-form"
        :disabled="isSaving || !form.descricao"
        class="h-9 px-4 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm disabled:opacity-50"
      >
        <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" stroke-width="1.5" />
        <Check v-else class="w-4 h-4" stroke-width="1.5" />
        {{ isSaving ? 'Adicionando...' : 'Adicionar Item' }}
      </button>
    </template>
  </BaseModal>
</template>

