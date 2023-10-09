<template>
	<WbSubwidget :fullwidth="fullwidth ? true : false">
		<div class="col-12 m-0 mb-0 px-0 py-0 configitem">
			<div class="titlecolumn m-0 p-0 d-flex align-items-center">
				<span class="d-flex align-items-baseline m-0 p-0" @click="toggleInfo">
					<i
						v-if="props.icon"
						class="fa-solid fa-sm m-0 p-0 me-2 item-icon"
						:class="props.icon"
					/>
					{{ title }}</span
				>
				<span>
					<i
						v-if="props.infotext"
						class="fa-solid fa-sm fa-circle-question ms-4 me-2"
						:style="iconstyle"
						@click="toggleInfo"
					/>
				</span>
			</div>

			<p
				v-if="showInfo"
				class="infotext shadow m-0 ps-2 mb-1 p-1"
				@click="toggleInfo"
			>
				<i class="me-1 fa-solid fa-sm fa-circle-info" />
				{{ infotext }}
			</p>
			<div class="row ms-1 mb-2 p-0 pt-2 d-flex align-items-center">
				<div class="col me-1 p-0 ps-4 selectors">
					<span class="d-flex justify-content-stretch align-items-center">
						<span>
							<slot />
						</span>
					</span>
				</div>
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

.titlecolumn {
	color: var(--color-fg);
	font-size: var(--font-settings);
}

.selectors {
	font-size: var(--font-settings);
}

.configitem {
	font-size: var(--font-settings);
}
</style>
