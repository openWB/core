import { etData } from './model'

export function processEtProviderMessages(topic: string, message: string) {
	if (topic == 'openWB/optional/et/provider') {
		etData.etProvider = JSON.parse(message).name
	} else if (topic == 'openWB/optional/et/get/prices') {
		const plist = JSON.parse(message)
		etData.etPriceList = new Map<Date, number>()
		Object.keys(plist).map((datestring) => {
			etData.etPriceList.set(
				new Date(+datestring * 1000),
				plist[datestring] * 100000,
			)
		})
	} else {
		// console.warn('Ignored ET Provider message: ' + topic)
	}
}
