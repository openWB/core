import { reactive } from 'vue'
export class Counter {
	id: number
	name = 'Zähler'
	power = 0
	energy_imported = 0
	energy_exported = 0
	grid = false
	type = 'counter'
	color = 'var(--color-evu)'
	energyPv = 0
	energyBat = 0
	pvPercentage = 0
	icon = ''
	constructor(index: number) {
		this.id = index
	}
}

export const counters: { [key: number]: Counter } = reactive({})

export function addCounter(index: number, type: string) {
	if (!(index in counters)) {
		counters[index] = new Counter(index)
		counters[index].type = type
		switch (type) {
			case 'counter':
				counters[index].color = 'var(--color-evu)'
				break
			case 'inverter':
				counters[index].color = 'var(--color-pv)'
				break
			case 'cp':
				counters[index].color = 'var(--color-charging)'
				break
			case 'bat':
				counters[index].color = 'var(--color-bat)'
				break
		}
		//console.info('Added counter ' + index)
	} else {
		console.info('Duplicate counter message: ' + index)
	}
}
