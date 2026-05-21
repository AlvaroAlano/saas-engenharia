<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  caixaData: {
    type: Object,
    required: true
  }
})

const formatCurrency = (val) => {
  if (val === undefined || val === null) return '0,00'
  return Number(val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<template>
  <div class="space-y-4">
    <!-- Progresso Geral -->
    <div class="bg-surface border border-hairline rounded-xl p-4 shadow-sm">
      <div class="flex justify-between items-center mb-2">
        <span class="text-xs font-bold text-ink uppercase tracking-wider">Progresso Físico Geral</span>
        <span class="text-sm font-bold text-brand-primary">{{ caixaData.progresso_geral }}%</span>
      </div>
      <div class="w-full bg-canvas rounded-full h-2 border border-hairline overflow-hidden">
        <div 
          class="bg-brand-primary h-full rounded-full transition-all duration-500" 
          :style="{ width: `${caixaData.progresso_geral}%` }"
        ></div>
      </div>
    </div>

    <!-- Juros de Obra Estimados (PCI/PFUI) -->
    <div class="bg-brand-primary/5 border border-brand-primary/20 rounded-xl p-4 shadow-sm relative overflow-hidden">
      <div class="flex items-center gap-2 mb-2">
        <span class="material-symbols-outlined text-brand-primary text-lg">info</span>
        <h4 class="text-xs font-bold text-ink uppercase tracking-wider">Juros de Evolução de Obra</h4>
        
        <!-- Tooltip Educacional Premium -->
        <div class="group relative inline-block cursor-help ml-1">
          <span class="material-symbols-outlined text-ink-muted text-sm hover:text-ink transition-colors">help</span>
          <div class="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-zinc-950 text-white text-[10px] rounded-lg p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 shadow-xl leading-relaxed z-30">
            <span class="font-bold block mb-1">Como funcionam os juros de obra?</span>
            Os juros de evolução de obra são cobrados pela Caixa sobre a fatia do financiamento já liberada para a construção. Eles aumentam à medida que a obra avança e cessam apenas após a emissão e averbação do Habite-se.
            <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-zinc-950"></div>
          </div>
        </div>
      </div>
      
      <p class="text-[11px] text-ink-muted mb-3 leading-relaxed">
        Valores estimados de juros cobrados pela Caixa Econômica Federal durante esta fase da construção.
      </p>
      
      <div class="grid grid-cols-2 gap-4 bg-surface border border-hairline/60 rounded-lg p-3">
        <div>
          <span class="text-[10px] text-ink-muted block uppercase tracking-wider">Mês Atual (Est.)</span>
          <span class="text-sm font-bold text-brand-primary">R$ {{ formatCurrency(caixaData.juros_mensal_atual) }}</span>
        </div>
        <div>
          <span class="text-[10px] text-ink-muted block uppercase tracking-wider">Acumulado Pago (Est.)</span>
          <span class="text-sm font-bold text-ink">R$ {{ formatCurrency(caixaData.juros_acumulado_estimado) }}</span>
        </div>
      </div>
    </div>
    
    <!-- Detalhamento de Etapas (Caixômetro) -->
    <div class="bg-surface border border-hairline rounded-xl overflow-hidden shadow-sm">
      <div class="bg-canvas px-4 py-2.5 border-b border-hairline flex justify-between items-center">
        <h4 class="text-xs font-bold text-ink uppercase tracking-wider">Cronograma de Desembolso</h4>
        <span class="text-[9px] bg-brand-primary/10 text-brand-primary px-2 py-0.5 rounded font-mono font-bold uppercase">PCI / PFUI</span>
      </div>
      
      <div class="divide-y divide-hairline">
        <div v-for="etapa in caixaData.etapas" :key="etapa.nome" class="p-4">
          <div class="flex justify-between items-center mb-1.5">
            <span class="text-xs font-semibold text-ink">{{ etapa.nome }}</span>
            <span class="text-xs font-bold text-brand-primary">{{ etapa.progresso }}%</span>
          </div>
          <div class="w-full bg-canvas rounded-full h-1.5 border border-hairline overflow-hidden mb-2">
            <div 
              class="bg-brand-primary h-full rounded-full transition-all duration-300" 
              :style="{ width: `${etapa.progresso}%` }"
            ></div>
          </div>
          <div class="flex justify-between text-[10px] text-ink-muted font-mono">
            <span>Liberado: R$ {{ formatCurrency(etapa.valor_medido) }}</span>
            <span>Total: R$ {{ formatCurrency(etapa.valor_total) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
