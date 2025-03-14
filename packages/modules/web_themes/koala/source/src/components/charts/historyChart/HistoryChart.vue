<template>
  <div class="chart-container">
    <ChartjsLine
      :data="lineChartData"
      :options="chartOptions"
      :class="'chart'"
      ref="chartRef"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue';
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
  ChartTypeRegistry
} from 'chart.js';
import { useMqttStore } from 'src/stores/mqtt-store';
import 'chartjs-adapter-luxon';
import type { HistoryChartTooltipItem } from './history-chart-model';

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

// Define a type for the component that contains the Chart instance
interface ChartComponentRef {
  chart?: Chart;
}

const chartRef = ref<ChartComponentRef | null>(null);
const $q = useQuasar();
const props = defineProps<{
  showLegend: boolean;
}>();

const hiddenDatasets = ref<string[]>([]);

// ******  on mount hook to preserve legend item state (hidden/shown) on card swipe / page reload *****
onMounted(() => {
  const savedHiddenDatasets = localStorage.getItem('historyChartHiddenDatasets');
  if (savedHiddenDatasets) {
    hiddenDatasets.value = JSON.parse(savedHiddenDatasets);
  }

  //delay to ensure the chart is fully rendered
  setTimeout(() => {
    if (chartRef.value?.chart) {
      const chart = chartRef.value.chart;

      if (chart.options.plugins && chart.options.plugins.legend) {
        chart.options.plugins.legend.onClick = function(
          e: ChartEvent,
          legendItem: LegendItem,
          legend: LegendElement<keyof ChartTypeRegistry>
        ) {
          // Get the dataset index
          const index = legendItem.datasetIndex!;
          const chartInstance = legend.chart;

         // Toggle visibility
         if (chartInstance.isDatasetVisible(index)) {
            chartInstance.hide(index);
            hiddenDatasets.value.push(legendItem.text);
          } else {
            chartInstance.show(index);
            hiddenDatasets.value = hiddenDatasets.value.filter(
              item => item !== legendItem.text
            );
          }

          localStorage.setItem(
            'historyChartHiddenDatasets',
            JSON.stringify(hiddenDatasets.value)
          );

          chartInstance.update();
        };
      }

      // Apply initial hidden datasets
      chart.data.datasets.forEach((dataset, index) => {
        if (hiddenDatasets.value.includes(dataset.label as string)) {
          chart.hide(index);
        }
      });
      chart.update();
    }
  }, 100);
});

const legendDisplay = computed(() => props.showLegend);

const mqttStore = useMqttStore();

const selectedData = computed(() => {
  const data = mqttStore.chartData;
  const currentTime = Math.floor(Date.now() / 1000);
  return data.filter((item) => item.timestamp > currentTime - chartRange.value);
});

const chargePointIds = computed(() => mqttStore.chargePointIds);
const chargePointNames = computed(() => mqttStore.chargePointName);

const meterName = computed(() => {
  const gridId = mqttStore.getGridId;
  if (gridId !== undefined) {
    return mqttStore.getCounterName(gridId);
  }
  return 'Zähler';
});

const vehicles = computed(() => mqttStore.vehicleList());
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
      y: item[`cp${cpId}-power`] as number,
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
          data: selectedData.value.map((item) => ({
            x: item.timestamp * 1000,
            y: item[socKey as keyof typeof item] as number,
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
        label: meterName.value,
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
          y: item['house-power'] as number,
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
          y: item['pv-all'] as number,
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
          y: item['bat-all-power'] as number,
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
          y: item['bat-all-soc'] as number,
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
      display: legendDisplay.value,
      fullSize: true,
      align: 'center' as const,
      position: 'bottom' as const,
      labels: {
        boxWidth: 19,
        boxHeight: 0.1,
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

watch(() => lineChartData.value, () => {
    if (chartRef.value?.chart) {
      const chart = chartRef.value.chart;
      chart.data.datasets.forEach((dataset, index) => {
        if (hiddenDatasets.value.includes(dataset.label as string)) {
          chart.hide(index);
        } else {
          chart.show(index);
        }
      });
      chart.update();
    }
}, { deep: true });
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
