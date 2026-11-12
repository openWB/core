<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-[60] flex items-start justify-center bg-[rgba(10,12,16,0.5)] px-2 pt-[4vh] pb-2 sm:px-5 sm:pt-[8vh] sm:pb-5"
    @click="close"
  >
    <div
      class="panel max-h-[94vh] overflow-y-auto px-4 py-4 sm:max-h-[90vh] sm:px-7 sm:py-6"
      :style="{ width: `min(${width}px, 100%)` }"
      @click.stop
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
import BaseIconButton from './BaseIconButton.vue'
import IconClose from './icons/IconClose.vue'

withDefaults(defineProps<{ modelValue: boolean; title: string; width?: number }>(), { width: 520 })
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

function close(): void {
  emit('update:modelValue', false)
}
</script>
