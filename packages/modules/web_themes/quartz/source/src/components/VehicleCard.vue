<template>
  <div class="panel px-4 py-3">
    <div class="mb-2.5 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <IconCar class="text-car" />
        <span class="text-[14px] font-bold">{{ name }}</span>
      </div>
      <VehicleSocEditor
        v-if="info"
        :vehicle-id="vehicleId"
        :vehicle-name="name"
      />
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
        v-if="priority !== undefined"
        class="whitespace-nowrap rounded-full px-[9px] py-[3px] text-[11px] font-bold badge-muted"
      >Prio {{ priority }}</span>
      <span
        v-if="connectionState.length === 0"
        class="whitespace-nowrap rounded-full px-[9px] py-[3px] text-[11px] font-bold badge-muted"
      >Nicht zugeordnet</span>
      <span
        v-for="cp in connectionState"
        :key="cp.id"
        :class="['whitespace-nowrap rounded-full px-[9px] py-[3px] text-[11px] font-bold', cp.charging ? 'badge-ok' : cp.plugged ? 'badge-wait' : 'badge-muted']"
      >{{ cp.name }}</span>
      <span
        v-if="socValue !== undefined"
        class="ml-auto text-[13px] font-bold"
      >{{ Math.round(socValue) }}&nbsp;%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import IconCar from './icons/IconCar.vue'
import VehicleSocEditor from './VehicleSocEditor.vue'

const props = defineProps<{ vehicleId: number }>()
const mqttStore = useMqttStore()

const name = computed(() => mqttStore.vehicleList.find((v) => v.id === props.vehicleId)?.name ?? `Fahrzeug ${props.vehicleId}`)
const info = computed(() => mqttStore.vehicleInfo(props.vehicleId))
const faultState = computed(() => mqttStore.vehicleFaultState(props.vehicleId))
const faultMessage = computed(() => mqttStore.vehicleFaultMessage(props.vehicleId))
const connectionState = computed(() => mqttStore.vehicleConnectionState(props.vehicleId))
const socValue = computed(() => mqttStore.vehicleSocValue(props.vehicleId))
const priority = computed(() => mqttStore.vehiclePriority(props.vehicleId))
</script>
