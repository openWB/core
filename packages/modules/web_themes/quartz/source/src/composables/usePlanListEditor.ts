import { ref, type Ref } from 'vue'

/** Shared by both Zielladen's and Zeitladen's frequency selector - same options, same order in both. */
export const frequencyOptions = [
  { value: 'once', label: 'Einmalig' },
  { value: 'daily', label: 'Täglich' },
  { value: 'weekly', label: 'Wöchentlich' },
] as const

export function frequencyLabel(selected: string): string {
  return frequencyOptions.find((o) => o.value === selected)?.label ?? selected
}

/**
 * The add/edit/delete/save-the-whole-array CRUD shape shared by ScheduledChargingPlans.vue
 * (Zielladen) and TimeChargingPlans.vue (Zeitladen) - only what differs per plan type (the plans
 * array itself, how to persist a new array, and a new plan's defaults) is passed in.
 */
export function usePlanListEditor<T extends { id: number | null }>(
  plans: Ref<T[]>,
  persist: (next: T[]) => void,
  createNew: (existingIds: number[]) => T,
) {
  const editing = ref<T | null>(null) as Ref<T | null>
  const editingIndex = ref<number | null>(null)

  function openEdit(plan: T, index: number): void {
    // plan is a Vue-reactive Proxy (sourced from the Pinia store) - structuredClone can throw
    // on that in some engines; a JSON round-trip safely unwraps it into plain, editable data
    editing.value = JSON.parse(JSON.stringify(plan)) as T
    editingIndex.value = index
  }

  function openNew(): void {
    const existingIds = plans.value.map((p) => p.id ?? 0)
    editing.value = createNew(existingIds)
    editingIndex.value = null
  }

  function save(): void {
    if (!editing.value) return
    const next = [...plans.value]
    if (editingIndex.value !== null) next[editingIndex.value] = editing.value
    else next.push(editing.value)
    persist(next)
    editing.value = null
  }

  function remove(): void {
    if (editingIndex.value === null) return
    const next = plans.value.filter((_, i) => i !== editingIndex.value)
    persist(next)
    editing.value = null
  }

  return { editing, editingIndex, openEdit, openNew, save, remove }
}
