<template>
  <div class="settings-divider" />
  <div class="settings-group-label">
    Aktive Speichersteuerung
  </div>

  <div class="status-box status-box-warning my-2.5">
    <p class="mt-0">
      Die aktive Speichersteuerung durch openWB basiert auf öffentlich zugänglichen Informationen zu den
      verschiedenen Speichersystemen. Diese können auch nicht vom Hersteller freigegebene Informationen beinhalten.
    </p>
    <p>
      Fragen bezüglich der Gewährleistung und Hardwarekompatibilität sind vor der Nutzung mit dem Hersteller zu
      klären. openWB übernimmt keine Haftung für Schäden, welche aus der Nutzung der "aktiven Speichersteuerung"
      entstehen. Mit der Aktivierung (Schalter unten) bestätigst du, dass du die Hinweise gelesen und verstanden
      hast und die Verantwortung für die Nutzung der aktiven Speichersteuerung übernimmst.
    </p>
  </div>

  <div class="toggle-row">
    <label for="bat-control-activated">Speicher aktiv steuern</label>
    <input
      id="bat-control-activated"
      type="checkbox"
      :checked="activated"
      @change="mqttStore.setBatControlActivated(($event.target as HTMLInputElement).checked)"
    >
  </div>
  <div class="mode-note">
    {{ activated
      ? 'Speicher wird aktiv gesteuert. Grundlage ist die nachfolgende Konfiguration.'
      : 'Speicher wird nicht aktiv gesteuert, sondern regelt eigenständig. Es greifen die Regelparameter der Speicherbeachtung.' }}
  </div>

  <template v-if="activated">
    <div class="settings-group-label mt-3">
      Aktiv steuerbare Speicher
    </div>
    <div
      v-if="hasNonControllableBatteries"
      class="status-box status-box-warning my-2.5"
    >
      Es sind nicht steuerbare Speicher im System vorhanden. Diese führen gewöhnlich eigenständig eine
      Nullpunktausregelung durch und versuchen auch aktiv gesteuerte Speicher auszugleichen.
    </div>

    <div
      v-if="controllableIds.length === 0"
      class="status-box status-box-info my-2.5"
    >
      Die Speicherentladung kann nicht aktiv gesteuert werden, da die Entladeleistung nicht an den/die
      konfigurierten Speicher übergeben werden kann.
    </div>

    <template v-else>
      <div
        v-for="id in controllableIds"
        :key="id"
        class="my-2.5 rounded-lg bg-bg px-3 py-2.5"
      >
        <div class="mb-1 text-[13px] font-bold">
          {{ mqttStore.batteryName(id) }}
        </div>
        <FieldNumber
          label="Maximale Entladeleistung"
          unit="kW"
          :min="0.01"
          :step="0.01"
          :model-value="mqttStore.batteryInstanceMaxDischargePower(id)"
          @update="(v) => mqttStore.setBatteryInstanceMaxDischargePower(id, v)"
        />
        <FieldNumber
          label="Maximale Ladeleistung"
          unit="kW"
          :min="0.01"
          :step="0.01"
          :model-value="mqttStore.batteryInstanceMaxChargePower(id)"
          @update="(v) => mqttStore.setBatteryInstanceMaxChargePower(id, v)"
        />
      </div>

      <div class="settings-divider" />
      <FieldSlider
        label="Untere Entladeschranke"
        unit="%"
        :min="5"
        :max="100"
        :model-value="minSoc"
        @update="(v) => mqttStore.setBatControlSocRange(v, maxSoc)"
      />
      <FieldSlider
        label="Obere Ladeschranke"
        unit="%"
        :min="5"
        :max="100"
        :model-value="maxSoc"
        @update="(v) => mqttStore.setBatControlSocRange(minSoc, v)"
      />

      <BaseSegmentedControl
        label="Regelbedingung"
        :model-value="condition"
        :options="conditionOptions"
        @update="mqttStore.setPowerLimitCondition($event)"
      />

      <div class="settings-divider" />

      <template v-if="condition === 'manual' || condition === 'vehicle_charging'">
        <div class="settings-group-label">
          {{ condition === 'manual' ? 'Manuell' : 'Fahrzeugladung oder Verbraucherbetrieb aktiv' }}
        </div>
        <BaseSegmentedControl
          label="Speichersteuerung"
          :model-value="manualMode"
          :options="manualModeOptions"
          @update="mqttStore.setManualMode($event)"
        />
        <BaseSegmentedControl
          v-if="manualMode === 'manual_limit'"
          label="Regelmodus"
          :model-value="powerLimitMode"
          :options="powerLimitModeOptions"
          @update="mqttStore.setPowerLimitMode($event)"
        />
      </template>

      <template v-if="condition === 'price_limit'">
        <div class="settings-group-label">
          Preisgrenze (Variable Strompreise)
        </div>
        <div
          v-if="!mqttStore.electricityPriceConfigured"
          class="status-box status-box-warning my-2.5"
        >
          Bitte in den übergreifenden Ladeeinstellungen einen Strompreis-Anbieter konfigurieren. Ohne
          Strompreis-Anbieter schaltet der Speicher auf Eigenregelung.
        </div>
        <div class="toggle-row">
          <label for="price-limit-activated">Preisgrenze für Netzbezug statt Speicherentladung</label>
          <input
            id="price-limit-activated"
            type="checkbox"
            :checked="priceLimitActivated"
            @change="mqttStore.setPriceLimitActivated(($event.target as HTMLInputElement).checked)"
          >
        </div>
        <FieldNumber
          label="Eigenregelung für Strompreise über"
          unit="ct/kWh"
          :step="0.001"
          :model-value="priceLimit"
          @update="mqttStore.setPriceLimit"
        />
        <BaseSegmentedControl
          label="Regelmodus für Strompreise zwischen Preisgrenzen"
          :model-value="powerLimitMode"
          :options="powerLimitModeOptions"
          @update="mqttStore.setPowerLimitMode($event)"
        />
        <div class="toggle-row">
          <label for="price-charge-activated">Preisgrenze für Regelmodus (aktiv laden)</label>
          <input
            id="price-charge-activated"
            type="checkbox"
            :checked="priceChargeActivated"
            @change="mqttStore.setPriceChargeActivated(($event.target as HTMLInputElement).checked)"
          >
        </div>
        <FieldNumber
          label="Speicher aktiv laden für Strompreise unter"
          unit="ct/kWh"
          :step="0.001"
          :model-value="chargeLimit"
          @update="mqttStore.setChargeLimit"
        />
      </template>

      <template v-if="behaviorDescription.length">
        <div class="settings-divider" />
        <div class="settings-group-label">
          Beschreibung des Verhaltens
        </div>
        <div class="status-box status-box-info my-2.5">
          <p
            v-for="(line, index) in behaviorDescription"
            :key="index"
            :class="{ 'mt-0': index === 0 }"
          >
            {{ line }}
          </p>
        </div>
      </template>
    </template>
  </template>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import BaseSegmentedControl from './BaseSegmentedControl.vue'
import FieldSlider from './FieldSlider.vue'
import FieldNumber from './FieldNumber.vue'

const mqttStore = useMqttStore()

const activated = computed(() => mqttStore.batControlActivated())
const minSoc = computed(() => mqttStore.batControlMinSoc())
const maxSoc = computed(() => mqttStore.batControlMaxSoc())
const condition = computed(() => mqttStore.powerLimitCondition())
const manualMode = computed(() => mqttStore.manualMode())
const powerLimitMode = computed(() => mqttStore.powerLimitMode())
const priceLimitActivated = computed(() => mqttStore.priceLimitActivated())
const priceLimit = computed(() => mqttStore.priceLimit())
const priceChargeActivated = computed(() => mqttStore.priceChargeActivated())
const chargeLimit = computed(() => mqttStore.chargeLimit())

const controllableIds = computed(() =>
  mqttStore.batteryIds.filter((id) => mqttStore.batteryInstancePowerLimitControllable(id) === true),
)
const hasNonControllableBatteries = computed(() =>
  mqttStore.batteryIds.some((id) => mqttStore.batteryInstancePowerLimitControllable(id) === false),
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
