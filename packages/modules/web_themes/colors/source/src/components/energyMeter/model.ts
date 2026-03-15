import { type PowerItem } from '@/assets/js/types'
import { registry } from '@/assets/js/model'
import { graphData } from '../powerGraph/model'

export function autPct(item: PowerItem) {
	if (item.name == 'PV') {
		const exportedEnergy = registry.getEnergy('evuOut')
		const generatedEnergy = registry.getEnergy('pv')
		return Math.round(
			((generatedEnergy - exportedEnergy) / generatedEnergy) * 100,
		)
	} else if (item.name == 'Netz') {
		const exportedEnergy = registry.getEnergy('evuOut')
		const importedEnergy = registry.getEnergy('evuIn')
		const generatedEnergy = registry.getEnergy('pv')
		const batEnergy = registry.getEnergy('batOut')
		const storedEnergy = registry.getEnergy('batIn')
		return Math.round(
			((generatedEnergy + batEnergy - exportedEnergy - storedEnergy) /
				(generatedEnergy +
					batEnergy +
					importedEnergy -
					exportedEnergy -
					storedEnergy)) *
				100,
		)
	} else {
		return item[graphData.graphScope].pvPercentage
	}
}
