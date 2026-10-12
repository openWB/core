import type { Chart, TooltipItem, ChartDataset, LegendItem } from 'chart.js';

export interface HistoryChartTooltipItem extends TooltipItem<'line'> {
  dataset: TooltipItem<'line'>['dataset'] & {
    unit?: string;
  };
}

// Define a type for the component that contains the Chart instance
export interface ChartComponentRef {
  chart?: Chart;
}

export type Category =
  | 'chargepoint'
  | 'vehicle'
  | 'battery'
  | 'consumer'
  | 'component';

export const CONSUMER_TOTAL_LABEL = 'Verbraucher ges.';

export const CONSUMER_TOTAL_KEY = 'consumer-total';
export const BATTERY_TOTAL_KEY = 'battery-total';
export const BATTERY_SOC_KEY = 'battery-soc';

export const consumerDatasetKey = (id: number) => `consumer-${id}`;

// Add category and key to the chart datasets
export interface CategorizedDataset extends ChartDataset<
  'line',
  { x: number; y: number }
> {
  category: Category;
  key: string;
}

// Add category and key to the legendItem
export interface LegendItemWithCategory extends LegendItem {
  category?: Category;
  key?: string;
}
