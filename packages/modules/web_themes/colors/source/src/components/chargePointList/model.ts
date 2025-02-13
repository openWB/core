import { computed, reactive } from 'vue'
import { updateServer } from '@/assets/js/sendMessages'
import { ChargeMode, type PowerItem } from '@/assets/js/types'
import { globalConfig } from '@/assets/js/themeConfig'
import { masterData } from '@/assets/js/model'
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
	chargeTemplate = 0
	evTemplate = 0
	private _chargeMode = ChargeMode.pv_charging
	private _hasPriority = false
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
	private _timedCharging = false
	private _instantChargeLimitMode = ''
	private _instantTargetCurrent = 0
	private _instantTargetSoc = 0
	private _instantMaxEnergy = 0
	private _pvFeedInLimit = false
	private _pvMinCurrent = 0
	private _pvMaxSoc = 0
	private _pvMinSoc = 0
	private _pvMinSocCurrent = 0
	private _etActive = false
	private _etMaxPrice = 20

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
		return this._chargeMode
	}
	set chargeMode(cm: ChargeMode) {
		this._chargeMode = cm
		updateServer('chargeMode', cm, this.id)
	}
	updateChargeMode(cm: ChargeMode) {
		this._chargeMode = cm
	}
	get hasPriority() {
		return this._hasPriority
	}
	set hasPriority(prio: boolean) {
		this._hasPriority = prio
		updateServer('cpPriority', prio, this.id)
	}
	updateCpPriority(prio: boolean) {
		this._hasPriority = prio
	}
	get timedCharging() {
		if (chargeTemplates[this.chargeTemplate]) {
			return chargeTemplates[this.chargeTemplate].time_charging.active
		} else {
			return false
		}
	}
	set timedCharging(setting: boolean) {
		// chargeTemplates[this.chargeTemplate].time_charging.active = false
		chargeTemplates[this.chargeTemplate].time_charging.active = setting
		updateServer('cpTimedCharging', setting, this.chargeTemplate)
	}
	get instantTargetCurrent() {
		return this._instantTargetCurrent
	}
	set instantTargetCurrent(current: number) {
		this._instantTargetCurrent = current
		updateServer('cpInstantTargetCurrent', current, this.id)
	}
	updateInstantTargetCurrent(current: number) {
		this._instantTargetCurrent = current
	}
	get instantChargeLimitMode() {
		return this._instantChargeLimitMode
	}
	set instantChargeLimitMode(mode: string) {
		this._instantChargeLimitMode = mode
		updateServer('cpInstantChargeLimitMode', mode, this.id)
	}
	updateInstantChargeLimitMode(mode: string) {
		this._instantChargeLimitMode = mode
	}
	get instantTargetSoc() {
		return this._instantTargetSoc
	}
	set instantTargetSoc(soc: number) {
		this._instantTargetSoc = soc
		updateServer('cpInstantTargetSoc', soc, this.id)
	}
	updateInstantTargetSoc(soc: number) {
		this._instantTargetSoc = soc
	}
	get instantMaxEnergy() {
		return this._instantMaxEnergy
	}
	set instantMaxEnergy(max: number) {
		this._instantMaxEnergy = max
		updateServer('cpInstantMaxEnergy', max, this.id)
	}
	updateInstantMaxEnergy(max: number) {
		this._instantMaxEnergy = max
	}
	get pvFeedInLimit() {
		return this._pvFeedInLimit
	}
	set pvFeedInLimit(setting: boolean) {
		this._pvFeedInLimit = setting
		updateServer('cpPvFeedInLimit', setting, this.id)
	}
	updatePvFeedInLimit(setting: boolean) {
		this._pvFeedInLimit = setting
	}
	get pvMinCurrent() {
		return this._pvMinCurrent
	}
	set pvMinCurrent(min: number) {
		this._pvMinCurrent = min
		updateServer('cpPvMinCurrent', min, this.id)
	}
	updatePvMinCurrent(min: number) {
		this._pvMinCurrent = min
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
		return this._pvMinSoc
	}
	set pvMinSoc(min: number) {
		this._pvMinSoc = min
		updateServer('cpPvMinSoc', min, this.id)
	}
	updatePvMinSoc(min: number) {
		this._pvMinSoc = min
	}
	get pvMinSocCurrent() {
		return this._pvMinSocCurrent
	}
	set pvMinSocCurrent(a: number) {
		this._pvMinSocCurrent = a
		updateServer('cpPvMinSocCurrent', a, this.id)
	}
	updatePvMinSocCurrent(a: number) {
		this._pvMinSocCurrent = a
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
	get etActive() {
		if (vehicles[this.connectedVehicle]) {
			return vehicles[this.connectedVehicle].etActive
		} else {
			return false
		}
	}
	set etActive(val) {
		if (vehicles[this.connectedVehicle]) {
			vehicles[this.connectedVehicle].etActive = val
		}
	}
	get etMaxPrice() {
		return vehicles[this.connectedVehicle].etMaxPrice ?? 0
	}
	set etMaxPrice(newPrice: number) {
		updateServer('cpEtMaxPrice', Math.round(newPrice * 10) / 1000000, this.id)
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
			showInGraph: true,
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
	get etActive() {
		if (chargeTemplates[this.chargeTemplateId]) {
			return chargeTemplates[this.chargeTemplateId].et.active
		} else {
			return false
		}
	}
	set etActive(val) {
		if (chargeTemplates[this.chargeTemplateId]) {
			updateServer('priceCharging', val, this.chargeTemplateId)
		}
	}
	get etMaxPrice() {
		if (chargeTemplates[this.chargeTemplateId]) {
			if (chargeTemplates[this.chargeTemplateId].et.active) {
				return chargeTemplates[this.chargeTemplateId].et.max_price * 100000
			}
		}
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
export interface ChargeSchedule {
	name: string
	active: boolean
	timed: boolean
	time: string
	current: number
	limit: {
		selected: string
		amount: number
		soc_limit: number
		soc_scheduled: number
	}
	frequency: {
		once: Array<Date>
		selected: string
		weekly: boolean[]
	}
}
export interface ChargeTemplate {
	name: string
	prio: boolean
	chargemode: {
		selected: ChargeMode
		instant_charging: {
			current: number
			limit: {
				selected: string
				soc: number
				amount: number
			}
		}
		pv_charging: {
			feed_in_limit: boolean
			min_current: number
			max_soc: number
			min_soc: number
			min_soc_current: number
		}
	}
	time_charging: {
		active: boolean
	}
	disable_after_unplug: boolean
	load_default: boolean
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
		const cpcolor =
			'var(--color-cp' + (Object.values(chargePoints).length - 1) + ')'
		chargePoints[chargePointIndex].color = cpcolor
		const cpId = 'cp' + chargePointIndex
		if (!masterData[cpId]) {
			masterData[cpId] = {
				name: 'Ladepunkt',
				color: cpcolor,
				icon: 'Ladepunkt',
			}
		} else {
			masterData['cp' + chargePointIndex].color = cpcolor
		}
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
	const result: number[] = []
	const cps = Object.values(chargePoints)
	const vhcls = Object.values(vehicles).filter((v) => v.visible)
	// vehicle 1
	let v1 = -1
	switch (cps.length) {
		case 0:
			v1 = vhcls[0] ? vhcls[0].id : -1
			break
		default:
			v1 = cps[0].connectedVehicle //?? vhcls[0] ? vhcls[0].id : -1
	}
	// vehicle 2
	let v2 = -1
	switch (cps.length) {
		case 0:
		case 1:
			v2 = vhcls[0] ? vhcls[0].id : -1
			break
		default:
			v2 = cps[1].connectedVehicle //?? vhcls[1] ? vhcls[1].id : -1
	}
	// change v2 if the same as v1
	if (v1 == v2) {
		v2 = vhcls[1] ? vhcls[1].id : -1
	}
	if (v1 != -1) {
		result.push(v1)
	}
	if (v2 != -1) {
		result.push(v2)
	}
	return result
})
