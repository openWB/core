import { defineStore } from 'pinia';
import { ref, watch } from 'vue';
import { useQuasar } from 'quasar';

export const historyChartHeights = [
  { label: 'Klein', value: 300 },
  { label: 'Mittel', value: 500 },
  { label: 'Groß', value: 800 },
];

export const useLocalDataStore = defineStore('localData', () => {
  const $q = useQuasar();

  // Display preferences belong to this browser, not the openWB configuration.
  const defaultSlides = [
    'daily_totals',
    'history_chart',
    'flow_diagram',
    'sankey_chart',
    'forecast_price_chart',
  ];
  const defaultDeviceSections = [
    'charge-points',
    'vehicles',
    'batteries',
    'consumers',
  ];
  // Apply the complete dashboard start state once to new and existing profiles.
  // Afterwards explicit choices, including disabled views, remain persistent.
  if (localStorage.getItem('koala-dashboard-defaults-version') !== '1') {
    const defaults = {
      'koala-desktop-overview': 'true',
      'koala-desktop-slides': JSON.stringify(defaultSlides),
      'koala-device-sections': JSON.stringify(defaultDeviceSections),
      'koala-device-layout': 'grid',
      'koala-history-height': '500',
    };
    for (const [key, value] of Object.entries(defaults)) {
      localStorage.setItem(key, value);
    }
    localStorage.setItem('koala-dashboard-defaults-version', '1');
  }
  const savedList = (key: string, fallback: string[]): string[] => {
    try {
      const value: unknown = JSON.parse(localStorage.getItem(key) || 'null');
      return Array.isArray(value) &&
        value.every((item) => typeof item === 'string')
        ? value
        : fallback;
    } catch {
      return fallback;
    }
  };
  const desktopOverview = ref(
    localStorage.getItem('koala-desktop-overview') !== 'false',
  );
  const desktopSlides = ref(
    savedList('koala-desktop-slides', defaultSlides).filter(
      (name) => !['forecast_chart', 'electricity_price_chart'].includes(name),
    ),
  );
  localStorage.setItem(
    'koala-desktop-slides',
    JSON.stringify(desktopSlides.value),
  );
  // Introduce the combined view once without resetting other dashboard choices.
  if (localStorage.getItem('koala-forecast-prices-default-applied') !== '1') {
    if (!desktopSlides.value.includes('forecast_price_chart')) {
      desktopSlides.value.push('forecast_price_chart');
    }
    localStorage.setItem(
      'koala-desktop-slides',
      JSON.stringify(desktopSlides.value),
    );
    localStorage.setItem('koala-forecast-prices-default-applied', '1');
  }
  const additionalChartsOpen = ref(false);
  const dashboardVisual = ref(
    localStorage.getItem('koala-dashboard-visual') || 'flow_diagram',
  );
  watch(dashboardVisual, (value) =>
    localStorage.setItem('koala-dashboard-visual', value),
  );
  const savedHistoryHeight = Number(
    localStorage.getItem('koala-history-height'),
  );
  const historyChartHeight = ref(
    Number.isFinite(savedHistoryHeight) && savedHistoryHeight > 0
      ? historyChartHeights.reduce((closest, option) =>
          Math.abs(option.value - savedHistoryHeight) <
          Math.abs(closest.value - savedHistoryHeight)
            ? option
            : closest,
        ).value
      : 500,
  );
  const expandedDailyTotals = ref(savedList('koala-expanded-daily-totals', []));
  watch(
    expandedDailyTotals,
    (value) =>
      localStorage.setItem(
        'koala-expanded-daily-totals',
        JSON.stringify(value),
      ),
    { deep: true },
  );
  const dashboardDeviceSections = ref(
    savedList('koala-device-sections', defaultDeviceSections),
  );
  const deviceLayout = ref<'grid' | 'sections'>(
    localStorage.getItem('koala-device-layout') === 'sections'
      ? 'sections'
      : 'grid',
  );
  watch(deviceLayout, (value) =>
    localStorage.setItem('koala-device-layout', value),
  );
  watch(historyChartHeight, (value) =>
    localStorage.setItem('koala-history-height', String(value)),
  );
  watch(
    dashboardDeviceSections,
    (value) =>
      localStorage.setItem('koala-device-sections', JSON.stringify(value)),
    { deep: true },
  );
  watch(desktopOverview, (value) =>
    localStorage.setItem('koala-desktop-overview', String(value)),
  );
  watch(
    desktopSlides,
    (value) =>
      localStorage.setItem('koala-desktop-slides', JSON.stringify(value)),
    { deep: true },
  );

  //////////////    Legend Visibility     ///////////////////////

  const legendVisibility = ref<Record<string, boolean>>({
    history_chart: !$q.platform.is.mobile,
    sankey_chart: !$q.platform.is.mobile,
  });
  const isLegendVisible = (chart: string) =>
    legendVisibility.value[chart] ?? !$q.platform.is.mobile;

  const toggleLegendVisibility = (chart: string) => {
    legendVisibility.value[chart] = !isLegendVisible(chart);
  };

  //////////////    Legend Item Visibility     ///////////////////////

  const hiddenDatasets = ref<string[]>([]);

  // Function to add a dataset to hidden list
  const hideDataset = (datasetKey: string) => {
    if (!hiddenDatasets.value.includes(datasetKey)) {
      hiddenDatasets.value.push(datasetKey);
    }
  };

  const showDataset = (datasetKey: string) => {
    hiddenDatasets.value = hiddenDatasets.value.filter(
      (item) => item !== datasetKey,
    );
  };

  const toggleDataset = (datasetKey: string) => {
    if (hiddenDatasets.value.includes(datasetKey)) {
      showDataset(datasetKey);
    } else {
      hideDataset(datasetKey);
    }
  };

  const isDatasetHidden = (datasetKey: string): boolean => {
    return hiddenDatasets.value.includes(datasetKey);
  };

  return {
    dashboardVisual,
    expandedDailyTotals,
    deviceLayout,
    historyChartHeight,
    dashboardDeviceSections,
    desktopOverview,
    desktopSlides,
    additionalChartsOpen,
    hiddenDatasets,
    isDatasetHidden,
    toggleDataset,
    hideDataset,
    showDataset,
    isLegendVisible,
    toggleLegendVisibility,
  };
});
