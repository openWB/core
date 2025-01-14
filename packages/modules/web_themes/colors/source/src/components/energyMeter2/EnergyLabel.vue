<template>
	<g :id="'barlabel-' + props.id">
		<!-- Name-Icon -->
		<text
			:y="yPos"
			:x="props.margin.left"
			:font-size="labelfontsize"
			text-anchor="start"
			:fill="item.color"
			:class="item.icon.length <= 2 ? 'fas' : ''"
		>
			{{ trimName(props.item.icon) }}
		</text>
		<!-- Energy -->
		<text
			:y="yPos"
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
			:y="yPos"
			:x="props.width - props.margin.right"
			:font-size="labelfontsize - 2"
			text-anchor="end"
			fill="var(--color-pv)"
		>
			{{ autString() }}
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
	id: string
	item: PowerItem
	yscale: d3.ScaleBand<string>
	margin: MarginType
	width: number
	itemHeight: number
	autarchy?: number
	autText?: string
}>()

const labelfontsize = 24

const yPos = computed(() => {
	return (props.yscale(props.id)! as number) + props.itemHeight / 3
})

function autString(): string {
	if (props.autarchy) {
		return (
			props.autText + ': ' + props.autarchy.toLocaleString(undefined) + ' %'
		)
	} else {
		return ''
	}
}

function trimName(name: string) {
	const maxlen = 14
	return name.length > maxlen ? name.slice(0, maxlen - 1) + '...' : name
}
</script>

<style scoped></style>
