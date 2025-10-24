import { reactive } from 'vue'
import { globalData } from '@/assets/js/model'

class EtData {
	active = false
	etPriceList = new Map<Date, number>()
	etProvider = ''
	etMaxPrice = 0
	country = 'de'

	get etCurrentPriceString() {
		const [p] = etData.etPriceList.values()
		return (
			(Math.round(p * 10) / 10).toFixed(1) +
			(globalData.country === 'ch' ? ' Rp' : ' ct')
		)
	}
}

export interface ServerPriceList {
	[key: string]: number
}

export const etData = reactive(new EtData())
