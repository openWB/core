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
          v-if="acChargingEnabled"
          label="Stromstärke"
          unit="A"
          :min="6"
          :max="32"
          :model-value="instant.current"
          @update="(v) => setField('chargemode.instant_charging.current', v)"
        />
        <FieldSlider
          v-if="dcChargingEnabled"
          label="DC-Sollleistung"
          unit="kW"
          :min="-dcMaxPower"
          :max="dcMaxPower"
          :model-value="convertDcCurrentToPower(instant.dc_current)"
          @update="(v) => setField('chargemode.instant_charging.dc_current', convertPowerToDcCurrent(v))"
        />
        <BaseSegmentedControl
          v-if="acChargingEnabled"
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
          v-if="acChargingEnabled"
          label="Minimaler Dauerstrom"
          unit="A"
          :min="0"
          :max="16"
          :discrete-values="MIN_CURRENT_STEPS"
          :off-value="0"
          :model-value="pv.min_current"
          @update="(v) => setField('chargemode.pv_charging.min_current', v)"
        />
        <FieldSlider
          v-if="dcChargingEnabled"
          label="Minimaler DC-Dauerleistung"
          unit="kW"
          :min="0"
          :max="300"
          :model-value="convertDcCurrentToPower(pv.dc_min_current)"
          @update="(v) => setField('chargemode.pv_charging.dc_min_current', convertPowerToDcCurrent(v))"
        />
        <BaseSegmentedControl
          v-if="acChargingEnabled"
          label="Anzahl Phasen bei Überschuss"
          :model-value="pv.phases_to_use"
          :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }, { value: 0, label: 'Automatik' }]"
          @update="(v) => setField('chargemode.pv_charging.phases_to_use', v)"
        />
        <template v-if="vehicleSocType !== undefined">
          <FieldSlider
            label="Mindest-SoC für das Fahrzeug"
            unit="%"
            :min="0"
            :max="100"
            :model-value="pv.min_soc"
            @update="(v) => setField('chargemode.pv_charging.min_soc', v)"
          />
          <FieldSlider
            v-if="acChargingEnabled"
            label="Mindest-SoC-Strom"
            unit="A"
            :min="6"
            :max="32"
            :model-value="pv.min_soc_current"
            @update="(v) => setField('chargemode.pv_charging.min_soc_current', v)"
          />
          <FieldSlider
            v-if="dcChargingEnabled"
            label="DC Mindest-SoC-Leistung"
            unit="kW"
            :min="0"
            :max="300"
            :model-value="convertDcCurrentToPower(pv.dc_min_soc_current)"
            @update="(v) => setField('chargemode.pv_charging.dc_min_soc_current', convertPowerToDcCurrent(v))"
          />
          <BaseSegmentedControl
            v-if="acChargingEnabled"
            label="Anzahl Phasen Mindest-SoC"
            :model-value="pv.phases_to_use_min_soc"
            :options="[{ value: 1, label: '1' }, { value: 3, label: 'Maximum' }, { value: 0, label: 'Automatik' }]"
            @update="(v) => setField('chargemode.pv_charging.phases_to_use_min_soc', v)"
          />
        </template>
        <LimitFields
          :limit="pv.limit"
          field-prefix="chargemode.pv_charging.limit"
          @set="setField"
        />
      </template>

      <template v-else-if="mode === 'eco_charging'">
        <FieldSlider
          v-if="acChargingEnabled"
          label="Minimaler Dauerstrom unter der Preisgrenze"
          unit="A"
          :min="6"
          :max="16"
          :model-value="eco.current"
          @update="(v) => setField('chargemode.eco_charging.current', v)"
        />
        <FieldSlider
          v-if="dcChargingEnabled"
          label="Minimale Dauerleistung unter der Preisgrenze"
          unit="kW"
          :min="4"
          :max="300"
          :model-value="convertDcCurrentToPower(eco.dc_current)"
          @update="(v) => setField('chargemode.eco_charging.dc_current', convertPowerToDcCurrent(v))"
        />
        <BaseSegmentedControl
          v-if="acChargingEnabled"
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
          <label>Zeitladen</label>
          <BaseToggle
            :model-value="template.time_charging.active"
            @update:model-value="setField('time_charging.active', $event)"
          />
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
import { eurPerWhToCtPerKwh, ctPerKwhToEurPerWh, convertDcCurrentToPower, convertPowerToDcCurrent } from '@/utils/format'
import { chargeModes } from '@/utils/chargeModes'
import BaseModal from './BaseModal.vue'
import FieldSlider from './FieldSlider.vue'
import BaseTabGroup from './BaseTabGroup.vue'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import LimitFields from './LimitFields.vue'
import ScheduledChargingPlans from './ScheduledChargingPlans.vue'
import TimeChargingPlans from './TimeChargingPlans.vue'
import ElectricityTariffChart from './ElectricityTariffChart.vue'
import BaseToggle from './BaseToggle.vue'

const props = defineProps<{ chargePointId: number; modelValue: boolean }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()

const mqttStore = useMqttStore()

const name = computed(() => mqttStore.chargePointName(props.chargePointId))
const template = computed(() => mqttStore.chargePointChargeTemplate(props.chargePointId))
const mode = computed(() => template.value?.chargemode.selected)

// both false while the chargepoint's own config/template topics are still loading - a brief,
// expected gap, not something to paper over with a fallback
const acChargingEnabled = computed(() => mqttStore.chargePointChargeType(props.chargePointId) === 'AC')
const dcChargingEnabled = computed(() => mqttStore.chargePointChargeType(props.chargePointId) === 'DC')
// corresponds to the backend's dc_max_current default (435 A)
const dcMaxPower = computed(() => mqttStore.chargePointDcMaxPower(props.chargePointId) ?? 300)
// undefined when the connected vehicle can't report its own SoC at all - gates hiding the
// entire Mindest-SoC sub-block (fields are meaningless without it)
const vehicleSocType = computed(() => mqttStore.chargePointConnectedVehicleSocType(props.chargePointId))

// defaults match control/ev/charge_template.py's own dataclass defaults - only used to narrow
// between "template still loading" and "mode === x", never actually shown unguarded
const DEFAULT_LIMIT: Limit = { selected: 'none', soc: 50, amount: 50000 }

// "Minimaler Dauerstrom" (pv_charging/eco_charging) is "Aus" (0) or 6-16A - no EVSE/vehicle can
// sustain continuous charging below 6A (IEC 61851)
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
