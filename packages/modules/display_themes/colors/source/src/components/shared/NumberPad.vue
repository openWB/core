<template>
	<div class="codedisplay">{{ hiddencode }}</div>
	<div class="numberpad">
		<PadButton v-for="val in 9" :key="val" :model-value=val @update:model-value="addDigit">{{ val }}</PadButton>
		<PadButton :model-value="-1" @update:model-value="addDigit"><span class="fas fa-delete-left"></span></PadButton>
		<PadButton :model-value="0" @update:model-value="addDigit">0</PadButton>
		<PadButton :model-value="-2" @update:model-value="addDigit"><span class="fas fa-circle-check"></span></PadButton>


	</div>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue';
import PadButton from './PadButton.vue';
const code = ref("")

const hiddencode = computed(() => {
	return '*'.repeat(code.value.length)
})
function addDigit(digit: number) {
	console.log(digit)
	if (digit == -1) {
		code.value = code.value.slice(0, -1)
	} else if (digit == -2) {
		//submit value
	} else {
		code.value = code.value + digit.toString()
		console.log(code.value)
	}
}
</script>
<style scoped>
.codedisplay {
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24px;
	border: 10px;
}

.numberpad {
	display: grid;
	grid-template-columns: auto auto auto;
}
</style>