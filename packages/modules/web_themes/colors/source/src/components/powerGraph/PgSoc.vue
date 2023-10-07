<template>
  <path
    class="soc-baseline"
    :d="line"
    stroke="var(--color-bg)"
    stroke-width="1"
    fill="none"
  ></path>
  <path
    class="soc-dashes"
    :d="line"
    :stroke="cpColor"
    stroke-width="1"
    :style="{ strokeDasharray: '3,3' }"
    fill="none"
  >
  </path>
  <text
    class="cpname"
    :x="nameX"
    :y="nameY"
    :style="{ fill: cpColor, fontSize: 10 }"
    :text-anchor="textPosition"
  >
    {{ cpName }}
  </text>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as d3 from 'd3'
import { chargePoints, vehicles } from '../chargePointList/model'
import { graphData, type GraphDataItem } from './model'

const props = defineProps<{
  width: number
  height: number
  margin: { left: number; top: number; right: number; bottom: number }
  order: number // 0 or 1
}>()
const evs = computed (() => Object.values(vehicles))
const xScale = computed(() => {
  let e = d3.extent(graphData.data, (d) => d.date)
  if (e[0] && e[1]) {
    return d3.scaleTime<number>().domain(e).range([0, props.width])
  } else {
    return d3.scaleTime().range([0, 0])
  }
})
const yScale = computed(() => {
  return d3
    .scaleLinear()
    .range([props.height - 10, 0])
    .domain([0, 100])
})
const line = computed(() => {
  const path = d3
    .line<GraphDataItem>()
    .x((d) => xScale.value(d.date))
    .y((d) => (yScale.value(d['soc' + props.order]) != undefined) ? yScale.value(d['soc' + props.order]) : yScale.value(0))
  let p = path(graphData.data)
  return p ? p : ''
})
const cpName = computed(() => {
  return evs.value[props.order].name ?? ''
})
const cpColor = computed(() => {
  return props.order == 0 
    ? 'var(--color-cp1)'
    : 'var(--color-cp2)'
})
const nameX = computed(() => {
  if (props.order == 0) {
    return props.width - 3
  } else {
    return 3
  }
})
const nameY = computed(() => {
  if (graphData.data.length > 0) {
    if (props.order == 0) {
      return yScale.value(
        graphData.data[graphData.data.length - 1].soc0 + 2)
      
    } else {
      return yScale.value(graphData.data[0].soc1 + 2) 
    }
  } else {
    return 0
  }
})
const textPosition = computed(() => {
  if (props.order == 0) {
    return 'end'
  } else {
    return 'start'
  }
})
</script>
<style scoped></style>
