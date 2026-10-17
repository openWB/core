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
				<span class="ms-2">
					<i
						v-if="cp.faultState === 0"
						@click="showInfo = !showInfo"
						class="fa-solid fa-xs fa-circle-info"
					/>
					<i
						v-if="cp.faultState != 0"
						@click="showFault = !showFault"
						class="fa-solid fa-sm fa-triangle-exclamation"
					/>
				</span>
			</span>
		</template>

		<template #buttons>
			<span type="button" class="ms-2 ps-1 pt-1" @click="toggleConfigMode()">
				<span class="fa-solid fa-lg ps-1 fa-ellipsis-vertical" />
			</span>
		</template>

		<!-- Chargepoint info -->
		<div v-if="!configmode" class="subgrid">
			<transition name="status-fade">
				<div
					v-if="showInfo"
					class="statustext status-entry py-1 px-2 mb-2 rounded shadow"
				>
					{{ cp.stateStr }}
				</div>
			</transition>
			<transition name="status-fade">
				<div
					v-if="showFault"
					class="faulttext status-entry p-1 mb-2 rounded shadow"
				>
					{{ cp.faultStr }}
				</div>
			</transition>
			<div class="grid12" @click="configmode = !configmode">
				<!-- Status information -->
				<InfoItem heading="Status:" class="grid-col-4 grid-left">
					<span :style="{ color: statusColor }">
						<i :class="statusIcon" />
						{{ statusString }}
					</span>
				</InfoItem>
				<!-- Ladung -->
				<InfoItem heading="Geladen:" class="grid-col-4 grid-center">
					<FormatWattH :watt-h="chargepoint.dailyYield" />
				</InfoItem>
				<div class="grid-col-4">&nbsp;</div>
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
const showInfo = ref(false)
const showFault = ref(false)

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

.statustext {
	grid-column: 1 / 13;
	justify-self: center;
	font-size: var(--font-small);
	color: black;
	background: var(--color-menu);
}

.faulttext {
	grid-column: 1 / 13;
	border: 1px solid var(--color-battery);
	justify-self: center;
	font-size: var(--font-small);
	color: black;
	background: var(--color-battery);
}

.status-entry {
	overflow: hidden;
	transform-origin: top center;
	will-change: opacity, transform;
}

.status-fade-enter-active,
.status-fade-leave-active {
	transition:
		opacity 0.22s cubic-bezier(0.22, 1, 0.36, 1),
		transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}

.status-fade-enter-from {
	opacity: 0;
	transform: translateY(-6px) scaleY(0.96);
}

.status-fade-leave-to {
	opacity: 0;
	transform: translateY(-4px) scaleY(0.94);
}

.status-fade-enter-to,
.status-fade-leave-from {
	opacity: 1;
	transform: translateY(0) scaleY(1);
}

.fa-circle-info {
	color: var(--color-menu);
}

.fa-triangle-exclamation {
	color: var(--color-battery);
}
</style>
