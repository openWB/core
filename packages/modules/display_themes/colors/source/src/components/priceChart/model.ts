import { reactive } from 'vue'
// import { updateServer } from '@/assets/js/sendMessages'
class EtData {
	active = false
	etPriceList = new Map<Date, number>()
	etProvider = ''
	etMaxPrice = 0

	get etCurrentPriceString() {
		const [p] = etData.etPriceList.values()
		return (Math.round(p * 10) / 10).toFixed(1) + ' ct'
	}
}

export interface ServerPriceList {
	[key: string]: number
}

export const etData = reactive(new EtData())
