import { globalData } from '@/assets/js/model'
import { etData } from './model'

export function processEtProviderMessages(topic: string, message: string) {
	if (topic == 'openWB/optional/ep/configured') {
		etData.active = message == 'true'
	} else if (topic == 'openWB/optional/ep/flexible_tariff/provider') {
		const data = JSON.parse(message)
		etData.etProvider = data.name
		if (data.configuration) {
			if (data.configuration.country != null) {
				globalData.country = data.configuration.country
				etData.country = data.configuration.country
			}
			if (data.configuration.unit != null) {
				etData.unit = data.configuration.unit
			}
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
