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
