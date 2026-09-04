import { boot } from 'quasar/wrappers';
import { Chart } from 'chart.js';

// Chart.js draws in its own Helvetica/Arial stack, which resolves to a
// different face on every platform and matches none of them to the Roboto the
// rest of the app is set in. Set the global default rather than a per-chart
// `options.font`: scale ticks and axis titles resolve their font through
// Chart.defaults, not through the chart's options, so a per-chart setting
// reaches only the plugins that read `chart.options.font` by hand.
export default boot(() => {
  Chart.defaults.font.family = "'Roboto', sans-serif";
});
