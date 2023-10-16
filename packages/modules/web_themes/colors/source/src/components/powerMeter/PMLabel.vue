<template>
	<g v-if="showMe" id="pmLabel">
		<text
			:x="x"
			:y="y"
			:fill="color"
			:text-anchor="anchor"
			:font-size="labelfontsize"
			class="pmLabel"
		>
			<tspan :class="textclass"> {{ text }} </tspan
			><tspan>
				<FormatWatt v-if="data !== undefined" :watt="data.power" />
			</tspan>
		</text>
	</g>
</template>

<script setup lang="ts">
import type { PowerItem, ItemProps } from '@/assets/js/types'
import FormatWatt from '../shared/FormatWatt.vue'
import { computed } from 'vue'

//props
const props = defineProps<{
	x: number
	y: number
	data?: PowerItem
	props?: ItemProps
	anchor: string
	labeltext?: string
	labelicon?: string
	labelcolor?: string
}>()

//state
const labelfontsize = 22

// computed
const text = computed(() => {
	return props.labeltext
		? props.labeltext
		: props.props
		? props.props.icon + ' '
		: props.labelicon
		? props.labelicon + ' '
		: ''
})
const color = computed(() => {
	return props.labelcolor
		? props.labelcolor
		: props.props
		? props.props.color
		: ''
})
const showMe = computed(() => {
	return !props.data || props.data.power > 0
})
const textclass = computed(() => {
	return props.labeltext ? '' : 'fas'
})
</script>

<style scoped></style>
