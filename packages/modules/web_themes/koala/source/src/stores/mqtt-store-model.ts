export interface ThemeConfiguration {
  history_chart_range: number;
}

export interface ConnectionOptions {
  protocol: string;
  host: string;
  port: number;
  endpoint: string;
  connectTimeout: number;
  reconnectPeriod: number;
}

export interface TopicObject {
  [key: string]: unknown;
}

export interface TopicList {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

export interface TopicCount {
  [key: string]: number;
}

export interface Hierarchy {
  id: number;
  type: string;
  children: Hierarchy[];
}
export interface ChartData {
  [key: string]: number[];
}

export interface ChargePointConnectedVehicleConfig {
  average_consumption: number;
  charge_template: number;
  chargemode: string;
  current_plan: number | null;
  ev_template: number;
  priority: boolean;
  time_charging_in_use: boolean;
}

export interface ChargePointConnectedVehicleSoc {
  fault_str: string;
  fault_state: string;
  range_charged: number;
  range_unit: string;
  range?: number;
  soc: number;
  time_stamp: Date;
}

export interface ChargePointConnectedVehicleInfo {
  id: number;
  name: string;
}
export interface ChargeTemplateConfiguration {
  name: string;
  prio: boolean;
  load_default: boolean;
  time_charging: {
    active: boolean;
  };
  chargemode: {
    selected: string;
    eco_charging: {
      current: number;
      dc_current: number;
      limit: {
        selected: string;
        amount: number;
        soc: number;
      };
      max_price: number;
      phases_to_use: number;
    };
    instant_charging: {
      current: number;
      dc_current: number;
      limit: {
        selected: string;
        amount: number;
        soc: number;
      };
      phases_to_use: number;
    };
    pv_charging: {
      dc_min_current: number;
      dc_min_soc_current: number;
      feed_in_limit: boolean;
      limit: {
        selected: string;
        amount: number;
        soc: number;
      };
      min_current: number;
      min_soc: number;
      min_soc_current: number;
      phases_to_use: number;
      phases_to_use_min_soc: number;
    };
    scheduled_charging: object;
  };
}

export interface ValueObject {
  textValue: string;
  value: number;
  unit: string;
  scaledValue: number;
  scaledUnit: string;
}

export interface Vehicle {
  id: number;
  name: string;
}

export interface ScheduledChargingPlan {
  id: number;
  name: string;
  active: boolean;
  et_active: boolean;
  current: number;
  dc_current: number;
  time: string;
  phases_to_use: number;
  phases_to_use_pv: number;
  frequency: {
    selected: string;
    once?: string;
    weekly: boolean[];
  };
  limit: {
    selected: string;
    amount?: number;
    soc_limit?: number;
    soc_scheduled?: number;
  };
}

export interface GraphDataPoint {
  timestamp: number;
  time: string;
  grid: number;
  'house-power': number;
  'charging-all': number;
  'pv-all': number;
  'bat-all-power': number;
  'bat-all-soc': number;
  [key: `cp${number}-power`]: number;
  [key: `ev${number}-soc`]: number | null;
}

export interface BatteryConfiguration {
  name: string;
  info: {
    manufacturer: string;
    model: string;
  };
  type: string;
  id: number;
  configuration: object;
}
