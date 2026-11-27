import { computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import EnergyFlowChart from './energyFlowChart/EnergyFlowChart.vue';
import HistoryChart from './historyChart/HistoryChart.vue';
import DailyTotals from './dailyTotals/DailyTotals.vue';
import SankeyChart from './sankeyChart/SankeyChart.vue';
import ForecastPriceChart from './forecastPriceChart/ForecastPriceChart.vue';
import { useForecastPriceModules } from './forecastPriceChart/useForecastPriceModules';

export const topCharts = [
  { name: 'flow_diagram', label: 'Energiefluss', component: EnergyFlowChart },
  { name: 'history_chart', label: 'Tagesverlauf', component: HistoryChart },
  {
    name: 'daily_totals',
    label: 'Leistung und Tageswerte',
    component: DailyTotals,
  },
  { name: 'sankey_chart', label: 'Sankey', component: SankeyChart },
  {
    name: 'forecast_price_chart',
    label: 'PV-Prognose & Strompreise',
    component: ForecastPriceChart,
  },
];

export function useTopCharts() {
  const mqttStore = useMqttStore();
  const { forecastConfigured, pricesConfigured, title } =
    useForecastPriceModules();
  return computed(() => {
    const order = mqttStore.themeConfiguration?.top_carousel_slide_order;
    const configured: Record<string, boolean> = {
      forecast_price_chart: forecastConfigured.value || pricesConfigured.value,
    };
    const availableCharts = topCharts
      .filter((chart) => configured[chart.name] !== false)
      .map((chart) =>
        chart.name === 'forecast_price_chart'
          ? { ...chart, label: title.value }
          : chart,
      );
    if (!order?.length) return availableCharts;
    const orderedCharts = order.flatMap((name) =>
      availableCharts.filter((chart) => chart.name === name),
    );
    // Older theme configurations only know the original carousel diagrams.
    return orderedCharts.concat(
      availableCharts.filter(
        (chart) => chart.name in configured && !order.includes(chart.name),
      ),
    );
  });
}
