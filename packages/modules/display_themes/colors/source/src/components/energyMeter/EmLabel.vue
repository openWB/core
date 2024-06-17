<template>
	<g :id="'barlabel-' + props.item.name">
		<!-- Energy -->
		<text
			:x="(props.xScale(item.name) as number) + props.xScale.bandwidth() / 2"
			:y="labelY"
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
			:x="(props.xScale(item.name) as number) + props.xScale.bandwidth() / 2"
			:y="props.yScale(item.energy) - 10"
			:font-size="labelfontsize - 2"
			text-anchor="middle"
			:fill="subColor()"
		>
			{{ subString() }}
		</text>
		<!-- Name-Icon -->
		<text
			:x="(props.xScale(item.name) as number) + props.xScale.bandwidth() / 2"
			:y="props.height - props.margin.bottom - 5"
			:font-size="labelfontsize"
			text-anchor="middle"
			:fill="item.color"
			:class="item.icon.length <= 2 ? 'fas' : ''"
		>
			{{ truncateCategory(item.name, item.icon) }}
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
	xScale: d3.ScaleBand<string>
	yScale: d3.ScaleLinear<number, number, never>
	margin: MarginType
	height: number
	barcount: number
	autarchy?: number
	autText?: string
}>()
const labelY = computed(() =>
	props.autarchy
		? props.yScale(props.item.energy) - 25
		: props.yScale(props.item.energy) - 10,
)

const labelfontsize = computed(() => {
	let fontsize = 16
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
	}
	return fontsize
})
const maxTextLength = computed(() => {
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
})
function truncateCategory(id: string, name: string) {
	if (name.length > maxTextLength.value) {
		return name.substring(0, maxTextLength.value) + '.'
	} else {
		return name
	}
}
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
