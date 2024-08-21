/*
 * types.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

// Type definitions for all components
import { updateServer } from '@/assets/js/sendMessages'
import { ChargeMode } from '@/components/chargePointList/model'

export class ShDevice implements PowerItem {
	id: number
	name = ''
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

export class GlobalData {
	batterySoc = 0
	isBatteryConfigured = true
	chargeMode = '0'
	private _pvBatteryPriority = 'ev_mode' // 'ev_mode' | 'bat_mode' | 'min_soc_bat_mode'
	displayLiveGraph = true
	isEtEnabled = true
	etMaxPrice = 0
	etCurrentPrice = 0
	cpDailyExported = 0
	evuId = 0
	etProvider = ''
	ipAddress = ''
	systemTime = 0.0
	version = ''
	versionDetails = ''
	devBranch = ''
	get pvBatteryPriority() {
		return this._pvBatteryPriority
	}
	set pvBatteryPriority(prio: string) {
		this._pvBatteryPriority = prio
		updateServer('pvBatteryPriority', prio)
	}
	updatePvBatteryPriority(prio: string) {
		this._pvBatteryPriority = prio
	}
}

export interface Hierarchy {
	id: number
	type: string
	children: [Hierarchy]
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

export interface PowerItem {
	name: string
	power: number
	energy: number
	energyPv: number
	energyBat: number
	pvPercentage: number
	color: string
	icon: string
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
export const evPriorityModes: [string, string][] = [
	['EV', 'ev_mode'],
	['Speicher', 'bat_mode'],
	['MinSoc', 'min_soc_bat_mode'],
]
