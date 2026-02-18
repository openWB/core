<template>
	<WbSubwidget :fullwidth="fullwidth ? true : false">
		<div class="configitem grid-col-12 mt-0 mb-0 px-0 py-0">
			<div
				class="titlerow m-0 p-0 d-flex justify-content-between align-items-center"
			>
				<span class="lefttitle d-flex justify-content-end align-items-baseline">
					<span class="d-flex align-items-center m-0 p-0" @click="toggleInfo">
						<i
							v-if="props.icon"
							class="fa-solid fa-sm m-0 p-0 me-2 item-icon"
							:class="props.icon"
						/>
						{{ title }}
					</span>
					<span class="d-flex">
						<i
							v-if="props.infotext"
							class="fa-solid fa-sm fa-circle-question ms-3 me-2"
							:style="iconstyle"
							@click="toggleInfo"
						/>
					</span>
				</span>
				<span class="righttitle d-flex align-items-center">
					<span class="inlinecontent"><slot name="inline-item" /></span>
				</span>
			</div>
			<p
				v-if="showInfo"
				class="infotext shadow m-0 ps-2 mb-1 p-3"
				@click="toggleInfo"
			>
				<i class="me-1 fa-solid fa-sm fa-circle-info" />
				{{ infotext }}
			</p>
			<div
				class="ms-1 mb-2 p-0 pt-2 d-flex justify-content-stretch align-items-center contentrow"
			>
				<slot />
			</div>
		</div>
	</WbSubwidget>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import WbSubwidget from './WbSubwidget.vue'

const props = defineProps<{
	title: string
	infotext?: string
	icon?: string
	fullwidth?: boolean
}>()
const showInfo = ref(false)
function toggleInfo() {
	showInfo.value = !showInfo.value
}
const iconstyle = computed(() => {
	let style = { color: 'var(--color-charging)' }
	if (showInfo.value) {
		style.color = 'var(--color-battery)'
	}
	return style
})
</script>

<style scoped>
.infotext {
	font-size: var(--font-settings);
	color: var(--color-battery);
}

.item-icon {
	color: var(--color-menu);
	font-size: var(--font-settings);
}

.titlerow {
	display: grid;
	grid-column: 1 / 13;
	grid-template-columns: subgrid;
	color: var(--color-fg);
	font-size: var(--font-settings);
	flex-grow: 1;
}

.selectors {
	font-size: var(--font-settings);
}

.configitem {
	font-size: var(--font-settings);
	display: flex;
	flex-direction: column;
	justify-content: stretch;
	align-items: stretch;
	height: 100%;
	width: 100%;
}
.lefttitle {
	display: grid;
	grid-column: 1 / 7;
}
.righttitle {
	display: grid;
	grid-column: 7 / 13;
	justify-content: stretch;
}
.inlinecontent {
	display: grid;
	width: 100%;
}
.contentrow {
	display: flex;
	height: 100%;
	width: 100%;
}
.infotext {
	font-size: var(--font-settings);
	text-align: center;
	color: var(--color-charging);
	grid-column: span 12;
	border-radius: 12px;
}
</style>
