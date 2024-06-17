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
						>Energie heute: {{ formatWattH(item.energy) }}
					</tspan>
					<tspan v-if="(props.autarchy ?? 0) > 0" x="25" dy="1.3em"
						>Autarkie: {{ props.autarchy ?? 0 }} %</tspan
					>
					<tspan v-if="item.energyPv > 0" x="30" dy="1.3em"
						>PV: {{ formatWatt(item.energyPv) }}</tspan
					>
					<tspan v-if="item.energyBat > 0" x="30" dy="1.3em"
						>Speicher: {{ formatWatt(item.energyBat) }}</tspan
					>
					<tspan x="25" dy="1.3em"
						>Aktuelle Leistung: {{ formatWatt(item.power) }}</tspan
					>
				</text>
			</g>
		</g>
		<!-- const ttips = svg
		.selectAll('ttip')
		.data(plotdata.value)
		.enter()
		.append('g')
		.attr('class', 'ttarea')
	ttips
		.append('rect')
		.attr('x', (d) => xScale.value(d[0]))
		.attr('y', (d) => yScale.value(d[1]))
		.attr('height', (d) => yScale.value(yDomain.value[0]) - yScale.value(d[1]))
		.attr('class', 'ttrect')
		.attr('width', barwidth.value)
		.attr('opacity', '1%')
		.attr('fill', 'var(--color-charging)')
	const tt = ttips
		.append('g')
		.attr('class', 'ttmessage')
		.attr(
			'transform',
			(d) =>
				'translate(' +
				(xScale.value(d[0]) - 30 + barwidth.value / 2) +
				',' +
				(yScale.value(d[1]) - 18) +
				')',
		)
	tt.append('rect')
		.attr('rx', 5)
		.attr('width', '60')
		.attr('height', '30')
		.attr('fill', 'var(--color-menu)')
	const texts = tt
		.append('text')
		.attr('text-anchor', 'middle')
		.attr('x', 30)
		.attr('y', 12)
		.attr('font-size', axisfontsize)
		.attr('fill', 'var(--color-bg)')
	texts
		.append('tspan')
		.attr('x', 30)
		.attr('dy', '0em')
		.text((d) => timeFormat('%H:%M')(d[0]))
	texts
		.append('tspan')
		.attr('x', 30)
		.attr('dy', '1.1em')
		.text((d) => Math.round(d[1] * 10) / 10 + ' ct') -->
	</g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as d3 from 'd3'
import type { MarginType, PowerItem } from '@/assets/js/types'
import { formatWatt, formatWattH } from '@/assets/js/helpers'

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
		props.yScale(props.item.energy) -
		props.margin.top -
		props.margin.bottom,
)
</script>
