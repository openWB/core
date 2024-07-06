/*
 * model.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

import { masterData } from '@/assets/js/model'
import { reactive, ref } from 'vue'
export class Battery {
	id: number
	name = 'Speicher'
	color = 'var(--color-battery)'
	dailyYieldExport = 0
	dailyYieldImport = 0
	monthlyYieldExport = 0
	monthlyYieldImport = 0
	yearlyYieldExport = 0
	yearlyYieldImport = 0
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

export const batterySummary = reactive(new BatterySummary())
export const batteries = ref(new Map<number, Battery>())
export const addBattery = (index: number) => {
	batteries.value.set(index, new Battery(index))
	batteries.value.get(index)!.color =
		masterData['bat' + batteries.value.size].color
}

export function resetBatteries() {
	batteries.value = new Map<number, Battery>()
}
