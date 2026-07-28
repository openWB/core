/** Fixed node ids. Chargepoints/consumers use dynamic ids (see input). */
export const NODE_GRID = 'grid';
export const NODE_PV = 'pv';
export const NODE_BATTERY = 'battery';
export const NODE_HOUSE = 'house';

/**
 * Raw signed power per component, using the same sign conventions as the
 * existing EnergyFlowChart / store getters:
 *   grid    : + import (source)   | - export (sink)
 *   pv      : - production (source)| + consumption (rare)
 *   battery : + charging (sink)   | - discharging (source)
 *   cp/consumer power: + drawing (sink) | - feeding back, e.g. V2G (source)
 */
export interface EnergyFlowInput {
  grid: number;
  pv: number;
  battery: number;
  chargePoints: DynamicNodeInput[];
  consumers: DynamicNodeInput[];
}

export interface DynamicNodeInput {
  id: string;
  label: string;
  power: number;
}

export interface FlowNode {
  id: string;
  label: string;
  power: number;
}

export interface FlowEdge {
  from: string;
  to: string;
  flow: number;
}

export interface AllocationResult {
  edges: FlowEdge[];
  /** Every node that participates, so the caller can build labels + columns. */
  nodes: FlowNode[];
  sources: FlowNode[];
  sinks: FlowNode[];
  totalSources: number;
  totalSinks: number;
  imbalance: number;
}

const MIN_EDGE_WATTS = 1;

/**
 * Split the raw component totals into source and sink nodes with positive
 * magnitudes. Household consumption is added as the residual so the diagram
 * balances by construction.
 */
function classifyNodes(input: EnergyFlowInput): {
  sources: FlowNode[];
  sinks: FlowNode[];
} {
  const sources: FlowNode[] = [];
  const sinks: FlowNode[] = [];

  if (input.grid > 0) {
    sources.push({ id: NODE_GRID, label: 'Netz', power: input.grid });
  } else if (input.grid < 0) {
    sinks.push({ id: NODE_GRID, label: 'Netz', power: -input.grid });
  }

  if (input.pv < 0) {
    sources.push({ id: NODE_PV, label: 'PV', power: -input.pv });
  }

  if (input.battery > 0) {
    sinks.push({ id: NODE_BATTERY, label: 'Speicher', power: input.battery });
  } else if (input.battery < 0) {
    sources.push({
      id: NODE_BATTERY,
      label: 'Speicher',
      power: -input.battery,
    });
  }

  for (const cp of input.chargePoints) {
    if (cp.power > 0) {
      sinks.push({ id: cp.id, label: cp.label, power: cp.power });
    } else if (cp.power < 0) {
      sources.push({ id: cp.id, label: cp.label, power: -cp.power });
    }
  }

  for (const consumer of input.consumers) {
    if (consumer.power > 0) {
      sinks.push({ id: consumer.id, label: consumer.label, power: consumer.power });
    } else if (consumer.power < 0) {
      sources.push({ id: consumer.id, label: consumer.label, power: -consumer.power });
    }
  }

  // Household consumption = balancing residual.
  const totalSources = sumPower(sources);
  const otherSinks = sumPower(sinks);
  const house = Math.max(0, totalSources - otherSinks);
  if (house > 0) {
    sinks.push({ id: NODE_HOUSE, label: 'Hausverbrauch', power: house });
  }

  return { sources, sinks };
}

function sumPower(nodes: FlowNode[]): number {
  return nodes.reduce((total, node) => total + node.power, 0);
}

export interface GroupOptions {
  threshold: number;
  id: string;
  label: string;
}

/**
 * Collapse a list of dynamic nodes (chargePoints or consumers) into a single
 * aggregated node once it exceeds the threshold.
 */
export function groupNodes(
  nodes: DynamicNodeInput[],
  options: GroupOptions,
): DynamicNodeInput[] {
  if (nodes.length <= options.threshold) {
    return nodes;
  }
  const power = nodes.reduce((total, node) => total + node.power, 0);
  return [{ id: options.id, label: options.label, power }];
}

/**
 * Compute the Sankey edges from the raw component totals using the uniform
 * proportional rule. Returns edges plus the classified nodes and totals.
 */
export function allocate(input: EnergyFlowInput): AllocationResult {
  const { sources, sinks } = classifyNodes(input);
  const totalSources = sumPower(sources);
  const totalSinks = sumPower(sinks);

  const edges: FlowEdge[] = [];
  if (totalSources > 0 && totalSinks > 0) {
    for (const source of sources) {
      const share = source.power / totalSources;
      for (const sink of sinks) {
        const flow = sink.power * share;
        if (flow >= MIN_EDGE_WATTS) {
          edges.push({ from: source.id, to: sink.id, flow });
        }
      }
    }
  }

  return {
    edges,
    nodes: [...sources, ...sinks],
    sources,
    sinks,
    totalSources,
    totalSinks,
    imbalance: totalSources - totalSinks,
  };
}
