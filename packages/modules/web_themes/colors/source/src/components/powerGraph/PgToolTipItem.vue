<template>
	<g class="ttmessage" :transform="'translate(' + xScale(entry.date) + ',0)'">
		<rect
			rx="5"
			:width="boxwidth"
			:height="height()"
			fill="var(--color-bg)"
			opacity="90%"
			stroke="var(--color-menu)"
		/>
		<text
			text-anchor="start"
			x="5"
			y="20"
			font-size="16"
			fill="var(--color-fg)"
		>
			<tspan text-anchor="middle" :x="boxwidth / 2" dy="0em">{{
				timeFormat('%H:%M')(new Date(entry.date))
			}}</tspan>
			<line y="120" x1="5" x2="100" stroke="var(--color-fg)" stroke-width="1" />
			<PgToolTipLine
				cat="evuIn"
				:indent="5"
				:power="entry.evuIn"
				:width="boxwidth"
			/>
			<PgToolTipLine
				cat="batOut"
				:indent="5"
				:power="entry.batOut"
				:width="boxwidth"
			/>
			<PgToolTipLine cat="pv" :indent="5" :power="entry.pv" :width="boxwidth" />
			<PgToolTipLine
				v-for="pv in pvs()"
				:key="pv.id"
				cat="pv"
				:name="pv.name"
				:power="pv.power"
				:indent="10"
				:width="boxwidth"
			/>
			<PgToolTipLine
				cat="house"
				:indent="5"
				:power="entry.house"
				:width="boxwidth"
			/>
			<PgToolTipLine
				cat="charging"
				:indent="5"
				:power="entry.charging"
				:width="boxwidth"
			/>
			<PgToolTipLine
				v-for="cp in cps()"
				:key="cp.id"
				cat="charging"
				:name="cp.name"
				:power="cp.power"
				:indent="10"
				:width="boxwidth"
			/>
			<PgToolTipLine
				cat="devices"
				:indent="5"
				:power="entry.devices"
				:width="boxwidth"
			/>
			<PgToolTipLine
				v-for="dev in devs()"
				:key="dev.id"
				cat="devices"
				:name="dev.name"
				:power="dev.power"
				:indent="10"
				:width="boxwidth"
			/>
			<PgToolTipLine
				cat="counters"
				:indent="5"
				:power="entry.counters"
				:width="boxwidth"
			/>
			<PgToolTipLine
				v-for="ctr in counters()"
				:key="ctr.id"
				cat="counters"
				:name="ctr.name"
				:power="ctr.power"
				:indent="10"
				:width="boxwidth"
			/>
			<PgToolTipLine
				cat="batIn"
				:indent="5"
				:power="entry.batIn"
				:width="boxwidth"
			/>
			<PgToolTipLine
				cat="evuOut"
				:indent="5"
				:power="entry.evuOut"
				:width="boxwidth"
			/>
		</text>
	</g>
</template>

<script setup lang="ts">
import { itemNames, type GraphDataItem } from './model'
import type { ScaleTime } from 'd3'
import { timeFormat } from 'd3'
import PgToolTipLine from './PgToolTipLine.vue'

const props = defineProps<{
	entry: GraphDataItem
	boxwidth: number
	xScale: ScaleTime<number, number>
}>()

//function linecount() {
//	return Object.values(props.entry).filter((v) => v > 0).length
//}
function height() {
	return Object.values(props.entry).filter((v) => v > 0).length * 18 + 40
}
function pvs() {
	return Object.entries(props.entry)
		.filter(([k, v]) => k.startsWith('pv') && k.length > 2 && v > 0)
		.map(([k, v]) => {
			return {
				power: v,
				name: itemNames.value.get(k)
					? trimName(itemNames.value.get(k)!)
					: 'Wechselr.',
				id: k,
			}
		})
}
function cps() {
	return Object.entries(props.entry)
		.filter(([k, v]) => k.startsWith('cp') && k.length > 2 && v > 0)
		.map(([k, v]) => {
			return {
				power: v,
				name: itemNames.value.get(k)
					? trimName(itemNames.value.get(k)!)
					: 'Ladep.',
				id: k,
			}
		})
}
function devs() {
	return Object.entries(props.entry)
		.filter(([k, v]) => k.startsWith('sh') && k.length > 2 && v > 0)
		.map(([k, v]) => {
			return {
				power: v,
				name: itemNames.value.get(k)
					? trimName(itemNames.value.get(k)!)
					: 'Gerät',
				id: k,
			}
		})
}
function counters() {
	return Object.entries(props.entry)
		.filter(
			([k, v]) =>
				k.startsWith('counter') && k != 'counters' && k.length > 2 && v > 0,
		)
		.map(([k, v]) => {
			return {
				power: v,
				name: itemNames.value.get(k)
					? trimName(itemNames.value.get(k)!)
					: 'Zähler',
				id: k,
			}
		})
}
function trimName(name: string) {
	if (name.length > 6) {
		return name.slice(0, 6) + '...'
	}
	return name
}
</script>
<style scoped lang="ts"></style>
