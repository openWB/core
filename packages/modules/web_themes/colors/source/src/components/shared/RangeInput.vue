<template>
	<span class="d-flex flex-fill justify-content-between">
		<span type="button" class="minusButton" @click="stepDown">
			<i class="fa fa-xl fa-minus-square me-2" />
		</span>
		<input
			:id="id"
			v-model.number="v"
			type="range"
			class="form-range flex-fill"
			:min="min"
			:max="max"
			:step="step"
		/>
		<span type="button" class="plusButton" @click="stepUp">
			<i class="fa fa-xl fa-plus-square ms-2" />
		</span>
	</span>
	<span class="d-flex justify-content-between align-items-start">
		<span class="minlabel ps-4"> {{ min }} </span>
		<span class="valuelabel">{{ v }} {{ unit }}</span>
		<span class="maxlabel pe-4"> {{ max }} </span>
	</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
	id: string
	min: number
	max: number
	step: number
	unit: string
	decimals?: number
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
</style>
