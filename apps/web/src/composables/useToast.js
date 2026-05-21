import { ref } from 'vue'

const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref('success') // 'success' | 'error' | 'warning' | 'info'

let timeoutId = null
let currentDuration = 3000

export function useToast() {
  const startTimer = () => {
    if (timeoutId) clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      toastVisible.value = false
    }, currentDuration)
  }

  const showToast = (msg, type = 'success', duration = 3000) => {
    toastMessage.value = msg
    toastType.value = type
    toastVisible.value = true
    currentDuration = duration
    
    startTimer()
  }

  const pauseTimer = () => {
    if (timeoutId) clearTimeout(timeoutId)
  }

  const resumeTimer = () => {
    if (toastVisible.value) {
      startTimer()
    }
  }

  return {
    toastVisible,
    toastMessage,
    toastType,
    showToast,
    pauseTimer,
    resumeTimer
  }
}
