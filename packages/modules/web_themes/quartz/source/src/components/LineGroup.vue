<template>
  <div class="border-t border-border py-1.5 first-of-type:border-t-0">
    <div class="flex items-center gap-[7px] text-[13px]">
      <span
        class="legend-dot"
        :style="{ background: color }"
      />
      {{ label }}
    </div>

    <div
      v-if="mode !== undefined"
      class="mt-1.5 mb-1"
    >
      <BaseTabGroup
        dense
        :model-value="mode"
        :options="categoryModeOptions"
        @update="$emit('update:mode', $event)"
      />
    </div>

    <div
      v-if="mode === undefined || mode === 'individual'"
      :class="mode === undefined ? 'mt-1.5 flex flex-col gap-1' : 'flex flex-col gap-1'"
    >
      <InstanceCheckboxList
        :items="items"
        :color="color"
        :is-visible="isVisible"
        :set-visible="setVisible"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { categoryModeOptions } from '@/composables/useChartSettings'
import BaseTabGroup from './BaseTabGroup.vue'
import InstanceCheckboxList from './InstanceCheckboxList.vue'

defineProps<{
  label: string
  color: string
  /** Omit entirely to always show the item list with no Gesamt/Einzeln switcher (e.g. Fahrzeug-SoC,
   *  which has no "combined" concept at all). */
  mode?: 'combined' | 'individual'
  items: { id: string; label: string }[]
  isVisible: (id: string) => boolean
  setVisible: (id: string, visible: boolean) => void
}>()
defineEmits<{ 'update:mode': [value: 'combined' | 'individual'] }>()
</script>
