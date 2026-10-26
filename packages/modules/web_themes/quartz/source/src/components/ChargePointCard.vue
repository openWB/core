<template>
  <div class="panel px-5 py-[18px]">
    <div class="mb-3 flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <IconBolt class="text-chargepoint" />
        <span class="text-[15px] font-bold">{{ name }}</span>
      </div>
      <div class="flex items-center gap-1.5">
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
        <span :class="['whitespace-nowrap rounded-full px-[9px] py-[3px] text-[11px] font-bold', stateBadgeClass]">{{ stateBadgeText }}</span>
      </div>
    </div>

    <ChargePointSettings
      v-model="showSettings"
      :charge-point-id="props.chargePointId"
    />

    <p
      v-if="faultState > 0 && faultMessage"
      class="mt-0 mb-2.5 text-xs text-grid"
    >
      {{ faultMessage }}
    </p>
    <p
      v-else-if="stateMessage"
      class="mt-0 mb-2.5 text-xs text-muted"
    >
      {{ stateMessage }}
    </p>

    <div class="mb-3 flex items-center gap-2 rounded-lg bg-bg px-2.5 py-2">
      <IconCar class="flex-none text-muted" />
      <select
        class="flex-1 border-0 bg-transparent text-[13px] text-text"
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
        class="whitespace-nowrap text-xs text-muted"
      >{{ Math.round(soc.soc) }}&nbsp;%</span>
      <div
        v-if="vehicleInfo"
        class="relative"
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
          class="fixed inset-0 z-10"
          @click="showSocEditor = false"
        />
        <div
          v-if="showSocEditor"
          class="panel absolute top-[calc(100%_+_8px)] right-0 z-[11] flex w-55 flex-col gap-2.5 p-3 shadow-[0_8px_24px_rgba(0,0,0,0.12)]"
        >
          <div class="settings-group-label">
            SoC {{ vehicleInfo.name }}
          </div>
          <div class="flex items-center gap-2 text-[13px]">
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
              class="w-14 rounded-[6px] border border-border bg-bg p-1 text-center text-text"
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
            class="w-full"
            @click="mqttStore.vehicleForceSocUpdate(vehicleInfo.id)"
          >
            SoC jetzt abrufen
          </BaseButton>
          <div class="flex justify-end gap-2">
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

    <div class="mt-3.5 flex gap-6 text-[13px]">
      <div>
        <div class="text-muted">
          Leistung
        </div>
        <div class="flex items-center gap-1.5 font-bold">
          {{ formatKw(power) }}
          <span
            v-if="phasesInUse > 0"
            class="rounded-full px-[7px] py-px text-[11px] font-bold phase-badge"
          >{{ phasesInUse }}~</span>
          <span
            v-if="chargingCurrent > 0"
            class="text-xs font-normal text-muted"
          >{{ chargingCurrent.toLocaleString(undefined, { maximumFractionDigits: 1 }) }}&nbsp;A</span>
        </div>
      </div>
      <div>
        <div class="text-muted">
          Geladen
        </div>
        <div class="font-bold">
          {{ formatKwh(energyCharged) }}
        </div>
      </div>
      <div v-if="soc?.range_charged">
        <div class="text-muted">
          Reichweite
        </div>
        <div class="font-bold">
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

.phase-badge {
  background: color-mix(in srgb, var(--chargepoint) 18%, transparent);
  color: var(--chargepoint);
}
</style>
