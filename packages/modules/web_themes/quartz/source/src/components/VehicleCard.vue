<template>
  <div class="panel px-4 py-3">
    <div class="mb-2.5 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <IconCar class="text-car" />
        <span class="text-[14px] font-bold">{{ name }}</span>
      </div>
      <span
        v-if="priority !== undefined"
        class="badge badge-muted"
      >Prio {{ priority }}</span>
    </div>

    <p class="mt-0 mb-2.5 text-xs text-muted">
      {{ info?.manufacturer || 'keine Angabe' }} &middot; {{ info?.model || 'keine Angabe' }}
    </p>

    <p
      v-if="faultState > 0 && faultMessage"
      class="mt-0 mb-2.5 text-xs text-grid"
    >
      {{ faultMessage }}
    </p>

    <div class="flex flex-wrap items-center gap-1.5">
      <span
        v-if="connectionState.length === 0"
        class="badge badge-muted"
      >Nicht zugeordnet</span>
      <span
        v-for="cp in connectionState"
        :key="cp.id"
        :class="['badge', stateBadgeClassFor(cp.charging, cp.plugged)]"
      >{{ cp.name }}</span>
      <span
        v-if="socValue !== undefined"
        class="ml-auto flex items-center gap-1 text-[13px] font-bold"
      >
        <BaseIconButton
          size="sm"
          aria-label="SoC jetzt abrufen"
          :title="socUpdateInProgress ? 'SoC wird abgerufen …' : 'SoC jetzt abrufen'"
          @click="mqttStore.vehicleForceSocUpdate(vehicleId)"
        >
          <IconRefresh :class="{ 'animate-spin': socUpdateInProgress }" />
        </BaseIconButton>
        {{ Math.round(socValue) }}&nbsp;%
        <VehicleSocEditor
          v-if="info"
          :vehicle-id="vehicleId"
          :vehicle-name="name"
        />
      </span>
    </div>

    <div
      v-if="range !== undefined || odometer !== undefined || socTimestamp !== undefined"
      class="mt-2.5 flex flex-wrap gap-4 text-[13px]"
    >
      <StatBlock
        v-if="range !== undefined"
        label="Reichweite"
        :value="`${Math.round(range)} km`"
      />
      <StatBlock
        v-if="odometer !== undefined"
        label="Kilometerstand"
        :value="`${Math.round(odometer)} km`"
      />
      <StatBlock
        v-if="socTimestamp !== undefined"
        label="Letzter Zeitstempel"
        :value="new Date(socTimestamp * 1000).toLocaleString('de-DE')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { stateBadgeClass as stateBadgeClassFor } from '@/utils/badge'
import IconCar from './icons/IconCar.vue'
import IconRefresh from './icons/IconRefresh.vue'
import StatBlock from './StatBlock.vue'
import VehicleSocEditor from './VehicleSocEditor.vue'
import BaseIconButton from './BaseIconButton.vue'

const props = defineProps<{ vehicleId: number }>()
const mqttStore = useMqttStore()

const name = computed(() => mqttStore.vehicleList.find((v) => v.id === props.vehicleId)?.name ?? `Fahrzeug ${props.vehicleId}`)
const info = computed(() => mqttStore.vehicleInfo(props.vehicleId))
const faultState = computed(() => mqttStore.vehicleFaultState(props.vehicleId))
const faultMessage = computed(() => mqttStore.vehicleFaultMessage(props.vehicleId))
const connectionState = computed(() => mqttStore.vehicleConnectionState(props.vehicleId))
const socValue = computed(() => mqttStore.vehicleSocValue(props.vehicleId))
const socUpdateInProgress = computed(() => mqttStore.vehicleSocUpdateInProgress(props.vehicleId))
const range = computed(() => mqttStore.vehicleRange(props.vehicleId))
const odometer = computed(() => mqttStore.vehicleOdometer(props.vehicleId))
const socTimestamp = computed(() => mqttStore.vehicleSocTimestamp(props.vehicleId))
const priority = computed(() => mqttStore.vehiclePriority(props.vehicleId))
</script>
