<template>
	<div class="p-2 m-0 d-flex flex-fill" :class="widgetWidth">
		<div class="wb-widget p-0 m-0 shadow">
			<div class="d-flex justify-content-between">
				<h3 class="m-4 me-0 mb-0">
					<slot name="title">
						<div class="p-0">(title goes here)</div>
					</slot>
					<slot name="subtitle" />
				</h3>
				<div class="p-4 pb-0 ps-0 m-0" style="text-align: right">
					<slot name="buttons" />
				</div>
			</div>
			<div class="px-4 pt-4 pb-2 wb-subwidget">
				<div class="row">
					<div class="col">
						<div class="container-fluid m-0 p-0">
							<slot />
						</div>
					</div>
				</div>
			</div>
			<div v-if="$slots.footer != undefined">
				<hr />
				<div class="px-4 py-2 wb-subwidget">
					<div class="row">
						<div class="col">
							<div class="container-fluid m-0 p-0">
								<slot name="footer" />
							</div>
						</div>
					</div>
				</div>
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

<style scoped></style>
