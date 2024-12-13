<template>
	<g :transform="'translate(' + margin.left + ',' + margin.top + ')'">
		<g
			id="PGXAxis"
			class="axis"
			:origin="drawAxis1"
			:origin2="autozoom"
			:transform="'translate(0,' + (height / 2 - 6) + ')'"
		/>
		<g
			id="PGXAxis2"
			class="axis"
			:origin="drawAxis2"
			:transform="'translate(0,' + (height / 2 + 10) + ')'"
		/>
		<g v-if="globalConfig.showGrid">
			<rect
				x="0"
				y="0"
				:width="width"
				:height="height / 2 - 10"
				fill="none"
				stroke="var(--color-grid)"
				stroke-width="0.5"
			/>
		</g>
		<g v-if="globalConfig.showGrid">
			<rect
				x="0"
				:y="height / 2 + 10"
				:width="width"
				:height="height / 2 - 10"
				fill="none"
				stroke="var(--color-grid)"
				stroke-width="0.5"
			/>
		</g>
	</g>
</template>

<script setup lang="ts">
import type { AxisContainerElement, ScaleTime, Selection } from 'd3'
import { axisBottom, axisTop, select, timeFormat } from 'd3'
import { globalConfig } from '@/assets/js/themeConfig'
import { graphData, xScaleMonth, xScale, zoomedRange } from './model'
import { computed } from 'vue'

const props = defineProps<{
	width: number
	height: number
	margin: { left: number; top: number; right: number; bottom: number }
}>()
// state
const fontsize = 12

// computed
const xAxisGenerator = computed(() => {
	return axisBottom<Date>(xScale.value as ScaleTime<number, number, never>)
		.ticks(6)
		.tickSizeInner(ticksize.value)
		.tickFormat(timeFormat('%H:%M'))
})
const xAxisGenerator2 = computed(() => {
	return axisTop<Date>(xScale.value as ScaleTime<number, number, never>)
		.ticks(6)
		.tickSizeInner(ticksize.value + 3)
		.tickFormat(timeFormat(''))
})

const xAxisGeneratorMonth = computed(() =>
	axisBottom<number>(xScaleMonth.value)
		.ticks(4)
		.tickSizeInner(ticksize.value)
		.tickFormat((d) => d.toString()),
)
const xAxisGeneratorMonth2 = computed(() =>
	axisBottom<number>(xScaleMonth.value)
		.ticks(4)
		.tickSizeInner(ticksize.value)
		.tickFormat(() => ''),
)

const ticksize = computed(() => {
	if (graphData.graphMode !== 'month' && graphData.graphMode !== 'year') {
		return globalConfig.showGrid ? -(props.height / 2 - 7) : -10
	} else {
		return 0
	}
})

const drawAxis1 = computed(() => {
	let axis = select<AxisContainerElement, number>('g#PGXAxis')
	axis.selectAll('*').remove()
	if (graphData.graphMode == 'month' || graphData.graphMode == 'year') {
		axis.call(xAxisGeneratorMonth.value)
	} else {
		axis.call(xAxisGenerator.value)
	}

	axis
		.selectAll('.tick > text')
		//.attr('color', 'var(--color-axis)')
		.attr('fill', (d, i) =>
			i >= 0 || graphData.graphMode == 'month' || graphData.graphMode == 'year'
				? 'var(--color-axis)'
				: 'var(--color-bg)',
		)
		.attr('font-size', fontsize)

	if (globalConfig.showGrid) {
		axis
			.selectAll('.tick line')
			.attr('stroke', 'var(--color-grid)')
			.attr('stroke-width', '0.5')
	} else {
		axis.selectAll('.tick line').attr('stroke', 'var(--color-bg)')
	}
	axis.select('.domain').attr('stroke', 'var(--color-bg)')
	axis
		.append('text')
		.attr('x', -props.margin.left)
		.attr('y', 12)
		.attr('fill', 'var(--color-axis)')
		.attr('font-size', fontsize)
		.text(graphData.graphMode == 'year' ? 'MW' : 'kW')
		.attr('text-anchor', 'start')
	return 'PGXAxis.vue'
})
const drawAxis2 = computed(() => {
	let axis = select<AxisContainerElement, number>('g#PGXAxis2')
	axis.selectAll('*').remove()

	if (graphData.graphMode == 'month' || graphData.graphMode == 'year') {
		axis.call(xAxisGeneratorMonth2.value)
	} else {
		axis.call(xAxisGenerator2.value)
	}

	axis
		.selectAll('.tick > text')
		//.attr('color', 'var(--color-axis)')
		.attr('fill', (d, i) =>
			i >= 0 || graphData.graphMode == 'month' || graphData.graphMode == 'year'
				? 'var(--color-axis)'
				: 'var(--color-bg)',
		)
		.attr('font-size', fontsize)

	if (globalConfig.showGrid) {
		axis
			.selectAll('.tick line')
			.attr('stroke', 'var(--color-grid)')
			.attr('stroke-width', '0.5')
		axis.select('.domain').attr('stroke', 'var(--color-bg)')
	} else {
		axis.selectAll('.tick line').attr('stroke', 'var(--color-bg)')
	}

	axis.select('.domain').attr('stroke', 'var(--color-bg)')

	return 'PGXAxis2.vue'
})

const autozoom = computed(() => {
	if (graphData.graphMode != 'month' && graphData.graphMode != 'year') {
		const axis: Selection<SVGGElement, unknown, HTMLElement, unknown> =
			select('g#PGXAxis')
		const axis2: Selection<SVGGElement, unknown, HTMLElement, unknown> =
			select('g#PGXAxis2')

		if (graphData.graphMode == 'month' || graphData.graphMode == 'year') {
			xScaleMonth.value.range(zoomedRange.value)
			axis.call(xAxisGeneratorMonth.value)
			axis2.call(xAxisGeneratorMonth2.value)
		} else {
			xScale.value.range(zoomedRange.value)
			axis.call(xAxisGenerator.value)
			axis2.call(xAxisGenerator2.value)
		}
	}

	return 'zoomed'
})
</script>

<style></style>
