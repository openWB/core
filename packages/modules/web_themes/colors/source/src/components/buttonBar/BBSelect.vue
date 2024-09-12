/* * BBSelect.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus Hagen
*/

<template>
	<div class="container-fluid p-0 m-0">
		<div class="row p-0 m-0">
			<div v-for="(bt, id) in buttons" :key="id" class="col-md-4 p-1">
				<div class="d-grid gap-2">
					<button
						type="button"
						:class="buttonClass(bt.mode as ChargeMode)"
						:style="{}"
						@click="selectChargeMode(bt.mode as ChargeMode)"
					>
						{{ bt.name }}
					</button>
				</div>
			</div>
			<!-- Lock buttons -->
			<div class="col-md-4 p-1">
				<div class="d-grid gap-2">
					<button
						v-if="cp.isLocked"
						type="button"
						class="btn btn-outline-success buttonTextSize"
						data-bs-dismiss="modal"
						@click="lockCP(false)"
					>
						Entsperren
					</button>
					<button
						v-if="!cp.isLocked"
						type="button"
						class="btn btn-outline-danger buttonTextSize"
						data-bs-dismiss="modal"
						@click="lockCP(true)"
					>
						Sperren
					</button>
				</div>
			</div>
		</div>
		<!-- Battery priority settings -->
		<div v-if="globalData.isBatteryConfigured">
			<hr />
			<div class="row">
				<div class="col text-center">Vorrang im Lademodus PV-Laden:</div>
			</div>
			<div class="row justify-content-center m-1 p-0">
				<div class="col-lg-4 p-1 m-0">
					<div class="d-grid gap-2">
						<button
							id="evPriorityBtn"
							type="button"
							class="priorityModeBtn btn btn-secondary buttonTextSize"
							:class="priorityButtonClass('ev_mode')"
							data-dismiss="modal"
							priority="1"
							@click="setBatteryPriority('ev_mode')"
						>
							EV
							<span class="fas fa-car ms-2">&nbsp;</span>
						</button>
					</div>
				</div>
				<div class="col-lg-4 p-1 m-0">
					<div class="d-grid gap-2">
						<button
							id="batteryPriorityBtn"
							type="button"
							class="priorityModeBtn btn btn-secondary buttonTextSize"
							:class="priorityButtonClass('bat_mode')"
							data-dismiss="modal"
							priority="0"
							@click="setBatteryPriority('bat_mode')"
						>
							Speicher
							<span class="fas fa-car-battery ms-2">&nbsp;</span>
						</button>
					</div>
				</div>
				<div class="col-lg-4 p-1 m-0">
					<div class="d-grid gap-2">
						<button
							id="minsocPriorityBtn"
							type="button"
							class="priorityModeBtn btn btn-secondary buttonTextSize"
							:class="priorityButtonClass('min_soc_bat_mode')"
							data-dismiss="modal"
							priority="0"
							@click="setBatteryPriority('min_soc_bat_mode')"
						>
							MinSoc
							<span class="fas fa-battery-half">&nbsp;</span>
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { globalData } from '@/assets/js/model'
import { ChargeMode } from '@/assets/js/types'
import { chargePoints } from '@/components/chargePointList/model'

const props = defineProps<{
	cpId: number
}>()
// state
const buttons = [
	{
		mode: 'instant_charging',
		name: 'Sofort',
		color: 'var(--color-charging)',
	},
	{
		mode: 'scheduled_charging',
		name: 'Zielladen',
		color: 'var(--color-battery)',
	},
	{ mode: 'pv_charging', name: 'PV', color: 'var(--color-pv)' },
	{ mode: 'standby', name: 'Standby', color: 'var(--color-axis)' },
	{ mode: 'stop', name: 'Stop', color: 'var(--color-axis)' },
]
const cp = computed(() => {
	return chargePoints[props.cpId]
})
// methods
function buttonClass(chargemode: ChargeMode) {
	if (chargemode == cp.value.chargeMode) {
		return 'btn btn-success buttonTextSize'
	} else {
		return 'btn btn-secondary buttonTextSize'
	}
}
function priorityButtonClass(m: string) {
	return globalData.pvBatteryPriority == m ? 'btn-success' : 'btn-secondary'
}
function selectChargeMode(mode: ChargeMode) {
	cp.value.chargeMode = mode
}
function lockCP(flag: boolean) {
	cp.value.isLocked = flag
}
function setBatteryPriority(mode: string) {
	globalData.pvBatteryPriority = mode
}
</script>

<style scoped></style>
