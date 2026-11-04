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

/** State-of-charge (%), a fundamentally different unit from power - kept separate from CategoryData/CategoryKey. */
export interface SocPoint {
  timestamp: number
  soc: number
}

export interface SocSeries {
  id: string
  label: string
  points: SocPoint[]
}

/** Same {all, individual} shape as CategoryData, for the battery SoC line - individual is empty in
 *  live mode (only an aggregate 'bat-all-soc' is published there, same asymmetry the 'battery' power
 *  category already has between day/live). */
export interface SocCategoryData {
  all: SocPoint[]
  individual: SocSeries[]
}
