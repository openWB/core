<template>
	<WbSubwidget :titlecolor="chargepoint.color" :fullwidth="true" :small="true">
		<template #title>
			<div class="d-flex align-items-center">
				<span class="cpname">{{ chargepoint.name }} </span>
				<span class="badge rounded-pill statusbadge mx-2" :style="statusColor">
					<i :class="statusIcon" class="me-1" />
					{{ statusString }}</span
				>
			</div>
		</template>
		<template #buttons>
			<div class="d-flex float-right justify-content-end align-items-center">
				<span
					class="badge rounded-pill modebadge mx-2"
					type="button"
					:style="modeStyle"
					data-bs-toggle="modal"
					:data-bs-target="'#cpsconfig-' + chargepoint.id"
				>
					<i class="fa me-1" :class="modeIcon" /> {{ modeString }}
				</span>
				<span
					class="fa-solid ms-2 fa-lg fa-edit ps-1"
					type="button"
					data-bs-toggle="modal"
					:data-bs-target="'#cpsconfig-' + chargepoint.id"
				/>
			</div>
		</template>
		<div class="subgrid">
			<InfoItem
				:heading="chargepoint.vehicleName"
				:small="true"
				class="grid-left grid-col-4"
			>
				<span
					v-if="chargepoint.isSocConfigured"
					class="d-flex justify-content-center align-items-center vehiclestatus"
				>
					<BatterySymbol
						v-if="chargepoint.soc"
						class="me-1"
						:soc="chargepoint.soc"
					/>
					<i
						v-if="chargepoint.isSocConfigured && chargepoint.isSocManual"
						type="button"
						class="fa-solid fa-sm fas fa-edit"
						:style="{ color: 'var(--color-menu)' }"
						@click="editSoc = !editSoc"
					/>
					<i
						v-if="chargepoint.isSocConfigured && !chargepoint.isSocManual"
						type="button"
						class="fa-solid fa-sm me-2"
						:class="
							chargepoint.waitingForSoc ? 'fa-spinner fa-spin' : 'fa-sync'
						"
						:style="{ color: 'var(--color-menu)' }"
						@click="loadSoc"
					/>
				</span>
			</InfoItem>

			<InfoItem heading="Parameter:" :small="true" class="grid-col-4">
				<div class="d-flex flex-column align-items-center px-0">
					<span class="d-flex justify-content-center flex-wrap">
						<span>{{ chargePowerString }}</span>

						<span class="d-flex align-items-center">
							<span class="badge phasesInUse rounded-pill">
								{{ chargePhasesString }}</span
							>
							<span>
								{{ chargeAmpereString }}
							</span>
						</span>
					</span>
				</div>
			</InfoItem>
			<InfoItem heading="Geladen:" :small="true" class="grid-right grid-col-4">
				<div class="d-flex flex-wrap justify-content-center chargeinfo">
					<span class="me-1">{{ chargeEnergyString }}</span>
					<span>{{ chargedRangeString }}</span>
				</div>
			</InfoItem>
		</div>
		<div v-if="editSoc" class="subgrid socEditRow m-0 p-0">
			<div
				class="socEditor rounded mt-2 d-flex flex-column align-items-center grid-col-12"
			>
				<span class="d-flex m-1 p-0 socEditTitle">Ladestand einstellen:</span>
				<span class="d-flex justify-content-stretch align-items-center">
					<span>
						<RangeInput
							id="manualSoc"
							v-model="manualSoc"
							:min="0"
							:max="100"
							:step="1"
							unit="%"
						/>
					</span>
				</span>
				<span
					type="button"
					class="fa-solid d-flex fa-lg me-2 mb-3 align-self-end fa-circle-check"
					@click="setSoc"
				/>
			</div>
		</div>
	</WbSubwidget>

	<Teleport to="body">
		<ModalComponent
			:key="chargepoint.id"
			:modal-id="'cpsconfig-' + chargepoint.id"
		>
			<template #title> Konfiguration: {{ chargepoint.name }} </template>
			<CPChargeConfigPanel
				v-if="chargepoint != undefined"
				:chargepoint="chargepoint"
			/>
		</ModalComponent>
	</Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { chargePoints, type ChargePoint } from '../model'
import { chargemodes, globalConfig } from '@/assets/js/themeConfig'
import { formatWatt, formatWattH } from '@/assets/js/helpers'
import CPChargeConfigPanel from '../cpConfig/CPChargeConfigPanel.vue'
import BatterySymbol from '../../shared/BatterySymbol.vue'
import RangeInput from '@/components/shared/RangeInput.vue'
import { updateServer } from '@/assets/js/sendMessages'
import ModalComponent from '@/components/shared/ModalComponent.vue'
import WbSubwidget from '@/components/shared/WbSubwidget.vue'
import InfoItem from '@/components/shared/InfoItem.vue'
const props = defineProps<{
	chargepoint: ChargePoint
}>()
const editSoc = ref(false)
const modeIcon = computed(() => {
	return chargemodes[props.chargepoint.chargeMode].icon
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
const statusColor = computed(() => {
	let result = 'var(--color-axis)'
	if (props.chargepoint.isLocked) {
		result = 'var(--color-evu)'
	} else if (props.chargepoint.isCharging) {
		result = 'var(--color-charging)'
	} else if (props.chargepoint.isPluggedIn) {
		result = 'var(--color-battery)'
	}
	return { color: result, border: `0.5px solid ${result} ` }
})
const modeStyle = computed(() => {
	switch (props.chargepoint.chargeMode) {
		case 'stop':
			return { 'background-color': 'var(--fg)' }
		default:
			return {
				'background-color': chargemodes[props.chargepoint.chargeMode].color,
			}
	}
})
const chargePowerString = computed(() => {
	return formatWatt(props.chargepoint.power, globalConfig.decimalPlaces)
})
const chargeAmpereString = computed(() => {
	return props.chargepoint.current + ' A'
})
const chargePhasesString = computed(() => {
	return props.chargepoint.phasesInUse
})
const chargeEnergyString = computed(() => {
	if (props.chargepoint.dailyYield > 0) {
		return formatWattH(props.chargepoint.dailyYield, globalConfig.decimalPlaces)
	} else {
		return '0 Wh'
	}
})
const chargedRangeString = computed(() => {
	return (
		'(' +
		Math.round(props.chargepoint.rangeCharged).toString() +
		' ' +
		props.chargepoint.rangeUnit +
		')'
	)
})
const modeString = computed(() => {
	return chargemodes[props.chargepoint.chargeMode].name
})
/* function nameCellStyle() {
	return { color: props.chargepoint.color }
} */
function loadSoc() {
	updateServer('socUpdate', 1, props.chargepoint.connectedVehicle)
	chargePoints[props.chargepoint.id].waitingForSoc = true
}
function setSoc() {
	updateServer('setSoc', manualSoc.value, props.chargepoint.connectedVehicle)
	editSoc.value = false
}
const manualSoc = computed({
	get() {
		return props.chargepoint.soc
	},
	set(s: number) {
		chargePoints[props.chargepoint.id].soc = s
	},
})
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
</script>

<style scoped>
.tablerow {
	margin: 14px;
	border-top: 0.1px solid var(--color-scale);
}

.tablecell {
	color: var(--color-fg);
	background-color: var(--color-bg);
	text-align: center;
	padding-top: 2px;
	padding-left: 2px;
	padding-right: 2px;
	vertical-align: baseline;
	line-height: 1.4rem;
	font-size: var(--font-small);
}

.buttoncell {
	background-color: var(--color-bg);
	padding: 0;
	margin: 0;
}

.left {
	text-align: left;
}

.tablecell.right {
	text-align: right;
}

.tablecolum1 {
	color: var(--color-fg);
	text-align: left;
	margin: 0;
	padding: 0;
}

.tableicon {
	color: var(--color-menu);
}

.fa-star {
	color: var(--color-evu);
}

.fa-clock {
	color: var(--color-battery);
}

.socEditor {
	border: 1px solid var(--color-menu);
	background-color: var(--color-bg);
}

.socEditRow td {
	background-color: var(--color-bg);
}

.fa-circle-check {
	color: var(--color-menu);
}

.socEditTitle {
	color: var(--color-fg);
}

.statusbadge {
	background-color: var(--color-bg);
	font-weight: bold;
	font-size: var(--font-verysmall);
}
.modebadge {
	color: var(--color-bg);
}
.cpname {
	font-size: var(--font-small);
}

.fa-edit {
	color: var(--color-menu);
}
.infolist {
	justify-content: center;
}
</style>
