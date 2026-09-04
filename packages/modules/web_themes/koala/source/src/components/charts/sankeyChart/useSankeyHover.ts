/**
 * Hover focus for the Sankey diagram: the flow under the cursor keeps its
 * color while every other flow is dimmed toward grey, so the hovered one
 * stands out.
 */
import { ref } from 'vue';
import type { Plugin } from 'chart.js';

// Non-hovered flows are pushed toward grey. The sankey plugin re-applies its
// own alpha to flow gradients, so fading by alpha alone would change only the
// nodes, not the flows — we must change the RGB.
const FADE_TOWARD = 150; // mid grey (neutral in light and dark)
const FADE_AMOUNT = 0.65; // 0 = untouched, 1 = fully grey

export function useSankeyHover(colorForNode: (id: string) => string) {
  // Index of the flow under the cursor, as a position in the dataset's `data`
  // array (null = none).
  const hoveredIndex = ref<number | null>(null);

  /**
   * Tracks the hovered flow. This is a plugin rather than the `onHover` option
   * because Chart.js only calls onHover for events inside the chart area, so a
   * mouseout could never clear the highlight that way. Chart.js also replays
   * the last in-area event after every update(), which would re-apply the
   * highlight that same repaint was meant to clear. afterEvent sees every
   * event, mouseout included, and can tell a replay from a real one.
   */
  const hoverPlugin: Plugin<'sankey'> = {
    id: 'sankeyHoverFocus',
    afterEvent(chart, args) {
      // Ignore the post-update replay: it re-reports a stale in-area position
      // and would resurrect a highlight we just cleared.
      if (args.replay) {
        return;
      }
      const left = !args.inChartArea || args.event.type === 'mouseout';
      hoveredIndex.value = left
        ? null
        : (chart.getActiveElements()[0]?.index ?? null);
    },
  };

  /**
   * Returns the color function for one end of a flow: the node's own color,
   * or a faded version when a different flow is hovered.
   *
   * Call this inside the computed that builds the chart data, and call it
   * afresh on every recompute: it reads the hover state there, which is what
   * makes the dataset rebuild — and Chart.js re-resolve the flow colors — when
   * the hover changes. Hoisting the result out of the computed would freeze
   * the highlight.
   */
  const focusColors = () => {
    const hovered = hoveredIndex.value;
    return (nodeId: string, dataIndex: number): string => {
      const base = colorForNode(nodeId);
      return hovered !== null && dataIndex !== hovered ? fade(base) : base;
    };
  };

  /**
   * Fades an arbitrary color unless its flow is the hovered one, for things
   * drawn outside the dataset — the flow value labels, which would otherwise
   * stay at full contrast over a dimmed band.
   */
  const dimIfUnfocused = (color: string, dataIndex: number): string => {
    const hovered = hoveredIndex.value;
    return hovered !== null && dataIndex !== hovered ? fade(color) : color;
  };

  return { hoverPlugin, focusColors, dimIfUnfocused };
}

/**
 * Faded version of a color for non-hovered flows: mixed toward grey.
 */
function fade(color: string): string {
  const rgb = toRgb(color);
  if (rgb === null) {
    return color;
  }
  const mix = (channel: number) =>
    Math.round(channel * (1 - FADE_AMOUNT) + FADE_TOWARD * FADE_AMOUNT);
  return `rgb(${mix(rgb.r)}, ${mix(rgb.g)}, ${mix(rgb.b)})`;
}

/**
 * Parse a hex or rgb/rgba color string to its RGB channels.
 */
function toRgb(color: string): { r: number; g: number; b: number } | null {
  if (color.startsWith('#')) {
    let hex = color.slice(1);
    if (hex.length === 3) {
      hex = hex
        .split('')
        .map((char) => char + char)
        .join('');
    }
    const value = parseInt(hex, 16);
    return { r: (value >> 16) & 255, g: (value >> 8) & 255, b: value & 255 };
  }
  const match = color.match(/rgba?\(([^)]+)\)/);
  if (match) {
    const [r, g, b] = match[1]
      .split(',')
      .map((part) => parseInt(part.trim(), 10));
    return { r, g, b };
  }
  return null;
}
