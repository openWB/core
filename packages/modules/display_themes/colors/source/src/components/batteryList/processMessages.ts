/*
 * processMessages.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

import { usageSummary, sourceSummary, globalData } from '@/assets/js/model'
import { batteries } from './model'
export function processBatteryMessages(topic: string, message: string) {
	const index = getIndex(topic)
	if (index && !(index in batteries)) {
		console.warn('Invalid battery index received: ' + index)
		return
	}
	if (topic == 'openWB/bat/config/configured') {
		globalData.isBatteryConfigured = message == 'true'
	} else if (topic == 'openWB/bat/get/power') {
		if (+message > 0) {
			usageSummary.batIn.power = +message
			sourceSummary.batOut.power = 0
		} else {
			usageSummary.batIn.power = 0
			sourceSummary.batOut.power = -message
		}
	} else if (topic == 'openWB/bat/get/soc') {
		globalData.batterySoc = +message
	} else if (topic == 'openWB/bat/get/daily_exported') {
		sourceSummary.batOut.energy = +message
	} else if (topic == 'openWB/bat/get/daily_imported') {
		usageSummary.batIn.energy = +message
	} else if (index) {
		if (topic.match(/^openwb\/bat\/[0-9]+\/get\/daily_yield_export$/i)) {
			batteries[index].dailyYieldExport = +message
		} else if (topic.match(/^openwb\/bat\/[0-9]+\/get\/daily_yield_import$/i)) {
			batteries[index].dailyYieldImport = +message
		} else if (topic.match(/^openwb\/bat\/[0-9]+\/get\/exported$/i)) {
			batteries[index].exported = +message
		} else if (topic.match(/^openwb\/bat\/[0-9]+\/get\/fault_state$/i)) {
			batteries[index].faultState = +message
		} else if (topic.match(/^openwb\/bat\/[0-9]+\/get\/fault_str$/i)) {
			batteries[index].faultStr = message
		} else if (topic.match(/^openwb\/bat\/[0-9]+\/get\/imported$/i)) {
			batteries[index].imported = +message
		} else if (topic.match(/^openwb\/bat\/[0-9]+\/get\/power$/i)) {
			batteries[index].power = +message
		} else if (topic.match(/^openwb\/bat\/[0-9]+\/get\/soc$/i)) {
			batteries[index].soc = +message
		} else {
			// console.warn('Ignored battery message: ' + topic)
		}
	} else {
		// console.warn('Ignored battery message: ' + topic)
	}
}

function getIndex(topic: string): number | undefined {
	let index = 0
	try {
		const matches = topic.match(/(?:\/)([0-9]+)(?=\/)/g)
		if (matches) {
			index = +matches[0].replace(/[^0-9]+/g, '')
			return index
		} else {
			return undefined
		}
	} catch (e) {
		console.warn('Parser error in getIndex for topic ' + topic + ' : ' + e)
	}
}
