import { describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import { usePlanListEditor } from './usePlanListEditor'

interface Plan {
  id: number | null
  name: string
}

function setup(initial: Plan[]) {
  const plans = ref<Plan[]>(initial)
  const persist = vi.fn()
  const add = vi.fn()
  return { plans, persist, add, editor: usePlanListEditor<Plan>(plans, persist, add) }
}

describe('usePlanListEditor', () => {
  it('asks the backend for a new plan and opens the one that appears', async () => {
    const { plans, add, editor } = setup([{ id: 3, name: 'a' }])
    editor.openNew()
    expect(add).toHaveBeenCalledOnce()
    expect(editor.addPending.value).toBe(true)
    expect(editor.editing.value).toBeNull()

    plans.value = [
      { id: 3, name: 'a' },
      { id: 9, name: 'neu' },
    ]
    await nextTick()
    expect(editor.editing.value).toEqual({ id: 9, name: 'neu' })
    expect(editor.editingIndex.value).toBe(1)
    expect(editor.addPending.value).toBe(false)
  })

  it('removes a plan that was only created for the edit when going back, by writing the list without it', async () => {
    const { plans, persist, editor } = setup([{ id: 3, name: 'a' }])
    editor.openNew()
    plans.value = [
      { id: 3, name: 'a' },
      { id: 4, name: 'neu' },
    ]
    await nextTick()
    editor.cancel()
    expect(persist).toHaveBeenCalledWith([{ id: 3, name: 'a' }])
    expect(editor.editing.value).toBeNull()
  })

  it('keeps an existing plan when going back', () => {
    const { persist, editor } = setup([{ id: 3, name: 'a' }])
    editor.openEdit({ id: 3, name: 'a' }, 0)
    editor.cancel()
    expect(persist).not.toHaveBeenCalled()
  })

  it('saves the edited plan by id and leaves the others untouched', () => {
    const { persist, editor } = setup([
      { id: 3, name: 'a' },
      { id: 5, name: 'b' },
    ])
    editor.openEdit({ id: 5, name: 'b' }, 1)
    editor.editing.value!.name = 'b2'
    editor.save()
    expect(persist).toHaveBeenCalledWith([
      { id: 3, name: 'a' },
      { id: 5, name: 'b2' },
    ])
  })

  it('does not keep the plan of a stale index when the list changed while editing', () => {
    const { plans, persist, editor } = setup([
      { id: 3, name: 'a' },
      { id: 5, name: 'b' },
    ])
    editor.openEdit({ id: 5, name: 'b' }, 1)
    plans.value = [{ id: 5, name: 'b' }]
    editor.save()
    expect(persist).toHaveBeenCalledWith([{ id: 5, name: 'b' }])
  })

  it('deletes the plan being edited', () => {
    const { persist, editor } = setup([
      { id: 3, name: 'a' },
      { id: 5, name: 'b' },
    ])
    editor.openEdit({ id: 3, name: 'a' }, 0)
    editor.remove()
    expect(persist).toHaveBeenCalledWith([{ id: 5, name: 'b' }])
  })
})
