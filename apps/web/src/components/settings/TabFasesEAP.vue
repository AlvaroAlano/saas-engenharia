<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { useToast } from '../../composables/useToast'
import { useFases } from '../../composables/useFases'
import {
  Plus, Pencil, Trash2, Save, X, Loader2,
  GripVertical,
  HardHat, Layers, Building, Zap, Paintbrush,
  Wrench, Home, Package, Settings2, LayoutGrid,
  Info, AlertTriangle
} from 'lucide-vue-next'

const { showToast } = useToast()
const { fases, ensureFases, reloadFases } = useFases()

// dbReady = true quando as fases vieram do banco (têm campo id).
// false = ainda usando o fallback ETAPAS_OBRA (migration ainda não rodou).
const dbReady = computed(() => fases.value.length > 0 && !!fases.value[0].id)

// ── Icon / Color catalogs ─────────────────────────────────────────────────

const ICONS = [
  { key: 'engineering',   label: 'Capacete',       comp: HardHat   },
  { key: 'foundation',    label: 'Camadas',         comp: Layers    },
  { key: 'domain',        label: 'Edifício',        comp: Building  },
  { key: 'electric_bolt', label: 'Elétrica',        comp: Zap       },
  { key: 'format_paint',  label: 'Pintura',         comp: Paintbrush},
  { key: 'wrench',        label: 'Ferramentas',     comp: Wrench    },
  { key: 'home',          label: 'Casa',            comp: Home      },
  { key: 'package',       label: 'Pacote',          comp: Package   },
  { key: 'settings',      label: 'Configurações',   comp: Settings2 },
  { key: 'grid',          label: 'Grade',           comp: LayoutGrid},
]

const COLORS = [
  { key: 'amber',   bg: 'bg-amber-500',   ring: 'ring-amber-500'   },
  { key: 'orange',  bg: 'bg-orange-500',  ring: 'ring-orange-500'  },
  { key: 'blue',    bg: 'bg-blue-500',    ring: 'ring-blue-500'    },
  { key: 'violet',  bg: 'bg-violet-500',  ring: 'ring-violet-500'  },
  { key: 'emerald', bg: 'bg-emerald-500', ring: 'ring-emerald-500' },
  { key: 'red',     bg: 'bg-red-500',     ring: 'ring-red-500'     },
  { key: 'slate',   bg: 'bg-slate-500',   ring: 'ring-slate-500'   },
  { key: 'cyan',    bg: 'bg-cyan-500',    ring: 'ring-cyan-500'    },
  { key: 'indigo',  bg: 'bg-indigo-500',  ring: 'ring-indigo-500'  },
  { key: 'green',   bg: 'bg-green-500',   ring: 'ring-green-500'   },
]

// ── Helpers ────────────────────────────────────────────────────────────────

const iconComp   = (key) => ICONS.find(i => i.key === key)?.comp   ?? HardHat
const colorBg    = (key) => COLORS.find(c => c.key === key)?.bg    ?? 'bg-blue-500'
const colorRing  = (key) => COLORS.find(c => c.key === key)?.ring  ?? 'ring-blue-500'

// ── Edit state ─────────────────────────────────────────────────────────────

const editingId = ref(null)   // ID da fase sendo editada inline
const editForm  = reactive({ label: '', icon: 'engineering', color: 'blue' })
const isSaving  = ref(false)
const isDeleting = ref(null)  // ID da fase sendo excluída

const openEdit = (fase) => {
  if (!dbReady.value || !fase.id) return
  editingId.value   = fase.id
  editForm.label    = fase.label
  editForm.icon     = fase.icon
  editForm.color    = fase.color
}

const cancelEdit = () => {
  editingId.value = null
}

const saveEdit = async (fase) => {
  if (!dbReady.value || !fase.id) { showToast('Execute a migration 016 para habilitar edição.', 'error'); return }
  if (!editForm.label.trim()) return
  isSaving.value = true
  try {
    await axios.put(`/configuracoes/fases/${fase.id}`, {
      label: editForm.label.trim(),
      icon:  editForm.icon,
      color: editForm.color,
    })
    editingId.value = null
    await reloadFases()
    showToast('Fase atualizada com sucesso!', 'success')
  } catch (e) {
    showToast(e.response?.data?.detail || 'Erro ao salvar fase.', 'error')
  } finally {
    isSaving.value = false
  }
}

const deleteFase = async (fase) => {
  if (!dbReady.value || !fase.id) return
  if (!confirm(`Excluir a fase "${fase.label}"? Esta ação não pode ser desfeita.`)) return
  isDeleting.value = fase.id
  try {
    await axios.delete(`/configuracoes/fases/${fase.id}`)
    showToast('Fase excluída.', 'success')
    await reloadFases()
  } catch (e) {
    showToast(e.response?.data?.detail || 'Erro ao excluir fase.', 'error')
  } finally {
    isDeleting.value = null
  }
}

// ── Drag-and-drop (todas as fases, ordem salva por usuário) ───────────────

const isReordering = ref(false)
const draggedId    = ref(null)
const dragOverId   = ref(null)

// Chave usada no drag: id quando disponível (DB), senão value (fallback)
const faseKey = (f) => f.id ?? f.value

const onDragStart = (key) => {
  if (!dbReady.value) return
  draggedId.value = key
}
const onDragEnter = (key) => {
  if (!draggedId.value || key === draggedId.value) return
  dragOverId.value = key
}
const onDragLeave = (key) => {
  if (dragOverId.value === key) dragOverId.value = null
}
const onDragEnd = () => {
  draggedId.value  = null
  dragOverId.value = null
}

const onDrop = async (targetKey) => {
  if (!draggedId.value || draggedId.value === targetKey) { onDragEnd(); return }

  const list    = fases.value
  const fromIdx = list.findIndex(f => faseKey(f) === draggedId.value)
  const toIdx   = list.findIndex(f => faseKey(f) === targetKey)
  if (fromIdx === -1 || toIdx === -1) { onDragEnd(); return }

  const reordered = [...list]
  const [moved]   = reordered.splice(fromIdx, 1)
  reordered.splice(toIdx, 0, moved)

  onDragEnd()
  isReordering.value = true
  try {
    await axios.put('/configuracoes/fases/ordem', {
      valores: reordered.map(f => f.value),
    })
    await reloadFases()
  } catch {
    showToast('Erro ao reordenar fases.', 'error')
    await reloadFases()
  } finally {
    isReordering.value = false
  }
}

// ── Create ─────────────────────────────────────────────────────────────────

const showCreate = ref(false)
const createForm  = reactive({ label: '', icon: 'engineering', color: 'blue' })
const isCreating  = ref(false)

const openCreate = () => {
  createForm.label = ''
  createForm.icon  = 'engineering'
  createForm.color = 'blue'
  showCreate.value = true
}

const createFase = async () => {
  if (!dbReady.value) { showToast('Execute a migration 016 para habilitar criação de fases.', 'error'); return }
  if (!createForm.label.trim()) return
  isCreating.value = true
  try {
    await axios.post('/configuracoes/fases', {
      label: createForm.label.trim(),
      icon:  createForm.icon,
      color: createForm.color,
    })
    showCreate.value = false
    await reloadFases()
    showToast('Nova fase criada com sucesso!', 'success')
  } catch (e) {
    showToast(e.response?.data?.detail || 'Erro ao criar fase.', 'error')
  } finally {
    isCreating.value = false
  }
}

onMounted(ensureFases)
</script>

<template>
  <div class="bg-surface rounded-md border border-hairline overflow-hidden">

    <!-- Header -->
    <div class="px-6 py-4 border-b border-hairline">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h3 class="text-sm font-bold text-ink">Fases de Obra</h3>
          <p class="text-xs text-ink-muted mt-0.5 max-w-xl">
            Organize como os serviços são agrupados na EAP e na árvore de orçamento.
            As 5 fases do sistema podem ser renomeadas e reordenadas, mas não excluídas.
            Fases personalizadas podem ser criadas, editadas e excluídas — desde que não tenham itens vinculados.
          </p>
        </div>
        <button
          @click="openCreate"
          :disabled="!dbReady"
          class="shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-orange-500 text-white hover:bg-orange-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Plus class="w-3.5 h-3.5" stroke-width="2" />
          Nova fase
        </button>
      </div>
    </div>

    <!-- Banner: migration pendente -->
    <div v-if="!dbReady" class="px-5 py-3 border-b border-hairline bg-amber-500/8 flex items-start gap-2.5">
      <AlertTriangle class="w-4 h-4 text-amber-600 shrink-0 mt-0.5" stroke-width="1.5" />
      <div>
        <p class="text-xs font-semibold text-amber-700">Migration 016 pendente</p>
        <p class="text-[11px] text-amber-600 mt-0.5 leading-relaxed">
          A tabela <code class="font-mono bg-amber-500/15 px-1 rounded">fases_obra</code> ainda não existe no banco.
          Execute a migration <strong>016_fases_obra.sql</strong> no Supabase para habilitar o gerenciamento de fases.
          Até lá, as 5 fases padrão continuam funcionando normalmente em todo o sistema — só a edição está desabilitada.
        </p>
      </div>
    </div>

    <!-- Info -->
    <div class="px-6 py-2.5 border-b border-hairline bg-canvas/40 flex items-center gap-2">
      <Info class="w-3.5 h-3.5 text-ink-muted shrink-0" stroke-width="1.5" />
      <p class="text-[11px] text-ink-muted">
        As alterações aqui afetam automaticamente a tela de orçamento e os templates EAP de todas as obras.
      </p>
    </div>

    <!-- ── Lista unificada: todas as fases arrastáveis ── -->
    <div class="px-5 py-1.5 bg-canvas/40 border-b border-hairline flex items-center gap-2">
      <div v-if="isReordering" class="flex items-center gap-1.5 text-[10px] text-ink-muted">
        <Loader2 class="w-3 h-3 animate-spin" stroke-width="1.5" />
        Salvando ordem...
      </div>
      <p v-else class="text-[11px] text-ink-muted">
        Arraste qualquer fase para definir a ordem que preferir — inclusive as do sistema.
      </p>
    </div>

    <div class="divide-y divide-hairline">
      <template v-for="fase in fases" :key="faseKey(fase)">
        <!-- Linha draggable -->
        <div
          :draggable="dbReady"
          @dragstart.stop="onDragStart(faseKey(fase))"
          @dragenter.prevent="onDragEnter(faseKey(fase))"
          @dragleave="onDragLeave(faseKey(fase))"
          @dragover.prevent
          @drop.prevent="onDrop(faseKey(fase))"
          @dragend="onDragEnd"
          class="transition-all select-none"
          :class="[
            draggedId  === faseKey(fase) ? 'opacity-40'                   : '',
            dragOverId === faseKey(fase) ? 'border-t-2 border-orange-500' : '',
            editingId  === fase.id       ? 'bg-canvas/50'                 : 'hover:bg-canvas/30',
            dbReady ? 'cursor-grab active:cursor-grabbing' : '',
          ]"
        >
          <div class="flex items-center gap-3 px-5 py-3">
            <!-- Grip handle -->
            <GripVertical class="w-4 h-4 text-ink-muted/40 shrink-0" stroke-width="1.5" />

            <!-- Cor + ícone -->
            <div class="w-7 h-7 rounded-md flex items-center justify-center shrink-0" :class="colorBg(fase.color)">
              <component :is="iconComp(fase.icon)" class="w-4 h-4 text-white" stroke-width="1.5" />
            </div>

            <!-- Label + slug -->
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-ink">{{ fase.label }}</p>
              <p class="text-[11px] text-ink-muted font-mono">{{ fase.value }}</p>
            </div>

            <!-- Badge sistema -->
            <span v-if="fase.tipo === 'SISTEMA'"
              class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-ink-muted/8 text-ink-muted border border-hairline shrink-0">
              Sistema
            </span>

            <!-- Ações -->
            <div class="flex items-center gap-1 shrink-0">
              <button v-if="editingId !== fase.id" type="button" @click="openEdit(fase)"
                :disabled="!dbReady"
                class="p-1.5 rounded-md text-ink-muted hover:text-blue-600 hover:bg-blue-500/10 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                title="Editar nome/ícone/cor">
                <Pencil class="w-3.5 h-3.5" stroke-width="1.5" />
              </button>
              <button
                v-if="fase.tipo === 'CUSTOMIZADO' && editingId !== fase.id"
                type="button"
                @click="deleteFase(fase)"
                :disabled="isDeleting === fase.id"
                class="p-1.5 rounded-md text-ink-muted hover:text-red-500 hover:bg-red-500/10 transition-all disabled:opacity-50"
                title="Excluir fase">
                <Loader2 v-if="isDeleting === fase.id" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
                <Trash2 v-else class="w-3.5 h-3.5" stroke-width="1.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- Formulário de edição inline -->
        <div v-if="editingId === fase.id" class="px-5 pb-4 pt-1 bg-canvas/50 border-t border-hairline">
          <div class="flex items-start gap-4 flex-wrap">
            <div class="flex-1 min-w-[200px]">
              <label class="block text-[11px] font-semibold text-ink-muted mb-1">Nome</label>
              <input v-model="editForm.label" type="text"
                @keydown.enter="saveEdit(fase)" @keydown.escape="cancelEdit"
                class="w-full bg-surface border border-hairline rounded-lg px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-all"
                :placeholder="fase.label" />
            </div>
            <div>
              <p class="text-[11px] font-semibold text-ink-muted mb-1">Ícone</p>
              <div class="flex flex-wrap gap-1">
                <button v-for="ic in ICONS" :key="ic.key" type="button" @click="editForm.icon = ic.key" :title="ic.label"
                  class="w-8 h-8 rounded-md flex items-center justify-center transition-all border"
                  :class="editForm.icon === ic.key ? 'bg-blue-500/15 border-blue-500/50 text-blue-600' : 'border-hairline text-ink-muted hover:bg-canvas hover:text-ink'">
                  <component :is="ic.comp" class="w-4 h-4" stroke-width="1.5" />
                </button>
              </div>
            </div>
            <div>
              <p class="text-[11px] font-semibold text-ink-muted mb-1">Cor</p>
              <div class="flex flex-wrap gap-1.5">
                <button v-for="col in COLORS" :key="col.key" type="button" @click="editForm.color = col.key" :title="col.key"
                  class="w-6 h-6 rounded-full transition-all"
                  :class="[col.bg, editForm.color === col.key ? `ring-2 ring-offset-1 ${col.ring}` : 'opacity-70 hover:opacity-100']" />
              </div>
            </div>
          </div>
          <div class="mt-3 flex items-center gap-2">
            <span class="text-[11px] text-ink-muted">Prévia:</span>
            <div class="w-6 h-6 rounded-md flex items-center justify-center shrink-0" :class="colorBg(editForm.color)">
              <component :is="iconComp(editForm.icon)" class="w-3.5 h-3.5 text-white" stroke-width="1.5" />
            </div>
            <span class="text-sm font-semibold text-ink">{{ editForm.label || fase.label }}</span>
          </div>
          <div class="mt-3 flex items-center gap-2">
            <button type="button" @click="saveEdit(fase)" :disabled="isSaving || !editForm.label.trim()"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              <Loader2 v-if="isSaving" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
              <Save v-else class="w-3.5 h-3.5" stroke-width="1.5" />
              Salvar
            </button>
            <button type="button" @click="cancelEdit" class="px-3 py-1.5 rounded-lg text-xs text-ink-muted hover:bg-canvas transition-colors">
              Cancelar
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- Create form -->
    <div v-if="showCreate" class="px-5 py-4 border-t border-hairline bg-orange-500/5">
      <p class="text-xs font-bold text-orange-600 mb-3">Nova fase personalizada</p>

      <div class="flex items-start gap-4 flex-wrap">

        <!-- Label -->
        <div class="flex-1 min-w-[200px]">
          <label class="block text-[11px] font-semibold text-ink-muted mb-1">Nome <span class="text-red-500">*</span></label>
          <input
            v-model="createForm.label"
            type="text"
            @keydown.enter="createFase"
            @keydown.escape="showCreate = false"
            placeholder="Ex: Paisagismo"
            class="w-full bg-surface border border-hairline rounded-lg px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/50 transition-all"
          />
          <p class="text-[10px] text-ink-muted mt-1">O identificador interno será gerado automaticamente a partir do nome.</p>
        </div>

        <!-- Icon picker -->
        <div>
          <p class="text-[11px] font-semibold text-ink-muted mb-1">Ícone</p>
          <div class="flex flex-wrap gap-1">
            <button
              v-for="ic in ICONS"
              :key="ic.key"
              type="button"
              @click="createForm.icon = ic.key"
              :title="ic.label"
              class="w-8 h-8 rounded-md flex items-center justify-center transition-all border"
              :class="createForm.icon === ic.key
                ? 'bg-orange-500/15 border-orange-500/50 text-orange-600'
                : 'border-hairline text-ink-muted hover:bg-canvas hover:text-ink'"
            >
              <component :is="ic.comp" class="w-4 h-4" stroke-width="1.5" />
            </button>
          </div>
        </div>

        <!-- Color picker -->
        <div>
          <p class="text-[11px] font-semibold text-ink-muted mb-1">Cor</p>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="col in COLORS"
              :key="col.key"
              type="button"
              @click="createForm.color = col.key"
              :title="col.key"
              class="w-6 h-6 rounded-full transition-all"
              :class="[col.bg, createForm.color === col.key ? `ring-2 ring-offset-1 ${col.ring}` : 'opacity-70 hover:opacity-100']"
            />
          </div>
        </div>

      </div>

      <!-- Preview -->
      <div class="mt-3 flex items-center gap-2">
        <span class="text-[11px] text-ink-muted">Prévia:</span>
        <div
          class="w-6 h-6 rounded-md flex items-center justify-center shrink-0"
          :class="colorBg(createForm.color)"
        >
          <component :is="iconComp(createForm.icon)" class="w-3.5 h-3.5 text-white" stroke-width="1.5" />
        </div>
        <span class="text-sm font-semibold text-ink">{{ createForm.label || 'Nova fase' }}</span>
      </div>

      <!-- Actions -->
      <div class="mt-3 flex items-center gap-2">
        <button
          type="button"
          @click="createFase"
          :disabled="isCreating || !createForm.label.trim()"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Loader2 v-if="isCreating" class="w-3.5 h-3.5 animate-spin" stroke-width="1.5" />
          <Plus v-else class="w-3.5 h-3.5" stroke-width="2" />
          Criar fase
        </button>
        <button
          type="button"
          @click="showCreate = false"
          class="px-3 py-1.5 rounded-lg text-xs text-ink-muted hover:bg-canvas transition-colors"
        >
          Cancelar
        </button>
      </div>
    </div>

    <!-- Empty create CTA (when no create form open) -->
    <div v-else class="px-5 py-3 border-t border-hairline">
      <button
        type="button"
        @click="openCreate"
        class="flex items-center gap-1.5 text-xs font-medium text-ink-muted hover:text-orange-600 transition-colors group"
      >
        <span class="w-5 h-5 rounded-md flex items-center justify-center bg-canvas border border-hairline group-hover:bg-orange-500/10 group-hover:border-orange-500/30 transition-all">
          <Plus class="w-3 h-3" stroke-width="2.5" />
        </span>
        Adicionar fase personalizada
      </button>
    </div>

  </div>
</template>
