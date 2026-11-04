<template>
  <BaseModal
    :model-value="modelValue"
    :title="`Einstellungen · ${name}`"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <span class="field-label">Betriebsmodus</span>
    <BaseSegmentedControl
      :model-value="mqttStore.consumerMode(consumerId)"
      :options="chargeModes"
      @update="mqttStore.setConsumerMode(consumerId, $event)"
    />

    <div class="settings-divider" />
    <div class="toggle-row">
      <label for="cu-reset-active">Betriebsmodus automatisch umstellen</label>
      <input
        id="cu-reset-active"
        type="checkbox"
        :checked="resetActive"
        @change="setResetField('active', ($event.target as HTMLInputElement).checked)"
      >
    </div>

    <template v-if="resetActive">
      <label
        class="field-label mt-3"
        for="cu-reset-time"
      >Uhrzeit</label>
      <input
        id="cu-reset-time"
        type="time"
        class="field-select"
        :value="resetTime"
        @change="setResetField('time', ($event.target as HTMLInputElement).value)"
      >

      <BaseSegmentedControl
        label="Wiederholung"
        :model-value="resetFrequencySelected"
        :options="frequencyOptions"
        @update="setResetField('frequency.selected', $event)"
      />
      <WeekdayToggle
        v-if="resetFrequencySelected === 'weekly'"
        :model-value="resetFrequencyWeekly"
        @update="setResetField('frequency.weekly', $event)"
      />
      <input
        v-if="resetFrequencySelected === 'once'"
        type="date"
        class="field-select"
        :value="resetFrequencyOnce"
        @change="setResetField('frequency.once', ($event.target as HTMLInputElement).value)"
      >

      <span class="field-label mt-3">Zielmodus</span>
      <BaseSegmentedControl
        :model-value="resetTargetMode"
        :options="chargeModes"
        @update="setResetField('chargemode', $event)"
      />
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { chargeModes } from '@/utils/chargeModes'
import BaseModal from './BaseModal.vue'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import WeekdayToggle from './WeekdayToggle.vue'

const props = defineProps<{ modelValue: boolean; consumerId: number; name: string }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()

const mqttStore = useMqttStore()

const frequencyOptions = [
  { value: 'daily', label: 'Täglich' },
  { value: 'weekly', label: 'Wöchentlich' },
  { value: 'once', label: 'Einmalig' },
] as const

const resetChargemode = computed(() => mqttStore.consumerUsage(props.consumerId)?.reset_chargemode)
const resetActive = computed(() => resetChargemode.value?.active ?? false)
const resetTime = computed(() => resetChargemode.value?.time ?? '00:00')
const resetTargetMode = computed(() => resetChargemode.value?.chargemode ?? 'scheduled_charging')
const resetFrequencySelected = computed(() => resetChargemode.value?.frequency.selected ?? 'daily')
const resetFrequencyWeekly = computed(() => resetChargemode.value?.frequency.weekly ?? [false, false, false, false, false, false, false])
const resetFrequencyOnce = computed(() => resetChargemode.value?.frequency.once ?? new Date().toISOString().slice(0, 10))

function setResetField(path: string, value: unknown): void {
  mqttStore.setConsumerResetChargemodeField(props.consumerId, path, value)
}
</script>
