/**
 * Draw node names and formatted flow values in one collision-aware pass.
 * Anything that does not fit is reported to the accessible HTML fallback.
 */
import { toFont } from 'chart.js/helpers';
import type { Plugin } from 'chart.js';
import type { Flow } from 'chartjs-chart-sankey';

const POSITIONS = [0.5, 0.35, 0.65, 0.25, 0.75, 0.15, 0.85];
const GAP = 4;
const PAD_X = 6;
const PAD_Y = 3;

interface LabelBox {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

interface NodeBox extends LabelBox {
  id: string;
}

export interface SankeyLabelLayout {
  missingNodes: string[];
  missingFlows: number[];
}

function overlaps(a: LabelBox, b: LabelBox): boolean {
  return (
    a.left < b.right + GAP &&
    a.right + GAP > b.left &&
    a.top < b.bottom + GAP &&
    a.bottom + GAP > b.top
  );
}

export function createFlowLabels(options: {
  format: (watts: number) => string;
  color: () => string;
  showNodeNames: () => boolean;
  onLayout: (layout: SankeyLabelLayout) => void;
}): { plugin: Plugin<'sankey'>; labelled: ReadonlySet<number> } {
  const labelled = new Set<number>();
  const plugin: Plugin<'sankey'> = {
    id: 'sankeyFlowLabels',
    afterDatasetsDraw(chart) {
      const { ctx, chartArea } = chart;
      const flows = chart.getDatasetMeta(0).data as Flow[];
      const dataset = chart.data.datasets[0];
      const nodeWidth = dataset.nodeWidth ?? 16;
      // Aggregate incoming/outgoing endpoints instead of using controller internals.
      const nodes = new Map<string, NodeBox>();
      const addNode = (
        id: string,
        left: number,
        top: number,
        height: number,
      ) => {
        const existing = nodes.get(id);
        nodes.set(id, {
          id,
          left,
          right: left + nodeWidth,
          top: Math.min(existing?.top ?? top, top),
          bottom: Math.max(existing?.bottom ?? top + height, top + height),
        });
      };
      for (const flow of flows) {
        if (flow.from && flow.to) {
          addNode(flow.from.key, flow.x - nodeWidth, flow.y, flow.height);
          addNode(flow.to.key, flow.x2, flow.y2, flow.height);
        }
      }

      const placed: LabelBox[] = [];
      const nodeBoxes = [...nodes.values()];
      const layout: SankeyLabelLayout = { missingNodes: [], missingFlows: [] };
      const fits = (box: LabelBox) =>
        box.left >= chartArea.left &&
        box.right <= chartArea.right &&
        box.top >= chartArea.top &&
        box.bottom <= chartArea.bottom &&
        !nodeBoxes.some((other) => overlaps(box, other)) &&
        !placed.some((other) => overlaps(box, other));

      ctx.save();
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const draw = (text: string, box: LabelBox) => {
        placed.push(box);
        ctx.fillStyle = options.color();
        ctx.fillText(
          text,
          (box.left + box.right) / 2,
          (box.top + box.bottom) / 2,
        );
      };

      const nodeFont = toFont({
        ...chart.options.font,
        size: 16,
        weight: 500,
        lineHeight: 1.2,
      });
      ctx.font = nodeFont.string;
      for (const node of nodeBoxes) {
        const text = dataset.labels?.[node.id] ?? node.id;
        const width = ctx.measureText(text).width + PAD_X * 2;
        const height = nodeFont.lineHeight + PAD_Y * 2;
        const y = Math.max(
          chartArea.top + height / 2,
          Math.min((node.top + node.bottom) / 2, chartArea.bottom - height / 2),
        );
        // Keep the name next to its node, on the inward-facing side.
        const left =
          node.left > (chartArea.left + chartArea.right) / 2
            ? node.left - GAP * 2 - width
            : node.right + GAP * 2;
        const box = {
          left,
          right: left + width,
          top: y - height / 2,
          bottom: y + height / 2,
        };
        if (options.showNodeNames() && fits(box)) {
          draw(text, box);
        } else {
          layout.missingNodes.push(node.id);
        }
      }

      const valueFont = toFont({
        ...chart.options.font,
        size: 16,
        weight: 500,
        lineHeight: 1.2,
      });
      ctx.font = valueFont.string;
      labelled.clear();
      // Give the most significant flows first choice of a readable location.
      const ordered = flows
        .map((flow, index) => ({ flow, index }))
        .sort((a, b) => b.flow.flow - a.flow.flow);
      for (const { flow, index } of ordered) {
        const text = options.format(flow.flow);
        const halfWidth = ctx.measureText(text).width / 2 + PAD_X;
        const halfHeight = valueFont.lineHeight / 2 + PAD_Y;
        if (flow.height >= halfHeight * 2) {
          for (const t of POSITIONS) {
            const x = flow.x + (flow.x2 - flow.x) * t * (2 - 3 * t + 2 * t * t);
            const y =
              flow.y +
              (flow.y2 - flow.y) * t * t * (3 - 2 * t) +
              flow.height / 2;
            const box = {
              left: x - halfWidth,
              right: x + halfWidth,
              top: y - halfHeight,
              bottom: y + halfHeight,
            };
            if (box.left >= flow.x && box.right <= flow.x2 && fits(box)) {
              draw(text, box);
              labelled.add(index);
              break;
            }
          }
        }
        if (!labelled.has(index)) layout.missingFlows.push(index);
      }
      ctx.restore();
      options.onLayout(layout);
    },
  };
  return { plugin, labelled };
}
