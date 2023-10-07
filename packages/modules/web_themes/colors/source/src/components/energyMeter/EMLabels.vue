<template>
   <g id="emBarLabels">
    <!-- Bars -->
    <g v-for="item in plotdata">
      <EmLabel :item="item" :xScale="xScale" :yScale="yScale" :margin="margin" :height="height" :barcount="plotdata.length"
        :autText="autTxt(item)" :autarchy="autPct(item)">
      </EmLabel>
    </g>
  </g>
</template>

<script setup lang="ts">
import * as d3 from 'd3'
import type { PowerItem, MarginType } from '@/assets/js/types'
import { graphData } from '../powerGraph/model'
import { historicSummary, sourceSummary, usageSummary } from '@/assets/js/model'
import EmLabel from './EmLabel.vue'
const props = defineProps<{
  plotdata: PowerItem[]
  xScale: d3.ScaleBand<string>
  yScale: d3.ScaleLinear<number, number>
  height: number
  margin: MarginType
}>()
// computed
// methods
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

<style>

</style>
