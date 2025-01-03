<template>
	<span class="d-flex flex-column">
		<span class="d-flex flex-fill justify-content-between align-items-center">
			<span type="button" class="minusButton" @click="stepDown">
				<i class="fa fa-xl fa-minus-square me-2" />
			</span>
			<div class="d-flex flex-fill flex-column justify-content-center m-0 p-0">
				<figure
					v-if="props.showSubrange"
					id="rangeIndicator"
					class="rangeIndicator"
				>
					<svg viewBox="0 0 100 2">
						<g>
							<rect
								class="below"
								:x="0"
								y="0"
								:width="subrangeX"
								height="2"
								rx="1"
								ry="1"
								fill="var(--color-evu)"
							/>
							<rect
								class="bar"
								:x="subrangeX"
								y="0"
								:width="subrangeWidth"
								height="2"
								rx="1"
								ry="1"
								fill="var(--color-charging)"
							/>
							<rect
								class="above"
								:x="subrangeX + subrangeWidth"
								y="0"
								:width="subrangeX"
								height="2"
								rx="1"
								ry="1"
								fill="var(--color-pv)"
							/>
						</g>
					</svg>
				</figure>
				<input
					:id="id"
					v-model.number="v"
					type="range"
					class="form-range flex-fill"
					:min="min"
					:max="max"
					:step="step"
				/>
			</div>
			<span type="button" class="plusButton" @click="stepUp">
				<i class="fa fa-xl fa-plus-square ms-2" />
			</span>
		</span>
		<span class="d-flex justify-content-between align-items-center">
			<span class="minlabel ps-4"> {{ min }} </span>
			<span class="valuelabel">{{ v }} {{ unit }}</span>
			<span class="maxlabel pe-4"> {{ max }} </span>
		</span>
	</span>
</template>

<script setup lang="ts">
import { scaleLinear } from 'd3'
import { computed } from 'vue'
const props = defineProps<{
	id: string
	min: number
	max: number
	step: number
	unit: string
	decimals?: number
	showSubrange?: boolean
	subrangeMin?: number
	subrangeMax?: number
	modelValue: number // for v-model binding
}>()

const dec = props.decimals ?? 0
const emit = defineEmits(['update:modelValue'])
const v = computed({
	get() {
		return Math.round(props.modelValue * Math.pow(10, dec)) / Math.pow(10, dec)
	},
	set(value: number) {
		emit('update:modelValue', value)
	},
})
//methods
function stepDown() {
	if (v.value > props.min) {
		v.value =
			Math.round((v.value - props.step) * Math.pow(10, dec)) / Math.pow(10, dec)
	}
}
function stepUp() {
	if (v.value < props.max) {
		v.value =
			Math.round((v.value + props.step) * Math.pow(10, dec)) / Math.pow(10, dec)
	}
}
const subrangeScale = computed(() => {
	const sc = scaleLinear().domain([props.min, props.max]).range([0, 100])
	return sc
})
const subrangeX = computed(() => {
	return subrangeScale.value(props.subrangeMin ? props.subrangeMin : 0)
})
const subrangeWidth = computed(() => {
	if (props.subrangeMin && props.subrangeMax) {
		return (
			subrangeScale.value(props.subrangeMax) -
			subrangeScale.value(props.subrangeMin)
		)
	} else {
		return 0
	}
})
</script>

<style scoped>
.minlabel {
	color: var(--color-menu);
}

.maxlabel {
	color: var(--color-menu);
}

.valuelabel {
	color: var(--color-fg);
}

.minusButton {
	color: var(--color-menu);
}

.plusButton {
	color: var(--color-menu);
}
.rangeIndicator {
	margin: 0px;
	padding: 0px;
	line-height: 10px;
}
</style>
