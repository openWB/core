import { ref } from 'vue'

export interface Toast {
  id: number
  message: string
}

const TOAST_TIMEOUT_MS = 6000

const toasts = ref<Toast[]>([])
let nextId = 1

export function dismissToast(id: number): void {
  toasts.value = toasts.value.filter((toast) => toast.id !== id)
}

/** Shows a short error message; the same text is not stacked while it is still visible. */
export function showErrorToast(message: string): void {
  if (toasts.value.some((toast) => toast.message === message)) return
  const id = nextId++
  toasts.value.push({ id, message })
  setTimeout(() => dismissToast(id), TOAST_TIMEOUT_MS)
}

export function useToasts() {
  return { toasts, dismissToast }
}
