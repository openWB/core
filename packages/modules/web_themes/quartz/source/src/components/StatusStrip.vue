<template>
  <div class="flex flex-wrap gap-2.5 py-4">
    <StatChip
      v-for="chip in chips"
      :key="chip.label"
      :icon="chip.icon"
      :label="chip.label"
      :value="chip.value"
      :color="chip.color"
      :clickable="chip.clickable"
      @click="chip.onClick?.()"
    />
  </div>

  <PriceDetailCard v-model="showPriceDetail" />
  <ForecastDetailCard v-model="showForecastDetail" />
</template>

<script setup lang="ts">
import { computed, ref, type Component } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { formatKw, formatCentsPerKwh } from '@/utils/format'
import StatChip from './StatChip.vue'
import PriceDetailCard from './PriceDetailCard.vue'
import ForecastDetailCard from './ForecastDetailCard.vue'
import IconSun from './icons/IconSun.vue'
import IconBolt from './icons/IconBolt.vue'
import IconBattery from './icons/IconBattery.vue'
import IconHouse from './icons/IconHouse.vue'
import IconConsumer from './icons/IconConsumer.vue'
import IconTag from './icons/IconTag.vue'
import IconCloudSun from './icons/IconCloudSun.vue'

const mqttStore = useMqttStore()

const showPriceDetail = ref(false)
const showForecastDetail = ref(false)

interface Chip {
  label: string
  value: string
  icon: Component
  color: string
  clickable?: boolean
  onClick?: () => void
}

const chips = computed<Chip[]>(() => {
  const result: Chip[] = [
    { label: 'Erzeugung', value: formatKw(mqttStore.pvPower), icon: IconSun, color: 'pv' },
    { label: 'Netz', value: formatKw(mqttStore.gridPower), icon: IconBolt, color: 'grid' },
    {
      label: `Speicher · ${mqttStore.batterySoc} %`,
      value: formatKw(mqttStore.batteryPower),
      icon: IconBattery,
      color: 'battery',
    },
    { label: 'Hausverbrauch', value: formatKw(mqttStore.houseConsumption), icon: IconHouse, color: 'consumption' },
    { label: 'Ladepunkte', value: formatKw(mqttStore.chargePointSumPower), icon: IconBolt, color: 'chargepoint' },
    { label: 'Verbraucher', value: formatKw(mqttStore.consumerPower), icon: IconConsumer, color: 'consumer' },
  ]
  if (mqttStore.electricityPriceConfigured && mqttStore.currentElectricityPrice !== undefined) {
    result.push({
      label: 'Strompreis',
      value: formatCentsPerKwh(mqttStore.currentElectricityPrice),
      icon: IconTag,
      color: 'text',
      clickable: true,
      onClick: () => (showPriceDetail.value = true),
    })
  }
  if (mqttStore.forecastConfigured && mqttStore.currentForecastPower !== undefined) {
    result.push({
      label: 'Prognose aktuell',
      value: formatKw(mqttStore.currentForecastPower),
      icon: IconCloudSun,
      color: 'pv',
      clickable: true,
      onClick: () => (showForecastDetail.value = true),
    })
  }
  return result
})
</script>
