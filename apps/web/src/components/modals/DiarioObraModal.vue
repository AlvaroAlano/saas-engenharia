<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { supabase } from '../../supabase'
import { useToast } from '../../composables/useToast'
import { compressImage, formatFileSize } from '../../utils/imageCompressor'
import { Camera, X, SquarePen, Loader2, Image, Send, History, Images, Clock, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  isOpen: Boolean,
  projectId: String,
  projectName: String
})

const emit = defineEmits(['close', 'posted'])
const { showToast } = useToast()

// --- Estado do formulário ---
const descricao = ref('')
const imageFile = ref(null)
const imagePreview = ref(null)
const compressedBlob = ref(null)
const compressionInfo = ref(null)
const isSubmitting = ref(false)
const isCompressing = ref(false)

// --- Estado do feed ---
const feedPosts = ref([])
const isLoadingFeed = ref(false)

// --- Computed ---
const canSubmit = computed(() => descricao.value.trim().length > 0 && !isSubmitting.value && !isCompressing.value)

// --- Watchers ---
watch(() => props.isOpen, (open) => {
  if (open && props.projectId) {
    carregarFeed()
    resetForm()
  }
})

// --- Métodos ---
const resetForm = () => {
  descricao.value = ''
  imageFile.value = null
  imagePreview.value = null
  compressedBlob.value = null
  compressionInfo.value = null
}

const carregarFeed = async () => {
  isLoadingFeed.value = true
  try {
    const res = await axios.get(`/portal/feed/${props.projectId}`)
    if (res.data.success) {
      feedPosts.value = res.data.data
    }
  } catch (err) {
    console.error('Erro ao carregar feed:', err)
  } finally {
    isLoadingFeed.value = false
  }
}

const handleFileSelect = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  // Validação básica
  if (!file.type.startsWith('image/')) {
    showToast('Selecione um arquivo de imagem válido.', 'error')
    return
  }

  if (file.size > 20 * 1024 * 1024) {
    showToast('Imagem muito grande. Máximo de 20 MB.', 'error')
    return
  }

  isCompressing.value = true
  try {
    const result = await compressImage(file, {
      maxWidth: 1200,
      maxHeight: 1200,
      quality: 0.7
    })
    imageFile.value = file
    imagePreview.value = result.dataUrl
    compressedBlob.value = result.blob
    compressionInfo.value = {
      original: formatFileSize(result.originalSize),
      compressed: formatFileSize(result.compressedSize),
      reduction: Math.round((1 - result.compressedSize / result.originalSize) * 100)
    }
  } catch (err) {
    console.error('Erro na compressão:', err)
    showToast('Erro ao processar imagem.', 'error')
  } finally {
    isCompressing.value = false
  }
}

const removeImage = () => {
  imageFile.value = null
  imagePreview.value = null
  compressedBlob.value = null
  compressionInfo.value = null
  // Reset do input file
  const input = document.getElementById('diario-file-input')
  if (input) input.value = ''
}

const uploadImageToStorage = async () => {
  if (!compressedBlob.value || !props.projectId) return null

  const fileName = `diario/${props.projectId}/${Date.now()}_${Math.random().toString(36).slice(2, 8)}.jpg`

  const { data, error } = await supabase.storage
    .from('obras-fotos')
    .upload(fileName, compressedBlob.value, {
      contentType: 'image/jpeg',
      cacheControl: '31536000',
      upsert: false
    })

  if (error) {
    console.error('Erro no upload ao Storage:', error)
    throw new Error(`Upload falhou: ${error.message}`)
  }

  // Gera URL pública
  const { data: urlData } = supabase.storage
    .from('obras-fotos')
    .getPublicUrl(data.path)

  return urlData.publicUrl
}

const publicarPost = async () => {
  if (!canSubmit.value) return

  isSubmitting.value = true
  try {
    let imagensUrls = []

    // Upload da imagem se houver
    if (compressedBlob.value) {
      const url = await uploadImageToStorage()
      if (url) imagensUrls.push(url)
    }

    // Criar post via API backend
    await axios.post('/portal/feed', {
      projeto_id: props.projectId,
      descricao: descricao.value.trim(),
      imagens: imagensUrls
    })

    showToast('Post publicado no diário de obra!', 'success')
    resetForm()
    await carregarFeed()
    emit('posted')
  } catch (err) {
    console.error('Erro ao publicar post:', err)
    showToast(err.response?.data?.detail || 'Erro ao publicar post.', 'error')
  } finally {
    isSubmitting.value = false
  }
}

const deletarPost = async (postId) => {
  if (!confirm('Excluir este registro do diário?')) return
  try {
    await axios.delete(`/portal/feed/${postId}`)
    feedPosts.value = feedPosts.value.filter(p => p.id !== postId)
    showToast('Registro excluído.', 'success')
  } catch (err) {
    console.error('Erro ao deletar post:', err)
    showToast('Erro ao excluir registro.', 'error')
  }
}

const formatDate = (isoDate) => {
  if (!isoDate) return '—'
  const d = new Date(isoDate)
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 z-[130] flex items-end sm:items-center justify-center bg-black/45 dark:bg-black/65 backdrop-blur-sm p-4" style="z-index: 130;" @click.self="emit('close')">
      
      <!-- Container Mobile-First: Sobe do fundo no mobile, centralizado no desktop -->
      <div class="bg-surface w-full sm:max-w-lg sm:rounded-md rounded-t-md border border-hairline shadow-2xl flex flex-col max-h-[92vh] sm:max-h-[85vh] overflow-hidden animate-in slide-in-from-bottom duration-300">
        
        <!-- Header Fixo -->
        <div class="px-6 py-4 border-b border-hairline flex items-center justify-between bg-surface shrink-0">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 bg-blue-500/10 rounded-md flex items-center justify-center shrink-0">
              <Camera class="w-5 h-5 text-blue-600" stroke-width="1.5" />
            </div>
            <div>
              <h3 class="text-lg font-medium text-ink leading-tight select-none">Diário de Obra</h3>
              <p class="text-[10px] text-ink-muted font-bold uppercase tracking-wider mt-0.5 select-none font-sans">{{ projectName || 'Projeto' }}</p>
            </div>
          </div>
          <button @click="emit('close')" class="text-ink-muted hover:text-ink transition-colors p-1.5 rounded-md hover:bg-surface-hover flex items-center justify-center cursor-pointer select-none">
            <X class="w-4 h-4" stroke-width="1.25" />
          </button>
        </div>

        <!-- Conteúdo Scrollável -->
        <div class="flex-1 overflow-y-auto">
          
          <!-- Formulário de Novo Post -->
          <div class="p-6 space-y-4 bg-surface border-b border-hairline">
            <p class="text-[10px] text-ink-muted font-bold uppercase tracking-wider flex items-center gap-1.5 select-none font-sans">
              <SquarePen class="w-3.5 h-3.5" stroke-width="1.5" />
              Novo Registro de Canteiro
            </p>
            
            <!-- Textarea Descrição -->
            <textarea 
              v-model="descricao"
              rows="3"
              placeholder="O que aconteceu hoje na obra? Ex: Concretagem da laje do térreo concluída..."
              class="w-full bg-black/[0.04] dark:bg-neutral-800/60 border border-transparent text-ink rounded-md py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent transition-all placeholder:text-ink-muted/80 font-sans resize-none"
            ></textarea>

            <!-- Área de Foto -->
            <div class="mt-3">
              <!-- Preview da imagem comprimida -->
              <div v-if="imagePreview" class="relative rounded-md overflow-hidden border border-hairline bg-canvas">
                <img :src="imagePreview" alt="Preview" class="w-full h-48 object-cover" />
                <!-- Badge de compressão -->
                <div v-if="compressionInfo" class="absolute bottom-2 left-2 bg-black/70 text-white text-[9px] font-mono px-2 py-1 rounded-md backdrop-blur-sm select-none">
                  {{ compressionInfo.original }} → {{ compressionInfo.compressed }} 
                  <span class="text-emerald-400 font-bold">(−{{ compressionInfo.reduction }}%)</span>
                </div>
                <!-- Botão remover -->
                <button @click="removeImage" class="absolute top-2 right-2 w-7 h-7 bg-red-600 hover:bg-red-700 text-white rounded-md flex items-center justify-center shadow-lg transition-colors cursor-pointer select-none">
                  <X class="w-3.5 h-3.5" stroke-width="1.5" />
                </button>
              </div>

              <!-- Estado de compressão -->
              <div v-else-if="isCompressing" class="flex items-center justify-center gap-2 py-6 text-ink-muted text-sm border border-dashed border-hairline rounded-md bg-black/[0.02] dark:bg-neutral-800/20 select-none font-sans">
                <Loader2 class="w-4 h-4 animate-spin text-blue-600" stroke-width="1.5" />
                Processando e comprimindo imagem...
              </div>

              <!-- Botões de captura/upload -->
              <div v-else class="flex gap-2 select-none">
                <label class="flex-1 flex items-center justify-center gap-2 py-2 border border-dashed border-hairline hover:border-blue-500/55 rounded-md cursor-pointer bg-black/[0.02] dark:bg-neutral-800/20 hover:bg-blue-500/5 transition-all text-sm text-ink-muted hover:text-ink group font-sans font-medium">
                  <Camera class="w-4 h-4 text-ink-muted group-hover:text-blue-600 transition-colors" stroke-width="1.5" />
                  <span>Tirar Foto</span>
                  <input 
                    id="diario-file-input-camera"
                    type="file" 
                    accept="image/*" 
                    capture="environment"
                    class="hidden" 
                    @change="handleFileSelect"
                  />
                </label>
                <label class="flex items-center justify-center gap-1.5 px-4 py-2 border border-dashed border-hairline hover:border-blue-500/55 rounded-md cursor-pointer bg-black/[0.02] dark:bg-neutral-800/20 hover:bg-blue-500/5 transition-all text-sm text-ink-muted hover:text-ink group font-sans font-medium">
                  <Image class="w-4 h-4 text-ink-muted group-hover:text-blue-600 transition-colors" stroke-width="1.5" />
                  <span>Galeria</span>
                  <input 
                    id="diario-file-input"
                    type="file" 
                    accept="image/*"
                    class="hidden" 
                    @change="handleFileSelect"
                  />
                </label>
              </div>
            </div>

            <!-- Botão Publicar -->
            <button
              @click="publicarPost"
              :disabled="!canSubmit"
              class="w-full mt-4 h-10 px-4 rounded-md font-medium text-sm transition-all flex items-center justify-center gap-1.5 shadow-sm select-none"
              :class="canSubmit 
                ? 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer' 
                : 'bg-black/[0.04] dark:bg-neutral-800/60 text-ink-muted cursor-not-allowed border border-hairline'"
            >
              <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" stroke-width="1.5" />
              <Send v-else class="w-4 h-4" stroke-width="1.5" />
              {{ isSubmitting ? 'Publicando...' : 'Publicar no Diário' }}
            </button>
          </div>

          <!-- Feed / Timeline do Diário -->
          <div class="px-6 py-5 bg-canvas border-t border-hairline">
            <p class="text-[10px] text-ink-muted font-bold uppercase tracking-wider mb-4 flex items-center gap-1.5 select-none font-sans">
              <History class="w-3.5 h-3.5" stroke-width="1.5" />
              Histórico de Canteiro ({{ feedPosts.length }})
            </p>

            <!-- Loading -->
            <div v-if="isLoadingFeed" class="flex items-center justify-center py-8 text-ink-muted font-sans select-none">
              <Loader2 class="w-4 h-4 animate-spin mr-2 text-blue-600" stroke-width="1.5" />
              Carregando registros...
            </div>

            <!-- Vazio -->
            <div v-else-if="feedPosts.length === 0" class="text-center py-8 select-none">
              <div class="w-14 h-14 bg-black/[0.04] dark:bg-neutral-800/60 rounded-md flex items-center justify-center mx-auto mb-3">
                <Images class="w-6 h-6 text-ink-muted" stroke-width="1.5" />
              </div>
              <p class="text-xs font-semibold text-ink">Nenhum registro ainda</p>
              <p class="text-[11px] text-ink-muted mt-1 font-sans">Publique o primeiro registro fotográfico da obra acima.</p>
            </div>

            <!-- Lista de Posts -->
            <div v-else class="space-y-3">
              <div v-for="post in feedPosts" :key="post.id" class="bg-surface rounded-md border border-hairline overflow-hidden shadow-sm transition-all">
                
                <!-- Imagem do post -->
                <div v-if="post.imagens && post.imagens.length > 0" class="relative">
                  <img :src="post.imagens[0]" alt="Foto da obra" class="w-full h-44 object-cover select-none" />
                  <span v-if="post.imagens.length > 1" class="absolute bottom-2 right-2 bg-black/70 text-white text-[9px] font-bold px-2 py-1 rounded-md select-none font-mono">
                    +{{ post.imagens.length - 1 }} fotos
                  </span>
                </div>

                <!-- Conteúdo -->
                <div class="p-4">
                  <p class="text-xs text-ink leading-relaxed whitespace-pre-wrap select-text font-sans">{{ post.descricao }}</p>
                  <div class="flex items-center justify-between mt-3 pt-2.5 border-t border-hairline">
                    <span class="text-[9px] text-ink-muted font-mono flex items-center gap-1 select-none">
                      <Clock class="w-3 h-3 text-ink-muted" stroke-width="1.5" />
                      {{ formatDate(post.criado_em) }}
                    </span>
                    <button 
                      @click.stop="deletarPost(post.id)" 
                      class="p-1 rounded-md text-ink-muted hover:text-red-650 hover:bg-red-500/10 transition-all cursor-pointer flex items-center justify-center select-none"
                      title="Excluir registro"
                    >
                      <Trash2 class="w-3.5 h-3.5" stroke-width="1.5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>
