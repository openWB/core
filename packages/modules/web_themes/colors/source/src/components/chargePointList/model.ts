import { computed, reactive } from 'vue'
import { updateChargeTemplate, updateServer } from '@/assets/js/sendMessages'
import {
	ChargeMode,
	PowerItemType,
	type EnergyData,
	type PowerItem,
} from '@/assets/js/types'
import { globalConfig } from '@/assets/js/themeConfig'
import { getColor } from '@/assets/js/model'
export class ChargePoint implements PowerItem {
	id: number
	name = 'Ladepunkt'
	icon = 'Ladepunkt'
	type = PowerItemType.chargepoint
	ev = 0
	template = 0
	connectedPhases = 0
	phase_1 = 0
	autoPhaseSwitchHw = false
	controlPilotInterruptionHw = false
	isEnabled = true
	isPluggedIn = false
	isCharging = false
	private _isLocked = false
	private _connectedVehicle = 0
	chargeTemplate: ChargeTemplate | null = null
	evTemplate = 0
	private _chargeMode = ChargeMode.pv_charging
	private _hasPriority = false
	currentPlan = ''
	averageConsumption = 0
	private _vehicleName = ''
	rangeCharged = 0
	rangeUnit = ''
	counter = 0
	dailyYield = 0
	now: EnergyData = {
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
	}
	past: EnergyData = {
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
	}
	energyPv = 0
	energyBat = 0
	pvPercentage = 0
	faultState = 0
	faultStr = ''
	phasesInUse = 0
	power = 0
	chargedSincePlugged = 0
	stateStr = ''
	current = 0
	currents = [0, 0, 0]
	phasesToUse = 0
	// soc = 0
	isSocConfigured = true
	isSocManual = false
	waitingForSoc = false
	color = 'white'
	showInGraph = true
	private _timedCharging = false
	private _instantChargeLimitMode = ''
	private _instantTargetCurrent = 0
	private _instantTargetSoc = 0
	private _instantMaxEnergy = 0
	private _instantTargetPhases = 0
	private _pvFeedInLimit = false
	private _pvMinCurrent = 0
	private _pvMaxSoc = 0
	private _pvMinSoc = 0
	private _pvMinSocCurrent = 0
	private _pvMinSocPhases = 1
	private _pvChargeLimitMode = ''
	private _pvTargetSoc = 0
	private _pvMaxEnergy = 0
	private _pvTargetPhases = 0
	private _ecoMinCurrent = 0
	private _ecoTargetPhases = 0
	private _ecoChargeLimitMode = ''
	private _ecoTargetSoc = 0
	private _ecoMaxEnergy = 0
	private _etActive = false
	private _etMaxPrice = 20

	constructor(index: number) {
		this.id = index
	}
	get vehicleName() {
		return vehicles[this.connectedVehicle]?.name ?? ''
	}
	set vehicleName(name: string) {
		this._vehicleName = name
	}
	get isLocked() {
		return this._isLocked
	}
	set isLocked(locked: boolean) {
		this._isLocked = locked
		updateServer('cpLock', locked, this.id)
	}
	updateIsLocked(locked: boolean) {
		this._isLocked = locked
	}
	get connectedVehicle() {
		return this._connectedVehicle
	}
	set connectedVehicle(vId: number) {
		this._connectedVehicle = vId
		updateServer('cpVehicle', vId, this.id)
	}
	updateConnectedVehicle(id: number) {
		this._connectedVehicle = id
	}
	get soc() {
		if (vehicles[this.connectedVehicle]) {
			return vehicles[this.connectedVehicle].soc
		} else {
			return 0
		}
	}
	set soc(newSoc: number) {
		if (vehicles[this.connectedVehicle]) {
			vehicles[this.connectedVehicle].soc = newSoc
		}
	}
	get chargeMode() {
		return this.chargeTemplate?.chargemode.selected ?? ChargeMode.stop
	}
	set chargeMode(cm: ChargeMode) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.selected = cm
			updateChargeTemplate(this.id)
		}
	}
	get hasPriority() {
		return this.chargeTemplate?.prio ?? false
	}
	set hasPriority(prio: boolean) {
		if (this.chargeTemplate) {
			this.chargeTemplate.prio = prio
			updateChargeTemplate(this.id)
		}
	}
	get timedCharging() {
		if (this.chargeTemplate) {
			return this.chargeTemplate.time_charging.active
		} else {
			return false
		}
	}
	set timedCharging(setting: boolean) {
		this.chargeTemplate!.time_charging.active = setting
		updateChargeTemplate(this.id)
	}
	get instantTargetCurrent() {
		return this.chargeTemplate?.chargemode.instant_charging.current ?? 0
	}
	set instantTargetCurrent(current: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.instant_charging.current = current
			updateChargeTemplate(this.id)
		}
	}
	get instantChargeLimitMode() {
		return (
			this.chargeTemplate?.chargemode.instant_charging.limit.selected ?? 'none'
		)
	}
	set instantChargeLimitMode(mode: string) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.instant_charging.limit.selected = mode
			updateChargeTemplate(this.id)
		}
	}
	get instantTargetSoc() {
		return this.chargeTemplate?.chargemode.instant_charging.limit.soc ?? 0
	}
	set instantTargetSoc(soc: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.instant_charging.limit.soc = soc
			updateChargeTemplate(this.id)
		}
	}
	get instantMaxEnergy() {
		return this.chargeTemplate?.chargemode.instant_charging.limit.amount ?? 0
	}
	set instantMaxEnergy(max: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.instant_charging.limit.amount = max
			updateChargeTemplate(this.id)
		}
	}
	get instantTargetPhases() {
		return this.chargeTemplate?.chargemode.instant_charging.phases_to_use ?? 0
	}
	set instantTargetPhases(phases: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.instant_charging.phases_to_use = phases
			updateChargeTemplate(this.id)
		}
	}
	get pvFeedInLimit() {
		return this.chargeTemplate?.chargemode.pv_charging.feed_in_limit ?? false
	}
	set pvFeedInLimit(setting: boolean) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.pv_charging.feed_in_limit = setting
			updateChargeTemplate(this.id)
		}
	}
	get pvMinCurrent() {
		return this.chargeTemplate?.chargemode.pv_charging.min_current ?? 0
	}
	set pvMinCurrent(min: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.pv_charging.min_current = min
			updateChargeTemplate(this.id)
		}
	}
	get pvMaxSoc() {
		return this._pvMaxSoc
	}
	set pvMaxSoc(max: number) {
		this._pvMaxSoc = max
		updateServer('cpPvMaxSoc', max, this.id)
	}
	updatePvMaxSoc(max: number) {
		this._pvMaxSoc = max
	}
	get pvMinSoc() {
		return this.chargeTemplate?.chargemode.pv_charging.min_soc ?? 0
	}
	set pvMinSoc(min: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.pv_charging.min_soc = min
			updateChargeTemplate(this.id)
		}
	}
	get pvMinSocCurrent() {
		return this.chargeTemplate?.chargemode.pv_charging.min_soc_current ?? 0
	}
	set pvMinSocCurrent(a: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.pv_charging.min_soc_current = a
			updateChargeTemplate(this.id)
		}
	}
	set pvMinSocPhases(n: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.pv_charging.phases_to_use_min_soc = n
			updateChargeTemplate(this.id)
		}
	}
	get pvMinSocPhases() {
		return (
			this.chargeTemplate?.chargemode.pv_charging.phases_to_use_min_soc ?? 0
		)
	}
	get pvChargeLimitMode() {
		return this.chargeTemplate?.chargemode.pv_charging.limit.selected ?? 'none'
	}
	set pvChargeLimitMode(mode: string) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.pv_charging.limit.selected = mode
			updateChargeTemplate(this.id)
		}
	}
	get pvTargetSoc() {
		return this.chargeTemplate?.chargemode.pv_charging.limit.soc ?? 0
	}
	set pvTargetSoc(soc: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.pv_charging.limit.soc = soc
			updateChargeTemplate(this.id)
		}
	}
	get pvMaxEnergy() {
		return this.chargeTemplate?.chargemode.pv_charging.limit.amount ?? 0
	}
	set pvMaxEnergy(max: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.pv_charging.limit.amount = max
			updateChargeTemplate(this.id)
		}
	}
	get pvTargetPhases() {
		return this.chargeTemplate?.chargemode.pv_charging.phases_to_use ?? 0
	}
	set pvTargetPhases(phases: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.pv_charging.phases_to_use = phases
			updateChargeTemplate(this.id)
		}
	}
	get ecoMinCurrent() {
		return this.chargeTemplate?.chargemode.eco_charging.current ?? 0
	}
	set ecoMinCurrent(min: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.eco_charging.current = min
			updateChargeTemplate(this.id)
		}
	}
	get ecoTargetPhases() {
		return this.chargeTemplate?.chargemode.eco_charging.phases_to_use ?? 0
	}
	set ecoTargetPhases(phases: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.eco_charging.phases_to_use = phases
			updateChargeTemplate(this.id)
		}
	}
	get ecoChargeLimitMode() {
		return this.chargeTemplate?.chargemode.eco_charging.limit.selected ?? 'none'
	}
	set ecoChargeLimitMode(mode: string) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.eco_charging.limit.selected = mode
			updateChargeTemplate(this.id)
		}
	}
	get ecoTargetSoc() {
		return this.chargeTemplate?.chargemode.eco_charging.limit.soc ?? 0
	}
	set ecoTargetSoc(soc: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.eco_charging.limit.soc = soc
			updateChargeTemplate(this.id)
		}
	}
	get ecoMaxEnergy() {
		return this.chargeTemplate?.chargemode.eco_charging.limit.amount ?? 0
	}
	set ecoMaxEnergy(max: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.eco_charging.limit.amount = max
			updateChargeTemplate(this.id)
		}
	}
	get etMaxPrice() {
		return (
			(this.chargeTemplate?.chargemode.eco_charging.max_price ?? 0) * 100000
		)
	}
	set etMaxPrice(newPrice: number) {
		if (this.chargeTemplate) {
			this.chargeTemplate.chargemode.eco_charging.max_price =
				Math.ceil(newPrice * 1000) / 100000000
			updateChargeTemplate(this.id)
		}
	}
	get etActive() {
		return (
			this.chargeTemplate &&
			this.chargeTemplate.chargemode.selected == ChargeMode.eco_charging
		)
	}
	get realCurrent() {
		switch (this.phasesInUse) {
			case 0:
				return 0
			case 1:
				return this.currents[0]
			case 2:
				return (this.currents[0] + this.currents[1]) / 2
			case 3:
				return (this.currents[0] + this.currents[1] + this.currents[2]) / 3
			default:
				return 0
		}
	}
}
export class Vehicle {
	id: number
	name = '__invalid'
	tags: Array<string> = []
	config = {}
	soc = 0
	range = 0
	constructor(index: number) {
		this.id = index
	}
	private _chargeTemplateId = 0
	isSocConfigured = false
	isSocManual = false
	get chargeTemplateId() {
		return this._chargeTemplateId
	}
	set chargeTemplateId(id: number) {
		this._chargeTemplateId = id
		updateServer('vhChargeTemplateId', id, this.id)
	}
	updateChargeTemplateId(id: number) {
		this._chargeTemplateId = id
	}
	private _evTemplateId = 0
	get evTemplateId() {
		return this._evTemplateId
	}
	set evTemplateId(id: number) {
		this._evTemplateId = id
		updateServer('vhEvTemplateId', id, this.id)
	}
	updateEvTemplateId(id: number) {
		this._evTemplateId = id
	}
	get chargepoint(): ChargePoint | undefined {
		for (const cp of Object.values(chargePoints)) {
			if (cp.connectedVehicle == this.id) {
				return cp
			}
		}
		return undefined
	}
	get visible(): boolean {
		return (
			this.name != '__invalid' &&
			(this.id != 0 || globalConfig.showStandardVehicle)
		)
	}
}
export interface ConnectedVehicleConfig {
	average_consumption: number
	charge_template: number
	chargemode: string
	current_plan: string
	ev_template: number
	priority: boolean
}
export interface ChargeTimePlan {
	id: number
	name: string
	active: boolean
	time: [string, string]
	current: number
	dc_current: number
	phases_to_use: number
	limit: {
		selected: 'none' | 'soc' | 'amount'
		amount?: number
		soc?: number
	}
	frequency: {
		selected: 'daily' | 'weekly' | 'once'
		once?: [string, string]
		weekly: [boolean, boolean, boolean, boolean, boolean, boolean, boolean]
	}
}
export interface ChargeSchedule {
	id: number
	name: string
	active: boolean
	time: string
	current: number
	dc_current: number
	phases_to_use: number
	phases_to_use_pv: number
	et_active: boolean
	bidi_charging_enabled: boolean
	bidi_power: number
	limit: {
		selected: 'soc' | 'amount'
		amount?: number
		soc_limit?: number
		soc_scheduled: number
	}
	frequency: {
		once?: string
		selected: 'weekly' | 'daily' | 'once'
		weekly: [boolean, boolean, boolean, boolean, boolean, boolean, boolean]
	}
}
export interface ChargeTemplate {
	id: number
	name: string
	prio: boolean
	load_default: boolean
	time_charging: {
		active: boolean
		plans: [ChargeTimePlan]
	}
	chargemode: {
		selected: ChargeMode
		eco_charging: {
			current: number
			dc_current: number
			limit: {
				selected: string
				soc: number
				amount: number
			}
			max_price: number
			phases_to_use: number
		}
		pv_charging: {
			dc_min_current: number
			dc_min_soc_current: number
			feed_in_limit: boolean
			limit: {
				selected: string
				amount: number
				soc: number
			}
			min_current: number
			min_soc_current: number
			min_soc: number
			phases_to_use: number
			phases_to_use_min_soc: number
		}
		scheduled_charging: {
			plans: [ChargeSchedule]
		}
		instant_charging: {
			current: number
			dc_current: number
			limit: {
				selected: string
				soc: number
				amount: number
			}
			phases_to_use: number
		}
	}
}
export interface EvTemplate {
	name: string
	max_current_multi_phases: number
	max_phases: number
	phase_switch_pause: number
	prevent_switch_stop: boolean
	control_pilot_interruption: boolean
	control_pilot_interruption_duration: number
	average_consump: number
	min_current: number
	max_current_one_phase: number
	battery_capacity: number
	efficiency: number
	nominal_difference: number
	request_interval_charging: number
	request_interval_not_charging: number
	request_only_plugged: boolean
}
export const chargePoints: { [key: number]: ChargePoint } = reactive({})
export const vehicles: { [key: number]: Vehicle } = reactive({}) // the list of vehicles, key is the vehicle ID
export const chargeTemplates: { [key: number]: ChargeTemplate } = reactive({})
export const evTemplates: { [key: number]: EvTemplate } = reactive({})

export function addChargePoint(chargePointIndex: number) {
	if (!(chargePointIndex in chargePoints)) {
		chargePoints[chargePointIndex] = new ChargePoint(chargePointIndex)
		const cpcolor = getColor('cp', Object.values(chargePoints).length - 1)
		//
		//'var(--color-cp' + (Object.values(chargePoints).length - 1) + ')'
		chargePoints[chargePointIndex].color = cpcolor
		//const cpId = 'cp' + chargePointIndex
		/* if (!masterData[cpId]) {
			masterData[cpId] = {
				name: 'Ladepunkt',
				color: cpcolor,
				icon: 'Ladepunkt',
			}
		} else {
			masterData['cp' + chargePointIndex].color = cpcolor
		}
		 */
		// console.info('Added chargepoint ' + chargePointIndex)
	} else {
		// console.info('Duplicate chargepoint message: ' + chargePointIndex)
	}
}
export function resetChargePoints() {
	Object.keys(chargePoints).forEach((key) => {
		delete chargePoints[parseInt(key)]
	})
}

export const topVehicles = computed(() => {
	let result: number[] = []
	const connectedVehicles = Object.values(chargePoints)
		.filter((cp) => vehicles[cp.connectedVehicle] && vehicles[cp.connectedVehicle].isSocConfigured)
		.map((cp) => cp.connectedVehicle)
	console.log('connected vehicles', connectedVehicles)
	const otherVehicles = Object.values(vehicles)
		.filter((v) => v.visible && v.isSocConfigured && !connectedVehicles.includes(v.id)) // only show vehicles with configured soc and that are visible
	console.log('other vehicles', otherVehicles)
	result = connectedVehicles.concat(otherVehicles.map((v) => v.id)).slice(0, 2)
	if (result.length == 0) {
		result = [-1,-1]
	} else if (result.length == 1) {
		result.push(-1)
	}
	return result
})
export const chargeLimitModes = [
	{ name: 'keine', id: 'none' },
	{ name: 'Ladestand', id: 'soc' },
	{ name: 'Energie', id: 'amount' },
]
