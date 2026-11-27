<template>
  <div class="panel px-4 py-3">
    <div class="mb-2.5 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <IconBolt class="text-chargepoint" />
        <span class="text-[14px] font-bold">{{ name }}</span>
      </div>
      <div class="flex items-center gap-1">
        <BaseIconButton
          :tone="locked ? 'error' : 'ok'"
          :aria-label="locked ? 'Ladepunkt entsperren' : 'Ladepunkt sperren'"
          :title="locked ? 'Ladepunkt entsperren' : 'Ladepunkt sperren'"
          @click="locked = !locked"
        >
          <IconLock v-if="locked" />
          <IconLockOpen v-else />
        </BaseIconButton>
        <BaseIconButton
          aria-label="Ladepunkt-Einstellungen öffnen"
          title="Ladepunkt-Einstellungen öffnen"
          @click="showSettings = true"
        >
          <IconGear />
        </BaseIconButton>
        <span :class="['badge', stateBadgeClass]">{{ stateBadgeText }}</span>
      </div>
    </div>

    <ChargePointSettings
      v-model="showSettings"
      :charge-point-id="props.chargePointId"
    />

    <div
      class="status-box mb-2.5 min-h-24 px-3 py-2 text-xs"
      :class="faultState > 0 && faultMessage ? 'status-box-fault' : 'status-box-info'"
    >
      {{ faultState > 0 && faultMessage ? faultMessage : stateMessage || 'Kein Status verfügbar.' }}
    </div>

    <div class="mb-2.5 flex items-center gap-1.5 rounded-lg bg-bg px-2 py-1.5">
      <IconCar class="flex-none text-car" />
      <select
        class="flex-1 border-0 bg-transparent text-[13px] text-text"
        aria-label="Fahrzeug an diesem Ladepunkt"
        :value="vehicleInfo?.id"
        @change="onVehicleChange(($event.target as HTMLSelectElement).value)"
      >
        <option
          v-for="vehicle in vehicleList"
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
      <VehicleSocRefreshButton
        v-if="vehicleInfo"
        :vehicle-id="vehicleInfo.id"
      />
      <VehicleSocEditor
        v-if="vehicleInfo"
        :vehicle-id="vehicleInfo.id"
        :vehicle-name="vehicleInfo.name"
        :charge-point-id="props.chargePointId"
      />
    </div>

    <div class="rounded-lg bg-bg p-3">
      <BaseTabGroup
        dense
        class="justify-center"
        :model-value="chargeMode"
        :options="modes"
        @update="mqttStore.setChargePointChargeMode(props.chargePointId, $event)"
      />
    </div>

    <div class="mt-3 flex flex-wrap items-end gap-x-2 gap-y-2 text-xs">
      <StatBlock
        class="min-w-[4.25rem] flex-none"
        label="Leistung"
      >
        <span class="flex items-center gap-1">
          <IconArrowDown
            v-if="power !== 0"
            class="shrink-0 text-muted"
            :class="{ 'rotate-180': power < 0 }"
            :aria-label="power > 0 ? 'Lädt' : 'Entlädt (V2H)'"
          />
          {{ formatKw(power) }}
        </span>
      </StatBlock>
      <StatBlock
        class="min-w-[2.6rem] flex-none"
        label="Phasen"
        :value="phasesInUse > 0 ? `${phasesInUse}~` : '–'"
      />
      <StatBlock
        class="min-w-[2.6rem] flex-none"
        label="Strom"
        :value="chargingCurrent > 0 ? `${chargingCurrent.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} A` : '–'"
      />
      <StatBlock
        class="min-w-[3.4rem] flex-none"
        label="Geladen"
        :value="formatKwh(energyCharged, 1)"
      />
      <StatBlock
        v-if="soc?.range_charged"
        label="Reichweite"
        :value="`+${Math.round(soc.range_charged)} ${soc.range_unit}`"
      />
      <StatBlock
        v-if="limitLabel"
        label="Ziel"
      >
        <span
          class="flex items-center gap-1"
          title="Ladebegrenzung"
        >
          <IconTarget class="text-muted" />
          {{ limitLabel }}
        </span>
      </StatBlock>
      <span
        v-if="timeChargingActive"
        class="text-accent"
        title="Zeitladen aktiv"
      >
        <IconClock />
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { useVehicles } from '@/composables/useVehicles'
import { formatKw, formatKwh } from '@/utils/format'
import { chargeModes as modes } from '@/utils/chargeModes'
import { stateBadgeClass as stateBadgeClassFor } from '@/utils/badge'
import IconBolt from './icons/IconBolt.vue'
import IconCar from './icons/IconCar.vue'
import IconLock from './icons/IconLock.vue'
import IconLockOpen from './icons/IconLockOpen.vue'
import IconGear from './icons/IconGear.vue'
import IconTarget from './icons/IconTarget.vue'
import IconClock from './icons/IconClock.vue'
import IconArrowDown from './icons/IconArrowDown.vue'
import ChargePointSettings from './ChargePointSettings.vue'
import BaseIconButton from './BaseIconButton.vue'
import BaseTabGroup from './BaseTabGroup.vue'
import VehicleSocEditor from './VehicleSocEditor.vue'
import VehicleSocRefreshButton from './VehicleSocRefreshButton.vue'
import StatBlock from './StatBlock.vue'

const props = defineProps<{ chargePointId: number }>()
const mqttStore = useMqttStore()
const { vehicleList } = useVehicles()

const showSettings = ref(false)

const name = computed(() => mqttStore.chargePointName(props.chargePointId))
const power = computed(() => mqttStore.chargePointPower(props.chargePointId))
const energyCharged = computed(() => mqttStore.chargePointEnergyChargedPlugged(props.chargePointId))
const chargeMode = computed(() => mqttStore.chargePointChargeMode(props.chargePointId))

// only instant, pv and eco have a plain limit (scheduled has one per plan, stop none)
const limitLabel = computed(() => {
  const mode = chargeMode.value
  if (mode !== 'instant_charging' && mode !== 'pv_charging' && mode !== 'eco_charging') return undefined
  const limit = mqttStore.chargePointChargeTemplate(props.chargePointId)?.chargemode[mode].limit
  if (!limit || limit.selected === 'none') return undefined
  return limit.selected === 'soc'
    ? `${limit.soc} %`
    : `${(limit.amount / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })} kWh`
})
const timeChargingActive = computed(() => mqttStore.chargePointChargeTemplate(props.chargePointId)?.time_charging.active ?? false)
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
// measured current (average of the active phases), not the setpoint
const chargingCurrent = computed(() => {
  const active = mqttStore.chargePointInstanceCurrents(props.chargePointId).slice(0, phasesInUse.value)
  return active.length > 0 ? active.reduce((sum, current) => sum + current, 0) / active.length : 0
})
const faultState = computed(() => mqttStore.chargePointFaultState(props.chargePointId))
const faultMessage = computed(() => mqttStore.chargePointFaultMessage(props.chargePointId))

// charging needs real power (charge_state can lag); "locked" only counts once charging has stopped with a vehicle plugged in
const isCharging = computed(() => chargeState.value && power.value > 0)
const isLockedShown = computed(() => locked.value && plugState.value && !isCharging.value)

const stateBadgeText = computed(() => {
  if (isLockedShown.value) return 'Gesperrt'
  if (isCharging.value) return 'Lädt'
  if (plugState.value) return 'Angesteckt'
  return 'Nicht angesteckt'
})
const stateBadgeClass = computed(() => stateBadgeClassFor(isCharging.value, plugState.value, isLockedShown.value))

function onVehicleChange(value: string): void {
  const id = Number(value)
  const vehicle = mqttStore.vehicleList.find((v) => v.id === id)
  if (vehicle) mqttStore.setChargePointConnectedVehicle(props.chargePointId, vehicle.id, vehicle.name)
}
</script>
