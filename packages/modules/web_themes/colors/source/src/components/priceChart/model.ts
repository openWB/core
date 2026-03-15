import { reactive } from 'vue'
import { globalData } from '@/assets/js/model'

class EtData {
	active = false
	etPriceList = new Map<Date, number>()
	etProvider = ''
	etMaxPrice = 0
	country = 'de'

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
}

export interface ServerPriceList {
	[key: string]: number
}

export const etData = reactive(new EtData())
