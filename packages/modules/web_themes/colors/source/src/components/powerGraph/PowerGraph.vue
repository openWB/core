<template>
  <WBWidget :full-width="true">
    <template v-slot:title>{{ heading }}</template>
    <template v-slot:buttons>
      <PgSelector widgetid="graphsettings" @shiftLeft="shiftLeft" @shiftRight="shiftRight" @shiftUp="shiftUp"
        @shiftDown="shiftDown" :show-left-button="true" :show-right-button="true"></PgSelector>
    </template>

    <figure id="powergraph" class="p-0 m-0" @click="changeStackOrder">
      <svg :viewBox="'0 0 ' + width + ' ' + height">
        <!-- Draw the source graph -->
        <PGSourceGraph :width="width - margin.left - 2 * margin.right" :height="(height - margin.top - margin.bottom) / 2"
          :margin="margin" />
        <PGUsageGraph :width="width - margin.left - 2 * margin.right" :height="(height - margin.top - margin.bottom) / 2"
          :margin="margin" :stack-order="globalConfig.usageStackOrder" />
        <PGXAxis :width="width - margin.left - 2 * margin.right" :height="height - margin.top - margin.bottom"
          :margin="margin" :graphData="graphData" />
        <g :transform="'translate(' + margin.left + ',' + margin.top + ')'">
          <PgSoc v-if="(graphData.graphMode == 'day' ||
              graphData.graphMode == 'today') &&
            Object.values(vehicles).length > 0
            " :width="width - margin.left - 2 * margin.right" :height="(height - margin.top - margin.bottom) / 2"
            :margin="margin" :order="0"></PgSoc>
          <PgSoc v-if="(graphData.graphMode == 'day' ||
              graphData.graphMode == 'today') &&
            Object.values(vehicles).length > 1
            " :width="width - margin.left - 2 * margin.right" :height="(height - margin.top - margin.bottom) / 2"
            :margin="margin" :order="1"></PgSoc>
          <PgSocAxis v-if="graphData.graphMode == 'day' || graphData.graphMode == 'today'
            " :width="width - margin.left - margin.right" :height="(height - margin.top - margin.bottom) / 2"
            :margin="margin"></PgSocAxis>
        </g>
        <g id="button">
            <text :x="width" :y="height - 10" color="var(--color-menu)" text-anchor="end">
            <tspan fill="var(--color-menu)" class="fas fa-lg">{{ "\uf0dc" }}</tspan>
          </text>
        </g>
      </svg>
    </figure>
  </WBWidget>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import WBWidget from '../shared/WBWidget.vue'
import PGSourceGraph from './PGSourceGraph.vue'
import PGUsageGraph from './PGUsageGraph.vue'
import PGXAxis from './PGXAxis.vue'
// import PGMenu from './PGMenu.vue'
import {
  graphData,
  dayGraph,
  monthGraph,
  setInitializeUsageGraph,
  shiftLeft,
  shiftRight,
  shiftUp,
  shiftDown,
  yearGraph
} from './model'
import { globalConfig } from '@/assets/js/themeConfig'
import PgSoc from './PgSoc.vue'
import PgSocAxis from './PgSocAxis.vue'
import { vehicles } from '../chargePointList/model'
import { formatMonth } from '@/assets/js/helpers'
import PgSelector from './PgSelector.vue'

// state
const width = 500
const height = 500
const margin = { top: 10, right: 20, bottom: 10, left: 25 }
const stackOrderMax = 2

// computed
const heading = computed(() => {
  let heading = 'Leistung / Ladestand '
  switch (graphData.graphMode) {
    case 'live':
      if (graphData.data.length) {
        const startTime = graphData.data[0].date
        const endTime = graphData.data[graphData.data.length - 1].date
      } else {
        console.warn('Graph Data empty.')
      }
      break
    case 'today':
      // heading = heading + 'heute'
      break
    case 'day':
      let d = dayGraph.date
    //  heading = heading + (dayGraph.date.getDate()) + '.' + (dayGraph.date.getMonth()+1)
  }
  return heading
})

function changeStackOrder() {
  let newOrder = globalConfig.usageStackOrder + 1
  if (newOrder > stackOrderMax) {
    newOrder = 0
  }
  globalConfig.usageStackOrder=newOrder
  setInitializeUsageGraph(true)
}
</script>

<style scoped>
.fa-ellipsis-vertical {
  color: var(--color-menu);
}

.datebadge {
  background-color: var(--color-menu);
  color: var(--color-bg);
  font-size: var(--font-medium);
  font-weight: normal;
}
</style>
