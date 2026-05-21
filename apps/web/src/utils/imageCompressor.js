/**
 * Compressor de Imagem Client-Side via Canvas API
 * Usado no Diário de Obra para reduzir tamanho antes do upload ao Supabase Storage.
 * Reduz significativamente custos de hospedagem e melhora tempo de upload em campo (4G).
 */

/**
 * Comprime um File de imagem retornando um novo Blob redimensionado.
 * @param {File} file - Arquivo de imagem original
 * @param {Object} options
 * @param {number} options.maxWidth - Largura máxima (default: 1200px)
 * @param {number} options.maxHeight - Altura máxima (default: 1200px)
 * @param {number} options.quality - Qualidade JPEG 0-1 (default: 0.7)
 * @returns {Promise<{blob: Blob, dataUrl: string, originalSize: number, compressedSize: number}>}
 */
export async function compressImage(file, options = {}) {
  const { maxWidth = 1200, maxHeight = 1200, quality = 0.7 } = options

  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        // Calcula dimensões mantendo aspect ratio
        let { width, height } = img
        if (width > maxWidth || height > maxHeight) {
          const ratio = Math.min(maxWidth / width, maxHeight / height)
          width = Math.round(width * ratio)
          height = Math.round(height * ratio)
        }

        // Renderiza no Canvas
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        ctx.drawImage(img, 0, 0, width, height)

        // Converte para Blob JPEG comprimido
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error('Falha na compressão da imagem.'))
              return
            }
            const dataUrl = canvas.toDataURL('image/jpeg', quality)
            resolve({
              blob,
              dataUrl,
              originalSize: file.size,
              compressedSize: blob.size,
              fileName: file.name.replace(/\.[^.]+$/, '.jpg')
            })
          },
          'image/jpeg',
          quality
        )
      }
      img.onerror = () => reject(new Error('Falha ao carregar imagem para compressão.'))
      img.src = e.target.result
    }
    reader.onerror = () => reject(new Error('Falha ao ler arquivo de imagem.'))
    reader.readAsDataURL(file)
  })
}

/**
 * Formata bytes em texto legível
 */
export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
