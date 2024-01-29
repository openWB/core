<template>
	<span class="d-flex flex-column align-items-center">
		<span class="heading mt-1" :style="headingstyle">
			{{ props.heading }}
		</span>
		<span class="mx-1">
			<span
				class="d-flex my-0 align-items-center content"
				:style="contentstyle"
			>
				<slot />
			</span>
		</span>
	</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
	heading: string
	small?: boolean
}>()

const headingstyle = computed(() => {
	if (props.small) {
		return {
			'font-size': 'var(--font-small)',
		}
	} else {
		return {
			'font-size': 'var(--font-small)',
		}
	}
})
const contentstyle = computed(() => {
	if (props.small) {
		return {
			'font-size': 'var(--font-small)',
		}
	} else {
		return {
			'font-size': 'var(--font-normal)',
		}
	}
})
</script>

<style scoped>
.heading {
	color: var(--color-menu);
	font-weight: normal;
}

.content {
	color: var(--color-fg);
	font-weight: bold;
}
</style>
