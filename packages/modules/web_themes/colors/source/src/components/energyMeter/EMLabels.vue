<template>
	<g id="emBarLabels">
		<!-- Bars -->
		<g v-for="(item, i) in props.plotdata" :key="i">
			<EmLabel
				:id="i.toString()"
				:item="item"
				:x-scale="props.xScale"
				:y-scale="props.yScale"
				:margin="props.margin"
				:height="props.height"
				:barcount="props.plotdata.length"
				:aut-text="autTxt(item)"
				:autarchy="autPct(item)"
			/>
		</g>
	</g>
</template>

<script setup lang="ts">
import * as d3 from 'd3'
import EmLabel from './EmLabel.vue'
import type { MarginType, PowerItem } from '@/assets/js/types'
import { autPct } from './model'
const props = defineProps<{
	plotdata: PowerItem[]
	xScale: d3.ScaleBand<string>
	yScale: d3.ScaleLinear<number, number>
	height: number
	margin: MarginType
}>()
// computed
// methods

function autTxt(item: PowerItem) {
	if (item.name == 'PV') {
		return 'Eigen'
	} else {
		return 'Aut'
	}
}
</script>

<style></style>
