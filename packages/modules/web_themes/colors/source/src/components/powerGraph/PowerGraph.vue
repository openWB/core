<template>
	<WBWidget :full-width="true">
		<template #title>
			{{ heading }}
		</template>
		<template #buttons>
			<div class="d-flex justify-content-end">
				<PgSelector
					widgetid="graphsettings"
					:show-left-button="true"
					:show-right-button="true"
					:ignore-live="false"
					@shift-left="shiftLeft"
					@shift-right="shiftRight"
					@shift-up="shiftUp"
					@shift-down="shiftDown"
				/>
				<span type="button" class="ms-1 p-0 pt-1" @click="changeStackOrder">
					<span class="fa-solid fa-lg ps-1 fa-sort" />
				</span>
				<span
					v-if="widescreen"
					type="button"
					class="ms-1 p-0 pt-1"
					@click="zoomGraph"
				>
					<span class="fa-solid fa-lg ps-1" :class="zoomIcon()" />
				</span>
			</div>
		</template>

		<figure
			v-show="graphData.data.length > 0"
			id="powergraphFigure"
			class="p-0 m-0"
		>
			<svg
				id="powergraph"
				class="powergraphSvg"
				:viewBox="'0 0 ' + width + ' ' + height"
			>
				<!-- Draw the source graph -->
				<PgSourceGraph
					:width="width - margin.left - 2 * margin.right"
					:height="(height - margin.top - margin.bottom) / 2"
					:margin="margin"
				/>
				<PgUsageGraph
					:width="width - margin.left - 2 * margin.right"
					:height="(height - margin.top - margin.bottom) / 2"
					:margin="margin"
					:stack-order="globalConfig.usageStackOrder"
				/>
				<PgXAxis
					:width="width"
					:height="height - margin.top - margin.bottom"
					:margin="margin"
				/>
				<g :transform="'translate(' + margin.left + ',' + margin.top + ')'">
					<PgSoc
						v-if="
							(graphData.graphMode == 'day' ||
								graphData.graphMode == 'today' ||
								graphData.graphMode == 'live') &&
							vehicles[topVehicles[0]] != undefined &&
							vehicles[topVehicles[0]].isSocConfigured
						"
						:width="width - margin.left - 2 * margin.right"
						:height="(height - margin.top - margin.bottom) / 2"
						:margin="margin"
						:order="0"
					/>
					<PgSoc
						v-if="
							(graphData.graphMode == 'day' ||
								graphData.graphMode == 'today' ||
								graphData.graphMode == 'live') &&
							vehicles[topVehicles[1]] != undefined &&
							vehicles[topVehicles[1]].isSocConfigured
						"
						:width="width - margin.left - 2 * margin.right"
						:height="(height - margin.top - margin.bottom) / 2"
						:margin="margin"
						:order="1"
					/>
					<PgSoc
						v-if="
							(graphData.graphMode == 'day' ||
								graphData.graphMode == 'today' ||
								graphData.graphMode == 'live') &&
							globalData.isBatteryConfigured
						"
						:width="width - margin.left - 2 * margin.right"
						:height="(height - margin.top - margin.bottom) / 2"
						:margin="margin"
						:order="2"
					/>
					<PriceLine
						v-if="
							globalConfig.showPrices &&
							(graphData.graphMode == 'day' || graphData.graphMode == 'today')
						"
						:width="width - margin.left - 2 * margin.right"
						:height="(height - margin.top - margin.bottom) / 2"
						:margin="margin"
					/>

					<PgSocAxis
						v-if="
							graphData.graphMode == 'day' ||
							graphData.graphMode == 'today' ||
							graphData.graphMode == 'live'
						"
						:width="width - margin.left - margin.right"
						:height="(height - margin.top - margin.bottom) / 2"
						:margin="margin"
					/>
				</g>
				<PgToolTips
					v-if="graphData.graphMode == 'day' || graphData.graphMode == 'today'"
					:width="width - margin.left - margin.right"
					:height="height - margin.top - margin.bottom"
					:margin="margin"
					:data="graphData.data"
				></PgToolTips>
			</svg>
		</figure>
	</WBWidget>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import WBWidget from '../shared/WBWidget.vue'
import PgSourceGraph from './PgSourceGraph.vue'
import PgUsageGraph from './PgUsageGraph.vue'
import PgXAxis from './PgXAxis.vue'
import { globalData } from '@/assets/js/model'
import {
	graphData,
	setInitializeUsageGraph,
	shiftLeft,
	shiftRight,
	shiftUp,
	shiftDown,
	width,
	height,
	margin,
	mytransform,
} from './model'
import { onMounted } from 'vue'
import { zoom, type D3ZoomEvent, type Selection, select } from 'd3'
import { globalConfig, widescreen } from '@/assets/js/themeConfig'
import { topVehicles, vehicles } from '../chargePointList/model'
import PgSoc from './PgSoc.vue'
import PgSocAxis from './PgSocAxis.vue'
import PgSelector from './PgSelector.vue'
import PgToolTips from './PgToolTips.vue'
import PriceLine from './PriceLine.vue'

// state
const stackOrderMax = 2
const heading = computed(() => {
	switch (graphData.graphMode) {
		case 'year':
			return 'Jahresübersicht'
		case 'month':
			return 'Monatsübersicht'
		default:
			return 'Verlauf'
	}
})
/**
 * Changes the stack order for usage graph visualization
 * Cycles through available stack orders (0 to stackOrderMax)
 * Triggers usage graph reinitialization after change
 */
function changeStackOrder() {
	let newOrder = globalConfig.usageStackOrder + 1
	if (newOrder > stackOrderMax) {
		newOrder = 0
	}
	globalConfig.usageStackOrder = newOrder
	setInitializeUsageGraph(true)
}

/**
 * Configures zoom behavior for the power graph SVG
 * @param svg - D3 Selection of the SVG element to apply zoom to
 */
function setZoom(svg: Selection<Element, unknown, HTMLElement, unknown>) {
	const myextent: [[number, number], [number, number]] = [
		[0, margin.top],
		[width, height - margin.top],
	]
	svg.call(
		zoom<Element, unknown>()
			.scaleExtent([1, 8])
			.translateExtent([
				[0, 0],
				[width, height],
			])
			.extent(myextent)
			.filter(filter)
			.on('zoom', zoomed),
	)
}

/**
 * Handles zoom events on the graph
 * Updates the transform value used for rendering
 * @param event - D3 zoom event containing transform information
 */
function zoomed(event: D3ZoomEvent<SVGGElement, unknown>) {
	mytransform.value = event.transform
}

/**
 * Filters zoom/pan events to control graph interaction
 * Prevents default scroll behavior and applies zoom constraints
 * @param event - Browser pointer or wheel event
 * @returns boolean indicating if the event should trigger zoom
 */
function filter(event: PointerEvent | WheelEvent) {
	event.preventDefault()
	return (!event.ctrlKey || event.type === 'wheel') && !event.button
}

/**
 * Toggles the zoom state of the graph
 * Sets the current widget as active and toggles zoom mode
 */
function zoomGraph() {
	globalConfig.zoomedWidget = 1
	globalConfig.zoomGraph = !globalConfig.zoomGraph
}
function zoomIcon() {
	return globalConfig.zoomGraph ? 'fa-minimize' : 'fa-maximize'
}
onMounted(() => {
	const svg = select<Element, unknown>('svg#powergraph')
	setZoom(svg)
})
</script>

<style scoped>
.fa-maximize {
	color: var(--color-menu);
}
.fa-minimize {
	color: var(--color-charging);
}
.fa-sort {
	color: var(--color-menu);
}
</style>
