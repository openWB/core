<template>
	<div class="px-4 pt-3 mb-2 wb-subwidget m-0" :class="widgetwidth">
		<div class="row p-0 m-0">
			<div class="col p-0 m-0">
				<div class="d-flex justify-content-between">
					<h3 class="m-0 mb-2" :style="titlestyle">
						<slot name="title" />
					</h3>

					<div class="col p-0 m-0" style="text-align: right">
						<slot name="buttons" />
					</div>
				</div>
			</div>
		</div>
		<div class="container-fluid m-0 p-0">
			<slot />
		</div>
	</div>
</template>
<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
	titlecolor?: string
	fullwidth?: boolean
}>()
const titlestyle = computed(() => {
	return props.titlecolor
		? { color: props.titlecolor }
		: { color: 'var(--color-fg)' }
})
const widgetwidth = computed(() => {
	return props.fullwidth ? 'col-lg-12' : 'col-lg-4'
})
</script>
<style scoped>
.wb-subwidget {
	border-top: 0.5px solid var(--color-scale);
}
</style>
