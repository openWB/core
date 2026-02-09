<template>
	<g
		:id="'bartooltip-' + props.item.name"
		transform="scale(1,-1) translate (0,-445)"
	>
		<!-- Tooltips -->
		<g class="ttarea">
			<rect
				class="ttrect"
				:x="props.xScale(item.name)"
				y="0"
				:width="props.xScale.bandwidth()"
				:height="barheight"
				:fill="item.color"
				opacity="1%"
			></rect>
			<g class="ttmessage" transform="scale (1,-1) translate(90,-345)">
				<rect
					class="popupbox"
					rx="5"
					width="300"
					height="190"
					fill="var(--color-input)"
				></rect>
				<text
					text-anchor="start"
					font-size="16pt"
					fill="var(--color-bg)"
					x="180"
					y="30"
				>
					<tspan
						v-if="item.icon.length <= 2"
						class="fas"
						x="25"
						:fill="item.color"
						>{{ item.icon }}
					</tspan>
					<tspan
						v-if="item.icon.length > 2"
						class="fas"
						x="25"
						:fill="item.color"
						>{{ '\uf0e7' }}
					</tspan>

					<tspan font-weight="bold" dx="5" :fill="item.color">{{
						item.name
					}}</tspan>
					<tspan x="25" dy="1.5em"
						>Energie heute: {{ formatWattH(item[graphScope].energy) }}
					</tspan>
					<tspan v-if="(props.autarchy ?? 0) > 0" x="25" dy="1.3em"
						>Autarkie: {{ props.autarchy ?? 0 }} %</tspan
					>
					<tspan v-if="item[graphScope].energyPv > 0" x="30" dy="1.3em"
						>PV: {{ formatWatt(item[graphScope].energyPv) }}</tspan
					>
					<tspan v-if="item[graphScope].energyBat > 0" x="30" dy="1.3em"
						>Speicher: {{ formatWatt(item[graphScope].energyBat) }}</tspan
					>
					<tspan x="25" dy="1.3em"
						>Aktuelle Leistung: {{ formatWatt(item.power) }}</tspan
					>
				</text>
			</g>
		</g>
	</g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as d3 from 'd3'
import type { MarginType, PowerItem } from '@/assets/js/types'
import { formatWatt, formatWattH } from '@/assets/js/helpers'
import { graphData } from '../powerGraph/model'

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
const barheight = computed(
	() =>
		props.height -
		props.yScale(props.item[graphScope.value].energy) -
		props.margin.top -
		props.margin.bottom,
)
const graphScope = computed(() => (graphData.usePastData ? 'past' : 'now'))
</script>
