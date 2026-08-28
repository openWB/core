/**
 * Value labels drawn in the middle of each flow.
 *
 * The plugin has a built-in `flowLabels` option, but it renders the raw flow
 * number (`${this.flow}` in Flow.draw), so there is no way to format watts as
 * "6,90 kW". This draws the labels ourselves instead, with the same formatting
 * the rest of the theme uses.
 */
import { defaults } from 'chart.js';
import { toFont } from 'chart.js/helpers';
import type { Plugin } from 'chart.js';

// Clear space to leave either side of the text.
const HORIZONTAL_MARGIN = 8;

interface FlowGeometry {
  flow: number;
  height: number;
  x: number;
  x2: number;
  y: number;
  y2: number;
}

export function createFlowLabels(options: {
  format: (watts: number) => string;
  color: (dataIndex: number) => string;
}): Plugin<'sankey'> {
  return {
    id: 'sankeyFlowLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      const flows = chart.getDatasetMeta(0).data as unknown as FlowGeometry[];
      // Same font the plugin resolves for the node labels, so the two sets of
      // text match.
      const font = toFont(chart.options.font ?? defaults.font);

      ctx.save();
      ctx.font = font.string;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      // The index is the flow's position in the dataset, which is what the
      // hover focus keys off, so `color` can dim a label with its band.
      for (const [dataIndex, flow] of flows.entries()) {
        // Bands thinner than a line of text cannot hold the label legibly.
        if (flow.height < font.lineHeight) {
          continue;
        }
        const text = options.format(flow.flow);
        if (
          ctx.measureText(text).width >
          flow.x2 - flow.x - HORIZONTAL_MARGIN
        ) {
          continue;
        }
        const x = (flow.x + flow.x2) / 2;
        const y = (flow.y + flow.y2) / 2 + flow.height / 2;
        ctx.fillStyle = options.color(dataIndex);
        ctx.fillText(text, x, y);
      }
      ctx.restore();
    },
  };
}
