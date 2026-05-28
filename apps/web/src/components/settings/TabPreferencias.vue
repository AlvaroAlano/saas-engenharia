<script setup>
import { ref } from 'vue'
import { isDark, toggleTheme } from '../../composables/useTheme'
import { useToast } from '../../composables/useToast'
import { Sun, Moon, Check } from 'lucide-vue-next'
import BaseButton from '../ui/BaseButton.vue'

const { showToast } = useToast()
const bdiPadrao = ref(Number(localStorage.getItem('bdi_padrao_global') || 25))

const setTheme = (mode) => {
  const wantDark = mode === 'dark'
  if (wantDark !== isDark.value) toggleTheme()
}

const saveBdi = () => {
  const val = Number(bdiPadrao.value)
  if (isNaN(val) || val < 0 || val > 100) {
    showToast('BDI deve ser entre 0 e 100%.', 'error'); return
  }
  localStorage.setItem('bdi_padrao_global', String(val))
  showToast('BDI padrão salvo!', 'success')
}
</script>

<template>
  <div class="space-y-5">

    <!-- Card: Aparência -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Aparência</h3>
        <p class="text-xs text-ink-muted mt-0.5">Escolha o tema visual da interface.</p>
      </div>
      <div class="px-6 py-5">
        <div class="grid grid-cols-2 gap-3 max-w-sm">

          <!-- Light Mode -->
          <button
            @click="setTheme('light')"
            class="relative rounded-md border-2 p-3.5 text-left transition-all cursor-pointer focus:outline-none"
            :class="!isDark ? 'border-brand-primary bg-brand-primary/5' : 'border-hairline hover:border-ink-muted'"
          >
            <!-- Preview -->
            <div class="w-full h-16 rounded-lg bg-white border border-gray-200 mb-3 overflow-hidden">
              <div class="h-3.5 bg-gray-50 border-b border-gray-200 flex items-center gap-1 px-2">
                <div class="w-1.5 h-1.5 rounded-full bg-gray-300"></div>
                <div class="w-1.5 h-1.5 rounded-full bg-gray-300"></div>
                <div class="w-1.5 h-1.5 rounded-full bg-gray-300"></div>
              </div>
              <div class="p-2 space-y-1.5">
                <div class="h-1 bg-gray-200 rounded w-3/4"></div>
                <div class="h-1 bg-gray-100 rounded w-1/2"></div>
              </div>
            </div>
            <span class="text-xs font-semibold text-ink flex items-center gap-1.5">
              <Sun class="w-4 h-4" stroke-width="1.5" />
              Claro
            </span>
            <span v-if="!isDark" class="absolute top-2 right-2 w-4 h-4 rounded-full bg-brand-primary flex items-center justify-center">
              <Check class="w-2.5 h-2.5 text-white" stroke-width="1.5" />
            </span>
          </button>

          <!-- Dark Mode -->
          <button
            @click="setTheme('dark')"
            class="relative rounded-md border-2 p-3.5 text-left transition-all cursor-pointer focus:outline-none"
            :class="isDark ? 'border-brand-primary bg-brand-primary/5' : 'border-hairline hover:border-ink-muted'"
          >
            <!-- Preview -->
            <div class="w-full h-16 rounded-lg bg-zinc-900 border border-zinc-700 mb-3 overflow-hidden">
              <div class="h-3.5 bg-zinc-800 border-b border-zinc-700 flex items-center gap-1 px-2">
                <div class="w-1.5 h-1.5 rounded-full bg-zinc-600"></div>
                <div class="w-1.5 h-1.5 rounded-full bg-zinc-600"></div>
                <div class="w-1.5 h-1.5 rounded-full bg-zinc-600"></div>
              </div>
              <div class="p-2 space-y-1.5">
                <div class="h-1 bg-zinc-700 rounded w-3/4"></div>
                <div class="h-1 bg-zinc-600 rounded w-1/2"></div>
              </div>
            </div>
            <span class="text-xs font-semibold text-ink flex items-center gap-1.5">
              <Moon class="w-4 h-4" stroke-width="1.5" />
              Escuro
            </span>
            <span v-if="isDark" class="absolute top-2 right-2 w-4 h-4 rounded-full bg-brand-primary flex items-center justify-center">
              <Check class="w-2.5 h-2.5 text-white" stroke-width="1.5" />
            </span>
          </button>

        </div>
      </div>
    </div>

    <!-- Card: Padrões de Orçamento -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Padrões de Orçamento</h3>
        <p class="text-xs text-ink-muted mt-0.5">Valores pré-preenchidos ao criar um novo projeto.</p>
      </div>
      <div class="px-6 py-5">
        <div class="max-w-xs space-y-1.5">
          <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">BDI Padrão Global (%)</label>
          <div class="flex items-center gap-3">
            <input
              v-model.number="bdiPadrao"
              type="number"
              min="0"
              max="100"
              step="0.5"
              class="w-full bg-canvas border border-hairline text-ink rounded-md px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all"
            />
            <span class="text-sm font-bold text-ink-muted shrink-0">%</span>
          </div>
          <p class="text-[11px] text-ink-muted">Aplicado automaticamente ao criar novos orçamentos.</p>
        </div>
      </div>
      <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex justify-end">
        <BaseButton variant="primary" @click="saveBdi" class="px-5 h-9 font-bold gap-2">
          Salvar Preferências
        </BaseButton>
      </div>
    </div>

  </div>
</template>
