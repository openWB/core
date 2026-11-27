<template>
  <BaseIconButton
    v-if="canRefresh"
    size="sm"
    aria-label="SoC jetzt abrufen"
    :title="inProgress ? 'SoC wird abgerufen …' : 'SoC jetzt abrufen'"
    @click="mqttStore.vehicleForceSocUpdate(vehicleId)"
  >
    <IconRefresh :class="{ 'animate-spin': inProgress }" />
  </BaseIconButton>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import BaseIconButton from './BaseIconButton.vue'
import IconRefresh from './icons/IconRefresh.vue'

const props = defineProps<{ vehicleId: number }>()
const mqttStore = useMqttStore()

// a manual SoC has no source to fetch from - there the pencil is shown instead
const canRefresh = computed(() => {
  const type = mqttStore.vehicleSocType(props.vehicleId)
  return type !== undefined && type !== 'manual'
})
const inProgress = computed(() => mqttStore.vehicleSocUpdateInProgress(props.vehicleId))
</script>
