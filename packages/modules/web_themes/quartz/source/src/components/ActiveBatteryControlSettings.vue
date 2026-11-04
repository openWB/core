<template>
  <!-- activation (bat_control_activated) and whether a battery is controllable at all are both
       decided outside Quartz (legacy settings UI / the module's own capability) - this section
       only ever appears once both are already true, nothing to show/explain otherwise -->
  <div
    v-if="activated && controllableIds.length > 0"
    class="mt-3 rounded-lg bg-bg p-3"
  >
    <div class="settings-group-label mb-2">
      Speichersteuerung
    </div>

    <div
      v-for="id in controllableIds"
      :key="id"
      class="mb-2.5 rounded-lg bg-panel px-3 py-2.5 last:mb-0"
    >
      <div class="mb-1 text-[13px] font-bold">
        {{ mqttStore.batteryName(id) }}
      </div>
      <FieldNumber
        label="Maximale Entladeleistung"
        unit="kW"
        :min="0.01"
        :step="0.01"
        :decimals="2"
        :model-value="mqttStore.batteryInstanceMaxDischargePower(id)"
        @update="(v) => mqttStore.setBatteryInstanceMaxDischargePower(id, v)"
      />
      <FieldNumber
        label="Maximale Ladeleistung"
        unit="kW"
        :min="0.01"
        :step="0.01"
        :decimals="2"
        :model-value="mqttStore.batteryInstanceMaxChargePower(id)"
        @update="(v) => mqttStore.setBatteryInstanceMaxChargePower(id, v)"
      />
    </div>

    <FieldSlider
      label="Untere Entladeschranke"
      unit="%"
      :min="5"
      :max="100"
      :model-value="minSoc"
      @update="(v) => mqttStore.setBatteryControlSocRange(v, maxSoc)"
    />
    <FieldSlider
      label="Obere Ladeschranke"
      unit="%"
      :min="5"
      :max="100"
      :model-value="maxSoc"
      @update="(v) => mqttStore.setBatteryControlSocRange(minSoc, v)"
    />

    <BaseSegmentedControl
      label="Regelbedingung"
      :model-value="condition"
      :options="conditionOptions"
      @update="mqttStore.setBatteryPowerLimitCondition($event)"
    />

    <template v-if="condition === 'manual' || condition === 'vehicle_charging'">
      <BaseSegmentedControl
        label="Speichersteuerung"
        :model-value="manualMode"
        :options="manualModeOptions"
        @update="mqttStore.setBatteryManualMode($event)"
      />
      <BaseSegmentedControl
        v-if="manualMode === 'manual_limit'"
        label="Regelmodus"
        :model-value="powerLimitMode"
        :options="powerLimitModeOptions"
        @update="mqttStore.setBatteryPowerLimitMode($event)"
      />
    </template>

    <template v-if="condition === 'price_limit'">
      <div
        v-if="!mqttStore.electricityPriceConfigured"
        class="status-box status-box-warning my-2.5"
      >
        Bitte in den übergreifenden Ladeeinstellungen einen Strompreis-Anbieter konfigurieren.
      </div>
      <div class="toggle-row">
        <label for="price-limit-activated">Preisgrenze für Netzbezug statt Speicherentladung</label>
        <input
          id="price-limit-activated"
          type="checkbox"
          :checked="priceLimitActivated"
          @change="mqttStore.setBatteryPriceLimitActivated(($event.target as HTMLInputElement).checked)"
        >
      </div>
      <FieldNumber
        label="Eigenregelung für Strompreise über"
        unit="ct/kWh"
        :step="0.001"
        :decimals="3"
        :model-value="priceLimit"
        @update="mqttStore.setBatteryPriceLimit"
      />
      <BaseSegmentedControl
        label="Regelmodus für Strompreise zwischen Preisgrenzen"
        :model-value="powerLimitMode"
        :options="powerLimitModeOptions"
        @update="mqttStore.setBatteryPowerLimitMode($event)"
      />
      <div class="toggle-row">
        <label for="price-charge-activated">Preisgrenze für Regelmodus (aktiv laden)</label>
        <input
          id="price-charge-activated"
          type="checkbox"
          :checked="priceChargeActivated"
          @change="mqttStore.setBatteryPriceChargeActivated(($event.target as HTMLInputElement).checked)"
        >
      </div>
      <FieldNumber
        label="Speicher aktiv laden für Strompreise unter"
        unit="ct/kWh"
        :step="0.001"
        :decimals="3"
        :model-value="chargeLimit"
        @update="mqttStore.setBatteryChargeLimit"
      />
    </template>

    <div
      v-if="behaviorDescription.length"
      class="mode-note"
    >
      <p
        v-for="(line, index) in behaviorDescription"
        :key="index"
        :class="index === 0 ? 'mt-0' : 'mt-1'"
      >
        {{ line }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import FieldSlider from './FieldSlider.vue'
import FieldNumber from './FieldNumber.vue'

const mqttStore = useMqttStore()

const activated = computed(() => mqttStore.batteryControlActivated())
const minSoc = computed(() => mqttStore.batteryControlMinSoc())
const maxSoc = computed(() => mqttStore.batteryControlMaxSoc())
const condition = computed(() => mqttStore.batteryPowerLimitCondition())
const manualMode = computed(() => mqttStore.batteryManualMode())
const powerLimitMode = computed(() => mqttStore.batteryPowerLimitMode())
const priceLimitActivated = computed(() => mqttStore.batteryPriceLimitActivated())
const priceLimit = computed(() => mqttStore.batteryPriceLimit())
const priceChargeActivated = computed(() => mqttStore.batteryPriceChargeActivated())
const chargeLimit = computed(() => mqttStore.batteryChargeLimit())

const controllableIds = computed(() =>
  mqttStore.batteryIds.filter((id) => mqttStore.batteryInstancePowerLimitControllable(id) === true),
)

const conditionOptions = [
  { value: 'manual', label: 'Manuell' },
  { value: 'vehicle_charging', label: 'Fahrzeugladung aktiv' },
  { value: 'price_limit', label: 'Preisgrenze' },
] as const

const manualModeOptions = computed(() => [
  { value: 'manual_disable', label: 'Eigenregelung', disabled: condition.value === 'vehicle_charging' },
  { value: 'manual_limit', label: 'Regelmodus anwenden' },
  { value: 'manual_charge', label: 'Speicher aktiv laden', disabled: condition.value === 'vehicle_charging' },
])

const powerLimitModeOptions = [
  { value: 'mode_no_discharge', label: 'volle Entladesperre' },
  { value: 'mode_discharge_home_consumption', label: 'Nur Hausverbrauch entladen' },
  { value: 'mode_charge_pv_production', label: 'PV-Ertrag speichern' },
] as const

// ported from the reference's own batteryBehaviorDescription computed - same condition/manual_mode/
// power_limit_mode -> text-lines mapping, kept terser per Quartz's existing style
const behaviorDescription = computed(() => {
  const lines: string[] = []
  if (condition.value === 'manual') {
    lines.push('Die Konfiguration wird dauerhaft angewendet.')
  }
  if (condition.value === 'vehicle_charging') {
    lines.push('Die Konfiguration wird angewendet, sobald ein Fahrzeug lädt oder ein gesteuerter Verbraucher Leistung bezieht.')
  }
  if (condition.value === 'price_limit') {
    lines.push(`Die Konfiguration wird abhängig vom Strompreis angewendet (zwischen ${chargeLimit.value.toFixed(3)} und ${priceLimit.value.toFixed(3)} ct/kWh).`)
  }
  if (condition.value === 'manual' || condition.value === 'vehicle_charging') {
    if (manualMode.value === 'manual_disable') lines.push('Der Speicher arbeitet in Eigenregelung.')
    if (manualMode.value === 'manual_limit') lines.push('Der konfigurierte Regelmodus wird angewendet.')
    if (manualMode.value === 'manual_charge') lines.push('Der Speicher wird aktiv geladen.')
  }
  if (condition.value === 'price_limit' || manualMode.value === 'manual_limit') {
    if (powerLimitMode.value === 'mode_no_discharge') {
      lines.push('Die Speicherentladung ist vollständig gesperrt. Alle Verbraucher werden durch Netz oder PV versorgt.')
    }
    if (powerLimitMode.value === 'mode_discharge_home_consumption') {
      lines.push('Der Speicher versorgt ausschließlich den Hausverbrauch. Fahrzeugladung erfolgt nicht aus dem Speicher.')
    }
    if (powerLimitMode.value === 'mode_charge_pv_production') {
      lines.push('PV-Ertrag wird vorrangig im Speicher gespeichert. Verbraucher werden bei Bedarf aus dem Netz versorgt.')
    }
  }
  return lines
})
</script>
