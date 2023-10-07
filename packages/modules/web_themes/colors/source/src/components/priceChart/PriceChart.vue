<template>
  <WBWidget v-if="etData.isEtEnabled">
    <template v-slot:title> Preisbasiertes Laden </template>
    <template v-slot:buttons>
      <span class="color-charging"> Max: {{ etData.etMaxPrice }} ct</span>
    </template>
    <div class="row p-0 m-0">
      <div class="col-12 pricechartColumn p-0 m-0">
        <figure id="pricechart" class="p-0 m-0">
          <svg viewBox="0 0 400 120">
            <g
              :transform="'translate(' + margin.left + ',' + margin.right + ')'"
              id="priceChartCanvas"
            ></g>
          </svg>
        </figure>
      </div>
    </div>
    <div class="row m-0 p-0">
      <div class="col-2 m-0 p-0 d-flex justify-content-start">
        <button type="button" class="btn btn-secondary priceLess price-button"
        @click="reducePrice">
          <i class="fa fa-xl fa-minus-square"></i>
        </button>
      </div>
      <div class="col-8 d-flex justify-content-center">
        <input
          type="range"
          class="form-range"
          id="maxPrice"
          min="-25"
          max="95"
          step="0.1"
          v-model.number="etData.etMaxPrice"
        />
      </div>
      <div class="col-2 m-0 p-0 d-flex justify-content-end">
        <button type="button" class="btn btn-secondary priceMore price-button"
        @click="increasePrice">
          <i class="fa fa-xl fa-plus-square"></i>
        </button>
      </div>
    </div>
    <div class="p-0 m-0">
      <div class="col m-0 p-0 tablecell maxPrice">
        <label for="maxPrice" class="col-form-label p-0 m-0"
          >Max. Preis: {{ etData.etMaxPrice }} ct
        </label>
      </div>
    </div>
  </WBWidget>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import * as d3 from 'd3'
import { etData } from './model'
import WBWidget from '../shared/WBWidget.vue'

const width = 400
const height = 120
const margin = { top: 5, bottom: 15, left: 15, right: 5 }
const xxx = ref(0)
const plotdata = computed(() => {
  let valueArray: number[][] = []
  if (etData.etPriceList != '') {
    let lineBuffer = etData.etPriceList.split(/\r?\n|\r/) // split into lines
    lineBuffer.shift() // remove first line
    valueArray = lineBuffer
      .map((line) => {
        // split lines into tuples [time,price]
        return line.split(',')
      })
      .map((line) => [+line[0] * 1000, +line[1]]) // multiply timestamps by 1000
  }
  return valueArray
})
const barwidth = computed(() => {
  if (plotdata.value.length > 1) {
    return (width - margin.left - margin.right) / plotdata.value.length - 1
  } else {
    return 0
  }
})
const xScale = computed(() => {
  let xdomain = d3.extent(plotdata.value, (d) => d[0]) as [number, number]
  xdomain[1] = xdomain[1] + 3600000
  return d3
    .scaleTime()
    .range([0, width - margin.left - margin.right])
    .domain(xdomain)
})
const yScale = computed(() => {
  let ydomain = d3.extent(plotdata.value, (d) => d[1]) as [number, number]
  if (ydomain[0] > 0) {
    ydomain[0] = 0
  }
  ydomain[1] = Math.floor(ydomain[1] + 1)
  return d3
    .scaleLinear()
    .range([height - margin.bottom - margin.top, 0])
    .domain(ydomain)
})
const linePath = computed(() => {
  console.log(etData)
  const generator = d3.line()
  const points = [
    [0, yScale.value(etData.etMaxPrice)],
    [width - margin.left - margin.right, yScale.value(etData.etMaxPrice)],
  ]
  return generator(points as [number, number][])
})
const xAxisGenerator = computed(() => {
  return d3
    .axisBottom<Date>(xScale.value)
    .ticks(4)
    .tickFormat(d3.timeFormat('%H:%M'))
})
const yAxisGenerator = computed(() => {
  return d3
    .axisLeft<number>(yScale.value)
    .ticks(6)
    .tickSizeInner(-(width - margin.right - margin.left))
    .tickFormat((d) => d.toString())
})
const draw = computed(() => {
  let svg = d3.select('g#priceChartCanvas')
  svg.selectAll('*').remove()
  const bargroups = svg
    .selectAll('bar')
    .data(plotdata.value)
    .enter()
    .append('g')
  bargroups
    .append('rect')
    .attr('class', 'bar')
    .attr('x', (d) => xScale.value(d[0]))
    .attr('y', (d) => (d[1] >= 0 ? yScale.value(d[1]) : yScale.value(0)))
    .attr('width', barwidth.value)
    .attr('height', (d) =>
      d[1] >= 0
        ? yScale.value(0) - yScale.value(d[1])
        : yScale.value(d[1]) - yScale.value(0),
    )
    .attr('fill', (d) =>
      d[1] <= etData.etMaxPrice ? 'var(--color-charging)' : 'var(--color-axis',
    )
  // Line for max price
  svg.append('path').attr('d', linePath.value).attr('stroke', 'yellow')
  // X Axis
  const xAxis = svg.append('g').attr('class', 'axis').call(xAxisGenerator.value)
  xAxis.attr(
    'transform',
    'translate(' + margin.left + ',' + (height - margin.bottom) + ')',
  )
  xAxis.selectAll('.tick').attr('font-size', 8).attr('color', 'var(--color-bg)')
  xAxis
    .selectAll('.tick line')
    .attr('stroke', 'var(--color-bg)')
    .attr('stroke-width', '0.5')
  xAxis.select('.domain').attr('stroke', 'var(--color-bg')
  // Y Axis
  const yAxis = svg.append('g').attr('class', 'axis').call(yAxisGenerator.value)
  yAxis.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')
  yAxis.selectAll('.tick').attr('font-size', 8).attr('color', 'var(--color-bg)')

  yAxis
    .selectAll('.tick line')
    .attr('stroke', 'var(--color-bg)')
    .attr('stroke-width', '0.5')

  yAxis.select('.domain').attr('stroke', 'var(--color-bg)')

  return 'PriceChart.vue'
})
function increasePrice () {
    etData.etMaxPrice = Math.round(etData.etMaxPrice*10 + 1) / 10
}
function reducePrice () {
    etData.etMaxPrice = Math.round(etData.etMaxPrice*10 - 1) / 10
}
</script>

<style scoped>
.color-charging {
  color: var(--color-charging);
}
.price-button {
  background-color: var(--color-bg);
  color: var(--color-fg);
  border: 0;
}
</style>
