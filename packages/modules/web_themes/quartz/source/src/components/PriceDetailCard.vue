<template>
  <BaseModal
    :model-value="modelValue"
    title="Strompreis"
    :width="880"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div
      v-if="flexibleTariffProvider || gridFeeProvider"
      class="info-box"
    >
      <div
        v-if="flexibleTariffProvider"
        class="info-row"
      >
        <span class="info-label">Stromtarif</span>
        <span>{{ flexibleTariffProvider.name }}</span>
      </div>
      <div
        v-if="gridFeeProvider"
        class="info-row"
      >
        <span class="info-label">Netzentgelte</span>
        <span>{{ gridFeeProvider.name }}</span>
      </div>
    </div>

    <div class="my-4 min-h-80">
      <ChartjsLine
        v-if="hasData"
        :data="chartData"
        :options="chartOptions"
      />
      <p
        v-else
        class="mode-note"
      >
        Keine Preisdaten verfügbar.
      </p>
    </div>

    <div
      v-if="statusMessages.length > 0"
      class="status-box"
      :class="{ 'status-box-fault': hasFault }"
    >
      <strong>Modulmeldung</strong>
      <p
        v-for="message in statusMessages"
        :key="message"
      >
        {{ message }}
      </p>
    </div>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Line as ChartjsLine } from 'vue-chartjs'
import { type ChartOptions, type ChartData } from 'chart.js'
import '@/utils/chartSetup'
import { useMqttStore } from '@/stores/mqtt-store'
import { getCssColor, shadeColor } from '@/utils/color'
import { formatTooltipTime, eurPerWhToCtPerKwh } from '@/utils/format'
import BaseModal from './BaseModal.vue'

defineProps<{ modelValue: boolean }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()

const mqttStore = useMqttStore()

const endOfToday = () => new Date().setHours(23, 59, 59, 999)

// each series is forward-filled one extra step (repeating the last value) so a stepped line
// reaches visibly to the end of the day instead of stopping dead at its last real entry
function toStepSeries(prices: Record<string, number>): { x: number; y: number }[] {
  const points = Object.entries(prices)
    .map(([timestamp, price]) => ({ x: Number(timestamp) * 1000, y: eurPerWhToCtPerKwh(price) }))
    .sort((a, b) => a.x - b.x)
  if (points.length === 0) return []
  const last = points[points.length - 1]
  const next = points.length > 1 ? last.x + (last.x - points[points.length - 2].x) - 1 : endOfToday()
  points.push({ x: Math.max(next, last.x), y: last.y })
  return points
}

const totalPoints = computed(() => toStepSeries(mqttStore.electricityPrices))
const tariffPoints = computed(() => toStepSeries(mqttStore.flexibleTariffPrices()))
const gridFeePoints = computed(() => toStepSeries(mqttStore.gridFeePrices()))

const flexibleTariffProvider = computed(() => mqttStore.flexibleTariffProvider())
const gridFeeProvider = computed(() => mqttStore.gridFeeProvider())

const hasData = computed(() => totalPoints.value.length > 0 || tariffPoints.value.length > 0 || gridFeePoints.value.length > 0)

const hasFault = computed(() => mqttStore.flexibleTariffFaultState() > 0 || mqttStore.gridFeeFaultState() > 0)

const statusMessages = computed(() => {
  const messages: string[] = []
  if (flexibleTariffProvider.value) {
    const state = mqttStore.flexibleTariffFaultState()
    messages.push(`Stromtarif: ${state > 0 ? mqttStore.flexibleTariffFaultMessage() : 'Kein Fehler.'}`)
  }
  if (gridFeeProvider.value) {
    const state = mqttStore.gridFeeFaultState()
    messages.push(`Netzentgelt: ${state > 0 ? mqttStore.gridFeeFaultMessage() : 'Kein Fehler.'}`)
  }
  return messages
})

const chartData = computed<ChartData<'line', { x: number; y: number }[]>>(() => {
  const totalColor = getCssColor('--pv')
  const tariffColor = getCssColor('--grid')
  const gridFeeColor = shadeColor(tariffColor, 35)
  const datasets: ChartData<'line', { x: number; y: number }[]>['datasets'] = []
  if (totalPoints.value.length > 0) {
    datasets.push({
      label: 'Gesamtpreis',
      data: totalPoints.value,
      borderColor: totalColor,
      backgroundColor: 'transparent',
      stepped: true,
      pointRadius: 0,
      borderWidth: 2,
    })
  }
  if (tariffPoints.value.length > 0) {
    datasets.push({
      label: 'Stromtarif',
      data: tariffPoints.value,
      borderColor: tariffColor,
      backgroundColor: 'transparent',
      stepped: true,
      pointRadius: 0,
      borderWidth: 1.5,
    })
  }
  if (gridFeePoints.value.length > 0) {
    datasets.push({
      label: 'Netzentgelt',
      data: gridFeePoints.value,
      borderColor: gridFeeColor,
      backgroundColor: 'transparent',
      stepped: true,
      pointRadius: 0,
      borderWidth: 1.5,
    })
  }
  return { datasets }
})

const chartOptions = computed<ChartOptions<'line'>>(() => {
  const mutedColor = getCssColor('--muted')
  const borderColor = getCssColor('--border')
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: { color: mutedColor, boxWidth: 12, font: { size: 11 } },
      },
      tooltip: {
        enabled: true,
        callbacks: {
          title: (items) => {
            const x = items[0]?.parsed.x
            return typeof x === 'number' ? formatTooltipTime(x) : ''
          },
          label: (item) => `${item.dataset.label}: ${(item.parsed.y ?? 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} ct/kWh`,
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        time: { unit: 'hour' },
        grid: { color: borderColor },
        ticks: { color: mutedColor, font: { size: 11 } },
      },
      y: {
        grid: { color: borderColor },
        ticks: { color: mutedColor, font: { size: 12 } },
        title: { display: true, text: 'Preis [ct/kWh]', color: mutedColor, font: { size: 12 } },
      },
    },
  }
})
</script>

