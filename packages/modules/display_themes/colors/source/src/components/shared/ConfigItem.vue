<template>
	<span class="d-flex align-items-baseline m-0 p-0 scaled">
		<i
			v-if="props.icon"
			class="fa-solid fa-sm m-0 p-0 me-2 item-icon"
			:class="props.icon"
			:style="{
				color: props.iconcolor ? props.iconcolor : 'var(--color-charging)',
			}"
		/>
		{{ title }}</span
	>
	<div
		class="ms-1 mb-2 p-0 pt-2 d-flex justify-content-stretch align-items-center"
	>
		<span class="justify-content-stretch d-flex">
			<slot />
		</span>
	</div>
</template>

<script setup lang="ts">
const props = defineProps<{
	title: string
	infotext?: string
	icon?: string
	iconcolor?: string
	fullwidth?: boolean
}>()
</script>

<style scoped>
.infotext {
	font-size: var(--font-settings);
	color: var(--color-battery);
}

.item-icon {
	color: var(--color-charging);
	font-size: var(--font-settings);
}

.titlecolumn {
	color: var(--color-bg);
	font-size: var(--font-settings);
}

.selectors {
	font-size: var(--font-settings);
}

.configitem {
	font-size: var(--font-settings);

	align-items: baseline;
	justify-content: space-between;
}
</style>
