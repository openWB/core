<template>
  <div class="chart-container">
    <LineChart
      :chartData="lineChartData"
      :options="chartOptions"
      :class="'chart'"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useQuasar } from 'quasar';
import { LineChart } from 'vue-chart-3';
import { Chart, registerables } from 'chart.js';
import { useMqttStore } from 'src/stores/mqtt-store';
import 'chartjs-adapter-luxon';
import type { HistoryChartTooltipItem } from './history-chart-model';

Chart.register(...registerables);
const $q = useQuasar();

const props = defineProps<{
  showLegend: boolean;
}>();

const legendDisplay = computed(() => props.showLegend);

const mqttStore = useMqttStore();

const selectedData = computed(() => {
  const data = mqttStore.chartData;
  const currentTime = Math.floor(Date.now() / 1000);
  return data.filter((item) => item.timestamp > currentTime - 3600);
});

const chargePointIds = computed(() => mqttStore.chargePointIds);
const chargePointNames = computed(() => mqttStore.chargePointName);
const vehicles = computed(() => mqttStore.vehicleList());

const chargePointDatasets = computed(() =>
  chargePointIds.value.map((cpId) => ({
    label: `${chargePointNames.value(cpId)}`,
    unit: 'kW',
    borderColor: '#4766b5',
    backgroundColor: 'rgba(71, 102, 181, 0.2)',
    data: selectedData.value.map((item) => item[`cp${cpId}-power`] as number),
    borderWidth: 2,
    pointRadius: 0,
    pointHoverRadius: 4,
    pointHitRadius: 5,
    fill: true,
    yAxisID: 'y',
  })),
);

const vehicleDatasets = computed(() =>
  vehicles.value
    .map((vehicle) => {
      const socKey = `ev${vehicle.id}-soc`;
      if (selectedData.value.some((item) => socKey in item)) {
        return {
          label: `${vehicle.name} SoC`,
          unit: '%',
          borderColor: '#9F8AFF',
          borderWidth: 2,
          borderDash: [10, 5],
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHitRadius: 5,
          data: selectedData.value.map(
            (item) => item[socKey as keyof typeof item] as number,
          ),
          fill: false,
          yAxisID: 'y2',
        };
      }
      return undefined;
    })
    .filter(
      (dataset): dataset is NonNullable<typeof dataset> =>
        dataset !== undefined,
    ),
);

const lineChartData = computed(() => {
  return {
    labels: selectedData.value.map((item) => item.time),
    datasets: [
      {
        label: 'Grid Power',
        unit: 'kW',
        borderColor: '#a33c42',
        backgroundColor: 'rgba(239,182,188, 0.2)',
        data: selectedData.value.map((item) => item.grid),
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHitRadius: 5,
        fill: true,
        yAxisID: 'y',
      },
      {
        label: 'Hausverbrauch',
        unit: 'kW',
        borderColor: '#949aa1',
        backgroundColor: 'rgba(148, 154, 161, 0.2)',
        data: selectedData.value.map((item) => item['house-power'] as number),
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHitRadius: 5,
        fill: true,
        yAxisID: 'y',
      },
      {
        label: 'PV Power',
        unit: 'kW',
        borderColor: 'green',
        backgroundColor: 'rgba(144, 238, 144, 0.2)',
        data: selectedData.value.map((item) => item['pv-all'] as number),
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHitRadius: 5,
        fill: true,
        yAxisID: 'y',
      },
      {
        label: 'Speicher ges.',
        unit: 'kW',
        borderColor: '#b5a647',
        backgroundColor: 'rgba(181, 166, 71, 0.2)',
        data: selectedData.value.map((item) => item['bat-all-power'] as number),
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHitRadius: 5,
        fill: true,
        yAxisID: 'y',
      },
      {
        label: 'Speicher SoC',
        unit: '%',
        borderColor: '#FFB96E',
        borderWidth: 2,
        borderDash: [10, 5],
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHitRadius: 5,
        data: selectedData.value.map((item) => item['bat-all-soc'] as number),
        fill: false,
        yAxisID: 'y2',
      },
      ...chargePointDatasets.value,
      ...vehicleDatasets.value,
    ],
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: legendDisplay.value,
      position: 'bottom',
      fullSize: true,
      labels: {
        boxWidth: 19,
        boxHeight: 0.1,
      },
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      callbacks: {
        label: (item: HistoryChartTooltipItem) =>
          `${item.dataset.label}: ${item.formattedValue} ${item.dataset.unit}`,
      },
    },
  },
  scales: {
    x: {
      type: 'time',
      time: {
        unit: 'minute',
        stepSize: 5,
        displayFormats: {
          minute: 'HH:mm',
        },
      },
      ticks: {
        maxTicksLimit: 12,
        source: 'auto',
      },
      grid: {
        tickLength: 5,
        color: $q.dark.isActive
          ? 'rgba(255, 255, 255, 0.1)'
          : 'rgba(0, 0, 0, 0.1)',
      },
    },
    y: {
      position: 'left',
      type: 'linear',
      display: true,
      title: {
        display: true,
        text: 'Leistung [kW]',
      },
      ticks: {
        stepSize: 0.2,
        maxTicksLimit: 11,
      },
      grid: {
        color: $q.dark.isActive
          ? 'rgba(255, 255, 255, 0.1)'
          : 'rgba(0, 0, 0, 0.1)',
      },
    },
    y2: {
      position: 'right',
      type: 'linear',
      display: true,
      title: {
        display: true,
        text: 'SoC [%]',
      },
      min: 0,
      max: 100,
      ticks: {
        stepSize: 10,
      },
      grid: {
        display: false,
      },
    },
  },
}));
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.chart {
  object-fit: contain;
  height: 100%;
  width: 100%;
}
</style>
