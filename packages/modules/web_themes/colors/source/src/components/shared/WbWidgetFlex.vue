<template>
	<div class="p-2 m-0" :class="widgetWidth">
		<div class="wb-widget p-0 m-0 shadow widgetWidth">
			<div
				class="py-4 px-3 d-flex justify-content-between align-items-center titlerow"
			>
				<div class="d-flex align-items-center widgetname p-0 m-0">
					<slot name="title">
						<div class="p-0">(title goes here)</div>
					</slot>
					<slot name="subtitle" />
				</div>
				<div
					class="buttonrea d-flex float-right justify-content-end align-items-center"
				>
					<slot name="buttons" />
				</div>
			</div>
			<div class="grid12 pb-3">
				<slot />
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { globalConfig } from '@/assets/js/themeConfig'
const props = defineProps<{
	variableWidth?: boolean
	fullWidth?: boolean
}>()
const widgetWidth = computed(() => {
	return props.fullWidth
		? 'col-12'
		: props.variableWidth && globalConfig.preferWideBoxes
			? 'col-lg-6'
			: 'col-lg-4'
})
</script>

<style scoped>
.wb-widget {
	width: 100%;
	height: 100%;
	border-radius: 30px;
}
.widgetname {
	font-weight: bold;
	color: var(--color-fg);
	font-size: var(--font-large);
}
</style>
