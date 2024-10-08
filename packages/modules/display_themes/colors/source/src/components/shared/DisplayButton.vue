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
		<span v-if="props.icon" class="fas me-2 scaled" :class="props.icon"></span>
		<span class="scaled">
			<slot />
		</span>
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
	padding-left: 8px;
	padding-right: 8px;
	padding-top: 6px;
	padding-bottom: 6px;
	align-self: top;
	box-shadow: 1px 3px black;
	font-weight: bold;
	font-size: var(--font-small);
}
</style>
