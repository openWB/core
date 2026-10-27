<template>
  <BaseModal
    :model-value="modelValue"
    :title="`Speicher-Beachtung: ${name}`"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <BaseSegmentedControl
      :model-value="mode"
      :options="modeOptions"
      @update="mqttStore.setBatteryMode($event)"
    />
    <FieldSlider
      v-if="mode === 'min_soc_bat_mode'"
      label="Minimaler Speicher-SoC"
      unit="%"
      :min="0"
      :max="100"
      :model-value="socMin"
      @update="(v) => mqttStore.setBatteryPrioritySoc(v, socMax)"
    />
    <FieldSlider
      v-if="mode === 'min_soc_bat_mode'"
      label="Maximaler Speicher-SoC"
      unit="%"
      :min="0"
      :max="100"
      :model-value="socMax"
      @update="(v) => mqttStore.setBatteryPrioritySoc(socMin, v)"
    />

    <template v-if="mode === 'min_soc_bat_mode'">
      <div class="settings-divider" />
      <div class="settings-group-label">
        Speicher-Ladeleistung unterhalb Mindest-SoC
      </div>
      <div class="toggle-row">
        <label for="bat-power-reserve-active">Nur eine bestimmte Ladeleistung reservieren</label>
        <input
          id="bat-power-reserve-active"
          type="checkbox"
          :checked="powerReserveActive"
          @change="mqttStore.setBatteryPowerReserveActive(($event.target as HTMLInputElement).checked)"
        >
      </div>
      <FieldSlider
        v-if="powerReserveActive"
        label="Reservierte Ladeleistung"
        unit="kW"
        :min="0"
        :max="20"
        :step="0.1"
        :decimals="1"
        :model-value="powerReserve"
        @update="mqttStore.setBatteryPowerReserve"
      />

      <div class="settings-divider" />
      <div class="settings-group-label">
        Speicher-SoC oberhalb Maximal-SoC
      </div>
      <div class="toggle-row">
        <label for="bat-power-discharge-active">Entladung des Speichers erlauben</label>
        <input
          id="bat-power-discharge-active"
          type="checkbox"
          :checked="powerDischargeActive"
          @change="mqttStore.setBatteryPowerDischargeActive(($event.target as HTMLInputElement).checked)"
        >
      </div>
      <FieldSlider
        v-if="powerDischargeActive"
        label="Erlaubte Entladeleistung"
        unit="kW"
        :min="0"
        :max="20"
        :step="0.1"
        :decimals="1"
        :model-value="powerDischarge"
        @update="mqttStore.setBatteryPowerDischarge"
      />
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import BaseModal from './BaseModal.vue'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import FieldSlider from './FieldSlider.vue'

defineProps<{ modelValue: boolean; name: string }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()

const mqttStore = useMqttStore()

// 'ev_mode' label matches PR #4197 ("Fahrzeug-Vorrang umbenennen") - this mode already governs
// controlled consumers too, not just vehicles, the old "Fahrzeuge" label undersold that
const modeOptions = [
  { value: 'ev_mode', label: 'Fzg./Verbr.' },
  { value: 'bat_mode', label: 'Speicher' },
  { value: 'min_soc_bat_mode', label: 'Nach SoC des Speichers' },
]

const mode = computed(() => mqttStore.batteryMode())
const socMin = computed(() => mqttStore.batteryPrioritySocMin())
const socMax = computed(() => mqttStore.batteryPrioritySocMax())
const powerReserveActive = computed(() => mqttStore.batteryPowerReserveActive())
const powerReserve = computed(() => mqttStore.batteryPowerReserve())
const powerDischargeActive = computed(() => mqttStore.batteryPowerDischargeActive())
const powerDischarge = computed(() => mqttStore.batteryPowerDischarge())
</script>
