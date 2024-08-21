<template>
	<span
		class="d-flex flex-column align-items-center justify-content-start infoitem"
	>
		<span
			class="d-flex heading scaled"
			:style="headingstyle"
			:class="headingclass"
		>
			{{ props.heading }}
		</span>
		<!-- <span class="d-flex mx-1"> -->
		<span
			class="d-flex my-0 me-0 align-items-center content scaled"
			:style="contentstyle"
		>
			<slot />
		</span>
		<!-- </span> -->
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

const headingclass = computed(() => {
	if (props.small) {
		return 'mt-0'
	} else {
		return 'mt-1'
	}
})
</script>

<style scoped>
.heading {
	color: var(--color-menu);
	font-weight: normal;
	text-align: center;
}

.content {
	color: var(--color-fg);
	font-weight: bold;
}
</style>
