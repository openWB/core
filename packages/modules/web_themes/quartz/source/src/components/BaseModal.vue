<template>
  <div
    v-if="modelValue"
    class="modal-backdrop"
    @click="close"
  >
    <div
      class="panel modal-panel"
      :style="{ width: `min(${width}px, 100%)` }"
      @click.stop
    >
      <div class="modal-head">
        <h3>{{ title }}</h3>
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

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(10, 12, 16, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 60;
  padding: 20px;
}

.modal-panel {
  max-height: 90vh;
  overflow-y: auto;
  padding: 24px 28px;
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.modal-head h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
}
</style>
