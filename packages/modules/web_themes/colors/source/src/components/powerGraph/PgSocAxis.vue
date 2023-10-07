<template>
  <g
    id="PGSocAxis"
    class="axis"
    :transform="'translate('+(width-20)+',0)'"
  ></g>
</template>
<script setup lang="ts">
import { computed, onMounted } from 'vue'
import * as d3 from 'd3'
const props = defineProps<{
  width: number
  height: number
  margin: { left: number; top: number; right: number; bottom: number }
}>()
const y = computed(() => {
  return d3
    .scaleLinear()
    .range([props.height - 10, 0])
    .domain([0, 100])
})
const axisGenerator = computed(() => {
  return d3
    .axisRight(y.value)
    .ticks(5)
    .tickFormat((d) => d.toString() + '%')
})
function drawSocAxis() {
  let axis = d3.select<d3.AxisContainerElement,number>('g#PGSocAxis')
  axis.call(axisGenerator.value)
  axis.selectAll('.tick').attr('font-size', 12)
  axis.selectAll('.tick line').attr('stroke', 'var(--color-bg)')
  axis.select('.domain').attr('stroke', 'var(--color-bg)')
 }

onMounted(() => {
  drawSocAxis()
 })
</script>
<style scoped></style>
