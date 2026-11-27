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
  // Browser storage can be unavailable (blocked site data, policies, full
  // quota) and then throws. Every access goes through these two helpers so
  // that the store, and with it the whole UI, still loads with defaults.
  const readStorage = (key: string): string | null => {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  };
  const writeStorage = (key: string, value: string) => {
    try {
      localStorage.setItem(key, value);
    } catch {
      // Keep the value in memory only.
    }
  };
  // A ref that starts from the saved value and saves every change.
  // `parse` returns undefined for missing or invalid values to use the fallback.
  const persistedRef = <T>(
    key: string,
    fallback: T,
    parse: (value: string) => T | undefined,
  ) => {
    let initialValue = fallback;
    const saved = readStorage(key);
    if (saved !== null) {
      try {
        initialValue = parse(saved) ?? fallback;
      } catch {
        // Invalid saved value, keep the fallback.
      }
    }
    const preference = ref(initialValue);
    watch(
      preference,
      (value) =>
        writeStorage(
          key,
          Array.isArray(value) ? JSON.stringify(value) : String(value),
        ),
      { deep: true },
    );
    return preference;
  };
  const parseList = (saved: string): string[] | undefined => {
    const value: unknown = JSON.parse(saved);
    return Array.isArray(value) &&
      value.every((item) => typeof item === 'string')
      ? value
      : undefined;
  };

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
  if (readStorage('koala-dashboard-defaults-version') !== '1') {
    const defaults = {
      'koala-desktop-overview': 'true',
      'koala-desktop-slides': JSON.stringify(defaultSlides),
      'koala-device-sections': JSON.stringify(defaultDeviceSections),
      'koala-device-layout': 'grid',
      'koala-history-height': '500',
    };
    for (const [key, value] of Object.entries(defaults)) {
      writeStorage(key, value);
    }
    writeStorage('koala-dashboard-defaults-version', '1');
  }

  const desktopOverview = persistedRef(
    'koala-desktop-overview',
    true,
    (value) => value !== 'false',
  );
  // Separate forecast and price views were merged into forecast_price_chart.
  const legacySlides = ['forecast_chart', 'electricity_price_chart'];
  const desktopSlides = persistedRef(
    'koala-desktop-slides',
    [...defaultSlides],
    (value) => parseList(value)?.filter((name) => !legacySlides.includes(name)),
  );
  // Introduce the combined view once without resetting other dashboard choices.
  if (readStorage('koala-forecast-prices-default-applied') !== '1') {
    if (!desktopSlides.value.includes('forecast_price_chart')) {
      desktopSlides.value.push('forecast_price_chart');
    }
    writeStorage('koala-forecast-prices-default-applied', '1');
  }
  const additionalChartsOpen = ref(false);
  const dashboardVisual = persistedRef(
    'koala-dashboard-visual',
    'flow_diagram',
    (value) => value || undefined,
  );
  const historyChartHeight = persistedRef(
    'koala-history-height',
    500,
    (value) => {
      const height = Number(value);
      if (!Number.isFinite(height) || height <= 0) return undefined;
      return historyChartHeights.reduce((closest, option) =>
        Math.abs(option.value - height) < Math.abs(closest.value - height)
          ? option
          : closest,
      ).value;
    },
  );
  // Open tiles of the desktop daily totals strip only; the mobile carousel
  // keeps its own, unsaved expansion state.
  const expandedDailyTotals = persistedRef<string[]>(
    'koala-expanded-daily-totals',
    [],
    parseList,
  );
  const dashboardDeviceSections = persistedRef(
    'koala-device-sections',
    [...defaultDeviceSections],
    parseList,
  );
  const deviceLayout = persistedRef<'grid' | 'sections'>(
    'koala-device-layout',
    'grid',
    (value) => (value === 'sections' ? 'sections' : 'grid'),
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
