<template>
	<g>
		<defs>
			<filter id="f1">
				<feDropShadow
					dx="1"
					dy="1"
					rx="10"
					ry="10"
					stdDeviation="1"
					flood-opacity="0.7"
					flood-color="var(--color-axis)"
				/>
			</filter>
		</defs>
	</g>
	<g
		v-for="(consumer, i) in pieGenerator(
			props.plotdata.filter((v) => v.power != 0),
		)"
		:key="consumer.data.name"
	>
		<path
			:d="path(consumer)!"
			:fill="consumer.data.color"
			:stroke="strokeColor(consumer, i)"
		/>
	</g>
	<g v-if="props.showLabels">
		<g
			v-for="consumer in pieGenerator(plotdata.filter((v) => v.power != 0))"
			:key="consumer.data.name"
			:transform="'translate(' + path.centroid(consumer) + ')'"
		>
			<PMPopup
				v-if="categoriesToShow.includes(consumer.data.type)"
				:consumer="consumer.data"
			/>
		</g>
	</g>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { type PieArcDatum, arc, pie } from 'd3'
import { PowerItemType, type PowerItem } from '@/assets/js/types'
import PMPopup from './PMPopup.vue'

const props = defineProps<{
	upperArc: boolean
	plotdata: PowerItem[]
	radius: number
	showLabels: boolean
	categoriesToShow: PowerItemType[]
}>()

const cornerRadius = 20
const circleGapSize = Math.PI / 40
const arcCount = computed(() => props.plotdata.length - 1)
const pieGenerator = computed(() =>
	props.upperArc
		? pie<PowerItem>()
				.value((record: PowerItem) => Math.abs(record.power))
				.startAngle(-Math.PI / 2 + circleGapSize)
				.endAngle(Math.PI / 2 - circleGapSize)
				.sort(null)
		: pie<PowerItem>()
				.value((record: PowerItem) => record.power)
				.startAngle(Math.PI * 1.5 - circleGapSize)
				.endAngle(Math.PI / 2 + circleGapSize)
				.sort(null),
)
const path = computed(() =>
	arc<PieArcDatum<PowerItem>>()
		//.innerRadius((props.radius / 6) * 5)
		.innerRadius(props.radius * 0.88)
		.outerRadius(props.radius)
		.cornerRadius(cornerRadius),
)
function strokeColor(d: PieArcDatum<PowerItem>, i: number): string {
	return i == arcCount.value
		? d.data.power > 0
			? 'var(--color-scale)'
			: 'null'
		: d.data.color
}
</script>
<style scoped></style>
