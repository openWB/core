<template>
  <g
    id="pgSourceGraph"
    :origin="draw"
    :transform="'translate(' + margin.left + ',' + margin.top + ')'"
  ></g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as d3 from 'd3'
import { globalConfig } from '@/assets/js/themeConfig'
import {
  graphData,
  initializeSourceGraph,
  sourceGraphIsNotInitialized,
  sourceGraphIsInitialized,
} from './model'
import EnergyMeter from '../energyMeter/EnergyMeter.vue'
const props = defineProps<{
  width: number
  height: number
  margin: { left: number; top: number; right: number; bottom: number }
}>()

//state
const colors: { [key: string]: string } = {
  house: 'var(--color-house)',
  batIn: 'var(--color-battery)',
  inverter: 'var(--color-pv)',
  batOut: 'var(--color-battery)',
  selfUsage: 'var(--color-pv)',
  gridPush: 'var(--color-export)',
  gridPull: 'var(--color-evu)',
}
var paths: d3.Selection<SVGPathElement, [number, number][], d3.BaseType, any>
var rects: d3.Selection<SVGRectElement, [number, number], d3.BaseType, any>
const duration = globalConfig.showAnimations
  ? globalConfig.animationDuration
  : 0
const delay = globalConfig.showAnimations ? globalConfig.animationDelay : 0

// computed:
const draw = computed(() => {
  if (graphData.data.length > 0) {
    const graph = d3.select('g#pgSourceGraph')
    if (graphData.graphMode == 'month' || graphData.graphMode == 'year') {
      drawMonthGraph(graph)
    } else {
      drawGraph(graph)
    }
    const yAxis = graph.append('g').attr('class', 'axis')
    yAxis.call(yAxisGenerator.value)
    yAxis.selectAll('.tick').attr('font-size', 12)
    yAxis
      .selectAll('.tick line')
      .attr('stroke', ticklineColor.value)
      .attr('stroke-width', ticklineWidth.value)
    yAxis.select('.domain').attr('stroke', 'var(--color-bg)')
    return 'pgSourceGraph.vue'
  }
})
const keys = computed(() => {
  return (graphData.graphMode == 'month' || graphData.graphMode == 'year')
    ? ['gridPull', 'batOut', 'selfUsage', 'gridPush']
    : ['selfUsage', 'gridPush', 'batOut', 'gridPull']
})
const iScale = computed(() => {
  return d3
    .scaleLinear()
    .domain([0, graphData.data.length - 1])
    .range([0, props.width])
})

const iScaleMonth = computed(() =>
  d3
    .scaleBand<number>()
    .domain(Array.from({ length: graphData.data.length }, (v, k) => k))
    .range([0, props.width + props.margin.right])
    .paddingInner(0.4),
)
const stackGen = computed(() => d3.stack().keys(keys.value))
const stackedSeries = computed(() => stackGen.value(graphData.data))

const yScale = computed(() => {
  return d3
    .scaleLinear()
    .range([props.height - 10, 0])
    .domain(graphData.graphMode=='year'? [0,Math.ceil(extent.value[1]*10)/10]: [0, Math.ceil(extent.value[1])])
})

const extent = computed(() => {
  let result = d3.extent(graphData.data, (d) =>
    Math.max(d.solarPower + d.gridPull + d.batOut, d.selfUsage + d.gridPush),
  )
  if (result[0] != undefined && result[1] != undefined) {
    return result
  } else {
    return [0, 0]
  }
})
const ticklength = computed(() => (graphData.graphMode == 'month' || graphData.graphMode == 'year'))
  ? (-props.width - props.margin.right)
  : (-props.width)

const yAxisGenerator = computed(() => {
  return d3
    .axisLeft<number>(yScale.value)
    .tickSizeInner(ticklength)
    .ticks(4)
    .tickFormat((d: number) =>
      (d == 0 ? '' : Math.round(d * 10) / 10).toLocaleString(undefined),
    )
})
const ticklineWidth = computed(() => {
  if (globalConfig.showGrid) {
    return '0.5'
  } else {
    return '1'
  }
})
const ticklineColor = computed(() => {
  return globalConfig.showGrid ? 'var(--color-grid)' : 'var(--color-bg)'
})

function drawGraph(
  graph: d3.Selection<d3.BaseType, unknown, HTMLElement, any>,
) {
  const area0 = d3
    .area()
    .x((d, i) => iScale.value(i))
    .y(yScale.value(0))
  const area = d3
    .area()
    .x((d, i) => iScale.value(i))
    .y0((d) => yScale.value(d[0]))
    .y1((d) => yScale.value(d[1]))
  if (initializeSourceGraph) {
    graph.selectAll('*').remove()
    paths = graph
      .selectAll('.sourceareas')
      .data(stackedSeries.value as [number, number][][])
      .enter()
      .append('path')
      .attr('fill', (d, i) => colors[keys.value[i]])
      .attr('d', (series) => area0(series))
    paths
      .transition()
      .duration(duration)
      .delay(delay)
      .ease(d3.easeLinear)
      .attr('d', (series) => area(series))
    sourceGraphIsInitialized()
  } else {
    paths
      .data(stackedSeries.value as [number, number][][])
      .transition()
      .duration(0)
      .ease(d3.easeLinear)
      .attr('d', (series) => area(series))
  }
}
function drawMonthGraph(
  graph: d3.Selection<d3.BaseType, unknown, HTMLElement, any>,
) {
  if (initializeSourceGraph) {
    graph.selectAll('*').remove()
    rects = graph
      .selectAll('.sourcebar')
      .data(stackedSeries.value as [number, number][][])
      .enter()
      .append('g')
      .attr('fill', (d, i) => colors[keys.value[i]])
      .selectAll('rect')
      .data((d) => d)
      .enter()
      .append('rect')
      .attr('x', (d, i) => {
        return iScaleMonth.value(i) ?? 0
      })
      .attr('y', (d) => yScale.value(0))
      .attr('height', 0)
      .attr('width', iScaleMonth.value.bandwidth())
    rects
      .transition()
      .duration(duration)
      .delay(delay)
      .ease(d3.easeLinear)
      .attr('height', (d) => yScale.value(d[0]) - yScale.value(d[1]))
      .attr('y', (d) => yScale.value(d[1])),
      sourceGraphIsInitialized()
  } else {
    graph.selectAll('*').remove()
    rects = graph
      .selectAll('.sourcebar')
      .data(stackedSeries.value as [number, number][][])
      .enter()
      .append('g')
      .attr('fill', (d, i) => colors[keys.value[i]])
      .selectAll('rect')
      .data((d) => d)
      .enter()
      .append('rect')
      .attr('x', (d, i) => {
        return iScaleMonth.value(i) ?? 0
      })
      .attr('y', (d) => yScale.value(d[1]))
      .attr('width', iScaleMonth.value.bandwidth())
      .attr('height', (d) => yScale.value(d[0]) - yScale.value(d[1]))
  }
}
</script>

<style></style>
