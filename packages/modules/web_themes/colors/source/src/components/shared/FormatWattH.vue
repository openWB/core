<template>
	<span>
		{{ formatted }}
	</span>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { globalConfig } from '@/assets/js/themeConfig'
import { formatWattH } from '@/assets/js/helpers'
const props = defineProps<{
	wattH: number
}>()
const formatted = computed(() => {
	return formatWattH(props.wattH, globalConfig.decimalPlaces)
})
</script>
<style scoped></style>
