<template>
	<div class="p-2 m-0 d-flex" :class="widgetWidth">
		<div class="wb-widget p-0 m-0 shadow">
			<div class="d-flex justify-content-between">
				<h3 class="m-4 mb-3">
					<slot name="title">
						<div class="p-0">(title goes here)</div>
					</slot>
					<slot name="subtitle" />
				</h3>
				<div class="p-4 pb-0 col-4 m-0" style="text-align: right">
					<slot name="buttons" />
				</div>
			</div>
			<div class="container-fluid p-0">
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
	border-radius: 30px;
}
</style>
