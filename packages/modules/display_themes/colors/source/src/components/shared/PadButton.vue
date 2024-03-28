<template>
	<div class="m-2">
		<span class="numberbutton" type="button" @click="buttonClicked">
			<slot />
		</span>
	</div>
</template>
<script setup lang="ts">
const props = defineProps<{
	modelValue: number
}>()

function buttonClicked() {
	emit('update:modelValue', props.modelValue)
}


const emit = defineEmits(['update:modelValue'])
</script>
<style scoped>
.numberbutton {
	background-color: var(--color-menu);
	display: flex;
	font-size: 20px;
	padding: 16px;
	justify-content: center;
	align-items: center;
	border: 1px solid var(--color-menu);
	text-align: center;
	border-radius: 10px;
}
</style>