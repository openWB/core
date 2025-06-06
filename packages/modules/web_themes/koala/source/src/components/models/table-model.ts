import { QTableColumn } from 'quasar';

// export type columnConfig = {
//   fields: string[];
//   fieldsExpansionRow?: string[];
//   labels?: Record<string, string>;
//   align?: Align;
// };

export type columnConfiguration = {
  field: string;
  label: string;
  align?: 'left' | 'right' | 'center';
  expandField?: boolean;
};

export interface BodySlotProps<T> {
  key: string | number;
  row: T;
  cols: QTableColumn[];
  expand: boolean;
}

export interface ChargePointRow extends Record<string, unknown> {
  id: number;
  name: string | undefined;
  vehicle: string;
  plugged: boolean;
  chargeMode: string | undefined;
  timeCharging: boolean | undefined;
  soc: string;
  power: string;
  phaseNumber: number;
  current: string;
  powerColumn: '';
  charged: string;
}

export interface VehicleRow extends Record<string, unknown> {
  id: number;
  name: string;
  manufacturer: string;
  model: string;
  plugState: boolean;
  chargeState: boolean;
  vehicleSocValue: string;
}
