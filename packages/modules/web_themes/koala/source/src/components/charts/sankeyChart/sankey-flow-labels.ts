/**
 * Value labels drawn on each flow.
 *
 * The plugin has a built-in `flowLabels` option, but it renders the raw flow
 * number (`${this.flow}` in Flow.draw), so there is no way to format watts as
 * "6,90 kW". This draws the labels ourselves instead, with the same formatting
 * the rest of the theme uses.
 *
 * Labels are placed along the flow rather than always at its midpoint: two
 * flows that cross can pass through the same point, and stacking their values
 * there leaves both unreadable. A label that still cannot be placed is left
 * out, and the tooltip carries its value instead.
 */
import { defaults } from 'chart.js';
import { toFont } from 'chart.js/helpers';
import type { Plugin } from 'chart.js';

const HORIZONTAL_CLEARANCE = 8;

const VERTICAL_MARGIN = 2;

// Positions to try along the flow, as a fraction of its length. The midpoint
// first, then alternating outwards, so a label moves the shortest distance
// that clears its neighbours. Staying clear of the ends leaves the node labels
// alone and avoids the steepest part of the curve.
const POSITIONS = [0.5, 0.35, 0.65, 0.25, 0.75, 0.15, 0.85];

interface FlowGeometry {
  flow: number;
  height: number;
  x: number;
  x2: number;
  y: number;
  y2: number;
}

interface LabelBox {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

// Center of the flow band at `t`, 0 being the left node and 1 the right.
function centerAt(flow: FlowGeometry, t: number): { x: number; y: number } {
  // start + (distance to travel) × (fraction travelled at t)
  return {
    x: flow.x + (flow.x2 - flow.x) * t * (2 - 3 * t + 2 * t * t),
    y: flow.y + (flow.y2 - flow.y) * t * t * (3 - 2 * t) + flow.height / 2,
  };
}

function overlaps(a: LabelBox, b: LabelBox): boolean {
  return (
    a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top
  );
}

export function createFlowLabels(options: {
  format: (watts: number) => string;
  color: (dataIndex: number) => string;
}): { plugin: Plugin<'sankey'>; labelled: ReadonlySet<number> } {
  // tooltip not displayed for flows with labels.
  const labelled = new Set<number>();

  const plugin: Plugin<'sankey'> = {
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

      const placed: LabelBox[] = [];
      labelled.clear();

      for (const [dataIndex, flow] of flows.entries()) {
        // Bands thinner than a line of text cannot hold the label legibly.
        if (flow.height < font.lineHeight) {
          continue;
        }
        const text = options.format(flow.flow);
        const halfWidth =
          ctx.measureText(text).width / 2 + HORIZONTAL_CLEARANCE / 2;
        const halfHeight = font.lineHeight / 2 + VERTICAL_MARGIN;
        // First position that fits between the two nodes and clears every
        // label already placed.
        let center: { x: number; y: number } | undefined;
        let box: LabelBox | undefined;
        for (const t of POSITIONS) {
          const candidate = centerAt(flow, t);
          const candidateBox = {
            left: candidate.x - halfWidth,
            right: candidate.x + halfWidth,
            top: candidate.y - halfHeight,
            bottom: candidate.y + halfHeight,
          };
          if (candidateBox.left < flow.x || candidateBox.right > flow.x2) {
            continue;
          }
          if (placed.some((other) => overlaps(candidateBox, other))) {
            continue;
          }
          center = candidate;
          box = candidateBox;
          break;
        }
        // Nowhere left to put it: leave this one to the tooltip.
        if (center === undefined || box === undefined) {
          continue;
        }

        placed.push(box);
        labelled.add(dataIndex);
        ctx.fillStyle = options.color(dataIndex);
        ctx.fillText(text, center.x, center.y);
      }
      ctx.restore();
    },
  };

  return { plugin, labelled };
}
