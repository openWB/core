/*
 * types.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

// Type definitions for all components

export class ShDevice implements PowerItem {
	id: number
	name = ''
	type = PowerItemType.device
	power = 0
	energy = 0
	energyPv = 0
	energyBat = 0
	pvPercentage = 0
	configured = true
	showInGraph = true
	color = 'white'
	icon = ''
	countAsHouse = false
	constructor(index: number) {
		this.id = index
	}
}

export interface Hierarchy {
	id: number
	type: string
	children: [Hierarchy]
}
export enum ChargeMode {
	instant_charging = 'instant_charging',
	pv_charging = 'pv_charging',
	scheduled_charging = 'scheduled_charging',
	eco_charging = 'eco_charging',
	stop = 'stop',
}

export interface ChargeModeInfo {
	mode: ChargeMode
	name: string
	color: string
	icon: string
}

export interface ItemProps {
	name: string
	color: string
	icon: string
}
export enum PowerItemType {
	counter = 'counter',
	inverter = 'inverter',
	pvSummary = 'pvSummary',
	battery = 'battery',
	batterySummary = 'batterySummary',
	chargepoint = 'chargepoint',
	chargeSummary = 'chargeSummary',
	device = 'device',
	deviceSummary = 'deviceSummary',
	house = 'house',
}
export interface PowerItem {
	name: string
	type: PowerItemType
	power: number
	energy: number
	energyPv: number
	energyBat: number
	pvPercentage: number
	color: string
	icon: string
	showInGraph: boolean
}

export interface ItemList {
	[key: string]: PowerItem
}

export interface MarginType {
	left: number
	top: number
	right: number
	bottom: number
}

export class PvSystem implements PowerItem {
	id: number
	name = 'Wechselrichter'
	type = PowerItemType.inverter
	color = 'var(--color-pv)'
	power = 0
	energy = 0
	energy_month = 0
	energy_year = 0
	energy_total = 0
	energyPv = 0
	energyBat = 0
	pvPercentage = 0
	icon = ''
	showInGraph = true
	constructor(index: number) {
		this.id = index
	}
}

export const evPriorityModes: [string, string][] = [
	['EV', 'ev_mode'],
	['Speicher', 'bat_mode'],
	['MinSoc', 'min_soc_bat_mode'],
]
