<template>
	<div class="numberpad">
		<p class="codedisplay scaled">{{ hiddencode }}</p>
		<div class="numberentry">
			<PadButton
				v-for="val in 9"
				:key="val"
				:model-value="val"
				@update:model-value="addDigit"
				>{{ val }}</PadButton
			>
			<PadButton :model-value="0" @update:model-value="addDigit">0</PadButton>
			<PadButton
				:model-value="-1"
				color="var(--color-devices)"
				@update:model-value="addDigit"
				><span class="fas fa-delete-left"></span
			></PadButton>
			<PadButton
				:model-value="-2"
				color="var(--color-devices)"
				data-bs-dismiss="modal"
				@update:model-value="addDigit"
				><span class="fas fa-circle-check"></span
			></PadButton>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import PadButton from './PadButton.vue'
const props = defineProps<{
	modelValue: string
}>()

const code = ref(props.modelValue)
const emit = defineEmits(['update:modelValue'])
const hiddencode = computed(() => {
	return code.value.length == 0
		? 'Bitte geben Sie die PIN ein'
		: '*'.repeat(code.value.length)
})
function addDigit(digit: number) {
	if (digit == -1) {
		code.value = code.value.slice(0, -1)
	} else if (digit == -2) {
		emit('update:modelValue', code.value)

		code.value = ''
	} else {
		code.value = code.value + digit.toString()
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
	font-size: 24px;
	border: 10px;
	color: var(--color-fg);
}

.numberentry {
	display: grid;
	grid-template-columns: 60px 60px 60px;
	grid-template-rows: 65px 65px 65px 65px;
	grid-gap: 5px;
}
</style>
