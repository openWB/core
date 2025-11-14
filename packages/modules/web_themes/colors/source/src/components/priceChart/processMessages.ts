import { globalData } from '@/assets/js/model'
import { etData } from './model'

export function processEtProviderMessages(topic: string, message: string) {
	if (topic == 'openWB/optional/ep/configured') {
		const data = JSON.parse(message)
		if (data.type == null) {
			etData.active = false
		} else {
			etData.active = true
		}
		if (data.configuration && data.configuration.country != null) {
			globalData.country = data.configuration.country
		}
	} else if (topic == 'openWB/optional/ep/get/prices') {
		const plist = JSON.parse(message)
		etData.etPriceList = new Map<Date, number>()
		Object.keys(plist).forEach((datestring) => {
			etData.etPriceList.set(
				new Date(+datestring * 1000),
				plist[datestring] * 100000,
			)
		})
	} else {
		// console.warn('Ignored ET Provider message: ' + topic)
	}
}
