<template>
	<g id="emBargraph">
		<!-- Bars -->
		<g v-for="(item, i) in props.plotdata" :key="i">
			<EmBar
				:id="i.toString()"
				:item="item"
				:x-scale="props.xScale"
				:y-scale="props.yScale"
				:margin="props.margin"
				:height="props.height"
			/>
		</g>
		<animateTransform
			attribute-name="transform"
			type="scale"
			from="1 0"
			to="1 1"
			begin="0s"
			dur="2s"
		/>
	</g>
</template>

<script setup lang="ts">
import * as d3 from 'd3'
import type { MarginType, PowerItem } from '@/assets/js/types'
import EmBar from './EmBar.vue'
const props = defineProps<{
	plotdata: PowerItem[]
	xScale: d3.ScaleBand<string>
	yScale: d3.ScaleLinear<number, number, never>
	margin: MarginType
	height: number
}>()

// computed: {
</script>

<style></style>
