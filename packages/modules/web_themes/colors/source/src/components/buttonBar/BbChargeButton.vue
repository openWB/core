/* * BbChargeButton.vue * colors theme for openwb 2.0 * Copyright (c) 2022 Claus
Hagen */

<template>
	<div class="col-lg-4 p-0 m-0 mt-1">
		<div class="d-grid gap-2">
			<button
				type="button"
				class="btn mx-1 mb-0 p-1 mediumTextSize chargeButton shadow"
				:style="buttonStyle"
				data-bs-toggle="modal"
				:data-bs-target="'#' + modalId"
			>
				<div class="m-0 p-0 d-flex justify-content-between align-items-center">
					<!-- Status indicator -->
					<span class="mx-1 badge rounded-pill smallTextSize plugIndicator">
						<i :class="plugPillClass" />
						<span v-if="chargepoint.isCharging" class="ms-2">
							{{ formatWatt(chargepoint.power) }}
						</span>
					</span>
					<!-- Chargepoint name -->
					<span class="m-0 p-0">
						{{ chargepoint.name }}
					</span>
					<!-- Mode indicator -->
					<span
						class="mx-2 m-0 badge rounded-pill smallTextSize modeIndicator"
						:style="modePillStyle"
					>
						<i class="fa me-1" :class="modeIcon" />
						{{ modeString }}
						<!-- PV priority -->
						<span
							v-if="
								chargepoint.chargeMode == ChargeMode.pv_charging &&
								globalData.isBatteryConfigured
							"
							class="ps-1"
						>
							(
							<i class="fa m-0" :class="priorityIcon" />)
						</span>
					</span>
				</div>
			</button>
		</div>
		<ModalComponent :modal-id="modalId">
			<template #title> Lademodus für {{ chargepoint.name }} </template>
			<BBSelect :cp-id="chargepoint.id" />
		</ModalComponent>
	</div>
</template>

<script setup lang="ts">
import { globalData } from '@/assets/js/model'
import { ChargePoint, ChargeMode } from '@/components/chargePointList/model'
import { chargemodes } from '@/assets/js/themeConfig'
import { computed } from 'vue'
import { formatWatt } from '@/assets/js/helpers'
import BBSelect from './BBSelect.vue'
import ModalComponent from '@/components/shared/ModalComponent.vue'

//props
const props = defineProps<{
	chargepoint: ChargePoint
}>()
const modalId = 'chargeSelectModal' + props.chargepoint.id
const modeString = computed(() => {
	return chargemodes[props.chargepoint.chargeMode].name
})
const buttonStyle = computed(() => {
	let style = {
		background: 'var(--color-menu)',
	}
	if (props.chargepoint.isLocked) {
		style.background = 'var(--color-evu)'
	} else if (props.chargepoint.isCharging) {
		style.background = 'var(--color-charging)'
	} else if (props.chargepoint.isPluggedIn) {
		style.background = 'var(--color-battery)'
	}
	return style
})
interface ButtonStyle {
	background: string
	color: string
}
const modePillStyle = computed(() => {
	if (chargemodes) {
		let style = {
			background: chargemodes[props.chargepoint.chargeMode].color,
			color: 'white',
		}

		switch (props.chargepoint.chargeMode) {
			case ChargeMode.instant_charging:
				if (props.chargepoint.isCharging && !props.chargepoint.isLocked) {
					style = swapcolors(style)
				}
				break
			case ChargeMode.standby:
			case ChargeMode.stop:
				style.background = 'darkgrey'
				style.color = 'black'
				/* if (!props.chargepoint.isPluggedIn) {
					style = swapcolors(style)
				} */
				break
			case ChargeMode.scheduled_charging:
				if (
					props.chargepoint.isPluggedIn &&
					!props.chargepoint.isCharging &&
					!props.chargepoint.isLocked
				) {
					style = swapcolors(style)
				}
				break
			default:
				break
		}
		return style
	} else {
		return { background: 'var(--color-bg)', color: 'var(--color-bg)' }
	}
})
const modeIcon = computed(() => {
	if (chargemodes) {
		return chargemodes[props.chargepoint.chargeMode].icon
	} else {
		return ''
	}
})
const priorityIcon = computed(() => {
	if (globalData.pvBatteryPriority) {
		return 'fa-car-battery'
	} else {
		return 'fa-car'
	}
})
const plugPillClass = computed(() => {
	let icon = 'fa-ellipsis'
	if (props.chargepoint.isLocked) {
		icon = 'fa-lock'
	} else if (props.chargepoint.isCharging) {
		icon = ' fa-bolt'
	} else if (props.chargepoint.isPluggedIn) {
		icon = 'fa-plug'
	}

	return 'fa ' + icon
})

// methods
function swapcolors(style: ButtonStyle): ButtonStyle {
	let c = style.color
	style.color = style.background
	style.background = c
	return style
}
</script>

<style scoped>
.plugIndicator {
	color: white;
	border: 1px solid white;
}

.chargeButton {
	color: white;
}
.left {
	float: left;
}
.right {
	float: right;
}
.center {
	margin: auto;
}
</style>
