/*
 * helpers.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

export function formatWatt(watt: number, decimalPlaces = 1) {
	let wattResult: number
	if (watt >= 1000 && decimalPlaces < 4) {
		switch (decimalPlaces) {
			case 0:
				wattResult = Math.round(watt / 1000)
				break
			case 1:
				wattResult = Math.round(watt / 100) / 10
				break
			case 2:
				wattResult = Math.round(watt / 10) / 100
				break
			case 3:
				wattResult = Math.round(watt) / 1000
				break
			default:
				wattResult = Math.round(watt / 100) / 10
				break
		}
		return (
			wattResult?.toLocaleString(undefined, {
				minimumFractionDigits: decimalPlaces,
			}) + ' kW'
		)
	} else {
		return Math.round(watt).toLocaleString() + ' W'
	}
}

export function formatWattH(
	wattH: number,
	decimalPlaces: number = 1,
	useMWh = false,
) {
	let wattResult: number
	if (wattH > 1000000) {
		useMWh = true
		wattH = wattH / 1000
	}
	if (wattH >= 1000 && decimalPlaces < 4) {
		switch (decimalPlaces) {
			case 0:
				wattResult = Math.round(wattH / 1000)
				break
			case 1:
				wattResult = Math.round(wattH / 100) / 10
				break
			case 2:
				wattResult = Math.round(wattH / 10) / 100
				break
			case 3:
				wattResult = Math.round(wattH) / 1000
				break
			default:
				wattResult = Math.round(wattH / 100) / 10
				break
		}
		return (
			wattResult.toLocaleString(undefined, {
				minimumFractionDigits: decimalPlaces,
			}) + (useMWh ? ' MWh' : ' kWh')
		)
	} else {
		return Math.round(wattH).toLocaleString() + (useMWh ? ' kWh' : ' Wh')
	}
}
export function formatTime(seconds: number) {
	const hours = Math.floor(seconds / 3600)
	const minutes = ((seconds % 3600) / 60).toFixed(0)
	if (hours > 0) {
		return hours + 'h ' + minutes + ' min'
	} else {
		return minutes + ' min'
	}
}
export function formatCurrentTime(d: Date, includeDay = false) {
	if (includeDay) {
		return d.toLocaleTimeString(['de-DE'], {
			weekday: 'short',
			hour: '2-digit',
			minute: '2-digit',
		})
	} else {
		return d.toLocaleTimeString(['de-DE'], {
			hour: '2-digit',
			minute: '2-digit',
		})
	}
}
export function formatDate(d: Date, mode: string = 'day') {
	switch (mode) {
		case 'day':
		case 'today':
			return `${d.getDate()}.${d.getMonth() + 1}.${d.getFullYear()}`
		case 'month':
			return `${d.getMonth()}-${d.getFullYear()}`
		case 'year':
			return `${d.getFullYear()}`
	}
}
export function formatMonth(month: number, year: number) {
	const months = [
		'Jan',
		'Feb',
		'März',
		'April',
		'Mai',
		'Juni',
		'Juli',
		'Aug',
		'Sep',
		'Okt',
		'Nov',
		'Dez',
	]
	return months[month] + ' ' + year
}

export function formatTemp(t: number) {
	return t != 999
		? (Math.round(t * 10) / 10).toLocaleString(undefined, {
				minimumFractionDigits: 1,
			}) + '°'
		: '-'
}

export function fgColor(colorname: string) {
	const root = document.documentElement
	const style = getComputedStyle(root)
	colorname = colorname.slice(4, -1) // remove 'var(...)'
	const bgColor = style.getPropertyValue(colorname).trim()
	const r = parseInt(bgColor.slice(1, 3), 16)
	const g = parseInt(bgColor.slice(3, 5), 16)
	const b = parseInt(bgColor.slice(5, 7), 16)
	const brightness = (r * 299 + g * 587 + b * 114) / 1000
	return brightness > 125 ? 'black' : 'white'
}
