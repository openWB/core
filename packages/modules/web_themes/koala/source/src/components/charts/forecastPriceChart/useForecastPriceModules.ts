import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';

export function useForecastPriceModules() {
  const mqttStore = useMqttStore();
  const forecastConfigured = computed(
    () => mqttStore.getValue('openWB/optional/forecast/configured') === true,
  );
  const pricesConfigured = computed(
    () => mqttStore.getValue('openWB/optional/ep/configured') === true,
  );
  const title = computed(() =>
    forecastConfigured.value && pricesConfigured.value
      ? 'PV-Prognose & Strompreise'
      : forecastConfigured.value
        ? 'PV-Prognose'
        : 'Strompreise',
  );
  return { forecastConfigured, pricesConfigured, title };
}
