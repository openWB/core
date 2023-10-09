<template>
	<span class="d-flex flex-column align-items-center">
		<span class="heading mt-1">
			{{ props.heading }}
		</span>
		<span class="mx-1">
			<span class="d-flex my-0 align-items-center content">
				<slot />
			</span>
		</span>
	</span>
</template>

<script setup lang="ts">
const props = defineProps<{
	heading: string
}>()
</script>

<style scoped>
.heading {
	color: var(--color-menu);
	font-size: var(--font-small);
}
.content {
	font-size: var(--font-normal);
	font-weight: bold;
}
</style>
