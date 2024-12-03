<template>
	<g id="emBargraph">
		<!-- Bars -->
		<g v-for="(item, i) in props.plotdata" :key="i">
			<EnergyBar
				:id="i.toString()"
				:item="item"
				:x-scale="props.xscale"
				:y-scale="props.yscale"
				:item-height="itemHeight"
			/>
		</g>
	</g>
</template>

<script setup lang="ts">
import * as d3 from 'd3'
import type { PowerItem } from '@/assets/js/types'
import EnergyBar from './EnergyBar.vue'

const props = defineProps<{
	plotdata: PowerItem[]
	yscale: d3.ScaleBand<string>
	xscale: d3.ScaleLinear<number, number, never>
	itemHeight: number
}>()
</script>

<style></style>
