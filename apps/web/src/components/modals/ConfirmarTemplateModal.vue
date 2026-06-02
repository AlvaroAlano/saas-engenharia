<script setup>
import { ref, watch, computed } from 'vue'
import { Network, AlertTriangle, Trash2, ListPlus, Star, Lock } from 'lucide-vue-next'
import BaseModal from './BaseModal.vue'

const props = defineProps({
  isOpen:         { type: Boolean, required: true },
  cartItemsCount: { type: Number,  default: 0 },
  // Lista opcional de templates disponíveis para o padrão do projeto.
  // Se vazio ou com 1 item, o seletor não é exibido.
  templates:      { type: Array,   default: () => [] },
})

const emit = defineEmits(['confirmar', 'cancelar'])

const modo               = ref('mesclar')
const selectedTemplateId = ref(null)

const syncSelection = (templates) => {
  const active = templates.find(t => t.is_active)
  selectedTemplateId.value = active?.id ?? templates[0]?.id ?? null
}

// Reseta estado ao abrir
watch(() => props.isOpen, (val) => {
  if (!val) return
  modo.value = 'mesclar'
  syncSelection(props.templates)
})

// Atualiza seleção quando templates chegam de forma assíncrona (modal já aberto)
watch(() => props.templates, (templates) => {
  if (!props.isOpen || selectedTemplateId.value) return
  syncSelection(templates)
})

const showSelector = computed(() => props.templates.length > 1)

const padraoBadge = {
  popular: { label: 'Popular',     text: 'text-emerald-700', bg: 'bg-emerald-500/10', border: 'border-emerald-500/25' },
  medio:   { label: 'Médio',       text: 'text-blue-700',   bg: 'bg-blue-500/10',   border: 'border-blue-500/25'   },
  alto:    { label: 'Alto Padrão', text: 'text-orange-700', bg: 'bg-orange-500/10', border: 'border-orange-500/25' },
}
</script>

<template>
  <BaseModal :isOpen="isOpen" @close="emit('cancelar')" maxWidthClass="max-w-md" zIndexClass="z-[140]">
    <template #header>
      <div class="flex items-center gap-2">
        <Network class="w-5 h-5 text-blue-600" stroke-width="1.5" />
        <h3 class="text-lg font-medium text-ink">Aplicar Template EAP</h3>
      </div>
    </template>

    <div class="space-y-4">

      <!-- Seletor de template (aparece só quando há mais de um disponível) -->
      <template v-if="showSelector">
        <div>
          <p class="text-sm font-semibold text-ink mb-2">Qual template deseja aplicar?</p>
          <div class="space-y-1.5">
            <div
              v-for="t in templates"
              :key="t.id"
              @click="selectedTemplateId = t.id"
              class="flex items-center gap-3 p-3 rounded-md border cursor-pointer transition-all"
              :class="selectedTemplateId === t.id
                ? 'border-blue-500 bg-blue-500/[0.04]'
                : 'border-hairline bg-transparent hover:bg-surface-hover'"
            >
              <div
                class="shrink-0 w-4 h-4 rounded-full border-2 flex items-center justify-center transition-colors"
                :class="selectedTemplateId === t.id ? 'border-blue-500' : 'border-neutral-400'"
              >
                <div v-if="selectedTemplateId === t.id" class="w-2 h-2 rounded-full bg-blue-500" />
              </div>

              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <p class="text-sm font-semibold text-ink truncate">{{ t.nome }}</p>
                  <Star v-if="t.is_active" class="w-3 h-3 text-amber-500 shrink-0" fill="currentColor" stroke-width="0" title="Template ativo" />
                  <Lock v-if="t.tipo === 'SISTEMA'" class="w-3 h-3 text-ink-muted shrink-0" stroke-width="1.5" title="Padrão do sistema" />
                </div>
                <div class="flex items-center gap-2 mt-0.5">
                  <span
                    class="text-[10px] font-bold px-1.5 py-px rounded-full border"
                    :class="[padraoBadge[t.padrao_obra]?.text, padraoBadge[t.padrao_obra]?.bg, padraoBadge[t.padrao_obra]?.border]"
                  >
                    {{ padraoBadge[t.padrao_obra]?.label }}
                  </span>
                  <span class="text-[11px] text-ink-muted">{{ t.total_itens }} itens</span>
                  <span v-if="t.is_active" class="text-[11px] text-amber-600 font-medium">· Ativo</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="h-px bg-hairline" />
      </template>

      <!-- Descrição de itens existentes -->
      <p class="text-sm text-ink-muted leading-snug">
        A árvore de orçamento já possui
        <span class="font-semibold text-ink">{{ cartItemsCount }} {{ cartItemsCount === 1 ? 'item' : 'itens' }}</span>.
        Escolha como deseja prosseguir:
      </p>

      <!-- Modo mesclar / substituir -->
      <div class="space-y-2.5">
        <div
          class="flex items-start gap-3 p-4 rounded-md border cursor-pointer transition-all"
          :class="modo === 'mesclar' ? 'border-blue-500 bg-blue-500/[0.04]' : 'border-hairline bg-transparent hover:bg-surface-hover'"
          @click="modo = 'mesclar'"
        >
          <div class="mt-0.5 shrink-0 w-4 h-4 rounded-full border flex items-center justify-center transition-colors"
               :class="modo === 'mesclar' ? 'border-blue-500' : 'border-neutral-400'">
            <div v-if="modo === 'mesclar'" class="w-2 h-2 rounded-full bg-blue-600" />
          </div>
          <div>
            <p class="text-sm font-semibold text-ink">Adicionar apenas os que faltam (Recomendado)</p>
            <p class="text-xs text-ink-muted mt-0.5 leading-relaxed">Mantém os itens existentes e insere apenas os serviços do template que ainda não estão no seu orçamento.</p>
          </div>
        </div>

        <div
          class="flex items-start gap-3 p-4 rounded-md border cursor-pointer transition-all"
          :class="modo === 'substituir' ? 'border-red-500 bg-red-500/[0.04]' : 'border-hairline bg-transparent hover:bg-surface-hover'"
          @click="modo = 'substituir'"
        >
          <div class="mt-0.5 shrink-0 w-4 h-4 rounded-full border flex items-center justify-center transition-colors"
               :class="modo === 'substituir' ? 'border-red-500' : 'border-neutral-400'">
            <div v-if="modo === 'substituir'" class="w-2 h-2 rounded-full bg-red-600" />
          </div>
          <div>
            <p class="text-sm font-semibold text-ink">Substituir tudo (Limpar orçamento)</p>
            <p class="text-xs text-ink-muted mt-0.5 leading-relaxed">Remove todos os itens atuais e insere o template do zero. <strong>Esta ação não pode ser desfeita.</strong></p>
          </div>
        </div>
      </div>

      <!-- Aviso substituição -->
      <transition enter-active-class="transition-all duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
        <div v-if="modo === 'substituir'" class="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-500/10 rounded-md border border-red-100 dark:border-red-500/20">
          <AlertTriangle class="w-4 h-4 text-red-500 shrink-0 mt-0.5" stroke-width="1.5" />
          <p class="text-xs text-red-700 dark:text-red-400 leading-snug font-medium">
            Atenção: Os {{ cartItemsCount }} itens existentes e suas quantidades editadas serão perdidos permanentemente.
          </p>
        </div>
      </transition>

    </div>

    <template #footer>
      <button
        type="button"
        @click="emit('cancelar')"
        class="h-9 px-4 text-sm font-medium text-ink-muted hover:text-ink bg-transparent hover:bg-surface-hover rounded-md transition-colors cursor-pointer flex items-center justify-center"
      >
        Cancelar
      </button>
      <button
        type="button"
        @click="emit('confirmar', modo, selectedTemplateId)"
        class="h-9 px-4 text-sm font-medium text-white rounded-md transition-colors cursor-pointer flex items-center justify-center gap-1.5 shadow-sm"
        :class="modo === 'substituir' ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'"
      >
        <Trash2 v-if="modo === 'substituir'" class="w-4 h-4" stroke-width="1.5" />
        <ListPlus v-else class="w-4 h-4" stroke-width="1.5" />
        {{ modo === 'substituir' ? 'Substituir Tudo' : 'Confirmar Importação' }}
      </button>
    </template>
  </BaseModal>
</template>
