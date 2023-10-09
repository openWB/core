<template>
	{{ formatted }}
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { globalConfig } from '@/assets/js/themeConfig'
import { formatWatt } from '@/assets/js/helpers'
const props = defineProps<{
	watt: number
}>()
const formatted = computed(() => {
	return formatWatt(props.watt, globalConfig.decimalPlaces)
})
</script>
<style scoped></style>
