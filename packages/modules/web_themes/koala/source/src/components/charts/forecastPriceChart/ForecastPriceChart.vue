<template>
  <div
    class="chart-container forecast-price-chart"
    :class="{ 'forecast-price-slider': !props.dashboard }"
  >
    <header class="combined-header">
      <h2 class="text-subtitle1 text-weight-bold q-ma-none combined-title">
        <q-icon v-if="forecastConfigured" :name="fasCloudSun" size="sm" />
        <q-icon v-if="pricesConfigured" :name="fasRankingStar" size="sm" />
        {{ title }}
      </h2>
    </header>
    <div class="combined-summary">
      <dl v-if="forecastConfigured">
        <div>
          <dt>PV-Anbieter:</dt>
          <dd>{{ forecastProvider || 'Noch nicht verfügbar' }}</dd>
        </div>
        <div>
          <dt>Aktuell:</dt>
          <dd>{{ format(currentForecast) }} kW</dd>
        </div>
        <div>
          <dt>Heute gesamt:</dt>
          <dd>{{ format(todayEnergy) }} kWh</dd>
        </div>
        <div>
          <dt>Morgen gesamt:</dt>
          <dd>{{ format(tomorrowEnergy) }} kWh</dd>
        </div>
      </dl>
      <dl v-if="pricesConfigured">
        <div v-for="provider in priceProviders" :key="provider.key">
          <dt>{{ provider.label }}:</dt>
          <dd>{{ provider.name || 'Noch nicht verfügbar' }}</dd>
        </div>
        <div>
          <dt>Aktueller Gesamtpreis:</dt>
          <dd>{{ format(price) }} ct/kWh</dd>
        </div>
      </dl>
    </div>
    <div
      ref="plot"
      class="combined-plot"
      @mouseleave="hoveredTime = null"
      @touchend="hoveredTime = null"
    >
      <ChartjsLine
        v-if="hasData && fontsReady"
        :data="chartData"
        :options="chartOptions"
        :plugins="[hoverReadoutPlugin]"
      />
      <div v-else-if="!hasData" class="combined-empty text-grey" role="status">
        {{ emptyMessage }}
      </div>
    </div>
    <div class="combined-messages">
      <div
        v-for="status in statuses"
        :key="status.key"
        class="combined-status"
        role="status"
      >
        <q-icon :name="status.icon" :color="status.color" size="xs" />
        <span>{{ status.label }} – {{ status.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref } from 'vue';
import { useQuasar } from 'quasar';
import { fasCloudSun, fasRankingStar } from '@quasar/extras/fontawesome-v7';
import { Line as ChartjsLine } from 'vue-chartjs';
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import type { ChartData, ChartOptions, Plugin } from 'chart.js';
import 'chartjs-adapter-luxon';
import { useMqttStore } from 'src/stores/mqtt-store';
import { forecastNumber, forecastPoints } from '../forecastChart/forecast-data';
import {
  currentPrice,
  priceIntervalEnd,
  pricePoints,
} from '../electricityPriceChart/price-data';
import {
  timeSeriesAxisFont,
  timeSeriesTooltip,
  wrapTooltipLabel,
} from '../time-series-options';
import { outlookRange } from './common-range';
import { useForecastPriceModules } from './useForecastPriceModules';
import {
  forecastValueAt,
  outlookTimeline,
  forecastOnTimeline,
  pricesOnTimeline,
} from './outlook-series';

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Legend,
  Filler,
);

const props = defineProps<{ dashboard?: boolean }>();
const mqttStore = useMqttStore();
const $q = useQuasar();
const { forecastConfigured, pricesConfigured, title } =
  useForecastPriceModules();
const forecastTopic = (suffix: string) =>
  mqttStore.getValue(`openWB/optional/forecast/${suffix}`);
const priceTopic = (suffix: string) =>
  mqttStore.getValue(`openWB/optional/ep/${suffix}`);
const now = ref(Date.now());
const hoveredTime = ref<number | null>(null);
const readoutTime = computed(() => hoveredTime.value ?? now.value);
const hoverReadoutPlugin: Plugin<'line'> = {
  id: 'outlookHoverReadout',
  afterEvent(_chart, args) {
    if (!args.inChartArea || args.event.type === 'mouseout')
      hoveredTime.value = null;
  },
};
const plot = ref<HTMLElement>();
const plotWidth = ref(600);
const fontsReady = ref(false);
let observer: ResizeObserver | undefined;
let timer: ReturnType<typeof setTimeout> | undefined;
const updateClock = () => {
  now.value = Date.now();
  timer = setTimeout(updateClock, 60_000 - (now.value % 60_000));
};
onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    plotWidth.value = entry.contentRect.width;
  });
  if (plot.value) observer.observe(plot.value);
  const family = getComputedStyle(document.body).fontFamily;
  void Promise.allSettled(
    [400, 500, 700].map((weight) =>
      document.fonts.load(`${weight} 16px ${family}`),
    ),
  ).then(() => {
    fontsReady.value = true;
  });
  updateClock();
});
onBeforeUnmount(() => {
  clearTimeout(timer);
  observer?.disconnect();
});

const providerName = (provider: unknown) =>
  provider &&
  typeof provider === 'object' &&
  'name' in provider &&
  typeof provider.name === 'string'
    ? provider.name
    : '';
const forecastProvider = computed(() =>
  providerName(forecastTopic('provider')),
);
const points = computed(() =>
  forecastConfigured.value
    ? forecastPoints(forecastTopic('get/values'), now.value)
    : [],
);
const currentForecast = computed(() =>
  forecastValueAt(points.value, readoutTime.value),
);
const todayEnergy = computed(() =>
  forecastNumber(forecastTopic('get/today_kwh')),
);
const tomorrowEnergy = computed(() =>
  forecastNumber(forecastTopic('get/tomorrow_kwh')),
);
const priceProviders = computed(() =>
  !pricesConfigured.value
    ? []
    : [
        { key: 'flexible_tariff', label: 'Stromtarif', color: '#C95555' },
        { key: 'grid_fee', label: 'Netzentgelte', color: '#D99B28' },
      ].flatMap((entry) => {
        const provider = priceTopic(`${entry.key}/provider`);
        return provider &&
          typeof provider === 'object' &&
          'type' in provider &&
          provider.type
          ? [{ ...entry, name: providerName(provider) }]
          : [];
      }),
);
const totalPrices = computed(() =>
  pricesConfigured.value ? pricePoints(priceTopic('get/prices')) : [],
);
const displayRange = computed(() =>
  outlookRange(
    points.value,
    totalPrices.value,
    now.value,
    forecastConfigured.value,
    pricesConfigured.value,
  ),
);
const emptyMessage = computed(() =>
  forecastConfigured.value && pricesConfigured.value
    ? 'Keine PV-Prognose- und Strompreisdaten für einen gemeinsamen Zeitraum vorhanden.'
    : forecastConfigured.value
      ? 'Noch keine PV-Prognosedaten für heute und morgen vorhanden.'
      : 'Noch keine Strompreisdaten vorhanden.',
);
const price = computed(() =>
  currentPrice(totalPrices.value, readoutTime.value),
);
const format = (value: number | null) =>
  value === null
    ? '—'
    : value.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
const statuses = computed(() =>
  [
    ...(forecastConfigured.value
      ? [
          {
            key: 'forecast',
            label: 'PV-Prognose',
            state: forecastTopic('get/fault_state'),
            message: forecastTopic('get/fault_str'),
          },
        ]
      : []),
    ...priceProviders.value.map((provider) => ({
      key: provider.key,
      label: provider.label,
      state: priceTopic(`${provider.key}/get/fault_state`),
      message: priceTopic(`${provider.key}/get/fault_str`),
    })),
  ].map((entry) => {
    const state = forecastNumber(entry.state);
    const message =
      typeof entry.message === 'string' && entry.message.trim()
        ? entry.message
        : state === null
          ? 'Status noch nicht verfügbar.'
          : state === 0
            ? 'Kein Fehler.'
            : state === 1
              ? 'Warnung im Modul.'
              : 'Fehler im Modul.';
    return {
      key: entry.key,
      label: entry.label,
      message:
        state === 0
          ? message.replace(/^Die flexible_tariff Preisliste/, 'Die Preisliste')
          : message,
      icon:
        state === null
          ? 'help_outline'
          : state === 0
            ? 'check_circle'
            : state === 1
              ? 'warning'
              : 'error',
      color:
        state === null
          ? 'grey'
          : state === 0
            ? 'positive'
            : state === 1
              ? 'warning'
              : 'negative',
    };
  }),
);

const priceSeries = computed(() => {
  const limit = priceIntervalEnd(totalPrices.value) ?? undefined;
  return [
    {
      label: 'Gesamtpreis',
      color: '#3B82F6',
      points: totalPrices.value,
    },
    ...priceProviders.value.map((provider) => ({
      label: provider.label,
      color: provider.color,
      points: pricePoints(priceTopic(`${provider.key}/get/prices`)).filter(
        (point) => limit === undefined || point.x < limit,
      ),
    })),
  ];
});
const timeline = computed(() =>
  outlookTimeline(
    points.value,
    priceSeries.value.map((series) => series.points),
    displayRange.value,
    now.value,
  ),
);
const chartData = computed<ChartData<'line'>>(() => {
  return {
    datasets: [
      ...(forecastConfigured.value
        ? [
            {
              label: 'PV-Prognose',
              yAxisID: 'power',
              data: forecastOnTimeline(points.value, timeline.value),
              borderColor: '#28a745',
              backgroundColor: 'rgba(40, 167, 69, 0.18)',
              fill: true,
              tension: 0,
              borderWidth: 2,
              pointRadius: 0,
              pointHoverRadius: 4,
            },
          ]
        : []),
      ...priceSeries.value
        .filter((series) => series.points.length)
        .map((series) => ({
          label: series.label,
          yAxisID: 'price',
          data: pricesOnTimeline(series.points, timeline.value),
          borderColor: series.color,
          backgroundColor: series.color,
          stepped: 'before' as const,
          fill: false,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
        })),
    ],
  };
});
const hasData = computed(() => displayRange.value !== null);
const chartOptions = computed<ChartOptions<'line'>>(() => {
  void $q.dark.isActive;
  const color = getComputedStyle(document.body).color;
  const range = displayRange.value;
  const axisFont = props.dashboard ? timeSeriesAxisFont : undefined;
  const ticks = { color, font: axisFont, maxTicksLimit: 6 };
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    // Every series is sampled on the same timestamps, so index is time-safe.
    interaction: { mode: 'index', axis: 'x', intersect: false },
    onHover: (_event, elements) => {
      hoveredTime.value = elements.length
        ? (timeline.value[elements[0].index] ?? null)
        : null;
    },
    plugins: {
      legend: {
        position: 'top',
        labels: { color, boxWidth: 16, font: axisFont },
      },
      tooltip: {
        ...(props.dashboard ? timeSeriesTooltip : {}),
        callbacks: {
          label: (context) => {
            const text = `${context.dataset.label}: ${format(context.parsed.y)} ${context.dataset.yAxisID === 'power' ? 'kW' : 'ct/kWh'}`;
            const canvas = context.chart.ctx;
            canvas.save();
            canvas.font = `${props.dashboard ? timeSeriesTooltip.bodyFont.size : Chart.defaults.font.size}px ${Chart.defaults.font.family}`;
            const lines = wrapTooltipLabel(
              text,
              canvas,
              Math.max(60, Math.min(480, context.chart.width - 64)),
            );
            canvas.restore();
            return lines;
          },
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        min: range?.start,
        max: range?.end,
        time: {
          unit: 'hour',
          displayFormats: { hour: 'dd.LL. HH:mm' },
          tooltipFormat: 'dd.LL.yyyy HH:mm',
        },
        ticks: {
          color,
          font: axisFont,
          padding: 8,
          maxTicksLimit: Math.max(
            2,
            Math.min(12, Math.floor(plotWidth.value / 100)),
          ),
          maxRotation: 0,
          callback: (value) => {
            const date = new Date(Number(value));
            return [
              date.toLocaleDateString(undefined, {
                day: '2-digit',
                month: '2-digit',
              }),
              date.toLocaleTimeString(undefined, {
                hour: '2-digit',
                minute: '2-digit',
              }),
            ];
          },
        },
        grid: { display: false },
      },
      power: {
        display: forecastConfigured.value,
        type: 'linear',
        position: 'left',
        beginAtZero: true,
        ticks,
        title: {
          display: true,
          text: 'PV-Leistung [kW]',
          color,
          font: axisFont,
        },
        grid: {
          color: $q.dark.isActive
            ? 'rgba(255,255,255,0.12)'
            : 'rgba(0,0,0,0.10)',
        },
      },
      price: {
        display: pricesConfigured.value,
        type: 'linear',
        position: forecastConfigured.value ? 'right' : 'left',
        ticks,
        title: {
          display: true,
          text: 'Preis [ct/kWh]',
          color,
          font: axisFont,
        },
        grid: {
          drawOnChartArea: !forecastConfigured.value,
          color: $q.dark.isActive
            ? 'rgba(255,255,255,0.12)'
            : 'rgba(0,0,0,0.10)',
        },
      },
    },
  };
});
</script>

<style scoped>
.forecast-price-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow-y: auto;
}
.forecast-price-slider {
  padding: 12px;
  background: var(--q-card-background);
  border-radius: 15px;
  filter: drop-shadow(0 0 0.3rem var(--q-chart-shadow));
}
.combined-header,
.combined-summary,
.combined-messages {
  flex: 0 0 auto;
}
.combined-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.combined-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: start;
  justify-content: flex-start;
  gap: 12px 32px;
}
.combined-summary dl {
  display: grid;
  grid-template-columns: max-content minmax(0, max-content);
  gap: 6px 16px;
  margin: 0;
  max-width: 100%;
  min-width: 0;
}
.combined-summary dl > div {
  display: contents;
}
.combined-summary dd {
  margin: 0;
  text-align: right;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  max-width: 22em;
  overflow-wrap: anywhere;
}
.combined-plot {
  position: relative;
  flex: 1 0 140px;
  min-height: 140px;
}
.combined-plot > canvas {
  width: 100% !important;
  height: 100% !important;
}
.combined-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.combined-messages {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 24px;
}
.combined-status {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.combined-status > .q-icon {
  flex-shrink: 0;
}
.combined-status > span {
  min-width: 0;
}
</style>
