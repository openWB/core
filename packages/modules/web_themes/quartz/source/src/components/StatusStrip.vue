<template>
  <div style="display: flex; gap: 10px; padding: 16px 0; flex-wrap: wrap">
    <StatChip
      v-for="chip in chips"
      :key="chip.label"
      :icon="chip.icon"
      :label="chip.label"
      :value="chip.value"
      :color="chip.color"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { formatKw, formatCentsPerKwh } from '@/utils/format'
import StatChip from './StatChip.vue'
import IconSun from './icons/IconSun.vue'
import IconBolt from './icons/IconBolt.vue'
import IconBattery from './icons/IconBattery.vue'
import IconHouse from './icons/IconHouse.vue'
import IconConsumer from './icons/IconConsumer.vue'
import IconTag from './icons/IconTag.vue'
import IconCloudSun from './icons/IconCloudSun.vue'

const mqttStore = useMqttStore()

const chips = computed(() => {
  const result = [
    { label: 'Erzeugung', value: formatKw(mqttStore.pvPower), icon: IconSun, color: 'pv' },
    { label: 'Netz', value: formatKw(mqttStore.gridPower), icon: IconBolt, color: 'grid' },
    {
      label: `Speicher · ${mqttStore.batterySoc} %`,
      value: formatKw(mqttStore.batteryPower),
      icon: IconBattery,
      color: 'battery',
    },
    { label: 'Hausverbrauch', value: formatKw(mqttStore.houseConsumption), icon: IconHouse, color: 'consumption' },
    { label: 'Ladepunkte', value: formatKw(mqttStore.chargePointPower), icon: IconBolt, color: 'grid' },
    { label: 'Verbraucher', value: formatKw(mqttStore.consumerPower), icon: IconConsumer, color: 'consumer' },
  ]
  if (mqttStore.electricityPriceConfigured && mqttStore.currentElectricityPrice !== undefined) {
    result.push({
      label: 'Strompreis',
      value: formatCentsPerKwh(mqttStore.currentElectricityPrice),
      icon: IconTag,
      color: 'text',
    })
  }
  if (mqttStore.forecastConfigured && mqttStore.currentForecastPower !== undefined) {
    result.push({
      label: 'Prognose jetzt',
      value: formatKw(mqttStore.currentForecastPower),
      icon: IconCloudSun,
      color: 'pv',
    })
  }
  return result
})
</script>
