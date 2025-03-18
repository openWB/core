<template>
	<div class="numberpad">
		<p class="codedisplay scaled px-3 py-1 mb-4">{{ limit }} ct</p>
		<div class="numberentry">
			<PadButtonSmall
				v-for="val in 3"
				:key="val"
				:model-value="val"
				@update:model-value="addDigit"
				>{{ val }}</PadButtonSmall
			>
			<PadButtonSmall
				:model-value="-2"
				color="var(--color-devices)"
				@update:model-value="addDigit"
				><span class="fas fa-circle-check"></span
			></PadButtonSmall>
			<PadButtonSmall
				v-for="val in [4, 5, 6]"
				:key="val"
				:model-value="val"
				@update:model-value="addDigit"
				>{{ val }}</PadButtonSmall
			>
			<PadButtonSmall
				:model-value="-1"
				color="var(--color-devices)"
				@update:model-value="addDigit"
				><span class="fas fa-delete-left"></span
			></PadButtonSmall>
			<PadButtonSmall
				v-for="val in [7, 8, 9]"
				:key="val"
				:model-value="val"
				@update:model-value="addDigit"
				>{{ val }}</PadButtonSmall
			>
			<div></div>
			<div></div>
			<PadButtonSmall :model-value="0" @update:model-value="addDigit"
				>0</PadButtonSmall
			>
			<PadButtonSmall :model-value="-3" @update:model-value="addDigit"
				>,</PadButtonSmall
			>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PadButtonSmall from './PadButtonSmall.vue'
const props = defineProps<{
	modelValue: string
}>()

const limit = ref(props.modelValue)
const emit = defineEmits(['update:modelValue'])

function addDigit(digit: number) {
	if (digit == -1) {
		limit.value = limit.value.slice(0, -1)
	} else if (digit == -2) {
		emit('update:modelValue', limit.value)
		limit.value = ''
	} else if (digit == -3) {
		if (limit.value.indexOf('.') == -1) {
			limit.value = limit.value + '.'
		}
	} else {
		limit.value = limit.value + digit.toString()
	}
}
</script>
<style scoped>
.numberpad {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	background-color: var(--color-bg);
}
.codedisplay {
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 18px;
	border: 10px;
	border-radius: 10px;
	color: var(--color-bg);
	background-color: var(--color-fg);
}

.numberentry {
	display: grid;
	grid-template-columns: 50px 50px 50px 50px;
	grid-template-rows: 54px 54px 54px 54px;
	grid-gap: 5px;
}
</style>
