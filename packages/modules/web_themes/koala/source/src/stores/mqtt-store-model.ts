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
  et: {
    active: boolean;
    max_price: number;
  };
  time_charging: {
    active: boolean;
  };
  chargemode: {
    selected: string;
    pv_charging: {
      dc_min_current: number;
      dc_min_soc_current: number;
      min_soc_current: number;
      min_current: number;
      feed_in_limit: boolean;
      min_soc: number;
      max_soc: number;
    };
    scheduled_charging: object;
    instant_charging: {
      current: number;
      dc_current: number;
      limit: {
        selected: string;
        amount: number;
        soc: number;
      };
    };
  };
}

export interface ValueObject {
  [key: string]: string | number;
}

export interface Vehicle {
  id: number;
  name: string;
}

export interface ScheduledChargingPlan {
  id: string;
  active: boolean;
  frequency: {
    selected: string;
    once?: string;
    weekly?: boolean[];
    selected_days?: string[];
  };
  current: number;
  time: string;
  limit: {
    selected: string;
    amount?: number;
    soc_limit?: number;
    soc_scheduled?: number;
  };
  name: string;
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
