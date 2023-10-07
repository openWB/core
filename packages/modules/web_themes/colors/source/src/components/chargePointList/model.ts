import { reactive, ref } from 'vue'
import { updateServer } from '@/assets/js/sendMessages'
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
  phasesToUse = 0
  soc = 0
  isSocConfigured = true
  isSocManual = false
  color = 'white'
  private _scheduledCharging = false
  private _instantChargeLimitMode = ''
  private _instantTargetCurrent = 0
  private _instantTargetSoc = 0
  private _instantMaxEnergy = 0
  private _pvFeedInLimit = false
  private _pvMinCurrent = 0
  private _pvMaxSoc = 0
  private _pvMinSoc = 0
  private _pvMinSocCurrent = 0
  constructor(index: number) {
    this.id = index
  }
  get isLocked() {
    return this._isLocked
  }
  set isLocked(locked: boolean) {
    this._isLocked = locked
    updateServer ('cpLock', locked, this.id)
  }
  updateIsLocked (locked: boolean) {
    this._isLocked = locked
  }
  get connectedVehicle() {
    return this._connectedVehicle
  }
  set connectedVehicle(vId: number) {
    this._connectedVehicle = vId
    updateServer ('cpVehicle', vId, this.id)
  }
  updateConnectedVehicle (id: number) {
    this._connectedVehicle = id
  }
  get chargeMode() {
    return this._chargeMode
  }
  set chargeMode(cm: ChargeMode) {
    this._chargeMode = cm
    updateServer ('chargeMode', cm, this.id)
    }
  updateChargeMode (cm: ChargeMode) {
    this._chargeMode = cm
  }
  get hasPriority() {
    return this._hasPriority
  }
  set hasPriority(prio: boolean) {
    this._hasPriority = prio
    updateServer ('cpPriority', prio, this.id)
    }
  updateCpPriority (prio: boolean) {
    this._hasPriority = prio
  }
  get scheduledCharging() {
    return this._scheduledCharging
  }
  set scheduledCharging(setting: boolean) {
    this._scheduledCharging = setting
    updateServer ('cpScheduledCharging', setting, this.id)
  }
  updateScheduledCharging (setting: boolean) {
    this._scheduledCharging = setting
  }
  get instantTargetCurrent() {
    return this._instantTargetCurrent
  }
  set instantTargetCurrent(current: number) {
    this._instantTargetCurrent = current
    updateServer ('cpInstantTargetCurrent', current, this.id)
  }
  updateInstantTargetCurrent (current: number) {
    this._instantTargetCurrent = current
  }
  get instantChargeLimitMode() {
    return this._instantChargeLimitMode
  }
  set instantChargeLimitMode(mode: string) {
    this._instantChargeLimitMode = mode
    updateServer ('cpInstantChargeLimitMode', mode, this.id)
  }
  updateInstantChargeLimitMode (mode: string) {
    this._instantChargeLimitMode = mode
  }
  get instantTargetSoc() {
    return this._instantTargetSoc
  }
  set instantTargetSoc(soc: number) {
    this._instantTargetSoc = soc
    updateServer ('cpInstantTargetSoc', soc, this.id)
  }
  updateInstantTargetSoc (soc: number) {
    this._instantTargetSoc = soc
  }
  get instantMaxEnergy() {
    return this._instantMaxEnergy
  }
  set instantMaxEnergy(max: number) {
    this._instantMaxEnergy = max
    updateServer ('cpInstantMaxEnergy', max, this.id)
  }
  updateInstantMaxEnergy (max: number) {
    this._instantMaxEnergy = max
  }
  get pvFeedInLimit() {
    return this._pvFeedInLimit
  }
  set pvFeedInLimit(setting: boolean) {
    this._pvFeedInLimit = setting
    updateServer ('cpPvFeedInLimit', setting, this.id)
  }
  updatePvFeedInLimit (setting: boolean) {
    this._pvFeedInLimit = setting
  }
  get pvMinCurrent() {
    return this._pvMinCurrent
  }
  set pvMinCurrent(min: number) {
    this._pvMinCurrent = min
    updateServer ('cpPvMinCurrent', min, this.id)
  }
  updatePvMinCurrent (min: number) {
    this._pvMinCurrent = min
  }
  get pvMaxSoc() {
    return this._pvMaxSoc
  }
  set pvMaxSoc(max: number) {
    this._pvMaxSoc = max
    updateServer ('cpPvMaxSoc', max, this.id)
  }
  updatePvMaxSoc (max: number) {
    this._pvMaxSoc = max
  }
  get pvMinSoc() {
    return this._pvMinSoc
  }
  set pvMinSoc(min: number) {
    this._pvMinSoc = min
    updateServer ('cpPvMinSoc', min, this.id)
  }
  updatePvMinSoc (min: number) {
    this._pvMinSoc = min
  }
  get pvMinSocCurrent() {
    return this._pvMinSocCurrent
  }
  set pvMinSocCurrent(a: number) {
    this._pvMinSocCurrent = a
    updateServer ('cpPvMinSocCurrent', a, this.id)
  }
  updatePvMinSocCurrent (a: number) {
    this._pvMinSocCurrent = a
  }
  toPowerItem () : PowerItem {
    return {
      name: this.name,
      power: this.power,
      energy: this.dailyYield,
      energyPv: this.energyPv,
      energyBat: this.energyBat,
      pvPercentage: this.pvPercentage,
      color: this.color,
      icon: this.icon
    }
  }
}
export class Vehicle {
  id: number
  name = ''
  private _chargeTemplateId = 0
  private _evTemplateId = 0
  tags: Array<string> = []
  soc = 0
  range = 0
  constructor(index: number) {
    this.id = index
  }
  get chargeTemplateId() {
    return this._chargeTemplateId
  }
  set chargeTemplateId (id: number) {
    this._chargeTemplateId = id
    updateServer ('vhChargeTemplateId', id, this.id)
  }
  updateChargeTemplateId (id: number) {
    this._chargeTemplateId = id
  }
  get evTemplateId() {
    return this._evTemplateId
  }
  set evTemplateId (id: number) {
    this._evTemplateId = id
    updateServer ('vhEvTemplateId', id, this.id)
  }
  updateEvTemplateId (id: number) {
    this._evTemplateId = id
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
  standby = 'standby',
  stop = 'stop',
}
export interface ChargeTimePlan {
  frequency: {
    once: Array<Date>
    selected: string
    weekly: boolean[]
  }
  name: string
  time: Array<string>
  current: number
}
export function createChargeTimePlan () : ChargeTimePlan {
  return {
    frequency: {
      once: [new Date('2022-02-02'),new Date('2022-02-22')],
      selected: 'daily',
      weekly: [false,false,false,false,false,false,false]
    },
    name: 'Neuer Plan',
    time: ['10:00','16:00'],
    current: 16
  }
}
export interface ChargeSchedule {
  name: string
  timed: boolean
  time: string
  soc: number
  frequency: {
    once: Array<Date>
    selected: string
    weekly: boolean[]
  }
}
export function createChargeSchedule () : ChargeSchedule {
  return {
    name: 'Neuer Plan',
    timed: false,
    time: '12:00',
    soc: 80,
    frequency: {
      once: [new Date('2022-02-02'),new Date('2022-02-22')],
      selected: 'daily',
      weekly: [false,false,false,false,false,false,false]
    }
  }
}
export interface ChargeTemplate {
  name: string
  prio: boolean
  time_charging: {
    active: boolean
    plans: {[key:string]:ChargeTimePlan}
  }
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
    scheduled_charging: {
      plans: {[key:string]:ChargeSchedule}
    }
  }
  disable_after_unplug: boolean
  load_default: boolean
 
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
export const chargePoints : { [key: number]: ChargePoint } = reactive({})
export const vehicles: { [key: number]: Vehicle } = reactive({}) // the list of vehicles, key is the vehicle ID
export const chargeTemplates: { [key: number]: ChargeTemplate } = reactive({})
export const evTemplates: { [key: number]: EvTemplate } = reactive({})

export function addChargePoint(chargePointIndex: number) {
  if (!(chargePointIndex in chargePoints)) {
    chargePoints[chargePointIndex] = new ChargePoint(chargePointIndex)
    chargePoints[chargePointIndex].color =
      'var(--color-cp' + (Object.values(chargePoints).length) + ')'
    console.info('Added chargepoint ' + chargePointIndex)
  } else {
    console.info('Duplicate chargepoint message: ' + chargePointIndex)
  }
}
export function resetChargePoints() {
  Object.keys(chargePoints).forEach((key) => {
    delete chargePoints [parseInt(key)]
  })
}
