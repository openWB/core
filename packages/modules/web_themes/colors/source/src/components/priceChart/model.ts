import { reactive } from 'vue'
// import { updateServer } from '@/assets/js/sendMessages'
class EtData {
	etPriceList = new Map<Date, number>()
	etProvider = ''
	etMaxPrice = 0
}

export interface ServerPriceList {
	[key: string]: number
}

export const etData = reactive(new EtData())
