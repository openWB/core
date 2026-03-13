<template>
	<WBWidget
		v-if="!configmode"
		:variable-width="true"
		:full-width="props.fullWidth"
	>
		<template #title>
			<span class="d-flex justify-content-center align-items-center">
				<span :style="cpNameStyle" @click="configmode = !configmode">
					<span class="fa-solid fa-charging-station">&nbsp;</span>
					{{ props.chargepoint.name }}</span
				>
				<span
					v-if="cp.faultState == 2"
					class="WbBadge rounded-pill errorWbBadge ms-3"
					>Fehler</span
				>
			</span>
		</template>

		<template #buttons>
			<span type="button" class="ms-2 ps-1 pt-1" @click="toggleConfigMode()">
				<span class="fa-solid fa-lg ps-1 fa-ellipsis-vertical" />
			</span>
		</template>

		<!-- Chargepoint info -->
		<div v-if="!configmode">
			<div class="grid12" @click="configmode = !configmode">
				<!-- Status information -->
				<InfoItem heading="Status:" class="grid-col-4 grid-left">
					<span :style="{ color: statusColor }">
						<i :class="statusIcon" />
						{{ statusString }}
					</span>
				</InfoItem>
				<!-- Ladung -->
				<InfoItem heading="Geladen:" class="grid-col-4 grid-left">
					<FormatWattH :watt-h="chargepoint.dailyYield" />
				</InfoItem>
			</div>
		</div>
		<div v-if="configmode" class="row m-0 mt-0 p-0">
			<div class="col m-0 p-0">
				<ChargeConfigPanel
					v-if="chargepoint != undefined"
					:chargepoint="chargepoint"
				/>
			</div>
		</div>
		<!-- Car information-->
		<template #footer>
			<div class="mb-3">
				<VehicleData
					v-if="!configmode"
					:chargepoint="props.chargepoint"
					:full-width="props.fullWidth"
				/>
			</div>
		</template>
	</WBWidget>
	<WbWidgetFlex v-else :full-width="props.fullWidth">
		<template #title>
			<span :style="cpNameStyle" @click="configmode = !configmode">
				<span class="fas fa-gear">&nbsp;</span>
				Einstellungen {{ props.chargepoint.name }}</span
			>
		</template>

		<template #buttons>
			<span class="ms-2 pt-1" @click="configmode = !configmode">
				<span class="fa-solid fa-lg ps-1 fa-circle-check" />
			</span>
		</template>
		<ChargeConfigPanel
			v-if="chargepoint != undefined"
			:chargepoint="chargepoint"
		/>

		<button
			type="button"
			class="close-config-button btn ms-2 pt-1"
			@click="configmode = !configmode"
		>
			OK
		</button>
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { type ChargePoint } from './model'
import WBWidget from '@/components/shared/WBWidget.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
import ChargeConfigPanel from './cpConfig/ChargeConfigPanel.vue'
import FormatWattH from '../shared/FormatWattH.vue'
import WbWidgetFlex from '../shared/WbWidgetFlex.vue'
import VehicleData from './VehicleData.vue'

const props = defineProps<{
	chargepoint: ChargePoint
	fullWidth?: boolean
}>()
const cp = ref(props.chargepoint)
const configmode = ref(false)

// computed
const statusString = computed(() => {
	if (props.chargepoint.isLocked) {
		return 'Gesperrt'
	} else if (props.chargepoint.isCharging) {
		return 'Lädt'
	} else if (props.chargepoint.isPluggedIn) {
		return 'Bereit'
	} else {
		return 'Frei'
	}
})
const statusColor = computed(() => {
	if (props.chargepoint.isLocked) {
		return 'var(--color-evu)'
	} else if (props.chargepoint.isCharging) {
		return 'var(--color-charging)'
	} else if (props.chargepoint.isPluggedIn) {
		return 'var(--color-battery)'
	} else {
		return 'var(--color-axis)'
	}
})
const statusIcon = computed(() => {
	let icon = ''
	if (props.chargepoint.isLocked) {
		icon = 'fa-lock'
	} else if (props.chargepoint.isCharging) {
		icon = ' fa-bolt'
	} else if (props.chargepoint.isPluggedIn) {
		icon = 'fa-plug'
	}
	return 'fa ' + icon
})

const cpNameStyle = computed(() => {
	return { color: props.chargepoint.color }
	// return { color: 'var(--color-fg)' }
})

// methods
function toggleConfigMode() {
	configmode.value = !configmode.value
}
</script>

<style scoped>
.fa-ellipsis-vertical {
	color: var(--color-menu);
}
.fa-circle-check {
	color: var(--color-menu);
}
.errorWbBadge {
	color: var(--color-bg);
	background-color: var(--color-evu);
	font-size: var(--font-small);
}

.close-config-button {
	background: var(--color-menu);
	color: var(--color-bg);
	grid-column: 11 / span 2;
	font-size: var(--font-settings-button);
}
</style>
