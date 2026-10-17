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
	small?: boolean
}>()

const WbBadgestyle = computed(() => {
	let result = {
		color: props.color ?? 'var(--color-bg)',
		'background-color': props.bgcolor ?? 'var(--color-menu)',
		'font-size': props.small ? 'var(--font-smallbadge)' : 'var(--font-small)',
	}
	return result
})
</script>

<style scoped>
.pillWbBadge {
	font-weight: regular;
	display: flex;
	justify-content: center;
	align-items: center;
}
</style>
