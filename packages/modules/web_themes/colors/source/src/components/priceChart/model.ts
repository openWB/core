import { reactive } from 'vue'
import { globalData } from '@/assets/js/model'

class EtData {
	active = false
	etPriceList = new Map<Date, number>()
	etProvider = ''
	etMaxPrice = 0
	country = 'de'
	unit = 'ct'

	get etCurrentPriceString() {
		if (this.etPriceList.size > 0) {
			const [p] = this.etPriceList.values()
			return (
				(Math.round(p * 10) / 10).toFixed(1) +
				(globalData.country === 'ch' ? ' Rp' : ' ct')
			)
		} else {
			return '---'
		}
	}

	maxPriceForDuration(durationMinutes: number, maxTime?: Date): number {
		if (this.etPriceList.size > 0) {
			const plist = maxTime
				? [...this.etPriceList.entries()]
						.filter((entry) => entry[0] <= maxTime)
						.sort((a, b) => a[1] - b[1])
				: [...this.etPriceList.entries()].sort((a, b) => a[1] - b[1])
			let accumulatedMinutes = 0
			for (let i = 0; i < plist.length; i++) {
				accumulatedMinutes += 15
				if (accumulatedMinutes >= durationMinutes) {
					return plist[i][1]
				}
			}
			return -1 // return the highest price if duration exceeds available data
		} else {
			return -1
		}
	}

	maxDate(): Date | null {
		if (this.etPriceList.size > 0) {
			return Array.from(this.etPriceList.keys()).reduce((a, b) =>
				a > b ? a : b,
			)
		} else {
			return null
		}
	}
}

export interface ServerPriceList {
	[key: string]: number
}

export const etData = reactive(new EtData())
