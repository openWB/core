<template>
	<WbSubwidget :titlecolor="chargepoint.color" :fullwidth="true">
		<template #title>
			<span class="cpname">{{ chargepoint.name }} </span>
		</template>
		<template #buttons>
			<div class="d-flex float-right justify-content-end align-items-center">
				<span class="badge rounded-pill statusbadge mx-2" :style="statusColor">
					<i :class="statusIcon" class="me-1" />
					{{ statusString }}</span
				>
				<span class="badge rounded-pill modebadge mx-2" :style="modeStyle">
					<i class="fa me-1" :class="modeIcon" /> {{ modeString }}
				</span>
				<span
					class="fa-solid ms-2 fa-lg fa-edit ps-1"
					data-bs-toggle="modal"
					:data-bs-target="'#cpsconfig-' + chargepoint.id"
				/>
			</div>
		</template>
		<div class="d-flex justify-content-between">
			<InfoItem :heading="chargepoint.vehicleName" :small="true">
				<span v-if="chargepoint.isSocConfigured" class="flex-wrap">
					<BatterySymbol class="me-1" :soc="chargepoint.soc" />
					<i
						v-if="chargepoint.isSocConfigured && chargepoint.isSocManual"
						type="button"
						class="fa-solid fa-sm fas fa-edit me-2"
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
			<InfoItem heading="Parameter:" :small="true">
				<div class="d-flex flex-column">
					<span class="d-flex align-items-center flex-wrap">
						<span>{{ chargePowerString }}</span>

						<span class="d-flex align-items-center me-1">
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
			<InfoItem heading="Geladen:" :small="true">
				<div class="d-flex flex-wrap">
					<span class="me-2">{{ chargeEnergyString }}</span>
					<span>{{ chargedRangeString }}</span>
				</div>
			</InfoItem>
		</div>
	</WbSubwidget>
	<!-- <tr class="tablerow">
		<td
			class="tablecell left"
			data-bs-toggle="modal"
			:data-bs-target="'#cpsconfig-' + chargepoint.id"
		>
			<div class="d-flex flex-wrap">
				<span>
					<i :class="statusIcon" class="me-1" :style="statusColor" />
					<span class="me-1" :style="nameCellStyle()">
						{{ chargepoint.name }}</span
					>
				</span>
				<span
					><i v-if="chargepoint.hasPriority" class="fa-solid fa-xs fa-star" />
					<i v-if="chargepoint.timedCharging" class="fa-solid fa-xs fa-clock" />
				</span>
			</div>
		</td>
		<td class="tablecell left">
			<div class="d-flex flex-column">
				<span>{{ chargepoint.vehicleName }}</span>
				<span v-if="chargepoint.isSocConfigured" class="flex-wrap">
					<BatterySymbol class="me-1" :soc="chargepoint.soc" />
					<i
						v-if="chargepoint.isSocConfigured && chargepoint.isSocManual"
						type="button"
						class="fa-solid fa-sm fas fa-edit me-2"
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
			</div>
		</td>
		<td
			class="tablecell left"
			data-bs-toggle="modal"
			:data-bs-target="'#cpsconfig-' + chargepoint.id"
		>
			<div class="d-flex flex-column">
				<span class="d-flex align-items-center flex-wrap">
					<span>{{ chargePowerString }}</span>

					<span class="d-flex align-items-center me-1">
						<span class="badge phasesInUse rounded-pill">
							{{ chargePhasesString }}</span
						>
						<span>
							{{ chargeAmpereString }}
						</span>
					</span>
				</span>
				<span :style="modeStyle">
					<i class="fa me-1" :class="modeIcon" /> {{ modeString }}
				</span>
			</div>
		</td>
		<td
			class="tablecell left"
			data-bs-toggle="modal"
			:data-bs-target="'#cpsconfig-' + chargepoint.id"
		>
			<div class="d-flex flex-column">
				<span class="me-2">{{ chargeEnergyString }}</span>
				<span>{{ chargedRangeString }}</span>
			</div>
		</td>

		<td class="buttoncell right">
			<span
				class="fa-solid fa-lg fa-edit ps-1 tableicon"
				data-bs-toggle="modal"
				:data-bs-target="'#cpsconfig-' + chargepoint.id"
			/>
		</td>
	</tr>
	<tr v-if="editSoc" class="socEditRow m-0 p-0">
		<td colspan="5" class="m-0 p-0 pb-2">
			<div class="socEditor rounded mt-2 d-flex flex-column align-items-center">
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
		</td>
	</tr> -->
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
// import RangeInput from '@/components/shared/RangeInput.vue'
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
	let result = { 'background-color': 'var(--color-axis)' }
	if (props.chargepoint.isLocked) {
		result['background-color'] = 'var(--color-evu)'
	} else if (props.chargepoint.isCharging) {
		result['background-color'] = 'var(--color-charging)'
	} else if (props.chargepoint.isPluggedIn) {
		result['background-color'] = 'var(--color-battery)'
	}
	return result
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
	if (
		props.chargepoint.averageConsumption > 0 &&
		props.chargepoint.dailyYield > 0
	) {
		return (
			'(' +
			Math.round(
				props.chargepoint.dailyYield /
					props.chargepoint.averageConsumption /
					10,
			).toString() +
			' km)'
		)
	} else {
		return ''
	}
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
/* function setSoc() {
	updateServer('setSoc', manualSoc.value, props.chargepoint.connectedVehicle)
	editSoc.value = false
} */
/* const manualSoc = computed({
	get() {
		return props.chargepoint.soc
	},
	set(s: number) {
		chargePoints[props.chargepoint.id].soc = s
	},
}) */
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
	color: white;
}
.statusbadge {
	background-color: var(--color-menu);
	font-weight: normal;
}
.cpname {
	font-size: var(--font-medium);
}
</style>
