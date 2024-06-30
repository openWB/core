<template>
	<span class="pillWbBadge rounded-pill ms-2 px-2" :style="WbBadgestyle">
		<slot />
	</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
	color?: string
	bgcolor?: string
}>()

const WbBadgestyle = computed(() => {
	let result = {
		'background-color': props.bgcolor ?? 'var(--color-menu)',
		color: props.color ?? 'black',
	}
	return result
})
</script>

<style scoped>
.pillWbBadge {
	font-size: (var--font-small);
	font-weight: regular;
}
</style>
