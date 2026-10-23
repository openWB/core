<template>
  <div
    class="panel"
    style="padding: 18px 20px"
  >
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px">
      <div style="display: flex; align-items: center; gap: 10px">
        <IconBolt style="color: var(--chargepoint)" />
        <span style="font-weight: 700; font-size: 15px">{{ name }}</span>
      </div>
      <div style="display: flex; align-items: center; gap: 6px">
        <BaseIconButton
          :active="locked"
          :aria-label="locked ? 'Ladepunkt entsperren' : 'Ladepunkt sperren'"
          @click="locked = !locked"
        >
          <IconLock />
        </BaseIconButton>
        <BaseIconButton
          aria-label="Ladepunkt-Einstellungen öffnen"
          @click="showSettings = true"
        >
          <IconGear />
        </BaseIconButton>
        <span :class="['state-badge', stateBadgeClass]">{{ stateBadgeText }}</span>
      </div>
    </div>

    <ChargePointSettings
      v-model="showSettings"
      :charge-point-id="props.chargePointId"
    />

    <p
      v-if="faultState > 0 && faultMessage"
      class="state-message state-message-fault"
    >
      {{ faultMessage }}
    </p>
    <p
      v-else-if="stateMessage"
      class="state-message"
    >
      {{ stateMessage }}
    </p>

    <div class="vehicle-row">
      <IconCar style="color: var(--muted); flex: none" />
      <select
        class="veh-select"
        aria-label="Fahrzeug an diesem Ladepunkt"
        :value="vehicleInfo?.id"
        @change="onVehicleChange(($event.target as HTMLSelectElement).value)"
      >
        <option
          v-for="vehicle in mqttStore.vehicleList"
          :key="vehicle.id"
          :value="vehicle.id"
        >
          {{ vehicle.name }}
        </option>
      </select>
      <span
        v-if="soc?.soc !== undefined"
        style="font-size: 12px; color: var(--muted); white-space: nowrap"
      >{{ Math.round(soc.soc) }}&nbsp;%</span>
      <div
        v-if="vehicleInfo"
        style="position: relative"
      >
        <BaseIconButton
          size="sm"
          aria-label="SoC manuell eingeben"
          @click="openSocEditor"
        >
          <IconPencil />
        </BaseIconButton>
        <div
          v-if="showSocEditor"
          class="soc-editor-backdrop"
          @click="showSocEditor = false"
        />
        <div
          v-if="showSocEditor"
          class="soc-editor panel"
        >
          <div class="settings-group-label">
            SoC {{ vehicleInfo.name }}
          </div>
          <div class="soc-input-row">
            <BaseIconButton
              aria-label="SoC verringern"
              @click="socInputValue = Math.max(0, socInputValue - 1)"
            >
              &minus;
            </BaseIconButton>
            <input
              v-model.number="socInputValue"
              type="number"
              min="0"
              max="100"
              class="soc-input"
            >
            <span>%</span>
            <BaseIconButton
              aria-label="SoC erhöhen"
              @click="socInputValue = Math.min(100, socInputValue + 1)"
            >
              +
            </BaseIconButton>
          </div>
          <input
            v-model.number="socInputValue"
            type="range"
            min="0"
            max="100"
            class="range-slider"
          >
          <BaseButton
            style="width: 100%"
            @click="mqttStore.vehicleForceSocUpdate(vehicleInfo.id)"
          >
            SoC jetzt abrufen
          </BaseButton>
          <div class="soc-editor-actions">
            <BaseButton @click="showSocEditor = false">
              Abbrechen
            </BaseButton>
            <BaseButton
              variant="primary"
              @click="confirmSoc"
            >
              Übernehmen
            </BaseButton>
          </div>
        </div>
      </div>
    </div>

    <BaseTabGroup
      :model-value="chargeMode"
      :options="modes"
      @update="mqttStore.setChargePointChargeMode(props.chargePointId, $event)"
    />

    <div style="display: flex; gap: 24px; font-size: 13px; margin-top: 14px">
      <div>
        <div style="color: var(--muted)">
          Leistung
        </div>
        <div style="font-weight: 700; display: flex; align-items: center; gap: 6px">
          {{ formatKw(power) }}
          <span
            v-if="phasesInUse > 0"
            class="phase-badge"
          >{{ phasesInUse }}~</span>
          <span
            v-if="chargingCurrent > 0"
            style="font-weight: 400; color: var(--muted); font-size: 12px"
          >{{ chargingCurrent.toLocaleString(undefined, { maximumFractionDigits: 1 }) }}&nbsp;A</span>
        </div>
      </div>
      <div>
        <div style="color: var(--muted)">
          Geladen
        </div>
        <div style="font-weight: 700">
          {{ formatKwh(energyCharged) }}
        </div>
      </div>
      <div v-if="soc?.range_charged">
        <div style="color: var(--muted)">
          Reichweite
        </div>
        <div style="font-weight: 700">
          +{{ Math.round(soc.range_charged) }}&nbsp;{{ soc.range_unit }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { formatKw, formatKwh } from '@/utils/format'
import IconBolt from './icons/IconBolt.vue'
import IconCar from './icons/IconCar.vue'
import IconLock from './icons/IconLock.vue'
import IconGear from './icons/IconGear.vue'
import IconPencil from './icons/IconPencil.vue'
import ChargePointSettings from './ChargePointSettings.vue'
import BaseIconButton from './BaseIconButton.vue'
import BaseButton from './BaseButton.vue'
import BaseTabGroup from './BaseTabGroup.vue'

const props = defineProps<{ chargePointId: number }>()
const mqttStore = useMqttStore()

const showSettings = ref(false)

const modes = [
  { value: 'instant_charging', label: 'Sofort' },
  { value: 'pv_charging', label: 'PV-Laden' },
  { value: 'scheduled_charging', label: 'Zielladen' },
  { value: 'eco_charging', label: 'Eco' },
  { value: 'stop', label: 'Stop' },
]

const name = computed(() => mqttStore.chargePointName(props.chargePointId))
const power = computed(() => mqttStore.chargePointPower(props.chargePointId))
const energyCharged = computed(() => mqttStore.chargePointEnergyChargedPlugged(props.chargePointId))
const chargeMode = computed(() => mqttStore.chargePointChargeMode(props.chargePointId))
const vehicleInfo = computed(() => mqttStore.chargePointConnectedVehicleInfo(props.chargePointId))
const soc = computed(() => mqttStore.chargePointConnectedVehicleSoc(props.chargePointId))

const locked = computed({
  get: () => mqttStore.chargePointManualLock(props.chargePointId),
  set: (value: boolean) => mqttStore.setChargePointManualLock(props.chargePointId, value),
})

const plugState = computed(() => mqttStore.chargePointPlugState(props.chargePointId))
const chargeState = computed(() => mqttStore.chargePointChargeState(props.chargePointId))
const stateMessage = computed(() => mqttStore.chargePointStateMessage(props.chargePointId))
const phasesInUse = computed(() => mqttStore.chargePointPhasesInUse(props.chargePointId))
const chargingCurrent = computed(() => mqttStore.chargePointChargingCurrent(props.chargePointId))
const faultState = computed(() => mqttStore.chargePointFaultState(props.chargePointId))
const faultMessage = computed(() => mqttStore.chargePointFaultMessage(props.chargePointId))

const stateBadgeText = computed(() => {
  if (locked.value) return 'Gesperrt'
  if (chargeState.value) return 'Lädt'
  if (plugState.value) return 'Angesteckt'
  return 'Nicht angesteckt'
})
const stateBadgeClass = computed(() => {
  if (locked.value) return 'badge-muted'
  if (chargeState.value) return 'badge-ok'
  if (plugState.value) return 'badge-wait'
  return 'badge-muted'
})

function onVehicleChange(value: string): void {
  const id = Number(value)
  const vehicle = mqttStore.vehicleList.find((v) => v.id === id)
  if (vehicle) mqttStore.setChargePointConnectedVehicle(props.chargePointId, vehicle.id, vehicle.name)
}

const showSocEditor = ref(false)
const socInputValue = ref(0)

function openSocEditor(): void {
  if (!vehicleInfo.value) return
  socInputValue.value = Math.round(mqttStore.vehicleManualSoc(vehicleInfo.value.id))
  showSocEditor.value = true
}

function confirmSoc(): void {
  if (!vehicleInfo.value) return
  mqttStore.setVehicleManualSoc(vehicleInfo.value.id, props.chargePointId, socInputValue.value)
  showSocEditor.value = false
}
</script>

<style scoped>
.vehicle-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--bg);
  border-radius: 8px;
  margin-bottom: 12px;
}

.veh-select {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text);
  font-size: 13px;
}

.state-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 999px;
  white-space: nowrap;
}

.badge-ok {
  background: color-mix(in srgb, var(--pv) 18%, transparent);
  color: var(--pv);
}

.badge-wait {
  background: color-mix(in srgb, var(--chargepoint) 18%, transparent);
  color: var(--chargepoint);
}

.badge-muted {
  background: var(--bg);
  color: var(--muted);
}

.state-message {
  font-size: 12px;
  color: var(--muted);
  margin: 0 0 10px;
}

.state-message-fault {
  color: var(--grid);
}

.phase-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--chargepoint) 18%, transparent);
  color: var(--chargepoint);
}

.soc-editor-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10;
}

.soc-editor {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 11;
  width: 220px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.soc-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.soc-input {
  width: 56px;
  text-align: center;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  padding: 4px;
}

.soc-editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
