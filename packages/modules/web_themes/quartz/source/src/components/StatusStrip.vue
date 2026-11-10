<template>
  <div class="grid grid-cols-3 gap-2 py-4 sm:flex sm:flex-wrap sm:gap-2.5">
    <StatChip
      v-for="chip in chips"
      :key="chip.label"
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
const { counterIds } = useCounters()

const showPriceDetail = ref(false)
const showForecastDetail = ref(false)
const activeDetail = ref<CategoryKey | null>(null)

// Netz/Hausverbrauch have no aggregate fault topic of their own - both reuse the single
// EVU/grid counter's own fault state (the backend's one real "more generators than
// configured" warning is explicitly written onto that same counter object).
const gridCounterFaultState = computed(() => mqttStore.counterInstanceFaultState(mqttStore.gridCounterId() ?? -1))

const counterSumPower = computed(() => counterIds.value.reduce((sum, id) => sum + mqttStore.counterInstancePower(id), 0))
const counterFaultState = computed(() =>
  counterIds.value.reduce((max, id) => Math.max(max, mqttStore.counterInstanceFaultState(id)), 0),
)

const detailInfo = computed<Record<CategoryKey, { title: string; faultState: number }>>(() => ({
  pv: { title: 'Erzeugung', faultState: mqttStore.pvFaultStateTotal() },
  grid: { title: 'Netz', faultState: gridCounterFaultState.value },
  // reine Rechengröße, kein eigenes Modul -> kein Fehlerstatus
  house: { title: 'Hausverbrauch', faultState: 0 },
  battery: { title: 'Speicher', faultState: mqttStore.batteryFaultStateTotal() },
  chargepoint: { title: 'Ladepunkte', faultState: mqttStore.chargePointFaultStateTotal() },
  consumer: { title: 'Verbraucher', faultState: mqttStore.consumerFaultStateTotal() },
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

// grid: positive = Bezug (import, 'in'), negative = Einspeisung (export, 'out') - see
// sonnenbatterie/api.py's "export power must be negative" convention, shared by every counter.
// battery: positive = Laden (charge, 'in'), negative = Entladen (discharge, 'out') - confirmed
// empirically against the live bat-all-power topic (SoC visibly dropping while the value read
// strongly negative for 30s+), NOT from driver-specific code comments - those turned out to
// describe individual inverter drivers (Kostal/Enphase), not this aggregate topic's own
// convention, and were backwards for this installation's actual battery.
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

// chargepoints: positive = Lädt (into the vehicle, 'in'), negative = Entlädt (V2H/bidi discharge
// back into the house, 'out') - same convention as battery, but only meaningful for a bidi-capable
// setup; unverified against real V2H hardware, see plan notes.
const chargePointDirection = computed<'in' | 'out' | undefined>(() => {
  if (mqttStore.chargePointSumPower > 0) return 'in'
  if (mqttStore.chargePointSumPower < 0) return 'out'
  return undefined
})
const chargePointDirectionLabel = computed(() => (chargePointDirection.value === 'in' ? 'Lädt' : 'Entlädt'))

const chips = computed<Chip[]>(() => {
  const result: Chip[] = [
    {
      key: 'pv',
      label: 'Erzeugung',
      value: formatKw(mqttStore.pvPower),
      icon: IconSun,
      color: 'pv',
      faultState: detailInfo.value.pv.faultState,
      clickable: true,
      onClick: () => (activeDetail.value = 'pv'),
    },
    {
      key: 'grid',
      label: 'Netz',
      value: formatKw(mqttStore.gridPower),
      icon: IconBolt,
      color: 'grid',
      faultState: detailInfo.value.grid.faultState,
      clickable: true,
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
  result.push(
    {
      key: 'battery',
      label: `Speicher · ${mqttStore.batterySoc} %`,
      value: formatKw(mqttStore.batteryPower),
      icon: IconBattery,
      color: 'battery',
      faultState: detailInfo.value.battery.faultState,
      clickable: true,
      direction: batteryDirection.value,
      directionLabel: batteryDirectionLabel.value,
      onClick: () => (activeDetail.value = 'battery'),
    },
    {
      key: 'house',
      label: 'Hausverbrauch',
      value: formatKw(mqttStore.houseConsumption),
      icon: IconHouse,
      color: 'consumption',
      clickable: true,
      onClick: () => (activeDetail.value = 'house'),
    },
    {
      key: 'chargepoint',
      label: 'Ladepunkte',
      value: formatKw(mqttStore.chargePointSumPower),
      icon: IconBolt,
      color: 'chargepoint',
      faultState: detailInfo.value.chargepoint.faultState,
      clickable: true,
      direction: chargePointDirection.value,
      directionLabel: chargePointDirectionLabel.value,
      onClick: () => (activeDetail.value = 'chargepoint'),
    },
    {
      key: 'consumer',
      label: 'Verbraucher',
      value: formatKw(mqttStore.consumerPower),
      icon: IconConsumer,
      color: 'consumer',
      faultState: detailInfo.value.consumer.faultState,
      clickable: true,
      onClick: () => (activeDetail.value = 'consumer'),
    },
  )
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
  return result
})
</script>
