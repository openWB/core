<template>
	<div class="padbutton" :style="buttoncolor" @click="buttonClicked">
		<span class="digit scaled" type="button">
			<slot />
		</span>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
	modelValue: number
	color?: string
}>()

const active = ref(false)

function buttonClicked() {
	active.value = true
	emit('update:modelValue', props.modelValue)
	setTimeout(() => {
		active.value = false
	}, 300)
}
const buttoncolor = computed(() => {
	return active.value
		? { 'background-color': 'white', color: 'black' }
		: { 'background-color': props.color ?? 'var(--color-axis)' }
})
const emit = defineEmits(['update:modelValue'])
</script>

<style scoped>
.padbutton {
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 50%;
	border: 0.1px dotted var(--color-menu);
	box-shadow: 1px 3px black;
}
.digit {
	font-size: 24px;
	font-weight: bold;
	text-align: center;
	align-self: center;
	justify-self: center;
	display: flex;
}
</style>
