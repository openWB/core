<template>
	<div
		:style="{
			'background-color': props.color ? props.color : 'var(--color-fg)',
		}"
		class="mybutton"
		@click="buttonClicked"
	>
		<span v-if="props.icon" class="fas me-2" :class="props.icon"></span>
		<slot />
	</div>
</template>

<script setup lang="ts">
const props = defineProps<{
	icon?: string
	color?: string
}>()
const emit = defineEmits(['click'])
function buttonClicked() {
	emit('click', true)
}
</script>

<style scoped>
.mybutton {
	border: 10px;
	padding: 2px;
	align-self: top;
	color: var(--color-bg);
	border-radius: 4px;
	font-weight: bold;
	font-size: var(--font-small);
}
</style>
