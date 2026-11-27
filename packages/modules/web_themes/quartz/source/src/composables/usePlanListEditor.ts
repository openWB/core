import { ref, watch, type Ref } from 'vue'

/** Shared by both Zielladen's and Zeitladen's frequency selector - same options, same order in both. */
export const frequencyOptions = [
  { value: 'once', label: 'Einmalig' },
  { value: 'daily', label: 'Täglich' },
  { value: 'weekly', label: 'Wöchentlich' },
] as const

export function frequencyLabel(selected: string): string {
  return frequencyOptions.find((o) => o.value === selected)?.label ?? selected
}

/** Add, edit and delete for the plan lists. A new plan is created by the backend (it numbers ids across all templates): once it shows up in `plans` it is opened for editing, and "Zurück" removes it again by writing the list without it, which every role that may edit the template may do. */
const ADD_TIMEOUT_MS = 10_000

export function usePlanListEditor<T extends { id: number | null }>(
  plans: Ref<T[]>,
  persist: (next: T[]) => void,
  addInBackend: () => void,
) {
  const editing = ref<T | null>(null) as Ref<T | null>
  const editingIndex = ref<number | null>(null)
  const editingIsNew = ref(false)
  const addPending = ref(false)
  let knownIds: number[] = []
  let addTimer: ReturnType<typeof setTimeout> | undefined

  function openEdit(plan: T, index: number): void {
    // a JSON round-trip unwraps the reactive proxy (structuredClone can throw on it)
    editing.value = JSON.parse(JSON.stringify(plan)) as T
    editingIndex.value = index
    editingIsNew.value = false
  }

  function openNew(): void {
    knownIds = plans.value.map((p) => p.id ?? 0)
    addPending.value = true
    clearTimeout(addTimer)
    addTimer = setTimeout(() => {
      addPending.value = false
    }, ADD_TIMEOUT_MS)
    addInBackend()
  }

  watch(plans, (list) => {
    if (!addPending.value) return
    const index = list.findIndex((p) => p.id !== null && !knownIds.includes(p.id))
    if (index === -1) return
    addPending.value = false
    clearTimeout(addTimer)
    openEdit(list[index], index)
    editingIsNew.value = true
  })

  function save(): void {
    if (!editing.value) return
    const savedId = editing.value.id
    persist(plans.value.map((p) => (p.id === savedId ? editing.value! : p)))
    editing.value = null
    editingIsNew.value = false
  }

  function cancel(): void {
    if (editingIsNew.value) remove()
    editing.value = null
    editingIsNew.value = false
  }

  function remove(): void {
    if (!editing.value) return
    const removedId = editing.value.id
    persist(plans.value.filter((p) => p.id !== removedId))
    editing.value = null
    editingIsNew.value = false
  }

  return { editing, editingIndex, addPending, openEdit, openNew, save, cancel, remove }
}
