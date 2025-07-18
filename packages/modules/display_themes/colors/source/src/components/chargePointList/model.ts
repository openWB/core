import { reactive } from 'vue'
import { updateChargeTemplate, updateServer } from '@/assets/js/sendMessages'
import type { PowerItem } from '@/assets/js/types'
export class ChargePoint {
	id: number
	name = 'Ladepunkt'
	icon = 'Ladepunkt'
	type = ''
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
	chargeTemplateId = 0
	evTemplate = 0
	currentPlan = ''
	averageConsumption = 0
	vehicleName = ''
	rangeCharged = 0
	rangeUnit = ''
	counter = 0
	dailyYield = 0
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

	constructor(index: number) {
		this.id = index
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
		console.log('set mode')
		if (this.chargeTemplate) {
			console.log('active')
			this.chargeTemplate.chargemode.selected = cm
			updateChargeTemplate(this.id)
		}
	}
	get hasPriority() {
		return this.chargeTemplate?.prio ?? false
	}
	set hasPriority(prio: boolean) {
		this.chargeTemplate!.prio = prio
		updateChargeTemplate(this.id)
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
	toPowerItem(): PowerItem {
		return {
			name: this.name,
			power: this.power,
			energy: this.dailyYield,
			energyPv: this.energyPv,
			energyBat: this.energyBat,
			pvPercentage: this.pvPercentage,
			color: this.color,
			icon: this.icon,
		}
	}
}
export class Vehicle {
	id: number
	name = ''
	private _chargeTemplateId = 0
	private _evTemplateId = 0
	tags: Array<string> = []
	config = {}
	soc = 0
	range = 0
	private _etActive = false
	private _etMaxPrice = 20
	constructor(index: number) {
		this.id = index
	}
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
}
export interface ConnectedVehicleConfig {
	average_consumption: number
	charge_template: number
	chargemode: string
	current_plan: string
	ev_template: number
	priority: boolean
}
export enum ChargeMode {
	instant_charging = 'instant_charging',
	pv_charging = 'pv_charging',
	scheduled_charging = 'scheduled_charging',
	eco_charging = 'eco_charging',
	stop = 'stop',
}
export interface ChargeTimePlan {
	active: boolean
	frequency: {
		once: Array<Date>
		selected: string
		weekly: boolean[]
	}
	name: string
	time: Array<string>
	current: number
}
export class ChargeSchedule {
	name = 'Schedule'
	private _active = false
	timed = false
	time = ''
	current = 6
	limit = {
		selected: '',
		amount: 0,
		soc_limit: 0,
		soc_scheduled: 0,
	}
	frequency = {
		once: <Array<Date>>[],
		selected: '',
		weekly: <boolean[]>[],
	}
	get active() {
		return this._active
	}
	set active(val: boolean) {
		console.log('set active')
		this._active = val
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
			plans: ChargeSchedule[]
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
	disable_after_unplug: boolean
	et: {
		active: boolean
		max_price: number
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
	nominal_difference: number
	request_interval_charging: number
	request_interval_not_charging: number
	request_only_plugged: boolean
}
export const chargePoints: { [key: number]: ChargePoint } = reactive({})
export const vehicles: { [key: number]: Vehicle } = reactive({}) // the list of vehicles, key is the vehicle ID
export const chargeTemplates: { [key: number]: ChargeTemplate } = reactive({})
export const scheduledChargingPlans: { [key: number]: ChargeSchedule[] } =
	reactive({})
export const timeChargingPlans: { [key: number]: ChargeTimePlan[] } = reactive(
	{},
)

export const evTemplates: { [key: number]: EvTemplate } = reactive({})

export function addChargePoint(chargePointIndex: number) {
	if (!(chargePointIndex in chargePoints)) {
		chargePoints[chargePointIndex] = new ChargePoint(chargePointIndex)
		chargePoints[chargePointIndex].color =
			'var(--color-cp' + (Object.values(chargePoints).length - 1) + ')'
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
