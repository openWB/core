import { QTableColumn } from 'quasar';

export type ColumnConfiguration = {
  field: string;
  label: string;
  align?: 'left' | 'right' | 'center';
  expandField?: boolean;
  autoWidth?: boolean;
  shrink?: boolean;
};

export interface BodySlotProps<T> {
  key: string | number;
  row: T;
  cols: ExtendedQTableColumn[];
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
  color: string;
}

export interface VehicleRow extends Record<string, unknown> {
  id: number;
  name: string;
  manufacturer: string;
  model: string;
  plugState: boolean;
  chargeState: boolean;
  vehicleSocValue: string;
  color: string;
}

export type ExtendedQTableColumn = QTableColumn & {
  autoWidth?: boolean;
  shrink?: boolean;
};
