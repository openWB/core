import { TooltipItem } from 'chart.js'; // Importieren des TooltipItem-Typs

export interface HistoryChartTooltipItem extends TooltipItem<'line'> {
  dataset: TooltipItem<'line'>['dataset'] & {
    unit?: string;
  };
}
