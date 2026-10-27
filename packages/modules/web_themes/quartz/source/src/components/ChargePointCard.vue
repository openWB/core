<template>
  <div class="panel px-4 py-3">
    <div class="mb-2.5 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <IconBolt class="text-chargepoint" />
        <span class="text-[14px] font-bold">{{ name }}</span>
      </div>
      <div class="flex items-center gap-1">
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

    <div class="mb-2.5 flex items-center gap-1.5 rounded-lg bg-bg px-2 py-1.5">
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
      <VehicleSocEditor
        v-if="vehicleInfo"
        :vehicle-id="vehicleInfo.id"
        :vehicle-name="vehicleInfo.name"
        :charge-point-id="props.chargePointId"
      />
    </div>

    <BaseTabGroup
      dense
      :model-value="chargeMode"
      :options="modes"
      @update="mqttStore.setChargePointChargeMode(props.chargePointId, $event)"
    />

    <div class="mt-3 flex gap-4 text-[13px]">
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
import { chargeModes as modes } from '@/utils/chargeModes'
import IconBolt from './icons/IconBolt.vue'
import IconCar from './icons/IconCar.vue'
import IconLock from './icons/IconLock.vue'
import IconGear from './icons/IconGear.vue'
import ChargePointSettings from './ChargePointSettings.vue'
import BaseIconButton from './BaseIconButton.vue'
import BaseTabGroup from './BaseTabGroup.vue'
import VehicleSocEditor from './VehicleSocEditor.vue'

const props = defineProps<{ chargePointId: number }>()
const mqttStore = useMqttStore()

const showSettings = ref(false)

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
</script>

<style scoped>
.phase-badge {
  background: color-mix(in srgb, var(--chargepoint) 18%, transparent);
  color: var(--chargepoint);
}
</style>
