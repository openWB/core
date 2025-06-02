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
      v-if="legendDisplay && legendLarge"
      :chart="chartRef?.chart || null"
      class="legend-wrapper q-mt-sm"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
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
  ChartEvent,
  LegendItem,
  LegendElement,
  ChartTypeRegistry,
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

const legendDisplay = computed(() => props.showLegend);
const mqttStore = useMqttStore();
const localDataStore = useLocalDataStore();
const $q = useQuasar();
const props = defineProps<{
  showLegend: boolean;
}>();

const chartRef = ref<ChartComponentRef | null>(null);

const legendLarge = computed(() =>
  lineChartData?.value?.datasets.length > 15 ? true : false,
);

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
      applyHiddenDatasetsToChart(chart);
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

const chargePointDatasets = computed(() =>
  chargePointIds.value.map((cpId) => ({
    label: `${chargePointNames.value(cpId)}`,
    unit: 'kW',
    borderColor: '#4766b5',
    backgroundColor: 'rgba(71, 102, 181, 0.2)',
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
const lineChartData = computed(() => {
  return {
    datasets: [
      {
        label: gridMeterName.value,
        unit: 'kW',
        borderColor: '#a33c42',
        backgroundColor: 'rgba(239,182,188, 0.2)',
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
      },
      {
        label: 'Hausverbrauch',
        unit: 'kW',
        borderColor: '#949aa1',
        backgroundColor: 'rgba(148, 154, 161, 0.2)',
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
      },
      {
        label: 'PV ges.',
        unit: 'kW',
        borderColor: 'green',
        backgroundColor: 'rgba(144, 238, 144, 0.2)',
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
      },
      {
        label: 'Speicher ges.',
        unit: 'kW',
        borderColor: '#b5a647',
        backgroundColor: 'rgba(181, 166, 71, 0.2)',
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
      display: !legendLarge.value && legendDisplay.value,
      fullSize: true,
      align: 'center' as const,
      position: 'bottom' as const,
      labels: {
        boxWidth: 19,
        boxHeight: 0.1,
      },
      onClick: (
        e: ChartEvent,
        legendItem: LegendItem,
        legend: LegendElement<keyof ChartTypeRegistry>,
      ) => {
        const index = legendItem.datasetIndex!;
        const chartInstance = legend.chart;
        const datasetName = legendItem.text;

        // Toggle visibility using the store
        localDataStore.toggleDataset(datasetName);

        // Update chart visibility
        if (localDataStore.isDatasetHidden(datasetName)) {
          chartInstance.hide(index);
        } else {
          chartInstance.show(index);
        }
      },
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
        maxTicksLimit: 12,
        source: 'auto' as const,
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
</style>
