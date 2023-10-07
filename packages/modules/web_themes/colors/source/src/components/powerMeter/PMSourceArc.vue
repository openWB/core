<template>
  <g id="pmSourceArc" :origin="draw"></g>
</template>

<script setup lang="ts">
import { globalConfig } from '@/assets/js/themeConfig'
import type { PowerItem, ItemList } from '@/assets/js/types'
import { sourceSummary, masterData } from '@/assets/js/model'
import * as d3 from 'd3'
import { computed, watchEffect } from 'vue';
// props
const props = defineProps<{
  radius: number
  cornerRadius: number
  circleGapSize: number
  emptyPower: number
}>()
//  computed: 
const draw = computed(() => {
  // Draw the arc using d3
  const arcCount = Object.values(sourceSummary).length
  let emptyPowerItem: PowerItem = {
    name: '',
    power: props.emptyPower,
    energy: 0,
    energyPv: 0,
    energyBat: 0,
    pvPercentage: 0,
    color: 'var(--color-bg)',
    icon: ''
  }
  let plotdata = sourceSummary
  plotdata['zz-empty'] = emptyPowerItem

  const pieGenerator = d3
    .pie<PowerItem>()
    .value((record: PowerItem) => record.power)
    .startAngle(-Math.PI / 2 + props.circleGapSize)
    .endAngle(Math.PI / 2 - props.circleGapSize)
    .sort(null)
  const path = d3
    .arc<d3.PieArcDatum<PowerItem>>()
    .innerRadius((props.radius / 6) * 5)
    .outerRadius(props.radius)
    .cornerRadius(props.cornerRadius)
    .padAngle(0)
  const graph = d3.select('g#pmSourceArc')
  graph.selectAll('*').remove()
  graph
    .selectAll('sources')
    .data(pieGenerator(Object.values(plotdata)))
    .enter()
    .append('path')
    .attr('d', path)
    .attr('fill', (d) => d.data.color)
    .attr('stroke', (d, i) =>
      i == arcCount
        ? d.data.power > 0
          ? 'var(--color-scale)'
          : 'null'
        : d.data.color,
    )
  return 'pmSourceArc.vue'
})

watchEffect(() => {
  let currentMax =
    sourceSummary.pv.power +
    sourceSummary.evuIn.power +
    sourceSummary.batOut.power
  if (currentMax > globalConfig.maxPower) {
    globalConfig.maxPower = currentMax
  }
})
</script>

<style></style>
