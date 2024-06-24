<template>
	<WbWidgetFlex
		v-for="(group, index) in devices"
		:key="index"
		:variable-width="true"
	>
		<template #title>
			<span @click="toggleconfig">
				<span class="fas fa-plug me-2" style="color: var(--color-devices)"
					>&nbsp;</span
				>
				<span class="sh-title py-4">{{ title(index) }}</span>
			</span>
		</template>
		<template #buttons>
			<span class="ms-2 pt-1" @click="toggleconfig">
				<span class="fa-solid fa-lg ps-1 fa-ellipsis-vertical" />
			</span>
		</template>
		<SHListItem
			v-for="device in group"
			:key="device.id"
			:device="<ShDevice>device"
			class="subgrid pb-2"
		/>
	</WbWidgetFlex>
	<!-- Configuration -->
	<WbWidgetFlex v-if="configmode">
		<template #title>
			<span class="smarthome" @click="toggleconfig">
				<span class="fas fa-gear">&nbsp;</span> Einstellungen</span
			>
		</template>
		<template #buttons>
			<span class="ms-2 pt-1" @click="toggleconfig">
				<span class="fa-solid fa-lg ps-1 fa-circle-check" />
			</span>
		</template>
		<ConfigItem
			title="Im Energie-Graph anzeigen:"
			icon="fa-chart-column"
			:fullwidth="true"
		>
			<div v-for="(element, idx) in activeDevices" :key="idx">
				<input
					:id="'check' + idx"
					v-model="element.showInGraph"
					class="form-check-input"
					type="checkbox"
					:value="element"
				/>
				<label class="form-check-label px-2" :for="'check' + idx">{{
					element.name
				}}</label>
			</div>
		</ConfigItem>
		<div class="row p-0 m-0" @click="toggleconfig">
			<div class="col-12 mb-3 pe-3 mt-0">
				<button class="btn btn-sm btn-secondary float-end">Schließen</button>
			</div>
		</div>
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import { computed, ref, type ComputedRef } from 'vue'
import WbWidgetFlex from '../shared/WbWidgetFlex.vue'
import SHListItem from './SHListItem.vue'
import { ShDevice, shDevices } from './model'
import { widescreen } from '@/assets/js/themeConfig'
import ConfigItem from '../shared/ConfigItem.vue'

const devicesPerWidget = 3 // max number of devices to be displayed in one box

const devices = computed(() =>
	widescreen.value
		? (<ComputedRef<ShDevice[]>>activeDevices).value.reduce<ShDevice[][]>(
				(grouping: ShDevice[][], device: ShDevice) => {
					const result = grouping
					let lastGroup = grouping[grouping.length - 1]
					if (lastGroup.length >= devicesPerWidget) {
						grouping.push([device])
					} else {
						lastGroup.push(device)
					}
					return result
				},
				[[]] as ShDevice[][],
			)
		: [activeDevices.value],
)
const activeDevices = computed(() => {
	return [...shDevices.values()].filter((dev) => dev.configured)
})

function title(index: number) {
	return (
		'Geräte' +
		(widescreen.value && devices.value.length > 1
			? '(' + (index + 1) + ')'
			: '')
	)
}
function toggleconfig() {
	configmode.value = !configmode.value
}

const configmode = ref(false)
</script>

<style scoped>
.sh-title {
	color: var(--color-title);
}

.tableheader {
	background-color: var(--color-bg);
	color: var(--color-menu);
}

.fa-ellipsis-vertical {
	color: var(--color-menu);
}

.fa-circle-check {
	color: var(--color-menu);
}

.smarthome {
	color: var(--color-devices);
}
</style>
