<template>
  <WBWidget :full-width="true">
    <template v-slot:title>{{ heading }}</template>
    <template v-slot:buttons>
      <PgSelector widgetid="graphsettings" @shiftLeft="shiftLeft" @shiftRight="shiftRight" @shiftUp="shiftUp"
        @shiftDown="shiftDown" :show-left-button="true" :show-right-button="true"></PgSelector>
    </template>
  <!--   <div class="collapse" id="graphsettings2">
      <PGMenu @shiftLeft="shiftLeft" @shiftRight="shiftRight" :show-left-button="globalConfig.showLeftButton"
        :show-right-button="globalConfig.showRightButton" widgetid="graphsettings2">
      </PGMenu>
    </div> -->
    <figure id="energymeter" class="p-0 m-0">
      <svg viewBox="0 0 500 500">
        <g :transform="'translate(' + margin.left + ',' + margin.top + ')'">
          <!--  Bar Graph -->
          <EMBarGraph :plotdata="plotdata" :xScale="xScale" :yScale="yScale" :height="height" :margin="margin">
          </EMBarGraph>
          <!-- Y Axis -->
          <EMYAxis :yScale="yScale" :width="width" :fontsize="axisFontsize" :config="globalConfig"></EMYAxis>
          <text :x="-margin.left" y="-15" fill="var(--color-axis)" :font-size="axisFontsize">
            {{ graphData.graphMode == 'year' ? 'MWh' : 'kWh' }}
          </text>
          <EMLabels :plotdata="plotdata" :xScale="xScale" :yScale="yScale" :height="height" :margin="margin"
            :config="globalConfig"></EMLabels>
        </g>
      </svg>
    </figure>
  </WBWidget>
</template>
<script setup lang="ts">
import * as d3 from 'd3'
import type { PowerItem } from '@/assets/js/types'
import { sourceSummary, historicSummary } from '@/assets/js/model'
import { formatMonth } from '@/assets/js/helpers'
//import PGMenu from '../powerGraph/PGMenu.vue'
import EMBarGraph from './EMBarGraph.vue'
import EMYAxis from './EMYAxis.vue'
import EMLabels from './EMLabels.vue'
import WBWidget from '../shared/WBWidget.vue'
import PgSelector from '../powerGraph/PgSelector.vue'
import { globalConfig, setInitializeEnergyGraph } from '@/assets/js/themeConfig'
import {
  monthGraph,
  shiftLeft,
  shiftRight,
  shiftUp,
  shiftDown,
  yearGraph
} from '@/components/powerGraph/model'
import { dayGraph, graphData } from '@/components/powerGraph/model'
import { computed } from 'vue'
// props
const props = defineProps<{
  usageDetails: PowerItem[]
}>()
//state
const width = 500
const height = 500
const margin = {
  top: 25,
  bottom: 30,
  left: 25,
  right: 0,
}
const axisFontsize = 12
// computed
const plotdata = computed(() => {
  let sources = Object.values(sourceSummary)
  let usage = props.usageDetails
  let historic = Object.values(historicSummary)
  let result: PowerItem[] = []
  setInitializeEnergyGraph(true)
  switch (graphData.graphMode) {
    default:
    case 'live':
    case 'today':
      result = sources
        .concat(usage)
        .filter((row) => row.energy > 0)
      break
    case 'day':
    case 'month':
    case 'year':
      result = historic.filter((row) => row.energy > 0)
  }
  return result
})
const xScale = computed(() => {
  return d3
    .scaleBand()
    .range([0, width - margin.left - margin.right])
    .domain(plotdata.value.map((d) => d.name))
    .padding(0.4)
})
const yScale = computed(() => {
  return d3
    .scaleLinear()
    .range([height - margin.bottom - margin.top, 15])
    .domain([0, d3.max(plotdata.value, (d: PowerItem) => d.energy) as number])
})
const heading = 'Energie'
const displayDate = computed(() => {
  switch (graphData.graphMode) {
    case 'live':
      if (graphData.data.length) {
        const startTime = graphData.data[0].date
        const endTime = graphData.data[graphData.data.length - 1].date
        const liveGraphMinutes = Math.round((endTime - startTime) / 60000)
        return liveGraphMinutes + ' min'
      } else {
        console.warn('Graph Data empty.')
      }
      break
    case 'today':
      return 'heute'
    case 'day':
      let d = dayGraph.date
      return (
        dayGraph.date.getDate() + '.' + (dayGraph.date.getMonth() + 1) + '.'
      )
    case 'month':
      return formatMonth(monthGraph.month - 1, monthGraph.year)
    case 'year':
      return yearGraph.year.toString()
    default: return "???"
  }
})
</script>

<style scoped>

</style>
