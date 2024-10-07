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

export interface ChartData {
  [key: string]: number[];
}
