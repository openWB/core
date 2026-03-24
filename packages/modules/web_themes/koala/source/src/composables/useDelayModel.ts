import { ref, computed, watch, onBeforeUnmount } from 'vue'

function clone<T>(value: T): T {
  if (typeof value === 'object' && value !== null) {
    return { ...value }
  }
  return value
}

type Comparable = number | Record<string, unknown>
function isEqual<T extends Comparable>(a: T, b: T): boolean {
  if (typeof a === 'object' && a !== null) {
    const objA = a as Record<string, unknown>
    const objB = b as Record<string, unknown>

    return Object.keys(objA).every(
      (key) => objA[key] === objB[key]
    )
  }
  return a === b
}

export function useDelayModel<T>(
  props: { modelValue: T },
  emit: (event: 'update:model-value', value: T) => void,
  delay = 2000
) {
  const tempValue = ref<T>(clone(props.modelValue))

  const updateTimeout = ref<NodeJS.Timeout | null>(null)

  const updatePending = computed(() => {
    return !isEqual(tempValue.value, props.modelValue)
  })

  const delayedValue = computed({
    get: () => tempValue.value,
    set: (newValue: T) => {
      if (updateTimeout.value) {
        clearTimeout(updateTimeout.value)
      }
      tempValue.value = clone(newValue)
    },
  })

  watch(
    delayedValue,
    (newValue) => {
      if (!updatePending.value) return

      if (updateTimeout.value) {
        clearTimeout(updateTimeout.value)
      }

      updateTimeout.value = setTimeout(() => {
        emit('update:model-value', clone(newValue))
      }, delay)
    },
    { deep: true }
  )

  watch(
    () => props.modelValue,
    (newValue) => {
      tempValue.value = clone(newValue)
    }
  )

  onBeforeUnmount(() => {
    if (updateTimeout.value) {
      clearTimeout(updateTimeout.value)
      emit('update:model-value', clone(tempValue.value))
    }
  })

  return {
    delayedValue,
    updatePending,
  }
}
