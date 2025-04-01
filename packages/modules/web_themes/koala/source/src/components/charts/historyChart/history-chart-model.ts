import { TooltipItem, Chart } from 'chart.js'; // Importieren des TooltipItem-Typs
export interface HistoryChartTooltipItem extends TooltipItem<'line'> {
  dataset: TooltipItem<'line'>['dataset'] & {
    unit?: string;
  };
}

// Define a type for the component that contains the Chart instance
export interface ChartComponentRef {
  chart?: Chart;
}
