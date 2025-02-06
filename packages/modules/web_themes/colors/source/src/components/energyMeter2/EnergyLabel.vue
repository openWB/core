<template>
	<g :id="'barlabel-' + props.item.name">
		<!-- Name-Icon -->
		<text
			:y="
				props.height -
				(props.yscale(item.name) as number) -
				props.margin.bottom -
				60
			"
			:x="props.margin.left"
			:font-size="labelfontsize"
			text-anchor="start"
			:fill="item.color"
			:class="item.icon.length <= 2 ? 'fas' : ''"
		>
			{{ item.icon }}
		</text>
		<!-- Energy -->
		<text
			:y="
				props.height -
				(props.yscale(item.name) as number) -
				props.margin.bottom -
				60
			"
			:x="props.width / 2 + props.margin.left"
			:font-size="labelfontsize"
			text-anchor="middle"
			fill="var(--color-menu)"
		>
			{{
				formatWattH(
					item.energy,
					globalConfig.decimalPlaces,
					//graphData.graphMode == 'year',
					false,
				)
			}}
		</text>
		<!-- Autarchy / Self consumption -->
		<text
			:y="
				props.height -
				(props.yscale(item.name) as number) -
				props.margin.bottom -
				60
			"
			:x="props.width - props.margin.right"
			:font-size="labelfontsize - 2"
			text-anchor="end"
			:fill="subColor()"
		>
			{{ subString() }}
		</text>
	</g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as d3 from 'd3'
import type { MarginType, PowerItem } from '@/assets/js/types'
import { globalConfig } from '@/assets/js/themeConfig'
import { formatWattH } from '@/assets/js/helpers'

const props = defineProps<{
	item: PowerItem
	xscale: d3.ScaleLinear<number, number, never>
	yscale: d3.ScaleBand<string>
	margin: MarginType
	height: number
	width: number
	barcount: number
	autarchy?: number
	autText?: string
}>()
/* const labelY = computed(() =>
	props.autarchy
		? props.xscale(props.item.energy) - 25
		: props.xscale(props.item.energy) - 10,
) */

const labelfontsize = computed(() => {
	/* let fontsize = 16
	let xCount = props.barcount
	if (xCount <= 5) {
		fontsize = 16
	} else if (xCount == 6) {
		fontsize = 14
	} else if (xCount > 6 && xCount <= 8) {
		fontsize = 13
	} else if (xCount == 9) {
		fontsize = 11
	} else if (xCount == 10) {
		fontsize = 10
	} else {
		fontsize = 9
	} */
	//return fontsize
	return 24
})
/* const maxTextLength = computed(() => {
	let textLength = 12
	let xCount = props.barcount
	if (xCount <= 5) {
		textLength = 12
	} else if (xCount == 6) {
		textLength = 11
	} else if (xCount > 6 && xCount <= 8) {
		textLength = 8
	} else if (xCount == 9) {
		textLength = 8
	} else if (xCount == 10) {
		textLength = 7
	} else {
		textLength = 6
	}
	return textLength
}) */
/* function truncateCategory(id: string, name: string) {
	if (name.length > maxTextLength.value) {
		return name.substring(0, maxTextLength.value) + '.'
	} else {
		return name
	}
} */
function subString(): string {
	if (props.autarchy) {
		return (
			props.autText + ': ' + props.autarchy.toLocaleString(undefined) + ' %'
		)
	} else {
		return ''
	}
}
function subColor(): string {
	return 'var(--color-pv)'
}
</script>

<style scoped></style>
