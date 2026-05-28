<script setup>
import { ref, computed, onMounted } from 'vue'
import { supabase } from '../../supabase'
import { useToast } from '../../composables/useToast'
import axios from 'axios'
import BaseButton from '../ui/BaseButton.vue'
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Loader2,
  Plus,
  MapPin,
  X,
  Trash2,
  ImagePlus
} from 'lucide-vue-next'

const { showToast } = useToast()

const vitrine = ref({
  slug_vitrine: '',
  descricao_vitrine: '',
  fotos_portfolio: [],
  cidades_atuacao: []
})
const isLoading = ref(true)
const isSavingSlug = ref(false)
const isSavingBio = ref(false)
const isSavingCidades = ref(false)
const isSavingPortfolio = ref(false)

const cidadeInput = ref('')

const SLUG_REGEX = /^[a-z0-9][a-z0-9-]{2,49}$/

const slugError = computed(() => {
  const s = vitrine.value.slug_vitrine
  if (!s) return ''
  if (s !== s.toLowerCase()) return 'Use apenas letras minúsculas.'
  if (!SLUG_REGEX.test(s)) return 'Use 3–50 caracteres: letras minúsculas, números e hífens. Deve começar com letra ou número.'
  return ''
})

const slugPreview = computed(() => {
  const s = vitrine.value.slug_vitrine
  return s ? `vertice.app/p/${s}` : 'vertice.app/p/seu-slug'
})

const fetchVitrine = async () => {
  isLoading.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return
    const { data } = await supabase
      .from('perfis_b2b')
      .select('slug_vitrine, descricao_vitrine, fotos_portfolio, cidades_atuacao')
      .eq('id', user.id)
      .single()
    if (data) {
      vitrine.value = {
        slug_vitrine: data.slug_vitrine || '',
        descricao_vitrine: data.descricao_vitrine || '',
        fotos_portfolio: data.fotos_portfolio || [],
        cidades_atuacao: data.cidades_atuacao || []
      }
    }
  } catch (e) {
    console.error('Erro ao carregar vitrine:', e)
  } finally {
    isLoading.value = false
  }
}

const saveSlug = async () => {
  if (slugError.value) return
  isSavingSlug.value = true
  try {
    await axios.post('/api/vitrine/configurar', {
      slug_vitrine: vitrine.value.slug_vitrine.toLowerCase().trim()
    })
    showToast('URL da vitrine salva!', 'success')
  } catch (e) {
    const msg = e.response?.data?.detail || 'Erro ao salvar URL. Verifique se o slug já está em uso.'
    showToast(msg, 'error')
  } finally {
    isSavingSlug.value = false
  }
}

const saveBio = async () => {
  isSavingBio.value = true
  try {
    await axios.post('/api/vitrine/configurar', {
      descricao_vitrine: vitrine.value.descricao_vitrine
    })
    showToast('Apresentação salva!', 'success')
  } catch (e) {
    showToast('Erro ao salvar apresentação.', 'error')
  } finally {
    isSavingBio.value = false
  }
}

const addCidade = () => {
  const cidade = cidadeInput.value.trim()
  if (!cidade || vitrine.value.cidades_atuacao.includes(cidade)) {
    cidadeInput.value = ''
    return
  }
  vitrine.value.cidades_atuacao.push(cidade)
  cidadeInput.value = ''
}

const removeCidade = (index) => {
  vitrine.value.cidades_atuacao.splice(index, 1)
}

const saveCidades = async () => {
  if (cidadeInput.value.trim()) addCidade()
  isSavingCidades.value = true
  try {
    await axios.post('/api/vitrine/configurar', {
      cidades_atuacao: vitrine.value.cidades_atuacao
    })
    showToast('Cidades de atuação salvas!', 'success')
  } catch (e) {
    showToast('Erro ao salvar cidades.', 'error')
  } finally {
    isSavingCidades.value = false
  }
}

const handlePortfolioUpload = async (event) => {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  isSavingPortfolio.value = true
  try {
    const newUrls = []
    for (const file of files) {
      const ext = file.name.split('.').pop()
      const filePath = `portfolio/${Math.random().toString(36).slice(2)}.${ext}`
      const { error } = await supabase.storage.from('identidade').upload(filePath, file)
      if (error) { showToast(`Erro ao enviar ${file.name}.`, 'error'); continue }
      const { data: { publicUrl } } = supabase.storage.from('identidade').getPublicUrl(filePath)
      newUrls.push(publicUrl)
    }
    if (newUrls.length) {
      vitrine.value.fotos_portfolio = [...vitrine.value.fotos_portfolio, ...newUrls]
      await axios.post('/api/vitrine/configurar', {
        fotos_portfolio: vitrine.value.fotos_portfolio
      })
      showToast(`${newUrls.length} foto(s) adicionada(s)!`, 'success')
    }
  } catch (e) {
    showToast('Erro ao salvar portfólio.', 'error')
  } finally {
    isSavingPortfolio.value = false
    event.target.value = ''
  }
}

const removePortfolioPhoto = async (index) => {
  vitrine.value.fotos_portfolio.splice(index, 1)
  isSavingPortfolio.value = true
  try {
    await axios.post('/api/vitrine/configurar', {
      fotos_portfolio: vitrine.value.fotos_portfolio
    })
    showToast('Foto removida.', 'info')
  } catch (e) {
    showToast('Erro ao atualizar portfólio.', 'error')
  } finally {
    isSavingPortfolio.value = false
  }
}

onMounted(fetchVitrine)
</script>

<template>
  <div v-if="isLoading" class="flex justify-center py-16">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary"></div>
  </div>

  <div v-else class="space-y-5">

    <!-- Card: URL da Vitrine -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">URL da Vitrine</h3>
        <p class="text-xs text-ink-muted mt-0.5">Defina o endereço público do seu perfil de engenheiro.</p>
      </div>
      <div class="px-6 py-5 space-y-4">
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-ink-muted uppercase tracking-wide">Slug Personalizado</label>
          <div class="flex items-center gap-0 border border-hairline rounded-md overflow-hidden focus-within:ring-1 focus-within:ring-brand-primary focus-within:border-brand-primary transition-all bg-canvas" :class="slugError ? 'border-red-400 focus-within:ring-red-400' : ''">
            <span class="px-3 py-2.5 text-sm text-ink-muted bg-canvas/50 border-r border-hairline shrink-0 select-none">vertice.app/p/</span>
            <input
              v-model="vitrine.slug_vitrine"
              type="text"
              class="flex-1 px-3 py-2.5 text-sm text-ink bg-transparent outline-none placeholder:text-ink-muted font-mono"
              placeholder="seu-nome"
              @input="vitrine.slug_vitrine = vitrine.slug_vitrine.toLowerCase()"
            />
          </div>
          <p v-if="slugError" class="text-xs text-red-500 flex items-center gap-1">
            <AlertTriangle class="w-3.5 h-3.5" stroke-width="1.5" />
            {{ slugError }}
          </p>
          <p v-else-if="vitrine.slug_vitrine" class="text-xs text-ink-muted flex items-center gap-1">
            <CheckCircle2 class="w-3.5 h-3.5 text-green-500" stroke-width="1.5" />
            Seu perfil ficará em <span class="font-mono text-brand-primary ml-1">{{ slugPreview }}</span>
          </p>
          <p v-else class="text-xs text-ink-muted">Use 3–50 caracteres: letras minúsculas, números e hífens.</p>
        </div>
      </div>
      <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex items-center justify-between gap-3">
        <a
          v-if="vitrine.slug_vitrine && !slugError"
          :href="`/p/${vitrine.slug_vitrine}`"
          target="_blank"
          class="flex items-center gap-1.5 text-xs font-semibold text-ink-muted hover:text-brand-primary transition-colors"
        >
          <ExternalLink class="w-3.5 h-3.5" stroke-width="1.5" />
          Visualizar Vitrine
        </a>
        <span v-else class="text-xs text-ink-muted italic">Salve uma URL para visualizar</span>
        <BaseButton
          variant="primary"
          @click="saveSlug"
          :disabled="isSavingSlug || !!slugError || !vitrine.slug_vitrine"
          class="px-5 h-9 font-bold gap-2"
        >
          <Loader2 v-if="isSavingSlug" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          {{ isSavingSlug ? 'Salvando...' : 'Salvar URL' }}
        </BaseButton>
      </div>
    </div>

    <!-- Card: Apresentação -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Apresentação</h3>
        <p class="text-xs text-ink-muted mt-0.5">Descreva sua experiência, especialidades e diferenciais. Visível no seu perfil público.</p>
      </div>
      <div class="px-6 py-5">
        <textarea
          v-model="vitrine.descricao_vitrine"
          rows="5"
          class="w-full bg-canvas border border-hairline text-ink rounded-md px-4 py-3 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all resize-none placeholder:text-ink-muted leading-relaxed"
          placeholder="Ex: Engenheiro civil com 10 anos de experiência em obras residenciais de alto padrão no litoral catarinense. Especialista em estruturas metálicas e gerenciamento de obras Caixa..."
        ></textarea>
        <p class="text-xs text-ink-muted mt-1.5 text-right">{{ vitrine.descricao_vitrine.length }} / 1000 caracteres</p>
      </div>
      <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex justify-end">
        <BaseButton
          variant="primary"
          @click="saveBio"
          :disabled="isSavingBio"
          class="px-5 h-9 font-bold gap-2"
        >
          <Loader2 v-if="isSavingBio" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          {{ isSavingBio ? 'Salvando...' : 'Salvar Apresentação' }}
        </BaseButton>
      </div>
    </div>

    <!-- Card: Cidades de Atuação -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Cidades de Atuação</h3>
        <p class="text-xs text-ink-muted mt-0.5">Informe onde você atua para aparecer no matchmaking da região.</p>
      </div>
      <div class="px-6 py-5 space-y-3">
        <div class="flex gap-2">
          <input
            v-model="cidadeInput"
            type="text"
            class="flex-1 bg-canvas border border-hairline text-ink rounded-md px-4 py-2.5 text-sm focus:ring-1 focus:ring-brand-primary focus:border-brand-primary outline-none transition-all placeholder:text-ink-muted"
            placeholder="Ex: Florianópolis - SC"
            @keydown.enter.prevent="addCidade"
            @keydown.,.prevent="addCidade"
          />
          <BaseButton
            variant="primary"
            size="icon"
            @click="addCidade"
            class="h-10 w-10 shrink-0"
          >
            <Plus class="w-4 h-4" stroke-width="1.5" />
          </BaseButton>
        </div>
        <p class="text-xs text-ink-muted">Pressione Enter ou vírgula para adicionar.</p>
        <div v-if="vitrine.cidades_atuacao.length" class="flex flex-wrap gap-2 pt-1">
          <span
            v-for="(cidade, i) in vitrine.cidades_atuacao"
            :key="i"
            class="flex items-center gap-1.5 bg-brand-primary/10 text-brand-primary px-3 py-1.5 rounded-lg text-xs font-semibold"
          >
            <MapPin class="w-3.5 h-3.5 text-brand-primary shrink-0" stroke-width="1.5" />
            {{ cidade }}
            <button @click="removeCidade(i)" class="ml-0.5 hover:text-red-500 transition-colors cursor-pointer flex items-center justify-center">
              <X class="w-3 h-3 hover:text-red-500 transition-colors" stroke-width="1.5" />
            </button>
          </span>
        </div>
        <p v-else class="text-xs text-ink-muted italic">Nenhuma cidade adicionada ainda.</p>
      </div>
      <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex justify-end">
        <BaseButton
          variant="primary"
          @click="saveCidades"
          :disabled="isSavingCidades"
          class="px-5 h-9 font-bold gap-2"
        >
          <Loader2 v-if="isSavingCidades" class="w-4 h-4 animate-spin" stroke-width="1.5" />
          {{ isSavingCidades ? 'Salvando...' : 'Salvar Cidades' }}
        </BaseButton>
      </div>
    </div>

    <!-- Card: Portfólio de Obras -->
    <div class="bg-surface rounded-md border border-hairline overflow-hidden">
      <div class="px-6 py-5 border-b border-hairline">
        <h3 class="text-sm font-bold text-ink">Portfólio de Obras</h3>
        <p class="text-xs text-ink-muted mt-0.5">Fotos das suas obras concluídas. Exibidas na galeria do seu perfil público.</p>
      </div>
      <div class="px-6 py-5 space-y-4">
        <!-- Grid de fotos -->
        <div v-if="vitrine.fotos_portfolio.length" class="grid grid-cols-3 sm:grid-cols-4 gap-3">
          <div
            v-for="(url, i) in vitrine.fotos_portfolio"
            :key="url"
            class="relative group aspect-square rounded-md overflow-hidden border border-hairline bg-canvas"
          >
            <img :src="url" class="h-full w-full object-cover" />
            <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <BaseButton
                variant="danger"
                size="icon"
                @click="removePortfolioPhoto(i)"
                class="p-1.5 rounded-lg text-white"
              >
                <Trash2 class="w-4 h-4 text-white" stroke-width="1.5" />
              </BaseButton>
            </div>
          </div>

          <!-- Botão de adicionar mais -->
          <label class="aspect-square rounded-md border-2 border-dashed border-hairline hover:border-brand-primary/50 bg-canvas hover:bg-brand-primary/5 flex flex-col items-center justify-center gap-1 cursor-pointer transition-colors group">
            <ImagePlus class="w-6 h-6 text-ink-muted group-hover:text-brand-primary transition-colors" stroke-width="1.5" />
            <span class="text-[10px] text-ink-muted group-hover:text-brand-primary font-semibold uppercase tracking-wide transition-colors">Adicionar</span>
            <input type="file" class="hidden" accept="image/*" multiple @change="handlePortfolioUpload" :disabled="isSavingPortfolio" />
          </label>
        </div>

        <!-- Estado vazio -->
        <div v-else>
          <label class="flex flex-col items-center justify-center gap-3 py-10 border-2 border-dashed border-hairline rounded-md hover:border-brand-primary/50 hover:bg-brand-primary/5 transition-colors cursor-pointer group">
            <ImagePlus class="w-10 h-10 text-ink-muted group-hover:text-brand-primary transition-colors" stroke-width="1.5" />
            <div class="text-center">
              <p class="text-sm font-semibold text-ink-muted group-hover:text-brand-primary transition-colors">Clique para adicionar fotos</p>
              <p class="text-xs text-ink-muted mt-0.5">PNG, JPG até 10 MB. Múltiplos arquivos suportados.</p>
            </div>
            <input type="file" class="hidden" accept="image/*" multiple @change="handlePortfolioUpload" :disabled="isSavingPortfolio" />
          </label>
        </div>

        <div v-if="isSavingPortfolio" class="flex items-center gap-2 text-xs text-ink-muted">
          <Loader2 class="w-4 h-4 animate-spin" stroke-width="1.5" />
          Enviando fotos...
        </div>
      </div>
      <div class="px-6 py-4 bg-canvas/50 border-t border-hairline flex items-center justify-between">
        <p class="text-xs text-ink-muted">{{ vitrine.fotos_portfolio.length }} foto(s) no portfólio</p>
        <p v-if="vitrine.slug_vitrine" class="text-xs text-ink-muted">
          Visível em <a :href="`/p/${vitrine.slug_vitrine}`" target="_blank" class="text-brand-primary hover:underline font-mono">{{ slugPreview }}</a>
        </p>
      </div>
    </div>

  </div>
</template>
