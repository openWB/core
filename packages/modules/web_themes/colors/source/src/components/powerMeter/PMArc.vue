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
	<g v-if="globalConfig.showRelativeArcs">
		<path
			:d="pathFrame(0)!"
			fill="var(--color-bg)"
			stroke="var(--color-menu)"
		/>
	</g>
	<g
		v-for="consumer in pieGenerator(props.plotdata.filter((v) => v.power != 0))"
		:key="consumer.data.name"
	>
		<path
			v-if="consumer.data.name != 'empty'"
			:d="path(consumer)!"
			:fill="consumer.data.color"
			:stroke="strokeColor(consumer)"
		/>
	</g>
	<g v-if="globalConfig.showPmLabels">
		<g
			v-for="consumer in pieGenerator(plotdata.filter((v) => v.power != 0))"
			:key="consumer.data.name"
			:transform="'translate(' + path.centroid(consumer) + ')'"
		>
			<PMPopup
				v-if="
					categoriesToShow.includes(consumer.data.type) &&
					Math.abs(consumer.data.power) / summarizedPower > 0.06 &&
					consumer.data.name != 'empty'
				"
				:consumer="consumer.data"
			/>
		</g>
	</g>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { type PieArcDatum, arc, pie } from 'd3'
import { PowerItemType, type PowerItem } from '@/assets/js/types'
import { globalConfig } from '@/assets/js/themeConfig'
import PMPopup from './PMPopup.vue'

const props = defineProps<{
	upperArc: boolean
	plotdata: PowerItem[]
	radius: number
	categoriesToShow: PowerItemType[]
}>()
const cornerRadius = computed(() => (globalConfig.showRelativeArcs ? 0 : 10))
// const cornerRadius = 10
const circleGapSize = Math.PI / 40
//const arcCount = computed(() => props.plotdata.filter (d => d.power !=0).length - 1)
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
		.innerRadius(props.radius * 0.87)
		.outerRadius(props.radius)
		.cornerRadius(cornerRadius.value),
)

var pathFrame = arc<number>()
	.startAngle(
		props.upperArc
			? -Math.PI / 2 + circleGapSize
			: Math.PI * 1.5 - circleGapSize,
	)
	.endAngle(
		props.upperArc ? Math.PI / 2 - circleGapSize : Math.PI / 2 + circleGapSize,
	)
	.innerRadius(props.radius * 0.87)
	.outerRadius(props.radius)
	.cornerRadius(0)

function strokeColor(d: PieArcDatum<PowerItem>): string {
	return d.data.name == 'empty'
		? d.data.power > 0
			? 'var(--color-scale)'
			: 'null'
		: d.data.color
}
const summarizedPower = computed(() => {
	return props.plotdata.reduce((sum, item) => sum + Math.abs(item.power), 0)
})
</script>
<style scoped></style>
