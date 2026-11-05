<template>
  <BaseModal
    :model-value="modelValue"
    :title="`Einstellungen · ${name}`"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <p
      v-if="!template"
      class="mode-note"
    >
      Kein Fahrzeug an diesem Ladepunkt verbunden.
    </p>

    <template v-if="template">
      <div class="mb-3.5 rounded-lg bg-bg p-3">
        <BaseTabGroup
          class="justify-center"
          :model-value="mode"
          :options="chargeModes"
          @update="mqttStore.setChargePointChargeMode(props.chargePointId, $event)"
        />
      </div>

      <template v-if="mode === 'instant_charging'">
        <FieldSlider
          label="Stromstärke"
          unit="A"
          :min="6"
          :max="32"
          :model-value="instant.current"
          @update="(v) => setField('chargemode.instant_charging.current', v)"
        />
        <BaseSegmentedControl
          :model-value="instant.phases_to_use"
          :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }]"
          @update="(v) => setField('chargemode.instant_charging.phases_to_use', v)"
        />
        <LimitFields
          :limit="instant.limit"
          field-prefix="chargemode.instant_charging.limit"
          @set="setField"
        />
      </template>

      <template v-else-if="mode === 'pv_charging'">
        <FieldSlider
          label="Minimaler Dauerstrom"
          unit="A"
          :min="0"
          :max="16"
          :discrete-values="MIN_CURRENT_STEPS"
          :off-value="0"
          :model-value="pv.min_current"
          @update="(v) => setField('chargemode.pv_charging.min_current', v)"
        />
        <BaseSegmentedControl
          label="Anzahl Phasen bei Überschuss"
          :model-value="pv.phases_to_use"
          :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }, { value: 0, label: 'Automatik' }]"
          @update="(v) => setField('chargemode.pv_charging.phases_to_use', v)"
        />
        <FieldSlider
          label="Mindest-SoC für das Fahrzeug"
          unit="%"
          :min="0"
          :max="100"
          :model-value="pv.min_soc"
          @update="(v) => setField('chargemode.pv_charging.min_soc', v)"
        />
        <FieldSlider
          label="Mindest-SoC-Strom"
          unit="A"
          :min="6"
          :max="32"
          :model-value="pv.min_soc_current"
          @update="(v) => setField('chargemode.pv_charging.min_soc_current', v)"
        />
        <BaseSegmentedControl
          label="Anzahl Phasen Mindest-SoC"
          :model-value="pv.phases_to_use_min_soc"
          :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }, { value: 0, label: 'Automatik' }]"
          @update="(v) => setField('chargemode.pv_charging.phases_to_use_min_soc', v)"
        />
        <LimitFields
          :limit="pv.limit"
          field-prefix="chargemode.pv_charging.limit"
          @set="setField"
        />
      </template>

      <template v-else-if="mode === 'eco_charging'">
        <FieldSlider
          label="Minimaler Dauerstrom unter der Preisgrenze"
          unit="A"
          :min="6"
          :max="16"
          :model-value="eco.current"
          @update="(v) => setField('chargemode.eco_charging.current', v)"
        />
        <BaseSegmentedControl
          label="Anzahl Phasen bei Überschuss"
          :model-value="eco.phases_to_use"
          :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }, { value: 0, label: 'Automatik' }]"
          @update="(v) => setField('chargemode.eco_charging.phases_to_use', v)"
        />
        <FieldSlider
          label="Preisgrenze"
          unit="ct/kWh"
          :min="0"
          :max="50"
          :step="0.01"
          :decimals="2"
          :model-value="eurPerWhToCtPerKwh(eco.max_price)"
          @update="(v) => setField('chargemode.eco_charging.max_price', ctPerKwhToEurPerWh(v))"
        />
        <ElectricityTariffChart
          :model-value="eurPerWhToCtPerKwh(eco.max_price)"
          @update:model-value="(v) => setField('chargemode.eco_charging.max_price', ctPerKwhToEurPerWh(v))"
        />
        <LimitFields
          :limit="eco.limit"
          field-prefix="chargemode.eco_charging.limit"
          @set="setField"
        />
      </template>

      <template v-else-if="mode === 'stop'">
        <p class="mode-note">
          Für „Stop“ gibt es keine weiteren Einstellungen.
        </p>
      </template>

      <template v-if="mode === 'scheduled_charging'">
        <div class="settings-divider" />
        <ScheduledChargingPlans :charge-point-id="props.chargePointId" />
      </template>

      <template v-if="mode !== 'stop'">
        <div class="settings-divider" />
        <div class="toggle-row">
          <label for="cp-zeitladen">Zeitladen</label>
          <input
            id="cp-zeitladen"
            type="checkbox"
            :checked="template.time_charging.active"
            @change="setField('time_charging.active', ($event.target as HTMLInputElement).checked)"
          >
        </div>
        <TimeChargingPlans
          v-if="template.time_charging.active"
          :charge-point-id="props.chargePointId"
        />
      </template>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore, type Limit } from '@/stores/mqtt-store'
import { eurPerWhToCtPerKwh, ctPerKwhToEurPerWh } from '@/utils/format'
import { chargeModes } from '@/utils/chargeModes'
import BaseModal from './BaseModal.vue'
import FieldSlider from './FieldSlider.vue'
import BaseTabGroup from './BaseTabGroup.vue'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import LimitFields from './LimitFields.vue'
import ScheduledChargingPlans from './ScheduledChargingPlans.vue'
import TimeChargingPlans from './TimeChargingPlans.vue'
import ElectricityTariffChart from './ElectricityTariffChart.vue'

const props = defineProps<{ chargePointId: number; modelValue: boolean }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()

const mqttStore = useMqttStore()

const name = computed(() => mqttStore.chargePointName(props.chargePointId))
const template = computed(() => mqttStore.chargePointChargeTemplate(props.chargePointId))
const mode = computed(() => template.value?.chargemode.selected)

// defaults match control/ev/charge_template.py's own dataclass defaults - only used to narrow
// between "template still loading" and "mode === x", never actually shown unguarded
const DEFAULT_LIMIT: Limit = { selected: 'none', soc: 50, amount: 50000 }

// "Minimaler Dauerstrom" (pv_charging/eco_charging) is "Aus" (0) or 6-16A - no EVSE/vehicle can
// sustain continuous charging below 6A (IEC 61851), same discrete range koala's own slider uses
const MIN_CURRENT_STEPS = [0, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
const instant = computed(
  () => template.value?.chargemode.instant_charging ?? { current: 16, dc_current: 145, phases_to_use: 3, limit: DEFAULT_LIMIT },
)
const pv = computed(
  () =>
    template.value?.chargemode.pv_charging ?? {
      min_current: 0,
      dc_min_current: 145,
      min_soc: 0,
      min_soc_current: 10,
      dc_min_soc_current: 145,
      phases_to_use: 0,
      phases_to_use_min_soc: 3,
      limit: DEFAULT_LIMIT,
    },
)
const eco = computed(
  () =>
    template.value?.chargemode.eco_charging ?? {
      current: 6,
      dc_current: 145,
      max_price: 0.0002,
      phases_to_use: 3,
      limit: DEFAULT_LIMIT,
    },
)

function setField(path: string, value: unknown): void {
  mqttStore.setChargePointChargeTemplateField(props.chargePointId, path, value)
}
</script>
