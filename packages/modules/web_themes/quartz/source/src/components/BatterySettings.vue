<template>
  <BaseModal
    :model-value="modelValue"
    title="Einstellungen · Speicher"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="rounded-lg bg-bg p-3">
      <div class="settings-group-label mb-2">
        Speicherbeachtung
      </div>
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
          <label>Nur eine bestimmte Ladeleistung reservieren</label>
          <BaseToggle
            :model-value="powerReserveActive"
            @update:model-value="mqttStore.setBatteryPowerReserveActive($event)"
          />
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
          <label>Entladung des Speichers erlauben</label>
          <BaseToggle
            :model-value="powerDischargeActive"
            @update:model-value="mqttStore.setBatteryPowerDischargeActive($event)"
          />
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
    </div>

    <ActiveBatteryControlSettings />
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import BaseModal from './BaseModal.vue'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import FieldSlider from './FieldSlider.vue'
import ActiveBatteryControlSettings from './ActiveBatteryControlSettings.vue'
import BaseToggle from './BaseToggle.vue'

defineProps<{ modelValue: boolean }>()
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
