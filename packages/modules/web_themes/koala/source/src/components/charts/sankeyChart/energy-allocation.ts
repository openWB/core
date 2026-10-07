/** Fixed node ids. Chargepoints/consumers use dynamic ids (see input). */
export const NODE_GRID = 'grid';
export const NODE_PV = 'pv';
export const NODE_BATTERY = 'battery';
export const NODE_HOUSE = 'house';
export const NODE_HOUSE_REST = 'house_rest';
export const NODE_NOT_IN_HOME = 'not_in_home';

/** Column of each node in the diagram, left to right. */
export const COLUMN_SOURCE = 0;
export const COLUMN_SINK = 1;
export const COLUMN_HOUSE_PART = 2;

/**
 * Raw signed power per component, using the same sign conventions as the
 * existing EnergyFlowChart / store getters:
 *   grid    : + import (source)   | - export (sink)
 *   pv      : - production (source)| + consumption (rare)
 *   battery : + charging (sink)   | - discharging (source)
 *   cp/consumer power: + drawing (sink) | - feeding back, e.g. V2G (source)
 *
 * Consumers flagged `inHouse` are counted in the home consumption. They are
 * not drawn as sinks of their own but as parts of the household node, which
 * splits into them and the remaining household consumption in a third column.
 */
export interface EnergyFlowInput {
  grid: number;
  pv: number;
  battery: number;
  chargePoints: DynamicNodeInput[];
  consumers: DynamicNodeInput[];
  /**
   * Power not counted in the home consumption that is no consumer.
   * + drawing (sink) | - feeding (source).
   */
  notInHomeOther?: number;
  /**
   * Hybrid inverter/battery pairs. A hybrid battery charges from its inverter's
   * PV directly on the shared DC bus, before the remaining PV mixes with grid
   * on the AC side. Absent/empty means no hybrid handling (standard behavior).
   */
  hybrid?: HybridPair[];
}

export interface HybridPair {
  inverterPv: number;
  batteryCharge: number;
}

export interface DynamicNodeInput {
  id: string;
  label: string;
  power: number;
  inHouse?: boolean;
}

export interface FlowNode {
  id: string;
  label: string;
  power: number;
  column: number;
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
  /** Consumers counted in the home consumption plus the remainder. */
  houseParts: FlowNode[];
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
  houseParts: FlowNode[];
} {
  const sources: FlowNode[] = [];
  const sinks: FlowNode[] = [];
  const houseParts: FlowNode[] = [];
  const source = (id: string, label: string, power: number) =>
    sources.push({ id, label, power, column: COLUMN_SOURCE });
  const sink = (id: string, label: string, power: number) =>
    sinks.push({ id, label, power, column: COLUMN_SINK });

  if (input.grid > 0) {
    source(NODE_GRID, 'Netz', input.grid);
  } else if (input.grid < 0) {
    sink(NODE_GRID, 'Netz', -input.grid);
  }

  if (input.pv < 0) {
    source(NODE_PV, 'PV', -input.pv);
  }

  if (input.battery > 0) {
    sink(NODE_BATTERY, 'Speicher', input.battery);
  } else if (input.battery < 0) {
    source(NODE_BATTERY, 'Speicher', -input.battery);
  }

  for (const cp of input.chargePoints) {
    if (cp.power > 0) {
      sink(cp.id, cp.label, cp.power);
    } else if (cp.power < 0) {
      source(cp.id, cp.label, -cp.power);
    }
  }

  for (const consumer of input.consumers) {
    if (consumer.power > 0 && consumer.inHouse) {
      houseParts.push({
        id: consumer.id,
        label: consumer.label,
        power: consumer.power,
        column: COLUMN_HOUSE_PART,
      });
    } else if (consumer.power > 0) {
      sink(consumer.id, consumer.label, consumer.power);
    } else if (consumer.power < 0) {
      source(consumer.id, consumer.label, -consumer.power);
    }
  }

  const notInHomeOther = input.notInHomeOther ?? 0;
  if (notInHomeOther > 0) {
    sink(NODE_NOT_IN_HOME, 'Sonstige', notInHomeOther);
  } else if (notInHomeOther < 0) {
    source(NODE_NOT_IN_HOME, 'Sonstige', -notInHomeOther);
  }

  // Household consumption = balancing residual. It includes the consumers
  // counted in the home consumption, as they are not sinks of their own.
  const totalSources = sumPower(sources);
  const otherSinks = sumPower(sinks);
  const house = Math.max(0, totalSources - otherSinks);
  if (house > 0) {
    sink(NODE_HOUSE, 'Hausverbrauch', house);
  }

  return { sources, sinks, houseParts: splitHouse(house, houseParts) };
}

/**
 * Split the household node into the consumers counted in it and the rest.
 * Measurement noise can make those consumers add up to more than the
 * residual; they are then scaled down so the household node still balances.
 */
function splitHouse(house: number, consumers: FlowNode[]): FlowNode[] {
  if (house <= 0 || consumers.length === 0) {
    return [];
  }
  const consumerTotal = sumPower(consumers);
  const scale = Math.min(1, house / consumerTotal);
  const parts = consumers.map((node) => ({
    ...node,
    power: node.power * scale,
  }));
  const rest = house - consumerTotal * scale;
  if (rest >= MIN_EDGE_WATTS) {
    parts.push({
      id: NODE_HOUSE_REST,
      label: 'Sonstiger Hausverbrauch',
      power: rest,
      column: COLUMN_HOUSE_PART,
    });
  }
  return parts;
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
 * Fold edges sharing the same from/to into one summed edge. The hybrid
 * carve-out and the proportional pass can both emit a PV -> battery edge
 * whenever both nodes still have power left over (any system with a second
 * inverter or a second battery). Left unmerged that draws two ribbons between
 * the same pair of nodes and lists two tooltip entries for one flow.
 */
function mergeEdges(edges: FlowEdge[]): FlowEdge[] {
  const merged: FlowEdge[] = [];
  for (const edge of edges) {
    const existing = merged.find(
      (candidate) => candidate.from === edge.from && candidate.to === edge.to,
    );
    if (existing === undefined) {
      merged.push({ ...edge });
    } else {
      existing.flow += edge.flow;
    }
  }
  return merged;
}

/**
 * Compute the Sankey edges from the raw component totals.
 *
 * Rule: uniform proportional (every sink gets the same source mix), with one
 * pre-step for hybrid systems. On a hybrid inverter the battery charges from
 * that inverter's PV directly on the DC bus, upstream of where PV and grid mix
 * on the AC side. So we first carve a fixed PV -> battery edge for that DC
 * charge, then run the proportional rule on whatever source/sink power remains.
 * With no hybrid pairs this reduces to plain uniform proportional.
 */
export function allocate(input: EnergyFlowInput): AllocationResult {
  const { sources, sinks, houseParts } = classifyNodes(input);
  const totalSources = sumPower(sources);
  const totalSinks = sumPower(sinks);

  // Hybrid carve-out: PV routed to hybrid batteries on the DC bus.
  const pvNode = sources.find((node) => node.id === NODE_PV);
  const batteryNode = sinks.find((node) => node.id === NODE_BATTERY);
  let pvDirectToBattery = 0;
  if (pvNode !== undefined && batteryNode !== undefined) {
    for (const pair of input.hybrid ?? []) {
      pvDirectToBattery += Math.min(pair.inverterPv, pair.batteryCharge);
    }
    // Never route more than the PV we actually have or the battery took.
    pvDirectToBattery = Math.max(
      0,
      Math.min(pvDirectToBattery, pvNode.power, batteryNode.power),
    );
  }

  // Amounts fed into the proportional pass, with the DC charge removed. Node
  // totals are reconstituted from (fixed edge + proportional edges), so node
  // sizes in the diagram stay correct.
  const propSources = sources.map((node) =>
    node.id === NODE_PV
      ? { ...node, power: node.power - pvDirectToBattery }
      : node,
  );
  const propSinks = sinks.map((node) =>
    node.id === NODE_BATTERY
      ? { ...node, power: node.power - pvDirectToBattery }
      : node,
  );
  const remainingSourceTotal = sumPower(propSources);

  const edges: FlowEdge[] = [];
  if (pvDirectToBattery >= MIN_EDGE_WATTS) {
    edges.push({ from: NODE_PV, to: NODE_BATTERY, flow: pvDirectToBattery });
  }
  if (remainingSourceTotal > 0) {
    for (const source of propSources) {
      if (source.power <= 0) {
        continue;
      }
      const share = source.power / remainingSourceTotal;
      for (const sink of propSinks) {
        if (sink.power <= 0) {
          continue;
        }
        const flow = sink.power * share;
        if (flow >= MIN_EDGE_WATTS) {
          edges.push({ from: source.id, to: sink.id, flow });
        }
      }
    }
  }

  // Second stage: household -> the consumers counted in it and the rest.
  for (const part of houseParts) {
    if (part.power >= MIN_EDGE_WATTS) {
      edges.push({ from: NODE_HOUSE, to: part.id, flow: part.power });
    }
  }

  return {
    edges: mergeEdges(edges),
    nodes: [...sources, ...sinks, ...houseParts],
    sources,
    sinks,
    houseParts,
    totalSources,
    totalSinks,
    imbalance: totalSources - totalSinks,
  };
}
