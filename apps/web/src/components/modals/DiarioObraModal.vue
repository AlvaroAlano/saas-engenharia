<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { supabase } from '../../supabase'
import { useToast } from '../../composables/useToast'
import { compressImage, formatFileSize } from '../../utils/imageCompressor'

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
    <div v-if="isOpen" class="fixed inset-0 z-[130] flex items-end sm:items-center justify-center bg-slate-900/60 backdrop-blur-sm" style="z-index: 130;" @click.self="emit('close')">
      
      <!-- Container Mobile-First: Sobe do fundo no mobile, centralizado no desktop -->
      <div class="bg-white w-full sm:max-w-lg sm:rounded-2xl rounded-t-2xl shadow-2xl flex flex-col max-h-[92vh] sm:max-h-[85vh] overflow-hidden animate-in slide-in-from-bottom duration-300">
        
        <!-- Header Fixo -->
        <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-slate-50 to-white shrink-0">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 bg-indigo-100 rounded-xl flex items-center justify-center">
              <span class="material-symbols-outlined text-indigo-600 text-lg" style="font-variation-settings: 'FILL' 1;">photo_camera</span>
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-800">Diário de Obra</h3>
              <p class="text-[10px] text-slate-400 font-medium uppercase tracking-wide">{{ projectName || 'Projeto' }}</p>
            </div>
          </div>
          <button @click="emit('close')" class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors">
            <span class="material-symbols-outlined text-xl">close</span>
          </button>
        </div>

        <!-- Conteúdo Scrollável -->
        <div class="flex-1 overflow-y-auto">
          
          <!-- Formulário de Novo Post -->
          <div class="px-5 py-4 border-b border-slate-100 bg-white">
            <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-3 flex items-center gap-1">
              <span class="material-symbols-outlined text-xs">edit_note</span>
              Novo Registro
            </p>
            
            <!-- Textarea Descrição -->
            <textarea 
              v-model="descricao"
              rows="3"
              placeholder="O que aconteceu hoje na obra? Ex: Concretagem da laje do térreo concluída..."
              class="w-full bg-slate-50 border border-slate-200 rounded-xl py-3 px-4 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 transition-all resize-none"
            ></textarea>

            <!-- Área de Foto -->
            <div class="mt-3">
              <!-- Preview da imagem comprimida -->
              <div v-if="imagePreview" class="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-50">
                <img :src="imagePreview" alt="Preview" class="w-full h-48 object-cover" />
                <!-- Badge de compressão -->
                <div v-if="compressionInfo" class="absolute bottom-2 left-2 bg-black/70 text-white text-[9px] font-mono px-2 py-1 rounded-md backdrop-blur-sm">
                  {{ compressionInfo.original }} → {{ compressionInfo.compressed }} 
                  <span class="text-emerald-400 font-bold">(−{{ compressionInfo.reduction }}%)</span>
                </div>
                <!-- Botão remover -->
                <button @click="removeImage" class="absolute top-2 right-2 w-7 h-7 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center shadow-lg transition-colors">
                  <span class="material-symbols-outlined text-sm">close</span>
                </button>
              </div>

              <!-- Estado de compressão -->
              <div v-else-if="isCompressing" class="flex items-center justify-center gap-2 py-6 text-slate-500 text-sm border border-dashed border-slate-200 rounded-xl bg-slate-50">
                <span class="material-symbols-outlined animate-spin text-indigo-500">progress_activity</span>
                Comprimindo imagem...
              </div>

              <!-- Botões de captura/upload -->
              <div v-else class="flex gap-2">
                <label class="flex-1 flex items-center justify-center gap-2 py-3 border-2 border-dashed border-slate-200 hover:border-indigo-300 rounded-xl cursor-pointer bg-slate-50 hover:bg-indigo-50/50 transition-all text-sm text-slate-500 hover:text-indigo-600 group">
                  <span class="material-symbols-outlined text-lg group-hover:text-indigo-500 transition-colors" style="font-variation-settings: 'FILL' 1;">photo_camera</span>
                  <span class="font-medium">Tirar Foto</span>
                  <input 
                    id="diario-file-input-camera"
                    type="file" 
                    accept="image/*" 
                    capture="environment"
                    class="hidden" 
                    @change="handleFileSelect"
                  />
                </label>
                <label class="flex items-center justify-center gap-1.5 px-4 py-3 border-2 border-dashed border-slate-200 hover:border-indigo-300 rounded-xl cursor-pointer bg-slate-50 hover:bg-indigo-50/50 transition-all text-sm text-slate-500 hover:text-indigo-600 group">
                  <span class="material-symbols-outlined text-lg group-hover:text-indigo-500 transition-colors">image</span>
                  <span class="font-medium">Galeria</span>
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
              class="w-full mt-4 py-3 rounded-xl font-bold text-sm uppercase tracking-wide transition-all flex items-center justify-center gap-2 shadow-sm active:scale-[0.98]"
              :class="canSubmit 
                ? 'bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer' 
                : 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'"
            >
              <span v-if="isSubmitting" class="material-symbols-outlined animate-spin text-lg">sync</span>
              <span v-else class="material-symbols-outlined text-lg">send</span>
              {{ isSubmitting ? 'Publicando...' : 'Publicar no Diário' }}
            </button>
          </div>

          <!-- Feed / Timeline do Diário -->
          <div class="px-5 py-4 bg-slate-50/80">
            <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-4 flex items-center gap-1">
              <span class="material-symbols-outlined text-xs">timeline</span>
              Registros Anteriores ({{ feedPosts.length }})
            </p>

            <!-- Loading -->
            <div v-if="isLoadingFeed" class="flex items-center justify-center py-8 text-slate-400">
              <span class="material-symbols-outlined animate-spin text-xl mr-2">progress_activity</span>
              Carregando registros...
            </div>

            <!-- Vazio -->
            <div v-else-if="feedPosts.length === 0" class="text-center py-8">
              <div class="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <span class="material-symbols-outlined text-2xl text-slate-300">photo_library</span>
              </div>
              <p class="text-xs font-semibold text-slate-500">Nenhum registro ainda</p>
              <p class="text-[11px] text-slate-400 mt-1">Publique o primeiro registro fotográfico da obra acima.</p>
            </div>

            <!-- Lista de Posts -->
            <div v-else class="space-y-3">
              <div v-for="post in feedPosts" :key="post.id" class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                
                <!-- Imagem do post -->
                <div v-if="post.imagens && post.imagens.length > 0" class="relative">
                  <img :src="post.imagens[0]" alt="Foto da obra" class="w-full h-44 object-cover" />
                  <span v-if="post.imagens.length > 1" class="absolute bottom-2 right-2 bg-black/60 text-white text-[9px] font-bold px-2 py-1 rounded-md">
                    +{{ post.imagens.length - 1 }} fotos
                  </span>
                </div>

                <!-- Conteúdo -->
                <div class="p-3.5">
                  <p class="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">{{ post.descricao }}</p>
                  <div class="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-100">
                    <span class="text-[9px] text-slate-400 font-mono flex items-center gap-1">
                      <span class="material-symbols-outlined text-[11px]">schedule</span>
                      {{ formatDate(post.criado_em) }}
                    </span>
                    <button 
                      @click.stop="deletarPost(post.id)" 
                      class="text-slate-400 hover:text-red-500 p-1 rounded transition-colors"
                      title="Excluir registro"
                    >
                      <span class="material-symbols-outlined text-sm">delete</span>
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
