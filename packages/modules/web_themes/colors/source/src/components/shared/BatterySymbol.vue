<template>
	<span>
		<i class="fa" :class="batterySymbol" :style="batStyle" />
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
	if (props.soc <= 10) {
		return 'fa-battery-empty'
	} else if (props.soc < 50) {
		return 'fa-battery-quarter'
	} else if (props.soc < 75) {
		return 'fa-battery-half'
	} else if (props.soc < 95) {
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
