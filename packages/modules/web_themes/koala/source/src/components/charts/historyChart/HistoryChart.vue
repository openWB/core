<template>
  <div class="chart-container">
    <div class="chart-wrapper">
      <ChartjsLine
        :key="chartInstanceKey"
        :data="lineChartData"
        :options="chartOptions"
        ref="chartRef"
      />
    </div>
    <HistoryChartLegend
      v-if="legendDisplay"
      :chart="chartInstance"
      class="legend-wrapper q-mt-sm"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import type { ChartOptions } from 'chart.js';
import { Line as ChartjsLine } from 'vue-chartjs';
import {
  Chart,
  Legend,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Filler,
  ChartDataset,
  ChartType,
} from 'chart.js';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useLocalDataStore } from 'src/stores/localData-store';
import { GraphDataPoint } from 'src/stores/mqtt-store-model';
import HistoryChartLegend from 'src/components/charts/historyChart/HistoryChartLegend.vue';
import 'chartjs-adapter-luxon';
import type {
  HistoryChartTooltipItem,
  ChartComponentRef,
} from './history-chart-model';

Chart.register(
  Legend,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Filler,
);

const mqttStore = useMqttStore();
const localDataStore = useLocalDataStore();
const $q = useQuasar();
const props = defineProps<{
  showLegend: boolean;
}>();

const chartRef = ref<ChartComponentRef | null>(null);

const chartInstance = computed(() => {
  return (chartRef.value?.chart as Chart) ?? null;
});

const legendDisplay = computed(() => props.showLegend);

const applyHiddenDatasetsToChart = <TType extends ChartType, TData>(
  chart: Chart<TType, TData>,
): void => {
  chart.data.datasets.forEach((dataset: ChartDataset<TType, TData>, index) => {
    if (
      typeof dataset.label === 'string' &&
      localDataStore.isDatasetHidden(dataset.label)
    ) {
      chart.hide(index);
    }
  });
  chart.update();
};

watch(
  () => chartRef.value?.chart,
  (chart) => {
    if (chart) {
      applyHiddenDatasetsToChart(chart as Chart);
    }
  },
  { immediate: true },
);

const selectedData = computed((): GraphDataPoint[] => {
  const data = mqttStore.chartData;
  const currentTime = Math.floor(Date.now() / 1000);
  return data.filter((item) => item.timestamp > currentTime - chartRange.value);
});

const chargePointIds = computed(() => mqttStore.chargePointIds);
const chargePointNames = computed(() => mqttStore.chargePointName);

const gridMeterName = computed(() => {
  const gridId = mqttStore.getGridId;
  if (gridId !== undefined) {
    return mqttStore.getComponentName(gridId);
  }
  return 'Zähler';
});

//used to recreate chart instance once grid meter name is received from MQTT topic.
const chartInstanceKey = computed(() => gridMeterName.value);

const vehicles = computed(() => mqttStore.vehicleList);
const chartRange = computed(
  () => mqttStore.themeConfiguration?.history_chart_range || 3600,
);

const getGlobalColor = (name: string, fallback?: string) => {
  const fromRoot = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return fromRoot || fallback;
};

const secondaryCounterDatasets = computed(() =>
  mqttStore.getSecondaryCounterIds
    .map((id) => {
      return {
        label: mqttStore.getComponentName(id),
        category: 'component',
        unit: 'kW',
        borderColor: getGlobalColor('--q-secondary-counter-stroke'),
        backgroundColor: getGlobalColor('--q-secondary-counter-fill'),
        data: selectedData.value.map((item) => ({
          x: item.timestamp * 1000,
          y: item[`counter${id}-power`] ?? 0,
        })),
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHitRadius: 5,
        fill: true,
        yAxisID: 'y',
      };
    })
    .filter((dataset) => dataset.label !== undefined),
);

const chargePointDatasets = computed(() =>
  chargePointIds.value.map((cpId) => ({
    label: `${chargePointNames.value(cpId)}`,
    category: 'chargepoint',
    unit: 'kW',
    borderColor: getGlobalColor('--q-charge-point-stroke'),
    backgroundColor: getGlobalColor('--q-charge-point-fill'),
    data: selectedData.value.map((item) => ({
      x: item.timestamp * 1000,
      y: item[`cp${cpId}-power`] || 0,
    })),
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
      const socKey = `ev${vehicle.id}-soc` as keyof GraphDataPoint;
      if (selectedData.value.some((item) => socKey in item)) {
        return {
          label: `${vehicle.name} SoC`,
          category: 'vehicle',
          unit: '%',
          borderColor: '#9F8AFF',
          borderWidth: 2,
          borderDash: [10, 5],
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHitRadius: 5,
          data: selectedData.value.map((item) => ({
            x: item.timestamp * 1000,
            y: Number(item[socKey] ?? 0),
          })),
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

const chartLabels = computed(() => {
  const minTimestamp = selectedData.value.length
    ? selectedData.value[0].timestamp
    : Math.floor(Date.now() / 1000) - chartRange.value;
  const maxTimestamp = selectedData.value.length
    ? selectedData.value[selectedData.value.length - 1].timestamp
    : Math.floor(Date.now() / 1000);
  const dataRange = maxTimestamp - minTimestamp;
  let range = 300; // 5 Minuten
  if (dataRange <= 30 * 60) {
    // bis 30 Minuten
    range = 60; // 1 Minute
  } else if (dataRange <= 60 * 60) {
    // bis 60 Minuten
    range = 120; // 2 Minuten
  }

  const calculatedLabels = <number[]>[];
  let first = minTimestamp - (minTimestamp % range);
  if (first < minTimestamp) first += range;
  for (let t = first; t <= maxTimestamp; t += range) {
    calculatedLabels.push(t * 1000);
  }
  return calculatedLabels;
});

const lineChartData = computed(() => {
  let datasets = [];
  if (gridMeterName.value !== undefined) {
    datasets.push({
      label: gridMeterName.value,
      category: 'component',
      unit: 'kW',
      borderColor: getGlobalColor('--q-grid-stroke'),
      backgroundColor: getGlobalColor('--q-grid-fill'),
      data: selectedData.value.map((item) => ({
        x: item.timestamp * 1000,
        y: item.grid,
      })),
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHitRadius: 5,
      fill: true,
      yAxisID: 'y',
    });
  }
  if (mqttStore.getHomePower('value') !== undefined) {
    datasets.push({
      label: 'Hausverbrauch',
      category: 'component',
      unit: 'kW',
      borderColor: getGlobalColor('--q-home-stroke'),
      backgroundColor: getGlobalColor('--q-home-fill'),
      data: selectedData.value.map((item) => ({
        x: item.timestamp * 1000,
        y: item['house-power'],
      })),
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHitRadius: 5,
      fill: true,
      yAxisID: 'y',
    });
  }
  datasets.push(...secondaryCounterDatasets.value);
  if (mqttStore.getPvConfigured) {
    datasets.push({
      label: 'PV ges.',
      category: 'component',
      unit: 'kW',
      borderColor: getGlobalColor('--q-pv-stroke'),
      backgroundColor: getGlobalColor('--q-pv-fill'),
      data: selectedData.value.map((item) => ({
        x: item.timestamp * 1000,
        y: item['pv-all'],
      })),
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHitRadius: 5,
      fill: true,
      yAxisID: 'y',
    });
  }
  if (mqttStore.batteryConfigured) {
    datasets.push(
      {
        label: 'Speicher ges.',
        category: 'component',
        unit: 'kW',
        borderColor: getGlobalColor('--q-battery-stroke'),
        backgroundColor: getGlobalColor('--q-battery-fill'),
        data: selectedData.value.map((item) => ({
          x: item.timestamp * 1000,
          y: item['bat-all-power'],
        })),
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHitRadius: 5,
        fill: true,
        yAxisID: 'y',
      },
      {
        label: 'Speicher SoC',
        category: 'component',
        unit: '%',
        borderColor: '#FFB96E',
        borderWidth: 2,
        borderDash: [10, 5],
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHitRadius: 5,
        data: selectedData.value.map((item) => ({
          x: item.timestamp * 1000,
          y: item['bat-all-soc'],
        })),
        fill: false,
        yAxisID: 'y2',
      },
    );
  }
  datasets.push(...chargePointDatasets.value);
  datasets.push(...vehicleDatasets.value);
  return {
    labels: chartLabels.value,
    datasets: datasets,
  };
});

const chartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      callbacks: {
        label: (item: HistoryChartTooltipItem) =>
          `${item.dataset.label}: ${item.formattedValue} ${item.dataset.unit}`,
      },
    },
  },
  scales: {
    x: {
      type: 'time' as const,
      time: {
        unit: 'minute' as const,
        displayFormats: {
          minute: 'HH:mm' as const,
        },
      },
      ticks: {
        maxTicksLimit: 40,
        source: 'labels' as const,
      },
      grid: {
        tickLength: 5,
        color: $q.dark.isActive
          ? 'rgba(255, 255, 255, 0.1)'
          : 'rgba(0, 0, 0, 0.1)',
      },
    },
    y: {
      position: 'left' as const,
      type: 'linear' as const,
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
      position: 'right' as const,
      type: 'linear' as const,
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
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.legend-wrapper {
  flex: 0 0 auto;
}

.chart-wrapper {
  flex: 1;
  min-height: 0;
}

.chart-wrapper > canvas {
  width: 100% !important;
  height: 100% !important;
}
</style>
