<template>
	<div
		:style="{
			'background-color': props.bgcolor ? props.bgcolor : 'var(--color-bg)',
			color: props.color ? props.color : 'var(--color-title)',
		}"
		class="displaybutton rounded-pill"
		type="button"
		@click="buttonClicked"
	>
		<span v-if="props.icon" class="fas me-2" :class="props.icon"></span>
		<slot />
	</div>
</template>

<script setup lang="ts">
const props = defineProps<{
	icon?: string
	bgcolor?: string
	color?: string
}>()
const emit = defineEmits(['click'])
function buttonClicked() {
	emit('click', true)
}
</script>

<style scoped>
.displaybutton {
	border: 0.1px solid var(--color-frame);
	padding: 8px;
	align-self: top;
	box-shadow: 1px 3px black;
	font-weight: bold;
	font-size: var(--font-small);
}
</style>
