<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-[60] flex items-start justify-center bg-[rgba(10,12,16,0.5)] px-2 pt-[4vh] pb-2 sm:px-5 sm:pt-[8vh] sm:pb-5"
    @pointerdown="pressedOnBackdrop = $event.target === $event.currentTarget"
    @click="onBackdropClick"
  >
    <div
      ref="panel"
      role="dialog"
      aria-modal="true"
      :aria-label="title"
      tabindex="-1"
      class="panel max-h-[94vh] overscroll-contain outline-none overflow-y-auto px-4 py-4 sm:max-h-[90vh] sm:px-7 sm:py-6"
      :style="{ width: `min(${width}px, 100%)` }"
      @click.stop
      @keydown.tab="onTab"
    >
      <div class="mb-3 flex items-center justify-between sm:mb-[18px]">
        <h3 class="m-0 text-[15px] font-bold sm:text-[17px]">
          {{ title }}
        </h3>
        <div class="flex items-center gap-1.5">
          <slot name="header-actions" />
          <BaseIconButton
            aria-label="Schließen"
            title="Schließen"
            @click="close"
          >
            <IconClose />
          </BaseIconButton>
        </div>
      </div>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useEscapeKey } from '@/composables/useEscapeKey'
import BaseIconButton from './BaseIconButton.vue'
import IconClose from './icons/IconClose.vue'
import { FOCUSABLE_SELECTOR, trapTarget } from '@/utils/focusTrap'

const props = withDefaults(defineProps<{ modelValue: boolean; title: string; width?: number }>(), { width: 520 })
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

function close(): void {
  emit('update:modelValue', false)
}

// closes only if the press also started on the backdrop (a slider drag released outside ends in a click there)
const pressedOnBackdrop = ref(false)
function onBackdropClick(event: MouseEvent): void {
  if (event.target === event.currentTarget && pressedOnBackdrop.value) close()
  pressedOnBackdrop.value = false
}

useEscapeKey(() => props.modelValue, close)

function onTab(event: KeyboardEvent): void {
  const container = panel.value
  if (!container) return
  const focusable = [...container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)]
  if (focusable.length === 0) {
    event.preventDefault()
    return
  }
  const target = trapTarget(focusable, document.activeElement, event.shiftKey, container)
  if (target) {
    event.preventDefault()
    target.focus()
  }
}

// focus moves into the dialog and back on close
const panel = ref<HTMLElement | null>(null)
let previouslyFocused: Element | null = null
watch(
  () => props.modelValue,
  async (open) => {
    if (open) {
      previouslyFocused = document.activeElement
      await nextTick()
      panel.value?.focus()
    } else if (previouslyFocused instanceof HTMLElement) {
      previouslyFocused.focus()
      previouslyFocused = null
    }
  },
)
</script>
