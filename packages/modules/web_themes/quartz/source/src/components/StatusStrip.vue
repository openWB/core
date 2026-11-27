<template>
  <div class="grid grid-cols-3 gap-2 py-4 sm:flex sm:flex-wrap sm:gap-2.5">
    <StatChip
      v-for="chip in chips"
      :key="chip.key ?? chip.label"
      :icon="chip.icon"
      :label="chip.label"
      :value="chip.value"
      :color="chip.color"
      :clickable="chip.clickable"
      :fault-state="chip.faultState"
      :direction="chip.direction"
      :direction-label="chip.directionLabel"
      @click="chip.onClick?.()"
    />
  </div>

  <PriceDetailCard v-model="showPriceDetail" />
  <ForecastDetailCard v-model="showForecastDetail" />
  <EntityDetailCard
    v-if="activeDetail"
    :model-value="true"
    :title="detailInfo[activeDetail].title"
    :category-key="activeDetail"
    @update:model-value="activeDetail = null"
  />
</template>

<script setup lang="ts">
import { computed, ref, type Component } from 'vue'
import { useMqttStore } from '@/stores/mqtt-store'
import { useCounters } from '@/composables/useCounters'
import { useConsumers } from '@/composables/useConsumers'
import { formatKw, formatCentsPerKwh } from '@/utils/format'
import type { CategoryKey } from '@/types/chart'
import StatChip from './StatChip.vue'
import PriceDetailCard from './PriceDetailCard.vue'
import ForecastDetailCard from './ForecastDetailCard.vue'
import EntityDetailCard from './EntityDetailCard.vue'
import IconSun from './icons/IconSun.vue'
import IconBolt from './icons/IconBolt.vue'
import IconBattery from './icons/IconBattery.vue'
import IconHouse from './icons/IconHouse.vue'
import IconConsumer from './icons/IconConsumer.vue'
import IconCounter from './icons/IconCounter.vue'
import IconTag from './icons/IconTag.vue'
import IconCloudSun from './icons/IconCloudSun.vue'

const mqttStore = useMqttStore()
const { counterIds, homeConsumptionCounterIds, counterPower: counterSumPower } = useCounters()
const { visibleConsumerIds, visibleConsumerPower, homeConsumptionConsumerIds } = useConsumers()

const showPriceDetail = ref(false)
const showForecastDetail = ref(false)
const activeDetail = ref<CategoryKey | null>(null)

// Netz and Hausverbrauch have no fault topic of their own; the backend's generator warning sits on the grid counter
const gridCounterFaultState = computed(() => mqttStore.counterInstanceFaultState(mqttStore.gridCounterId() ?? -1))

const counterFaultState = computed(() =>
  counterIds.value.reduce((max, id) => Math.max(max, mqttStore.counterInstanceFaultState(id)), 0),
)

const consumerFaultState = computed(() =>
  visibleConsumerIds.value.reduce((max, id) => Math.max(max, mqttStore.consumerInstanceFaultState(id)), 0),
)
const houseFaultState = computed(() =>
  Math.max(
    homeConsumptionConsumerIds.value.reduce((max, id) => Math.max(max, mqttStore.consumerInstanceFaultState(id)), 0),
    homeConsumptionCounterIds.value.reduce((max, id) => Math.max(max, mqttStore.counterInstanceFaultState(id)), 0),
  ),
)
const detailInfo = computed<Record<CategoryKey, { title: string; faultState: number }>>(() => ({
  pv: { title: 'Erzeugung', faultState: mqttStore.pvFaultStateTotal() },
  grid: { title: 'Netz', faultState: gridCounterFaultState.value },
  house: { title: 'Hausverbrauch', faultState: houseFaultState.value },
  battery: { title: 'Speicher', faultState: mqttStore.batteryFaultStateTotal() },
  chargepoint: { title: 'Ladepunkte', faultState: mqttStore.chargePointFaultStateTotal() },
  consumer: { title: 'Verbraucher', faultState: consumerFaultState.value },
  counter: { title: 'Zähler', faultState: counterFaultState.value },
}))

interface Chip {
  key?: CategoryKey
  label: string
  value: string
  icon: Component
  color: string
  faultState?: number
  clickable?: boolean
  onClick?: () => void
  direction?: 'in' | 'out'
  directionLabel?: string
}

// positive = Bezug / Laden, negative = Einspeisung / Entladen (battery checked against the live bat-all-power topic)
const gridDirection = computed<'in' | 'out' | undefined>(() => {
  if (mqttStore.gridPower > 0) return 'in'
  if (mqttStore.gridPower < 0) return 'out'
  return undefined
})
const gridDirectionLabel = computed(() => (gridDirection.value === 'in' ? 'Bezug' : 'Einspeisung'))
const batteryDirection = computed<'in' | 'out' | undefined>(() => {
  if (mqttStore.batteryPower > 0) return 'in'
  if (mqttStore.batteryPower < 0) return 'out'
  return undefined
})
const batteryDirectionLabel = computed(() => (batteryDirection.value === 'in' ? 'Lädt' : 'Entlädt'))

// same convention as the battery; unverified with real V2H hardware
const chargePointDirection = computed<'in' | 'out' | undefined>(() => {
  if (mqttStore.chargePointSumPower > 0) return 'in'
  if (mqttStore.chargePointSumPower < 0) return 'out'
  return undefined
})
const chargePointDirectionLabel = computed(() => (chargePointDirection.value === 'in' ? 'Lädt' : 'Entlädt'))

// "–" instead of 0 W while the live feed is not there (still loading, or the user's role does not allow it)
const power = (kw: number): string => (mqttStore.liveValuesReceived ? formatKw(kw) : '–')

const chips = computed<Chip[]>(() => {
  const result: Chip[] = [
    {
      key: 'pv',
      label: 'Erzeugung',
      value: power(mqttStore.pvPower),
      icon: IconSun,
      color: 'pv',
      faultState: detailInfo.value.pv.faultState,
      // the details are only offered when the user may see an inverter (else the popup would be empty)
      clickable: mqttStore.inverterIds.length > 0,
      onClick: () => (activeDetail.value = 'pv'),
    },
    {
      key: 'grid',
      label: 'Netz',
      value: power(mqttStore.gridPower),
      icon: IconBolt,
      color: 'grid',
      faultState: detailInfo.value.grid.faultState,
      clickable: mqttStore.gridCounterAccessible(),
      direction: gridDirection.value,
      directionLabel: gridDirectionLabel.value,
      onClick: () => (activeDetail.value = 'grid'),
    },
  ]
  if (counterIds.value.length > 0) {
    result.push({
      key: 'counter',
      label: 'Zähler',
      value: formatKw(counterSumPower.value),
      icon: IconCounter,
      color: 'grid',
      faultState: detailInfo.value.counter.faultState,
      clickable: true,
      onClick: () => (activeDetail.value = 'counter'),
    })
  }
  // without a battery there is nothing to show (the live feed leaves its battery fields out, too)
  if (mqttStore.batteryConfigured) {
    result.push({
      key: 'battery',
      label: mqttStore.liveValuesReceived ? `Speicher ${mqttStore.batterySoc}%` : 'Speicher',
      value: power(mqttStore.batteryPower),
      icon: IconBattery,
      color: 'battery',
      faultState: detailInfo.value.battery.faultState,
      clickable: mqttStore.batteryIds.length > 0,
      direction: batteryDirection.value,
      directionLabel: batteryDirectionLabel.value,
      onClick: () => (activeDetail.value = 'battery'),
    })
  }
  result.push(
    {
      key: 'house',
      label: 'Hausverbrauch',
      value: power(mqttStore.houseConsumption),
      icon: IconHouse,
      color: 'consumption',
      clickable: true,
      onClick: () => (activeDetail.value = 'house'),
    },
    {
      key: 'chargepoint',
      label: 'Ladepunkte',
      value: power(mqttStore.chargePointSumPower),
      icon: IconBolt,
      color: 'chargepoint',
      faultState: detailInfo.value.chargepoint.faultState,
      clickable: true,
      direction: chargePointDirection.value,
      directionLabel: chargePointDirectionLabel.value,
      onClick: () => (activeDetail.value = 'chargepoint'),
    }
  )
  if (visibleConsumerIds.value.length > 0) {
    result.push({
      key: 'consumer',
      label: 'Verbraucher',
      value: formatKw(visibleConsumerPower.value),
      icon: IconConsumer,
      color: 'consumer',
      faultState: detailInfo.value.consumer.faultState,
      clickable: true,
      onClick: () => (activeDetail.value = 'consumer'),
    })
  }
  if (mqttStore.electricityPriceConfigured && mqttStore.currentElectricityPrice !== undefined) {
    result.push({
      label: 'Strompreis',
      value: formatCentsPerKwh(mqttStore.currentElectricityPrice),
      icon: IconTag,
      color: 'text',
      faultState: Math.max(mqttStore.flexibleTariffFaultState(), mqttStore.gridFeeFaultState()),
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
      faultState: mqttStore.forecastFaultState(),
      clickable: true,
      onClick: () => (showForecastDetail.value = true),
    })
  }
  // nothing for what the installation does not have
  const missing = new Set<CategoryKey>()
  if (!mqttStore.pvConfigured) missing.add('pv')
  if (mqttStore.gridCounterId() === undefined) missing.add('grid')
  if (mqttStore.chargePointIds.length === 0) missing.add('chargepoint')
  return result.filter((chip) => !(chip.key && missing.has(chip.key)))
})
</script>
