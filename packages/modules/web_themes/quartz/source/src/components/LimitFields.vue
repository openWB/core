<template>
  <BaseSegmentedControl
    label="Begrenzung"
    :model-value="limit.selected"
    :options="limitOptions"
    @update="(v) => $emit('set', `${fieldPrefix}.selected`, v)"
  />
  <FieldSlider
    v-if="limit.selected === 'soc'"
    label="Ziel-SoC"
    unit="%"
    :min="0"
    :max="100"
    :model-value="limit.soc"
    @update="(v) => $emit('set', `${fieldPrefix}.soc`, v)"
  />
  <FieldSlider
    v-if="limit.selected === 'amount'"
    label="Energiemenge"
    unit="kWh"
    :min="0"
    :max="100"
    :decimals="1"
    :model-value="limit.amount / 1000"
    @update="(v) => $emit('set', `${fieldPrefix}.amount`, v * 1000)"
  />
</template>

<script setup lang="ts">
import FieldSlider from './FieldSlider.vue'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import type { Limit } from '@/stores/mqtt-store'

defineProps<{ limit: Limit; fieldPrefix: string }>()
defineEmits<{ set: [path: string, value: unknown] }>()

const limitOptions = [
  { value: 'none', label: 'Keine' },
  { value: 'soc', label: 'SoC' },
  { value: 'amount', label: 'Menge' },
]
</script>
