<template>
  <g id="emBargraph">
    <!-- Bars -->
    <g v-for="item in plotdata">
      <EmBar :item="item" :xScale="xScale" :yScale="yScale" :margin="margin" :height="height" :barcount="plotdata.length"
        :autText="autTxt(item)" :autarchy="autPct(item)">
      </EmBar>
    </g>
    <animateTransform attribute-name="transform" type="scale" from="1 0" to="1 1" begin="0s" dur="2s"></animateTransform>
  </g>
</template>

<script setup lang="ts">
import * as d3 from 'd3'
import type { MarginType, PowerItem } from '@/assets/js/types'
import EmBar from './EmBar.vue'
import { sourceSummary, historicSummary, usageSummary } from '@/assets/js/model'
import { graphData } from '../powerGraph/model'

const props = defineProps<{
  plotdata: PowerItem[]
  xScale: d3.ScaleBand<string>
  yScale: d3.ScaleLinear<number, number, never>
  margin: MarginType
  height: number
}>()

// computed: {
function autPct(item: PowerItem) {
  if (item.name == 'PV') {
    const src = (graphData.graphMode == 'live' || graphData.graphMode == 'day') ? sourceSummary : historicSummary
    const usg = (graphData.graphMode == 'live' || graphData.graphMode == 'day') ? usageSummary : historicSummary
    const exportedEnergy = usg.evuOut.energy
    const generatedEnergy = src.pv.energy
    return Math.round((generatedEnergy - exportedEnergy) / generatedEnergy * 100)
  } else if (item.name == 'Netz') {
    const src = (graphData.graphMode == 'live' || graphData.graphMode == 'day') ? sourceSummary : historicSummary
    const usg = (graphData.graphMode == 'live' || graphData.graphMode == 'day') ? usageSummary : historicSummary
    const exportedEnergy = usg.evuOut.energy
    const importedEnergy = src.evuIn.energy
    const generatedEnergy = src.pv.energy
    const batEnergy = src.batOut.energy
    const storedEnergy = usg.batIn.energy
    return Math.round((generatedEnergy + batEnergy - exportedEnergy - storedEnergy) / (generatedEnergy + batEnergy + importedEnergy - exportedEnergy - storedEnergy) * 100)
  } else {
    return item.pvPercentage
  }
}

function autTxt(item: PowerItem) {
  if (item.name == 'PV') {
    return 'Eigen'
  } else {
    return 'Aut'
  }
}
</script>

<style></style>
