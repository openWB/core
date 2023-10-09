<template>
	<WBWidget :full-width="true">
		<template #title>
			{{ heading }}
		</template>
		<template #buttons>
			<PgSelector
				widgetid="graphsettings"
				:show-left-button="true"
				:show-right-button="true"
				@shift-left="shiftLeft"
				@shift-right="shiftRight"
				@shift-up="shiftUp"
				@shift-down="shiftDown"
			/>
		</template>

		<figure id="powergraph" class="p-0 m-0" @click="changeStackOrder">
			<svg :viewBox="'0 0 ' + width + ' ' + height">
				<!-- Draw the source graph -->
				<PGSourceGraph
					:width="width - margin.left - 2 * margin.right"
					:height="(height - margin.top - margin.bottom) / 2"
					:margin="margin"
				/>
				<PGUsageGraph
					:width="width - margin.left - 2 * margin.right"
					:height="(height - margin.top - margin.bottom) / 2"
					:margin="margin"
					:stack-order="globalConfig.usageStackOrder"
				/>
				<PGXAxis
					:width="width - margin.left - 2 * margin.right"
					:height="height - margin.top - margin.bottom"
					:margin="margin"
					:graph-data="graphData"
				/>
				<g :transform="'translate(' + margin.left + ',' + margin.top + ')'">
					<PgSoc
						v-if="
							(graphData.graphMode == 'day' ||
								graphData.graphMode == 'today') &&
							Object.values(vehicles).length > 0
						"
						:width="width - margin.left - 2 * margin.right"
						:height="(height - margin.top - margin.bottom) / 2"
						:margin="margin"
						:order="0"
					/>
					<PgSoc
						v-if="
							(graphData.graphMode == 'day' ||
								graphData.graphMode == 'today') &&
							Object.values(vehicles).length > 1
						"
						:width="width - margin.left - 2 * margin.right"
						:height="(height - margin.top - margin.bottom) / 2"
						:margin="margin"
						:order="1"
					/>
					<PgSocAxis
						v-if="
							graphData.graphMode == 'day' || graphData.graphMode == 'today'
						"
						:width="width - margin.left - margin.right"
						:height="(height - margin.top - margin.bottom) / 2"
						:margin="margin"
					/>
				</g>
				<g id="button">
					<text
						:x="width"
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
import PGSourceGraph from './PGSourceGraph.vue'
import PGUsageGraph from './PGUsageGraph.vue'
import PGXAxis from './PGXAxis.vue'
import {
	graphData,
	setInitializeUsageGraph,
	shiftLeft,
	shiftRight,
	shiftUp,
	shiftDown,
} from './model'
import { globalConfig } from '@/assets/js/themeConfig'
import PgSoc from './PgSoc.vue'
import PgSocAxis from './PgSocAxis.vue'
import { vehicles } from '../chargePointList/model'
import PgSelector from './PgSelector.vue'

// state
const width = 500
const height = 500
const margin = { top: 10, right: 20, bottom: 10, left: 25 }
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
