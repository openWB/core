<template>
	<span class="d-flex justify-content-center align-items-center">
		<i class="fa me-1" :class="batterySymbol" :style="batStyle" />
		{{ Math.round(soc) + '%' }}
	</span>
</template>
<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
	soc: number
	color?: string
}>()

const batterySymbol = computed(() => {
	if (props.soc <= 12) {
		return 'fa-battery-empty'
	} else if (props.soc < 38) {
		return 'fa-battery-quarter'
	} else if (props.soc < 62) {
		return 'fa-battery-half'
	} else if (props.soc < 87) {
		return 'fa-battery-three-quarters'
	} else {
		return 'fa-battery-full'
	}
})

const batStyle = computed(() => {
	const col = props.color ?? 'var(--color-menu)'
	return { color: col }
})
</script>
<style scoped>
.batIcon {
	color: var(--color-menu);
}
</style>
