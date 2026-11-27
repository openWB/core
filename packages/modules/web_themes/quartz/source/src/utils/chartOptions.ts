import type { ChartOptions } from 'chart.js'
import { getCssColor } from '@/utils/color'

type Plugins = NonNullable<ChartOptions<'line'>['plugins']>

interface CardChartOptions {
  yTitle: string
  xUnit?: 'hour' | 'day'
  yMinSuggested?: number
  noAnimation?: boolean
  plugins: Plugins
}

/** The look shared by the time charts in the detail and settings cards. */
export function cardChartOptions(options: CardChartOptions): ChartOptions<'line'> {
  const muted = getCssColor('--muted')
  const border = getCssColor('--border')
  return {
    responsive: true,
    maintainAspectRatio: false,
    ...(options.noAnimation ? { animation: false as const } : {}),
    interaction: { mode: 'index', intersect: false },
    plugins: options.plugins,
    scales: {
      x: {
        type: 'time',
        time: { unit: options.xUnit ?? 'hour' },
        grid: { color: border },
        ticks: { color: muted, font: { size: 11 } },
      },
      y: {
        ...(options.yMinSuggested === undefined ? {} : { suggestedMin: options.yMinSuggested }),
        grid: { color: border },
        ticks: { color: muted, font: { size: 12 } },
        title: { display: true, text: options.yTitle, color: muted, font: { size: 12 } },
      },
    },
  }
}
