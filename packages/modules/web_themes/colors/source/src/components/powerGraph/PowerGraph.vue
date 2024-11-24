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
				<span
					v-if="widescreen"
					type="button"
					class="ms-1 p-0 pt-1"
					@click="zoomGraph"
				>
					<span class="fa-solid fa-lg ps-1 fa-magnifying-glass" />
				</span>
			</div>
		</template>

		<figure v-show="graphData.data.length > 0" id="powergraph" class="p-0 m-0">
			<svg id="powergraph" :viewBox="'0 0 ' + width + ' ' + height">
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
					:width="width - margin.left - 2 * margin.right"
					:height="height - margin.top - margin.bottom"
					:margin="margin"
					:graph-data="graphData"
				/>
				<g :transform="'translate(' + margin.left + ',' + margin.top + ')'">
					<PgSoc
						v-if="
							(graphData.graphMode == 'day' ||
								graphData.graphMode == 'today' ||
								graphData.graphMode == 'live') &&
							Object.values(vehicles).filter((v) => v.visible).length > 0
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
							Object.values(vehicles).filter((v) => v.visible).length > 1
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
				<g id="button" type="button" @click="changeStackOrder">
					<text
						:x="width - 10"
						:y="height - 10"
						color="var(--color-menu)"
						text-anchor="end"
					>
						<tspan fill="var(--color-menu)" class="fas fa-lg">
							{{ '\uf0dc' }}
						</tspan>
					</text>
				</g>
			</svg>
		</figure>
	</WBWidget>
</template>

<script setup lang="ts">
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
import { globalConfig, widescreen } from '@/assets/js/themeConfig'
import PgSoc from './PgSoc.vue'
import PgSocAxis from './PgSocAxis.vue'
import { vehicles } from '../chargePointList/model'
import PgSelector from './PgSelector.vue'
import { zoom, type D3ZoomEvent, type Selection, select } from 'd3'
import { onMounted } from 'vue'
import PgToolTips from './PgToolTips.vue'

// state
const stackOrderMax = 2
const heading = 'Leistung / Ladestand '
function changeStackOrder() {
	let newOrder = globalConfig.usageStackOrder + 1
	if (newOrder > stackOrderMax) {
		newOrder = 0
	}
	globalConfig.usageStackOrder = newOrder
	setInitializeUsageGraph(true)
}
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

// callback that is called when the user tries to pan/zoom in the window
function zoomed(event: D3ZoomEvent<SVGGElement, unknown>) {
	mytransform.value = event.transform
}

// prevent scrolling then apply the default filter
function filter(event: PointerEvent | WheelEvent) {
	event.preventDefault()
	return (!event.ctrlKey || event.type === 'wheel') && !event.button
}

function zoomGraph() {
	globalConfig.zoomedWidget = 1
	globalConfig.zoomGraph = !globalConfig.zoomGraph
}

onMounted(() => {
	const svg = select<Element, unknown>('svg#powergraph')
	setZoom(svg)
})
</script>

<style scoped>
.fa-magnifying-glass {
	color: var(--color-menu);
}

.dateWbBadge {
	background-color: var(--color-menu);
	color: var(--color-bg);
	font-size: var(--font-medium);
	font-weight: normal;
}

.waitsign {
	text-align: center;
	font-size: var(--font-medium);
	color: var(--color-fg);
	border: 1px solid var(--color-bg);
	padding: 2em;
	margin: 2em;
	margin-top: 4em;
	background-color: var(--color-bg);
}
</style>
