<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-[60] flex items-center justify-center bg-[rgba(10,12,16,0.5)] p-5"
    @click="close"
  >
    <div
      class="panel max-h-[90vh] overflow-y-auto px-7 py-6"
      :style="{ width: `min(${width}px, 100%)` }"
      @click.stop
    >
      <div class="mb-[18px] flex items-center justify-between">
        <h3 class="m-0 text-[17px] font-bold">
          {{ title }}
        </h3>
        <BaseIconButton
          aria-label="Schließen"
          @click="close"
        >
          <IconClose />
        </BaseIconButton>
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
