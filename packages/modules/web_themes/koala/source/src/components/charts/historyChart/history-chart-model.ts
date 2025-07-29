import type { Chart, ChartDataset, TooltipItem } from 'chart.js'; // Importieren des TooltipItem-Typs
export interface HistoryChartTooltipItem extends TooltipItem<'line'> {
  dataset: TooltipItem<'line'>['dataset'] & {
    unit?: string;
  };
}

// Define a type for the component that contains the Chart instance
export interface ChartComponentRef {
  chart?: Chart;
}

export type Category = 'chargepoint' | 'vehicle' | 'battery' | 'component';

// Add category to the chart datasets
export interface CategorizedDataset
  extends ChartDataset<'line', { x: number; y: number }> {
  category: Category;
}
