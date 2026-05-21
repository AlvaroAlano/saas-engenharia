import { ref } from 'vue'

const isSidebarOpen = ref(false)

export function useSidebar() {
  const toggleSidebar = () => {
    isSidebarOpen.value = !isSidebarOpen.value
  }

  return { isSidebarOpen, toggleSidebar }
}