<template>
	<span>
		<i class="fa batIcon" :class="batterySymbol" />
		{{ Math.round(soc) + '%' }}
	</span>
</template>
<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
	soc: number
}>()

const batterySymbol = computed(() => {
	if (props.soc <= 12) {
		return 'fa-battery-empty'
	} else if (props.soc < 38) {
		return 'fa-battery-quarter'
	} else if (props.soc < 63) {
		return 'fa-battery-half'
	} else if (props.soc < 89) {
		return 'fa-battery-three-quarters'
	} else {
		return 'fa-battery-full'
	}
})
</script>
<style scoped>
.batIcon {
	color: var(--color-menu);
}
</style>
