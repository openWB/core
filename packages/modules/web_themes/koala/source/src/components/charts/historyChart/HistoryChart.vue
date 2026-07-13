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
import type { ChartOptions, Point } from 'chart.js';
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
  const gridId = mqttStore.gridId;
  if (gridId !== undefined) {
    return mqttStore.componentName(gridId);
  }
  return 'Zähler';
});

//used to recreate chart instance once grid meter name is received from MQTT topic.
const chartInstanceKey = computed(() => gridMeterName.value);

const vehicles = computed(() => mqttStore.vehicleList);
const chartRange = computed(
  () => mqttStore.themeConfiguration?.history_chart_range || 3600,
);

const getGlobalColor = (name: string, fallback: string = '#888888') => {
  const fromRoot = getComputedStyle(document.body)
    .getPropertyValue(name)
    .trim();
  return fromRoot || fallback;
};

const hexColorToRgba = (hex: string, opacity = 1) => {
  hex = hex.replace('#', '');
  const num = parseInt(hex, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
};

const secondaryCounterDatasets = computed(() =>
  mqttStore.secondaryCounterIds
    .map((id) => {
      const baseColor =
        mqttStore.secondaryCounterColor(id) ||
        getGlobalColor('--q-secondary-counter-stroke');
      return {
        label: mqttStore.componentName(id),
        category: 'component',
        unit: 'kW',
        borderColor: baseColor,
        backgroundColor: hexColorToRgba(baseColor, 0.1),
        data: selectedData.value.map(
          (item) =>
            ({
              x: item.timestamp * 1000,
              y: item[`counter${id}-power` as keyof GraphDataPoint] ?? 0,
            }) as Point,
        ),
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
  chargePointIds.value.map((cpId) => {
    const baseColor =
      mqttStore.chargePointColor(cpId) ||
      getGlobalColor('--q-charge-point-stroke');

    return {
      label: `${chargePointNames.value(cpId)}`,
      category: 'chargepoint',
      unit: 'kW',
      borderColor: baseColor,
      backgroundColor: hexColorToRgba(baseColor, 0.1),
      data: selectedData.value.map(
        (item) =>
          ({
            x: item.timestamp * 1000,
            y: item[`cp${cpId}-power` as keyof GraphDataPoint] || 0,
          }) as Point,
      ),
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHitRadius: 5,
      fill: true,
      yAxisID: 'y',
    };
  }),
);

const consumerDatasets = computed(() => {
  const ids = mqttStore.consumerIds;
  if (ids.length === 0) return [];
  const defaultColor = getGlobalColor('--q-consumer');

  const individualDataset = (id: number) => {
    const baseColor = mqttStore.consumerColor(id) || defaultColor;
    const label = mqttStore.consumerName(id) || `Verbraucher ${id}`;
    return {
      label,
      category: 'consumer',
      unit: 'kW',
      borderColor: baseColor,
      backgroundColor: hexColorToRgba(baseColor, 0.1),
      data: selectedData.value.map(
        (item) =>
          ({
            x: item.timestamp * 1000,
            y: item[`consumer${id}-power` as keyof GraphDataPoint] ?? 0,
          }) as Point,
      ),
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHitRadius: 5,
      fill: true,
      yAxisID: 'y',
    };
  };

  if (ids.length === 1) {
    return [individualDataset(ids[0])];
  }

  return [
    {
      label: 'Verbraucher ges.',
      category: 'consumer',
      unit: 'kW',
      borderColor: defaultColor,
      backgroundColor: hexColorToRgba(defaultColor, 0.1),
      data: selectedData.value.map(
        (item) =>
          ({
            x: item.timestamp * 1000,
            y: item['consumer-all'],
          }) as Point,
      ),
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHitRadius: 5,
      fill: true,
      yAxisID: 'y',
    },
    ...ids.map((id) => ({
      ...individualDataset(id),
      hidden: localDataStore.isDatasetHidden(
        mqttStore.consumerName(id) || `Verbraucher ${id}`,
      ),
    })),
  ];
});

const seededHiddenConsumers = new Set<string>();
watch(
  () =>
    mqttStore.consumerIds.length > 1
      ? mqttStore.consumerIds.map(
          (id) => mqttStore.consumerName(id) || `Verbraucher ${id}`,
        )
      : [],
  (labels) => {
    labels.forEach((label) => {
      if (!seededHiddenConsumers.has(label)) {
        seededHiddenConsumers.add(label);
        localDataStore.hideDataset(label);
      }
    });
  },
  { immediate: true },
);

const vehicleDatasets = computed(() =>
  vehicles.value
    .map((vehicle) => {
      const socKey = `ev${vehicle.id}-soc` as keyof GraphDataPoint;
      if (selectedData.value.some((item) => socKey in item)) {
        const baseColor =
          mqttStore.vehicleColor(vehicle.id) ||
          getGlobalColor('--q-vehicle-stroke');
        return {
          label: `${vehicle.name} SoC`,
          category: 'vehicle',
          unit: '%',
          borderColor: baseColor,
          borderWidth: 2,
          borderDash: [10, 5],
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHitRadius: 5,
          data: selectedData.value.map(
            (item) =>
              ({
                x: item.timestamp * 1000,
                y: Number(item[socKey] ?? 0),
              }) as Point,
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
    const baseColor = getGlobalColor('--q-grid-stroke');
    datasets.push({
      label: gridMeterName.value,
      category: 'component',
      unit: 'kW',
      borderColor: baseColor,
      backgroundColor: hexColorToRgba(baseColor, 0.1),
      data: selectedData.value.map(
        (item) =>
          ({
            x: item.timestamp * 1000,
            y: item.grid,
          }) as Point,
      ),
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHitRadius: 5,
      fill: true,
      yAxisID: 'y',
    });
  }
  if (mqttStore.homePower('value') !== undefined) {
    datasets.push({
      label: 'Hausverbrauch',
      category: 'component',
      unit: 'kW',
      borderColor: getGlobalColor('--q-home-stroke'),
      backgroundColor: getGlobalColor('--q-home-fill'),
      data: selectedData.value.map(
        (item) =>
          ({
            x: item.timestamp * 1000,
            y: item['house-power'],
          }) as Point,
      ),
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHitRadius: 5,
      fill: true,
      yAxisID: 'y',
    });
  }
  datasets.push(...secondaryCounterDatasets.value);
  if (mqttStore.pvConfigured) {
    const baseColor = getGlobalColor('--q-pv-stroke');
    datasets.push({
      label: 'PV ges.',
      category: 'component',
      unit: 'kW',
      borderColor: baseColor,
      backgroundColor: hexColorToRgba(baseColor, 0.1),
      data: selectedData.value.map(
        (item) =>
          ({
            x: item.timestamp * 1000,
            y: item['pv-all'],
          }) as Point,
      ),
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHitRadius: 5,
      fill: true,
      yAxisID: 'y',
    });
  }
  if (mqttStore.batteryConfigured) {
    const baseColor = getGlobalColor('--q-battery-stroke');
    datasets.push(
      {
        label: 'Speicher ges.',
        category: 'component',
        unit: 'kW',
        borderColor: baseColor,
        backgroundColor: hexColorToRgba(baseColor, 0.1),
        data: selectedData.value.map(
          (item) =>
            ({
              x: item.timestamp * 1000,
              y: item['bat-all-power'],
            }) as Point,
        ),
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
        data: selectedData.value.map(
          (item) =>
            ({
              x: item.timestamp * 1000,
              y: item['bat-all-soc'],
            }) as Point,
        ),
        fill: false,
        yAxisID: 'y2',
      },
    );
  }
  datasets.push(...chargePointDatasets.value);
  datasets.push(...vehicleDatasets.value);
  datasets.push(...consumerDatasets.value);
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
  background: var(--q-card-background);
  border-radius: 15px;
  filter: drop-shadow(0 0 0.3rem var(--q-shadow));
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
