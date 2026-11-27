import { onBeforeUnmount, onMounted } from 'vue'

export function useEscapeKey(isOpen: () => boolean, close: () => void): void {
  function onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape' && isOpen()) close()
  }
  onMounted(() => document.addEventListener('keydown', onKeydown))
  onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
}
