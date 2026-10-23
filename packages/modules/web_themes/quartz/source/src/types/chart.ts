export type CategoryKey = 'pv' | 'grid' | 'house' | 'battery' | 'consumer' | 'chargepoint'

export interface InstancePoint {
  timestamp: number
  power: number
}

export interface InstanceSeries {
  id: string
  label: string
  points: InstancePoint[]
}

/** 'all' is the combined/summed series; 'individual' is empty where the data source has no per-component breakdown. */
export interface CategoryData {
  all: InstancePoint[]
  individual: InstanceSeries[]
}
