export type CategoryKey = 'pv' | 'grid' | 'house' | 'battery' | 'consumer' | 'chargepoint' | 'counter'

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

export interface SocPoint {
  timestamp: number
  soc: number
}

export interface SocSeries {
  id: string
  label: string
  points: SocPoint[]
}

/** Same shape as CategoryData; individual is empty in live mode (only the aggregate is published). */
export interface SocCategoryData {
  all: SocPoint[]
  individual: SocSeries[]
}
