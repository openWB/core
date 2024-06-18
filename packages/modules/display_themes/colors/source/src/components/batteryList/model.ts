/*
 * model.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

import { reactive } from 'vue'
export class Battery {
	id: number
	dailyYieldExport = 0
	dailyYieldImport = 0
	exported = 0
	faultState = 0
	faultStr = ''
	imported = 0
	power = 0
	soc = 0
	constructor(index: number) {
		this.id = index
	}
}
export class BatterySummary {
	dailyExport = 0
	dailyImport = 0
	exported = 0
	imported = 0
	power = 0
	soc = 0
}
export const batteries: { [key: number]: Battery } = reactive({})
export const batterySummary = reactive(new BatterySummary())

export function addBattery(index: number) {
	if (!(index in batteries)) {
		batteries[index] = new Battery(index)
	} else {
		console.info('Duplicate battery message: ' + index)
	}
}

export function resetBatteries() {
	Object.keys(batteries).forEach((key) => {
		delete batteries[parseInt(key)]
	})
}
