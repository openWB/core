<template>
	<g id="emYAxis" class="axis" :origin="drawYAxis" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AxisScale, AxisContainerElement } from 'd3'
import { axisLeft, select } from 'd3'
import { globalConfig } from '@/assets/js/themeConfig'
import { graphData } from '../powerGraph/model'
const props = defineProps<{
	yScale: AxisScale<number>
	width: number
	fontsize: number
}>()

// computed
const yAxisGenerator = computed(() => {
	return axisLeft<number>(props.yScale)
		.tickFormat((d) => formatNumber(d))
		.ticks(6)
		.tickSizeInner(-props.width)
})
const drawYAxis = computed(() => {
	const yAxis = select<AxisContainerElement, number>('g#emYAxis')
	yAxis.attr('class', 'axis').call(yAxisGenerator.value)

	yAxis
		.append('text')
		.attr('y', 6)
		.attr('dy', '0.71em')
		.attr('text-anchor', 'end')
		.text('energy')

	yAxis.selectAll('.tick').attr('font-size', props.fontsize)
	if (globalConfig.showGrid) {
		yAxis
			.selectAll('.tick line')
			.attr('stroke', 'var(--color-grid)')
			.attr('stroke-width', '0.5')
	} else {
		yAxis.selectAll('.tick line').attr('stroke', 'var(--color-bg)')
	}
	yAxis.select('.domain').attr('stroke', 'var(--color-bg)')
	return 'emYAxis.vue'
})

function formatNumber(n: number) {
	if (n > 0) {
		if (graphData.graphMode == 'year') {
			return (n / 1000000).toString()
		} else {
			return (n / 1000).toString()
		}
	} else {
		return ''
	}
}
</script>

<style></style>
